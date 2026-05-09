---
name: research-prd
description: "Use when docs/research/prd needs a professional Research PRD for a concrete master-student execution project."
---

# Research PRD

## Overview

Maintain `docs/research/prd/research_prd.md` and `research_prd.tex` as the human research source of truth. The PRD is verbose, pedagogical, technically rigorous, and execution-oriented for capable master students who may lack full background.

## Required Chapter Structure

The PRD must contain exactly these top-level sections:

1. Executive Summary
2. Background Tutorial
3. Related Work Map
4. Benchmark and Reproduction Plan
5. Problem Statement
6. Research Questions and Hypotheses
7. Formalization
8. Proposed Method
9. System and Implementation Design
10. Experiment Design
11. Task Graph and Student Work Plan
12. Harness and Acceptance Criteria
13. Evidence Ledger
14. Paper Plan
15. Risks, Limitations, and Ethics

Do not include a visible `Reader Model and Usage` section. Treat that as an internal writing assumption.

## Content Rules

- Define concrete tasks, benchmarks, experiments, validation conditions, and Go / No-Go checkpoints.
- Include reproduction modes: `official_code_reuse`, `official_code_adaptation`, or `paper_based_reimplementation`.
- Separate planned evidence from observed evidence.
- Map every claim to evidence requirements before allowing it into the paper.
- Explain enough background for a strong but non-expert master student.

## Validation

```bash
python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode prd-ready
```

If a required section is missing, fix the PRD before generating Paper, Spec, Plan, PPT, or Audit.
