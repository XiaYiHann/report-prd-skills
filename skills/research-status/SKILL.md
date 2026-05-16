---
name: research-status
description: "Use when the user asks for the current research-loop status, active epoch, active gate/task, blockers, validation state, baseline lock state, or evidence gate state without executing or modifying research."
---

# Research Status

## Purpose

Report the current `docs/research/` state as a read-only status snapshot.

This skill answers “where are we now?” It does not initialize a workspace, advance
`TASK_QUEUE.yaml`, refresh `goal.md`, modify `RESEARCH_DIRECTION.md`, create
`Vn+1`, run experiments, or admit claims.

## Read Order

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/BASELINE_LOCK.yaml`
7. `docs/research/{CURRENT}/EVIDENCE_GATE.yaml`
8. `docs/research/{CURRENT}/HUMAN_REVIEW_REQUESTS.yaml`

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

- workspace role: meta-framework, epoch workspace, legacy/mixed, or missing;
- active version and `STATUS.yaml.status`;
- current gate and active task from `TASK_QUEUE.yaml`;
- declared RQs from `RESEARCH_SPINE.yaml`;
- baseline lock status;
- evidence gate state: draft claims, allowed claims, next required gate;
- validators: `direction-ready`, `epoch-ready`, `rq-driven-ready`, `baseline-lock-ready`, `goal-ready`, `loop-ready`;
- blockers and human review requests.

## Boundaries

- Do not write files.
- Do not treat validator failure as research failure; report it as current protocol state.
- Do not convert draft claims into allowed claims.
- Do not infer scientific conclusions from clean status output.
