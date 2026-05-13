---
name: research-init
description: "Use when a repo needs a new docs/research workspace or when an older report-style research workspace needs migration."
---

# Research Init

## Overview

Initialize `docs/research/` as the durable workspace for the research execution skill family. This is setup only: it creates the **Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop** workspace plus legacy-compatible PRD/Paper/Spec/Plan/Audit directories without inventing datasets, baselines, metrics, commands, or results.

Definition:

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

The initializer must produce a serious research template, not an empty `TODO` skeleton. `research_prd.tex` is the canonical source and uses `ctex` + TikZ tables/figures; `research_prd.md` is the Chinese companion reading artifact.

The generated paper and spec are also real templates, not empty files:

- `paper/planned_paper.md` and `.tex` include a NeurIPS / ICLR / AAAI-style planned manuscript structure, placeholder discipline, and gap report.
- `spec/**/*.yaml` includes contract templates for RQ chains, reproduction targets, experiments, harnesses, evidence, anti-mock rules, and paper result bindings.
- YAML keys, IDs, and schema fields stay English; all explanatory values, blockers, prompts, criteria, and gap reports are Chinese.

## Source Model

- Research PRD is the human research source of truth.
- Research Paper is derived academic expression.
- Research Spec is the machine-readable execution contract.
- Research Plan is a dated concrete execution run.
- Research Insight interprets existing evidence into current `Vn/wiki/*`.
- Research Audit checks drift among all artifacts.

## Command

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo /absolute/path/to/repo \
  --title "Project Title" \
  --purpose "minimum viable research goal"
```

The command creates the new default structure:

- `docs/research/RESEARCH_DIRECTION.md`
- `docs/research/CURRENT`
- `docs/research/INDEX.md`
- `docs/research/agent/RUNBOOK.md`
- `docs/research/agent/CLAUDE_LOOP_PROMPT.md`
- `docs/research/agent/CODEX_GOAL_TEMPLATE.md`
- `docs/research/agent/SUBAGENT_POLICY.md`
- `docs/research/agent/LITERATURE_POLICY.md`
- `docs/research/agent/GIT_POLICY.md`
- `docs/research/explore/sessions/EXP_0001.md`
- `docs/research/explore/syntheses/EXP_SYNTHESIS.md`
- `docs/research/explore/proposals/*`
- `docs/research/V0/goal.md`
- `docs/research/V0/PRD.md`
- `docs/research/V0/SPEC.yaml`
- `docs/research/V0/PLAN.md`
- `docs/research/V0/STATUS.yaml`
- `docs/research/V0/TASK_QUEUE.yaml`
- `docs/research/V0/NEXT_ACTION.md`
- `docs/research/V0/LOOP_LOG.md`
- `docs/research/V0/GIT_STATE.yaml`
- `docs/research/V0/git_log.md`
- `docs/research/V0/runs/TASK_001_report.md`
- `docs/research/V0/wiki/*`
- `docs/research/V0/closeout.md`
- `docs/research/V0/PAPER_BINDING_DECISION.md`
- root `AGENTS.md`
- root `CLAUDE.md`

It also keeps legacy-compatible directories:

- `docs/research/prd/`
- `docs/research/paper/`
- `docs/research/spec/`
- `docs/research/plans/`
- `docs/research/audits/`
- `docs/research/insights/` as compatibility storage only; current epoch insight belongs in `docs/research/V0/wiki/*`.

If `latexmk` or `xelatex` is available, initialization renders a real PDF from the `.tex` source. If no LaTeX engine is available, it writes a Chinese `render_blocker.md` and does not create a fake PDF.

## Workflow

1. Resolve the repository root.
2. Run the initializer.
3. Inspect `docs/research/prd/research_prd.md` and fill the Research PRD before treating the spec as executable.
4. Inspect `docs/research/RESEARCH_DIRECTION.md`, then fill and approve the Research Corridor before letting agents explore.
5. Resolve current epoch through `docs/research/CURRENT`; default is `V0`.
6. Fill `docs/research/V0/PRD.md`; this is the active epoch's research truth.
7. Run `research-spec` only after the active PRD has concrete RQs, hypotheses, benchmarks, experiments, harnesses, and evidence boundaries.
8. Run validation:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode prd-ready
```

## Hard Rules

- Do not initialize `docs/report/` for new work. If the user explicitly requests it, record `report_init_blocker.md` explaining that `docs/research/` is the current architecture, wait for explicit human confirmation, and only then degrade to legacy initialization.
- Do not create `research-evidence`, `research-writing`, or `research-goal`; use `research-insight` for interpretation.
- Scaffold files may contain blockers; readiness validators must fail until contracts are concrete.
- PRD, Plan, prompts, gap reports, and explanatory YAML values must be Chinese.
- YAML keys and stable IDs stay English for parser compatibility.
- Use structured placeholders such as `【待填写：...】`; do not leave raw `TODO` placeholders.
- `CURRENT` defaults to `V0`.
- `V0/STATUS.yaml` defaults to `status=initialized`.
- `V0/goal.md` defaults to a scaffold with YAML frontmatter (`version`, `language`, `style`, `evidence_rule`, `gate_strategy`, `commit_policy`) and Chinese body sections: 工作目录, 全局约束, 版本目标, 总规则, Gate 序列, 测试要求, 提交要求, 最终回复格式. It is the per-version high-level execution prompt and constraint anchor.
- `V0/NEXT_ACTION.md` defaults to active task: 完善并人工批准 `RESEARCH_DIRECTION.md` 与 `V0/PRD.md`。
- `V0/TASK_QUEUE.yaml` tasks include a Git policy block.
- `V0/GIT_STATE.yaml` disables push by default and records commit/tag policies.
- Do not delete legacy `prd/spec/plans/audits/insights`; mark them as legacy-compatible context.
