---
name: report-goal
description: "Use when the user wants a long-running Codex Goal prompt from a docs/report workspace, especially when main, paper, and spec products must be checked for consistency and compiled into milestone-gated AI execution."
---

# Report Goal

## Overview

Use this skill to turn a report workspace into an execution-grade Goal prompt. The output is a prompt, not an implementation patch, unless the user explicitly asks to start the goal.

The preferred report workspace is slug-local and has three derived products:

- `docs/report/<slug>/main/`：人类设计真源，定义研究与工程意图。
- `docs/report/<slug>/paper/`：学术表达真源，定义顶会论文叙事与 placeholder。
- `docs/report/<slug>/spec/`：机器执行真源，唯一决定 milestone 顺序、gate、task、harness、artifact 与 evidence 准入。

`report-goal` must read all three products, but it must not give them equal execution authority. `main` and `paper` can create alignment work only. Implementation and experiment execution can proceed only from `spec`.

If `spec/` is missing, structurally invalid, or not execution-ready, generate only a Chinese `spec 修复目标` that asks the agent to use `report-spec` or repair `spec/`. If `spec/` is ready but `main/` or `paper/` is missing or inconsistent with `spec/`, generate only a Chinese `三产物对齐目标`. Generate a Chinese long-running implementation goal only when the three products exist and `spec/` is execution-ready. Use `--allow-legacy-prose-goal` only when the user explicitly wants the older prose-derived behavior.

## Workflow

1. Resolve the repository root, report file, and active `docs/report/<slug>/` workspace.
2. Read `AGENTS.md` if present, then inspect `main/`, `paper/`, and `spec/`.
3. Scan the repository for implementation evidence, tests, scripts, configs, artifacts, and existing modules related to the report.
4. Validate `spec/task_graph.yaml`, `spec/harness.yaml`, `spec/evidence_contract.yaml`, and `spec/experiment_manifest.yaml` when present.
5. Check paper placeholders against `spec` experiment IDs or evidence contracts.
6. If `spec` is not execution-ready, generate a Chinese `spec 修复目标`.
7. If `spec` is ready but `main` / `paper` / `spec` are incomplete or inconsistent, generate a Chinese `三产物对齐目标`.
8. If all three products are ready, compile one self-contained Chinese long-running execution Goal prompt from `spec`, with `main` and `paper` used only as consistency context.
9. Do not call `create_goal` unless the user explicitly asks to start the goal in this turn.

## Preferred Script

Run the bundled script from the repository root:

```bash
python3 ~/.agents/skills/report-goal/scripts/generate_report_goal_prompt.py \
  --repo . \
  --report docs/report/report.md \
  --out docs/report/report-goal-prompt.md
```

Use `--print` if the user wants the prompt in the chat. Use `--max-report-lines` to limit extracted report evidence for very large reports.
The default output is a compact Chinese three-artifact-gated prompt when `docs/report/<slug>/main|paper|spec` exists. User-visible prompt headings and instructions should be Chinese by default. Legacy manifest gating is retained only for older workspaces that do not yet have the three-product layout. Use `--style full` only with `--allow-legacy-prose-goal` when the user explicitly asks for the older detailed scan prompt with longer repository listings.

Compatibility escape hatch:

```bash
python3 ~/.agents/skills/report-goal/scripts/generate_report_goal_prompt.py \
  --repo . \
  --report docs/report/report.md \
  --out docs/report/report-goal-prompt.md \
  --allow-legacy-prose-goal
```

## Core Principle

Do not hardcode project-specific gates, module paths, datasets, models, or artifacts in the skill. The skill must compile them from the selected workspace and current repository.

The template is only a structure for Ralph Loop execution. In three-artifact mode, generated implementation content must obey these authority rules:

- 目标与设计解释：来自 `main/`。
- 论文完整性与 placeholder 义务：来自 `paper/`。
- milestone 顺序、gate、task contract、harness command、artifact path 和 evidence 准入：只能来自 `spec/`。
- research claim 执行：只能来自 `spec/experiment_manifest.yaml` 与 `spec/evidence_contract.yaml`。
- 约束：来自 `spec`、`main` non-goals，以及本地 `AGENTS.md` / `RTK.md`。

The generated prompt must explicitly forbid inferring experiments, datasets, baselines, metrics, seeds, models, tasks, or results from the paper.

## Language

Generate the Goal prompt in Chinese by default. Keep command names, file paths, status labels, git commit messages, and the completion promise literal unchanged when they are machine-facing values.

## Ralph Loop Adaptation

The generated prompt must be safe for Claude Code Ralph Loop usage. Ralph Loop repeats the same prompt across sessions while preserving files and git history, so the prompt must be idempotent and resume from repository state.

Include a recommended invocation:

```bash
/ralph-loop:ralph-loop "$(cat docs/report/report-goal-prompt.md)" --completion-promise "REPORT_GOAL_COMPLETE"
```

Require every iteration to read `report-goal/status.md`, `report-goal/gap-matrix.md`, `report-goal/decision-log.md`, recent git log, and current git status before choosing work. Require the agent to select only the earliest incomplete gate and never redo a gate that already has passing evidence plus a matching commit.

The generated prompt must instruct the future agent to output `REPORT_GOAL_COMPLETE` only when the Final Gate is complete, validation evidence exists, and `report-goal/final-summary.md` exists. This prevents false completion promises from prematurely terminating Ralph Loop.

## Prompt Requirements

The generated prompt must require the future agent to:

- Treat `main/` as 人类设计真源 and current code/tests/artifacts as implementation truth.
- Treat `paper/` as 学术表达真源, not an execution source.
- Treat `spec/` as 机器执行真源 for milestone order, gate progression, harness commands, artifact paths, and evidence links.
- Rebuild context from disk before changing files.
- Preserve unrelated worktree changes.
- Implement in `spec/task_graph.yaml` milestone order, not by convenience.
- Use TDD for code changes.
- Require `report-goal/gap-matrix.md` before implementation starts.
- Require milestone progress in `report-goal/status.md`.
- Require decisions in `report-goal/decision-log.md`.
- Require external references in `report-goal/sources.md` when web search is used.
- Require a closeout in `report-goal/final-summary.md`.
- Require strict sequential gates: Gate 0 discovery, Gate 1 contracts/scaffolding, Gate 2..N report milestones, Final Gate integration/closeout.
- Require inner gate before outer gate: every gate must have passing tests (inner gate) before invoking Codex plugin gate-quality review (outer gate). No outer review without inner gate pass, per ThoughtWorks methodology.
- Require every gate to pass inner gate (tests), pass outer gate (Codex review), resolve blocking review findings, and produce a git commit before the next gate starts.
- Require Codex review output to be saved under `report-goal/reviews/gate-<n>-codex-review.md`.
- Require `/codex:adversarial-review --wait --scope working-tree` as the preferred gate-quality review path when the Codex plugin is available.
- Require the future agent to stop for user decision if the Codex plugin is unavailable, unless the user explicitly allows a fallback reviewer.
- Require clean commit hygiene: stage only current-gate files, preserve unrelated user changes, and stop for user input if unrelated dirty files prevent an isolated gate commit.
- Require evidence over claims: test output must be saved to `report-goal/evidence/gate-<n>-test-output.txt`. Reject "should work" or "based on code structure" as verification.
- Require every evidence entry to link to a manifest-declared `task_id`, `harness_id`, artifact path, command, and commit.
- Require every milestone to have an explicit gate and every current milestone gate to be fully complete before the next milestone begins.
- Require `paper` updates to preserve placeholders until evidence contract accepts real evidence.
- Require Final Gate to verify `main` / `paper` / `spec` consistency before `REPORT_GOAL_COMPLETE`.
- Require independent test re-run after agent claims pass, not just agent self-report.
- Require tautological test detection in Codex review: tests must validate the specification, not the implementation.
- Require integration check: new code must be wired into call chains. Unconnected functions are a gate failure.
- Require TODO/FIXME detection before gate commit: each TODO must be logged in `report-goal/decision-log.md`.
- Avoid broad rewrites unless the report explicitly requires them.
- Record gaps that remain blocked by missing model weights, hardware, credentials, or external services.
- Run the smallest meaningful tests first, then broader verification.
- Update report progress only after observed implementation facts exist.

For research PRDs that define custom implementation-phase constraints, the prompt must preserve those constraints when present in the report.

## Anti-Patterns

Avoid these failures:

- Do not emit only a generic "scan repo and implement report" template.
- Do not generate an implementation goal when `spec/` is missing or invalid.
- Do not use `paper/` as an execution source.
- Do not let `main/` prose create executable tasks that are absent from `spec`.
- Do not hardcode CIGR, OLMoE, GSM8K, DAO, Ares, or any other project into the script.
- Do not use fake placeholder paths such as `src/core/module_a.py`.
- Do not treat report prose as implementation proof.
- Do not use mock, toy, synthetic, stub, proxy, or cached evidence as final gate or research claim evidence.
- Do not omit report line references for extracted goals and gates.
- Do not let the generated prompt ask the future agent to rediscover everything without carrying forward the script's report extraction and scan summary.

## Output Shape

Return:

- `Prompt path`: the generated prompt file.
- `Source report`: the report file used.
- `Implementation scan summary`: concise counts of matched files, missing modules, tests, and scripts.
- `How to use`: one sentence saying the prompt can be used as the Goal objective.

If the repository has no report file, stop and ask for the report path.
