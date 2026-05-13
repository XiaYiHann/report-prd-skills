---
name: research-plan
description: "Use when a dated research execution run needs a bounded plan, AI loop prompt, source hashes, gates, or harness scope from Research Spec."
---

# Research Plan

## Overview

Create bounded execution plans for the current epoch. New default outputs are `docs/research/{CURRENT}/PLAN.md`, `TASK_QUEUE.yaml`, and `NEXT_ACTION.md`; legacy dated plans under `docs/research/plans/YYYY-MM-DD-purpose/` remain supported. A plan is a bounded run contract for Codex or Claude Code. Its **executable contracts** are derived from `Vn/SPEC.yaml`; Paper provides context only after paper binding is allowed. When Paper and Spec conflict, Spec wins.

Plan prose, AI loop prompts, and run logs must be Chinese. `plan.yaml` keeps English keys and stable IDs, but explanatory values such as `purpose`, `forbidden_actions`, and `completion_condition` should be Chinese.

## Supported Tracks

- `reproduction`
- `implementation`
- `experiment`
- `paper-update`
- `insight-feedback`

Supported selectors:

- `--gate G_ID`
- `--target codex`
- `--target ralph-loop`

## Outputs

- `docs/research/{CURRENT}/PLAN.md`
- `docs/research/{CURRENT}/TASK_QUEUE.yaml`
- `docs/research/{CURRENT}/NEXT_ACTION.md`
- `plan.md`
- `plan.yaml`
- `ai_loop_prompt.md`
- `current_state.md`
- `blocker_log.md`
- `decision_log.md`
- `run_log.md`
- `insight_log.md` (legacy compatibility)
- `final_summary.md`

## Prerequisites

- `research-spec` must be installed; the plan generator reads `Vn/SPEC.yaml` and calls `validate_research.py`.
- `research-init` shared scripts must be on the Python path.

## Command

```bash
python3 ~/.claude/skills/research-plan/scripts/generate_research_plan.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09 \
  --purpose reproduce-b01 \
  --track reproduction \
  --target codex
```

Validate:

```bash
python3 ~/.claude/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode plan-ready
```

## AI Loop Contract

For the epoch loop, Plan must encode:

```yaml
version: V0
loop_target: paper_binding
loop_mode:
  claude_code: ralph_loop
  codex: goal_driven
active_task_source: TASK_QUEUE.yaml
single_step_file: NEXT_ACTION.md
```

Plan generation must first read `Vn/goal.md` and inject its global constraints (language, style, evidence rules, gate strategy, commit policy) into `PLAN.md` and `ai_loop_prompt.md`. The goal.md constraints are the ceiling; PLAN.md and NEXT_ACTION.md must not contradict them.

**Distinction**: `goal.md` is the version-level anchor that defines the overall mission for the entire `Vn`. `PLAN.md` is the concrete execution schedule derived from it. `NEXT_ACTION.md` is the task-level file that changes every loop and names exactly one atomic deliverable. Do not conflate the version goal with the current task.

Loop rules:

- Each loop may complete at most one active task.
- After each loop, update `LOOP_LOG.md`.
- If blocked twice by same cause, escalate to `gate_blocked`.
- If no active task exists, generate one from `PLAN.md` or close version.
- Do not start a new version unless current version is closed.
- Stay inside `RESEARCH_DIRECTION.md`.
- Plan complete does not equal Paper Binding.
- Record Git state before and after task execution when Git is available.
- Write `runs/TASK_XXX_report.md` with diff summary, commands, evidence, and commit hash.

Codex goal rules:

- Codex goal must name one concrete deliverable.
- Codex must run tests when code changes.
- Codex must cite terminal/test evidence in run report.
- Codex must cite Git diff/commit evidence when a task commit is created.
- Codex should not perform broad literature search unless task `phase=literature` and network is available.

Claude ralph-loop rules:

- Read `NEXT_ACTION.md` first.
- Do not expand scope mid-loop.
- Use subagents for large search or audit work.
- Write compact persistent state after each loop.
- Never rely on previous chat memory.

Git protocol:

- Before work: `git status --short`, current commit hash.
- After work: tests if code changed, `git diff --stat`, update `LOOP_LOG.md`, optionally commit current task according to `TASK_QUEUE.yaml.git`, record hash in `GIT_STATE.yaml`.
- Never push, reset, clean, rebase, force push, rewrite history, or delete out-of-scope files unless the user explicitly authorizes it.

## AI Loop Prompt Enforcement

`generate_research_plan.py` is responsible for generating `ai_loop_prompt.md`. The following clauses are machine-enforced requirements, not advisory suggestions:

`ai_loop_prompt.md` must contain:

- 可执行真源是 `docs/research/spec/`；执行时以 Spec 为准，Paper 为辅助参考；
- PRD 是人类研究真源；
- Paper 是上下文参考与实验设计叙事，帮助 AI 理解 baseline、表格结构和预期结果形态；
- 可以从 Paper 读取实验设计意图（baseline、metric、表格结构、叙事逻辑），但具体的 dataset、seed、command、artifact 路径必须从 Spec 获取；
- 若 Paper 与 Spec 冲突，以 Spec 为准；
- 执行最早尚未完成的 gate；
- 运行声明的 harness 并保存 stdout/stderr；
- 更新 current state、blocker、decision、run、final summary，并在 epoch workspace 中交给 `research-insight` 更新 `Vn/wiki/*`；
- 禁止将 mock / planning 值当作已验证结果写入证据或论文结论；
- required information 缺失时停止并记录 blocker；
- 包含 `## Subagent Dispatch`，在需要专业 worker 时委派 Claude Code project-level subagent：
  - mathematical formulation or proof issue → `research-math`
  - literature / benchmark selection → `research-literature`
  - baseline reproduction → `research-reproduce`
  - method implementation → `research-coding`
  - full experiment execution → `research-experiment`
  - result analysis / anomaly / pivot → `research-analysis`
  - paper writing/update → `research-paper`
  - cross-file consistency check → `research-audit`
- 说明 `/research` controller 仍负责 state、gate 和 promotion，subagent 不得修改 PRD core claims 或绕过 Spec/Plan；
- **每轮执行后必须回答洞察问题；新项目写入当前 `Vn/wiki/*`，legacy dated plan 才写入 `insight_log.md`**：
  - 我们理解到了什么？
  - 有没有异常？
  - 有没有与 PRD 假设冲突的现象？
  - 有没有比原始 idea 更简单的解释？
  - 有没有新的研究问题出现？
  - 有没有值得微调 15 度的方向？

`research-plan` 不再是主要 insight 生成入口。它负责把这些问题放进执行 prompt；正式解释、分类和 wiki promotion 由 `research-insight` 完成。

### Validation

`validate_research.py --mode loop-prompt-ready` checks that `ai_loop_prompt.md` contains all must-say clauses. A missing clause causes a validation failure, not a warning.
