---
name: research-init
description: "Use when a repo needs a new docs/research workspace or when an older report-style research workspace needs migration."
---

# Research Init

## Overview

Initialize `docs/research/` as the durable workspace for the research execution skill family. This is setup only: it creates a Chinese, top-level Research PRD template, a top-conference planned paper template, global spec contract templates, plans, audits, and slide-image deck directories without inventing datasets, baselines, metrics, commands, or results.

The initializer must produce a serious research template, not an empty `TODO` skeleton. `research_prd.tex` is the canonical source and uses `ctex` + TikZ tables/figures; `research_prd.md` is the Chinese companion reading artifact.

The generated paper and spec are also real templates, not empty files:

- `paper/planned_paper.md` and `.tex` include a NeurIPS / ICLR / AAAI-style planned manuscript structure, placeholder discipline, and gap report.
- `spec/**/*.yaml` includes contract templates for RQ chains, reproduction targets, experiments, harnesses, evidence, anti-mock rules, and paper result bindings.
- YAML keys, IDs, and schema fields stay English; all explanatory values, blockers, prompts, criteria, and gap reports are Chinese.

## Source Model

- Research PRD is the human research source of truth.
- Research Paper is derived academic expression.
- Research Spec is the machine-readable execution contract.
- Research Plan is a dated concrete execution run.
- Research Audit checks drift among all artifacts.
- Research PPT is a PNG/PDF slide-image workflow, not `.pptx`.

## Command

```bash
python3 ~/.agents/skills/research-init/scripts/init_research.py \
  --repo /absolute/path/to/repo \
  --title "Project Title" \
  --purpose "minimum viable research goal"
```

The command creates:

- `docs/research/prd/`
- `docs/research/paper/`
- `docs/research/spec/`
- `docs/research/plans/`
- `docs/research/ppt/`
- `docs/research/audits/`

If `latexmk` or `xelatex` is available, initialization renders a real PDF from the `.tex` source. If no LaTeX engine is available, it writes a Chinese `render_blocker.md` and does not create a fake PDF.

## Workflow

1. Resolve the repository root.
2. Run the initializer.
3. Inspect `docs/research/prd/research_prd.md` and fill the Research PRD before treating the spec as executable.
4. Run `research-spec` only after the PRD has concrete RQs, hypotheses, benchmarks, experiments, harnesses, and evidence boundaries.
5. Run validation:

```bash
python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode prd-ready
```

## Hard Rules

- Do not initialize `docs/report/` for new work.
- Do not create `research-evidence`, `research-writing`, or `research-goal`.
- Do not create `.pptx` output.
- Scaffold files may contain blockers; readiness validators must fail until contracts are concrete.
- PRD, Plan, prompts, gap reports, and explanatory YAML values must be Chinese.
- YAML keys and stable IDs stay English for parser compatibility.
- Use structured placeholders such as `【待填写：...】`; do not leave raw `TODO` placeholders.
