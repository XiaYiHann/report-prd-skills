---
name: research-audit
description: "Use when landed research artifacts may be stale, inconsistent, or drifted across PRD, Paper, Spec, Plans, PPT, and artifacts."
---

# Research Audit

## Overview

Audit already-written files. This is not a paper review only; it is a cross-file drift detector for:

- RESEARCH_DIRECTION.md
- CURRENT
- Current `Vn`
- PRD
- Paper
- Spec
- Plans
- PPT
- artifacts if present

It is also the format gatekeeper, migration guide, Git checkpoint auditor, and Paper Binding guard for epoch_v1.

## Audit Modes

Conceptual `/research audit` modes:

- `format` — checks epoch_v1 files, template metadata, agent docs, `AGENTS.md`, `CLAUDE.md`.
- `migration` — detects legacy flat layout and writes migration guidance.
- `epoch` — checks current `Vn` authority chain, task queue, next action, wiki, closeout.
- `git` — checks `GIT_STATE.yaml`, task commit hashes, dirty tree, closeout/paper binding commits.
- `evidence` — checks artifact/evidence eligibility and anti-mock rules.
- `paper-binding` — checks Paper Binding gates.
- `full` — runs all relevant audit families.

CLI scaffold:

```bash
python3 ~/.claude/skills/research-audit/scripts/generate_research_audit.py \
  --repo /absolute/path/to/repo \
  --mode migration
```

## Required Questions

- Does current `Vn/PRD.md`, `Vn/PLAN.md`, or `Vn/NEXT_ACTION.md` exceed the Research Corridor?
- Has any agent modified `RESEARCH_DIRECTION.md` without explicit user instruction?
- Does `CURRENT` match `Vn/STATUS.yaml.version`?
- Is the active task in `TASK_QUEUE.yaml` the same as `NEXT_ACTION.md`?
- Is there exactly one active task?
- Was `Vn+1` created before current `Vn/closeout.md` and closed status?
- PRD updated but paper not updated?
- PRD updated but spec not updated?
- Spec updated but existing plan is stale?
- Paper has an experiment not in spec?
- Plan has a task or harness not in spec?
- Spec has an experiment not in PRD?
- PPT has claim or result not grounded in PRD, paper, or spec?
- Are there insights in `docs/research/insights/` not reflected in the latest spec?
- Are there open pivot proposals without human decision?
- Are negative results hidden (not logged)?
- Does the PRD still claim something contradicted by a recorded insight?
- Are diagnostic experiments proposed but not scheduled in spec/plan?
- Is an old-version artifact used for a current claim without explicit `carry_forward` in current PRD or SPEC?
- Is paper binding attempted before `closed_stable` or `paper_binding_ready`?
- Is exploratory-only or prompt-only evidence used as a main result?
- Does `GIT_STATE.yaml` exist?
- Are done tasks missing commit hashes?
- Is closeout or paper binding attempted with a dirty tree?
- Does the workspace look `epoch_v1`, `legacy_flat`, `mixed`, or `unknown`?

## Outputs

`docs/research/audits/YYYY-MM-DD-audit/`:

- `audit_report.md`
- `alignment_matrix.yaml`
- `drift_findings.yaml`
- `repair_plan.md`

`repair_plan.md` now splits repairs into:
- **must-fix-before-execution** (execution failures)
- **insight-opportunity** (research failures / anomalies / diagnostic experiments)
- **can-fix-later**
- **recommended next research-plan target**
- **recommended next insight-feedback target**

## Command

```bash
python3 ~/.claude/skills/research-audit/scripts/generate_research_audit.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09

python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode audit-ready
```

`repair_plan.md` must separate must-fix-before-execution, can-fix-later, and recommended next `research-plan` target.

## Epoch Audit Rules

- Audit current `Vn` first; legacy folders are context unless `CURRENT` is absent.
- Old versions may contribute hypothesis seeds and history, not current claim evidence.
- Wiki and closeout completeness are gates for `closeout-ready`.
- Paper/PPT claims must not exceed `PAPER_BINDING_DECISION.md`.

## Migration Audit Rules

Audit may detect, classify, generate `MIGRATION_AUDIT.md`, generate `MIGRATION_PLAN.md`, and point out blockers. It must not default to moving old artifacts, rewriting PRD research claims, treating old insight as paper evidence, or marking a legacy project epoch-ready.

Legacy migration should become an explicit task such as `TASK_MIGRATE_LEGACY_TO_V0`.
