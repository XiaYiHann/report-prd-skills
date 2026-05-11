# research-execution-skills

`research-execution-skills` 是一组面向 Claude Code / Codex 的研究执行技能。它不再是通用的 `report PRD` 工具，而是把一个研究想法推进成可执行研究工作区：

```text
Research PRD   = 人类研究真源
Research Paper = 从 PRD 派生的学术论文表达
Research Spec  = 从 PRD 编译出的全局机器执行合同
Research Plan  = 从 Spec 派生的 dated 具体执行计划
Research Audit = PRD / Paper / Spec / Plan / PPT / artifacts 的漂移审计
Research PPT   = 面向 Codex + ImageGen 的 PNG/PDF 幻灯片图像工作流
```

核心原则：`RESEARCH_DIRECTION.md` 控制探索边界；`/research explore` 负责纯探索；当前 `Vn/PRD.md` 是当前 epoch 的研究真源；`Vn/SPEC.yaml` 是执行合同；`Vn/PLAN.md`、`Vn/TASK_QUEUE.yaml`、`Vn/NEXT_ACTION.md` 只从 Spec 派生；Git 记录真实工程变化；Paper / PPT 只是表达层，不能反推实验、数据集、基线、指标、seed、任务、harness 或结果。

升级后的系统名是 **Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop**：

```text
Explore 负责想
Vn 负责做
Git 负责记
Wiki 负责沉淀
Audit 负责守门
Closeout 负责进入下一轮或论文绑定
```

## Charter-bounded Epoch Research Loop

新版系统定义为 **Charter-bounded Epoch Research Loop**。

中文定义：

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

English definition:

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

线性循环被升级为：

```text
Research Direction
  -> V0 PRD
  -> V0 Spec
  -> V0 Plan
  -> V0 Task Queue
  -> Claude/Codex executes NEXT_ACTION
  -> Gate
  -> Wiki
  -> Closeout
  -> V1 PRD
  -> ...
  -> Vn closed_stable
  -> Paper Binding
```

## Research Direction / Charter

`docs/research/RESEARCH_DIRECTION.md` 是所有版本的上位约束。它记录 research seed、Research Corridor、Out-of-Scope Directions、prior work basis、desired paper shape、AI autonomy boundary 和 global stop conditions。AI 不能自动修改核心方向，不能越过走廊 pivot，也不能把 exploratory insight 写成 paper result。

## Epoch Versions: V0, V1, V2

新版默认工作区是 epoch-based：

```text
docs/research/
  RESEARCH_DIRECTION.md
  CURRENT
  INDEX.md
  agent/
    RUNBOOK.md
    CLAUDE_LOOP_PROMPT.md
    CODEX_GOAL_TEMPLATE.md
    SUBAGENT_POLICY.md
    LITERATURE_POLICY.md
  V0/
    PRD.md
    SPEC.yaml
    PLAN.md
    STATUS.yaml
    TASK_QUEUE.yaml
    NEXT_ACTION.md
    LOOP_LOG.md
    plans/
    runs/
    artifacts/
    audits/
    wiki/
    closeout.md
    PAPER_BINDING_DECISION.md
```

每个 `Vn` 是完整研究轮次，不是 PRD minor version。旧版本 `V0...Vn-1` 只能作为 context / memory / history，不再有执行权。旧版本 artifact 不能直接支持当前版本 claim，除非当前 `Vn/PRD.md` 或 `Vn/SPEC.yaml` 显式 `carry_forward`。

## Current Version Resolution

`docs/research/CURRENT` 只包含当前版本名，例如 `V0`。读取顺序固定为：

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/NEXT_ACTION.md`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.md`
7. `docs/research/{CURRENT}/SPEC.yaml`
8. `docs/research/{CURRENT}/PLAN.md`

## Claude Code Ralph-loop Usage

Claude Code 持续循环时读取 `docs/research/agent/CLAUDE_LOOP_PROMPT.md`。每轮只执行 `NEXT_ACTION.md` 中的一个原子任务；完成后更新 `LOOP_LOG.md`、`TASK_QUEUE.yaml`、`NEXT_ACTION.md`，如果产生 insight 则更新 `wiki/`。如果 blocked，写具体 blocker，不伪造 stdout/stderr、artifact 或 benchmark。

## Codex Goal Usage

Codex 使用 `docs/research/agent/CODEX_GOAL_TEMPLATE.md`：目标必须是完成当前 `NEXT_ACTION.md` 的 active task。若改代码，运行相关测试；若不能测试，写明 blocker。Codex 不修改 Research Direction，不在 closeout 前创建下一版本，不把未验证 artifact 写成 paper result。

## Task Queue and Next Action

`TASK_QUEUE.yaml` 是队列；同一时间只能有一个 `active` task，除非显式并行且 `allowed_files` 不冲突。`NEXT_ACTION.md` 是 Claude Code / ralph-loop / Codex 的单步控制文件。短规则：

> 工程问题留在当前版本；研究问题改变才开下一版本。

## Version Wiki

每个版本保留轻量 wiki，不引入 graph database：

```text
wiki/
  epoch_summary.md
  evidence_map.md
  positive_signals.md
  negative_results.md
  failed_paths.md
  baseline_landscape.md
  literature_notes.md
  open_questions.md
  next_version_seed.md
```

wiki 记录成功信号、失败路径、负结果、baseline 认知、文献 blocker 和下一版种子。

## Version Closeout

每个版本必须以 `closeout.md` 结束。关闭状态包括 `closed_success`、`closed_negative`、`closed_blocked`、`closed_falsified`、`closed_pivot_required`、`closed_stable`。`gate_blocked` 不是失败，而是合法 closeout 条件。

## When to Create Next Version

只有当前版本 `closeout.md` 完成且 status 为 `closed_*` 时，才允许创建 `Vn+1` draft。创建条件包括研究问题变化、hard gate 阻断但出现更合理 framing、核心假设被负结果反驳、baseline/metric/dataset/model 改变主 claim、exploration 结束需要进入 confirmatory/intervention/training。

不创建新版本：修 bug、补 artifact path、修测试、增加 sanity check、重跑 seed、小 baseline 补充、Spec 字段补全、Paper placeholder 修正、Plan stale 后重新生成。

## Paper Binding

Paper Binding 只能在当前版本 `status=closed_stable` 或 `paper_binding_ready` 时发生，且必须存在 `PAPER_BINDING_DECISION.md`，明确 `paper_binding_ready: true`。Allowed claim 必须绑定 experiment、run、artifact、metric、baseline、seed protocol 和 audit status。Exploratory insight 只能进入 motivation / discussion；prompt-only scaffold 不能成为实验结果。

## Subagent Policy

`docs/research/agent/SUBAGENT_POLICY.md` 定义 `literature_scout`、`repo_explorer`、`experiment_engineer`、`debugger`、`artifact_auditor`、`wiki_synthesizer`、`paper_binder`。主 agent 仍负责读取 Direction、判断 corridor、管理状态、更新 NEXT_ACTION、阻止 paper claim 越权。

## Literature Policy

`docs/research/agent/LITERATURE_POLICY.md` 要求在 project start、version start、baseline lock、unexpected strong/negative result、before paper binding 检索。修 bug、补 artifact path、跑测试、更新 wiki、执行已锁定 Plan、小工程重构不需要检索。无网络时写 literature blocker，不编造文献。

## Git Memory Layer

Git 是 research-loop 的 checkpoint system。每个版本包含：

```text
Vn/GIT_STATE.yaml
Vn/git_log.md
Vn/runs/TASK_XXX_report.md
```

Task、gate、closeout、Paper Binding 都应记录 branch、pre/post commit、diff stat、commit hash、dirty-tree 状态和 tag。推荐 tag：

```text
research/V0/closed_success
research/V0/closed_blocked
research/V1/closed_stable
research/paper_binding/V2
```

Git 安全边界：

- AI 可以：`git status`、`git diff`、`git log`、`git add` allowed files、`git commit` 当前 task、`git tag` closeout / paper binding。
- AI 不可以：`git push`、`git reset --hard`、`git clean -fd`、`git rebase`、覆盖用户修改的 checkout、rewrite history、force push、删除 task 范围外文件。

除非用户明确授权，否则所有破坏性 Git 操作都禁止。

## Research Explore Skill

`research-explore` 是纯聊天式研究探索入口：

```text
/research explore
/research explore --save
/research explore --mode idea
/research explore --mode literature
/research explore --mode baseline
/research explore --mode next-version
/research explore --mode paper-shape
/research explore --mode failure-analysis
```

它可以结合当前 research context、使用 web search、保存 explore session、提出 next action / next version / baseline / literature 建议。它不能直接修改 PRD、不能修改 `RESEARCH_DIRECTION.md`、不能创建 `Vn+1`、不能进入 Paper Binding、不能把探索结论写成稳定 claim。

Explore 保存到：

```text
docs/research/explore/sessions/
docs/research/explore/syntheses/
docs/research/explore/proposals/
```

## Audit Modernization

`research-audit` 同时是格式守门员、迁移指导器、证据审计器。概念模式：

```text
/research audit --mode format
/research audit --mode migration
/research audit --mode epoch
/research audit --mode git
/research audit --mode evidence
/research audit --mode paper-binding
/research audit --mode full
```

新增 validator：

- `format-ready`：检查 epoch_v1 必备文件、模板版本、agent docs、`AGENTS.md` / `CLAUDE.md`。
- `migration-ready`：识别 `epoch_v1`、`legacy_flat`、`mixed`、`unknown`。
- `git-ready`：检查 `GIT_STATE.yaml`、task git policy、done task commit hash、closeout/paper-binding git 记录、dirty tree。

Migration audit 可以生成 `docs/research/audits/MIGRATION_AUDIT.md` 和 `docs/research/MIGRATION_PLAN.md`，但不能默认改写研究主张，也不能把旧 insight 直接变成 paper evidence。

## Updated Full Loop

```text
Explore
  -> Research Direction
  -> CURRENT/Vn
  -> PRD
  -> SPEC
  -> PLAN
  -> TASK_QUEUE
  -> NEXT_ACTION
  -> Claude/Codex execution
  -> Git checkpoint
  -> Gate
  -> Wiki
  -> Audit
  -> Closeout
  -> Vn+1 or Paper Binding
```

总结句：

> Explore 负责想，Vn 负责做，Git 负责记，Wiki 负责沉淀，Audit 负责守门，Closeout 负责进入下一轮或论文绑定。

## Validator Modes

新增 validator mode：

- `direction-ready`
- `epoch-ready`
- `loop-ready`
- `closeout-ready`
- `paper-binding-ready`
- `format-ready`
- `migration-ready`
- `git-ready`

保留 legacy readiness mode：`prd-ready`、`paper-ready`、`spec-ready`、`plan-ready`、`ppt-ready`、`audit-ready`、`insight-ready`、`alignment-check`。

## Unified `/research` Loop

`/research` 是默认入口。新版优先解析 `RESEARCH_DIRECTION.md`、`CURRENT` 和当前 `Vn`；legacy workspace 仍保留兼容。用户完成并人工批准 Research Direction 与当前版本 PRD 后，统一控制器会检查 `docs/research/`，用文件系统事实重算当前阶段，并按 Direction / PRD / Spec / Plan / Task Queue / Next Action / Audit / Wiki 约束推进项目。

标准循环：

1. 用户填写 Research PRD，并加入 `PRD_STATUS: HUMAN_APPROVED`。
2. `/research` 检查 PRD readiness；未批准或缺少 RQ、证伪条件、benchmark、实验、dataset、baseline、metric、harness 时停止。
3. PRD ready 后，`/research` 编译或修复 `docs/research/spec/`。仅当缺口是 PRD-compatible 的执行细节时自动修；如果需要决定数据集、baseline、metric、核心 RQ 或主 claim，则写入 `docs/research/audits/YYYY-MM-DD-prd-review/` 并停止。
4. Spec ready 后，`/research` 创建或更新 `docs/research/plans/plan_queue.yaml`，选择最高优先级 pending entry，生成下一份 dated plan。
5. 执行阶段只按 Plan 和 Spec 的最早 gate 推进。当前脚本实现是 deterministic file controller：它会写状态、计划、prompt、反馈和 audit，但不会伪造 harness stdout/stderr 或实验 artifact。
6. 计划完成或阻塞后，`/research` 写 `docs/research/spec/feedback/`、追加 insight log，并生成 audit。
7. 失败会被分类为 Execution Failure、Spec Gap、PRD Ambiguity 或 Research Falsification / Insight Trigger。PRD ambiguity、核心假设失败、open pivot proposal 和未解决负结果都会阻断自动执行并请求人类审查。
8. Paper / PPT 是表达层，只能从 PRD、Spec 和已验证 artifacts 更新；不得从论文反推实验，也不得填入未验证结果。

旧的分技能仍可手动使用：`research-prd`、`research-paper`、`research-spec`、`research-plan`、`research-audit`、`research-ppt`。但自动托管研究项目时，默认先运行 `/research`。

执行 backend 目前显式保守：

```text
--executor prompt-only   # 当前已实现
--executor local-shell   # 预留，尚未执行 harness
--executor codex         # 预留
--executor hermes        # 预留
```

除 `prompt-only` 外，backend 槽位只记录意图，不代表已经能真实执行 shell、Codex goal 或 Hermes 任务。

初始化产物不是空 `TODO` 骨架。`research-init` 会生成 `RESEARCH_DIRECTION.md`、`CURRENT`、`V0/` epoch、agent runbook、`AGENTS.md`、`CLAUDE.md`，同时保留 legacy 的中文顶级 Research PRD 模板：LaTeX 是真源，使用 `ctex`、TikZ、`booktabs`、`tabularx` 组织图表；Markdown 是伴随审阅稿。它也会生成 planned top-conference paper 模板和 Spec 执行合同模板。若本机有 `latexmk` 或 `xelatex`，脚本会真实渲染 PDF；否则写入中文 `render_blocker.md`，不会伪造 PDF。

## 安装与迁移

一行在线安装（默认安装 Claude Code skills，并在当前项目安装 Claude Code project-level subagents）：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh | bash
```

默认写入：

```text
~/.claude/skills/research
~/.claude/skills/research-explore
~/.claude/skills/research-init
~/.claude/skills/research-prd
~/.claude/skills/research-paper
~/.claude/skills/research-spec
~/.claude/skills/research-plan
~/.claude/skills/research-audit
~/.claude/skills/research-ppt

./.claude/agents/research-math.md
./.claude/agents/research-literature.md
./.claude/agents/research-reproduce.md
./.claude/agents/research-coding.md
./.claude/agents/research-experiment.md
./.claude/agents/research-analysis.md
./.claude/agents/research-paper.md
./.claude/agents/research-ppt.md
./.claude/agents/research-audit.md
```

从本地 checkout 安装：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" bash install.sh
```

安装器不会默认创建 `docs/research/`，避免污染当前项目。如需同时创建基础目录：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh \
  | bash -s -- --init-workspace
```

常用选项：

```bash
./install.sh --init-workspace   # 同时创建 docs/research/ epoch 工作区
./install.sh --no-agents        # 只安装 skills
./install.sh --user-agents      # subagents 安装到 ~/.claude/agents
./install.sh --project-agents   # subagents 安装到 ./.claude/agents，默认
./install.sh --skills-only      # 只安装 skills
./install.sh --agents-only      # 只安装 subagents
./install.sh --force            # 覆盖已有目标文件
./install.sh --dry-run          # 只打印计划，不写文件
```

自定义目标目录：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" \
RESEARCH_EXECUTION_SKILLS_TARGET_DIR=/path/to/.claude/skills \
RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR=/path/to/project/.claude/agents \
bash install.sh
```

subagent 模板源位于：

```text
agents/claude-code/*.md
```

默认复制到当前项目的 Claude Code 标准 subagent 目录：

```text
.claude/agents/
```

第一版安装 9 个 Claude Code project-level subagents：`research-math`、`research-literature`、`research-reproduce`、`research-coding`、`research-experiment`、`research-analysis`、`research-paper`、`research-ppt`、`research-audit`。这些文件是 Claude Code 原生的 Markdown + YAML frontmatter 格式；不要把自定义 registry 当成主 subagent 定义格式。

一键安装完成后，目标目录里应主要看到：

```text
research/            # unified autonomous controller
research-explore/    # pure exploration, literature/baseline/next-version discussion
research-init/
research-prd/
research-paper/
research-spec/
research-plan/
research-audit/
research-ppt/
```

旧的 `report-*` skill 不再默认安装。安装器默认遵守已有文件：目标已存在时跳过；传 `--force` 才覆盖。

## 技能列表

| Skill | 用途 |
|---|---|
| [`research`](skills/research/SKILL.md) | 默认统一入口：检查 `docs/research/`，维护 state/queue，推进 PRD、Spec、Plan、执行提示、Audit、Insight、Paper/PPT 边界。 |
| [`research-explore`](skills/research-explore/SKILL.md) | 纯探索入口：讨论 idea、文献、baseline、novelty、failure analysis、paper shape、next-version framing；可保存 EXP session，但不执行。 |
| [`research-init`](skills/research-init/SKILL.md) | 初始化 `docs/research/`，创建中文 LaTeX 真源 Research PRD、paper、spec、plans、audits、ppt scaffold。 |
| [`research-prd`](skills/research-prd/SKILL.md) | 维护专业 Research PRD，面向能够执行项目但未必熟悉完整背景的硕士生，默认图文并茂。 |
| [`research-paper`](skills/research-paper/SKILL.md) | 从 PRD 生成和打磨 planned NeurIPS / ICLR / AAAI 风格论文，并强制实验结果 placeholder 绑定。 |
| [`research-spec`](skills/research-spec/SKILL.md) | 把 PRD 编译成全局执行合同：数据集、基线、复现目标、实验、模型、指标、seed、task graph、harness、evidence contract、anti-mock 规则。 |
| [`research-plan`](skills/research-plan/SKILL.md) | 从 Spec 生成 dated 具体执行计划：`docs/research/plans/YYYY-MM-DD-purpose/`。 |
| [`research-audit`](skills/research-audit/SKILL.md) | 审计 PRD、Paper、Spec、Plans、PPT、artifacts 之间的一致性与漂移。 |
| [`research-ppt`](skills/research-ppt/SKILL.md) | 生成 slide-image deck spec、逐页 ImageGen prompt、PNG 页面输出计划和 PDF 导出计划；不生成 `.pptx`。 |

不要新增独立的 `research-evidence`、`research-writing` 或 `research-goal`。证据由 Spec / Plan / Audit 字段承担；写作优化属于 `research-paper`；长期执行 prompt 属于 `research-plan`。

## Legacy 标准工作区

以下 legacy 结构仍可被旧命令读取；新版默认入口是上文的 `RESEARCH_DIRECTION.md` + `CURRENT` + `Vn/` epoch。

```text
docs/research/
  state.yaml

  prd/
    research_prd.tex
    research_prd.md
    research_prd.pdf
    render_blocker.md  # 仅在缺少 LaTeX 引擎或真实编译失败时出现

  paper/
    planned_paper.tex
    planned_paper.md
    planned_paper.pdf
    placeholder_map.yaml
    paper_gap_report.md

  spec/
    README.md
    global_spec.yaml
    shared/
      dataset_manifest.yaml
      metric_manifest.yaml
      model_manifest.yaml
      environment_spec.yaml
      seed_protocol.yaml
      artifact_schema.yaml
      anti_mock_policy.yaml
      evidence_contract.yaml
      insight_policy.yaml
    insights/
      insight_manifest.yaml
      insight_policy.yaml
      anomaly_schema.yaml
      pivot_proposal_schema.yaml
      diagnostic_experiment_policy.yaml
    reproduction/
      benchmark_candidate_matrix.yaml
      reproduction_manifest.yaml
      reproduction_task_graph.yaml
      reproduction_harness.yaml
      reproduction_gap_report.md
    implementation/
      module_contracts.yaml
      implementation_task_graph.yaml
      implementation_harness.yaml
    experiments/
      experiment_manifest.yaml
      experiment_task_graph.yaml
      experiment_harness.yaml
    paper/
      placeholder_map.yaml
      result_binding.yaml
    feedback/
      README.md

  plans/
    plan_queue.yaml
    YYYY-MM-DD-purpose/
      plan.md
      plan.yaml
      ai_loop_prompt.md
      current_state.md
      blocker_log.md
      decision_log.md
      run_log.md
      final_summary.md

  ppt/
    main_deck/
      deck_spec.yaml
      slide_manifest.yaml
      slide_prompts/
        01_title.md
        02_motivation.md
        ...
      slide_notes.md
      deck_gap_report.md
      render_plan.md
      pages/
        01_title.png
        02_motivation.png
        ...
      exports/
        main_deck.pdf

  audits/
    YYYY-MM-DD-audit/
      audit_report.md
      alignment_matrix.yaml
      drift_findings.yaml
      repair_plan.md

  insights/
    insight_log.md
    anomaly_reports/
    negative_results/
    pivot_proposals/
    diagnostic_experiment_proposals/
```

## 实际工作流案例

这套系统的核心不是线性执行，而是**假设驱动的研究循环**。以下是三种典型操作模式。

### 模式 A：控制器托管（适合 reproduction / implementation）

```bash
# 09:00 你启动
research-plan --date 2026-05-10 --track reproduction --purpose reproduce-b01

# 09:05 /research 生成或刷新下一步执行 prompt
# 你去做别的（读 paper、开会、写代码）

# 17:00 你回来检查
cat docs/research/plans/2026-05-10-reproduce-b01/final_summary.md
# → "全部 gate 通过，baseline 复现成功"
# → 无 Mismatch，无 Surprise
# → Action: continue original plan

# 你：确认无异常，运行 research-audit
```

**你的投入：5 分钟启动 + 5 分钟检查。**

**接入真实 executor 后的放手条件**：
- 所有命令/路径/seed 已在 spec 中完整定义
- track 是 reproduction / implementation / experiment
- 没有 open pivot proposal
- insight_log.md 的 Action = continue original plan

---

### 模式 B：诊断模式（适合 diagnostic experiment / insight-feedback）

```bash
# 09:00 你启动
cat docs/research/plans/2026-05-10-diagnose-m1/insight_log.md
# → "Observation: M1 的 attention weight 在 90% samples 上接近 uniform"

# 11:00 你：读到这个，意识到可能是关键
# 你：手动添加 follow-up experiment 到 spec，重新运行 plan

# 15:00 你：确认这是真实 insight，不是 bug
# 你：运行 research-audit
# 你：阅读 repair_plan.md 的 insight-opportunity 部分
# 你：决定是否写 pivot proposal
```

**你的投入：持续参与，但 AI 帮你做所有执行和记录。**

**介入信号**：
- insight_log.md 出现 Mismatch / Surprise
- 任何一轮执行出现了未预期的异常
- validate_research --mode insight-ready 出现警告

---

### 模式 C：Pivot 决策模式（必须人类主导）

```
Day 1  AI：提交 pivot_proposal 到 insights/pivot_proposals/
       系统状态：insight_loop.status = "pivot_proposed"
       AI 停止所有执行，等待人类决策

Day 1-3 你：深度阅读
       - 原始 PRD v1 的 Chapter 6, 8, 10
       - 所有 anomaly_reports
       - 对比 pivot proposal 中的 "Required PRD Changes"

Day 3  你：做决策
       [ ] Approve  → 进入 PRD v2，AI 辅助生成文本
       [ ] Reject   → 写回复，要求补充实验
       [ ] Revise   → 修改 pivot 角度，再 submit

Day 4  你：如果 Approve，运行 research-spec 重新编译
       AI：自动级联更新 spec → plan → audit
```

**你的投入：数小时深度思考。这是科研中不可替代的部分。**

**强制停止信号**：
- insight_log.md 的 Action = propose pivot
- blocker_log.md 出现研究类 blocker（假设矛盾）
- AI 试图修改核心 RQ / Claim / 论文故事线

---

### 三层自动化边界

| 层级 | 内容 | AI 权限 | 人类角色 |
|------|------|---------|---------|
| **执行层** | 代码运行、环境修复、实验执行、日志更新 | 当前仅 prompt-only；接入 backend 后才可自动迭代 | 定期查看 summary |
| **洞察层** | Insight 记录、异常分类、Pivot 提案生成 | ✅ 自动准备材料 | 做决策（Approve/Reject/Revise） |
| **战略层** | 核心 RQ、问题表述、主 Claim、论文故事线 | ❌ 只辅助文本 | 完全控制，AI 不得修改 |

> **执行交给 AI，洞察留给自己。让 AI 做你最快的实验员和诚实的记录员，但让最终的方向判断永远属于人类。**

## Research PRD

`research-prd` 维护人类研究真源。PRD 不是短论文，也不是占位符列表，而是专业、详细、教学友好、可执行的研究设计文档。标题采用中文 + 英文 canonical label，必须包含：

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

PRD 要解释足够背景，使有能力但非该方向专家的硕士生可以执行；同时必须定义具体任务、benchmark、实验、harness、验收条件和证据边界。

模板质量要求：

- 每章包含章节目标、必须填写的信息、常见错误、证据边界、验收标准。
- 使用结构化中文占位符 `【待填写：...】`，不使用裸 `TODO`。
- 默认包含 TikZ 图骨架：研究问题到证据链、方法模块图、实验/复现流程图、Spec -> Plan -> Audit 执行闭环。
- 关键章节包含 RQ/Hypothesis 表、Benchmark Candidate Matrix、Experiment Matrix、Task Graph Table、Evidence Ledger、Risk Matrix。

## Research Paper

`research-paper` 从 PRD 派生 planned top-conference-style manuscript。它可以对已经在 PRD 中设计好的对象使用强表达：

`research-paper` 的最终产物必须是一篇完整顶会风格 manuscript draft，而不是填空模板。正文应当像 NeurIPS / ICLR / AAAI 论文一样完整叙述 Abstract、Introduction、Related Work、Problem Formulation、Method、Experiments、Results / Planned Result Bindings、Limitations 和 Conclusion。若真实实验尚未完成，只能生成 placeholder-complete manuscript：表格结构、caption、结果段落和解释逻辑可以完整，但所有未验证结果值必须保留为 Spec 绑定 typed placeholder，并在 `paper_gap_report.md` 记录投稿前必须替换的证据。不得填入 plausible mock numeric values。

- `We propose ...`
- `We formulate ...`
- `We design ...`
- `We evaluate ...`
- `Experiment E1 tests whether ...`
- `Table 1 reports ...`

但在证据验证前禁止写：

- `Experiments show that ...`
- `Our method outperforms ...`
- `We achieve state-of-the-art ...`
- `The results demonstrate ...`
- 任何没有 validated evidence 支撑的数字或比较。

未观测结果必须写成实验绑定 placeholder：

```text
{{E01.OURS.primary_metric}}
{{E01.B01.primary_metric}}
{{E02.ablation_delta}}
{{E03.latency_ms}}
```

每个 placeholder 必须注册在 `docs/research/paper/placeholder_map.yaml`，并绑定到 Spec 中的实验。

## Research Spec

`research-spec` 把 PRD 编译成全局机器执行合同：

```text
RQ
-> Hypothesis
-> Claim
-> Experiment
-> Dataset / Model / Baseline / Metric / Seed
-> Task
-> Harness
-> Evidence
-> Paper placeholder
```

`research-spec` 只能从 PRD 编译，不能从 Paper 推断实验。PRD 缺失的执行细节必须进入 gap report 或 blocker，不能由 agent 发明。

Spec 采用“英文键、中文值”策略：YAML key、ID、schema 字段保持英文，`title`、`description`、`purpose`、`blockers`、`acceptance_criteria`、`notes`、gap report 和 policy 说明使用中文。

初始化生成的 Spec 不是空 YAML。它包含教学型合同模板：

- `global_spec.yaml` 提供 RQ -> Hypothesis -> Claim -> Experiment -> Evidence -> Paper placeholder 的链路模板。
- `reproduction/reproduction_manifest.yaml` 提供 `reproduction_target_template` 和三类复现模式。
- `experiments/experiment_manifest.yaml` 提供 `experiment_template`，覆盖 support / falsification / mock policy。
- `experiments/experiment_harness.yaml` 提供 `harness_template`，要求 command 或 blocker、artifact、pass criteria、claim 支撑边界和 independent rerun。
- `paper/result_binding.yaml` 提供 `result_binding_template`。

这些 `*_template` 条目只用于指导填写，不代表已经声明了可执行实验。

复现不是单独技能，而是 Spec 和 Plan 内部的 track。复现模式必须显式声明：

- `official_code_reuse`
- `official_code_adaptation`
- `paper_based_reimplementation`

## Research Plan

`research-plan` 从 Spec 生成 dated bounded execution plan。`plan.yaml` 保持英文 key 和稳定 ID，但 `plan.md`、`ai_loop_prompt.md`、状态日志、阻塞日志、决策日志、运行日志和最终总结全部使用中文。它支持：

```text
research-plan --track reproduction
research-plan --track implementation
research-plan --track experiment
research-plan --track paper-update
research-plan --gate G_ID
research-plan --target codex
research-plan --target ralph-loop
```

每个 plan 必须记录 PRD、Paper、Spec 和 git commit 的 source hash。若 Spec 在 plan 创建后改变，`plan-ready` 必须失败，直到显式生成或更新 plan。

`ai_loop_prompt.md` 会包含 Claude Code `Subagent Dispatch` 段落。需要数学、文献、复现、编码、实验、分析、论文、PPT 或审计工作时，主会话应委派 `.claude/agents/research-*.md` 中的标准 Claude Code subagent；`/research` controller 仍负责 state、gate、promotion 和 audit 阻断。

## Research Audit

`research-audit` 检查：

- PRD -> Paper alignment
- PRD -> Spec alignment
- Spec -> Plan alignment
- Paper -> Spec alignment
- Plan -> Artifact alignment
- PRD / Paper / Spec -> PPT alignment

`repair_plan.md` 必须区分：

- must fix before execution
- can fix later
- recommended next `research-plan` target

## Research PPT

`research-ppt` 生成面向 Codex + ImageGen 的 slide-image deck spec：

- 每页幻灯片生成一个 PNG。
- 最终从 PNG 页面导出 PDF。
- 不创建传统 `.pptx`。

默认 `standard` 模式是 10 到 12 页：

1. Title
2. Background and motivation
3. Problem gap and research questions
4. Problem formulation
5. Key insight
6. Method overview
7. Method details / system design
8. Benchmark and reproduction plan
9. Experiment design
10. Expected contributions
11. Risks / challenges
12. Summary and next steps

## 校验器

统一校验入口：

```bash
python3 skills/research-spec/scripts/validate_research.py --repo . --mode prd-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode paper-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode spec-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode plan-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode ppt-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode audit-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode insight-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode alignment-check
python3 skills/research-spec/scripts/validate_research.py --repo . --mode format-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode migration-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode git-ready
```

readiness mode 必须硬失败。scaffold 可以存在 blocker，但不能被当成 execution-ready。

## 开发验证

运行：

```bash
python3 -m pytest tests -q
```

当前 GitHub 默认安装源是 `XiaYiHann/research-loop`；旧环境变量 `REPORT_PRD_SKILLS_*` 仅为兼容历史安装脚本保留。

## License

Apache 2.0
