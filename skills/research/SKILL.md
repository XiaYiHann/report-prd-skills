---
name: research
description: "Use when a research workspace under docs/research needs the default autonomous controller across PRD, Spec, Plan, execution, audit, insight feedback, paper, or PPT stages."
---

# research

## Purpose

`research` is the unified autonomous research workflow controller.

It inspects `docs/research/`, resolves the current epoch from `CURRENT`, and advances one bounded research loop through Direction, PRD, Spec, Plan, Task Queue, Next Action, execution, gate, wiki, closeout, and paper binding.

新版系统是 **Charter-bounded Epoch Research Loop**：

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

## Core hierarchy

`RESEARCH_DIRECTION.md` constrains exploration.  
`CURRENT` resolves the active epoch.  
`Vn/PRD.md` defines the current research truth.  
`Vn/SPEC.yaml` constrains execution.  
`Vn/PLAN.md` schedules execution.  
`Vn/TASK_QUEUE.yaml` defines available work.  
`Vn/NEXT_ACTION.md` defines the only task for the current loop.  
Runs and artifacts provide evidence.  
Wiki records durable insight.  
Closeout controls next version or Paper Binding.

Authority chain:

```text
RESEARCH_DIRECTION.md
  -> CURRENT
  -> Vn/PRD.md
  -> Vn/SPEC.yaml
  -> Vn/PLAN.md
  -> Vn/TASK_QUEUE.yaml
  -> Vn/NEXT_ACTION.md
  -> Vn/runs + Vn/artifacts
  -> Vn/audits
  -> Vn/wiki
  -> Vn/closeout.md
  -> Vn+1/PRD.md 或 paper binding
```

Every `/research` run must first read:

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/NEXT_ACTION.md`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.md`
7. `docs/research/{CURRENT}/SPEC.yaml`
8. `docs/research/{CURRENT}/PLAN.md`

旧版本只读 `closeout.md` 和轻量 wiki。禁止让旧版本 PRD 覆盖当前版本 PRD。

## Execution policy

- Always execute the earliest incomplete gate, or write the precise next execution prompt when the controller cannot safely run harnesses itself.
- Default to the current `Vn`; do not advance legacy folders when `CURRENT` exists.
- Execute only `Vn/NEXT_ACTION.md`; do not skip `TASK_QUEUE.yaml`.
- Stay inside the Research Corridor.
- Do not create `Vn+1` before current `Vn/closeout.md` is complete and status is `closed_*`.
- Never infer experiments from paper.
- Never fabricate data, metrics, baselines, or results.
- Never use mock/toy/smoke outputs as claim evidence.
- If execution fails, retry within the current plan's allowed scope.
- If spec is incomplete but PRD is clear, repair spec and regenerate the plan.
- If PRD is ambiguous or a research hypothesis is challenged, stop and request human review.

## Insight policy

The goal is not to mechanically prove the initial idea.

The PRD is treated as the current best research hypothesis. The agent must record failures, anomalies, negative results, and surprising observations. It may propose diagnostic experiments or 15-degree pivots. It must not modify core PRD claims without human approval.

## Version transition policy

工程问题留在当前版本；研究问题改变才开下一版本。

Create `Vn+1` only when current status is closed and `closeout.md` says `create_next_version: true`, or when closeout shows that the main research question, core hypothesis, baseline landscape, metric/dataset/model choice, or phase has changed. Do not create a new version for code bugs, missing paths, reruns, minor spec field fixes, paper placeholder fixes, or stale-plan regeneration.

## Paper Binding policy

Paper Binding is allowed only when current status is `closed_stable` or `paper_binding_ready`, `PAPER_BINDING_DECISION.md` says `paper_binding_ready: true`, and every allowed claim is backed by experiment, run, artifact, metric, baseline, seed protocol, and audit status. Exploratory insight can support motivation or discussion only.

## Outputs

- `docs/research/RESEARCH_DIRECTION.md`
- `docs/research/CURRENT`
- `docs/research/Vn/STATUS.yaml`
- `docs/research/Vn/TASK_QUEUE.yaml`
- `docs/research/Vn/NEXT_ACTION.md`
- `docs/research/Vn/LOOP_LOG.md`
- `docs/research/Vn/wiki/*`
- `docs/research/Vn/closeout.md`
- `docs/research/Vn/PAPER_BINDING_DECISION.md`
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
