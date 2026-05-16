#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def _active_task(queue: dict[str, Any]) -> dict[str, Any]:
    current = str(queue.get("current_task") or "")
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and str(task.get("task_id") or task.get("id") or "") == current:
            return task
    for task in as_list(queue.get("tasks")):
        if isinstance(task, dict) and str(task.get("status") or "") == "active":
            return task
    return {}


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
        payload.update(
            {
                "version_status": str(status.get("status") or ""),
                "current_gate": str(queue.get("current_gate") or status.get("current_gate") or ""),
                "active_task": {
                    "id": str(active.get("task_id") or active.get("id") or ""),
                    "title": str(active.get("title") or ""),
                    "phase": str(active.get("phase") or ""),
                    "status": str(active.get("status") or ""),
                    "gate_id": str(active.get("gate_id") or ""),
                }
                if active
                else {},
                "declared_rqs": [
                    str(rq.get("id"))
                    for rq in as_list(spine.get("research_questions"))
                    if isinstance(rq, dict) and rq.get("id")
                ],
                "baseline_lock_status": str(baseline.get("status") or ""),
                "evidence_gate": {
                    "next_required_gate": str(gate.get("next_required_gate") or ""),
                    "claim_counts": _claim_counts(gate),
                },
                "open_human_reviews": _open_human_reviews(human_reviews),
            }
        )

    if include_validators and research_dir.exists():
        payload["validators"] = _validator_status(research_dir)

    return payload


def render_markdown(status: dict[str, Any]) -> str:
    active = status.get("active_task") if isinstance(status.get("active_task"), dict) else {}
    gate = status.get("evidence_gate") if isinstance(status.get("evidence_gate"), dict) else {}
    claim_counts = gate.get("claim_counts") if isinstance(gate.get("claim_counts"), dict) else {}
    validators = status.get("validators") if isinstance(status.get("validators"), dict) else {}

    lines = [
        "# Research Status",
        "",
        f"- research_dir: `{status.get('research_dir', '')}`",
        f"- workspace_role: `{status.get('workspace_role', '')}`",
        f"- direction_status: `{status.get('direction_status', '')}`",
        f"- current_version: `{status.get('current_version', '') or 'N/A'}`",
        f"- version_status: `{status.get('version_status', '') or 'N/A'}`",
        f"- current_gate: `{status.get('current_gate', '') or 'N/A'}`",
        f"- baseline_lock_status: `{status.get('baseline_lock_status', '') or 'N/A'}`",
        f"- evidence_gate.next_required_gate: `{gate.get('next_required_gate', '') or 'N/A'}`",
        f"- claim_counts: allowed={claim_counts.get('allowed', 0)}, draft={claim_counts.get('draft', 0)}, forbidden={claim_counts.get('forbidden', 0)}",
        f"- declared_rqs: `{', '.join(status.get('declared_rqs') or []) or 'N/A'}`",
        "",
        "## Active Task",
    ]
    if active:
        lines.extend(
            [
                f"- id: `{active.get('id', '')}`",
                f"- title: {active.get('title', '')}",
                f"- phase: `{active.get('phase', '')}`",
                f"- status: `{active.get('status', '')}`",
                f"- gate_id: `{active.get('gate_id', '')}`",
            ]
        )
    else:
        lines.append("- none")

    open_reviews = status.get("open_human_reviews") or []
    lines.extend(["", "## Human Review"])
    if open_reviews:
        for item in open_reviews[:8]:
            if isinstance(item, dict):
                request_id = item.get("id") or item.get("request_id") or "<unknown>"
                title = item.get("title") or item.get("reason") or item.get("status") or ""
                lines.append(f"- `{request_id}`: {title}")
    else:
        lines.append("- none")

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
