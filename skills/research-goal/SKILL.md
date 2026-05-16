---
name: research-goal
description: "Use when the user wants to generate or refresh docs/research/{CURRENT}/goal.md as a long-running AI execution goal for the active Vn epoch."
---

# Research Goal

## Purpose

Generate or refresh the active epoch `Vn/goal.md` and `Vn/GOAL_LOCK.yaml`.

This skill is a synthesis layer, not an executor. It does not run experiments,
does not create tasks, does not modify `RESEARCH_DIRECTION.md`, and does not
replace the internal Plan compiler or `TASK_QUEUE.yaml`.

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
11. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
12. `docs/research/{CURRENT}/wiki/*` when present

## Output Contract

`goal.md` must state:

- current Vn context and active gate/task;
- all outstanding tasks across every declared RQ, including dependency edges and RQ-local Spec/Plan refs;
- `TASK_QUEUE.yaml` remains the single-step execution source;
- blocked branch tasks do not stop independent runnable tasks whose `depends_on` edges are already satisfied;
- baseline decisions come from `BASELINE_LOCK.yaml` and `baselines/INDEX.yaml`;
- no fabricated data, stdout/stderr, artifact, hash, citation, or paper result;
- stop conditions for stale contracts, blocked gates, human review, closeout, and Paper Binding;
- subagent dispatch rules for literature, reproduction, coding, experiment, analysis, paper, and audit work.

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
- Do not bypass `TASK_QUEUE.yaml`.
- Do not turn a goal into empirical evidence.
- Do not let `goal.md` contradict `PRD.tex`, `BASELINE_LOCK.yaml`, RQ-local `SPEC.yaml`, or `RESEARCH_SPINE.yaml`.
