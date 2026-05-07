---
name: report-update
description: "Update an existing PRD-based single-source report under docs/report after the user has settled the intended content, then re-render report.pdf and report.md and run global PRD consistency/self-check gates."
---

# Report Update

## Overview

Use this skill for confirmed PRD write-back. The report workspace already exists and remains the single source of truth.

If the writing direction is unclear, switch to `report-brainstorming`. If the claim is disputed, switch to `report-debate`.

## Active Report Resolution

- If the user names a workspace or section, use it.
- If the user references `report.pdf` or `report.md`, update the owning source workspace.
- If there is one obvious report under `docs/report/`, use it.
- If multiple candidates exist and the target is unclear, ask.

## Supported PRD Types

Only two report types are valid:

- `research-prd`
- `engineering-prd`

Legacy reports should be migrated before major write-back.

## Core Update Rules

- Update source files first, then re-render `docs/report/report.pdf` and `docs/report/report.md`.
- Keep LaTeX source as truth: `main.tex`, `sections/*.tex`, figures, sources, and metadata.
- Keep Markdown as a generated artifact; do not hand-edit `docs/report/report.md`.
- Keep repo-observed facts in `项目进度`.
- Maintain the four evidence layers: `source claim`, `design intent`, `repo-observed fact`, `report synthesis`.
- Use formal Chinese: rigorous, readable, information-dense.
- Run a global consistency sweep after any non-trivial update.
- Compile warnings must be fixed.

## Edit Preview Mode

正文 `.tex` 改动默认走 preview diff:

- additions: `\reportadd{...}`
- deletions: `\reportdel{...}`
- replacements: `\reportchg{old}{new}`

Do not clear preview macros until the user explicitly accepts. Non-`.tex` metadata, `项目进度`, and figure sources may be edited directly.

## Research PRD Write-back Gates

When updating `research-prd`, keep these structures current:

- Research Questions and falsifiable hypotheses.
- Scope, assumptions, constraints.
- Methodology, formulation, algorithm, and technical route.
- Baseline Matrix, Ablation Matrix, Reproducibility Table.
- Evidence Ledger with `planned` vs `observed` evidence status where relevant.
- Failure-case Table and negative results.
- Risk / ethics matrix and Go / No-Go gates.
- Project progress with real artifacts, commands, seeds, configs, and result paths.

If a claim becomes stronger, update the Evidence Ledger before strengthening prose.

## Engineering PRD Write-back Gates

When updating `engineering-prd`, keep these structures current:

- Goals & Non-Goals.
- Modular functional requirements.
- Acceptance Criteria per feature/module.
- Priorities and dependencies.
- NFR matrix.
- Data models, interface contracts, state, and error semantics.
- Testing, acceptance, release, and rollback plan.
- Operational Readiness Matrix.
- Roadmap and project progress.

If a requirement changes, update its Acceptance Criteria and test/acceptance matrix in the same pass.

## Diagram Rules

- Use one figure for one question.
- Split structure diagrams from sequence diagrams.
- Put dataflow/interface diagrams near contracts.
- Put state and gate diagrams near lifecycle or release logic.
- Add a short pre-figure sentence and post-figure takeaway for non-trivial figures.

## Workflow

1. Resolve active report and PRD type.
2. Confirm the write-back direction is settled.
3. Update `brief.yaml` only when objective, type, or constraints changed.
4. Update `sections/*.tex` using Edit Preview Mode.
5. Update `项目进度` if current state, artifact paths, blockers, or next gates changed.
6. Sweep summary, terms, captions, table headers, evidence layers, and progress references.
7. Render PDF, Markdown, and checks:

```bash
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

8. Review `docs/report/report.pdf`, `docs/report/report.md`, `build/compile-review.md`, and `build/self-check.md`.
9. Present diff summary and wait for acceptance before clearing preview macros.

## Accepting Preview Edits

After explicit user acceptance:

```bash
python3 ~/.agents/skills/report/_shared/scripts/accept_edits.py /absolute/path/to/report-dir --dry-run
python3 ~/.agents/skills/report/_shared/scripts/accept_edits.py /absolute/path/to/report-dir
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

## When To Escalate

Recommend `report-debate` when:

- a research claim is contentious.
- a baseline or ablation choice may be unfair.
- an engineering requirement has multiple incompatible implementations.
- a design choice needs explicit pro/con reasoning.
