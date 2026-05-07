---
name: report-goal
description: "Generate a long-running Codex Goal prompt from a PRD report. Use when the user wants to scan the current repository, compare implementation status against docs/report/report.md or another generated report.md, identify gaps, and produce a self-contained prompt for Codex Goal mode or another autonomous agent to execute until the report design is implemented."
---

# Report Goal

## Overview

Use this skill to turn a PRD report into an execution-grade Goal prompt. The output is a prompt, not an implementation patch, unless the user explicitly asks to start the goal.

The canonical source is `docs/report/report.md` unless the user names another report file. The prompt must cite the report path and tell the future agent to reread it before acting.

## Workflow

1. Resolve the repository root and report file.
2. Read `AGENTS.md` if present, then read the report file.
3. Scan the repository for implementation evidence, tests, scripts, configs, artifacts, and existing modules related to the report.
4. Compare report-required milestones against repo-observed implementation status.
5. Generate one self-contained Goal prompt using the standard report-backed execution template: Ralph Loop Launch, Mission, Source Of Truth, Initial Discovery Phase, Gap Matrix, Gate Protocol, Ralph Loop Iteration Rules, Execution Rules, Scope Control, Web Search Policy, and Completion Criteria.
6. Do not call `create_goal` unless the user explicitly asks to start the goal in this turn.

## Preferred Script

Run the bundled script from the repository root:

```bash
python3 ~/.agents/skills/report-goal/scripts/generate_report_goal_prompt.py \
  --repo . \
  --report docs/report/report.md \
  --out docs/report/report-goal-prompt.md
```

Use `--print` if the user wants the prompt in the chat. Use `--max-report-lines` to limit extracted report evidence for very large reports.
The default output is a compact template prompt. Use `--style full` only when the user explicitly asks for a detailed scan prompt with long repository listings.

## Ralph Loop Adaptation

The generated prompt must be safe for Claude Code Ralph Loop usage. Ralph Loop repeats the same prompt across sessions while preserving files and git history, so the prompt must be idempotent and resume from repository state.

Include a recommended invocation:

```bash
/ralph-loop "$(cat docs/report/report-goal-prompt.md)" --max-iterations 20 --completion-promise "REPORT_GOAL_COMPLETE"
```

Require every iteration to read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent git log, and current git status before choosing work. Require the agent to select only the earliest incomplete gate and never redo a gate that already has passing evidence plus a matching commit.

The generated prompt must instruct the future agent to output `REPORT_GOAL_COMPLETE` only when the Final Gate is complete, validation evidence exists, and `report-goal/final-summary.md` exists. This prevents false completion promises from prematurely terminating Ralph Loop.

## Prompt Requirements

The generated prompt must require the future agent to:

- Treat `report.md` as design truth and current code/tests/artifacts as implementation truth.
- Rebuild context from disk before changing files.
- Preserve unrelated worktree changes.
- Implement in milestone order from the report, not by convenience.
- Use TDD for code changes.
- Require `report-goal/gap-matrix.md` before implementation starts.
- Require milestone progress in `report-goal/status.md`.
- Require decisions in `report-goal/decision-log.md`.
- Require external references in `report-goal/sources.md` when web search is used.
- Require a closeout in `report-goal/final-summary.md`.
- Require strict sequential gates: Gate 0 discovery, Gate 1 contracts/scaffolding, Gate 2..N report milestones, Final Gate integration/closeout.
- Require every gate to pass validation and produce a git commit before the next gate starts.
- Require clean commit hygiene: stage only current-gate files, preserve unrelated user changes, and stop for user input if unrelated dirty files prevent an isolated gate commit.
- Avoid broad rewrites unless the report explicitly requires them.
- Record gaps that remain blocked by missing model weights, hardware, credentials, or external services.
- Run the smallest meaningful tests first, then broader verification.
- Update report progress only after observed implementation facts exist.

For research PRDs that define custom implementation-phase constraints, the prompt must preserve those constraints when present in the report.

## Output Shape

Return:

- `Prompt path`: the generated prompt file.
- `Source report`: the report file used.
- `Implementation scan summary`: concise counts of matched files, missing modules, tests, and scripts.
- `How to use`: one sentence saying the prompt can be used as the Goal objective.

If the repository has no report file, stop and ask for the report path.
