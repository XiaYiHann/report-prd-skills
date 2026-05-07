# Report Structures

The report family now produces only two first-class PRD structures:

- `research-prd`: for research programs, grant-style plans, paper-oriented method reports, experiment plans, and hypothesis-driven scientific projects.
- `engineering-prd`: for product, platform, system, implementation, AI-agent/vibe-coding, and executor-oriented engineering projects.

Legacy structures (`research`, `project`, `hybrid`, `teaching`, `executor-handbook`) are intentionally not supported by `init_report.py`. If an existing report uses one of those types, migrate it to `research-prd` or `engineering-prd` before further initialization or major update work.

Across both structures, keep one chapter named `项目进度`. It is the default place for repo-observed facts, milestones, blockers, run status, and current implementation state. Do not spread repo status across every section unless the user explicitly asks for a current-state audit.

Across both structures, `sections/*.tex` remains the single source of truth. `render_report.py` emits two sibling artifacts, `docs/report/report.pdf` and `docs/report/report.md`; the Markdown file is a derived reading artifact and must not become a parallel source tree.

## Research PRD

Use `research-prd` when the central question is:

> What is the research problem, why is the method plausible, and what evidence would make the claim acceptable?

Recommended flow:

1. Title page and executive summary: What / Why / How / Expected Impact / Key Metrics.
2. Background, literature review, and Gap Analysis.
3. Research objectives, Research Questions, falsifiable hypotheses, and Success Metrics.
4. Scope, boundaries, assumptions, and constraints.
5. Methodology and technical route: design, data sources, tools, statistical methods, Pilot / Feasibility.
6. Mathematical formulation, algorithm, derivation, or theoretical grounding.
7. Experimental design: setup, baselines, metrics, ablations, reproducibility.
8. Results, Evidence Ledger, interpretation, and failure cases.
9. Project progress: current repo-observed facts only.
10. Resources, team, timeline, risks, ethics, and Go / No-Go gates.
11. Expected outputs, impact plan, monitoring, conclusion, and appendices.

Required structures:

- `Research Questions` and falsifiable hypotheses with failure conditions.
- `Evidence Ledger`: `claim -> evidence -> source -> limitation -> confidence`.
- `Baseline Matrix`: method, metric, dataset split, hyperparameter fairness, result, conclusion.
- `Ablation Matrix`: component changed, single variable changed, expected effect, observed effect, interpretation.
- `Reproducibility Table`: random seed, data split, config, hardware, command, artifact path.
- `Failure-case Table`: failure condition, observed behavior, likely cause, impact on claim, next verification.
- `Go / No-Go Gate`: continue, stop, or downgrade conditions.
- Risk / ethics matrix for any research that can affect users, safety, privacy, cost, or public claims.

## Engineering PRD

Use `engineering-prd` when the central question is:

> What should be built, how should an AI agent or engineer implement it, and how will we know it is accepted?

Recommended flow:

1. Executive summary, Vibe Pitch, core value, and Success Metrics.
2. Problem, opportunity, user pain points, user stories.
3. Goals & Non-Goals.
4. Personas and key journeys.
5. Technical stack, system architecture, and Agent Rules.
6. Functional requirements and modular design.
7. Non-functional requirements: performance, security, scalability, reliability, coding standards.
8. Data models, interface contracts, state, and error semantics.
9. Testing, acceptance, release gates, and rollback conditions.
10. Project progress: current repo-observed facts only.
11. Roadmap, risks, operational readiness, and appendices.

Required structures:

- `Goals & Non-Goals`: explicit scope boundary.
- Modular functional requirements: one module per component/page/service/domain unit.
- Each module includes: one-sentence essence, architecture figure, component table, feature list, Acceptance Criteria, interface contract, sequence diagram, design decisions.
- `Acceptance Criteria`: testable checklist for each P0/P1 function.
- Priority and dependencies: P0/P1/P2 and dependency notes.
- NFR matrix: performance, security, scalability, reliability, observability, coding standards.
- Interface/data contract: input, output, error semantics, state transitions.
- Test and acceptance matrix: unit, integration, E2E, manual acceptance where needed.
- Operational Readiness Matrix: source-of-truth, owner, interface boundary, runbook / rollback, compatibility bridge retirement.
- Phased MVP roadmap with short iterations.

## Selection Rules

- Choose `research-prd` for hypotheses, literature gap, method novelty, experiments, ablations, theoretical framing, or grant/paper planning.
- Choose `engineering-prd` for product requirements, system design, implementation planning, APIs, modules, user journeys, acceptance criteria, release gates, or agent-executable work.
- If a project has both research and implementation content, choose the type that owns the next decision:
  - If the key risk is whether the claim is scientifically valid, choose `research-prd`.
  - If the key risk is whether the system can be built and accepted, choose `engineering-prd`.
- Do not choose a legacy type. Convert the intent into one of the two PRD structures.

## Section Quality Checklist

Every section should answer:

1. Why does this section exist?
2. What should the reader understand after finishing it?
3. What decision or implementation step does the next section build on?
4. Does the section start with a clear conclusion sentence?
5. Are the supporting points MECE?
6. Does the section include an appropriate diagram or table?
7. Does every figure answer one main question?
8. Does every figure have a pre-figure introduction and post-figure takeaway?
9. Are `source claim`, `design intent`, `repo-observed fact`, and `report synthesis` kept distinct?

Additional `research-prd` checks:

10. Are RQs and hypotheses falsifiable?
11. Does every central claim appear in the evidence ledger?
12. Are baselines representative and comparable?
13. Does each ablation isolate one factor?
14. Are failure cases and negative results visible?

Additional `engineering-prd` checks:

15. Does each module have Acceptance Criteria?
16. Are Goals and Non-Goals explicit?
17. Are interfaces and data contracts implementable?
18. Can an engineer or AI agent run the test/acceptance path without inventing policy?
