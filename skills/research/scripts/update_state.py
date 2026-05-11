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
    load_yaml,
    read_text,
    write_next_action_from_task_queue,
    write_task_run_report,
    write_yaml,
)


SCHEMA_VERSION = 1
VALID_STATUSES = {"done", "blocked", "failed", "skipped"}


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


def update_task_queue(epoch_dir: Path, task_id: str, status: str) -> dict[str, Any] | None:
    queue_path = epoch_dir / "TASK_QUEUE.yaml"
    queue = load_yaml(queue_path)
    tasks = queue.get("tasks", [])
    if not isinstance(tasks, list):
        return None

    next_task = None
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            continue
        if str(task.get("id", "")) == task_id:
            task["status"] = status
            task["completed_at"] = today_string()
            # Find next pending task
            for j in range(i + 1, len(tasks)):
                if isinstance(tasks[j], dict) and tasks[j].get("status") in ("pending", None):
                    next_task = tasks[j]
                    break
            break

    if next_task and status == "done":
        next_task["status"] = "active"

    if status in ("blocked", "failed"):
        queue["queue_status"] = "blocked"

    write_yaml(queue_path, queue, force=True)
    return next_task


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


def update_status_yaml(epoch_dir: Path, task_id: str, status: str) -> None:
    status_path = epoch_dir / "STATUS.yaml"
    payload = load_yaml(status_path) if status_path.exists() else {}
    payload["last_completed_task"] = task_id
    if status == "blocked":
        payload["status"] = "gate_blocked"
        payload["blocked_task"] = task_id
    elif status in ("done", "completed"):
        if payload.get("status") in ("gate_blocked", "blocked"):
            pass  # Don't override blocked status unless unblocked explicitly
        else:
            payload["status"] = "running"

    write_yaml(status_path, payload, force=True)


def write_run_report_from_args(
    epoch_dir: Path, version: str, task_id: str, status: str,
    commit_hash: str | None, gate_id: str | None, blocker_reason: str | None,
) -> None:
    report = {
        "report_version": 1,
        "task": {
            "version": version,
            "task_id": task_id,
            "status": status,
            "gate_id": gate_id,
        },
        "git": {
            "commit_created": commit_hash is not None,
            "commit_hash": commit_hash,
        },
        "execution": {"commands_run": [], "stdout_path": None, "stderr_path": None, "exit_code": None, "files_changed": []},
        "evidence": {"tests": {"passed": False, "output_path": None}, "artifacts": [], "blockers": []},
        "gate_outcome": {
            "gate_passed": status == "done",
            "gate_blocked": status in ("blocked", "failed"),
            "blocker_reason": blocker_reason,
        },
        "next_action": {"recommendation": None, "wiki_update_needed": False},
    }
    write_task_run_report(epoch_dir, version, task_id, report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Atomic state updater for the research loop.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--task-id", required=True, help="Task ID to update (e.g. TASK_002).")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES), help="Task outcome status.")
    parser.add_argument("--commit-hash", default="", help="Git commit hash after task completion.")
    parser.add_argument("--gate-id", default="", help="Gate ID this task belongs to.")
    parser.add_argument("--blocker-reason", default="", help="Reason when status is blocked or failed.")
    parser.add_argument("--note", default="", help="Optional free-text note for LOOP_LOG.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned updates without writing.")
    return parser.parse_args()


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

    if args.dry_run:
        print(f"[DRY RUN] would update state for {version}/{args.task_id} -> {args.status}")
        print(f"  commit_hash: {commit_hash}")
        print(f"  gate_id: {gate_id}")
        print(f"  blocker_reason: {blocker_reason}")
        return 0

    # 1. Update TASK_QUEUE.yaml and find next task
    next_task = update_task_queue(epoch_dir, args.task_id, args.status)
    print(f"[OK] TASK_QUEUE.yaml: {args.task_id} -> {args.status}")
    if next_task:
        print(f"[OK] next task activated: {next_task.get('id', '?')}")

    # 2. Append to LOOP_LOG.md
    append_loop_log(epoch_dir, args.task_id, args.status, commit_hash, args.note)
    print(f"[OK] LOOP_LOG.md appended")

    # 3. Update GIT_STATE.yaml
    update_git_state(epoch_dir, commit_hash, args.task_id, args.status)
    print(f"[OK] GIT_STATE.yaml updated")

    # 4. Update STATUS.yaml
    update_status_yaml(epoch_dir, args.task_id, args.status)
    print(f"[OK] STATUS.yaml updated")

    # 5. Write task run report
    write_run_report_from_args(epoch_dir, version, args.task_id, args.status, commit_hash, gate_id, blocker_reason)
    print(f"[OK] runs/{args.task_id}_report.yaml written")

    # 6. Regenerate NEXT_ACTION.md from TASK_QUEUE
    next_action_path = write_next_action_from_task_queue(epoch_dir, version)
    print(f"[OK] {next_action_path.relative_to(repo)} regenerated")

    print(f"\n[OK] atomic state update complete for {version}/{args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
