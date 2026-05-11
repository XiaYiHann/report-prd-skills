---
name: research-spec
description: "Use when docs/research/spec needs execution contracts, manifests, task graphs, harnesses, evidence contracts, or anti-mock readiness."
---

# Research Spec

## Overview

Compile the active epoch PRD into `docs/research/{CURRENT}/SPEC.yaml`. Legacy `docs/research/spec/` remains supported, but the default contract now lives inside the current `Vn`. The spec is the only source for executable experiments, tasks, gates, harnesses, artifacts, and evidence contracts.

Use English YAML keys and stable IDs for parser compatibility, but write explanatory values in Chinese: `title`, `description`, `purpose`, `notes`, `blockers`, `acceptance_criteria`, `repair`, gap reports, and policy explanations.

The scaffold includes explicit contract templates, not empty placeholder files. `global_spec.yaml` defines the RQ -> evidence -> paper placeholder chain template; reproduction, experiment, harness, and paper binding files contain `*_template` entries that show the required fields while keeping executable arrays empty until the PRD has been compiled.

Template entries are instructional only. Do not treat `experiment_template`, `harness_template`, `reproduction_target_template`, or `result_binding_template` as declared executable work.

## Authority Chain

Build the chain:

```text
RESEARCH_DIRECTION.md
  -> CURRENT
  -> Vn/PRD.md
  -> Vn/SPEC.yaml
  -> Vn/PLAN.md
  -> Vn/TASK_QUEUE.yaml
  -> Vn/NEXT_ACTION.md
  -> Vn/runs + Vn/artifacts
  -> Vn/audits
  -> research-insight
  -> Vn/wiki
  -> Vn/closeout.md
  -> Vn+1/PRD.md 或 paper binding
```

The authority chain now explicitly includes the **Insight Feedback Loop**. Experiments produce not only evidence but also observations that may refine the hypothesis. In epoch_v1, `research-insight` performs the interpretation step and writes durable insight to `Vn/wiki/*`; legacy `docs/research/insights/` is compatibility storage.

Do not infer experiments from the paper. Paper placeholders can be checked against the spec, but they cannot create executable work.

When the PRD lacks required details, record the missing contract in a Chinese gap report or blocker. Do not invent datasets, baselines, metrics, seeds, commands, artifact paths, reproduction modes, or empirical results.

## Required Layout

For the current epoch, `research-spec` owns `docs/research/{CURRENT}/SPEC.yaml` with:

- `version`
- `direction_ref`
- `prd_ref`
- `experiments`
- `datasets`
- `models`
- `baselines`
- `metrics`
- `seeds`
- `harnesses`
- `artifact_schemas`
- `gates`
- `anti_mock_policy`
- `runtime_backend_truth`
- `runtime_contract`
- `agent_autonomy`
- `literature_policy`
- `subagent_policy`
- `version_transition_policy`
- `engineering_gates`
- `carry_forward`

Legacy `docs/research/spec/` remains compatible and owns:

- `global_spec.yaml`
- `shared/dataset_manifest.yaml`
- `shared/metric_manifest.yaml`
- `shared/model_manifest.yaml`
- `shared/environment_spec.yaml`
- `shared/seed_protocol.yaml`
- `shared/artifact_schema.yaml`
- `shared/anti_mock_policy.yaml`
- `shared/evidence_contract.yaml`
- `shared/insight_policy.yaml`
- `insights/insight_manifest.yaml`
- `reproduction/benchmark_candidate_matrix.yaml`
- `reproduction/reproduction_manifest.yaml`
- `reproduction/reproduction_task_graph.yaml`
- `reproduction/reproduction_harness.yaml`
- `implementation/module_contracts.yaml`
- `implementation/implementation_task_graph.yaml`
- `implementation/implementation_harness.yaml`
- `experiments/experiment_manifest.yaml`
- `experiments/experiment_task_graph.yaml`
- `experiments/experiment_harness.yaml`
- `paper/placeholder_map.yaml`
- `paper/result_binding.yaml`

## Experiment Types

Every experiment in `experiment_manifest.yaml` should declare an `experiment_type`:

- `confirmatory` — validates a pre-registered hypothesis (default)
- `exploratory` — searches for unknown structure or patterns
- `diagnostic` — explains why a module or assumption fails
- `reproduction` — reproduces a baseline for comparability
- `ablation` — isolates the contribution of a component
- `stress` — tests robustness under extreme or edge conditions

Exploratory and diagnostic experiments are first-class citizens. They may trigger spec refinement or pivot proposals without invalidating the research process.

## Reproduction Track

Reproduction is a track inside Spec and Plan, not a top-level skill. Every reproduction target must declare one mode:

- `official_code_reuse`
- `official_code_adaptation`
- `paper_based_reimplementation`

Paper-based reimplementation must record algorithm sources, missing details, adopted defaults, faithfulness risk, and that it must be reported as non-official reimplementation.

## Commands

```bash
python3 ~/.claude/skills/research-spec/scripts/generate_research_spec.py \
  --repo /absolute/path/to/repo

python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode spec-ready
```

Readiness must fail on missing datasets, splits, baselines, metrics, seeds, commands, artifacts, harnesses, reproduction modes, or anti-mock evidence rules.

New validator modes:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode direction-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode epoch-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode loop-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode closeout-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode paper-binding-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode format-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode migration-ready
python3 ~/.claude/skills/research-spec/scripts/validate_research.py --repo /absolute/path/to/repo --mode git-ready
```

## Language Contract

- File names, YAML keys, IDs, and schema fields remain English.
- Human-facing values and Markdown reports are Chinese.
- `spec/README.md` must explain that Spec is compiled from PRD and that Paper cannot define experiments.
- `reproduction_gap_report.md` and related gap files must be Chinese and must use explicit blocker wording.
- Mock/toy/synthetic/stub/cached/proxy output may only support unit or smoke tests, never research claims, benchmarks, ablations, paper tables/figures, or Go / No-Go decisions.
- Agent reports are not evidence unless backed by commands, artifacts, or explicit prompt-only status.
- `prompt_only_scaffold` can document scaffold work, but cannot support paper result evidence.
- `can_modify_research_direction` must be false.
- Git Memory Layer records engineering state, but Git history does not interpret research results.
- Explore sessions can seed PRD/wiki/task proposals, but cannot become Spec truth without explicit promotion.
