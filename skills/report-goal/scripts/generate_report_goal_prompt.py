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


def format_plain_list(items: list[str], empty: str = "未从报告中抽取到明确条目。") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


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

按严格顺序执行 gate。当前 gate 未完成以下条件前，不得进入后续 gate：验证通过、更新 `report-goal/status.md`、更新 `report-goal/gap-matrix.md`、完成 Codex plugin gate 质量审查、修复所有阻塞性审查问题，并创建只包含当前 gate 相关改动的 git commit。

- Gate 0：发现与差距矩阵。将报告目标、gate、约束、产物、路径线索和仓库证据合成为 `report-goal/gap-matrix.md`、`report-goal/status.md` 与 `report-goal/decision-log.md`。Commit message：`docs(report-goal): complete gate 0 discovery`。
- Gate 1：契约与脚手架。只创建 gap matrix 中最早未完成 gate 所需的最小模块、schema、命令与测试骨架。Commit message：`chore(report-goal): complete gate 1 scaffolding`。
- Gate 2..N：按 gap matrix 中来自报告的 gate 顺序执行。每个 gate 先写或更新测试，再实现最小可通过改动，运行验证，更新 gate 文档，然后使用 `feat(report-goal): complete gate <n> <short-name>` 提交。
- Final Gate：集成与收尾。运行更广泛验证，核验关键工作流，产出 `report-goal/final-summary.md`，并使用 `docs(report-goal): complete final gate` 提交。

审查规则：本地验证通过后、gate commit 前，调用 Codex plugin 审查当前 gate 质量。若 slash command 可用，优先运行 `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"`。若 slash command 不可用但 plugin runtime 已安装，运行等价的 Codex companion 命令。将审查输出保存到 `report-goal/reviews/gate-<n>-codex-review.md`。修复每一个 BLOCK、Critical 与 Important 问题，重新运行验证，并重新运行 Codex review 后才能提交。若 Codex plugin 不可用，将准确原因记录到 `report-goal/status.md`，并停止等待用户决策。

提交规则：stage 前检查 `git status`，只 stage 当前 gate 相关文件，保留无关用户改动，不提交失败工作或未审查 gate 工作。若无关脏文件导致无法形成隔离 gate commit，停止并询问用户。

## Ralph Loop 迭代规则

每轮迭代开始时，读取 `report-goal/status.md`、`report-goal/gap-matrix.md`、`report-goal/decision-log.md`、最近的 `git log --oneline -5` 和 `git status --short`。若这些文件不存在，从 Gate 0 开始。每轮只选择最早的未完成 gate。已经有通过证据和匹配 git commit 的 gate 不得重做。

每轮结束时，仓库只能处于三种状态之一：一个 gate 已经通过 Codex 审查并提交到 git；阻塞项已记录到 `report-goal/status.md`；或因需要用户决策而停止。在 Final Gate 完成、所有验证和 Codex gate review 已通过或被用户显式延期、且 `report-goal/final-summary.md` 存在之前，不得输出 `REPORT_GOAL_COMPLETE`。若配置了 completion promise，只能在该条件完全真实时将其作为最后一行输出。

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

不得先实现再补矩阵。Gate 0 必须先把上面的 report-derived 目标、gate、约束、产物和仓库证据转写为 `report-goal/gap-matrix.md`。后续每个 gate 必须通过验证、更新 `report-goal/status.md` 和 `report-goal/gap-matrix.md`、完成 Codex plugin gate-quality review、修复阻塞项，并创建只包含当前 gate 改动的 git commit 后，才允许进入下一个 gate。

1. Gate 0：Discovery and gap matrix。产出 `report-goal/gap-matrix.md`、`report-goal/status.md`、`report-goal/decision-log.md`。Commit message：`docs(report-goal): complete gate 0 discovery`。
2. Gate 1：Contracts and scaffolding。只为 gap matrix 中最早未完成的 report gate 创建最小模块、schema、命令和测试骨架。Commit message：`chore(report-goal): complete gate 1 scaffolding`。
3. Gate 2..N：按 `report-goal/gap-matrix.md` 中来自报告的 gate 顺序实现。每个 gate 先写或更新测试，再实现最小可通过改动，运行验证，更新 gate 文档，Codex review 通过后提交。
4. Final Gate：运行全局验证，生成 `report-goal/final-summary.md`。Commit message：`docs(report-goal): complete final gate`。

Review rules: after local validation passes and before the gate commit, invoke the Codex plugin to review current gate quality. Prefer `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"` when slash commands are available. If slash commands are unavailable but the plugin runtime is installed, run the equivalent Codex companion command. Save the review output to `report-goal/reviews/gate-<n>-codex-review.md`. Resolve every BLOCK, Critical, and Important finding, rerun validation, and rerun Codex review before committing. If the Codex plugin is unavailable, record the exact reason in `report-goal/status.md` and stop for user decision.

Commit rules: inspect `git status` before staging, stage only files changed for the current gate, preserve unrelated user changes, and do not commit failing work or unreviewed gate work. If unrelated dirty files make a clean gate commit impossible, stop and ask the user.

## Ralph Loop 迭代规则

At the start of every iteration, read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent `git log --oneline -5`, and `git status --short`. If these files do not exist, begin with Gate 0. Select only the earliest incomplete gate. Do not redo a gate that already has passing evidence and a matching git commit.

At the end of each iteration, leave the repository in one of three states: a completed gate reviewed by Codex and committed to git; a documented blocker in `report-goal/status.md`; or a user-decision stop. Never output `REPORT_GOAL_COMPLETE` until the Final Gate is complete, all validations and Codex gate reviews have passed or been explicitly deferred by the user, and `report-goal/final-summary.md` exists. If a completion promise is configured, output it only as the final line and only when it is unequivocally true.

## 执行顺序

1. 完整阅读 `{report.as_posix()}`、`AGENTS.md`、`RTK.md`，校验本 prompt 抽取出的目标、gate、路径和产物是否完整。
2. 建立 `report-goal/gap-matrix.md`，逐项引用报告行号，并标注 observed implementation evidence。
3. 只实现 gap matrix 中最早的未完成 gate。
4. 采用 TDD 或最强可用验证方式，先补测试/验证，再写最小实现。
5. 验证通过后运行 Codex gate review，保存结果，修复阻塞问题。
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
- 每个 gate 都有验证命令、Codex review 记录和 git commit。
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
) -> str:
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
    prompt = build_prompt(repo, report, evidence, extraction, scan, args.style, out)

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
        print("How to use: pass this prompt file to Ralph Loop or Codex Goal as the objective.")
    if args.print or not args.out:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
