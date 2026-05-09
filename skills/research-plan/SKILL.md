---
name: research-plan
description: "Use when a dated research execution run needs a bounded plan, AI loop prompt, source hashes, gates, or harness scope from Research Spec."
---

# Research Plan

## Overview

Create dated concrete execution plans under `docs/research/plans/YYYY-MM-DD-purpose/`. A plan is a bounded run contract for Codex or Claude Code. Its **executable contracts** are derived from `docs/research/spec/`, but its **scope and scheduling** should reference the formulation and experimental design narrative in `docs/research/paper/`. The paper provides context on what baselines to compare, what tables to fill, and what story the evidence must support; the spec provides the exact commands, harnesses, and gates to execute. When the two conflict, spec wins.

Plan prose, AI loop prompts, and run logs must be Chinese. `plan.yaml` keeps English keys and stable IDs, but explanatory values such as `purpose`, `forbidden_actions`, and `completion_condition` should be Chinese.

## Supported Tracks

- `reproduction`
- `implementation`
- `experiment`
- `paper-update`

Supported selectors:

- `--gate G_ID`
- `--target codex`
- `--target ralph-loop`

## Outputs

- `plan.md`
- `plan.yaml`
- `ai_loop_prompt.md`
- `current_state.md`
- `blocker_log.md`
- `decision_log.md`
- `run_log.md`
- `final_summary.md`

## Command

```bash
python3 ~/.agents/skills/research-plan/scripts/generate_research_plan.py \
  --repo /absolute/path/to/repo \
  --date 2026-05-09 \
  --purpose reproduce-b01 \
  --track reproduction \
  --target codex
```

Validate:

```bash
python3 ~/.agents/skills/research-spec/scripts/validate_research.py \
  --repo /absolute/path/to/repo \
  --mode plan-ready
```

## AI Loop Contract

`ai_loop_prompt.md` must say:

- 可执行真源是 `docs/research/spec/`；执行时以 Spec 为准，Paper 为辅助参考；
- PRD 是人类研究真源；
- Paper 是上下文参考与实验设计叙事，帮助 AI 理解 baseline、表格结构和预期结果形态；
- 可以从 Paper 读取实验设计意图（baseline、metric、表格结构、叙事逻辑），但具体的 dataset、seed、command、artifact 路径必须从 Spec 获取；
- 若 Paper 与 Spec 冲突，以 Spec 为准；
- 执行最早尚未完成的 gate；
- 运行声明的 harness 并保存 stdout/stderr；
- 更新 current state、blocker、decision、run 和 final summary logs；
- 禁止将 mock / planning 值当作已验证结果写入证据或论文结论；
- required information 缺失时停止并记录 blocker。
