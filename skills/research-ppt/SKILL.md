---
name: research-ppt
description: "Use when a research project needs a slide-image deck plan for Codex plus ImageGen, PNG slide pages, or PDF export."
---

# Research PPT

## Overview

Generate `docs/research/ppt/main_deck/` as a slide-image deck specification. This workflow creates prompts and render plans for PNG pages and final PDF export. It must not create a traditional `.pptx` deck.

## Inputs

- Primary source: Research PRD.
- Secondary source: Research Paper.
- Constraint source: Research Spec.

## Outputs

- `deck_spec.yaml`
- `slide_manifest.yaml`
- `slide_prompts/*.md`
- `slide_notes.md`
- `deck_gap_report.md`
- `render_plan.md`
- `pages/*.png`
- `exports/main_deck.pdf`

## Modes

- `short`: 5-7 slides
- `standard`: 10-12 slides, default
- `long`: 15-20 slides
- `pitch`
- `defense`

## Command

```bash
python3 ~/.agents/skills/research-ppt/scripts/generate_research_ppt.py \
  --repo /absolute/path/to/repo \
  --mode standard

python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode ppt-ready
```

## Visual Rules

- top-tier academic conference talk;
- clean, modern, professional, figure-centric;
- white or very light background;
- one clear takeaway per slide;
- no invented experiments, results, or unregistered claims;
- no `.pptx` assumption.
