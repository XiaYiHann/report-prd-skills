---
name: research-paper
description: "Use when a planned top-conference-style research paper under docs/research/paper needs creation, update, placeholder checking, or polishing."
---

# Research Paper

## Overview

Generate or update `docs/research/paper/` as the academic expression derived from the PRD. The target style is NeurIPS/ICLR/AAAI: sharp motivation, clear gap, rigorous formulation, concise contributions, strong method narrative, and structured evaluation design.

The final output of this skill must be a **complete, submission-ready conference manuscript draft**, not a fill-in template. It should read like a real NeurIPS / ICLR / AA AI paper: Abstract, Introduction, Related Work, Problem Formulation, Method, Experiments, Results, Limitations, and Conclusion. Do not leave visible `【待填写】` placeholders in the final paper.

The paper surface may be English, because it targets top-conference manuscript style. Explanatory blockers and gap reports are Chinese. The paper must remain derived from PRD and checked against Spec; it cannot create executable experiments by itself.

When empirical evidence is not ready, write a **placeholder-complete manuscript**. The Results section, tables, figure captions, and narrative should be structurally complete, but every unverified result value must remain an experiment-bound placeholder such as `{{E01.OURS.primary_metric}}`. Do not insert plausible numeric mock values.

## Narrative Modes

This skill supports two paper narratives:

**Method-driven narrative** (default):
```text
We propose method X → Experiments → Improvement
```

**Insight-driven narrative** (preferred when execution reveals structure):
```text
We identify phenomenon Y → We explain why it matters → We design minimal mechanism Z → Evidence
```

When empirical evidence is not ready, write a **placeholder-complete manuscript**. This means the paper is complete in structure and argument, while all unobserved empirical values stay as typed placeholders registered in `placeholder_map.yaml` and described in `paper_gap_report.md`.

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
- `We observe that ...` (insight-driven)
- `Our analysis reveals ...` (insight-driven)
- `This phenomenon suggests ...` (insight-driven)

## Placeholder Discipline for Unobserved Results

**Placeholder-complete manuscript (allowed in draft):**

The Results section, tables, and figures may be complete in layout, captions, comparison rows, method columns, and explanatory prose. However, unverified empirical cells must use typed placeholders, not plausible numbers:

```text
{{E01.OURS.primary_metric}}
{{E01.B01.primary_metric}}
{{E02.ablation_delta}}
```

**Forbidden without evidence:**

Do not use narrative language or numeric cells that present unverified findings as data:

- `Experiments show that ...`
- `Our method outperforms ...`
- `We achieve state-of-the-art ...`
- `The results demonstrate ...`
- any plausible numeric result value for an unobserved experiment

Instead, use neutral descriptive language:

- `Table 1 reports the performance of ...`
- `As shown in Fig. 2, ...`
- `The evaluation compares ...`

The distinction is not only narrative voice. Numeric placeholders must remain visible until the declared harnesses pass and the result is bound to real artifacts.

## Outputs

- `planned_paper.tex`
- `planned_paper.md`
- `planned_paper.pdf`
- `placeholder_map.yaml`
- `paper_gap_report.md`

`planned_paper.tex` is a real `ctexart` LaTeX source using `booktabs` and `tabularx`. If no LaTeX engine is available, generation records a render blocker instead of writing a fake PDF.

## Commands

```bash
python3 ~/.claude/skills/research-paper/scripts/generate_research_paper.py \
  --repo /absolute/path/to/repo \
  --force

python3 ~/.claude/skills/research-paper/scripts/generate_research_paper.py \
  --repo /absolute/path/to/repo \
  --demo \
  --force

python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode paper-ready
```

If the paper needs a missing claim, experiment, dataset, baseline, metric, formula, or table, record it in `paper_gap_report.md`; do not invent it.
