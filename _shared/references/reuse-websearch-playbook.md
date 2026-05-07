# Reuse Websearch Playbook

Use this playbook when `report-audit` must determine whether a PRD is reinventing an existing method, library, dataset, benchmark, protocol, workflow, service, or reference implementation.

The goal is a reuse audit, not a broad literature review. The audit should answer one question: can the report build on an existing foundation, and if not, has it justified the new work clearly?

## Step 1: Extract The Reuse Target

From the report source, identify:

- proposed new artifact: method, subsystem, dataset, benchmark, service, pipeline, library, UI pattern, or operations process.
- required interface: API, file format, model contract, metric, dataset shape, deployment surface, or user workflow.
- hard constraints: license, privacy, latency, cost, governance, reproducibility, security, hardware, language, framework, or publication target.
- claimed reason for custom work.

Do not search before the target is specific enough to compare.

## Step 2: Check Repo-Local Foundations

Inspect local reusable foundations before external search:

- existing modules, packages, scripts, tests, fixtures, templates, and shared assets.
- dependency manifests and lockfiles.
- previous report artifacts, evidence ledgers, run outputs, and evaluation harnesses.
- internal APIs, schemas, CLIs, queues, pipelines, or configuration conventions.

Record local candidates even when they are incomplete. A partial local foundation may be better than a new parallel implementation.

## Step 3: Search Existing External Foundations

Use current websearch. Prefer primary or high-signal sources:

- official documentation and standards pages.
- package registries and release notes.
- maintained GitHub repositories with license, releases, issues, and examples.
- papers, benchmark leaderboards, dataset cards, and artifact pages.
- vendor documentation for managed services when the report is engineering-prd.

For `research-prd`, search at least:

- `<task> benchmark dataset baseline`
- `<method family> open source implementation`
- `<metric> evaluation protocol`
- `<problem> survey recent`

For `engineering-prd`, search at least:

- `<problem> library framework`
- `<protocol or interface> standard documentation`
- `<component> managed service`
- `<language or stack> reference implementation`

If a search family is irrelevant, state why.

## Step 4: Score Reuse Candidates

Create a reuse matrix with these columns:

| Need | Repo-local basis | External candidate | Source | Category | License / terms | Maturity | Fit | Integration cost | Evidence quality | Gaps | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use concise labels:

- `Fit`: high / medium / low.
- `Integration cost`: low / medium / high.
- `Evidence quality`: official / peer-reviewed / maintained OSS / anecdotal / unknown.
- `Recommendation`: reuse / adapt / cite as baseline / reject / needs debate.

## Step 5: Turn Search Into Audit Findings

Flag a finding when:

- the report proposes custom work while a high-fit repo-local or external reusable foundation exists.
- novelty is claimed without comparing to obvious prior art.
- baseline, benchmark, dataset, protocol, or package choices are missing.
- a dependency is proposed without license, maturity, security, or integration-risk discussion.
- the report rejects reuse without a falsifiable reason.

Do not force reuse. A custom path is acceptable when constraints, evidence, and tradeoffs are explicit.

## Step 6: Record Audit Evidence

Every reuse audit should include:

- search date.
- repo-local paths or artifacts checked.
- 3 to 6 cited sources, unless the space is genuinely sparse.
- the reuse matrix.
- build-vs-reuse conclusion.
- residual risks and any search limitation.

If websearch is unavailable, record `reuse gate: not verified by websearch` and treat that as residual risk.
