---
name: report-audit
description: "Reviews existing PRD-based reports with a persona-driven lens: Kaiming He for research-prd and Linus Torvalds for engineering-prd. Use when auditing report quality, evidence gates, PRD completeness, reusable foundations, or repair order."
---

# Report Audit

## Overview

Use this skill to review an existing PRD report rather than rewrite it. Output ranked findings and a repair order. Do not silently edit the report.

When the report proposes a new method, system, module, dataset, benchmark, workflow, or infrastructure component, audit whether existing reusable foundations already solve enough of the problem to avoid unnecessary reinvention.

## Type Detection

Read `brief.yaml`, `outline.md`, and section content.

- `research-prd`: use Kaiming He perspective: rigor, falsifiability, evidence, baselines, reproducibility, honest limitations.
- `engineering-prd`: use Linus Torvalds perspective: simple interfaces, executable requirements, acceptance criteria, operational clarity, no broken promises.

Legacy types should be treated as migration findings: recommend conversion to `research-prd` or `engineering-prd`.

## Required Checks

Always check:

- structure completeness.
- conclusion-first pyramid structure.
- MECE support.
- diagram/table coverage.
- figure grammar: overview before detail, one figure one question.
- information density and banned phrasing.
- terminology consistency.
- LaTeX compile cleanliness.
- Markdown export freshness at `docs/report/report.md`.
- design intent vs repo-observed fact separation.
- `项目进度` freshness and containment.
- reuse coverage: repo-local modules, dependencies, scripts, templates, tests, prior artifacts, external libraries, standards, datasets, benchmarks, reference implementations, managed services, and package foundations.

## Research PRD Audit Gates

For `research-prd`, audit:

- problem clarity and non-trivial motivation.
- Research Questions and falsifiable hypotheses.
- assumption and constraint visibility.
- method rigor and derivation correctness.
- baseline fairness and apples-to-apples comparison.
- ablation completeness; each ablation changes one variable.
- reproducibility: seeds, splits, configs, hardware, commands, artifact paths.
- Evidence Ledger: `claim -> evidence -> source -> limitation -> confidence`.
- planned evidence vs observed evidence separation.
- prior-art and reusable-foundation fit: canonical methods, public datasets, benchmarks, reference implementations, and open-source baselines.
- failure cases and negative results.
- risk, ethics, and Go / No-Go gates.
- conclusion strength vs evidence.

## Engineering PRD Audit Gates

For `engineering-prd`, audit:

- Goals & Non-Goals.
- modular functional requirements.
- Acceptance Criteria per feature/module.
- priorities and dependencies.
- NFR matrix: performance, security, scalability, reliability, coding standards.
- interface/data contracts, state transitions, error semantics.
- test and acceptance matrix.
- release and rollback gates.
- Operational Readiness Matrix: source-of-truth, owner, interface boundary, runbook / rollback, compatibility bridge retirement.
- reusable-foundation fit: existing frameworks, libraries, protocols, managed services, package registries, deployment templates, and reference architectures.
- roadmap feasibility.
- whether an AI agent or engineer can implement without inventing decisions.

## Websearch Reuse Gate

Use the shared playbook at `../report/_shared/references/reuse-websearch-playbook.md` when any audit finding depends on whether the report should build, adapt, or reuse an existing foundation.

Run this gate before recommending new implementation work. Check repo-local foundations first, then use websearch for current external foundations when the decision depends on public tooling, papers, datasets, standards, libraries, or managed services.

Apply the gate when:

- the report claims novelty or proposes a custom method.
- the report introduces a new subsystem, protocol, data pipeline, benchmark, or evaluation harness.
- the report leaves baseline, library, framework, or dataset choices implicit.
- the report repeats work that might already exist in public papers, OSS repositories, standards, package registries, or vendor documentation.

Treat websearch as an evidence-gathering audit step, not as permission to rewrite the report. Record search date, sources, candidate fit, license or usage constraints, integration cost, and residual gaps. If websearch cannot be performed, state that as an audit limitation and do not mark the reuse gate as passed.

## Workflow

1. Resolve the active report workspace.
2. Detect PRD type and state the persona.
3. Read `brief.yaml`, `outline.md`, key `sections/*.tex`, `sources.md`, figures, and build reports.
4. Run the Websearch Reuse Gate when the report proposes work that could reuse repo-local or external foundations.
5. Run render/self-check when artifact readiness matters:

```bash
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

6. Review `docs/report/report.pdf`, `docs/report/report.md`, `build/compile-review.md`, and `build/self-check.md`.
7. Perform manual PRD audit beyond script heuristics.
8. Emit findings first, ordered by severity and grounded in file/line references.

## Output Shape

Findings first. Then include:

- detected PRD type and persona.
- open questions or unresolved assumptions.
- PRD gate matrix.
- diagram coverage matrix.
- reusable-foundation matrix covering repo-local basis, external candidates, evidence source, reuse risk, and build / adapt / reuse recommendation.
- pyramid structure matrix.
- information-density notes.
- recommended repair order.

If no serious findings exist, say that explicitly and still mention residual risks.

## Escalate To Debate

Recommend `report-debate` when:

- a claim is contentious.
- a baseline choice may be unfair.
- a build-vs-reuse decision is technically or strategically disputed.
- a section is internally coherent but one-sided.
- a design route needs structured pro/con reasoning before update.
