---
name: research-audit
description: "Use when landed research artifacts may be stale, inconsistent, or drifted across PRD, Paper, Spec, Plans, PPT, and artifacts."
---

# Research Audit

## Overview

Audit already-written files. This is not a paper review only; it is a cross-file drift detector for:

- PRD
- Paper
- Spec
- Plans
- PPT
- artifacts if present

## Required Questions

- PRD updated but paper not updated?
- PRD updated but spec not updated?
- Spec updated but existing plan is stale?
- Paper has an experiment not in spec?
- Plan has a task or harness not in spec?
- Spec has an experiment not in PRD?
- PPT has claim or result not grounded in PRD, paper, or spec?
- Are there insights in `docs/research/insights/` not reflected in the latest spec?
- Are there open pivot proposals without human decision?
- Are negative results hidden (not logged)?
- Does the PRD still claim something contradicted by a recorded insight?
- Are diagnostic experiments proposed but not scheduled in spec/plan?

## Outputs

`docs/research/audits/YYYY-MM-DD-audit/`:

- `audit_report.md`
- `alignment_matrix.yaml`
- `drift_findings.yaml`
- `repair_plan.md`

`repair_plan.md` now splits repairs into:
- **must-fix-before-execution** (execution failures)
- **insight-opportunity** (research failures / anomalies / diagnostic experiments)
- **can-fix-later**
- **recommended next research-plan target**
- **recommended next insight-feedback target**

## Command

```bash
python3 ~/.claude/skills/research-audit/scripts/generate_research_audit.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09

python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode audit-ready
```

`repair_plan.md` must separate must-fix-before-execution, can-fix-later, and recommended next `research-plan` target.
