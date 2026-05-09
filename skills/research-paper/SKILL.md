---
name: research-paper
description: "Use when a planned top-conference-style research paper under docs/research/paper needs creation, update, placeholder checking, or polishing."
---

# Research Paper

## Overview

Generate or update `docs/research/paper/` as the academic expression derived from the PRD. The target style is NeurIPS/ICLR/AAAI: sharp motivation, clear gap, rigorous formulation, concise contributions, strong method narrative, and structured evaluation design.

The final output of this skill must be a **complete, submission-ready conference manuscript draft**, not a fill-in template. It should read like a real NeurIPS / ICLR / AA AI paper: Abstract, Introduction, Related Work, Problem Formulation, Method, Experiments, Results, Limitations, and Conclusion. Do not leave visible `【待填写】` placeholders in the final paper.

The paper surface may be English, because it targets top-conference manuscript style. Explanatory blockers and gap reports are Chinese. The paper must remain derived from PRD and checked against Spec; it cannot create executable experiments by itself.

When empirical evidence is not ready, write a **complete mock-data manuscript**. Use reasonable mock values to populate tables, figures, and result paragraphs so the paper presents as a polished, submission-grade manuscript. These values are **temporary placeholders** for the final evidence and must be recorded in `paper_gap_report.md` with exact locations and replacement conditions. They are not validated findings and must not be presented as such in the narrative voice.

## Allowed Language

For designed artifacts already defined in the PRD, the paper may say:

- `We propose ...`
- `We formulate ...`
- `We design ...`
- `We introduce ...`
- `We develop ...`
- `We evaluate ...`
- `Experiment E1 tests whether ...`
- `Table 1 reports ...`

## Allowed vs. Forbidden Language for Unobserved Results

**Mock manuscript values (allowed in draft):**

The Results section, tables, and figures may contain mock values that match the expected data format and scale. This ensures the manuscript reads as a complete paper and gives downstream AI execution a concrete reference for what baselines, metrics, and table structures to produce. Mock values should be numerically reasonable and consistent with the experimental design declared in the PRD.

**Validated findings (forbidden without evidence):**

Do not use narrative language that presents mock values as validated empirical findings:

- `Experiments show that ...`
- `Our method outperforms ...`
- `We achieve state-of-the-art ...`
- `The results demonstrate ...`
- any phrase that implies the mock values have been empirically confirmed.

Instead, use neutral descriptive language:

- `Table 1 reports the performance of ...`
- `As shown in Fig. 2, ...`
- `The evaluation compares ...`

The distinction is in the **narrative voice**, not the numbers. A table may display `0.852` as a mock value; the text may say "Table 1 reports an F1 score of 0.852," but it must not say "Our method achieves an F1 score of 0.852, outperforming the baseline."

## Outputs

- `planned_paper.tex`
- `planned_paper.md`
- `planned_paper.pdf`
- `placeholder_map.yaml`
- `paper_gap_report.md`

`planned_paper.tex` is a real `ctexart` LaTeX source using `booktabs` and `tabularx`. If no LaTeX engine is available, generation records a render blocker instead of writing a fake PDF.

## Commands

```bash
python3 ~/.agents/skills/research-paper/scripts/generate_research_paper.py \
  --repo /absolute/path/to/repo \
  --force

python3 ~/.agents/skills/research-paper/scripts/generate_research_paper.py \
  --repo /absolute/path/to/repo \
  --demo \
  --force

python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode paper-ready
```

If the paper needs a missing claim, experiment, dataset, baseline, metric, formula, or table, record it in `paper_gap_report.md`; do not invent it.
