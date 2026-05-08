#!/usr/bin/env python3
"""Validate report execution manifests without external schema tooling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"
FORBIDDEN_FINAL_EVIDENCE_KINDS = {"mock", "toy", "synthetic", "cached", "stub", "proxy"}
FINAL_EVIDENCE_ROLES = {
    "final",
    "research_claim",
    "benchmark",
    "baseline",
    "ablation",
    "paper_table",
    "paper_figure",
    "go_no_go",
}


@dataclass(frozen=True)
class ManifestIssue:
    severity: str
    category: str
    message: str
    location: str | None = None


@dataclass(frozen=True)
class ManifestValidationResult:
    report_dir: Path
    report_type: str
    issues: list[ManifestIssue]
    documents: dict[str, Any]

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def execution_ready(self) -> bool:
        return self.valid and not any(issue.severity == "readiness" for issue in self.issues)

    @property
    def task_order(self) -> list[dict[str, Any]]:
        task_graph = self.documents.get("task_graph") or {}
        tasks_by_id = {
            task.get("task_id"): task
            for task in task_graph.get("tasks", [])
            if isinstance(task, dict) and task.get("task_id")
        }
        ordered: list[dict[str, Any]] = []
        seen: set[str] = set()
        for gate in task_graph.get("gates", []):
            if not isinstance(gate, dict):
                continue
            for task_id in _as_list(gate.get("tasks")):
                task = tasks_by_id.get(task_id)
                if task and task_id not in seen:
                    ordered.append(task)
                    seen.add(task_id)
        for task_id, task in tasks_by_id.items():
            if task_id not in seen:
                ordered.append(task)
        return ordered


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _read_yaml(path: Path, issues: list[ManifestIssue], key: str) -> Any:
    if not path.exists():
        issues.append(ManifestIssue("error", "missing", f"缺少 execution manifest：`{path.name}`。", path.as_posix()))
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        issues.append(ManifestIssue("error", "yaml", f"`{path.name}` 不是合法 YAML：{exc}", path.as_posix()))
        return {}
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        issues.append(ManifestIssue("error", "schema", f"`{path.name}` 顶层必须是 mapping。", path.as_posix()))
        return {}
    if str(payload.get("schema_version", "")).strip() != SCHEMA_VERSION:
        issues.append(
            ManifestIssue(
                "error",
                "schema",
                f"`{path.name}` 缺少 `schema_version: \"{SCHEMA_VERSION}\"`。",
                path.as_posix(),
            )
        )
    return payload


def _duplicate_ids(items: list[dict[str, Any]], id_key: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_id = str(item.get(id_key, "")).strip()
        if not item_id:
            continue
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    return duplicates


def _validate_list(payload: dict[str, Any], key: str, issues: list[ManifestIssue], location: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        issues.append(ManifestIssue("error", "schema", f"`{location}` 中 `{key}` 必须是 list。", location))
        return []
    dict_items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            issues.append(ManifestIssue("error", "schema", f"`{location}` 中 `{key}[{index}]` 必须是 mapping。", location))
            continue
        dict_items.append(item)
    return dict_items


def _has_command_or_blocker(harness: dict[str, Any]) -> bool:
    command = harness.get("command")
    blocker = harness.get("blocker") or harness.get("blocked_by")
    if isinstance(command, str) and command.strip():
        return True
    if isinstance(command, list) and any(str(item).strip() for item in command):
        return True
    if isinstance(blocker, str) and blocker.strip():
        return True
    if isinstance(blocker, dict) and blocker:
        return True
    return False


def _evidence_source_kind(item: dict[str, Any]) -> str:
    for key in ("source_kind", "evidence_kind", "kind", "provenance"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def _evidence_roles(item: dict[str, Any]) -> set[str]:
    roles = {str(role).strip().lower() for role in _as_list(item.get("role")) if str(role).strip()}
    if item.get("final") is True:
        roles.add("final")
    if item.get("claim_id"):
        roles.add("research_claim")
    return roles


def validate_execution_manifests(report_dir: Path | str) -> ManifestValidationResult:
    report_dir = Path(report_dir).resolve()
    issues: list[ManifestIssue] = []

    report_manifest = _read_yaml(report_dir / "report.manifest.yaml", issues, "report")
    report_type = str(report_manifest.get("report_type", "")).strip()
    if report_manifest and report_type not in {"research-prd", "engineering-prd"}:
        issues.append(
            ManifestIssue(
                "error",
                "schema",
                "`report.manifest.yaml` 的 `report_type` 必须是 research-prd 或 engineering-prd。",
                (report_dir / "report.manifest.yaml").as_posix(),
            )
        )

    task_graph = _read_yaml(report_dir / "tasks" / "task_graph.yaml", issues, "task_graph")
    harness_manifest = _read_yaml(report_dir / "harness" / "harness.yaml", issues, "harness")
    evidence_manifest = _read_yaml(report_dir / "evidence" / "evidence_manifest.yaml", issues, "evidence")
    experiment_manifest: dict[str, Any] = {}
    if report_type == "research-prd":
        experiment_manifest = _read_yaml(report_dir / "experiments" / "experiment_manifest.yaml", issues, "experiments")

    tasks = _validate_list(task_graph, "tasks", issues, "tasks/task_graph.yaml") if task_graph else []
    gates = _validate_list(task_graph, "gates", issues, "tasks/task_graph.yaml") if task_graph else []
    harnesses = _validate_list(harness_manifest, "harnesses", issues, "harness/harness.yaml") if harness_manifest else []
    evidence_items = (
        _validate_list(evidence_manifest, "evidence_items", issues, "evidence/evidence_manifest.yaml")
        if evidence_manifest
        else []
    )
    claims = _validate_list(experiment_manifest, "claims", issues, "experiments/experiment_manifest.yaml") if experiment_manifest else []
    experiments = (
        _validate_list(experiment_manifest, "experiments", issues, "experiments/experiment_manifest.yaml")
        if experiment_manifest
        else []
    )

    task_ids = {str(task.get("task_id", "")).strip() for task in tasks if str(task.get("task_id", "")).strip()}
    harness_ids = {str(harness.get("harness_id", "")).strip() for harness in harnesses if str(harness.get("harness_id", "")).strip()}
    experiment_ids = {
        str(experiment.get("experiment_id", "")).strip()
        for experiment in experiments
        if str(experiment.get("experiment_id", "")).strip()
    }

    for id_key, items, location in [
        ("task_id", tasks, "tasks/task_graph.yaml"),
        ("gate_id", gates, "tasks/task_graph.yaml"),
        ("harness_id", harnesses, "harness/harness.yaml"),
        ("evidence_id", evidence_items, "evidence/evidence_manifest.yaml"),
        ("experiment_id", experiments, "experiments/experiment_manifest.yaml"),
        ("claim_id", claims, "experiments/experiment_manifest.yaml"),
    ]:
        for duplicate in _duplicate_ids(items, id_key):
            issues.append(ManifestIssue("error", "schema", f"`{id_key}` 重复：`{duplicate}`。", location))

    if task_graph and not tasks:
        issues.append(
            ManifestIssue(
                "readiness",
                "execution-readiness",
                "`tasks/task_graph.yaml` 仍为空；需要通过 `report-update --mode deep-spec` 写入真实 task contract。",
                (report_dir / "tasks" / "task_graph.yaml").as_posix(),
            )
        )
    if harness_manifest and not harnesses:
        issues.append(
            ManifestIssue(
                "readiness",
                "execution-readiness",
                "`harness/harness.yaml` 仍为空；每个 task 必须绑定至少一个 harness。",
                (report_dir / "harness" / "harness.yaml").as_posix(),
            )
        )

    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        if not task_id:
            issues.append(ManifestIssue("error", "schema", "task 缺少 `task_id`。", "tasks/task_graph.yaml"))
            continue
        task_harnesses = [str(item).strip() for item in _as_list(task.get("harnesses")) if str(item).strip()]
        if not task_harnesses:
            issues.append(
                ManifestIssue(
                    "readiness",
                    "execution-readiness",
                    f"task `{task_id}` 没有绑定 harness；不能进入 implementation goal。",
                    "tasks/task_graph.yaml",
                )
            )
        for harness_id in task_harnesses:
            if harness_id not in harness_ids:
                issues.append(
                    ManifestIssue(
                        "error",
                        "schema",
                        f"task `{task_id}` 引用了不存在的 harness `{harness_id}`。",
                        "tasks/task_graph.yaml",
                    )
                )
        for dep_id in [str(item).strip() for item in _as_list(task.get("depends_on")) if str(item).strip()]:
            if dep_id not in task_ids:
                issues.append(
                    ManifestIssue("error", "schema", f"task `{task_id}` 依赖不存在的 task `{dep_id}`。", "tasks/task_graph.yaml")
                )

    for gate in gates:
        gate_id = str(gate.get("gate_id", "")).strip()
        if not gate_id:
            issues.append(ManifestIssue("error", "schema", "gate 缺少 `gate_id`。", "tasks/task_graph.yaml"))
            continue
        for task_id in [str(item).strip() for item in _as_list(gate.get("tasks")) if str(item).strip()]:
            if task_id not in task_ids:
                issues.append(ManifestIssue("error", "schema", f"gate `{gate_id}` 引用了不存在的 task `{task_id}`。", "tasks/task_graph.yaml"))

    for harness in harnesses:
        harness_id = str(harness.get("harness_id", "")).strip()
        if not harness_id:
            issues.append(ManifestIssue("error", "schema", "harness 缺少 `harness_id`。", "harness/harness.yaml"))
            continue
        if not _has_command_or_blocker(harness):
            issues.append(
                ManifestIssue(
                    "readiness",
                    "execution-readiness",
                    f"harness `{harness_id}` 缺少 command 或显式 blocker。",
                    "harness/harness.yaml",
                )
            )

    for item in evidence_items:
        evidence_id = str(item.get("evidence_id", "")).strip() or "<missing evidence_id>"
        source_kind = _evidence_source_kind(item)
        roles = _evidence_roles(item)
        if roles & FINAL_EVIDENCE_ROLES and source_kind in FORBIDDEN_FINAL_EVIDENCE_KINDS:
            issues.append(
                ManifestIssue(
                    "error",
                    "academic-integrity",
                    f"evidence `{evidence_id}` 用 `{source_kind}` 标记 final/research evidence；这不能作为最终或科研 claim 证据。",
                    "evidence/evidence_manifest.yaml",
                )
            )

    if report_type == "research-prd":
        for claim in claims:
            claim_id = str(claim.get("claim_id", "")).strip()
            if not claim_id:
                issues.append(ManifestIssue("error", "schema", "claim 缺少 `claim_id`。", "experiments/experiment_manifest.yaml"))
                continue
            linked_experiments = [
                str(item).strip()
                for item in _as_list(claim.get("experiment_ids") or claim.get("experiments") or claim.get("experiment_id"))
                if str(item).strip()
            ]
            if not linked_experiments:
                issues.append(
                    ManifestIssue(
                        "error",
                        "schema",
                        f"research claim `{claim_id}` 没有关联 experiment；不能作为可执行科研 claim。",
                        "experiments/experiment_manifest.yaml",
                    )
                )
            for experiment_id in linked_experiments:
                if experiment_id not in experiment_ids:
                    issues.append(
                        ManifestIssue(
                            "error",
                            "schema",
                            f"research claim `{claim_id}` 引用了不存在的 experiment `{experiment_id}`。",
                            "experiments/experiment_manifest.yaml",
                        )
                    )

    return ManifestValidationResult(
        report_dir=report_dir,
        report_type=report_type,
        issues=issues,
        documents={
            "report": report_manifest,
            "task_graph": task_graph,
            "harness": harness_manifest,
            "evidence": evidence_manifest,
            "experiments": experiment_manifest,
        },
    )
