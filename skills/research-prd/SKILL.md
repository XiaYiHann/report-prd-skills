---
name: research-prd
description: "Use when docs/research/prd needs a professional Research PRD for a concrete research execution project."
---

# Research PRD

## Overview

Maintain `docs/research/prd/research_prd.tex` and `research_prd.md` as the human research source of truth. The LaTeX file is canonical; the Markdown file is a Chinese companion artifact for review and agent context.

The PRD must be verbose, pedagogical, technically rigorous, and execution-oriented for capable master students who may lack full background. It should read like a professional research execution document, not a short paper outline.

## Required Chapter Structure

The PRD must contain exactly these top-level sections, using Chinese headings with the English canonical label in parentheses:

1. 执行摘要（Executive Summary）
2. 背景教程（Background Tutorial）
3. 相关工作地图（Related Work Map）
4. 基准与复现计划（Benchmark and Reproduction Plan）
5. 问题陈述（Problem Statement）
6. 研究问题与假设（Research Questions and Hypotheses）
7. 形式化定义（Formalization）
8. 拟议方法（Proposed Method）
9. 系统与实现设计（System and Implementation Design）
10. 实验设计（Experiment Design）
11. 任务图与学生工作计划（Task Graph and Student Work Plan）
12. Harness 与验收标准（Harness and Acceptance Criteria）
13. 证据台账（Evidence Ledger）
14. 论文计划（Paper Plan）
15. 风险、局限与伦理（Risks, Limitations, and Ethics）
16. 探索与洞察策略（Exploration and Insight Policy）

Do not include a visible `Reader Model and Usage` section. Treat that as an internal writing assumption.

## Content Rules

- Define concrete tasks, benchmarks, experiments, validation conditions, and Go / No-Go checkpoints.
- Include reproduction modes: `official_code_reuse`, `official_code_adaptation`, or `paper_based_reimplementation`.
- Separate planned evidence from observed evidence.
- Map every claim to evidence requirements before allowing it into the paper.
- Explain enough background for a strong but non-expert master student.
- Every major chapter should include a table or TikZ figure placeholder.
- At minimum, keep figures for research-problem-to-evidence chain, method modules, experiment/reproduction flow, and Spec -> Plan -> Audit loop.
- Each chapter should state chapter goal, required content, common mistakes, evidence boundary, and acceptance criteria.
- Use `【待填写：...】` placeholders. Do not leave raw `TODO`.
- Do not fabricate empirical findings, dataset details, baseline performance, metric values, or claim evidence.
- **The PRD is the current best research hypothesis, not an immutable truth.** The agent may propose pivots based on execution evidence, but core RQ and claim changes require human approval.

## Human Clarification Rules (PRD Writing)

When writing or revising the PRD, the agent MUST stop and request human review before proceeding if any of the following conditions are met:

1. **Ambiguous research question**: The user's stated goal can be interpreted as more than one distinct research question.
2. **Contradictory constraints**: RESEARCH_DIRECTION.md, prior PRD sections, Paper, or Spec contain mutually exclusive requirements with no explicit priority rule.
3. **Missing evidence boundary**: The user requests a claim but does not define what evidence would support or refute it.
4. **Methodology divergence**: The proposed method deviates from the user's stated approach by more than a 15-degree pivot.
5. **Scope expansion**: Adding a new section, benchmark, baseline, or experiment would exceed the current epoch's stated goal or RESEARCH_DIRECTION.md boundary.
6. **Spine Matrix inconsistency**: A Claim ID lacks a bound Experiment ID and the agent cannot infer a reasonable default from PRD context.

Do NOT silently resolve ambiguity by choosing the most convenient interpretation. Record the ambiguity as a blocker in `HUMAN_REVIEW_REQUESTS.yaml` or the PRD gap report, then stop and ask.

## Epoch PRD (`Vn/PRD.md`)

For the active epoch, `Vn/PRD.md` is a lightweight 11-section contract. It must include:

- **Research Spine Matrix** as Section 2: a markdown table mapping `RQ ID -> Claim ID -> Experiment ID -> Evidence -> Figure/Table -> Paper Section` with a `Status` column (`planned` / `running` / `supported` / `missing` / `blocked`).
- Every claim in the Spine Matrix must have at least one bound experiment before the PRD is considered `prd_locked`.
- The Spine Matrix is the agent-facing execution contract; narrative sections (Core Question, Core Hypothesis, etc.) serve the matrix.
- **RQ boundary rule**: Every `RQ ID` declared in the Spine Matrix must fall within the scope defined by `RESEARCH_DIRECTION.md`. If an RQ would expand beyond the research corridor, stop and request human review before adding it to the matrix.

## Validation

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode prd-ready
```

If a required section is missing, fix the PRD before generating Paper, Spec, Plan, Insight, or Audit.
