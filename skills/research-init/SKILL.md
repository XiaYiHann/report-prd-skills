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

The initializer must produce a serious research template, not an empty `TODO` skeleton. For the active epoch, `V0/PRD.tex` is the canonical source and uses `ctex` + TikZ tables/figures; `V0/PRD.pdf` is the review artifact; `V0/PRD_SUMMARY.md` is agent context only. Legacy `prd/research_prd.tex` and `research_prd.md` are compatibility artifacts.

The generated paper and spec are also real templates, not empty files:

- `paper/planned_paper.md` and `.tex` include a NeurIPS / ICLR / AAAI-style planned manuscript structure, placeholder discipline, and gap report.
- `spec/**/*.yaml` includes contract templates for RQ chains, reproduction targets, experiments, harnesses, evidence, anti-mock rules, and paper result bindings.
- YAML keys, IDs, and schema fields stay English; all explanatory values, blockers, prompts, criteria, and gap reports are Chinese.

## Source Model

- `RESEARCH_DIRECTION.md` is the fixed Big-RQ constitution: question, falsification boundary, evidence contract, and autonomy boundary.
- `Vn/RESEARCH_SPINE.yaml` is the machine-traceable decomposition: Big RQ → Sub-RQ → Hypothesis → Claim → Evidence → Experiment.
- Research PRD is the current epoch's human research contract for one or more Spine-bound sub-questions.
- Research Paper is derived academic expression.
- Research Spec is the machine-readable execution contract.
- Research Plan is a dated concrete execution run.
- Research Insight interprets existing evidence into current `Vn/wiki/*`.
- Research Audit checks drift among all artifacts and hard-gates the fixed Direction template.

## Command

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo /absolute/path/to/repo \
  --title "Project Title" \
  --purpose "minimum viable research goal"
```

Minimal scientific judgment mode:

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo /absolute/path/to/repo \
  --judgment-file /absolute/path/to/judgment.yaml \
  --force
```

`judgment.yaml` must contain `big_rq`, `core_hypothesis`, `falsification_condition`, `closest_baseline`, `dataset_or_environment`, `metric_or_judgment_rule`, and `stop_rule`. This mode compiles the user-facing judgment into `SCIENTIFIC_JUDGMENT.yaml`, approved `RESEARCH_DIRECTION.md`, PRD binding, Spine, RQ-local Spec/Plan/Tasks, Task Queue, and `EVIDENCE_GATE.yaml`. It does not create epoch-level `SPEC.yaml` or `PLAN.md`, does not lock baselines, and does not admit claims; `BASELINE_LOCK.yaml` remains `needs_human_review` until G0/G1 evidence is observed and audited.

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
- `docs/research/V0/GOAL_LOCK.yaml`
- `docs/research/V0/PRD.tex`
- `docs/research/V0/PRD.pdf` or `docs/research/V0/render_blocker.md`
- `docs/research/V0/PRD_SUMMARY.md`
- `docs/research/V0/EVIDENCE_GATE.yaml`
- `docs/research/V0/RESEARCH_SPINE.yaml`
- `docs/research/V0/STATUS.yaml`
- `docs/research/V0/TASK_QUEUE.yaml`
- `docs/research/V0/PAPER_TYPE.yaml`
- `docs/research/V0/rqs/RQ01/SPEC.yaml`
- `docs/research/V0/rqs/RQ01/PLAN.md`
- `docs/research/V0/rqs/RQ01/TASKS.yaml`
- `docs/research/V0/rqs/RQ01/reproduction/*`
- `docs/research/V0/LOOP_LOG.md`
- `docs/research/V0/GIT_STATE.yaml`
- `docs/research/V0/git_log.md`
- `docs/research/V0/runs/TASK_001_report.md`
- `docs/research/V0/runs/TASK_XXX_blocker.md` when a task blocks and triage is recorded
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
3. Inspect and fill `docs/research/V0/PRD.tex`; rerender `PRD.pdf` before treating the spec as executable.
4. Inspect `docs/research/RESEARCH_DIRECTION.md`, then fill and approve the Big RQ, falsification condition, MVR, evidence contract, and Research Corridor before letting agents explore.
5. Resolve current epoch through `docs/research/CURRENT`; default is `V0`.
6. Use `docs/research/V0/PRD_SUMMARY.md` only as agent context; do not let it override `PRD.tex`.
7. Let `/research` run the internal Spec compiler only after the active PRD has concrete RQs, hypotheses, benchmarks, experiments, harnesses, and evidence boundaries. Do not expose `research-spec` as a normal user entry.
8. Run validation:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode prd-ready
```

## Hard Rules

- Do not initialize `docs/report/` for new work. If the user explicitly requests it, record `report_init_blocker.md` explaining that `docs/research/` is the current architecture, wait for explicit human confirmation, and only then degrade to legacy initialization.
- Do not create execution-type `research-evidence` or `research-writing`; use `research-insight` for interpretation and `research-goal` only for version-level goal synthesis.
- Scaffold files may contain blockers; readiness validators must fail until contracts are concrete.
- PRD, Plan, prompts, gap reports, and explanatory YAML values must be Chinese.
- YAML keys and stable IDs stay English for parser compatibility.
- Use structured placeholders such as `【待填写：...】`; do not leave raw `TODO` placeholders.
- `CURRENT` defaults to `V0`.
- `V0/STATUS.yaml` defaults to `status=initialized`.
- `V0/goal.md` is generated by `research-goal` as the per-version high-level execution prompt and constraint anchor. It defines the overall mission for the entire `V0`, every RQ's plan/task coverage, the version task dependency graph, the code-review-first triage rule for blocked tasks, and the blocker-note convention for `runs/TASK_XXX_blocker.md`; it is not a single-step action note. Task scheduling still comes from `TASK_QUEUE.yaml`, with orthogonal runnable tasks allowed to continue when an unrelated branch is blocked.
- Goal mode follows repair-then-execute: when contract drift has a single latest approved design source, repair stale secondary contracts, refresh `goal.md` / `GOAL_LOCK.yaml`, run `goal-ready` after the drift repair, and do not stop after a repair-only pass; continue executing the runnable task set until all goal tasks complete or a true human-owned blocker remains.
- Generated `goal.md` must include `prefer_subagents`: 优先使用 subagent 执行 bounded specialist work while keeping state updates and gate decisions in the main controller.
- `V0/GOAL_LOCK.yaml` records the source refs and hashes used to synthesize `goal.md`; `goal-ready` must fail when PRD, baseline lock, baseline dossier, spine, RQ-local contracts, task queue, evidence gate, status, or direction changes without a goal refresh.
- `V0/PRD.tex` defaults to active task: 完善并人工批准 `RESEARCH_DIRECTION.md` 与 `V0/PRD.tex`。
- `V0/rqs/RQ01/` defaults to the first RQ-local contract scaffold; every declared RQ must have local `SPEC.yaml`, `PLAN.md`, `TASKS.yaml`, and reproduction verification files.
- `V0/TASK_QUEUE.yaml` tasks include a Git policy block.
- `V0/GIT_STATE.yaml` disables push by default and records commit/tag policies.
- Do not delete legacy `prd/spec/plans/audits/insights`; mark them as legacy-compatible context.
