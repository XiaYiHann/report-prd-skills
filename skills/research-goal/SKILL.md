---
name: research-goal
description: "Use when the user wants to generate or refresh docs/research/{CURRENT}/goal.md as a long-running AI execution goal for the active Vn epoch."
---

# Research Goal

## Purpose

Generate or refresh the active epoch `Vn/goal.md` and `Vn/GOAL_LOCK.yaml`.

This skill is a synthesis layer, not an executor. It does not run experiments,
does not create tasks, does not modify `RESEARCH_DIRECTION.md`, and does not
replace the internal Plan compiler, `RESEARCH_SPINE.yaml`, or `rqs/RQxx/TASKS.yaml`.

## Authority Chain

Read in order:

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/PRD.tex`
5. `docs/research/{CURRENT}/BASELINE_LOCK.yaml`
6. `docs/research/{CURRENT}/baselines/INDEX.yaml`
7. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
8. `docs/research/{CURRENT}/rqs/RQxx/SPEC.yaml`
9. `docs/research/{CURRENT}/rqs/RQxx/PLAN.md`
10. `docs/research/{CURRENT}/rqs/RQxx/TASKS.yaml`
11. `docs/research/{CURRENT}/TASK_QUEUE.yaml` (compatibility aggregate view)
12. `docs/research/{CURRENT}/wiki/*` when present

## Output Contract

`goal.md` must state:

- current Vn context and version-level objective, not merely a single-step action note;
- every declared RQ's plan/task contract refs and all queue tasks that belong to that RQ;
- the full version task dependency graph, including what each task does, dependency edges, waiting dependencies, blocked ancestors, unlocked descendants, runnable status, and RQ-local Spec/Plan refs;
- RQ 调度真源是 `RESEARCH_SPINE.yaml`，单个 RQ 的执行真源是 `rqs/RQxx/TASKS.yaml`，`TASK_QUEUE.yaml` 只是兼容聚合视图；
- orthogonal runnable tasks may continue, or run in parallel when executor support and file scopes allow；中文约定可称为“正交 runnable tasks”；while blocked branch tasks freeze only their explicit descendants;
- blocked / failed tasks must first enter code-review-first triage so the executor can distinguish implementation or harness defects from idea/spec defects before declaring the branch genuinely blocked;
- `goal.md` must include a `## Blocked Task Triage Review` section that records the code-review-first triage rule, review order, and classification rule for blocked tasks;
- blocked / failed tasks must emit `runs/TASK_XXX_blocker.md` with the triage conclusion, reviewed evidence, and recovery decision before gate-blocked handoff;
- `goal.md` must include a `## Drift Repair Then Execute Policy` section with `repair_then_execute`: when drift can be repaired against a single latest approved design source, repair stale contracts first, run `goal-ready` after the drift repair, and do not stop after a repair-only pass; continue executing the runnable task set until all goal tasks complete or a true human-owned blocker remains;
- baseline decisions come from `BASELINE_LOCK.yaml` and `baselines/INDEX.yaml`;
- no fabricated data, stdout/stderr, artifact, hash, citation, or paper result;
- stop conditions for stale contracts, blocked gates, human review, closeout, and Paper Binding;
- `goal.md` must include a `## Subagent Execution Contract` section with `prefer_subagents`: 优先使用 subagent 执行 bounded specialist work; dispatch literature, reproduction, coding, experiment, analysis, math, paper, and audit work to runtime-provided specialist workers/reviewers when available, while the repository-managed Claude template surface currently only ships `research-experiment`; the main controller remains responsible for state updates, gate decisions, and evidence admission.

`GOAL_LOCK.yaml` records:

- source refs and hashes;
- target executor (`codex`, `claude-code`, or `both`);
- staleness triggers;
- `goal_hash`;
- `goal-ready` as the validator mode.

## Command

```bash
python3 ~/.claude/skills/research-goal/scripts/generate_research_goal.py \
  --repo /absolute/path/to/repo \
  --target both
```

Use `--target claude-code` when preparing a Claude Code goal-mode handoff, and
`--target codex` when preparing a Codex goal-mode run.

Validate:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode goal-ready
```

## Boundaries

- Do not edit `RESEARCH_DIRECTION.md`.
- Do not create `Vn+1`.
- Do not bypass `RESEARCH_SPINE.yaml` or `rqs/RQxx/TASKS.yaml`.
- Do not turn a goal into empirical evidence.
- Do not let `goal.md` contradict `PRD.tex`, `BASELINE_LOCK.yaml`, RQ-local `SPEC.yaml`, `RESEARCH_SPINE.yaml`, or the compatibility contract encoded in `TASK_QUEUE.yaml`.
