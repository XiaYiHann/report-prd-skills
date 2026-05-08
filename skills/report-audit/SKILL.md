---
name: report-audit
description: "Reviews existing PRD-based reports with a persona-driven or multi-agent lens. Use when auditing report quality, evidence gates, PRD completeness, reusable foundations, disputed claims, execution readiness, or repair order."
---

# Report Audit

## Overview

Use this skill to review an existing PRD report rather than rewrite it. Output ranked findings and a repair order. Do not silently edit the report.

When the report proposes a new method, system, module, dataset, benchmark, workflow, or infrastructure component, audit whether existing reusable foundations already solve enough of the problem to avoid unnecessary reinvention.

`report-audit` also owns disputed-claim and multi-perspective review. There is no separate debate skill; contested claims, baseline fairness disputes, build-vs-reuse disagreements, and one-sided sections should be handled here as multi-agent audit findings.

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
- execution-readiness: manifest scaffold, task graph, harness commands, evidence links, and anti-mock evidence policy.
- disputed-claim pressure: whether the section has only one-sided support, hidden assumptions, unfair comparison, or conclusion strength beyond evidence.

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
- every research claim maps to `claim_id`; every `claim_id` maps to experiment or proof artifact; every experiment declares dataset/split, baseline, metric, seed, command, artifact, falsification condition, and evidence policy.

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
- every milestone maps to task graph entries; every task has acceptance criteria and harness; every harness has exact command or explicit blocker; every final gate depends on executable evidence rather than prose.

## Execution-Readiness Mode

Use execution-readiness mode when the user asks whether the report can drive Claude/Codex execution, experiments, harnesses, evidence ledgers, or anti-mock completion.

Blocking findings:

- missing `report.manifest.yaml`, `tasks/task_graph.yaml`, `harness/harness.yaml`, or `evidence/evidence_manifest.yaml`.
- missing `experiments/experiment_manifest.yaml` for `research-prd`.
- task without harness.
- task references unknown harness.
- harness without command or explicit blocker.
- milestone exists in prose but not in task graph.
- final gate has no artifact path, schema/check, log, or independent validation rule.
- research claim has no linked experiment or proof artifact.
- observed result has no command, config, seed, commit, artifact, log, and validation harness.
- final/research evidence uses mock, toy, synthetic, stub, proxy, or cached output.

Treat these as execution blockers even if the PDF is readable and compiles cleanly.

## Multi-Agent Audit Mode

Use multi-agent audit mode when the report contains a disputed claim, major design choice, research novelty claim, baseline choice, build-vs-reuse decision, or unusually consequential conclusion.

If subagents are available and the user permits parallel agent work, run independent audit passes with narrow roles:

- `Research Skeptic`: attacks novelty, falsifiability, baseline fairness, ablation validity, evidence overclaim, and reproducibility.
- `Systems Engineer`: attacks module boundaries, interfaces, operational risk, harness quality, rollout, and rollback.
- `Reuse Scout`: checks repo-local and external reusable foundations before recommending new implementation.
- `Paper Reviewer`: checks whether claims, figures, tables, limitations, and contribution language would survive top-tier CS review.

If subagents are unavailable or the user did not ask for parallel agents, run the same roles sequentially in the main session and label them clearly. Keep the role outputs independent: do not let one role's conclusion erase another role's objection.

Synthesis rules:

- Findings still lead the answer, ordered by severity.
- A disputed point becomes a finding only when it has a concrete failing assumption, missing evidence, unfair comparison, invalid gate, or implementation risk.
- Record both the strongest supporting argument and the strongest objection for high-impact choices, but do not create a standalone debate artifact.
- The final repair order must say whether to keep, weaken, rewrite, postpone, or remove the disputed claim.

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
5. Run Multi-Agent Audit Mode when the report has contested claims or high-impact design choices.
6. Run render/self-check when artifact readiness matters:

```bash
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

7. Review `docs/report/report.pdf`, `docs/report/report.md`, `build/compile-review.md`, and `build/self-check.md`.
8. In execution-readiness mode, manually inspect the manifest graph in addition to script findings.
9. Perform manual PRD audit beyond script heuristics.
10. Emit findings first, ordered by severity and grounded in file/line references.

## Output Shape

Findings first. Then include:

- detected PRD type and persona.
- open questions or unresolved assumptions.
- PRD gate matrix.
- diagram coverage matrix.
- reusable-foundation matrix covering repo-local basis, external candidates, evidence source, reuse risk, and build / adapt / reuse recommendation.
- multi-agent audit matrix when used: role, strongest objection, evidence needed, severity, and recommended repair.
- execution-readiness matrix covering manifest presence, task graph, harness command, artifact/evidence path, research claim mapping, and anti-mock policy.
- pyramid structure matrix.
- information-density notes.
- recommended repair order.

If no serious findings exist, say that explicitly and still mention residual risks.

## No Separate Debate Skill

Do not route to `report-debate`; that skill is intentionally removed. If a claim is contentious, a baseline may be unfair, a build-vs-reuse decision is disputed, or a section is coherent but one-sided, handle it inside `report-audit` using Multi-Agent Audit Mode.
