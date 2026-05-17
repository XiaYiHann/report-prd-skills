---
name: research-status
description: "Use when the user asks for the current research-loop status, active epoch, active gate/task, blockers, validation state, baseline lock state, or evidence gate state without executing or modifying research."
---

# Research Status

## Purpose

Report the current `docs/research/` state as a read-only experiment progress
report.

This skill answers “what are we trying to prove, where are we in the current
experiment loop, what evidence is missing, and what can be done next?” It does
not initialize a workspace, advance `RESEARCH_SPINE.yaml` or `rqs/RQxx/TASKS.yaml`,
refresh `goal.md`, modify `RESEARCH_DIRECTION.md`, create `Vn+1`, run
experiments, or admit claims.

## Read Order

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
5. `docs/research/{CURRENT}/rqs/RQxx/TASKS.yaml`
6. `docs/research/{CURRENT}/TASK_QUEUE.yaml` (compatibility aggregate view)
7. `docs/research/{CURRENT}/BASELINE_LOCK.yaml`
8. `docs/research/{CURRENT}/EVIDENCE_GATE.yaml`
9. `docs/research/{CURRENT}/HUMAN_REVIEW_REQUESTS.yaml`
10. `docs/research/{CURRENT}/PRD_SUMMARY.md`
11. `docs/research/{CURRENT}/rqs/RQxx/RQ.md`
12. `docs/research/{CURRENT}/rqs/RQxx/SPEC.yaml`

## Command

```bash
python3 ~/.claude/skills/research-status/scripts/research_status.py \
  --repo /absolute/path/to/repo
```

Machine-readable output:

```bash
python3 ~/.claude/skills/research-status/scripts/research_status.py \
  --repo /absolute/path/to/repo \
  --json
```

## Report Contract

The report must distinguish:

- project-wide summary first: background, current goal, completed work, remaining work, blockers, and next step;
- workspace role: meta-framework, epoch workspace, legacy/mixed, or missing;
- beginner-facing plain-language summary: current state, missing/blocking condition,
  next step, verification command, and first files to read;
- active version and `STATUS.yaml.status`;
- current research goal: PRD title/purpose, Big RQ, core hypothesis, MVR status;
- current gate, declared RQs, and runnable RQ set from `RESEARCH_SPINE.yaml`,
  plus each RQ's local task progress, next RQ task, and experiment contract readiness;
- `TASK_QUEUE.yaml` only as a flat compatibility projection of the per-RQ task surface,
  including the current aggregated active task, required evidence, expected outputs,
  and harness predicate;
- gate/task progress across the current epoch, not just task counts;
- baseline lock status;
- evidence gate state: draft claims, allowed claims, next required gate, and
  conditions still blocking paper-admissible claims;
- wiki / closeout / next-version compounding surface when the current epoch is
  approaching closeout or has already accumulated reusable insight;
- blockers, human review requests, and dependency-free runnable tasks;
- blocker recovery hints: problem, triage classification, repair target, and verification command;
- next actions: continue runnable RQs, run independent ready tasks, or resolve
  blocker;
- validators: `direction-ready`, `epoch-ready`, `rq-driven-ready`, `baseline-lock-ready`, `goal-ready`, `loop-ready`;
- blockers and human review requests.

## Boundaries

- Do not write files.
- Do not treat validator failure as research failure; report it as current protocol state.
- Do not convert draft claims into allowed claims.
- Do not infer scientific conclusions from clean status output.
- Do not let `TASK_QUEUE.yaml` override `RESEARCH_SPINE.yaml` or `rqs/RQxx/TASKS.yaml`
  when they disagree.
- In the meta-framework repository, do not render epoch validators as “OK”; they
  are `N/A` because no repo-local project epoch should exist.
