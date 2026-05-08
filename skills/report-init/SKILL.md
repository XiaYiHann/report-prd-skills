---
name: report-init
description: "Initialize a new PRD-based single-source LaTeX report workspace under docs/report, render report.pdf and report.md, and run compile/self-check gates. Supports only research-prd and engineering-prd outputs."
---

# Report Init

## Overview

Use this skill to create a new PRD workspace from scratch.

`report-init` creates a stable, reusable, semi-empty PRD skeleton. It does not write a long first draft. The user and later workflows fill real content through `report-brainstorming` and `report-update`.

The source workspace lives under `docs/report/<slug>/`. The rendered artifacts live at `docs/report/report.pdf` and `docs/report/report.md`.

Initialization also creates empty execution manifest scaffolds. They are machine-readable placeholders, not implementation authority until `report-update --mode deep-spec` fills real task, harness, experiment, and evidence contracts.

## Supported Types

Only two report types are valid:

- `research-prd`: research program PRD for hypotheses, methods, experiments, evidence, risks, ethics, and Go / No-Go gates.
- `engineering-prd`: engineering/product/system PRD for goals, non-goals, modular requirements, Acceptance Criteria, interfaces, NFRs, testing, release, roadmap, and operational readiness.

Do not initialize legacy types (`research`, `project`, `hybrid`, `teaching`, `executor-handbook`). If a user asks for one, map the intent to `research-prd` or `engineering-prd`.

## Core Contract

- Generate a fixed semi-empty PRD skeleton, not a long first draft.
- Every chapter starts with a conclusion sentence placeholder.
- Every major chapter contains at least one table or figure.
- The template follows 金字塔结构 + 图解优先 + PRD gate first.
- Keep `source claim`, `design intent`, `repo-observed fact`, and `report synthesis` distinct.
- Keep current repo status in `项目进度`.
- Compile warnings are not acceptable.
- Markdown output is generated from the same LaTeX source; do not create a parallel Markdown source tree.
- Create `report.manifest.yaml`, `tasks/task_graph.yaml`, `harness/harness.yaml`, and `evidence/evidence_manifest.yaml` for every PRD.
- Create `experiments/experiment_manifest.yaml` for `research-prd`.
- Do not insert fake tasks, fake experiments, fake metrics, or fake observed evidence into scaffold manifests.
- If a meaningful choice affects the PRD type, audience, or scope, ask before initialization.

## Research PRD Requirements

The initialized workspace must include placeholders for:

- What / Why / How / Expected Impact / Key Metrics.
- Literature review and Gap Analysis.
- Research Questions and falsifiable hypotheses.
- In-Scope / Out-of-Scope / assumptions / constraints.
- Methodology, data sources, tools, Pilot / Feasibility.
- Formulation / algorithm / derivation.
- Baseline Matrix, Ablation Matrix, Reproducibility Table.
- Evidence Ledger: `claim -> evidence -> source -> limitation -> confidence`.
- Failure-case Table.
- Project progress.
- Resources, timeline, risk / ethics, Go / No-Go gates, impact plan.

## Engineering PRD Requirements

The initialized workspace must include placeholders for:

- Vibe Pitch, core value, Success Metrics.
- User pain points, user stories, opportunity window.
- Goals & Non-Goals.
- Personas and key journeys.
- Tech stack, architecture, and Agent Rules.
- Modular functional requirements.
- Acceptance Criteria per feature/module.
- Non-functional requirements.
- Data models, interface contracts, state and error semantics.
- Testing, acceptance, release gates, rollback.
- Project progress.
- Phased MVP roadmap and Operational Readiness Matrix.

When `--type engineering-prd` is used, default to `--module-source auto --diagram-depth draft`. The initializer scans repo module candidates and emits module overview, module architecture figures, I/O contract tables, sequence figures, and design decision placeholders. Scan output remains a drafting aid until confirmed by `report-update`.

## Workflow

1. Resolve the report type.
   - Use `research-prd` when the key risk is scientific validity.
   - Use `engineering-prd` when the key risk is implementation and acceptance.
2. Confirm primary audience only if it materially changes depth.
3. Initialize the workspace.

Research PRD:

```bash
python3 ~/.agents/skills/report/_shared/scripts/init_report.py \
  --project-root /absolute/path/to/project \
  --title "研究 PRD 标题" \
  --type research-prd \
  --audience mixed
```

Engineering PRD:

```bash
python3 ~/.agents/skills/report/_shared/scripts/init_report.py \
  --project-root /absolute/path/to/project \
  --title "工程 PRD 标题" \
  --type engineering-prd \
  --audience rookie \
  --module-source auto \
  --diagram-depth draft
```

4. Review generated `brief.yaml`, `outline.md`, `sections/*.tex`, and `sources.md`.
   Also review `report.manifest.yaml`, `tasks/task_graph.yaml`, `harness/harness.yaml`, and `evidence/evidence_manifest.yaml`.
5. Render PDF, Markdown, and self-check:

```bash
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

6. Inspect `docs/report/report.pdf`, `docs/report/report.md`, `build/compile-review.md`, and `build/self-check.md`.
7. Hand off to `report-brainstorming` or `report-update`.

## Quality Bar

- `build/compile-review.md` has no warnings.
- `build/self-check.md` has no errors.
- `docs/report/report.pdf` and `docs/report/report.md` both exist and reflect the same LaTeX source.
- `项目进度` exists.
- The PRD type-specific gates are present.
- The skeleton remains semi-empty and reusable.
- Execution manifests exist and remain scaffold-only until deep-spec write-back.
- No repo-observed facts are written outside `项目进度` unless explicitly needed and clearly marked.
