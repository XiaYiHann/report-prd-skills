---
name: research
description: "Use when a research workspace under docs/research needs the default autonomous controller across PRD, Spec, Plan, execution, audit, insight feedback, paper, or PPT stages."
---

# research

## Purpose

`research` is the unified autonomous research workflow controller.

It inspects `docs/research/`, determines the current project stage, and advances the project through PRD, Spec, Plan, execution, audit, insight feedback, paper, and PPT stages.

## Core hierarchy

PRD defines research.  
Spec constrains execution.  
Plan schedules execution.  
Harness decides completion.  
Artifacts provide evidence.  
Audit controls feedback.

## Execution policy

- Always execute the earliest incomplete gate, or write the precise next execution prompt when the controller cannot safely run harnesses itself.
- Never infer experiments from paper.
- Never fabricate data, metrics, baselines, or results.
- Never use mock/toy/smoke outputs as claim evidence.
- If execution fails, retry within the current plan's allowed scope.
- If spec is incomplete but PRD is clear, repair spec and regenerate the plan.
- If PRD is ambiguous or a research hypothesis is challenged, stop and request human review.

## Insight policy

The goal is not to mechanically prove the initial idea.

The PRD is treated as the current best research hypothesis. The agent must record failures, anomalies, negative results, and surprising observations. It may propose diagnostic experiments or 15-degree pivots. It must not modify core PRD claims without human approval.

## Outputs

- `docs/research/state.yaml`
- `docs/research/plans/plan_queue.yaml`
- dated plans under `docs/research/plans/YYYY-MM-DD-purpose/`
- audit reports under `docs/research/audits/YYYY-MM-DD-audit/`
- insight logs under `docs/research/insights/`
- spec feedback under `docs/research/spec/feedback/`
- human review requests under `docs/research/audits/YYYY-MM-DD-prd-review/`

## Command

```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo /absolute/path/to/repo --once
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --max-steps 1
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --dry-run --json
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --track reproduction
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --force-audit
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --executor prompt-only
```

The current implementation is a deterministic file-based controller. It creates and updates state, queues, plans, blocker files, feedback, audits, and next-step prompts. It does not fabricate harness outputs or claim that experiments ran when no harness was executed.

## Execution Backend

`--executor` is intentionally explicit:

- `prompt-only` is implemented now.
- `local-shell`, `codex`, and `hermes` are reserved backend slots.

Until a backend is implemented and tested, `/research` must not claim that it ran harnesses or generated experimental evidence.

## Claude Code Subagents

When project-level subagents are installed under `.claude/agents/`, `/research` remains the controller and the subagents are specialized workers:

- `research-math` for formulation and notation checks.
- `research-literature` for related work, benchmark, and baseline analysis.
- `research-reproduce` for baseline reproduction.
- `research-coding` for implementation under the current plan.
- `research-experiment` for declared experiment execution.
- `research-analysis` for anomalies, negative results, and pivot proposals.
- `research-paper` for placeholder-safe manuscript updates.
- `research-ppt` for slide-image deck planning.
- `research-audit` for cross-file drift and evidence checks.

Do not use a custom registry as the primary subagent format. Claude Code project agents are Markdown files with YAML frontmatter in `.claude/agents/`.
