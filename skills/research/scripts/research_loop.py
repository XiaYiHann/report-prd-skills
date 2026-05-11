#!/usr/bin/env python3
"""Unified file-based controller for docs/research workspaces.

The controller remains prompt-only. New workspaces include a
Charter-bounded Epoch Research Loop (`RESEARCH_DIRECTION.md`, `CURRENT`,
and `Vn/NEXT_ACTION.md`). The legacy deterministic controller below is kept
compatible with `prd/spec/plans/audits`; generated runbooks define the epoch
controller contract for Claude Code and Codex without claiming shell execution.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    PRD_SECTIONS,
    SPEC_FILES,
    generate_audit,
    generate_paper,
    generate_plan,
    hash_path,
    init_research_workspace,
    init_spec_scaffold,
    load_yaml,
    read_task_run_report,
    slugify,
    validate_research,
    write_next_action_from_task_queue,
)


SCHEMA_VERSION = 1
REQUIRED_RESEARCH_DIRS = ["prd", "paper", "spec", "plans", "audits", "insights"]
APPROVAL_MARKER = "PRD_STATUS: HUMAN_APPROVED"
STAGE_INIT = "S0_INIT"
STAGE_PRD_MISSING = "S1_PRD_MISSING"
STAGE_PRD_NOT_READY = "S1_PRD_NOT_READY"
STAGE_PRD_READY = "S1_PRD_READY"
STAGE_SPEC_MISSING = "S2_SPEC_MISSING"
STAGE_SPEC_NOT_READY = "S2_SPEC_NOT_READY"
STAGE_SPEC_READY = "S2_SPEC_READY"
STAGE_PLAN_MISSING = "S3_PLAN_MISSING"
STAGE_PLAN_READY = "S3_PLAN_READY"
STAGE_EXECUTING = "S4_EXECUTING_PLAN"
STAGE_PLAN_BLOCKED = "S4_PLAN_BLOCKED"
STAGE_PLAN_COMPLETE = "S4_PLAN_COMPLETE"
STAGE_AUDIT_REQUIRED = "S5_AUDIT_REQUIRED"
STAGE_INSIGHT_REVIEW = "S6_INSIGHT_REVIEW_REQUIRED"
STAGE_PAPER_UPDATE = "S7_PAPER_UPDATE_READY"
STAGE_COMPLETE = "S8_RESEARCH_COMPLETE"


@dataclass
class PrdStatus:
    status: str
    human_approved: bool = False
    issues: list[str] = field(default_factory=list)
    ambiguity_issues: list[str] = field(default_factory=list)


@dataclass
class SpecStatus:
    status: str
    issues: list[str] = field(default_factory=list)


@dataclass
class PlanStatus:
    active_plan: str | None = None
    status: str = "missing"
    issues: list[str] = field(default_factory=list)
    stale_findings: list[str] = field(default_factory=list)


@dataclass
class InsightStatus:
    open_pivot_proposals: list[str] = field(default_factory=list)
    open_human_review_requests: list[str] = field(default_factory=list)
    unresolved_negative_results: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return bool(
            self.open_pivot_proposals
            or self.open_human_review_requests
            or self.unresolved_negative_results
        )


@dataclass
class Detection:
    stage: str
    blocked: bool = False
    block_reason: str | None = None
    prd: PrdStatus = field(default_factory=lambda: PrdStatus("missing"))
    spec: SpecStatus = field(default_factory=lambda: SpecStatus("missing"))
    plan: PlanStatus = field(default_factory=PlanStatus)
    insights: InsightStatus = field(default_factory=InsightStatus)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def is_resolution_marked(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in [
            "human_decision: approved",
            "human_decision: rejected",
            "human_decision: resolved",
            "decision: approved",
            "decision: rejected",
            "resolved: true",
        ]
    )


class ResearchLoop:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.repo = Path(args.repo).resolve()
        workspace = Path(args.workspace)
        self.research_dir = workspace if workspace.is_absolute() else (self.repo / workspace)
        self.research_dir = self.research_dir.resolve()
        self.date = args.date or dt.date.today().isoformat()
        self.actions: list[dict[str, Any]] = []
        self.dry_run_writes: list[str] = []

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo).as_posix()
        except ValueError:
            return path.resolve().as_posix()

    def write_text(self, path: Path, content: str) -> None:
        if self.args.dry_run:
            self.dry_run_writes.append(self.rel(path))
            return
        write_text(path, content)

    def write_yaml(self, path: Path, payload: dict[str, Any]) -> None:
        if self.args.dry_run:
            self.dry_run_writes.append(self.rel(path))
            return
        write_yaml_file(path, payload)

    def ensure_state_files(self) -> None:
        if not self.research_dir.exists():
            return
        for dirname in REQUIRED_RESEARCH_DIRS:
            path = self.research_dir / dirname
            if not self.args.dry_run:
                path.mkdir(parents=True, exist_ok=True)
        for subdir in [
            self.research_dir / "insights" / "anomaly_reports",
            self.research_dir / "insights" / "negative_results",
            self.research_dir / "insights" / "pivot_proposals",
            self.research_dir / "insights" / "diagnostic_experiment_proposals",
        ]:
            if not self.args.dry_run:
                subdir.mkdir(parents=True, exist_ok=True)
        queue_path = self.queue_path
        if not queue_path.exists():
            self.write_yaml(queue_path, {"schema_version": SCHEMA_VERSION, "queue": []})
        if not (self.research_dir / "state.yaml").exists():
            self.write_state(Detection(stage=STAGE_INIT, blocked=True, block_reason="state initialized"))

    @property
    def queue_path(self) -> Path:
        return self.research_dir / "plans" / "plan_queue.yaml"

    def detect_prd(self) -> PrdStatus:
        prd_path = self.research_dir / "prd" / "research_prd.md"
        state = load_yaml(self.research_dir / "state.yaml")
        prd_state = state.get("prd", {}) if isinstance(state.get("prd"), dict) else {}
        if not prd_path.exists():
            return PrdStatus(status="missing", human_approved=bool(prd_state.get("human_approved")))
        text = read_text(prd_path)
        issues: list[str] = []
        for section in PRD_SECTIONS:
            english_label = section.split("（", 1)[-1].rstrip("）") if "（" in section else section
            if section not in text and english_label not in text:
                issues.append(f"missing required PRD section: {english_label}")
        human_approved = APPROVAL_MARKER in text or prd_state.get("human_approved") is True
        if not human_approved:
            issues.append(f"missing human approval marker: {APPROVAL_MARKER}")
        concrete_rqs = [
            line
            for line in text.splitlines()
            if re.search(r"\bRQ\d+\b", line) and "待填写" not in line and "template" not in line.lower()
        ]
        if not concrete_rqs:
            issues.append("no concrete RQ definition")
        concrete_falsification = [
            line
            for line in text.splitlines()
            if "falsification" in line.lower() and "待填写" not in line and "template" not in line.lower()
        ]
        if not concrete_falsification:
            issues.append("hypotheses have no concrete falsification condition")
        lower = text.lower()
        for label in ["benchmark", "experiment", "dataset", "baseline", "metric", "harness"]:
            if label not in lower:
                issues.append(f"missing {label} plan")
        gate_issues = self.detect_prd_gates(text)
        issues.extend(gate_issues)
        ambiguity = self.detect_prd_ambiguity(text)
        status = "ready" if not issues else "not_ready"
        return PrdStatus(status=status, human_approved=human_approved, issues=issues, ambiguity_issues=ambiguity)

    def detect_prd_ambiguity(self, text: str) -> list[str]:
        issues: list[str] = []
        lowered = text.lower()
        ambiguous_patterns = [
            ("dataset", r"(standard dataset|dataset plan:.*chosen later|without selection criteria)"),
            ("baseline", r"(mainstream baselines|baseline plan:.*chosen later|baseline.*without selection criteria)"),
            ("metric", r"(metric plan:.*chosen later|metric.*undefined|required metric is undefined)"),
        ]
        for label, pattern in ambiguous_patterns:
            if re.search(pattern, lowered, flags=re.DOTALL):
                issues.append(f"PRD ambiguity: {label} is not concretely selected or governed by explicit criteria")
        if "rq" in lowered and "experiment design" in lowered and "contradict" in lowered:
            issues.append("PRD ambiguity: RQ and experiment design appear contradictory")
        return issues

    def detect_prd_gates(self, text: str) -> list[str]:
        issues: list[str] = []
        has_gate_table = bool(re.search(r"(Gate 调度表|Gate Schedule)", text))
        if not has_gate_table:
            issues.append("missing Gate Schedule table in PRD chapter 11")
            return issues
        gate_lines = [
            line for line in text.splitlines()
            if re.match(r"^\|\s*G\d+\s*\|", line) and "待填写" not in line
        ]
        if not gate_lines:
            issues.append("no concrete Gate definition found in Gate Schedule table (all gates still 【待填写】)")
            return issues
        for line in gate_lines:
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 5:
                continue
            gate_id = cols[0] if len(cols) > 0 else ""
            tasks_cell = cols[2] if len(cols) > 2 else ""
            pass_cond = cols[3] if len(cols) > 3 else ""
            if not re.search(r"T\d+", tasks_cell):
                issues.append(f"Gate {gate_id}: no task_id (T_XX) referenced in tasks column")
            if not pass_cond or len(pass_cond) < 8 or "待填写" in pass_cond:
                issues.append(f"Gate {gate_id}: pass_condition is missing or too vague")
        return issues

    def detect_spec(self) -> SpecStatus:
        spec_dir = self.research_dir / "spec"
        if not spec_dir.exists():
            return SpecStatus(status="missing", issues=["missing docs/research/spec"])
        missing = [relative for relative in SPEC_FILES if not (spec_dir / relative).exists()]
        if missing:
            return SpecStatus(status="missing", issues=[f"missing spec/{item}" for item in missing])
        validation = validate_research(self.research_dir, "spec-ready")
        return SpecStatus(status="ready" if validation.ok else "not_ready", issues=validation.issues)

    def detect_insights(self) -> InsightStatus:
        insights_dir = self.research_dir / "insights"
        pivots = self.open_markdown_files(insights_dir / "pivot_proposals")
        negatives = self.open_markdown_files(insights_dir / "negative_results")
        review_requests: list[str] = []
        audits = self.research_dir / "audits"
        if audits.exists():
            for request in sorted(audits.glob("*-prd-review/prd_change_request.md")):
                text = read_text(request)
                if not is_resolution_marked(text):
                    review_requests.append(self.rel(request))
        return InsightStatus(
            open_pivot_proposals=pivots,
            open_human_review_requests=review_requests,
            unresolved_negative_results=negatives,
        )

    def open_markdown_files(self, directory: Path) -> list[str]:
        if not directory.exists():
            return []
        result = []
        for path in sorted(directory.glob("*.md")):
            if path.name.startswith("."):
                continue
            text = read_text(path)
            if not is_resolution_marked(text):
                result.append(self.rel(path))
        return result

    def plan_dirs(self) -> list[Path]:
        plans_dir = self.research_dir / "plans"
        if not plans_dir.exists():
            return []
        return sorted(path for path in plans_dir.iterdir() if path.is_dir() and (path / "plan.yaml").exists())

    def detect_plan(self) -> PlanStatus:
        state = load_yaml(self.research_dir / "state.yaml")
        state_plans = state.get("plans", {}) if isinstance(state.get("plans"), dict) else {}
        active_name = state_plans.get("active") if isinstance(state_plans.get("active"), str) else None
        plan_dirs = self.plan_dirs()
        if active_name:
            active_dir = self.research_dir / "plans" / active_name
            if (active_dir / "plan.yaml").exists():
                return self.inspect_plan(active_dir)
        for plan_dir in reversed(plan_dirs):
            status = self.inspect_plan(plan_dir)
            if status.status in {"active", "blocked", "complete", "stale"}:
                return status
        return PlanStatus(status="missing")

    def inspect_plan(self, plan_dir: Path) -> PlanStatus:
        payload = load_yaml(plan_dir / "plan.yaml")
        status_value = str(payload.get("status", "")).strip().lower()
        final_summary = read_text(plan_dir / "final_summary.md") if (plan_dir / "final_summary.md").exists() else ""
        blocker_log = read_text(plan_dir / "blocker_log.md") if (plan_dir / "blocker_log.md").exists() else ""
        run_log = read_text(plan_dir / "run_log.md") if (plan_dir / "run_log.md").exists() else ""
        stale_findings = self.plan_stale_findings(plan_dir, payload)
        if stale_findings:
            return PlanStatus(active_plan=plan_dir.name, status="stale", stale_findings=stale_findings)
        if status_value in {"blocked", "failed"} or "PLAN_STATUS: BLOCKED" in blocker_log or "BLOCKER_UNRESOLVED: true" in blocker_log:
            return PlanStatus(active_plan=plan_dir.name, status="blocked")
        if status_value in {"complete", "completed"} or "PLAN_STATUS: COMPLETE" in final_summary:
            evidence_seen = "HARNESS_EVIDENCE:" in final_summary or "harness" in run_log.lower()
            if evidence_seen:
                return PlanStatus(active_plan=plan_dir.name, status="complete")
            return PlanStatus(
                active_plan=plan_dir.name,
                status="blocked",
                issues=["plan declares completion but lacks explicit harness evidence reference"],
            )
        return PlanStatus(active_plan=plan_dir.name, status="active")

    def plan_stale_findings(self, plan_dir: Path, payload: dict[str, Any]) -> list[str]:
        versions = payload.get("source_versions", {}) if isinstance(payload.get("source_versions"), dict) else {}
        findings = []
        current_spec_hash = hash_path(self.research_dir / "spec")
        current_prd_hash = hash_path(self.research_dir / "prd")
        current_paper_hash = hash_path(self.research_dir / "paper")
        if versions.get("spec_hash") and versions.get("spec_hash") != current_spec_hash:
            findings.append(f"active plan {plan_dir.name} has stale spec hash")
        if versions.get("prd_hash") and versions.get("prd_hash") != current_prd_hash:
            findings.append(f"active plan {plan_dir.name} has stale PRD hash")
        if versions.get("paper_hash") and versions.get("paper_hash") != current_paper_hash:
            findings.append(f"active plan {plan_dir.name} has stale paper hash")
        return findings

    def detect(self) -> Detection:
        if not self.research_dir.exists():
            return Detection(stage=STAGE_INIT, blocked=False)

        prd = self.detect_prd()
        if prd.status == "missing":
            return Detection(stage=STAGE_PRD_MISSING, blocked=False, prd=prd)
        if prd.status != "ready":
            return Detection(
                stage=STAGE_PRD_NOT_READY,
                blocked=True,
                block_reason="PRD is not ready or lacks human approval: " + "; ".join(prd.issues),
                prd=prd,
            )

        insights = self.detect_insights()
        if insights.blocked:
            return Detection(
                stage=STAGE_INSIGHT_REVIEW,
                blocked=True,
                block_reason="open insight, pivot, negative result, or PRD review request requires human decision",
                prd=prd,
                insights=insights,
            )

        spec = self.detect_spec()
        if spec.status == "missing":
            return Detection(stage=STAGE_SPEC_MISSING, blocked=False, prd=prd, spec=spec, insights=insights)
        if spec.status != "ready":
            return Detection(
                stage=STAGE_SPEC_NOT_READY,
                blocked=True,
                block_reason="Spec is not ready: " + "; ".join(spec.issues[:6]),
                prd=prd,
                spec=spec,
                insights=insights,
            )

        if self.args.force_audit:
            return Detection(
                stage=STAGE_AUDIT_REQUIRED,
                blocked=True,
                block_reason="force audit requested",
                prd=prd,
                spec=spec,
                insights=insights,
            )

        plan = self.detect_plan()
        if plan.status == "stale":
            return Detection(
                stage=STAGE_AUDIT_REQUIRED,
                blocked=True,
                block_reason="; ".join(plan.stale_findings),
                prd=prd,
                spec=spec,
                plan=plan,
                insights=insights,
            )
        if plan.status == "blocked":
            return Detection(
                stage=STAGE_PLAN_BLOCKED,
                blocked=True,
                block_reason="active plan is blocked: " + "; ".join(plan.issues or ["see blocker_log.md"]),
                prd=prd,
                spec=spec,
                plan=plan,
                insights=insights,
            )
        if plan.status == "complete":
            return Detection(stage=STAGE_PLAN_COMPLETE, prd=prd, spec=spec, plan=plan, insights=insights)
        if plan.status == "active":
            return Detection(stage=STAGE_EXECUTING, prd=prd, spec=spec, plan=plan, insights=insights)

        queue = self.load_queue()
        pending = [item for item in queue.get("queue", []) if isinstance(item, dict) and item.get("status") == "pending"]
        if not pending:
            derived = self.derive_queue_entries()
            if derived:
                return Detection(stage=STAGE_PLAN_MISSING, prd=prd, spec=spec, insights=insights)
            if not (self.research_dir / "paper" / "planned_paper.md").exists():
                return Detection(stage=STAGE_PAPER_UPDATE, prd=prd, spec=spec, insights=insights)
            return Detection(stage=STAGE_COMPLETE, prd=prd, spec=spec, insights=insights)
        return Detection(stage=STAGE_PLAN_MISSING, prd=prd, spec=spec, insights=insights)

    def load_queue(self) -> dict[str, Any]:
        if not self.queue_path.exists():
            return {"schema_version": SCHEMA_VERSION, "queue": []}
        payload = load_yaml(self.queue_path)
        if not isinstance(payload.get("queue"), list):
            payload["queue"] = []
        payload.setdefault("schema_version", SCHEMA_VERSION)
        return payload

    def derive_queue_entries(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        reproduction = load_yaml(self.research_dir / "spec" / "reproduction" / "reproduction_manifest.yaml")
        for target in reproduction.get("reproduction_targets", []) or []:
            if not isinstance(target, dict):
                continue
            baseline_id = str(target.get("baseline_id") or target.get("reproduction_id") or "baseline").lower().replace("_", "-")
            entries.append(
                {
                    "plan_type": "reproduction",
                    "purpose": f"reproduce-{baseline_id}",
                    "status": "pending",
                    "priority": 10,
                    "source_spec": "docs/research/spec/reproduction/reproduction_manifest.yaml",
                }
            )
        implementation = load_yaml(self.research_dir / "spec" / "implementation" / "implementation_task_graph.yaml")
        for task in implementation.get("tasks", []) or []:
            if not isinstance(task, dict):
                continue
            task_id = str(task.get("task_id") or "core-method")
            entries.append(
                {
                    "plan_type": "implementation",
                    "purpose": f"implement-{slugify(task_id)}",
                    "status": "pending",
                    "priority": 20,
                    "source_spec": "docs/research/spec/implementation/implementation_task_graph.yaml",
                }
            )
        experiments = load_yaml(self.research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
        for experiment in experiments.get("experiments", []) or []:
            if not isinstance(experiment, dict):
                continue
            experiment_id = str(experiment.get("experiment_id") or "experiment").lower()
            entries.append(
                {
                    "plan_type": "experiment",
                    "purpose": f"run-{experiment_id}-main-experiment",
                    "status": "pending",
                    "priority": 30,
                    "source_spec": "docs/research/spec/experiments/experiment_manifest.yaml",
                }
            )
        seen: set[tuple[str, str]] = set()
        unique_entries = []
        for entry in entries:
            key = (str(entry["plan_type"]), str(entry["purpose"]))
            if key in seen:
                continue
            seen.add(key)
            unique_entries.append(entry)
        return unique_entries

    def ensure_queue_from_spec(self) -> dict[str, Any]:
        queue = self.load_queue()
        existing = {
            (str(item.get("plan_type")), str(item.get("purpose")))
            for item in queue.get("queue", [])
            if isinstance(item, dict)
        }
        for entry in self.derive_queue_entries():
            key = (str(entry["plan_type"]), str(entry["purpose"]))
            if key not in existing:
                queue["queue"].append(entry)
        self.write_yaml(self.queue_path, queue)
        return queue

    def select_next_queue_item(self, queue: dict[str, Any]) -> dict[str, Any] | None:
        pending = [
            item
            for item in queue.get("queue", [])
            if isinstance(item, dict)
            and item.get("status") == "pending"
            and (not self.args.track or item.get("plan_type") == self.args.track)
        ]
        pending.sort(key=lambda item: (int(item.get("priority", 100)), str(item.get("purpose", ""))))
        return pending[0] if pending else None

    def update_queue_item(self, purpose: str, status: str, plan_id: str | None = None) -> None:
        queue = self.load_queue()
        for item in queue.get("queue", []):
            if isinstance(item, dict) and item.get("purpose") == purpose:
                item["status"] = status
                if plan_id:
                    item["plan_id"] = plan_id
        self.write_yaml(self.queue_path, queue)

    def write_state(self, detection: Detection) -> None:
        previous = load_yaml(self.research_dir / "state.yaml")
        previous_stage = None
        if isinstance(previous.get("project_status"), dict):
            previous_stage = previous["project_status"].get("current_stage")
        queue = self.load_queue()
        queue_items = [item for item in queue.get("queue", []) if isinstance(item, dict)]
        completed = sorted(
            {
                str(item.get("plan_id") or item.get("purpose"))
                for item in queue_items
                if item.get("status") in {"complete", "completed"}
            }
            | {plan.name for plan in self.plan_dirs() if self.inspect_plan(plan).status == "complete"}
        )
        pending = [str(item.get("purpose")) for item in queue_items if item.get("status") == "pending"]
        latest_audit = self.latest_audit_dir()
        state_drift = []
        if previous_stage and previous_stage != detection.stage:
            state_drift.append(f"state current_stage updated from {previous_stage} to {detection.stage} after filesystem recomputation")
        state = {
            "schema_version": SCHEMA_VERSION,
            "project_status": {
                "current_stage": detection.stage,
                "active_plan": detection.plan.active_plan,
                "blocked": detection.blocked,
                "block_reason": detection.block_reason,
                "last_audit": self.rel(latest_audit) if latest_audit else None,
                "last_updated": self.date,
            },
            "prd": {
                "path": "docs/research/prd/research_prd.md",
                "status": detection.prd.status,
                "human_approved": detection.prd.human_approved,
                "version": None,
                "hash": hash_path(self.research_dir / "prd" / "research_prd.md"),
                "issues": detection.prd.issues,
            },
            "spec": {
                "path": "docs/research/spec/",
                "status": detection.spec.status,
                "version": None,
                "hash": hash_path(self.research_dir / "spec"),
                "issues": detection.spec.issues[:20],
            },
            "paper": {
                "path": "docs/research/paper/planned_paper.md",
                "status": "present" if (self.research_dir / "paper" / "planned_paper.md").exists() else "missing",
                "hash": hash_path(self.research_dir / "paper"),
            },
            "plans": {
                "active": detection.plan.active_plan,
                "completed": completed,
                "pending": pending,
            },
            "insights": {
                "open_pivot_proposals": detection.insights.open_pivot_proposals,
                "open_human_review_requests": detection.insights.open_human_review_requests,
                "unresolved_negative_results": detection.insights.unresolved_negative_results,
            },
        }
        if state_drift:
            state["state_drift_findings"] = state_drift
        self.write_yaml(self.research_dir / "state.yaml", state)

    def latest_audit_dir(self) -> Path | None:
        audits_dir = self.research_dir / "audits"
        if not audits_dir.exists():
            return None
        audit_dirs = sorted(path for path in audits_dir.iterdir() if path.is_dir() and path.name.endswith("-audit"))
        return audit_dirs[-1] if audit_dirs else None

    def write_prd_review_request(self, issues: list[str]) -> Path:
        review_dir = self.research_dir / "audits" / f"{self.date}-prd-review"
        issue_lines = "\n".join(f"- {issue}" for issue in issues)
        self.write_text(
            review_dir / "prd_change_request.md",
            "\n".join(
                [
                    "# PRD Change Request",
                    "",
                    "Automation stopped because the next execution step would change or invent PRD-level research decisions.",
                    "",
                    "## Blocking Issues",
                    issue_lines or "- Unspecified PRD ambiguity.",
                    "",
                    "## Human Decision Required",
                    "Approve / reject / revise the PRD-level choice before `/research` continues.",
                    "",
                    "HUMAN_DECISION: PENDING",
                    "",
                ]
            ),
        )
        self.write_text(
            review_dir / "repair_plan.md",
            "\n".join(
                [
                    "# PRD Review Repair Plan",
                    "",
                    "1. Update `docs/research/prd/research_prd.md` with concrete dataset, baseline, metric, RQ, hypothesis, or claim decisions.",
                    "2. Keep `PRD_STATUS: HUMAN_APPROVED` only after the revised PRD is reviewed.",
                    "3. Re-run `/research` to compile or repair `docs/research/spec/`.",
                    "",
                ]
            ),
        )
        return review_dir

    def write_audit_with_findings(self, findings: list[str]) -> Path:
        if not self.args.dry_run:
            audit_dir = generate_audit(self.research_dir, self.date, force=True)
        else:
            audit_dir = self.research_dir / "audits" / f"{self.date}-audit"
            self.dry_run_writes.append(self.rel(audit_dir))
        finding_payload = {
            "schema_version": SCHEMA_VERSION,
            "findings": [
                {
                    "severity": "hard_blocker",
                    "finding": finding,
                    "required_action": "repair before continuing automation",
                }
                for finding in findings
            ],
        }
        self.write_yaml(audit_dir / "drift_findings.yaml", finding_payload)
        self.write_text(
            audit_dir / "repair_plan.md",
            "# Repair Plan\n\n## Must fix before execution（执行失败）\n\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\n## Recommended Action\n\nRegenerate or repair the active plan after PRD/Spec/Paper hashes are aligned.\n",
        )
        return audit_dir

    def write_spec_feedback(self, plan_id: str) -> Path:
        feedback_dir = self.research_dir / "spec" / "feedback"
        if not (feedback_dir / "README.md").exists():
            self.write_text(
                feedback_dir / "README.md",
                "# Spec Feedback\n\nReusable execution lessons from dated plans. Do not store PRD-level changes here.\n",
            )
        feedback_path = feedback_dir / f"{plan_id}_lessons.md"
        self.write_text(
            feedback_path,
            "\n".join(
                [
                    f"# {plan_id} Lessons",
                    "",
                    "## Environment",
                    "- No environment fact is inferred by the controller. Add concrete versions only from recorded logs.",
                    "",
                    "## Harness Notes",
                    "- The controller accepted completion only because the plan declared `PLAN_STATUS: COMPLETE` and referenced harness evidence.",
                    "- Re-run or inspect the declared harness logs before promoting any paper claim.",
                    "",
                    "## Output Conversion",
                    "- No converter lesson was inferred automatically.",
                    "",
                    "## Future Plan Advice",
                    "- Keep stdout/stderr paths and artifact hashes explicit in `run_log.md` and `final_summary.md`.",
                    "- Do not treat smoke or mock outputs as research evidence.",
                    "",
                ]
            ),
        )
        return feedback_path

    def append_insight_entry(self, plan_id: str, status: str) -> None:
        insight_log = self.research_dir / "insights" / "insight_log.md"
        if not insight_log.exists():
            self.write_text(insight_log, "# Insight Log\n\n")
        existing = read_text(insight_log) if insight_log.exists() else "# Insight Log\n\n"
        entry = "\n".join(
            [
                "",
                f"## Insight Log Entry - {self.date} - {plan_id}",
                "",
                "## Source",
                f"- Plan: docs/research/plans/{plan_id}/",
                "- Experiment / Reproduction / Task: see linked `plan.yaml`.",
                "- Harness: see linked `plan.yaml`.",
                "- Artifacts: see `run_log.md` and `final_summary.md`.",
                "",
                "## Observation",
                f"The plan is currently classified as `{status}` by explicit plan logs. The controller did not fabricate or execute missing harness output.",
                "",
                "## Expected Behavior from PRD",
                "The PRD expects declared gates to be completed only through harness evidence and artifact records.",
                "",
                "## Mismatch / Surprise",
                "No research-level mismatch is inferred automatically. Human review should inspect the actual run logs.",
                "",
                "## Possible Explanation",
                "This entry records controller-level reflection, not an empirical result.",
                "",
                "## Research Value",
                "Execution bookkeeping only unless the underlying logs document a negative result, anomaly, or falsification.",
                "",
                "## Recommended Action",
                "- continue original plan if harness evidence is sufficient",
                "- repair execution or spec if logs are incomplete",
                "- request human PRD review if logs challenge a core hypothesis",
                "",
                "## Confidence",
                "medium",
                "",
            ]
        )
        self.write_text(insight_log, existing.rstrip() + "\n" + entry)

    def write_plan_next_step_prompt(self, plan_id: str) -> None:
        current_state = self.research_dir / "plans" / plan_id / "current_state.md"
        existing = read_text(current_state) if current_state.exists() else "# 当前状态\n\n"
        note = "\n".join(
            [
                "",
                f"## /research controller update - {self.date}",
                "",
                "当前计划仍未完成。统一控制器不会伪造 harness 输出。",
                "",
                "下一步：读取 `plan.yaml` 中的最早 gate，运行声明 harness，保存 stdout/stderr、artifact hash，并更新 `run_log.md`、`blocker_log.md`、`decision_log.md` 与 `final_summary.md`。",
                "",
                "如该 gate 需要专业 worker，按 `ai_loop_prompt.md` 的 Subagent Dispatch 规则委派 Claude Code 项目级 subagent；`/research` 控制器仍负责 state、gate 和 promotion。",
                "",
            ]
        )
        if note not in existing:
            self.write_text(current_state, existing.rstrip() + "\n" + note)
        self.regenerate_epoch_next_action()

    def regenerate_epoch_next_action(self) -> None:
        current_epoch_file = self.research_dir / "CURRENT"
        if not current_epoch_file.exists():
            return
        version = read_text(current_epoch_file).strip()
        epoch_dir = self.research_dir / version
        task_queue_path = epoch_dir / "TASK_QUEUE.yaml"
        if not task_queue_path.exists():
            return
        if not self.args.dry_run:
            write_next_action_from_task_queue(epoch_dir, version)
        else:
            self.dry_run_writes.append(
                str(epoch_dir / "NEXT_ACTION.md") + " (regenerated from TASK_QUEUE.yaml)"
            )

    def advance_once(self, detection: Detection) -> bool:
        """Advance one deterministic step. Return True when execution should stop."""
        if detection.stage in {STAGE_INIT, STAGE_PRD_MISSING}:
            if not self.args.dry_run:
                init_research_workspace(
                    self.repo,
                    title=self.repo.name or "Research Project",
                    purpose="minimum viable research goal",
                    force=False,
                )
            self.ensure_state_files()
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "initialized_research_workspace", "stage_before": detection.stage, "stage_after": refreshed.stage})
            return True

        self.ensure_state_files()

        if detection.stage == STAGE_PRD_NOT_READY:
            self.write_state(detection)
            self.actions.append({"action": "blocked_for_prd_readiness", "issues": detection.prd.issues})
            return True

        if detection.stage == STAGE_INSIGHT_REVIEW:
            self.write_audit_with_findings([detection.block_reason or "open insight review item"])
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "blocked_for_human_insight_review", "stage": refreshed.stage})
            return True

        if detection.stage == STAGE_SPEC_MISSING:
            if detection.prd.ambiguity_issues:
                review_dir = self.write_prd_review_request(detection.prd.ambiguity_issues)
                refreshed = self.detect()
                self.write_state(refreshed)
                self.actions.append({"action": "wrote_prd_review_request", "path": self.rel(review_dir)})
                return True
            if not self.args.dry_run:
                init_spec_scaffold(self.research_dir, force=False)
            self.write_audit_with_findings(["spec scaffold generated or repaired; validate remaining PRD-to-Spec gaps before execution"])
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "generated_spec_scaffold", "stage_after": refreshed.stage})
            return True

        if detection.stage == STAGE_SPEC_NOT_READY:
            if detection.prd.ambiguity_issues:
                review_dir = self.write_prd_review_request(detection.prd.ambiguity_issues)
                refreshed = self.detect()
                self.write_state(refreshed)
                self.actions.append({"action": "wrote_prd_review_request", "path": self.rel(review_dir)})
                return True
            if not self.args.dry_run:
                init_spec_scaffold(self.research_dir, force=False)
            self.write_audit_with_findings(detection.spec.issues[:10] or ["spec repair attempted"])
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "attempted_spec_repair", "remaining_issues": refreshed.spec.issues[:10]})
            return True

        if detection.stage == STAGE_PLAN_MISSING:
            queue = self.ensure_queue_from_spec()
            selected = self.select_next_queue_item(queue)
            if not selected:
                refreshed = self.detect()
                self.write_state(refreshed)
                self.actions.append({"action": "no_pending_plan"})
                return True
            purpose = str(selected["purpose"])
            track = str(selected["plan_type"])
            if not self.args.dry_run:
                plan_dir = generate_plan(
                    research_dir=self.research_dir,
                    date=self.date,
                    purpose=purpose,
                    track=track,
                    gate=self.args.gate or None,
                    target="codex",
                    force=False,
                )
                plan_yaml = load_yaml(plan_dir / "plan.yaml")
                plan_yaml["status"] = "active"
                plan_yaml["queue_source"] = selected.get("source_spec")
                write_yaml_file(plan_dir / "plan.yaml", plan_yaml)
                plan_id = plan_dir.name
            else:
                plan_id = f"{self.date}-{slugify(purpose)}"
                self.dry_run_writes.append(self.rel(self.research_dir / "plans" / plan_id))
            self.update_queue_item(purpose, "active", plan_id)
            self.regenerate_epoch_next_action()
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "generated_next_plan", "plan_id": plan_id, "track": track})
            return True

        if detection.stage == STAGE_EXECUTING and detection.plan.active_plan:
            self.write_plan_next_step_prompt(detection.plan.active_plan)
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "wrote_plan_execution_prompt", "plan_id": detection.plan.active_plan})
            return True

        if detection.stage == STAGE_PLAN_BLOCKED and detection.plan.active_plan:
            self.append_insight_entry(detection.plan.active_plan, "blocked")
            self.write_audit_with_findings([detection.block_reason or "active plan blocked"])
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "wrote_blocked_plan_insight_and_audit", "plan_id": detection.plan.active_plan})
            return True

        if detection.stage == STAGE_PLAN_COMPLETE and detection.plan.active_plan:
            plan_id = detection.plan.active_plan
            self.write_spec_feedback(plan_id)
            self.append_insight_entry(plan_id, "complete")
            if not self.args.dry_run:
                generate_audit(self.research_dir, self.date, force=True)
            else:
                self.dry_run_writes.append(self.rel(self.research_dir / "audits" / f"{self.date}-audit"))
            plan_yaml_path = self.research_dir / "plans" / plan_id / "plan.yaml"
            plan_yaml = load_yaml(plan_yaml_path)
            purpose = str(plan_yaml.get("purpose", "")).replace("执行目标：", "").strip()
            plan_yaml["status"] = "complete"
            self.write_yaml(plan_yaml_path, plan_yaml)
            if purpose:
                self.update_queue_item(purpose, "complete", plan_id)
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "completed_plan_feedback_and_audit", "plan_id": plan_id})
            return True

        if detection.stage == STAGE_AUDIT_REQUIRED:
            self.write_audit_with_findings(detection.plan.stale_findings or [detection.block_reason or "audit required"])
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "wrote_blocking_audit", "findings": detection.plan.stale_findings})
            return True

        if detection.stage == STAGE_PAPER_UPDATE:
            if not self.args.dry_run:
                generate_paper(self.research_dir, force=False)
            refreshed = self.detect()
            self.write_state(refreshed)
            self.actions.append({"action": "generated_missing_paper_layer"})
            return True

        self.write_state(detection)
        self.actions.append({"action": "no_action", "stage": detection.stage})
        return True

    def run(self) -> dict[str, Any]:
        max_steps = 1 if self.args.once else max(1, int(self.args.max_steps))
        initial = self.detect()
        current = initial
        for _ in range(max_steps):
            stop = self.advance_once(current)
            current = self.detect() if self.research_dir.exists() else current
            if stop or current.blocked:
                break
        final = self.detect() if self.research_dir.exists() else current
        if self.research_dir.exists() and not self.args.dry_run:
            self.write_state(final)
        return {
            "workspace": self.rel(self.research_dir),
            "initial_stage": initial.stage,
            "final_stage": final.stage,
            "blocked": final.blocked,
            "block_reason": final.block_reason,
            "actions": self.actions,
            "dry_run_writes": self.dry_run_writes,
            "execution_mode": "deterministic_file_controller",
            "execution_backend": {
                "mode": self.args.executor,
                "implemented": self.args.executor == "prompt-only",
                "note": "Only prompt-only is implemented; local-shell, codex, and hermes are reserved backend slots.",
            },
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified deterministic /research workflow controller.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--workspace", default="docs/research", help="Research workspace path, absolute or relative to repo.")
    parser.add_argument("--once", action="store_true", help="Run one controller step.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and report intended writes without mutating files.")
    parser.add_argument("--max-steps", type=int, default=1, help="Maximum deterministic controller steps.")
    parser.add_argument("--track", choices=["reproduction", "implementation", "experiment", "paper-update", "insight-feedback"], default="")
    parser.add_argument("--gate", default="", help="Optional target gate for generated plan.")
    parser.add_argument("--force-audit", action="store_true", help="Force audit generation before continuing.")
    parser.add_argument(
        "--executor",
        choices=["prompt-only", "local-shell", "codex", "hermes"],
        default="prompt-only",
        help="Execution backend slot. Only prompt-only is implemented in this controller version.",
    )
    parser.add_argument("--no-execute", action="store_true", help="Do not run harnesses; retained for CLI compatibility.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    parser.add_argument("--date", default="", help="Override date for generated plan/audit directories.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    controller = ResearchLoop(args)
    result = controller.run()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[research] {result['initial_stage']} -> {result['final_stage']}")
        for action in result["actions"]:
            print(f"[research] action: {action['action']}")
        if result["blocked"]:
            print(f"[research] blocked: {result['block_reason']}")
        print("[research] execution_mode: deterministic_file_controller")
        print(f"[research] execution_backend: {result['execution_backend']['mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
