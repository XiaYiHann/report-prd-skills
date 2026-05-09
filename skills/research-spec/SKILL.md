---
name: research-spec
description: "Use when docs/research/spec needs execution contracts, manifests, task graphs, harnesses, evidence contracts, or anti-mock readiness."
---

# Research Spec

## Overview

Compile the PRD into `docs/research/spec/`, the global and relatively stable execution contract. The spec is the only source for executable experiments, tasks, gates, harnesses, artifacts, and evidence contracts.

Use English YAML keys and stable IDs for parser compatibility, but write explanatory values in Chinese: `title`, `description`, `purpose`, `notes`, `blockers`, `acceptance_criteria`, `repair`, gap reports, and policy explanations.

The scaffold includes explicit contract templates, not empty placeholder files. `global_spec.yaml` defines the RQ -> evidence -> paper placeholder chain template; reproduction, experiment, harness, and paper binding files contain `*_template` entries that show the required fields while keeping executable arrays empty until the PRD has been compiled.

Template entries are instructional only. Do not treat `experiment_template`, `harness_template`, `reproduction_target_template`, or `result_binding_template` as declared executable work.

## Authority Chain

Build the chain:

```text
RQ
-> Hypothesis
-> Claim
-> Experiment
-> Dataset / Model / Baseline / Metric / Seed
-> Task
-> Harness
-> Evidence
-> Paper placeholder
```

Do not infer experiments from the paper. Paper placeholders can be checked against the spec, but they cannot create executable work.

When the PRD lacks required details, record the missing contract in a Chinese gap report or blocker. Do not invent datasets, baselines, metrics, seeds, commands, artifact paths, reproduction modes, or empirical results.

## Required Layout

`research-spec` owns:

- `global_spec.yaml`
- `shared/dataset_manifest.yaml`
- `shared/metric_manifest.yaml`
- `shared/model_manifest.yaml`
- `shared/environment_spec.yaml`
- `shared/seed_protocol.yaml`
- `shared/artifact_schema.yaml`
- `shared/anti_mock_policy.yaml`
- `shared/evidence_contract.yaml`
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

## Reproduction Track

Reproduction is a track inside Spec and Plan, not a top-level skill. Every reproduction target must declare one mode:

- `official_code_reuse`
- `official_code_adaptation`
- `paper_based_reimplementation`

Paper-based reimplementation must record algorithm sources, missing details, adopted defaults, faithfulness risk, and that it must be reported as non-official reimplementation.

## Commands

```bash
python3 ~/.agents/skills/research-spec/scripts/generate_research_spec.py \
  --repo /absolute/path/to/repo

python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode spec-ready
```

Readiness must fail on missing datasets, splits, baselines, metrics, seeds, commands, artifacts, harnesses, reproduction modes, or anti-mock evidence rules.

## Language Contract

- File names, YAML keys, IDs, and schema fields remain English.
- Human-facing values and Markdown reports are Chinese.
- `spec/README.md` must explain that Spec is compiled from PRD and that Paper cannot define experiments.
- `reproduction_gap_report.md` and related gap files must be Chinese and must use explicit blocker wording.
- Mock/toy/synthetic/stub/cached/proxy output may only support unit or smoke tests, never research claims, benchmarks, ablations, paper tables/figures, or Go / No-Go decisions.
