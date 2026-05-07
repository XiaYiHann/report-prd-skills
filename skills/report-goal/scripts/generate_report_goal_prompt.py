#!/usr/bin/env python3
"""Generate a Codex Goal prompt from a PRD report and repo scan."""

from __future__ import annotations

import argparse
import datetime as dt
import os
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


def scan_repo(repo: Path) -> ScanResult:
    files = find_files(repo)
    relevant_terms = (
        "report",
        "module",
        "core",
        "eval",
        "test",
        "scripts",
    )
    relevant = [path for path in files if any(term in path.lower() for term in relevant_terms)]
    expected = [
        "src/core/module_a.py",
        "src/core/module_b.py",
        "src/search/ranker.py",
        "src/analysis/baselines.py",
        "src/artifacts/schema.py",
        "scripts/run_eval.py",
        "scripts/run_trace.py",
        "scripts/run_value_table.py",
        "scripts/run_gap_report.py",
    ]
    present = [path for path in expected if (repo / path).exists()]
    missing = [path for path in expected if not (repo / path).exists()]
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


def truncate_lines(text: str, max_lines: int) -> tuple[str, bool]:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text, False
    kept = lines[:max_lines]
    kept.append(f"[truncated: {len(lines) - max_lines} additional lines omitted]")
    return "\n".join(kept), True


def build_short_prompt(repo: Path, report: Path, evidence: list[str], scan: ScanResult) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    evidence_preview = "\n".join(
        line if len(line) <= 120 else f"{line[:117]}..."
        for line in evidence[:2]
    )
    return f"""# Goal: Align implementation with report.md and complete the report-backed design

Generated at: {generated_at}
Repository: `{repo.as_posix()}`
Source report: `{report.as_posix()}`

## Ralph Loop Launch

Recommended Claude Code invocation:

```bash
/ralph-loop "$(cat {repo.as_posix()}/docs/report/report-goal-prompt.md)" --max-iterations 20 --completion-promise "REPORT_GOAL_COMPLETE"
```

Ralph Loop will feed this same prompt back after each session exit while preserving files and git history. Therefore this prompt is intentionally idempotent: each iteration must resume from repo state, not from conversation memory.

## Mission

You are executing a long-running engineering goal. Treat `{report.as_posix()}` as the design-intent document, not as proof that implementation exists. Scan the repository, compare implementation reality against the report, create `report-goal/gap-matrix.md`, then implement missing pieces milestone by milestone until the report-backed design is complete and verified.

## Source Of Truth

Primary design reference:
- `{report.as_posix()}`

Repository source of truth:
- actual code, tests, configs, scripts, runtime behavior, artifacts, and existing documentation.

Initial scan boundary: present report-aligned paths {len(scan.present_paths)}, missing paths {len(scan.missing_paths)}, test samples {len(scan.test_files)}, script samples {len(scan.script_files)}. These counts are only hints; verify from disk before acting.

Report anchors:

```text
{evidence_preview}
```

## Initial Discovery Phase

Before editing code, read `AGENTS.md`, `RTK.md`, and the report fully. Extract system goal, actors, modules, data model, API / CLI / UI surfaces, workflows, non-goals, acceptance criteria, validation expectations, and unresolved assumptions. Scan project structure, runtime, tests, commands, migrations, routes, workers, and deployment scripts.

## Gap Matrix

Do not implement before `report-goal/gap-matrix.md` exists. Classify every report requirement as `implemented_verified`, `implemented_unverified`, `partial`, `missing`, `conflict`, `obsolete_or_unrealistic`, or `needs_user_decision`. Each row must include report reference, expected behavior, observed evidence, missing work, affected files, proposed validation, priority, and risk.

## Gate Protocol

Execute the work as strict sequential gates. A later gate cannot start until the current gate has passing validation, updated `report-goal/status.md`, updated `report-goal/gap-matrix.md`, a Codex plugin gate-quality review, all blocking review findings resolved, and a git commit containing only that gate's related changes.

- Gate 0: Discovery and gap matrix. Produce `report-goal/gap-matrix.md`, `report-goal/status.md`, and `report-goal/decision-log.md`. Commit message: `docs(report-goal): complete gate 0 discovery`.
- Gate 1: Contracts and scaffolding. Create the minimal modules, schemas, commands, and test skeletons required by the first report milestone. Commit message: `chore(report-goal): complete gate 1 scaffolding`.
- Gate 2..N: Report milestones in order. For each milestone, write or update tests first, implement the smallest passing change, run validation, update gate docs, then commit with `feat(report-goal): complete gate <n> <short-name>`.
- Final Gate: Integration and closeout. Run broad validation, verify key workflows, produce `report-goal/final-summary.md`, and commit with `docs(report-goal): complete final gate`.

Review rules: after local validation passes and before the gate commit, invoke the Codex plugin to review current gate quality. Prefer `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"` when slash commands are available. If slash commands are unavailable but the plugin runtime is installed, run the equivalent Codex companion command. Save the review output to `report-goal/reviews/gate-<n>-codex-review.md`. Resolve every BLOCK, Critical, and Important finding, rerun validation, and rerun Codex review before committing. If the Codex plugin is unavailable, record the exact reason in `report-goal/status.md` and stop for user decision.

Commit rules: inspect `git status` before staging, stage only files changed for the current gate, preserve unrelated user changes, and do not commit failing work or unreviewed gate work. If unrelated dirty files make a clean gate commit impossible, stop and ask the user.

## Ralph Loop Iteration Rules

At the start of every iteration, read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent `git log --oneline -5`, and `git status --short`. If these files do not exist, begin with Gate 0. Select only the earliest incomplete gate. Do not redo a gate that already has passing evidence and a matching git commit.

At the end of each iteration, leave the repository in one of three states: a completed gate reviewed by Codex and committed to git; a documented blocker in `report-goal/status.md`; or a user-decision stop. Never output `REPORT_GOAL_COMPLETE` until the Final Gate is complete, all validations and Codex gate reviews have passed or been explicitly deferred by the user, and `report-goal/final-summary.md` exists. If a completion promise is configured, output it only as the final line and only when it is unequivocally true.

## Execution Rules

Work in small milestones. Each milestone must define objective, files likely to change, tests, implementation steps, validation commands, recovery notes, and completion evidence. Prefer TDD. After each milestone, run validation, fix failures, update `report-goal/status.md`, update `report-goal/gap-matrix.md`, and record decisions in `report-goal/decision-log.md`. Use web search only for current external facts, prefer official sources, and record them in `report-goal/sources.md`.

Scope control: do not perform broad rewrites, add frameworks, change product semantics, delete user work, or treat mock behavior as production-ready unless the report requires it. If report and implementation conflict in product semantics or data contracts, stop and ask the user.

Custom hard constraints when applicable: preserve any report-defined phase gates, implementation ordering, and module boundaries. Do not assume a specific project structure — follow the report's own module layout.

## Completion Criteria

The goal is complete only when every actionable report requirement is classified, every `missing`, `partial`, or `implemented_unverified` item is implemented or explicitly deferred, validations pass, key workflows have executable evidence, and `report-goal/final-summary.md` explains what was implemented, verified, deferred, how to run the project, and how to reproduce validation. Continue until complete, blocked by an explicit user decision, or stopped by tool/runtime limits.
"""


def build_full_prompt(repo: Path, report: Path, evidence: list[str], scan: ScanResult) -> str:
    generated_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    return f"""# Codex Goal Prompt: Implement Report Design

Objective: scan the repository, compare current implementation against `{report.as_posix()}`, then implement the report design end to end in milestone order until all report-defined acceptance gates are either passed or explicitly blocked by documented external constraints.

Generated at: {generated_at}
Repository root: `{repo.as_posix()}`
Design source of truth: `{report.as_posix()}`

## Non-negotiable Context Rules

- Before editing, reread `{report.as_posix()}` and local `AGENTS.md` / `RTK.md` if present.
- Treat the report as design truth; treat code, tests, scripts, configs, and artifacts on disk as implementation truth.
- Preserve unrelated worktree changes. Do not revert user changes.
- Use TDD for code changes: write the smallest meaningful failing test, implement the minimal code, then refactor.
- Do not broaden scope beyond the report. If the report and code disagree, prefer the report for target behavior and record the code gap.
- Keep progress facts in the report progress section only after they are repo-observed facts.

## Report Evidence To Anchor The Goal

```text
{chr(10).join(evidence)}
```

## Current Repo Scan Snapshot

Git status:

```text
{scan.git_status or "clean or unavailable"}
```

Git status truncated: `{str(scan.git_status_truncated).lower()}`

Expected report-aligned paths already present:

{format_list(scan.present_paths)}

Expected report-aligned paths currently missing:

{format_list(scan.missing_paths)}

Relevant tracked files sampled:

{format_list(scan.tracked_relevant_files[:60])}

Tests sampled:

{format_list(scan.test_files[:40])}

Scripts sampled:

{format_list(scan.script_files[:40])}

## Ralph Loop Launch

Recommended Claude Code invocation:

```bash
/ralph-loop "$(cat {repo.as_posix()}/docs/report/report-goal-prompt.md)" --max-iterations 20 --completion-promise "REPORT_GOAL_COMPLETE"
```

Ralph Loop re-feeds the same prompt after each session exit while preserving files and git history. Treat every iteration as a fresh-context resume from repo state.

## Gate Protocol

Execute the work as strict sequential gates. Do not start a later gate until the current gate has passing validation, updated `report-goal/status.md`, updated `report-goal/gap-matrix.md`, any required decision/source/final-summary updates, a Codex plugin gate-quality review, all blocking review findings resolved, and a git commit containing only the current gate's related changes.

1. Gate 0: Discovery and gap matrix. Produce `report-goal/gap-matrix.md`, `report-goal/status.md`, and `report-goal/decision-log.md`. Commit message: `docs(report-goal): complete gate 0 discovery`.
2. Gate 1: Contracts and scaffolding. Create the minimal modules, schemas, commands, and test skeletons required by the first report milestone. Commit message: `chore(report-goal): complete gate 1 scaffolding`.
3. Gate 2..N: Report milestones in order. For each milestone, write or update tests first, implement the smallest passing change, run validation, update gate docs, then commit with `feat(report-goal): complete gate <n> <short-name>`.
4. Final Gate: Integration and closeout. Run broad validation, verify key workflows, produce `report-goal/final-summary.md`, and commit with `docs(report-goal): complete final gate`.

Review rules: after local validation passes and before the gate commit, invoke the Codex plugin to review current gate quality. Prefer `/codex:adversarial-review --wait --scope working-tree "Review Gate <n> quality against {report.as_posix()} and report-goal/gap-matrix.md"` when slash commands are available. If slash commands are unavailable but the plugin runtime is installed, run the equivalent Codex companion command. Save the review output to `report-goal/reviews/gate-<n>-codex-review.md`. Resolve every BLOCK, Critical, and Important finding, rerun validation, and rerun Codex review before committing. If the Codex plugin is unavailable, record the exact reason in `report-goal/status.md` and stop for user decision.

Commit rules: inspect `git status` before staging, stage only files changed for the current gate, preserve unrelated user changes, and do not commit failing work or unreviewed gate work. If unrelated dirty files make a clean gate commit impossible, stop and ask the user.

## Ralph Loop Iteration Rules

At the start of every iteration, read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent `git log --oneline -5`, and `git status --short`. If these files do not exist, begin with Gate 0. Select only the earliest incomplete gate. Do not redo a gate that already has passing evidence and a matching git commit.

At the end of each iteration, leave the repository in one of three states: a completed gate reviewed by Codex and committed to git; a documented blocker in `report-goal/status.md`; or a user-decision stop. Never output `REPORT_GOAL_COMPLETE` until the Final Gate is complete, all validations and Codex gate reviews have passed or been explicitly deferred by the user, and `report-goal/final-summary.md` exists. If a completion promise is configured, output it only as the final line and only when it is unequivocally true.

## Execution Order

1. Build an implementation gap matrix from `{report.as_posix()}` against the repo. Include modules, scripts, tests, artifacts, commands, and report gates.
2. Implement the first missing gate in the report-defined order. Follow the report's own gate sequence without assuming a specific project domain.
3. Add or update tests for the implemented gate. Prefer small CPU/unit tests for contracts and smoke tests for integration boundaries.
4. Run the smallest relevant test command. Expand to broader tests only after the focused gate passes.
5. Produce artifacts required by the report gate. Follow the report's own artifact definitions for the corresponding milestones.
6. Update report progress only with observed facts, then rerender PDF/Markdown if report sources changed.
7. Continue to the next report gate until all design requirements are implemented, verified, or blocked with concrete evidence.

## Stop Rules

- Stop training or optimization work if the report says an earlier evaluator, audit, diagnostic, or reranking gate has not passed.
- Do not implement any optimization before the report-defined earlier gate passes.
- Do not continue legacy component patching if the report requires new module boundaries.
- Do not claim completion from smoke tests when the report requires heldout, multi-seed, or artifact-level gates.
- If GPU/model/data access is unavailable, create deterministic unit tests and document the exact blocked command, missing resource, and next executable command.

## Completion Criteria

The goal is complete only when:

- The repo contains the report-required modules, scripts, tests, and artifact schemas.
- Each report milestone is marked passed, failed, or externally blocked with evidence.
- The relevant tests and checks pass, including formatting and report render checks when report sources change.
- The final response lists completed gates, remaining blocked gates, commands run, artifact paths, and the next single executable step if anything remains.
"""


def build_prompt(repo: Path, report: Path, evidence: list[str], scan: ScanResult, style: str) -> str:
    if style == "full":
        return build_full_prompt(repo, report, evidence, scan)
    return build_short_prompt(repo, report, evidence, scan)


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

    evidence = extract_report_evidence(report, args.max_report_lines)
    scan = scan_repo(repo)
    prompt = build_prompt(repo, report, evidence, scan, args.style)

    if args.out:
        out = (repo / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        print(f"[OK] wrote goal prompt: {out}")
    if args.print or not args.out:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
