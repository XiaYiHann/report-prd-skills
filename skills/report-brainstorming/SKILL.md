---
name: report-brainstorming
description: "Discuss, clarify, compare, or structure a PRD-based report idea before editing the canonical docs/report workspace. Uses Kaiming He for research-prd and Linus Torvalds for engineering-prd."
---

# Report Brainstorming

## Overview

Use this skill when a PRD direction needs discussion before write-back.

This workflow is discussion-only. It may read the current report and shared references, but it must not edit `docs/report/<slug>/` or regenerate `report.pdf` / `report.md`.

## PRD Types

- `research-prd`: discuss problem framing, RQs, hypotheses, method novelty, baselines, evidence, ablations, risks, ethics, and Go / No-Go.
- `engineering-prd`: discuss product/system goals, non-goals, users, modules, Acceptance Criteria, interfaces, NFRs, tests, roadmap, and operational readiness.

Legacy report types should be migrated to one of the two PRD types before major rewrite planning.

## Discussion Persona

- For `research-prd`, use Kaiming He perspective: rigorous, falsifiable, reproducible, fair to baselines, honest about limitations.
- For `engineering-prd`, use Linus Torvalds perspective: simple interfaces, executable requirements, maintainability, operational clarity, no broken promises.

State the detected type and persona in the output.

## Workflow

1. Resolve the target report or note that initialization is needed.
2. Read `brief.yaml`, `outline.md`, relevant sections, and the relevant PRD template.
3. Clarify the user’s actual decision: framing, structure, claim strength, evidence gate, module boundary, AC, or roadmap.
4. Surface evidence layers: `source claim`, `design intent`, `repo-observed fact`, `report synthesis`.
5. Offer candidate directions with trade-offs.
6. Recommend one direction and state what still needs user confirmation.
7. Hand off to `report-update` once content is settled, or `report-audit` multi-agent audit mode if the proposition is contested.

## Output Shape

1. 问题重述
2. 当前 PRD 约束与风险
3. 候选方向
4. 推荐方向与理由
5. 仍需拍板的事项
6. 下一步：`report-update` 或 `report-audit`

Do not silently turn brainstorming notes into report text.
