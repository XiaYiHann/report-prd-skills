#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    as_list,
    current_epoch_name,
    is_meta_framework_workspace,
    load_yaml,
    read_text,
    resolve_research_dir,
    validate_research,
)


VALIDATOR_MODES = [
    "direction-ready",
    "epoch-ready",
    "rq-driven-ready",
    "baseline-lock-ready",
    "goal-ready",
    "loop-ready",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report the current research-loop status without modifying files.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--no-validators", action="store_true", help="Skip validator probes.")
    return parser.parse_args()


def _status_from_direction(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- status:"):
            return stripped.split(":", 1)[1].strip().strip("`") or "unknown"
        if stripped.lower().startswith("status:"):
            return stripped.split(":", 1)[1].strip().strip("`") or "unknown"
    return "unknown"


def _clean_scalar(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    while len(text) >= 2 and text[0] == "`" and text[-1] == "`":
        text = text[1:-1].strip()
    return text


def _markdown_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        key = key.strip().strip("`")
        if re.fullmatch(r"[A-Za-z0-9_./-]+", key):
            values[key] = _clean_scalar(value)
    return values


def _markdown_section_first_paragraph(text: str, heading: str) -> str:
    capture = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower() == f"## {heading}".lower():
            capture = True
            continue
        if capture and stripped.startswith("## "):
            return ""
        if capture and stripped and stripped != "---" and not stripped.startswith("#"):
            return stripped
    return ""


def _direction_summary(text: str) -> dict[str, str]:
    values = _markdown_key_values(text)
    return {
        "direction_id": values.get("direction_id", ""),
        "status": values.get("status", _status_from_direction(text)),
        "current_version": values.get("current_version", ""),
        "final_target": values.get("final_target", ""),
        "big_rq": values.get("big_rq", ""),
        "falsification_condition": values.get("falsification_condition", ""),
        "minimum_viable_purpose": values.get("minimum_viable_purpose", ""),
        "core_hypothesis_id": values.get("core_hypothesis_id", ""),
        "core_hypothesis": values.get("core_hypothesis", ""),
        "hypothesis_status": values.get("hypothesis_status", ""),
        "mvr_question": values.get("mvr_question", ""),
        "mvr_success_condition": values.get("mvr_success_condition", ""),
        "mvr_failure_condition": values.get("mvr_failure_condition", ""),
        "mvr_status": values.get("mvr_status", ""),
    }


def _prd_summary(epoch_dir: Path) -> dict[str, str]:
    values = _markdown_key_values(read_text(epoch_dir / "PRD_SUMMARY.md"))
    return {
        "title": values.get("title", ""),
        "purpose": values.get("purpose", ""),
        "canonical_prd": values.get("canonical_prd", "PRD.tex"),
        "review_pdf": values.get("review_pdf", "PRD.pdf"),
    }


def _task_id(task: dict[str, Any]) -> str:
    return str(task.get("task_id") or task.get("id") or "")


def _task_status(task: dict[str, Any]) -> str:
    return str(task.get("status") or "unknown")


def _active_task(queue: dict[str, Any]) -> dict[str, Any]:
    current = str(queue.get("current_task") or "")
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and str(task.get("task_id") or task.get("id") or "") == current:
            return task
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and str(task.get("status") or "") == "active":
            return task
    return {}


def _tasks_by_id(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict):
            task_id = _task_id(task)
            if task_id:
                tasks[task_id] = task
    return tasks


def _task_counts(tasks: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {"total": 0}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = _task_status(task)
        counts["total"] += 1
        counts[status] = counts.get(status, 0) + 1
    return counts


def _complete_status(status: str) -> bool:
    return status.lower() in {"done", "complete", "completed", "passed", "success"}


def _blocked_status(status: str) -> bool:
    return status.lower() in {"blocked", "gate_blocked", "failed", "error", "needs_human_review"}


def _dependency_ids(task: dict[str, Any]) -> list[str]:
    return [str(dep) for dep in as_list(task.get("depends_on")) if dep]


def _dependencies_satisfied(task: dict[str, Any], tasks_by_id: dict[str, dict[str, Any]]) -> bool:
    for dep_id in _dependency_ids(task):
        dep = tasks_by_id.get(dep_id)
        if not dep or not _complete_status(_task_status(dep)):
            return False
    return True


def _summarize_task(task: dict[str, Any]) -> dict[str, Any]:
    harness = task.get("harness") if isinstance(task.get("harness"), dict) else {}
    research_binding = task.get("research_binding") if isinstance(task.get("research_binding"), dict) else {}
    return {
        "id": _task_id(task),
        "title": str(task.get("title") or ""),
        "phase": str(task.get("phase") or ""),
        "status": _task_status(task),
        "gate_id": str(task.get("gate_id") or ""),
        "type": str(task.get("type") or ""),
        "depends_on": _dependency_ids(task),
        "rq_id": str(research_binding.get("rq_id") or ""),
        "claim_ids": [str(item) for item in as_list(research_binding.get("claim_ids"))],
        "experiment_ids": [str(item) for item in as_list(research_binding.get("experiment_ids"))],
        "success_criteria": [str(item) for item in as_list(task.get("success_criteria"))],
        "evidence_required": [str(item) for item in as_list(task.get("evidence_required"))],
        "output_refs": [str(item) for item in as_list(task.get("output_refs"))],
        "allowed_files": [str(item) for item in as_list(task.get("allowed_files"))],
        "harness": {
            "command": str(harness.get("command") or ""),
            "success_predicate": str(harness.get("success_predicate") or ""),
            "artifact_paths": [str(item) for item in as_list(harness.get("artifact_paths"))],
        },
    }


def _runnable_tasks(queue: dict[str, Any]) -> list[dict[str, Any]]:
    tasks_by_id = _tasks_by_id(queue)
    runnable: list[dict[str, Any]] = []
    for task in tasks_by_id.values():
        status = _task_status(task).lower()
        if status in {"pending", "ready"} and _dependencies_satisfied(task, tasks_by_id):
            runnable.append(_summarize_task(task))
    return runnable


def _gate_progress(queue: dict[str, Any]) -> list[dict[str, Any]]:
    tasks_by_id = _tasks_by_id(queue)
    gates: list[dict[str, Any]] = []
    for gate in as_list(queue.get("gates")):
        if not isinstance(gate, dict):
            continue
        gate_task_ids = [
            str(item.get("task_id") or item.get("id") or "")
            for item in as_list(gate.get("tasks"))
            if isinstance(item, dict)
        ]
        gate_tasks = [tasks_by_id[task_id] for task_id in gate_task_ids if task_id in tasks_by_id]
        if not gate_tasks:
            gate_tasks = [
                task
                for task in tasks_by_id.values()
                if str(task.get("gate_id") or "") == str(gate.get("gate_id") or "")
            ]
        audit = gate.get("audit") if isinstance(gate.get("audit"), dict) else {}
        gates.append(
            {
                "id": str(gate.get("gate_id") or ""),
                "name": str(gate.get("name") or ""),
                "status": str(gate.get("status") or ""),
                "task_counts": _task_counts(gate_tasks),
                "active_tasks": [_task_id(task) for task in gate_tasks if _task_status(task) == "active"],
                "blocked_tasks": [_task_id(task) for task in gate_tasks if _blocked_status(_task_status(task))],
                "audit_required": bool(audit.get("required")),
                "audit_status": str(audit.get("status") or ""),
            }
        )
    return gates


def _claim_counts(gate: dict[str, Any]) -> dict[str, int]:
    states = gate.get("claim_states") if isinstance(gate.get("claim_states"), dict) else {}
    return {
        "allowed": len(as_list(states.get("allowed_claim"))),
        "draft": len(as_list(states.get("draft_claim"))),
        "forbidden": len(as_list(states.get("forbidden_claim"))),
    }


def _open_human_reviews(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for request in as_list(payload.get("requests")):
        if not isinstance(request, dict):
            continue
        status = str(request.get("status") or "").lower()
        if status not in {"resolved", "closed", "done", "complete"}:
            result.append(request)
    return result


def _rq_progress(epoch_dir: Path, spine: dict[str, Any]) -> list[dict[str, Any]]:
    progress: list[dict[str, Any]] = []
    for rq in as_list(spine.get("research_questions")):
        if not isinstance(rq, dict):
            continue
        rq_id = str(rq.get("id") or "")
        rq_dir = epoch_dir / str(rq.get("rq_dir") or f"rqs/{rq_id}")
        spec = load_yaml(epoch_dir / str(rq.get("spec_ref") or rq_dir.relative_to(epoch_dir) / "SPEC.yaml"))
        if not spec:
            spec = load_yaml(rq_dir / "SPEC.yaml")
        tasks_payload = load_yaml(rq_dir / "TASKS.yaml")
        rq_text = read_text(rq_dir / "RQ.md")
        research_question = spec.get("research_question") if isinstance(spec.get("research_question"), dict) else {}
        human_approval = spec.get("human_approval") if isinstance(spec.get("human_approval"), dict) else {}
        experiment_contract = spec.get("experiment_contract") if isinstance(spec.get("experiment_contract"), dict) else {}
        tasks = as_list(tasks_payload.get("tasks"))
        next_task = {}
        for task in tasks:
            if isinstance(task, dict) and _task_status(task).lower() in {"active", "ready", "pending"}:
                next_task = _summarize_task(task)
                break
        progress.append(
            {
                "id": rq_id,
                "statement": _clean_scalar(
                    research_question.get("statement")
                    or rq.get("text")
                    or _markdown_section_first_paragraph(rq_text, "Statement")
                ),
                "motivation": _clean_scalar(research_question.get("motivation")),
                "approval_status": str(human_approval.get("status") or ""),
                "falsification_condition": _clean_scalar(research_question.get("falsification_condition")),
                "task_counts": _task_counts(tasks),
                "next_task": next_task,
                "blocked_tasks": [
                    _summarize_task(task)
                    for task in tasks
                    if isinstance(task, dict) and _blocked_status(_task_status(task))
                ],
                "experiment_contract": {
                    "datasets": [str(item) for item in as_list(experiment_contract.get("datasets"))],
                    "models": [str(item) for item in as_list(experiment_contract.get("models"))],
                    "baselines": [str(item) for item in as_list(experiment_contract.get("baselines"))],
                    "metrics": [str(item) for item in as_list(experiment_contract.get("metrics"))],
                    "harnesses": [str(item) for item in as_list(experiment_contract.get("harnesses"))],
                },
            }
        )
    return progress


def _collect_blockers(
    queue: dict[str, Any],
    baseline: dict[str, Any],
    open_reviews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and _blocked_status(_task_status(task)):
            blockers.append({"type": "task", "id": _task_id(task), "title": str(task.get("title") or ""), "status": _task_status(task)})
    for gate in as_list(queue.get("gates")):
        if isinstance(gate, dict) and _blocked_status(str(gate.get("status") or "")):
            blockers.append({"type": "gate", "id": str(gate.get("gate_id") or ""), "title": str(gate.get("name") or ""), "status": str(gate.get("status") or "")})
    baseline_status = str(baseline.get("status") or "")
    if baseline_status.lower() in {"blocked", "needs_human_review", "failed"}:
        blockers.append({"type": "baseline_lock", "id": "BASELINE_LOCK.yaml", "title": baseline_status, "status": baseline_status})
    for request in open_reviews:
        blockers.append(
            {
                "type": "human_review",
                "id": str(request.get("id") or request.get("request_id") or ""),
                "title": str(request.get("title") or request.get("reason") or ""),
                "status": str(request.get("status") or ""),
            }
        )
    return blockers


def _validator_status(research_dir: Path) -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    for mode in VALIDATOR_MODES:
        validation = validate_research(research_dir, mode)
        statuses[mode] = {
            "ok": validation.ok,
            "issue_count": len(validation.issues),
            "issues": validation.issues[:8],
        }
    return statuses


def _next_actions(payload: dict[str, Any], queue: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    current_experiment = payload.get("current_experiment") if isinstance(payload.get("current_experiment"), dict) else {}
    active = current_experiment.get("active_task") if isinstance(current_experiment.get("active_task"), dict) else {}
    if active:
        outputs = ", ".join(active.get("output_refs") or active.get("harness", {}).get("artifact_paths") or [])
        actions.append(
            {
                "type": "continue_active_task",
                "target": str(active.get("id") or ""),
                "description": f"Continue `{active.get('title', '')}` and produce {outputs or 'declared evidence artifacts'}.",
            }
        )
    for task in _runnable_tasks(queue)[:5]:
        if task.get("id") != active.get("id"):
            actions.append(
                {
                    "type": "runnable_task",
                    "target": str(task.get("id") or ""),
                    "description": f"`{task.get('title', '')}` has no unfinished dependencies.",
                }
            )
    if not actions and payload.get("blockers"):
        first = payload["blockers"][0]
        actions.append(
            {
                "type": "resolve_blocker",
                "target": str(first.get("id") or first.get("type") or ""),
                "description": str(first.get("title") or first.get("status") or "Resolve the current blocker."),
            }
        )
    if not actions:
        actions.append(
            {
                "type": "inspect_queue",
                "target": str(payload.get("current_gate") or ""),
                "description": "No active or dependency-free task is currently declared; inspect TASK_QUEUE.yaml.",
            }
        )
    return actions


def build_status(research_dir: Path, include_validators: bool = True) -> dict[str, Any]:
    direction = research_dir / "RESEARCH_DIRECTION.md"
    version = current_epoch_name(research_dir)
    role = "meta_framework" if is_meta_framework_workspace(research_dir) else "research_workspace"
    if not research_dir.exists():
        role = "missing"
    elif not version and role != "meta_framework":
        role = "legacy_or_incomplete"

    payload: dict[str, Any] = {
        "research_dir": str(research_dir),
        "workspace_role": role,
        "direction_status": _status_from_direction(read_text(direction)) if direction.exists() else "missing",
        "current_version": version or "",
        "version_status": "",
        "current_gate": "",
        "active_task": {},
        "research_goal": _direction_summary(read_text(direction)) if direction.exists() else {},
        "epoch_progress": {},
        "rq_progress": [],
        "current_experiment": {"active_task": {}, "declared_experiments": []},
        "blockers": [],
        "next_actions": [],
        "declared_rqs": [],
        "baseline_lock_status": "",
        "evidence_gate": {},
        "open_human_reviews": [],
        "validators": {},
    }

    if version:
        epoch_dir = research_dir / version
        status = load_yaml(epoch_dir / "STATUS.yaml")
        spine = load_yaml(epoch_dir / "RESEARCH_SPINE.yaml")
        queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
        baseline = load_yaml(epoch_dir / "BASELINE_LOCK.yaml")
        gate = load_yaml(epoch_dir / "EVIDENCE_GATE.yaml")
        human_reviews = load_yaml(epoch_dir / "HUMAN_REVIEW_REQUESTS.yaml")
        active = _active_task(queue)
        open_reviews = _open_human_reviews(human_reviews)
        rq_progress = _rq_progress(epoch_dir, spine)
        active_summary = _summarize_task(active) if active else {}
        payload.update(
            {
                "version_status": str(status.get("status") or ""),
                "current_gate": str(queue.get("current_gate") or status.get("current_gate") or ""),
                "active_task": active_summary,
                "research_goal": {
                    **payload["research_goal"],
                    **{f"prd_{key}": value for key, value in _prd_summary(epoch_dir).items() if value},
                },
                "epoch_progress": {
                    "queue_status": str(queue.get("queue_status") or ""),
                    "task_counts": _task_counts(as_list(queue.get("tasks"))),
                    "gates": _gate_progress(queue),
                    "last_completed_task": str(status.get("last_completed_task") or ""),
                    "close_reason": str(status.get("close_reason") or ""),
                },
                "rq_progress": rq_progress,
                "current_experiment": {
                    "current_gate": str(queue.get("current_gate") or status.get("current_gate") or ""),
                    "active_task": active_summary,
                    "declared_experiments": [
                        item for item in as_list(spine.get("experiments")) if isinstance(item, dict)
                    ],
                    "rq_bindings": [
                        {
                            "id": item.get("id"),
                            "approval_status": item.get("approval_status"),
                            "task_counts": item.get("task_counts"),
                        }
                        for item in rq_progress
                    ],
                },
                "declared_rqs": [
                    str(rq.get("id"))
                    for rq in as_list(spine.get("research_questions"))
                    if isinstance(rq, dict) and rq.get("id")
                ],
                "baseline_lock_status": str(baseline.get("status") or ""),
                "evidence_gate": {
                    "next_required_gate": str(gate.get("next_required_gate") or ""),
                    "claim_counts": _claim_counts(gate),
                    "draft_only_until": [str(item) for item in as_list(gate.get("evidence_admission", {}).get("draft_only_until") if isinstance(gate.get("evidence_admission"), dict) else [])],
                    "required_for_allowed_claim": [str(item) for item in as_list(gate.get("evidence_admission", {}).get("required_for_allowed_claim") if isinstance(gate.get("evidence_admission"), dict) else [])],
                },
                "open_human_reviews": open_reviews,
            }
        )
        payload["blockers"] = _collect_blockers(queue, baseline, open_reviews)
        payload["next_actions"] = _next_actions(payload, queue)

    if include_validators and research_dir.exists():
        payload["validators"] = _validator_status(research_dir)

    return payload


def render_markdown(status: dict[str, Any]) -> str:
    goal = status.get("research_goal") if isinstance(status.get("research_goal"), dict) else {}
    epoch_progress = status.get("epoch_progress") if isinstance(status.get("epoch_progress"), dict) else {}
    current_experiment = status.get("current_experiment") if isinstance(status.get("current_experiment"), dict) else {}
    active = current_experiment.get("active_task") if isinstance(current_experiment.get("active_task"), dict) else {}
    gate = status.get("evidence_gate") if isinstance(status.get("evidence_gate"), dict) else {}
    claim_counts = gate.get("claim_counts") if isinstance(gate.get("claim_counts"), dict) else {}
    validators = status.get("validators") if isinstance(status.get("validators"), dict) else {}

    lines = [
        "# Research Status",
        "",
        f"- research_dir: `{status.get('research_dir', '')}`",
        f"- workspace_role: `{status.get('workspace_role', '')}`",
        f"- current_version: `{status.get('current_version', '') or 'N/A'}`",
        f"- version_status: `{status.get('version_status', '') or 'N/A'}`",
        f"- current_gate: `{status.get('current_gate', '') or 'N/A'}`",
        "",
        "## Current Goal",
        f"- title: {goal.get('prd_title') or 'N/A'}",
        f"- purpose: {goal.get('prd_purpose') or goal.get('minimum_viable_purpose') or 'N/A'}",
        f"- big_rq: {goal.get('big_rq') or 'N/A'}",
        f"- core_hypothesis: {goal.get('core_hypothesis') or 'N/A'}",
        f"- mvr_status: `{goal.get('mvr_status') or 'N/A'}`",
        "",
        "## Experiment Progress",
        f"- queue_status: `{epoch_progress.get('queue_status') or 'N/A'}`",
        f"- task_counts: {', '.join(f'{key}={value}' for key, value in sorted((epoch_progress.get('task_counts') or {}).items())) or 'N/A'}",
        f"- baseline_lock_status: `{status.get('baseline_lock_status', '') or 'N/A'}`",
        f"- evidence_gate.next_required_gate: `{gate.get('next_required_gate', '') or 'N/A'}`",
        f"- claim_counts: allowed={claim_counts.get('allowed', 0)}, draft={claim_counts.get('draft', 0)}, forbidden={claim_counts.get('forbidden', 0)}",
    ]
    if active:
        lines.extend(
            [
                f"- active_task: `{active.get('id', '')}` {active.get('title', '')}",
                f"- active_phase: `{active.get('phase', '')}` / `{active.get('status', '')}`",
                f"- success_criteria: {'; '.join((active.get('success_criteria') or [])[:3]) or 'N/A'}",
                f"- evidence_required: {', '.join(active.get('evidence_required') or []) or 'N/A'}",
                f"- expected_outputs: {', '.join((active.get('output_refs') or active.get('harness', {}).get('artifact_paths') or [])[:6]) or 'N/A'}",
            ]
        )
    else:
        lines.append("- active_task: none")

    lines.extend(["", "## RQ Progress"])
    rq_progress = status.get("rq_progress") if isinstance(status.get("rq_progress"), list) else []
    if rq_progress:
        for item in rq_progress:
            if not isinstance(item, dict):
                continue
            counts = item.get("task_counts") if isinstance(item.get("task_counts"), dict) else {}
            next_task = item.get("next_task") if isinstance(item.get("next_task"), dict) else {}
            lines.append(
                f"- `{item.get('id', '')}` {item.get('statement') or 'N/A'} "
                f"(approval={item.get('approval_status') or 'N/A'}, tasks={counts.get('total', 0)}, "
                f"active={counts.get('active', 0)}, done={counts.get('done', counts.get('completed', 0))}, "
                f"next={next_task.get('id') or 'N/A'})"
            )
    else:
        lines.append("- none")

    open_reviews = status.get("open_human_reviews") or []
    blockers = status.get("blockers") if isinstance(status.get("blockers"), list) else []
    lines.extend(["", "## Blockers And Review"])
    if blockers:
        for item in blockers[:8]:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('type', '')}:{item.get('id', '')}` {item.get('title') or item.get('status') or ''}")
    else:
        lines.append("- blockers: none")
    if open_reviews:
        for item in open_reviews[:8]:
            if isinstance(item, dict):
                request_id = item.get("id") or item.get("request_id") or "<unknown>"
                title = item.get("title") or item.get("reason") or item.get("status") or ""
                lines.append(f"- human_review `{request_id}`: {title}")

    lines.extend(["", "## Next Actions"])
    actions = status.get("next_actions") or []
    if not actions:
        lines.append("- none")
    for action in actions:
        if isinstance(action, dict):
            lines.append(f"- `{action.get('type', '')}` {action.get('target', '')}: {action.get('description', '')}")

    if validators:
        lines.extend(["", "## Validators"])
        for mode in VALIDATOR_MODES:
            value = validators.get(mode, {})
            marker = "OK" if value.get("ok") else "BLOCKED"
            issue_count = value.get("issue_count", 0)
            lines.append(f"- {mode}: {marker} ({issue_count} issues)")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    status = build_status(research_dir, include_validators=not args.no_validators)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(status), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
