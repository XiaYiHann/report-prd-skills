# Report Debate Protocol

## Purpose

Use this protocol when a report section is under-argued, controversial, or likely to hide assumptions. The goal is not to let two agents improvise opinions. The goal is to force the decision into a structured record that distinguishes evidence, assumptions, and judgment.

This protocol is for design-document debate, not current-state repo verification. A future-state design may still be valid even when it is not implemented yet.

## Input Contract

Minimum inputs:

- report workspace path
- target section or paragraph
- proposition to debate

Optional but useful inputs:

- audience
- immutable assumptions
- candidate options that must be compared
- preferred source scope

Before starting the debate, confirm these inputs with the user. Do not let the debate workflow silently invent the proposition, baseline set, or write-back scope.

## Two-Agent Protocol

Launch two isolated analyses. If parallel agents are available, run them independently; if the current environment cannot spawn parallel agents, run pro then con sequentially using only the shared debate brief and without exposing one side's intermediate output to the other:

- `pro`: defend the current wording or the current proposed design
- `con`: attack the current wording or the current proposed design

Both agents may:

- read the target section
- read the same debate brief
- browse the web
- cite official docs, standards, papers, and primary project pages

Both agents may not:

- see each other's intermediate output
- directly edit the report
- reject a design only because the repo does not yet implement it
- collapse all evidence into one undifferentiated claim

## Required Classification

When synthesizing the debate, classify claims into:

- `source claim`
- `design intent`
- `repo-observed fact`
- `report synthesis`

Also classify each major argument as one of:

- factual statement
- value judgment
- prerequisite assumption

## Required Output Shape

The synthesizer should produce these seven items:

1. 当前争议点是什么
2. 正方最强论据是什么
3. 反方最强论据是什么
4. 哪些论点是事实，哪些是价值判断，哪些是前提假设
5. 现阶段更公允的结论是什么
6. 对正文应如何改写
7. 还剩哪些不确定项需要后续验证

After synthesis and before write-back, send the planned direction back to the user for confirmation. The user should approve the intended rewrite scope before the report is edited.

## Write-Back Rule

Default write-back shape:

- revise the original paragraph or section
- add a subsection named `争议与裁决`
- add a table when the decision involves multiple candidate options, major assumptions, or non-trivial trade-offs

Recommended columns:

- `观点`
- `最强依据`
- `成立前提`
- `主要风险`
- `裁决`

If the report uses the standard LaTeX workflow, prefer generating a reusable write-back skeleton first:

```bash
python3 ~/.agents/skills/report/_shared/scripts/generate_debate_section.py --title "技术路线裁决" --proposition "这里的技术路线是否成立"
```

Then fill the generated subsection and table instead of improvising the layout by hand.

## Quality Checks

Before accepting the result, verify:

- the synthesis did not confuse future design with current implementation
- the conclusion is more precise than the original paragraph
- at least one strong argument from each side survived into the synthesis
- the final wording remains formal academic prose while still being understandable to a serious first-time reader
- unresolved uncertainty is stated explicitly rather than hidden
