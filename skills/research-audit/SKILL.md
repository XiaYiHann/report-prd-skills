---
name: research-audit
description: "Use when landed research artifacts may be stale, inconsistent, or drifted across PRD, Paper, Spec, Plans, artifacts, and insights."
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
- artifacts if present

It is also the format gatekeeper, migration guide, Git checkpoint auditor, and Paper Binding guard for epoch_v1.

Audit is a hard gate, not only a scaffold generator. In epoch workspaces it must emit machine-readable PASS/WARN/FAIL checks, and P0/P1 failures block closeout promotion or Paper Binding. Codex / Claude Code remain the agent executors; audit verifies their submitted run reports, commands, artifact hashes, git evidence, and carry_forward declarations. It does not run an independent backend and must not treat prompt-only scaffold as result evidence.

Gate-aware audit must distinguish execution failure from research falsification. `failed_execution` means code, environment, dependency, timeout, or process failure; `failed_harness` means the verification predicate or artifact schema failed. Neither status can be interpreted as a falsified research hypothesis. A Gate may be marked `falsified` only after a `research_falsification_candidate` has valid harness outputs and adversarial audit rules out code, data, metric, harness, environment, PRD, and SPEC defects.

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
- Is `RESEARCH_DIRECTION.md` structurally complete: Direction Status, Research Seed, Research Corridor, Out-of-Scope Directions, Prior Work Basis, Desired Paper Shape, Autonomy Boundary, and Global Stop Conditions?
- Does Direction Status include `direction_id`, `status`, `created_at`, `updated_at`, `current_version`, `final_target`, and `owner_decision_required`?
- Is Direction status `human_approved` or `frozen` before execution/paper-binding claims proceed?
- Are Research Corridor, Out-of-Scope Directions, Autonomy Boundary, and Global Stop Conditions non-empty and non-placeholder?
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
- Do full experiments declare and verify real dataset provenance, real model/code provenance, frozen split, and non-smoke execution?
- Does any claim-supporting reproduction rely only on smoke, mock, toy, synthetic, stub, cached, or proxy output?
- Are there current-epoch insights in `Vn/wiki/*` not reflected in Spec, Plan, closeout, or Paper Binding decisions?
- Are there legacy insights in `docs/research/insights/` that should be migrated, archived, or explicitly ignored?
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

`alignment_matrix.yaml` must include `direction_completeness`; direction blockers should also appear in `audit_report.md`, `drift_findings.yaml`, and the must-fix section of `repair_plan.md`.

Current epoch audits also write machine-readable results to `docs/research/{CURRENT}/audits/YYYY-MM-DD-audit/audit_results.yaml`.

`repair_plan.md` now splits repairs into:
- **must-fix-before-execution** (execution failures)
- **insight-opportunity** (research failures / anomalies / diagnostic experiments; hand off to `research-insight`)
- **can-fix-later**
- **recommended next research-plan target**
- **recommended next research-insight target**

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
- Paper claims must not exceed `PAPER_BINDING_DECISION.md`.

## Migration Audit Rules

Audit may detect, classify, generate `MIGRATION_AUDIT.md`, generate `MIGRATION_PLAN.md`, and point out blockers. It must not default to moving old artifacts, rewriting PRD research claims, treating old insight as paper evidence, or marking a legacy project epoch-ready.

Legacy migration should become an explicit task such as `TASK_MIGRATE_LEGACY_TO_V0`.

Legacy `docs/research/insights/` is compatibility storage. Audit should prefer current `Vn/wiki/*` for epoch_v1 and flag unpromoted legacy insight as migration material, not current evidence.
