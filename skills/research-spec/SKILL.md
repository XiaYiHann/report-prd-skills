---
name: research-spec
description: "Use when docs/research/spec needs execution contracts, manifests, task graphs, harnesses, evidence contracts, or anti-mock readiness."
---

# Research Spec

## Overview

Compile the PRD into `docs/research/spec/`, the global and relatively stable execution contract. The spec is the only source for executable experiments, tasks, gates, harnesses, artifacts, and evidence contracts.

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
