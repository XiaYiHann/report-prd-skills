#!/usr/bin/env python3
"""Atomic state updater for the research loop.

Call this after each task execution to update all state files in one pass.
The executing agent (Claude Code) should run this script, not edit state files manually.

Usage:
    python3 update_state.py --repo /path/to/repo --task-id TASK_002 --status completed \\
        --commit-hash abc123 --gate-id G01

    python3 update_state.py --repo /path/to/repo --task-id TASK_003 --status blocked \\
        --blocker-reason "baseline code segfaults with CUDA 12.4"
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    GATE_STATUSES,
    TASK_STATUSES,
    as_list,
    load_yaml,
    missing_search_outputs,
    read_text,
    task_search_required,
    write_task_run_report,
    write_epoch_goal_files,
    write_yaml,
)


SCHEMA_VERSION = 1
VALID_STATUSES = set(TASK_STATUSES) | {"done", "failed"}
VALID_FAILURE_CLASSES = {
    "environment_failure",
    "execution_failure",
    "harness_failure",
    "spec_gap",
    "prd_ambiguity",
    "research_falsification_candidate",
    "confirmed_research_falsification",
}
VALID_EXECUTORS = {"codex", "claude-code", "manual"}
VALID_GOAL_TARGETS = {"codex", "claude-code", "both"}
DONE_TASK_STATUSES = {"completed", "skipped"}
BLOCKED_TASK_STATUSES = {"blocked", "failed_execution", "failed_harness"}


def today_string() -> str:
    return dt.date.today().isoformat()


def append_loop_log(epoch_dir: Path, task_id: str, status: str, commit_hash: str | None, note: str = "") -> None:
    log_path = epoch_dir / "LOOP_LOG.md"
    existing = ""
    if log_path.exists():
        existing = read_text(log_path)
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_line = f"\n- commit_hash: `{commit_hash}`" if commit_hash else ""
    entry = f"""
## {timestamp} — {task_id} — {status}

- task_id: {task_id}
- status: {status}{commit_line}
- note: {note if note else 'N/A'}
"""
    log_path.write_text((existing.rstrip() + "\n" + entry), encoding="utf-8")


def normalize_task_status(status: str) -> str:
    aliases = {"done": "completed", "failed": "failed_execution"}
    normalized = aliases.get(status, status)
    if normalized not in TASK_STATUSES:
        raise ValueError(f"invalid task status: {status}")
    return normalized


def _task_id(task: dict[str, Any]) -> str:
    return str(task.get("task_id") or task.get("id") or "")


def _gate_id(gate: dict[str, Any]) -> str:
    return str(gate.get("gate_id") or gate.get("id") or "")


def _task_dependencies(task: dict[str, Any]) -> list[str]:
    raw = task.get("depends_on", task.get("dependencies", []))
    if isinstance(raw, str):
        return [raw] if raw else []
    return [str(item) for item in as_list(raw) if str(item)]


def _task_status_by_id(tasks: list[dict[str, Any]]) -> dict[str, str]:
    return {_task_id(task): str(task.get("status") or "") for task in tasks if _task_id(task)}


def _task_runnable(task: dict[str, Any], status_by_id: dict[str, str]) -> bool:
    if str(task.get("status") or "") != "pending":
        return False
    for dep_id in _task_dependencies(task):
        if status_by_id.get(dep_id) not in DONE_TASK_STATUSES:
            return False
    return True


def _activate_task(queue: dict[str, Any], gate: dict[str, Any], task: dict[str, Any], gate_id: str) -> None:
    task["status"] = "active"
    _sync_gate_task_status(queue, _task_id(task), "active")
    gate["status"] = "active"
    queue["queue_status"] = "active"
    queue["current_gate"] = gate_id
    queue["current_task"] = _task_id(task)


def _sync_gate_task_status(queue: dict[str, Any], task_id: str, status: str) -> None:
    for gate in as_list(queue.get("gates")):
        if not isinstance(gate, dict):
            continue
        for gate_task in as_list(gate.get("tasks")):
            if isinstance(gate_task, dict) and str(gate_task.get("task_id") or "") == task_id:
                gate_task["status"] = status


def evaluate_gate_after_task(queue: dict[str, Any], gate_id: str) -> None:
    gates = [gate for gate in as_list(queue.get("gates")) if isinstance(gate, dict)]
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    gate = next((item for item in gates if _gate_id(item) == gate_id), None)
    if gate is None:
        return

    gate_tasks = [
        task for task in tasks
        if str(task.get("gate_id") or gate_id) == gate_id
    ]
    status_by_id = _task_status_by_id(tasks)
    blocked = [task for task in gate_tasks if str(task.get("status")) in BLOCKED_TASK_STATUSES]
    pending = [task for task in gate_tasks if str(task.get("status")) == "pending"]
    runnable = [task for task in pending if _task_runnable(task, status_by_id)]

    if runnable:
        gate["blocked_tasks"] = [_task_id(task) for task in blocked]
        _activate_task(queue, gate, runnable[0], gate_id)
        return

    if blocked:
        gate["status"] = "blocked"
        gate["blocked_tasks"] = [_task_id(task) for task in blocked]
        queue["queue_status"] = "blocked"
        queue["current_gate"] = gate_id
        queue["current_task"] = None
        return

    if pending:
        gate["status"] = "blocked"
        gate["blocked_tasks"] = []
        gate["block_reason"] = "no runnable task; pending tasks wait on unfinished dependencies"
        queue["queue_status"] = "blocked"
        queue["current_gate"] = gate_id
        queue["current_task"] = None
        return

    if gate_tasks and all(str(task.get("status")) in {"completed", "skipped"} for task in gate_tasks):
        audit = gate.get("audit", {}) if isinstance(gate.get("audit"), dict) else {}
        if audit.get("required") is True:
            gate["status"] = "audit_required"
            audit["status"] = "pending"
            gate["audit"] = audit
            queue["queue_status"] = "audit_required"
            queue["current_gate"] = gate_id
            queue["current_task"] = None
        else:
            gate["status"] = "passed"
            queue["queue_status"] = "passed"
            queue["current_gate"] = gate_id
            queue["current_task"] = None


def update_gate_aware_task_queue(
    epoch_dir: Path,
    task_id: str,
    status: str,
    gate_id: str | None,
    failure_class: str | None,
) -> dict[str, Any] | None:
    queue_path = epoch_dir / "TASK_QUEUE.yaml"
    queue = load_yaml(queue_path)
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    if not tasks:
        return None

    next_task = None
    resolved_gate_id = gate_id
    for task in tasks:
        if _task_id(task) == task_id:
            task["status"] = status
            task["completed_at"] = today_string()
            if failure_class:
                task["failure_class"] = failure_class
            resolved_gate_id = resolved_gate_id or str(task.get("gate_id") or "")
            _sync_gate_task_status(queue, task_id, status)
            break

    if resolved_gate_id:
        evaluate_gate_after_task(queue, resolved_gate_id)
    elif status in {"blocked", "failed_execution", "failed_harness"}:
        queue["queue_status"] = "blocked"

    write_yaml(queue_path, queue, force=True)
    current_task = str(queue.get("current_task") or "")
    if current_task:
        next_task = next((task for task in tasks if _task_id(task) == current_task), None)
    return next_task


def update_task_queue(epoch_dir: Path, task_id: str, status: str) -> dict[str, Any] | None:
    return update_gate_aware_task_queue(epoch_dir, task_id, status, None, None)


def current_task_payload(epoch_dir: Path, task_id: str) -> dict[str, Any] | None:
    queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and _task_id(task) == task_id:
            return task
    return None


def assert_search_completion_allowed(epoch_dir: Path, task: dict[str, Any] | None) -> None:
    if not task or not task_search_required(task):
        return
    missing = missing_search_outputs(epoch_dir, task)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"missing search evidence for { _task_id(task) }: {joined}")


def update_git_state(epoch_dir: Path, commit_hash: str | None, task_id: str, status: str) -> None:
    git_path = epoch_dir / "GIT_STATE.yaml"
    git_state = load_yaml(git_path) if git_path.exists() else {}
    tasks_log = git_state.get("task_log", [])
    if not isinstance(tasks_log, list):
        tasks_log = []

    entry: dict[str, Any] = {
        "task_id": task_id,
        "status": status,
        "date": today_string(),
    }
    if commit_hash:
        entry["commit_hash"] = commit_hash
    tasks_log.append(entry)

    git_state["task_log"] = tasks_log
    if commit_hash:
        git_state["last_commit"] = {
            "hash": commit_hash,
            "task_id": task_id,
            "date": today_string(),
        }

    write_yaml(git_path, git_state, force=True)


def update_status_yaml(epoch_dir: Path, task_id: str, status: str, queue: dict[str, Any] | None = None) -> None:
    status_path = epoch_dir / "STATUS.yaml"
    payload = load_yaml(status_path) if status_path.exists() else {}
    payload["last_completed_task"] = task_id
    if status in ("blocked", "failed_execution", "failed_harness"):
        queue_payload = queue if isinstance(queue, dict) else load_yaml(epoch_dir / "TASK_QUEUE.yaml")
        blocked_tasks = list(payload.get("blocked_tasks") or [])
        if task_id not in blocked_tasks:
            blocked_tasks.append(task_id)
        payload["blocked_tasks"] = blocked_tasks
        payload["blocked_task"] = task_id
        if str(queue_payload.get("queue_status") or "") == "active" and queue_payload.get("current_task"):
            payload["status"] = "running"
        else:
            payload["status"] = "gate_blocked"
    elif status in ("done", "completed"):
        if payload.get("status") in ("gate_blocked", "blocked"):
            pass  # Don't override blocked status unless unblocked explicitly
        else:
            payload["status"] = "running"

    write_yaml(status_path, payload, force=True)


def refresh_goal_contract(epoch_dir: Path) -> None:
    lock_path = epoch_dir / "GOAL_LOCK.yaml"
    target = "both"
    if lock_path.exists():
        payload = load_yaml(lock_path)
        locked_target = str(payload.get("target_executor") or "")
        if locked_target in VALID_GOAL_TARGETS:
            target = locked_target
    write_epoch_goal_files(epoch_dir, target_executor=target, force=True)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean true/false, got: {value}")


def parse_artifact_arg(raw: str) -> dict[str, str]:
    marker = ":sha256="
    if marker not in raw:
        raise ValueError("artifact must use path:sha256=<digest>")
    path, digest = raw.split(marker, 1)
    if not path.strip() or not digest.strip():
        raise ValueError("artifact must use path:sha256=<digest>")
    return {"path": path.strip(), "sha256": digest.strip()}


def build_run_report_from_args(epoch_dir: Path, version: str, args: Any) -> dict[str, Any]:
    artifacts = [parse_artifact_arg(raw) for raw in getattr(args, "artifact", [])]
    blocker_reason = args.blocker_reason.strip() or None
    commit_hash = args.commit_hash.strip() or None
    gate_id = args.gate_id.strip() or None
    status = normalize_task_status(args.status)
    failure_class = getattr(args, "failure_class", "") or None
    tests_passed = getattr(args, "tests_passed", None)
    return {
        "schema_version": 2,
        "report_version": 2,
        "epoch": version,
        "gate_id": gate_id,
        "task_id": args.task_id,
        "executor": getattr(args, "executor", "manual"),
        "task": {
            "version": version,
            "task_id": args.task_id,
            "status": status,
            "gate_id": gate_id,
        },
        "git": {
            "commit_created": commit_hash is not None,
            "commit_hash": commit_hash,
            "dirty_tree_after_task": getattr(args, "dirty_tree_after_task", False),
        },
        "environment": {},
        "command": {
            "raw": list(getattr(args, "command", [])),
            "cwd": str(epoch_dir.parent.parent),
            "timeout_sec": None,
            "exit_code": getattr(args, "exit_code", None),
        },
        "execution": {
            "executor": getattr(args, "executor", "manual"),
            "commands_run": list(getattr(args, "command", [])),
            "stdout_path": getattr(args, "stdout_path", None),
            "stderr_path": getattr(args, "stderr_path", None),
            "exit_code": getattr(args, "exit_code", None),
            "files_changed": list(getattr(args, "file_changed", [])),
        },
        "stdout_summary": "",
        "stderr_summary": "",
        "artifacts": artifacts,
        "metrics": [],
        "reproducibility": {},
        "anti_mock": {
            "dataset_type": None,
            "mock_labeled": None,
            "allowed_for_paper_claim": False,
        },
        "evidence": {
            "tests": {
                "passed": bool(tests_passed) if tests_passed is not None else False,
                "commands": list(getattr(args, "test_command", [])),
                "output_path": getattr(args, "test_output_path", None),
            },
            "artifacts": artifacts,
            "blockers": [blocker_reason] if blocker_reason else [],
        },
        "gate_outcome": {
            "gate_passed": False,
            "gate_blocked": status in ("blocked", "failed_execution", "failed_harness"),
            "blocker_reason": blocker_reason,
        },
        "conclusion": {
            "task_result": "pass" if status == "completed" else status,
            "failure_class": failure_class,
            "research_interpretation_allowed": False,
        },
        "next_action": {"recommendation": None, "wiki_update_needed": False},
    }


def write_run_report_from_args(
    epoch_dir: Path, version: str, task_id: str, status: str,
    commit_hash: str | None, gate_id: str | None, blocker_reason: str | None,
    args: argparse.Namespace,
) -> None:
    report = build_run_report_from_args(epoch_dir, version, args)
    write_task_run_report(epoch_dir, version, task_id, report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Atomic state updater for the research loop.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--task-id", required=True, help="Task ID to update (e.g. TASK_002).")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES), help="Task outcome status.")
    parser.add_argument("--commit-hash", default="", help="Git commit hash after task completion.")
    parser.add_argument("--gate-id", default="", help="Gate ID this task belongs to.")
    parser.add_argument("--blocker-reason", default="", help="Reason when status is blocked or failed.")
    parser.add_argument("--failure-class", default="", choices=[""] + sorted(VALID_FAILURE_CLASSES), help="Failure triage class.")
    parser.add_argument("--note", default="", help="Optional free-text note for LOOP_LOG.md.")
    parser.add_argument("--executor", default="manual", choices=sorted(VALID_EXECUTORS), help="Agent executor submitting this evidence.")
    parser.add_argument("--command", action="append", default=[], help="Command executed by the agent. Can be repeated.")
    parser.add_argument("--stdout-path", default=None, help="Path to captured stdout.")
    parser.add_argument("--stderr-path", default=None, help="Path to captured stderr.")
    parser.add_argument("--exit-code", type=int, default=None, help="Process exit code for the main command.")
    parser.add_argument("--test-command", action="append", default=[], help="Test command executed by the agent. Can be repeated.")
    parser.add_argument("--test-output-path", default=None, help="Path to captured test output.")
    parser.add_argument("--tests-passed", type=parse_bool, default=None, help="Whether tests passed.")
    parser.add_argument("--artifact", action="append", default=[], help="Artifact evidence in path:sha256=<digest> format.")
    parser.add_argument("--file-changed", action="append", default=[], help="Changed file path. Can be repeated.")
    parser.add_argument("--dirty-tree-after-task", type=parse_bool, default=False, help="Whether the tree was dirty after task completion.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned updates without writing.")
    args = parser.parse_args()
    for raw in args.artifact:
        try:
            parse_artifact_arg(raw)
        except ValueError as exc:
            parser.error(str(exc))
    return args


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    research_dir = repo / "docs" / "research"
    if not research_dir.exists():
        print(f"[ERROR] research workspace not found: {research_dir}")
        return 1

    current_file = research_dir / "CURRENT"
    version = read_text(current_file).strip() if current_file.exists() else "V0"
    epoch_dir = research_dir / version
    if not epoch_dir.exists():
        print(f"[ERROR] epoch directory not found: {epoch_dir}")
        return 1

    commit_hash = args.commit_hash.strip() or None
    gate_id = args.gate_id.strip() or None
    blocker_reason = args.blocker_reason.strip() or None
    status = normalize_task_status(args.status)
    failure_class = args.failure_class.strip() or None

    if args.dry_run:
        print(f"[DRY RUN] would update state for {version}/{args.task_id} -> {status}")
        print(f"  commit_hash: {commit_hash}")
        print(f"  gate_id: {gate_id}")
        print(f"  blocker_reason: {blocker_reason}")
        return 0

    if status == "completed":
        try:
            assert_search_completion_allowed(epoch_dir, current_task_payload(epoch_dir, args.task_id))
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    # 1. Update TASK_QUEUE.yaml and find next task
    next_task = update_gate_aware_task_queue(epoch_dir, args.task_id, status, gate_id, failure_class)
    print(f"[OK] TASK_QUEUE.yaml: {args.task_id} -> {status}")
    if next_task:
        print(f"[OK] next task activated: {next_task.get('task_id') or next_task.get('id', '?')}")

    # 2. Append to LOOP_LOG.md
    append_loop_log(epoch_dir, args.task_id, status, commit_hash, args.note)
    print(f"[OK] LOOP_LOG.md appended")

    # 3. Update GIT_STATE.yaml
    update_git_state(epoch_dir, commit_hash, args.task_id, status)
    print(f"[OK] GIT_STATE.yaml updated")

    # 4. Update STATUS.yaml
    queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
    update_status_yaml(epoch_dir, args.task_id, status, queue)
    print(f"[OK] STATUS.yaml updated")

    # 5. Write task run report
    write_run_report_from_args(epoch_dir, version, args.task_id, status, commit_hash, gate_id, blocker_reason, args)
    print(f"[OK] runs/{args.task_id}_report.yaml written")

    # 6. Refresh the version-level long-loop goal after queue/status drift.
    refresh_goal_contract(epoch_dir)
    print(f"[OK] GOAL_LOCK.yaml refreshed")

    # 7. Emit blocker prompt if the queue is blocked
    if str(queue.get("queue_status", "")) in ("blocked", "audit_required"):
        current_gate = str(queue.get("current_gate") or gate_id or "unknown")
        active = [t for t in as_list(queue.get("tasks")) if str(t.get("status")) == "active"]
        next_task_id = active[0].get("task_id") if active else None
        print(f"\n[PROMPT] queue_status={queue.get('queue_status')}; gate={current_gate}; next_task={next_task_id}")
        print(f"  blocker_reason: {blocker_reason or 'N/A'}")
        print(f"  failure_class: {failure_class or 'N/A'}")
        print("  -> A human decision is required before automation can continue.")

    print(f"\n[OK] atomic state update complete for {version}/{args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
