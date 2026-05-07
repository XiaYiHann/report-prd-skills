# Student and Practitioner Writing Guide

Use this guide when the report should be readable by students, junior engineers, operators, analysts, or other first-time readers while still keeping a formal academic-paper tone.

## Default Tone

- Prefer direct language over academic fog.
- Sound professional and formal, but keep the prose pedagogically clear.
- Use short paragraphs.
- Introduce only one new idea at a time.
- Avoid compressing intuition, notation, and edge cases into one paragraph.

## Background and Definition Rules

When a topic is unfamiliar, do not jump straight to conclusions or formulas.

For every important concept, try to cover this order:

1. Why this concept exists
2. What problem it solves
3. Plain-language intuition
4. Formal definition
5. Example or scenario
6. Practical implication

Define key terms close to first use. If the section is jargon-heavy, add a mini glossary or symbol table instead of hoping the reader can infer the meaning.

For long or dense reports, add navigational support early instead of waiting until the reader is already lost.

- a short reading guide when the report has multiple layers
- a terminology table when the vocabulary is domain-specific
- a symbol table when formulas span more than one section
- a section map when the report mixes explanation, critique, and execution guidance

## Formula Explanations

For every important formula:

1. State what question the formula answers.
2. Define each symbol immediately.
3. Explain the intuition in plain language.
4. Show the derivation in small steps.
5. Give a numeric or conceptual example.
6. State the practical implication.
7. State when the formula should not be trusted or applied blindly.

Good pattern:

1. Problem
2. Intuition
3. Definition
4. Derivation
5. Example
6. Interpretation

## Algorithm Explanations

For every algorithm or procedure:

1. Explain the goal.
2. Name the inputs and outputs.
3. Show the main loop or decision rule.
4. Explain why the rule works.
5. Describe what can go wrong.
6. Compare it to a simpler baseline when helpful.
7. Explain what the person implementing or using the algorithm must pay attention to.

If pseudocode appears, surround it with explanation before and after. Never drop pseudocode into the report without narrative framing.

## Figures and Tables

Every figure should do one job:

- explain structure
- compare outcomes
- show a process
- reveal an insight

For each figure:

1. Introduce it before the figure appears.
2. Add a caption that says what the reader should notice.
3. Refer back to it in the following paragraph.

If the report reuses a paper figure, screenshot, or repo artifact, do not assume it teaches well enough by itself. Add either:

- a companion explanatory diagram in the report's own language
- or a follow-up paragraph that translates the figure into the reader's mental model

Borrowed figures are evidence artifacts. Original explanatory figures are teaching artifacts. Good reports often need both.

## Turning Theory into Action

When the report contains theory, always translate it back into execution language.

- If a definition affects implementation, say what must be configured or checked.
- If a theorem or result affects decision-making, say what choice it changes.
- If a metric affects evaluation, say how a reader should interpret a high or low value.
- If an assumption is fragile, say how the reader can detect that it has been violated.

## Evidence Boundary For Learners

When the report is based on a paper, repo, or external standard, make the evidence layers visible.

- say what the source explicitly claims
- say what the local repo or experiment output actually shows
- say what is your interpretation or recommendation

This is especially important for students, because beginners often confuse:

- "the paper says this worked"
- "the current codebase can reproduce this"
- "this is probably true in general"

Do not let those three statements collapse into one.

## Common Failure Modes

Avoid these patterns:

- defining symbols far away from the equation
- showing a final formula without explaining what changed between lines
- writing "it is obvious" or similar shortcuts
- using diagrams without textual interpretation
- assuming the reader already knows the domain vocabulary
- skipping a toy example when the math is dense
- sounding authoritative while leaving key terms undefined
- presenting a result without explaining why the result matters in practice
- giving only a summary when the reader actually needs operational detail

## Recommended Pedagogical Devices

Use these often:

- short "intuition first" subsections
- symbol tables for dense notation
- one worked example after a derivation
- "common misunderstanding" callouts
- brief recap paragraphs at the end of long sections
- "in practice" paragraphs after theory-heavy sections
- small decision checklists when the reader must apply the content
- short "what this section is trying to prove" openers for experiment sections
- claim / evidence / limitation tables when the report critiques results
