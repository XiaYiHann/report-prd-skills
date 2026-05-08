#!/usr/bin/env python3
"""Generate a Codex Goal prompt from a PRD report and repo scan."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "report" / "_shared" / "scripts"
if SHARED_SCRIPT_DIR.exists():
    sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from manifest_validator import ManifestValidationResult, validate_execution_manifests, validate_spec_manifests


DEFAULT_KEYWORDS = (
    "Phase",
    "Milestone",
    "Recommended Execution Order",
    "下一步",
    "验收",
    "门禁",
    "gate",
    "acceptance",
    "baseline",
    "ablation",
)


@dataclass(frozen=True)
class ScanResult:
    git_status: str
    git_status_truncated: bool
    tracked_relevant_files: list[str]
    missing_paths: list[str]
    present_paths: list[str]
    test_files: list[str]
    script_files: list[str]


@dataclass(frozen=True)
class ReportExtraction:
    title: str
    objective_lines: list[str]
    gate_lines: list[str]
    constraint_lines: list[str]
    artifact_lines: list[str]
    path_hints: list[str]


@dataclass(frozen=True)
class ManifestInputs:
    report_dir: Path | None
    validation: ManifestValidationResult | None
    resolution_issues: list[str]

    @property
    def execution_ready(self) -> bool:
        return self.validation is not None and self.validation.execution_ready and not self.resolution_issues


@dataclass(frozen=True)
class ArtifactInputs:
    workspace_dir: Path | None
    main_dir: Path | None
    paper_dir: Path | None
    spec_dir: Path | None
    spec_validation: ManifestValidationResult | None
    resolution_issues: list[str]
    alignment_issues: list[str]

    @property
    def found(self) -> bool:
        return self.workspace_dir is not None

    @property
    def spec_ready(self) -> bool:
        return self.spec_validation is not None and self.spec_validation.execution_ready

    @property
    def alignment_ready(self) -> bool:
        return self.found and not self.resolution_issues and not self.alignment_issues

    @property
    def implementation_ready(self) -> bool:
        return self.spec_ready and self.alignment_ready


def run_command(repo: Path, args: list[str]) -> str:
    try:
        completed = subprocess.run(
            args,
            cwd=repo,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return f"[command unavailable: {' '.join(args)}: {exc}]"
    output = completed.stdout.strip()
    if completed.returncode != 0 and completed.stderr.strip():
        return f"{output}\n[stderr]\n{completed.stderr.strip()}".strip()
    return output


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(errors="replace").splitlines()


def extract_report_evidence(report: Path, max_lines: int) -> list[str]:
    lines = read_lines(report)
    selected: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        if any(keyword.lower() in line.lower() for keyword in DEFAULT_KEYWORDS):
            selected.append((idx, line.strip()))
    if not selected:
        selected = [(idx, line.strip()) for idx, line in enumerate(lines[:max_lines], start=1)]
    selected = selected[:max_lines]
    return [f"{report.as_posix()}:{idx}: {line}" for idx, line in selected if line]


def clean_report_line(line: str, max_chars: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", line).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 3]}..."


def select_lines(lines: list[str], patterns: tuple[str, ...], limit: int) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for idx, line in enumerate(lines, start=1):
        stripped = clean_report_line(line)
        if not stripped or stripped in seen:
            continue
        haystack = stripped.lower()
        if any(pattern.lower() in haystack for pattern in patterns):
            selected.append(f"{idx}: {stripped}")
            seen.add(stripped)
        if len(selected) >= limit:
            break
    return selected


def extract_path_hints(lines: list[str], limit: int) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for value in re.findall(r"`([^`]+)`", line):
            candidate = value.strip()
            if not candidate or candidate in seen:
                continue
            looks_like_path = (
                "/" in candidate
                or candidate.endswith((".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".parquet"))
                or candidate.startswith(("scripts", "src", "tests", "docs", "cigr", "app", "packages"))
            )
            if looks_like_path:
                hints.append(candidate)
                seen.add(candidate)
            if len(hints) >= limit:
                return hints
    return hints


def extract_report_context(report: Path) -> ReportExtraction:
    lines = read_lines(report)
    title = next((line.lstrip("# ").strip() for line in lines if line.startswith("# ")), report.stem)
    objective_lines = select_lines(
        lines,
        ("当前应", "目标", "mission", "主线", "下一步应", "最短正确路径", "answer", "contribution", "贡献"),
        6,
    )
    gate_lines = select_lines(
        lines,
        ("gate", "门禁", "里程碑", "milestone", "phase", "s0", "s1", "s2", "m1", "m2", "m3", "验收"),
        12,
    )
    constraint_lines = select_lines(
        lines,
        ("必须", "不得", "禁止", "只允许", "不能", "stop rule", "non-goal", "约束", "边界"),
        10,
    )
    artifact_lines = select_lines(
        lines,
        ("artifact", "产出", "输出", "manifest", "parquet", "json", "验证", "test", "命令", "self-check"),
        10,
    )
    return ReportExtraction(
        title=title,
        objective_lines=objective_lines,
        gate_lines=gate_lines,
        constraint_lines=constraint_lines,
        artifact_lines=artifact_lines,
        path_hints=extract_path_hints(lines, 40),
    )


def find_files(repo: Path) -> list[str]:
    output = run_command(repo, ["git", "ls-files"])
    if output.startswith("[command unavailable") or "[stderr]" in output:
        files: list[str] = []
        for root, dirs, names in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".venv", "node_modules"}]
            for name in names:
                rel = Path(root, name).relative_to(repo).as_posix()
                files.append(rel)
        return sorted(files)
    return [line for line in output.splitlines() if line.strip()]


def scan_repo(repo: Path, report_hints: list[str]) -> ScanResult:
    files = find_files(repo)
    term_set = {"report", "eval", "test", "tests", "script", "scripts", "artifact", "artifacts"}
    for path in report_hints:
        for token in re.split(r"[/_.:-]+", path.lower()):
            if len(token) > 2 and not token.isdigit():
                term_set.add(token)
    relevant_terms = tuple(sorted(term_set))
    relevant = [path for path in files if any(term in path.lower() for term in relevant_terms)]
    path_hints = [
        path for path in report_hints
        if not Path(path).is_absolute() and not re.search(r"\s", path) and not path.startswith("-")
    ]
    present = [path for path in path_hints if (repo / path).exists()]
    missing = [path for path in path_hints if not (repo / path).exists()]
    tests = [path for path in files if path.startswith("tests/") or "/tests/" in path or path.endswith("_test.py")]
    scripts = [path for path in files if path.startswith("scripts/")]
    git_status, git_status_truncated = truncate_lines(
        run_command(repo, ["git", "status", "--short"]),
        max_lines=80,
    )
    return ScanResult(
        git_status=git_status,
        git_status_truncated=git_status_truncated,
        tracked_relevant_files=relevant[:120],
        missing_paths=missing,
        present_paths=present,
        test_files=tests[:80],
        script_files=scripts[:80],
    )


def format_list(items: list[str], empty: str = "none") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- `{item}`" for item in items)


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def format_plain_list(items: list[str], empty: str = "未从报告中抽取到明确条目。") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def resolve_report_workspace(repo: Path, report: Path) -> tuple[Path | None, list[str]]:
    candidates: list[Path] = []
    issues: list[str] = []

    if (report.parent / "report.manifest.yaml").exists():
        candidates.append(report.parent)

    docs_report_dir = repo / "docs" / "report"
    if docs_report_dir.exists():
        for manifest_path in sorted(docs_report_dir.glob("*/report.manifest.yaml")):
            candidates.append(manifest_path.parent)

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        unique_candidates.append(resolved)
        seen.add(resolved)

    if not unique_candidates:
        issues.append(
            "未找到 `report.manifest.yaml`。需要先运行 report-init 或通过 report-update --mode deep-spec 补齐 execution manifests。"
        )
        return None, issues
    if len(unique_candidates) > 1:
        issues.append(
            "找到多个 report manifest，无法从 rendered report 自动判断目标工作区："
            + ", ".join(candidate.as_posix() for candidate in unique_candidates)
        )
        return None, issues
    return unique_candidates[0], issues


def validate_manifest_inputs(repo: Path, report: Path) -> ManifestInputs:
    report_dir, resolution_issues = resolve_report_workspace(repo, report)
    if report_dir is None:
        return ManifestInputs(report_dir=None, validation=None, resolution_issues=resolution_issues)
    return ManifestInputs(
        report_dir=report_dir,
        validation=validate_execution_manifests(report_dir),
        resolution_issues=resolution_issues,
    )


def _relative_parts(repo: Path, path: Path) -> tuple[str, ...]:
    try:
        return path.resolve().relative_to(repo.resolve()).parts
    except ValueError:
        return ()


def resolve_artifact_workspace(repo: Path, report: Path) -> tuple[Path | None, list[str]]:
    issues: list[str] = []
    parts = _relative_parts(repo, report)
    docs_report_dir = repo / "docs" / "report"

    if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "report":
        candidate = repo / "docs" / "report" / parts[2]
        if any((candidate / name).exists() for name in ("main", "paper", "spec")):
            return candidate.resolve(), issues

    candidates: list[Path] = []
    if docs_report_dir.exists():
        for candidate in sorted(path for path in docs_report_dir.iterdir() if path.is_dir()):
            if any((candidate / name).exists() for name in ("main", "paper", "spec")):
                candidates.append(candidate.resolve())

    if not candidates:
        return None, issues
    if len(candidates) > 1:
        issues.append(
            "找到多个 main/paper/spec 报告工作区，无法自动判断 active slug："
            + ", ".join(candidate.as_posix() for candidate in candidates)
        )
        return None, issues
    return candidates[0], issues


def _collect_paper_placeholders(paper_dir: Path) -> list[tuple[str, str]]:
    placeholders: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if not paper_dir.exists():
        return placeholders
    for path in sorted(paper_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".tex"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(errors="replace")
        for match in re.finditer(r"\{\{([^{}]+)\}\}", text):
            value = match.group(1).strip()
            key = (f"{{{{{value}}}}}", path.relative_to(paper_dir).as_posix())
            if key in seen:
                continue
            placeholders.append(key)
            seen.add(key)
    return placeholders


def _spec_experiment_ids(result: ManifestValidationResult) -> set[str]:
    experiment_ids: set[str] = set()
    experiments = result.documents.get("experiments", {}).get("experiments", [])
    if isinstance(experiments, list):
        experiment_ids.update(
            str(item.get("experiment_id", "")).strip()
            for item in experiments
            if isinstance(item, dict) and str(item.get("experiment_id", "")).strip()
        )
    evidence_contract = result.documents.get("evidence_contract", {})
    if isinstance(evidence_contract, dict):
        for claim in evidence_contract.get("claims", []) or []:
            if not isinstance(claim, dict):
                continue
            experiment_ids.update(
                str(item).strip()
                for item in _as_list(
                    claim.get("required_experiments")
                    or claim.get("experiment_ids")
                    or claim.get("experiments")
                    or claim.get("experiment_id")
                )
                if str(item).strip()
            )
    return experiment_ids


def _spec_registered_placeholders(result: ManifestValidationResult) -> set[str]:
    registered: set[str] = set()
    evidence_contract = result.documents.get("evidence_contract", {})
    if not isinstance(evidence_contract, dict):
        return registered
    for claim in evidence_contract.get("claims", []):
        if not isinstance(claim, dict):
            continue
        for placeholder in claim.get("paper_placeholders", []) or []:
            value = str(placeholder).strip()
            if value:
                registered.add(value)
    for item in evidence_contract.get("placeholders", []) or []:
        if isinstance(item, dict):
            value = str(item.get("placeholder", "")).strip()
        else:
            value = str(item).strip()
        if value:
            registered.add(value)
    return registered


def _placeholder_experiment_id(placeholder: str) -> str:
    inner = placeholder.strip().removeprefix("{{").removesuffix("}}").strip()
    return inner.split(".", 1)[0].strip()


def validate_artifact_inputs(repo: Path, report: Path) -> ArtifactInputs:
    workspace_dir, resolution_issues = resolve_artifact_workspace(repo, report)
    if workspace_dir is None:
        return ArtifactInputs(
            workspace_dir=None,
            main_dir=None,
            paper_dir=None,
            spec_dir=None,
            spec_validation=None,
            resolution_issues=resolution_issues,
            alignment_issues=[],
        )

    main_dir = workspace_dir / "main"
    paper_dir = workspace_dir / "paper"
    spec_dir = workspace_dir / "spec"
    alignment_issues: list[str] = []
    spec_validation: ManifestValidationResult | None = None

    if not main_dir.exists():
        alignment_issues.append(f"缺少 main 产物目录：`{main_dir.as_posix()}`。")
    if not paper_dir.exists():
        alignment_issues.append(f"缺少 paper 产物目录：`{paper_dir.as_posix()}`。")

    if spec_dir.exists():
        spec_validation = validate_spec_manifests(spec_dir)
    else:
        resolution_issues.append(f"缺少 spec 产物目录：`{spec_dir.as_posix()}`。")

    if paper_dir.exists() and spec_validation is not None:
        experiment_ids = _spec_experiment_ids(spec_validation)
        registered_placeholders = _spec_registered_placeholders(spec_validation)
        for placeholder, relative_path in _collect_paper_placeholders(paper_dir):
            experiment_id = _placeholder_experiment_id(placeholder)
            if placeholder in registered_placeholders or experiment_id in experiment_ids:
                continue
            alignment_issues.append(
                f"paper placeholder `{placeholder}` in `paper/{relative_path}` 未映射到 spec experiment 或 evidence contract。"
            )

    return ArtifactInputs(
        workspace_dir=workspace_dir,
        main_dir=main_dir if main_dir.exists() else None,
        paper_dir=paper_dir if paper_dir.exists() else None,
        spec_dir=spec_dir if spec_dir.exists() else None,
        spec_validation=spec_validation,
        resolution_issues=resolution_issues,
        alignment_issues=alignment_issues,
    )


def format_manifest_issues(manifest_inputs: ManifestInputs) -> str:
    lines: list[str] = []
    for issue in manifest_inputs.resolution_issues:
        lines.append(f"- [ERROR] {issue}")
    if manifest_inputs.validation is not None:
        for issue in manifest_inputs.validation.issues:
            location = f" `{issue.location}`" if issue.location else ""
            severity = "ERROR" if issue.severity == "error" else "READINESS"
            lines.append(f"- [{severity}]{location} {issue.message}")
    return "\n".join(lines) if lines else "- 无。"


def format_artifact_issues(artifact_inputs: ArtifactInputs) -> str:
    lines: list[str] = []
    for issue in artifact_inputs.resolution_issues:
        lines.append(f"- [ERROR] {issue}")
    for issue in artifact_inputs.alignment_issues:
        lines.append(f"- [ALIGNMENT] {issue}")
    if artifact_inputs.spec_validation is not None:
        for issue in artifact_inputs.spec_validation.issues:
            location = f" `{issue.location}`" if issue.location else ""
            severity = "ERROR" if issue.severity == "error" else "READINESS"
            lines.append(f"- [{severity}]{location} {issue.message}")
    return "\n".join(lines) if lines else "- 无。"


def format_artifact_paths(artifact_inputs: ArtifactInputs) -> str:
    if artifact_inputs.workspace_dir is None:
        return "- 未解析到三产物 workspace。"
    main_dir = artifact_inputs.workspace_dir / "main"
    paper_dir = artifact_inputs.workspace_dir / "paper"
    spec_dir = artifact_inputs.workspace_dir / "spec"
    return "\n".join(
        [
            f"- main: `{main_dir.as_posix()}`",
            f"- paper: `{paper_dir.as_posix()}`",
            f"- spec: `{spec_dir.as_posix()}`",
        ]
    )


def _command_text(command: object) -> str:
    if isinstance(command, list):
        return " && ".join(str(item) for item in command if str(item).strip())
    if command is None:
        return ""
    return str(command)


def format_manifest_tasks(result: ManifestValidationResult) -> str:
    harnesses = {
        harness.get("harness_id"): harness
        for harness in result.documents.get("harness", {}).get("harnesses", [])
        if isinstance(harness, dict) and harness.get("harness_id")
    }
    lines: list[str] = []
    for index, task in enumerate(result.task_order, start=1):
        task_id = str(task.get("task_id", "")).strip()
        title = str(task.get("title", "")).strip() or task_id
        raw_harnesses = task.get("harnesses", [])
        if not isinstance(raw_harnesses, list):
            raw_harnesses = [raw_harnesses]
        harness_ids = [str(item).strip() for item in raw_harnesses if str(item).strip()]
        command_parts: list[str] = []
        for harness_id in harness_ids:
            harness = harnesses.get(harness_id, {})
            command = _command_text(harness.get("command"))
            if command:
                command_parts.append(f"{harness_id}: `{command}`")
            else:
                command_parts.append(f"{harness_id}: <blocked>")
        commands = "; ".join(command_parts) if command_parts else "无 harness"
        lines.append(f"{index}. `{task_id}` - {title} - harness: {commands}")
    return "\n".join(lines) if lines else "未声明 task。"


def format_spec_milestones(result: ManifestValidationResult) -> str:
    task_graph = result.documents.get("task_graph") or {}
    gates = {
        gate.get("gate_id"): gate
        for gate in task_graph.get("gates", [])
        if isinstance(gate, dict) and gate.get("gate_id")
    }
    milestones = task_graph.get("milestones", [])
    if not isinstance(milestones, list) or not milestones:
        return format_manifest_tasks(result)

    task_by_id = {
        task.get("task_id"): task
        for task in task_graph.get("tasks", [])
        if isinstance(task, dict) and task.get("task_id")
    }
    lines: list[str] = []
    for index, milestone in enumerate(milestones, start=1):
        if not isinstance(milestone, dict):
            continue
        milestone_id = str(milestone.get("milestone_id", "")).strip() or f"M{index:02d}"
        title = str(milestone.get("title", "")).strip() or milestone_id
        gate_ids = [
            str(item).strip()
            for item in _as_list(milestone.get("gate_id") or milestone.get("gate_ids") or milestone.get("gates"))
            if str(item).strip()
        ]
        gate_text: list[str] = []
        for gate_id in gate_ids:
            gate = gates.get(gate_id, {})
            task_ids = [str(item).strip() for item in _as_list(gate.get("tasks")) if str(item).strip()]
            task_text = ", ".join(f"`{task_id}`" for task_id in task_ids if task_id in task_by_id) or "no tasks"
            gate_text.append(f"`{gate_id}` -> {task_text}")
        gates_rendered = "; ".join(gate_text) if gate_text else "no gate"
        lines.append(f"{index}. `{milestone_id}` - {title} - gate: {gates_rendered}")
    return "\n".join(lines) if lines else format_manifest_tasks(result)


def build_spec_repair_prompt(
    repo: Path,
    report: Path,
    extraction: ReportExtraction,
    artifact_inputs: ArtifactInputs,
) -> str:
    workspace = artifact_inputs.workspace_dir.as_posix() if artifact_inputs.workspace_dir else "<unresolved artifact workspace>"
    spec_dir = (artifact_inputs.workspace_dir / "spec").as_posix() if artifact_inputs.workspace_dir else "docs/report/<slug>/spec"
    return f"""# spec 修复目标：{extraction.title}

仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`
三产物工作区：`{workspace}`
目标 spec：`{spec_dir}`

## 任务

当前 `spec` 缺失、无效或未达到 execution-ready。不要实现产品功能、实验代码或论文结果；本轮唯一目标是使用 `report-spec` 或等价修复流程，把 `main` 中的设计意图编译为可执行 `spec`，并保持 `paper` 只作为表达产物。

## 当前阻塞

{format_artifact_issues(artifact_inputs)}

## 修复规则

- 从 `main/` 读取研究与工程设计；从 `paper/` 读取表达目标与 placeholder；不得从 `paper` 反向发明实验。
- 补齐 `spec/task_graph.yaml`、`spec/harness.yaml`、`spec/evidence_contract.yaml`，以及需要时的 `spec/experiment_manifest.yaml`。
- 每个 milestone 必须关联 gate；每个 gate 必须列出 task；每个 task 必须绑定 harness 和 acceptance criteria。
- harness 必须有真实 command 或显式 blocker；final/research evidence 不得使用 mock、toy、synthetic、stub、proxy 或 cached 结果。
- 修复后重新运行 `report-goal`。本 repair goal 不得输出 `REPORT_GOAL_COMPLETE`。
"""


def build_artifact_alignment_prompt(
    repo: Path,
    report: Path,
    extraction: ReportExtraction,
    artifact_inputs: ArtifactInputs,
) -> str:
    return f"""# 三产物对齐目标：{extraction.title}

仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`
三产物：
{format_artifact_paths(artifact_inputs)}

## 任务

`spec` 已经可以作为执行真源，但 `main` / `paper` / `spec` 之间仍存在产物缺失或一致性阻塞。不要开始工程实现或实验执行；本轮只修复三产物边界，使后续 goal 可以按 `spec` 严格执行。

## 当前阻塞

{format_artifact_issues(artifact_inputs)}

## 对齐规则

- `main` 中的 RQ、claim、experiment、task、harness、paper plan 必须能映射到 `spec`。
- `paper` 中的每个 placeholder 必须映射到 `spec` 中的 experiment 或 evidence contract。
- `paper` 不能新增 `main` 和 `spec` 未定义的数据集、baseline、metric、seed、实验或 claim。
- 对齐后只允许重新运行 `report-goal` 生成实现目标；本对齐目标不得输出 `REPORT_GOAL_COMPLETE`。
"""


def build_three_artifact_prompt(
    repo: Path,
    report: Path,
    extraction: ReportExtraction,
    artifact_inputs: ArtifactInputs,
    out_path: Path | None,
) -> str:
    assert artifact_inputs.spec_validation is not None
    assert artifact_inputs.workspace_dir is not None
    result = artifact_inputs.spec_validation
    prompt_path = out_path.as_posix() if out_path else f"{repo.as_posix()}/docs/report/report-goal-prompt.md"
    main_dir = artifact_inputs.main_dir or artifact_inputs.workspace_dir / "main"
    paper_dir = artifact_inputs.paper_dir or artifact_inputs.workspace_dir / "paper"
    spec_dir = artifact_inputs.spec_dir or result.report_dir
    return f"""# 三产物执行目标：{extraction.title}

仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`
main：`{main_dir.as_posix()}`
paper：`{paper_dir.as_posix()}`
spec：`{spec_dir.as_posix()}`

## Ralph Loop 启动方式

```bash
/ralph-loop:ralph-loop "$(cat {prompt_path})" --completion-promise "REPORT_GOAL_COMPLETE"
```

## 权威边界

1. `main/` 是人类设计真源：定义研究问题、方法、实验意图、任务拆分和教学解释。
2. `paper/` 是学术表达真源：定义顶会论文叙事、placeholder 和表达完整性。
3. `spec/` 是机器执行真源：唯一决定 milestone 顺序、gate、task、harness、artifact 和 evidence 准入。

不得从 `paper` 推断实验、数据集、baseline、metric、seed、模型、任务或结果。不得从 `main` prose 创建未进入 `spec` 的执行任务。

## Spec Milestone Order

`{spec_dir.as_posix()}/task_graph.yaml` 定义唯一执行顺序：

{format_spec_milestones(result)}

## 编译后的 Task / Harness

{format_manifest_tasks(result)}

## 执行协议

- 每轮先读取 `main/`、`paper/`、`spec/`、`report-goal/status.md`、`report-goal/gap-matrix.md`、`report-goal/decision-log.md`、`git status --short` 和最近 git log。
- 只选择 `spec/task_graph.yaml` 中最早未完成的 milestone / gate；不得跳过依赖或并行推进后续 milestone。
- 当前 milestone 的 task、harness、artifact、evidence、review、commit 全部完成后，才能进入下一个 milestone。
- 每个 task 先写或更新测试，再执行对应 harness command；完整 stdout/stderr 保存到 `report-goal/evidence/`。
- 每条 completion evidence 必须引用 `spec` 中声明的 `task_id`、`harness_id`、artifact path、命令和 git commit。
- `paper` 只能根据 `main`、`spec` 和 evidence 更新；未验证实验结果必须保留绑定到 spec experiment 的 placeholder。
- mock / toy / synthetic / cached 结果不得作为 final gate、research claim、baseline、ablation、paper table/figure 或 Go/No-Go 证据。

## Codex 审查门禁

每一个 milestone / gate 在标记完成之前，都必须先调用 Codex plugin 做 gate-quality review。只有 Codex 审查成功后，才可以把该 gate 记为完成、写入完成状态、创建 gate commit，并进入下一个 milestone。

- 内部门禁：先运行该 gate 声明的 harness command，并把 stdout / stderr / artifact / evidence 写入 `report-goal/evidence/`。
- 外部门禁：内部 harness 通过后，调用 Codex plugin。优先使用：

```bash
/codex:adversarial-review --wait --scope working-tree "Review the current gate against spec/task_graph.yaml, spec/harness.yaml, spec/evidence_contract.yaml, main/, paper/, and report-goal/status.md"
```

- 将 Codex 审查输出保存到 `report-goal/reviews/gate-<gate_id>-codex-review.md`。
- 如果 Codex plugin 不可用，必须把原因写入 `report-goal/status.md` 并停止等待用户决策；不得把该 gate 标记为完成。
- 如果 Codex 审查发现 BLOCK、Critical、Important 或等价阻塞问题，必须修复问题、重新运行该 gate 的 harness，再重新调用 Codex 审查。
- 只有 Codex 审查成功且没有未解决阻塞问题时，才允许进入下一 gate。

## 三产物一致性完成标准

- `main` 中声明的 RQ、claim、experiment、task、harness、paper plan 均已映射到 `spec`。
- `paper` 中所有 placeholder 均映射到 `spec` 的 experiment 或 evidence contract。
- `spec` 中每个 milestone 都有 gate；每个 gate 都有 task；每个 task 都有 harness、acceptance criteria 和 evidence contract。
- 每个 gate 都有保存的 Codex 审查记录，并且 Codex 审查成功。
- 所有 declared harness 已通过，evidence contract 已登记真实证据，独立复跑状态已记录。
- `report-goal/final-summary.md` 存在，并说明 main / paper / spec 的最终同步状态。

只有上述条件真实满足时，最终一行才允许输出 `REPORT_GOAL_COMPLETE`。
"""


def build_repair_prompt(
    repo: Path,
    report: Path,
    extraction: ReportExtraction,
    manifest_inputs: ManifestInputs,
) -> str:
    report_dir = manifest_inputs.report_dir.as_posix() if manifest_inputs.report_dir else "<unresolved report workspace>"
    return f"""# report-repair goal: {extraction.title}

仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`
报告工作区：`{report_dir}`

## 任务

当前报告尚未达到 execution-ready。不要实现产品功能、实验代码、论文结果或业务逻辑；本轮唯一目标是补齐 execution manifests，使报告可以被后续 `report-goal` 编译成实现目标。

必须补齐 execution manifests：
- `report.manifest.yaml`
- `tasks/task_graph.yaml`
- `harness/harness.yaml`
- `evidence/evidence_manifest.yaml`
- research-prd 额外需要 `experiments/experiment_manifest.yaml`

## 当前阻塞

{format_manifest_issues(manifest_inputs)}

## 修复规则

- 从 `{report.as_posix()}` 读取设计意图，只做 deep-spec lowering，不做实现。
- 每个 prose milestone / module / task / experiment commitment 必须落入对应 manifest。
- 不得创建虚假的 task、实验、metric、artifact 或 observed result。
- task 必须绑定 harness；harness 必须有 command 或显式 blocker；evidence 必须引用 task、harness、artifact、command 和 commit 的预期位置。
- mock / toy / synthetic / cached 只能用于 unit 或 smoke，不能作为 final gate、research claim、baseline、ablation、paper table/figure 或 Go/No-Go 证据。
- 修复后运行 manifest validator 和 report self-check，并把结果写入 `report-goal/status.md`。

## 完成标准

只有当 execution manifests 结构有效、task graph 与 harness 引用闭合、且不存在 execution-readiness 阻塞时，才允许后续重新运行 `report-goal` 生成实现目标。本修复目标不得输出 `REPORT_GOAL_COMPLETE`。
"""


def build_manifest_prompt(
    repo: Path,
    report: Path,
    extraction: ReportExtraction,
    manifest_inputs: ManifestInputs,
    out_path: Path | None,
) -> str:
    assert manifest_inputs.validation is not None
    result = manifest_inputs.validation
    prompt_path = out_path.as_posix() if out_path else f"{repo.as_posix()}/docs/report/report-goal-prompt.md"
    return f"""# manifest 门禁执行目标：{extraction.title}

仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`
报告工作区：`{result.report_dir.as_posix()}`

## Ralph Loop 启动方式

```bash
/ralph-loop:ralph-loop "$(cat {prompt_path})" --completion-promise "REPORT_GOAL_COMPLETE"
```

## 真源顺序

1. `{result.report_dir.as_posix()}/report.manifest.yaml` 定义报告与 manifest 边界。
2. `{result.report_dir.as_posix()}/tasks/task_graph.yaml` 定义执行顺序。
3. `{result.report_dir.as_posix()}/harness/harness.yaml` 定义完成判断器。
4. `{result.report_dir.as_posix()}/evidence/evidence_manifest.yaml` 定义允许登记的证据。
5. `{report.as_posix()}` 只作为设计解释来源；不得从 prose 猜测未在 manifest 中声明的 task。

## 编译后的 Task Graph

{format_manifest_tasks(result)}

## 执行协议

- 每轮先读取 `report-goal/status.md`、`report-goal/gap-matrix.md`、`report-goal/decision-log.md`、`git status --short` 和最近 git log。
- 只选择 task graph 中最早未完成的 task；不得跳过依赖。
- 每个 task 先写或更新测试，再执行对应 harness command；完整 stdout/stderr 保存到 `report-goal/evidence/`。
- 每条 completion evidence 必须引用 manifest 中声明的 `task_id`、`harness_id`、artifact path、命令和 git commit。
- mock / toy / synthetic / cached 结果不得作为 final gate、research claim、baseline、ablation、paper table/figure 或 Go/No-Go 证据。
- 每个 task 完成后更新 `report-goal/status.md`、`gap-matrix.md`、`decision-log.md` 和 evidence manifest，再提交只包含当前 task 的 git commit。

## 完成标准

只有 task graph 全部完成、所有 harness 通过、evidence manifest 完整、独立复跑状态已记录、`report-goal/final-summary.md` 存在时，最终一行才允许输出 `REPORT_GOAL_COMPLETE`。
"""


def truncate_lines(text: str, max_lines: int) -> tuple[str, bool]:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text, False
    kept = lines[:max_lines]
    kept.append(f"[truncated: {len(lines) - max_lines} additional lines omitted]")
    return "\n".join(kept), True


def build_short_prompt(
    repo: Path,
    report: Path,
    evidence: list[str],
    extraction: ReportExtraction,
    scan: ScanResult,
    out_path: Path | None,
) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    evidence_preview = "\n".join(
        line if len(line) <= 120 else f"{line[:117]}..."
        for line in evidence[:2]
    )
    prompt_path = out_path.as_posix() if out_path else f"{repo.as_posix()}/docs/report/report-goal-prompt.md"
    return f"""# Goal: {extraction.title}

生成时间：{generated_at}
仓库：`{repo.as_posix()}`
源报告：`{report.as_posix()}`

## Ralph Loop 启动方式

推荐 Claude Code 启动命令：

```bash
/ralph-loop:ralph-loop "$(cat {prompt_path})" --completion-promise "REPORT_GOAL_COMPLETE"
```

Ralph Loop 会在每次会话退出后重新投喂同一个 prompt，并保留文件修改与 git 历史。因此本 prompt 必须按幂等方式执行：每一轮都从仓库状态恢复，不依赖对话记忆。

## 任务

你正在执行一个长时间运行的工程目标。将 `{report.as_posix()}` 视为设计意图文档，而不是实现已经存在的证明。你的任务是根据下列 report-derived 目标线索和当前仓库事实，生成并执行 `report-goal/gap-matrix.md` 中的具体 gate，逐项补齐缺失实现，直到报告定义的设计真正完成并通过验证。

报告中抽取出的目标线索：
{format_plain_list(extraction.objective_lines)}

## 真源

主要设计参考：
- `{report.as_posix()}`

仓库实现真源：
- 实际代码、测试、配置、脚本、运行行为、artifacts 与现有文档。

初始扫描边界：报告提到的路径/命令线索 {len(extraction.path_hints)} 个，其中仓库中已存在 {len(scan.present_paths)} 个，缺失或无法直接定位 {len(scan.missing_paths)} 个；测试样本 {len(scan.test_files)} 个，脚本样本 {len(scan.script_files)} 个。这些计数只作线索，执行前必须从磁盘重新核对。

报告锚点：

```text
{evidence_preview}
```

报告中抽取出的路径、命令与 artifact 线索：
{format_list(extraction.path_hints[:30], "未从报告中抽取到明确路径。")}

当前仓库已匹配的线索：
{format_list(scan.present_paths, "暂无直接匹配。")}

当前仓库缺失或无法直接定位的线索：
{format_list(scan.missing_paths[:30], "暂无缺失线索。")}

## 初始发现阶段

编辑代码前，完整阅读 `AGENTS.md`、`RTK.md` 与报告。提取系统目标、用户或参与者、主要模块、数据模型、API / CLI / UI 入口、工作流、非目标、验收标准、验证期望与未决假设。扫描项目结构、运行时、测试、命令、迁移、路由、后台 worker 与部署脚本。必须把上述报告行号转写为项目专属 gate，不得照抄通用模板。

## 差距矩阵

在 `report-goal/gap-matrix.md` 存在之前不得开始实现。将报告中的每一条需求分类为 `implemented_verified`、`implemented_unverified`、`partial`、`missing`、`conflict`、`obsolete_or_unrealistic` 或 `needs_user_decision`。每一行必须包含报告引用、期望行为、观察到的实现证据、缺失工作、受影响文件、拟验证方式、优先级与风险。

报告中抽取出的 gate / 里程碑线索，必须进入 gap matrix：
{format_plain_list(extraction.gate_lines)}

## Gate 协议

按严格顺序执行 gate。当前 gate 未完成以下条件前，不得进入后续 gate：通过门禁、完成 Codex plugin gate 质量审查、修复所有阻塞性审查问题，并创建只包含当前 gate 相关改动的 git commit。

- Gate 0：发现与差距矩阵。将报告目标、gate、约束、产物、路径线索和仓库证据合成为 `report-goal/gap-matrix.md`、`report-goal/status.md` 与 `report-goal/decision-log.md`。Commit message：`docs(report-goal): complete gate 0 discovery`。
- Gate 1：契约与脚手架。只创建 gap matrix 中最早未完成 gate 所需的最小模块、schema、命令与测试骨架。Commit message：`chore(report-goal): complete gate 1 scaffolding`。
- Gate 2..N：按 gap matrix 中来自报告的 gate 顺序执行。每个 gate 先写或更新测试，再实现最小可通过改动，运行验证，更新 gate 文档，然后使用 `feat(report-goal): complete gate <n> <short-name>` 提交。
- Final Gate：集成与收尾。运行更广泛验证，核验关键工作流，产出 `report-goal/final-summary.md`，并使用 `docs(report-goal): complete final gate` 提交。

门禁规则（inner / outer gate）：每个 gate 必须分两步通过，不得跳过：
1. **Inner Gate（测试门禁）**：编写或更新测试，运行并通过。测试是系统契约，不能伪造。若测试失败，修复后重新运行，不得进入 outer gate。TDD 顺序：先红（测试失败）、再绿（实现最小可通过）、最后重构。
2. **Outer Gate（质量审查）**：inner gate 通过后，更新 `report-goal/status.md` 和 `report-goal/gap-matrix.md`，然后调用 Codex plugin 审查。若 slash command 可用，优先运行 `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"`。若 slash command 不可用但 plugin runtime 已安装，运行等价的 Codex companion 命令。将审查输出保存到 `report-goal/reviews/gate-<n>-codex-review.md`。修复每一个 BLOCK、Critical 与 Important 问题，重新运行测试（inner gate）并重新运行 Codex review（outer gate）后才能提交。若 Codex plugin 不可用，将准确原因记录到 `report-goal/status.md`，并停止等待用户决策。

没有通过 inner gate 的 gate 不得进入 outer gate。若 inner gate 测试无法编写（例如缺少模型权重、硬件、凭证、或外部服务），在 `report-goal/gap-matrix.md` 中标记为 `needs_user_decision` 并记录阻塞原因。

反幻觉验证规则（evidence over claims）：agent 必须用可执行的证据代替自评估，禁止幻影验证：
- **独立运行测试**：agent 声明测试通过后，必须用独立的 shell 命令重新运行一次测试（不是 agent 写的 test runner），并将完整输出保存到 `report-goal/evidence/gate-<n>-test-output.txt`。不接受 "tests should pass" 或 "based on the code structure" 等模糊表述。
- **测试不能是自证的**：如果同一个 gate 里既写了实现又写了测试，Codex review 必须检查测试是否真正验证了报告规格而非实现行为（tautological test detection）。如果测试只验证代码做了什么而非代码应该做什么，视为未通过。
- **命令输出即证据**：inner gate 的完成证据是实际命令输出（如 `pytest --tb=short` 的 stdout），不是 agent 的总结。将输出保存到 `report-goal/evidence/` 目录下。
- **集成验证**：每个 gate 完成后，确认新增代码被正确接入调用链（函数有 caller、路由有注册、模块有导入）。不能出现 "写了但没接入" 的情况。
- **TODO 检测**：gate 提交前，搜索当前 gate 改动中的 `TODO`、`FIXME`、`HACK`、`XXX` 标记。每个 TODO 必须在 `report-goal/decision-log.md` 中记录原因、影响、和预计解决时间。禁止用 TODO 代替未完成的工作。

提交规则：stage 前检查 `git status`，只 stage 当前 gate 相关文件，保留无关用户改动，不提交失败工作或未审查 gate 工作。若无关脏文件导致无法形成隔离 gate commit，停止并询问用户。

## Ralph Loop 迭代规则

每轮迭代开始时，读取 `report-goal/status.md`、`report-goal/gap-matrix.md`、`report-goal/decision-log.md`、最近的 `git log --oneline -5` 和 `git status --short`。若这些文件不存在，从 Gate 0 开始。每轮只选择最早的未完成 gate。已经有通过证据和匹配 git commit 的 gate 不得重做。

每轮结束时，仓库只能处于三种状态之一：一个 gate 已经通过 inner gate（测试）和 outer gate（Codex 审查）并提交到 git；阻塞项已记录到 `report-goal/status.md`；或因需要用户决策而停止。在 Final Gate 完成、所有验证和 Codex gate review 已通过或被用户显式延期、且 `report-goal/final-summary.md` 存在之前，不得输出 `REPORT_GOAL_COMPLETE`。若配置了 completion promise，只能在该条件完全真实时将其作为最后一行输出。

## 执行规则

按小里程碑工作。每个里程碑必须定义目标、预计改动文件、测试、实现步骤、验证命令、恢复说明与完成证据。优先采用 TDD。每个里程碑后运行验证，修复失败，更新 `report-goal/status.md`，更新 `report-goal/gap-matrix.md`，并将决策记录到 `report-goal/decision-log.md`。仅在当前外部事实重要时使用 web search，优先官方来源，并将引用记录到 `report-goal/sources.md`。

报告中抽取出的硬约束，必须进入 gate 进入条件和停止条件：
{format_plain_list(extraction.constraint_lines)}

报告中抽取出的验证、命令、产物和 evidence 线索，必须进入完成标准：
{format_plain_list(extraction.artifact_lines)}

范围控制：除非报告要求，不进行大范围重写，不新增框架，不改变产品语义，不删除用户工作，不将 mock 行为视为生产就绪。若报告与实现之间存在产品语义或数据契约冲突，停止并询问用户。

自定义硬约束：保留报告定义的阶段 gate、实现顺序与模块边界。不得假设固定项目结构，必须遵循报告自身的模块布局。

## 完成标准

只有满足以下条件时，目标才算完成：每一条可执行报告需求都已分类；每个 `missing`、`partial` 或 `implemented_unverified` 项都已实现或带理由显式延期；验证通过；关键工作流具备可执行证据；`report-goal/final-summary.md` 说明已实现内容、已验证内容、延期内容、项目运行方式与验证复现方式。持续工作直到完成、被明确用户决策阻塞，或被工具和运行时限制停止。
"""


def build_full_prompt(
    repo: Path,
    report: Path,
    evidence: list[str],
    extraction: ReportExtraction,
    scan: ScanResult,
    out_path: Path | None,
) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    prompt_path = out_path.as_posix() if out_path else f"{repo.as_posix()}/docs/report/report-goal-prompt.md"
    return f"""# Goal: {extraction.title}

目标：基于 `{report.as_posix()}` 和当前仓库事实，生成并执行项目专属的 gate 化实现计划，直到报告定义的设计完成、验证通过，或被明确外部条件阻塞。

生成时间：{generated_at}
仓库：`{repo.as_posix()}`
设计真源：`{report.as_posix()}`

## Ralph Loop 启动方式

```bash
/ralph-loop:ralph-loop "$(cat {prompt_path})" --completion-promise "REPORT_GOAL_COMPLETE"
```

Ralph Loop 会重复投喂同一 prompt。每轮必须从仓库状态、`report-goal/status.md`、`report-goal/gap-matrix.md`、`report-goal/decision-log.md`、`git log --oneline -5` 与 `git status --short` 恢复。

## Report-Derived 目标

{format_plain_list(extraction.objective_lines)}

## Report-Derived Gate / 里程碑

{format_plain_list(extraction.gate_lines)}

## Report-Derived 硬约束

{format_plain_list(extraction.constraint_lines)}

## Report-Derived 产物、命令与验证

{format_plain_list(extraction.artifact_lines)}

## 路径、命令与仓库扫描

报告提到的路径/命令/artifact 线索：
{format_list(extraction.path_hints[:60], "未从报告中抽取到明确路径。")}

当前仓库已匹配：
{format_list(scan.present_paths, "暂无直接匹配。")}

当前仓库缺失或无法直接定位：
{format_list(scan.missing_paths[:60], "暂无缺失线索。")}

相关已跟踪文件样本：
{format_list(scan.tracked_relevant_files[:80])}

测试样本：
{format_list(scan.test_files[:60])}

脚本样本：
{format_list(scan.script_files[:60])}

Git status：

```text
{scan.git_status or "clean or unavailable"}
```

Git status truncated: `{str(scan.git_status_truncated).lower()}`

## Gate 协议

不得先实现再补矩阵。Gate 0 必须先把上面的 report-derived 目标、gate、约束、产物和仓库证据转写为 `report-goal/gap-matrix.md`。每个 gate 必须分两步通过（inner gate → outer gate），并创建只包含当前 gate 改动的 git commit 后，才允许进入下一个 gate。

1. Gate 0：Discovery and gap matrix。产出 `report-goal/gap-matrix.md`、`report-goal/status.md`、`report-goal/decision-log.md`。Commit message：`docs(report-goal): complete gate 0 discovery`。
2. Gate 1：Contracts and scaffolding。只为 gap matrix 中最早未完成的 report gate 创建最小模块、schema、命令和测试骨架。Commit message：`chore(report-goal): complete gate 1 scaffolding`。
3. Gate 2..N：按 `report-goal/gap-matrix.md` 中来自报告的 gate 顺序实现。每个 gate 先写或更新测试，再实现最小可通过改动，运行验证，更新 gate 文档，通过双层门禁后提交。
4. Final Gate：运行全局验证，生成 `report-goal/final-summary.md`。Commit message：`docs(report-goal): complete final gate`。

Gate protocol (inner / outer gate): each gate must pass two checkpoints in order. No outer review without inner gate pass.

1. **Inner Gate (Test Gate)**: write or update tests, run and pass. Tests are the system contract — they cannot be faked. If tests fail, fix and rerun. Do not proceed to outer gate. Follow TDD: red (test fails), green (minimal implementation), refactor.
2. **Outer Gate (Quality Review)**: after inner gate passes, update `report-goal/status.md` and `report-goal/gap-matrix.md`, then invoke the Codex plugin. Prefer `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"` when slash commands are available. If slash commands are unavailable but the plugin runtime is installed, run the equivalent Codex companion command. Save review output to `report-goal/reviews/gate-<n>-codex-review.md`. Resolve every BLOCK, Critical, and Important finding, rerun tests (inner gate), and rerun Codex review (outer gate) before committing. If Codex plugin is unavailable, record exact reason in `report-goal/status.md` and stop for user decision.

If inner gate tests cannot be written (missing model weights, hardware, credentials, external services), mark the gate as `needs_user_decision` in `report-goal/gap-matrix.md` and record the blocker.

Anti-hallucination verification (evidence over claims): the agent must produce executable evidence instead of self-assessment. Phantom verification is not acceptable.
- **Independent test execution**: after the agent claims tests pass, re-run the test suite with an independent shell command and save full output to `report-goal/evidence/gate-<n>-test-output.txt`. Do not accept "tests should pass" or "based on the code structure" — only concrete command output counts as evidence.
- **Tests must not be tautological**: when the same gate writes both implementation and tests, the Codex review must verify that tests validate the specification (what the code should do), not the implementation (what the code does). Tautological tests are treated as failing.
- **Command output is evidence**: the inner gate completion evidence is actual test runner stdout (e.g. `pytest --tb=short`), not an agent summary. Save output under `report-goal/evidence/`.
- **Integration check**: after each gate, verify that new code is wired into the call chain (functions have callers, routes are registered, modules are imported). Functions that exist but are never called are a failure.
- **TODO/FIXME detection**: before committing, search gate changes for `TODO`, `FIXME`, `HACK`, `XXX`. Each must be logged in `report-goal/decision-log.md` with reason, impact, and resolution timeline. Do not use TODOs as a substitute for incomplete work.

Commit rules: inspect `git status` before staging, stage only files changed for the current gate, preserve unrelated user changes, and do not commit failing work or unreviewed gate work. If unrelated dirty files make a clean gate commit impossible, stop and ask the user.

## Ralph Loop 迭代规则

At the start of every iteration, read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent `git log --oneline -5`, and `git status --short`. If these files do not exist, begin with Gate 0. Select only the earliest incomplete gate. Do not redo a gate that already has passing evidence and a matching git commit.

At the end of each iteration, leave the repository in one of three states: a gate that has passed both inner gate (tests) and outer gate (Codex review) and is committed to git; a documented blocker in `report-goal/status.md`; or a user-decision stop. Never output `REPORT_GOAL_COMPLETE` until the Final Gate is complete, all validations and Codex gate reviews have passed or been explicitly deferred by the user, and `report-goal/final-summary.md` exists. If a completion promise is configured, output it only as the final line and only when it is unequivocally true.

## 执行顺序

1. 完整阅读 `{report.as_posix()}`、`AGENTS.md`、`RTK.md`，校验本 prompt 抽取出的目标、gate、路径和产物是否完整。
2. 建立 `report-goal/gap-matrix.md`，逐项引用报告行号，并标注 observed implementation evidence。
3. 只实现 gap matrix 中最早的未完成 gate。
4. **Inner Gate**: 采用 TDD，先写测试使之失败（红），再写最小实现使之通过（绿），最后重构。测试必须真实运行并通过。
5. **Outer Gate**: inner gate 通过后，运行 Codex gate review，保存结果，修复阻塞问题。若 review 要求修改代码，重新运行测试（inner gate）确认通过。
6. 只提交当前 gate 文件。
7. 继续下一 gate，直到 final summary 完成。

## 停止规则

- Stop training or optimization work if the report says an earlier evaluator, audit, diagnostic, or reranking gate has not passed.
- Do not implement any optimization before the report-defined earlier gate passes.
- Do not continue legacy component patching if the report requires new module boundaries.
- Do not claim completion from smoke tests when the report requires heldout, multi-seed, or artifact-level gates.
- If GPU/model/data access is unavailable, create deterministic unit tests and document the exact blocked command, missing resource, and next executable command.

## 完成标准

只有满足以下条件时，目标才完成：

- 每个 report-derived requirement 均已在 `report-goal/gap-matrix.md` 分类。
- 每个 `missing`、`partial`、`implemented_unverified` 项已实现、验证、提交，或被显式延期。
- 每个 gate 都有 inner gate 测试通过证据、outer gate Codex review 记录和 git commit。
- `report-goal/final-summary.md` 说明已实现内容、已验证内容、延期内容、运行方式和复现方式。
- 只有上述条件真实满足时，最终一行才输出 `REPORT_GOAL_COMPLETE`。
"""


def build_prompt(
    repo: Path,
    report: Path,
    evidence: list[str],
    extraction: ReportExtraction,
    scan: ScanResult,
    style: str,
    out_path: Path | None,
    manifest_inputs: ManifestInputs | None = None,
    allow_legacy_prose_goal: bool = False,
    artifact_inputs: ArtifactInputs | None = None,
) -> str:
    if artifact_inputs is not None and artifact_inputs.found and not allow_legacy_prose_goal:
        if not artifact_inputs.spec_ready:
            return build_spec_repair_prompt(repo, report, extraction, artifact_inputs)
        if not artifact_inputs.alignment_ready:
            return build_artifact_alignment_prompt(repo, report, extraction, artifact_inputs)
        return build_three_artifact_prompt(repo, report, extraction, artifact_inputs, out_path)
    if artifact_inputs is not None and artifact_inputs.resolution_issues and not allow_legacy_prose_goal:
        return build_artifact_alignment_prompt(repo, report, extraction, artifact_inputs)
    if manifest_inputs is not None and not allow_legacy_prose_goal:
        if not manifest_inputs.execution_ready:
            return build_repair_prompt(repo, report, extraction, manifest_inputs)
        return build_manifest_prompt(repo, report, extraction, manifest_inputs, out_path)
    if style == "full":
        return build_full_prompt(repo, report, evidence, extraction, scan, out_path)
    return build_short_prompt(repo, report, evidence, extraction, scan, out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--report", default="docs/report/report.md", help="Report markdown path.")
    parser.add_argument("--out", default="", help="Output markdown path. Defaults to stdout only.")
    parser.add_argument("--print", action="store_true", help="Print prompt to stdout.")
    parser.add_argument("--max-report-lines", type=int, default=45, help="Maximum report evidence lines.")
    parser.add_argument(
        "--style",
        choices=("short", "full"),
        default="short",
        help="Prompt length. short is the default few-hundred-word goal prompt.",
    )
    parser.add_argument(
        "--allow-legacy-prose-goal",
        action="store_true",
        help="Bypass manifest gating and generate the legacy prose-derived implementation prompt.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    report = (repo / args.report).resolve() if not Path(args.report).is_absolute() else Path(args.report)
    if not repo.exists() or not repo.is_dir():
        print(f"error: repo does not exist or is not a directory: {repo}", file=sys.stderr)
        return 2
    if not report.exists() or not report.is_file():
        print(f"error: report file not found: {report}", file=sys.stderr)
        return 2

    out = (repo / args.out).resolve() if args.out and not Path(args.out).is_absolute() else Path(args.out) if args.out else None
    extraction = extract_report_context(report)
    evidence = extract_report_evidence(report, args.max_report_lines)
    scan = scan_repo(repo, extraction.path_hints)
    artifact_inputs = validate_artifact_inputs(repo, report)
    manifest_inputs = validate_manifest_inputs(repo, report)
    prompt = build_prompt(
        repo,
        report,
        evidence,
        extraction,
        scan,
        args.style,
        out,
        manifest_inputs,
        args.allow_legacy_prose_goal,
        artifact_inputs,
    )

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        print(f"[OK] wrote goal prompt: {out}")
        print(f"Prompt path: {out}")
        print(f"Source report: {report}")
        print(
            "Implementation scan summary: "
            f"report_hints={len(extraction.path_hints)}, "
            f"present={len(scan.present_paths)}, "
            f"missing={len(scan.missing_paths)}, "
            f"tests={len(scan.test_files)}, scripts={len(scan.script_files)}"
        )
        if args.allow_legacy_prose_goal:
            print("Manifest gate: bypassed by --allow-legacy-prose-goal")
        elif artifact_inputs.implementation_ready:
            print(f"Three-artifact gate: execution-ready ({artifact_inputs.workspace_dir})")
        elif artifact_inputs.found:
            print("Three-artifact gate: repair/alignment goal generated")
        elif manifest_inputs.execution_ready:
            print(f"Manifest gate: execution-ready ({manifest_inputs.report_dir})")
        else:
            print("Manifest gate: repair goal generated")
        print("How to use: pass this prompt file to Ralph Loop or Codex Goal as the objective.")
    if args.print or not args.out:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
