---
name: research-plan
description: "Use when a dated research execution run needs a bounded plan, AI loop prompt, source hashes, gates, or harness scope from Research Spec."
---

# Research Plan

## Overview

Create dated concrete execution plans under `docs/research/plans/YYYY-MM-DD-purpose/`. A plan is a bounded run contract for Codex or Claude Code. It is derived from `docs/research/spec/`, not from the paper.

## Supported Tracks

- `reproduction`
- `implementation`
- `experiment`
- `paper-update`

Supported selectors:

- `--gate G_ID`
- `--target codex`
- `--target ralph-loop`

## Outputs

- `plan.md`
- `plan.yaml`
- `ai_loop_prompt.md`
- `current_state.md`
- `blocker_log.md`
- `decision_log.md`
- `run_log.md`
- `final_summary.md`

## Command

```bash
python3 ~/.agents/skills/research-plan/scripts/generate_research_plan.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09 \
  --purpose reproduce-b01 \
  --track reproduction \
  --target codex
```

Validate:

```bash
python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode plan-ready
```

## AI Loop Contract

`ai_loop_prompt.md` must say:

- executable source of truth is `docs/research/spec/`;
- PRD is human research truth;
- Paper is narrative target and placeholder map only;
- do not infer experiments from paper;
- execute the earliest incomplete gate;
- run declared harnesses and save stdout/stderr;
- update state, blocker, decision, run, and final summary logs;
- do not mock missing datasets, baselines, metrics, or results.
