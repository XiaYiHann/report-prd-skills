---
name: report-spec
description: "Use when the user wants to compile a report main artifact into machine-readable execution specs, task graphs, experiment manifests, harnesses, evidence contracts, anti-mock policies, or Codex goal inputs."
---

# Report Spec

## Overview

Use this skill to compile `main` into the machine-readable `spec` product. It is not a paper-writing skill and it must not invent research content.

`report-spec` is the execution compiler in the three-product model:

- `main/`: human design truth.
- `paper/`: academic expression truth.
- `spec/`: machine execution truth.

Codex and Claude execution must use `spec/`, not `paper/`, as the executable source.

## Source Of Truth

Read `docs/report/<slug>/main/` first. If the workspace has only the older LaTeX report layout, read `report.tex`, `sections/*.tex`, and rendered `docs/report/report.md` as the source for `main`.

Read `paper/` only to register placeholders and expression gaps. Do not infer experiments, datasets, baselines, metrics, seeds, models, tasks, or results from `paper`.

If required execution details are absent from `main`, write the gap to `spec/spec_gap_report.md` and mark the related spec entry as blocked. Do not fill missing details with fake defaults.

## Required Outputs

Create or update `docs/report/<slug>/spec/` with:

- `execution_spec.yaml`
- `experiment_manifest.yaml`
- `task_graph.yaml`
- `harness.yaml`
- `dataset_manifest.yaml`
- `model_manifest.yaml`
- `baseline_manifest.yaml`
- `metric_manifest.yaml`
- `seed_protocol.yaml`
- `evidence_contract.yaml`
- `anti_mock_policy.yaml`
- `codex_goal.md`
- `spec_gap_report.md`

The helper script can scaffold these files:

```bash
python3 skills/report-spec/scripts/generate_report_spec.py --workspace docs/report/<slug>
```

Validate readiness with:

```bash
python3 skills/report-spec/scripts/validate_report_spec.py --spec docs/report/<slug>/spec
```

## Compilation Chain

The spec must establish this chain when the information exists in `main`:

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

Every experiment must answer which RQ and claim it tests, which dataset/split/baseline/metric/seed protocol it uses, which command runs it, which artifact it emits, which harness judges it, and which condition supports or falsifies the claim.

## Execution-Readiness Rules

- Every milestone must have an explicit gate.
- Every gate must have task entries.
- Every task must have harnesses and acceptance criteria.
- Every harness must have a real command or explicit blocker.
- Every claim evidence contract must forbid mock, toy, smoke-only, synthetic, stub, proxy, or cached results as final claim evidence.
- Full experiment harnesses should require independent rerun when the report claims research evidence.
- `paper` placeholders must map to experiments or evidence contract entries.

## Anti-Mock Policy

Mock, toy, synthetic, stub, proxy, cached, and smoke-only outputs may be used for unit or smoke validation only when explicitly labeled. They must not support research claims, benchmark comparisons, ablations, final task completion, paper tables/figures, or Go / No-Go decisions.

## Workflow

1. Resolve the active `docs/report/<slug>/` workspace. Ask only if multiple workspaces are plausible.
2. Read `main/` or the legacy report source.
3. Read `paper/` only for placeholders and gap alignment.
4. Generate or update `spec/` without inventing missing scientific or engineering decisions.
5. Run `validate_report_spec.py`.
6. If validation is not execution-ready, leave precise blockers in `spec/spec_gap_report.md`.
7. Hand off to `report-goal` only when `spec/` is execution-ready.

## Common Mistakes

- Do not treat `paper` as an experiment source.
- Do not create placeholder tasks that look executable.
- Do not use fake commands such as `python train.py` unless the report or repo actually defines them.
- Do not mark scaffolded specs as execution-ready.
- Do not hide missing datasets, baselines, metrics, seeds, credentials, hardware, or model weights.
