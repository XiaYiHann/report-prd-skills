---
name: report-debate
description: "Use when a PRD report section, paragraph, claim, baseline, acceptance criterion, or design choice needs adversarial pro/con reasoning rather than open-ended brainstorming. Writes back only after confirmation."
---

# Report Debate

## Overview

Use this skill when a PRD section is under-argued, controversial, or likely to hide assumptions. This is not a generic brainstorm workflow. It is a structured debate over an existing section, claim, baseline, acceptance criterion, or design choice in a report workspace.

If the problem is still open-ended and the proposition is not crisp yet, switch to `report-brainstorming` first.

The default target is an existing section under a report workspace. The result should be written back into the same report only after the debate proposition and final rewrite direction are confirmed.

## Input Contract

Minimum inputs:

- target report workspace
- target section file or paragraph location
- proposition to debate
- PRD type (`research-prd` or `engineering-prd`)

Optional but useful:

- audience
- immutable assumptions
- candidate options that must be compared
- preferred source scope

Before launching the two agents, confirm with the user:

- the exact proposition being debated
- the target section or paragraph
- any immutable assumptions
- any candidate options that must be compared
- whether the result should revise only a paragraph, a subsection, or the full section

## Two-Agent Protocol

Generate a shared debate brief first:

```bash
python3 ~/.agents/skills/report/_shared/scripts/compile_debate_brief.py --report-dir /absolute/path/to/report-dir --section 05-core-design.tex --proposition "这里的技术路线是否成立"
```

Launch two isolated analyses. If parallel agents are available, run them independently; if not, run pro then con sequentially using only the shared brief and without exposing one side's intermediate output to the other:

- `pro`: defend the current wording or proposed design
- `con`: challenge the current wording or proposed design

Both agents may:

- read the target section
- read the same debate brief
- browse the web
- cite official docs, standards, papers, and primary project pages

Both agents may not:

- see each other's intermediate output
- edit the report directly
- reject a design only because the current repo does not yet implement it
- blur together `source claim`, `design intent`, `repo-observed fact`, and `report synthesis`

## Synthesis Protocol

The synthesizer is the main agent. Do not just count votes. Produce these seven items:

1. 当前争议点是什么
2. 正方最强论据是什么
3. 反方最强论据是什么
4. 哪些论点是事实，哪些是价值判断，哪些是前提假设
5. 现阶段更公允的结论是什么
6. 对 PRD 正文、Evidence Ledger 或 Acceptance Criteria 应如何改写
7. 还剩哪些不确定项需要后续验证

Before writing the final text back into the report, summarize the synthesis to the user and let the user confirm the intended write-back direction.

## When NOT to Use

Do not use this skill when:

- The problem is still open-ended — use `report-brainstorming` first
- The user wants a simple review — use `report-audit`
- The user wants to update confirmed content — use `report-update`
- The report workspace does not exist — use `report-init`

## Shared Contract

This skill follows the `report` family shared contract defined in `../report/SKILL.md`. Key points:

- Four evidence layers: both agents must keep them distinct
- Repo status: do not reject a design only because current repo does not implement it
- Writing style: synthesis should use formal Chinese with academic rigor
- Research PRD debates must identify whether the issue is a claim, hypothesis, baseline, ablation, evidence gate, or limitation.
- Engineering PRD debates must identify whether the issue is a goal, non-goal, interface, module boundary, Acceptance Criteria, NFR, rollout, or operational gate.

## Write-Back Rule

Default write-back shape:

- revise the original paragraph or section
- add a subsection named `争议与裁决`
- add a comparison table when the decision depends on assumptions, alternatives, or major trade-offs

For LaTeX reports, generate a write-back skeleton first:

```bash
python3 ~/.agents/skills/report/_shared/scripts/generate_debate_section.py --title "技术路线裁决" --proposition "这里的技术路线是否成立"
```

After rewriting:

1. run a local consistency sweep on the affected concept
2. re-render `report.pdf` and `report.md`
3. inspect compile review, Markdown output, and self-check outputs

```bash
python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
```

If the debate result changes the framing of adjacent sections, hand the report back through `report-update` or do an equivalent report-wide consistency pass before stopping.

## Shared Resources

- `../report/_shared/scripts/compile_debate_brief.py`
- `../report/_shared/scripts/generate_debate_section.py`
- `../report/_shared/scripts/render_report.py`
- `../report/_shared/references/debate-protocol.md`
- `../report/_shared/references/decision-gates.md`
- `../report/_shared/references/executor-report-style.md`
- `../report/_shared/references/anti-patterns.md`

Read `../report/_shared/references/debate-protocol.md` before running the debate when the section is non-trivial.
