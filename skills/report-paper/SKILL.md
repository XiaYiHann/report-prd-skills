---
name: report-paper
description: "Use when the user asks to generate, draft, revise, or audit a top-tier computer-science conference paper from an existing docs/report workspace, including NeurIPS, ICLR, AAAI, ICML, ACL, or similar paper outputs."
---

# Report Paper

## Overview

Use this skill to derive a top-tier computer-science conference paper from the current report workspace.

`report-paper` is the only paper-specific report skill. Do not split it into `report-paper-plan`, `report-paper-draft`, `report-ingest-results`, venue-specific skills, or user-facing parser commands.

Do not create a user-facing parser, CLI flag surface, or script that the user must remember. The agent must infer the paper task from natural language and the report state.

## Source Of Truth

- Human design truth: `docs/report/<slug>/report.tex`, section files, and rendered `docs/report/report.md`.
- Machine execution truth: `report.manifest.yaml`, `tasks/task_graph.yaml`, `harness/harness.yaml`, `evidence/evidence_manifest.yaml`, and for research reports, `experiments/experiment_manifest.yaml`.
- Paper output: `docs/report/<slug>/paper/`.

The paper is not an independent truth source. It is an academic expression of the report, manifests, and evidence ledger.

## Workflow

1. Resolve the active report workspace. If multiple workspaces exist and the target is ambiguous, ask.
2. Read `brief.yaml`, `outline.md`, `report.manifest.yaml`, relevant `sections/*.tex`, `sources.md`, and rendered `docs/report/report.md`.
3. Inspect `evidence/evidence_manifest.yaml` and `experiments/experiment_manifest.yaml` when present.
4. Decide the paper state automatically:
   - planned-only evidence -> write a preregistration-style paper: Introduction, Related Work, Method, Experimental Protocol, Expected Evidence Plan, Reproducibility, Limitations.
   - observed validated evidence -> write a full paper draft with Results, Tables/Figures, Ablations, Failure Cases, and Limitations.
   - prose claims stronger than evidence -> stop and repair the report/evidence boundary before drafting.
5. Create or update `docs/report/<slug>/paper/` as a derived artifact workspace.
6. Keep claims conservative and traceable: every result sentence must map to evidence, artifact, command, seed/config, commit, and harness where applicable.

## Academic Integrity Rules

- Do not invent results, baselines, ablations, datasets, citations, or venue claims.
- Do not write observed-result language from planned experiments.
- Do not use mock, toy, synthetic, stub, proxy, or cached outputs as final result evidence.
- Do not claim state-of-the-art unless the report defines the exact benchmark scope and evidence supports it.
- If evidence is missing, write the missing-evidence boundary explicitly or generate only the preregistration-style paper.

## Output Expectations

The output should be a real paper workspace under `docs/report/<slug>/paper/`, not a chat-only outline, unless the user explicitly asks for discussion only.

Default paper style:

- Chinese interaction with the user; paper prose may be English when targeting international CS venues.
- NeurIPS / ICLR / AAAI level rigor by default, unless the user names a venue.
- Clear contribution boundaries, fair baselines, falsifiable claims, reproducibility details, limitations, and failure cases.

After editing, report what was created or updated and which evidence state was used: planned-only, observed-supported, or blocked-by-evidence-gap.
