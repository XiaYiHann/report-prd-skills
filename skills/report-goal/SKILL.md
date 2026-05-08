---
name: report-goal
description: "Generate a long-running Codex Goal prompt from a PRD report. Use when the user wants to scan the current repository, compare implementation status against docs/report/report.md or another generated report.md, identify gaps, and produce a self-contained prompt for Codex Goal mode or another autonomous agent to execute until the report design is implemented."
---

# Report Goal

## Overview

Use this skill to turn a PRD report into an execution-grade Goal prompt. The output is a prompt, not an implementation patch, unless the user explicitly asks to start the goal.

The canonical source is `docs/report/report.md` unless the user names another report file. The prompt must cite the report path and tell the future agent to reread it before acting.

`report-goal` is manifest-gated by default. It first validates the owning report workspace's execution manifests:

- `report.manifest.yaml`
- `tasks/task_graph.yaml`
- `harness/harness.yaml`
- `evidence/evidence_manifest.yaml`
- `experiments/experiment_manifest.yaml` for `research-prd`

If the manifests are missing, structurally invalid, or not execution-ready, generate a report-repair goal only. Do not generate an implementation goal from prose guesses. Use `--allow-legacy-prose-goal` only when the user explicitly wants the older prose-derived behavior.

## Workflow

1. Resolve the repository root and report file.
2. Read `AGENTS.md` if present, then read the report file.
3. Scan the repository for implementation evidence, tests, scripts, configs, artifacts, and existing modules related to the report.
4. Resolve and validate the execution manifests for the report workspace.
5. If manifests are not execution-ready, generate a Chinese report-repair goal whose only objective is to complete deep-spec lowering and harness/evidence contracts.
6. If manifests are execution-ready, compile one self-contained Chinese implementation Goal prompt from `task_graph.yaml` and `harness.yaml`, with the report prose used only as design explanation.
7. Do not call `create_goal` unless the user explicitly asks to start the goal in this turn.

## Preferred Script

Run the bundled script from the repository root:

```bash
python3 ~/.agents/skills/report-goal/scripts/generate_report_goal_prompt.py \
  --repo . \
  --report docs/report/report.md \
  --out docs/report/report-goal-prompt.md
```

Use `--print` if the user wants the prompt in the chat. Use `--max-report-lines` to limit extracted report evidence for very large reports.
The default output is a compact Chinese manifest-gated prompt. Use `--style full` only with `--allow-legacy-prose-goal` when the user explicitly asks for the older detailed scan prompt with longer repository listings.

Compatibility escape hatch:

```bash
python3 ~/.agents/skills/report-goal/scripts/generate_report_goal_prompt.py \
  --repo . \
  --report docs/report/report.md \
  --out docs/report/report-goal-prompt.md \
  --allow-legacy-prose-goal
```

## Core Principle

Do not hardcode project-specific gates, module paths, datasets, models, or artifacts in the skill. The skill must infer them from the selected report and the current repository. If the report is CIGR, the output may contain CIGR-specific gates because they were extracted from that report. If the report is DAO, Ares, or another project, the output must naturally contain that project's gates, paths, commands, and validation evidence.

The template is only a structure for Ralph Loop execution. In manifest-gated mode, the generated implementation content must be concrete to the selected manifest:

- Objective: derived from the manifest title and report summary.
- Gates and task order: derived from `tasks/task_graph.yaml`.
- Commands and pass/fail surface: derived from `harness/harness.yaml`.
- Completion evidence: derived from `evidence/evidence_manifest.yaml`.
- Research claim execution: derived from `experiments/experiment_manifest.yaml`.
- Constraints: derived from manifest contracts, report non-goals, and local `AGENTS.md` / `RTK.md`.

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

- Treat `report.md` as design truth and current code/tests/artifacts as implementation truth.
- Treat execution manifests as machine truth for task order, harness commands, artifact paths, and evidence links.
- Rebuild context from disk before changing files.
- Preserve unrelated worktree changes.
- Implement in `task_graph.yaml` order, not by convenience.
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
- Do not generate an implementation goal when execution manifests are missing or invalid.
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
