---
name: research-audit
description: "Use when existing research artifacts may be stale, inconsistent, or drifted across PRD, Paper, Spec, Plans, artifacts, and insights."
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

It is also the RQ-driven format gatekeeper, migration guide, Git checkpoint auditor, and Paper Binding guard for epoch_v1.

Audit is a hard gate, not only a scaffold generator. In epoch workspaces it must emit machine-readable PASS/WARN/FAIL checks, and P0/P1 failures block closeout promotion or Paper Binding. Codex / Claude Code remain the agent executors; audit verifies their submitted run reports, commands, artifact hashes, git evidence, and carry_forward declarations. It does not run an independent backend and must not treat prompt-only scaffold as result evidence.

Gate-aware audit must distinguish execution failure from research falsification. `failed_execution` means code, environment, dependency, timeout, or process failure; `failed_harness` means the verification predicate or artifact schema failed. Neither status can be interpreted as a falsified research hypothesis. A Gate may be marked `falsified` only after a `research_falsification_candidate` has valid harness outputs and adversarial audit rules out code, data, metric, harness, environment, PRD, and SPEC defects.

Reproduction audit uses `docs/research/agent/REPRODUCTION_POLICY.md` as the authoritative source for reproduction types, status values, and evidence levels. It uses `docs/research/agent/REPRODUCTION_AUDIT_POLICY.md` as the execution standard for gatekeeper output format and claim support rules. Both skills must keep these two files aligned. It must inspect `BASELINE_LOCK.yaml`, `baselines/INDEX.yaml`, selected baseline dossier cards, `REPRODUCTION_INDEX.yaml`, `PAPER_CLAIM_LEDGER.yaml`, search logs, run reports, and artifact hashes. Allowed paper claims require a compatible reproduction `claim_support_level`; `literature_only`, `official_smoke_only`, `failed_but_informative`, missing audit, or `claim_support_level: sanity_only | none` cannot support allowed paper claims.

**PAPER_CLAIM_LEDGER.yaml vs RESEARCH_SPINE.yaml**: `RESEARCH_SPINE.yaml` is the planning spine (RQ → Claim → Experiment → Evidence → Figure/Table → Paper Section). `PAPER_CLAIM_LEDGER.yaml` is the binding gate: it records which claims are `allowed` to enter the paper, their reproduction evidence compatibility, and audit status. Audit must verify that every `allowed` claim in the Ledger has a corresponding entry in the Spine and meets reproduction evidence requirements.

## Skill Invocation Contract

Conceptual command forms:

```text
/research audit
/research audit --mode format
/research audit --mode migration
/research audit --mode epoch
/research audit --mode git
/research audit --mode evidence
/research audit --mode paper-binding
/research audit --mode full
```

`/research audit` is invoked through the `research` controller. It does not run as a top-level skill outside the research loop.

## Audit Modes

- `format` — checks epoch_v1 file structure, standard RQ-driven layout, version-level `BASELINE_LOCK.yaml`, `baselines/INDEX.yaml`, selected baseline dossier refs, template metadata, the fixed Big-RQ `RESEARCH_DIRECTION.md` template, `RESEARCH_SPINE.yaml` chain integrity (`direction_ref`, RQ→Claim→Experiment→Evidence→Figure/Table→Paper Section), `ai_loop_prompt.md` required clauses, agent docs, `AGENTS.md`, `CLAUDE.md`, and the `## Research Agent Behavior Contract` / `## 研究智能体行为契约` section with all 10 required rules. Returns PASS/WARN/FAIL with severity.
- `migration` — detects workspace type (`unknown`, `legacy_flat`, `mixed`, `epoch_v1`) and RQ-driven status (`standard`, `migration_recommended`, `migration_required`), then writes detailed `MIGRATION_AUDIT.md` + `MIGRATION_PLAN.md` with phase-by-phase guidance, including how to bind `direction_ref`, create `Vn/baselines/`, create `Vn/rqs/RQxx/`, split legacy Spec/Plan into RQ-local contracts, and populate the Spine Matrix. Does not default to moving old artifacts or rewriting research claims.
- `epoch` — checks current `Vn` authority chain, task queue, next action, wiki, closeout.
- `git` — checks `GIT_STATE.yaml`, task commit hashes, dirty tree, closeout/paper binding commits.
- `evidence` — checks artifact/evidence eligibility and anti-mock rules.
- `paper-binding` — checks Paper Binding gates.
- `full` — runs all relevant audit families (epoch schema + format + evidence).

CLI scaffold:

```bash
python3 ~/.claude/skills/research-audit/scripts/generate_research_audit.py \
  --repo /absolute/path/to/repo \
  --mode migration
```

## Required Questions

- Does current `Vn/PRD.tex`, `Vn/RESEARCH_SPINE.yaml`, RQ-local `PLAN.md`, or `Vn/TASK_QUEUE.yaml` exceed the Research Corridor?
- Is `RESEARCH_DIRECTION.md` structurally complete under the fixed Big-RQ template: Direction Status, Big Research Question, Why This Question Matters, Core Hypothesis, Research Corridor, Out-of-Scope Directions, Minimum Viable Research, Evidence Contract, Global Stop Conditions, Autonomy Boundary, and Spine Binding?
- Does Direction Status include `direction_id`, `status`, `created_at`, `updated_at`, `current_version`, `final_target`, and `owner_decision_required`?
- Is Direction status `human_approved` or `frozen` before execution/paper-binding claims proceed?
- Is `big_rq` a concrete answerable research question rather than a build/roadmap statement?
- Are `falsification_condition`, `core_hypothesis`, `hypothesis_falsification`, `mvr_question`, `mvr_success_condition`, and `mvr_failure_condition` concrete and non-placeholder?
- Does Evidence Contract explicitly classify `toy`, `mock`, `smoke`, and `agent_report_only` as unable to support research claims?
- Does Spine Binding reference `RESEARCH_SPINE.yaml`, `CURRENT`, epoch PRD, RQ-local Spec, and closeout writeback?
- Are Research Corridor, Out-of-Scope Directions, Autonomy Boundary, and Global Stop Conditions non-empty and non-placeholder?
- Has any agent modified `RESEARCH_DIRECTION.md` without explicit user instruction?
- Does `CURRENT` match `Vn/STATUS.yaml.version`?

- Is there exactly one active task?
- Does every task in `Vn/TASK_QUEUE.yaml` declare `research_binding` with mode `direction_bootstrap`, `spine_bound`, `maintenance`, or `paper_binding`?
- Do all `spine_bound` task bindings resolve to valid `RESEARCH_SPINE.yaml` RQ, claim, experiment, and evidence ids?
- Are experiment, analysis, and result-binding active tasks blocked unless they bind concrete `experiment_ids` and `evidence_ids`?
- Are `direction_bootstrap`, `maintenance`, and `paper_binding` task bindings restricted to their allowed phases and justification rules?
- Was `Vn+1` created before current `Vn/closeout.md` and closed status?
- PRD updated but paper not updated?
- PRD updated but spec not updated?
- PRD updated but `RESEARCH_SPINE.yaml` is stale (source_prd_hash mismatch)?
- Spec updated but existing plan is stale?
- Paper has an experiment not in spec?
- Plan has a task or harness not in spec?
- Spec has an experiment not in PRD?
- Does `RESEARCH_SPINE.yaml` set `direction_ref` to a valid `RESEARCH_DIRECTION.md`?
- Does `RESEARCH_SPINE.yaml` have broken RQ→Claim→Experiment→Evidence→Figure/Table→Paper Section links?
- Does every RQ in `RESEARCH_SPINE.yaml` fall within the scope declared in `RESEARCH_DIRECTION.md`?
- Does every claim in `RESEARCH_SPINE.yaml` trace to at least one experiment and one evidence artifact?
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
- Does the current workspace use the standard RQ-driven layout: `Vn/PRD.tex`, `Vn/RESEARCH_SPINE.yaml`, `Vn/TASK_QUEUE.yaml`, and one `Vn/rqs/RQxx/` contract set per declared RQ?
- Does `Vn/baselines/INDEX.yaml` exist, and does it index curated baseline dossiers rather than raw search candidates?
- Does the current `Vn/BASELINE_LOCK.yaml` freeze the version-level baseline, dataset, metric, and borrowed experiment-design coordinate system before reproduction or innovation begins?
- Do all locked `selected_baselines[]`, `selected_datasets[]`, and `borrowed_experiment_designs[]` point to existing `baselines/Bxxx/` card files?
- If the workspace is not standard RQ-driven, does audit clearly tell the user to migrate and provide a migration plan without rewriting claims?

## Outputs

`docs/research/audits/YYYY-MM-DD-audit/`:

- `audit_report.md`
- `alignment_matrix.yaml`
- `drift_findings.yaml`
- `repair_plan.md`

`alignment_matrix.yaml` must include `direction_completeness`; direction blockers should also appear in `audit_report.md`, `drift_findings.yaml`, and the must-fix section of `repair_plan.md`.

Current epoch audits also write machine-readable results to `docs/research/{CURRENT}/audits/YYYY-MM-DD-audit/audit_results.yaml`.

`repair_plan.md` splits repairs into:
- **must-fix-before-execution** (execution failures)
- **insight-opportunity** (research failures / anomalies / diagnostic experiments)
- **can-fix-later**
- **recommended-next-target** (neutral type label: `execution_repair`, `spec_regeneration`, `insight_interpretation`, `plan_update`)

Audit marks and classifies; it does not route. The `research` controller reads `repair_plan.md` and decides which skill handles each repair type.

## Prerequisites

- `research-init` must be installed and its shared scripts (`research-init/_shared/scripts/`) must be on the Python path. The audit script imports `research_workspace` from that location.
- If `research-init` is missing, run `skill-sync` or install the research skill family as a unit.

## Command

```bash
python3 ~/.claude/skills/research-audit/scripts/generate_research_audit.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09

python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode audit-ready
```

`repair_plan.md` must separate must-fix-before-execution, can-fix-later, and the recommended next internal Plan compiler target.

## Epoch Audit Rules

- Audit current `Vn` first; legacy folders are context unless `CURRENT` is absent.
- Audit must run or reflect `goal-ready`; stale `GOAL_LOCK.yaml` is a pre-execution format blocker because `goal.md` may no longer match PRD, baseline, spine, spec, task queue, or status.
- Old versions may contribute hypothesis seeds and history, not current claim evidence.
- Wiki and closeout completeness are gates for `closeout-ready`.
- Paper claims must not exceed `PAPER_BINDING_DECISION.md`.

## Migration Audit Rules

Audit may detect, classify, generate `MIGRATION_AUDIT.md`, generate `MIGRATION_PLAN.md`, and point out blockers. It must not default to moving old artifacts, rewriting PRD research claims, treating old insight as paper evidence, or marking a legacy project epoch-ready.

Audit must explicitly report RQ-driven status. Missing active epoch files or missing `Vn/rqs/RQxx/` contracts are `migration_required`. A valid active epoch with remaining legacy flat files is `migration_recommended` until those files are migrated, archived, or explicitly marked compatibility-only.

Legacy migration should become an explicit task such as `TASK_MIGRATE_LEGACY_TO_V0`.

Legacy `docs/research/insights/` is compatibility storage. Audit should prefer current `Vn/wiki/*` for epoch_v1 and flag unpromoted legacy insight as migration material, not current evidence.

Baseline migration must preserve three layers: `search/` for raw discovery, `baselines/` for curated baseline knowledge, and `BASELINE_LOCK.yaml` for final version-level decisions. Audit must flag any locked baseline decision that lacks a dossier card reference.
