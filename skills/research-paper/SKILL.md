---
name: research-paper
description: "Use when a planned top-conference-style research paper under docs/research/paper needs creation, update, placeholder checking, or polishing. If the current epoch is not closed_stable, produce a placeholder-complete manuscript or gap report. If the epoch is closed_stable or paper_binding_ready and the Paper Binding Gate is satisfied, produce a binding-ready manuscript."
---

# Research Paper

## Overview

Generate or update `docs/research/paper/` as the academic expression derived from the current closed epoch. Paper is an expression layer, not an experiment source. The target style is NeurIPS/ICLR/AAAI: sharp motivation, clear gap, rigorous formulation, concise contributions, strong method narrative, and structured evaluation design.

The final output of this skill must be a **complete, submission-ready conference manuscript draft**, not a fill-in template. It should read like a real NeurIPS / ICLR / AA AI paper: Abstract, Introduction, Related Work, Problem Formulation, Method, Experiments, Results, Limitations, and Conclusion. Do not leave visible `【待填写】` placeholders in the final paper.

The paper surface may be English, because it targets top-conference manuscript style. Explanatory blockers and gap reports are Chinese. The paper must remain derived from PRD and checked against Spec; it cannot create executable experiments by itself.

This skill performs **expression execution** (document compilation, file output, LaTeX rendering). It does not perform **experiment execution** (running new experiments, generating undeclared data, or modifying `STATUS.yaml` / `RESEARCH_DIRECTION.md`). Expression execution is within this skill's scope; experiment execution is not.

## Skill Invocation Contract

Conceptual command forms:

```text
/research paper
/research paper --mode draft
/research paper --mode binding
```

`/research paper` is invoked through the `research` controller. It does not run as a top-level skill outside the research loop.

## Paper Binding Gate

Paper Binding can happen only when all conditions hold:

- `docs/research/CURRENT` points to a version whose `STATUS.yaml` is `closed_stable` or `paper_binding_ready`;
- `Vn/closeout.md` exists;
- `Vn/PAPER_BINDING_DECISION.md` sets `paper_binding_ready: true`;
- paper claim does not exceed `Vn/closeout.md`;
- every paper claim must trace forward to a Figure/Table and backward to Evidence via `Vn/RESEARCH_SPINE.yaml`;
- exploratory insight is used only for motivation / discussion, not main result;
- prompt-only scaffold is not used as experiment result;
- no unresolved negative result undermines the claim;
- artifact, run record, metric, baseline, seed protocol, audit status, real data check, real model/code check, and non-smoke full-run check support the claim.
- `PAPER_CLAIM_LEDGER.yaml` is the authoritative gate for which claims may enter the paper. It is distinct from `RESEARCH_SPINE.yaml` (planning/discovery spine): the Ledger tracks claim status (`allowed`, `blocked`, `pending_audit`) and reproduction evidence compatibility. Paper binding must not exceed the Ledger.
- `PAPER_BINDING_DECISION.md` records `real_data_check`, `real_model_check`, and `non_smoke_full_run` for every allowed claim.
- `PAPER_BINDING_DECISION.md` records source commit, paper binding commit, and paper binding tag when Git is enabled.
- working tree is clean unless an explicit dirty-tree blocker/justification is recorded.

If the gate is not satisfied, write a placeholder-complete manuscript or a gap report. Do not inject result numbers.

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

Validate paper binding:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode paper-binding-ready
```
