---
name: research-paper
description: "Use when a planned top-conference-style research paper under docs/research/paper needs creation, update, placeholder checking, or polishing."
---

# Research Paper

## Overview

Generate or update `docs/research/paper/` as the academic expression derived from the PRD. The target style is NeurIPS/ICLR/AAAI: sharp motivation, clear gap, rigorous formulation, concise contributions, strong method narrative, and structured evaluation design.

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

## Forbidden Before Evidence

Do not write:

- `Experiments show that ...`
- `Our method outperforms ...`
- `We achieve state-of-the-art ...`
- `The results demonstrate ...`
- any actual number or comparison not backed by validated evidence.

Unobserved results must be placeholders such as `{{E01.OURS.primary_metric}}` and registered in `placeholder_map.yaml`.

## Outputs

- `planned_paper.tex`
- `planned_paper.md`
- `planned_paper.pdf`
- `placeholder_map.yaml`
- `paper_gap_report.md`

## Commands

```bash
python3 ~/.agents/skills/research-paper/scripts/generate_research_paper.py \
  --repo /absolute/path/to/repo \
  --force

python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode paper-ready
```

If the paper needs a missing claim, experiment, dataset, baseline, metric, formula, or table, record it in `paper_gap_report.md`; do not invent it.
