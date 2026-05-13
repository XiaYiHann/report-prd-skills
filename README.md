# research-execution-skills

`research-execution-skills` 是一组面向 Codex / Claude Code 的研究执行技能。它不是独立服务端系统，也不提供独立常驻 backend；Codex / Claude Code 是实际执行 `NEXT_ACTION.md` 的 agent executor，技能族负责提供文件系统协议、状态提交入口、证据记录格式和审计门禁。

目标不是让 prompt-only 文档替代实验，而是让 agent executor 在 Git-backed epoch 协议下执行任务，并通过 `update_state.py`、run report、artifact hash 和 audit hard gate 留下可验证证据。

整个流程分为三个阶段：

```text
阶段 0：初始化       → research-init 创建 docs/research/ epoch 工作区
阶段 1：PRD 讨论生成  → AI 与用户逐章讨论，AI 填写 16 章 PRD（含 Gate 调度表），用户审批
阶段 2：自动执行      → AI 按 Gate 顺序自动执行所有 task，遇阻断才停，直到 closed_* 或 Paper Binding
```

核心原则：`RESEARCH_DIRECTION.md` 控制探索边界；`/research explore` 负责纯探索；当前 `Vn/PRD.md` 是当前 epoch 的研究真源（由 AI 在用户指导下生成）；`Vn/SPEC.yaml` 是执行合同；`Vn/PLAN.md`、`Vn/TASK_QUEUE.yaml`、`Vn/NEXT_ACTION.md` 只从 Spec 派生；`update_state.py` 在每次任务完成后原子更新 6 个状态文件；Git 记录真实工程变化；Paper 只是表达层，不能反推实验、数据集、基线、指标、seed、任务、harness 或结果。

系统名是 **Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop**：

```text
用户 + AI 讨论方向 → AI 填写 PRD → 用户审批 → AI 自动执行所有 Gate → 遇阻断停
Explore 负责想
Vn 负责做
Git 负责记
Insight 负责解释
Wiki 负责沉淀
Audit 负责守门
Closeout 负责进入下一轮或论文绑定
```

## 安装

一行在线安装（默认安装 Claude Code skills + 项目 subagents）：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh | bash
```

从本地 checkout 安装：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" bash install.sh
```

常用选项：

```bash
./install.sh --init-workspace   # 同时创建 docs/research/ epoch 工作区
./install.sh --no-agents        # 只安装 skills
./install.sh --force            # 覆盖已有目标文件
./install.sh --dry-run          # 只打印计划，不写文件
```

安装后文件布局：

```text
~/.claude/skills/
  research/            # unified autonomous controller
  research-explore/    # pure exploration
  research-insight/    # evidence-grounded interpretation
  research-init/       # workspace initialization
  research-prd/        # PRD maintenance
  research-paper/      # paper generation
  research-spec/       # spec compilation
  research-plan/       # plan generation
  research-audit/      # cross-file consistency audit

.claude/agents/
  research-math.md     research-literature.md  research-reproduce.md
  research-coding.md   research-experiment.md  research-analysis.md
  research-paper.md    research-audit.md
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
  V0/
    PRD.md
    SPEC.yaml
    PLAN.md
    STATUS.yaml
    TASK_QUEUE.yaml
    NEXT_ACTION.md
    LOOP_LOG.md
    GIT_STATE.yaml
    plans/
    runs/
      TASK_XXX_report.yaml    # 机器可读 YAML 运行报告
      TASK_XXX_report.md      # 人类可读 Markdown 运行报告
    artifacts/
    audits/
    wiki/
    closeout.md
    PAPER_BINDING_DECISION.md

.claude/
  agents/
    research-math.md          # Claude Code project-level subagents
    research-literature.md
    research-reproduce.md
    research-coding.md
    research-experiment.md
    research-analysis.md
    research-paper.md
    research-audit.md
```

关键执行工具：

| 文件 | 作用 |
|------|------|
| `skills/research/scripts/update_state.py` | 原子状态更新器：每次任务完成后一键更新 TASK_QUEUE、LOOP_LOG、GIT_STATE、STATUS、run report、NEXT_ACTION |
| `skills/research/scripts/research_loop.py` | 确定性状态机控制器：检测 PRD readiness、生成 Spec/Plan/TASK_QUEUE、推进 Gate |
| `skills/research-init/_shared/scripts/research_workspace.py` | 共享库：所有模板、NEXT_ACTION 生成、run report schema、Gate 检测 |

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

## 三阶段工作流

### 阶段 0：初始化

若 `docs/research/` 不存在，`research-init` 创建 epoch 工作区：

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo . --title "项目标题" --purpose "研究目标"
```

产物包括 `RESEARCH_DIRECTION.md`、`CURRENT`、`V0/` epoch、`CLAUDE.md`、`AGENTS.md`。

### 阶段 1：PRD 讨论与生成

初始化后 `NEXT_ACTION.md` 的 Active Task 为 TASK_001：完善 PRD。AI 与用户逐章讨论 16 章 PRD，AI 填写所有内容：

- 第 2 章背景教程、第 3 章相关工作地图：AI 搜索文献帮助理清 landscape
- 第 4 章基准与复现计划：AI 帮助选 concrete baseline、dataset、metric
- 第 6 章研究问题与假设：AI 帮用户把模糊 idea 变成可证伪的 RQ
- 第 10 章实验设计：AI 帮助设计 experiment matrix
- **第 11.2 章 Gate 调度表（关键）**：AI 帮用户把研究拆成有序 Gate，每个 Gate 定义 task 清单和可验证的 pass_condition
- 第 12 章 Harness：AI 帮用户定义每个 task 的 harness 命令和验收标准

用户审批后，AI 在 PRD.md 末尾添加 `PRD_STATUS: HUMAN_APPROVED`，运行 `update_state.py` 标记 TASK_001 done，进入阶段 2。

### 阶段 2：自动执行（Continuous Loop）

PRD 锁定后，控制器自动推进：

```bash
# Bootstrap：重复运行直到生成 SPEC/PLAN/TASK_QUEUE/NEXT_ACTION
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once
```

当 NEXT_ACTION.md 中出现具体执行任务后，进入持续循环：

```
while STATUS.yaml.status not in (closed_*, gate_blocked):
    1. 读取 NEXT_ACTION.md（含完整 task 执行细节）
    2. 执行 task（写代码/跑实验/复现 baseline）
    3. 完成后运行 update_state.py 原子更新 6 个状态文件
    4. NEXT_ACTION.md 已自动更新为下一个任务
    5. 继续循环，不询问用户
```

**停止条件**：`gate_blocked`（报告 blocker 等待人工决策）、`closed_*`（报告 closeout 摘要）、实验证据反驳 PRD 核心假设（写 negative_result 请求 review）。

若要在 Claude Code 中用 ralph-loop 驱动自动执行：

```bash
/ralph-loop "/research" --max-iterations 50 --completion-promise "RESEARCH_COMPLETE"
```

## Codex Goal Usage（遗留）

Codex 使用 `docs/research/agent/CODEX_GOAL_TEMPLATE.md`：目标必须是完成当前 `NEXT_ACTION.md` 的 active task。若改代码，运行相关测试；若不能测试，写明 blocker。Codex 不修改 Research Direction，不在 closeout 前创建下一版本，不把未验证 artifact 写成 paper result。

## Task Queue and Next Action

`TASK_QUEUE.yaml` 是 Gate-aware 队列；同一时间只能有一个 `active` Task，除非显式并行且 `allowed_files` 不冲突。`NEXT_ACTION.md` 是 Claude Code / ralph-loop / Codex 的单步控制文件。短规则：

> 工程问题留在当前版本；研究问题改变才开下一版本。

Terminology:

- Gate: 研究阶段门禁，必须有可验证的 pass/block/falsification 条件。
- Task: Gate 内的最小执行单元。
- Harness: 验证 Task 的命令、输入、输出、artifact 和判定器。
- Audit: Gate 或关键 Task 后的对抗性审查，P0/P1 失败会阻断推进。
- Insight: 从运行、阻断、失败、异常或负结果中沉淀的证据化知识。

Gate-aware 状态枚举：

- Task status: `pending`、`active`、`completed`、`blocked`、`failed_execution`、`failed_harness`、`skipped`。
- Gate status: `pending`、`active`、`audit_required`、`audit_failed`、`passed`、`blocked`、`falsified`。

Failure triage 是硬协议：`failed_execution` 和 `failed_harness` 只能进入修复、阻断或审计路径，不能被解释为研究假设失败。只有 harness 成功运行、输出有效、artifact hash 已记录，并经过 Audit 排除代码、数据、指标和 harness 缺陷后，才允许从 `research_falsification_candidate` 升级为 confirmed falsification。

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

Paper Binding 只能在当前版本 `status=closed_stable` 或 `paper_binding_ready` 时发生，且必须存在 `PAPER_BINDING_DECISION.md`，明确 `paper_binding_ready: true`。Allowed claim 必须绑定 experiment、run、artifact、metric、baseline、seed protocol、audit status、real data check、real model/code check 和 non-smoke full-run check。Exploratory insight 只能进入 motivation / discussion；prompt-only scaffold 不能成为实验结果。

## Subagent Policy

Claude Code project-level subagents 安装在 `.claude/agents/`，执行 YAML frontmatter 的 Markdown 文件：

| Subagent | 职责 |
|----------|------|
| `research-math` | 数学公式、符号检查 |
| `research-literature` | 文献搜索、baseline 分析 |
| `research-reproduce` | 复现 baseline |
| `research-coding` | 实现方法代码 |
| `research-experiment` | 运行声明实验 |
| `research-analysis` | 结果分析、异常检测、pivot 提案 |
| `research-paper` | 论文 placeholder 安全更新 |
| `research-audit` | 跨文件一致性检查 |

主 agent（`/research` controller）始终负责：状态推进、gate 判定、NEXT_ACTION 执行、wiki/closeout。

## Search and Evidence Acquisition Policy

Search is a hard evidence-acquisition step, not a writing aid. 新 epoch 默认先执行 `G0_SEARCH_LOCK`，再执行 `G1_REPRODUCTION_LOCK`；proposed-method experiment 不能在这两个 early gates resolved 之前成为 active task，除非存在明确 human waiver 和 audit 记录。

Search 必须覆盖 literature、official code、third-party implementations、datasets、model checkpoints、known issues / forks / reproduction notes，以及 current local repository state。要求在 project start、version start、baseline lock、reproduction task、dataset/model/metric selection、unexpected strong/negative result、pivot proposal、before paper binding 检索。修 bug、补 artifact path、跑测试、更新 wiki、执行已锁定 Plan、小工程重构不需要检索。无网络时写 search blocker，不编造文献、代码仓库、数据集、指标或模型能力。

Reproduction failure 必须分类，不能静默忽略，也不能当作 hypothesis falsification。`blocked_missing_code`、`blocked_missing_data`、`blocked_stale_dependency`、`blocked_ambiguous_algorithm`、`failed_metric_mismatch`、`failed_unexplained` 都需要进入 `REPRODUCTION_INDEX.yaml` 和 audit；只有 valid harness output 加 adversarial audit 才能支撑研究解释。

`docs/research/Vn/reproduction/` 是 reproduction metadata 真源；`reproduction/Vn/` 是可执行 reproduction workspace，只有具体复现任务开始时才创建。旧 epoch 的 reproduction 结果不能自动支撑当前 claim；必须通过 `SPEC.yaml` 的 `carry_forward` / `reproduction_contract` 显式继承，并满足同一研究问题、dataset/metric 兼容、artifact hash 和 audit passed。

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

## Research Insight Skill

`research-insight` 是显式的解释与沉淀入口。它不执行实验、不改 PRD、不做 Paper Binding；它只把已经存在的 run、artifact、blocker、negative result、failed path 或已保存 explore session 转成当前 epoch 的 evidence-grounded wiki 记录。

当前主路径是：

```text
TASK_XXX_report / LOOP_LOG / runs / artifacts / explore session
  -> research-insight
  -> Vn/wiki/evidence_map.md
  -> Vn/wiki/positive_signals.md
  -> Vn/wiki/negative_results.md
  -> Vn/wiki/failed_paths.md
  -> Vn/wiki/open_questions.md
  -> Vn/wiki/next_version_seed.md
```

`docs/research/insights/insight_log.md` 进入逐步退役状态：它仍作为 legacy workspace 的兼容读写目标和 migration source，但在存在 `CURRENT` 与 `Vn/wiki/` 时不再是默认 insight 真源。旧 insight 只能作为候选材料，不能直接支撑当前版本 claim，除非当前 `Vn/PRD.md` 或 `Vn/SPEC.yaml` 显式 `carry_forward`。

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

Audit 会显式检查 `RESEARCH_DIRECTION.md` 完整性：必备章节、Direction Status 字段、human-approved/frozen 状态、Research Corridor、Out-of-Scope、Autonomy Boundary 和 Global Stop Conditions。缺口会写入 `alignment_matrix.yaml` 的 `direction_completeness`、`drift_findings.yaml`、`audit_report.md` 和 `repair_plan.md`。

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
  -> Insight interpretation
  -> Wiki
  -> Audit
  -> Closeout
  -> Vn+1 or Paper Binding
```

总结句：

> Explore 负责想，Vn 负责做，Git 负责记，Insight 负责解释，Wiki 负责沉淀，Audit 负责守门，Closeout 负责进入下一轮或论文绑定。

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

保留 legacy readiness mode：`prd-ready`、`paper-ready`、`spec-ready`、`plan-ready`、`audit-ready`、`insight-ready`、`alignment-check`。其中 `insight-ready` 只服务旧 `docs/research/insights/` 兼容路径；新项目默认用 `research-insight` 更新当前 `Vn/wiki/*`。

## Unified `/research` Loop

`/research` 是默认入口。新版优先解析 `RESEARCH_DIRECTION.md`、`CURRENT` 和当前 `Vn`；legacy workspace 仍保留兼容。

### 三阶段自动化流程

**阶段 0：初始化。** 若 `docs/research/` 不存在，`research-init` 创建完整 epoch 工作区。

**阶段 1：AI 生成 PRD。** 用户无需手动填写 PRD。AI 与用户逐章讨论 16 章内容，AI 负责填写所有章节（包括 Gate 调度表和 Harness 表），用户只需审批。用户确认后 AI 添加 `PRD_STATUS: HUMAN_APPROVED`。

**阶段 2：自动执行。** PRD 锁定后，Bootstrap 控制器自动生成 Spec → Plan → TASK_QUEUE → NEXT_ACTION。之后进入持续循环：每轮执行 NEXT_ACTION.md 中的一个原子任务，完成后运行 `update_state.py` 原子更新 6 个状态文件，NEXT_ACTION.md 自动更新为下一个任务。循环不询问用户，直到：
- `STATUS.yaml.status` 为 `closed_*` 或 `paper_binding_ready` → 研究完成
- `STATUS.yaml.status` 为 `gate_blocked` → 报告 blocker，等待人工决策
- 实验证据反驳 PRD 核心假设 → 写 negative_result，请求人工 review

### 控制器命令

```bash
# Bootstrap 状态机（生成 Spec/Plan/TASK_QUEUE/NEXT_ACTION）
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once

# 原子状态更新（每次任务完成后执行）
python3 ~/.claude/skills/research/scripts/update_state.py \
  --repo . --task-id TASK_002 --status done --commit-hash abc123 --gate-id G01

# 标记阻塞
python3 ~/.claude/skills/research/scripts/update_state.py \
  --repo . --task-id TASK_003 --status blocked --blocker-reason "具体原因"
```

### Ralph-Loop 自动循环

```bash
# 启动自动执行（50 轮上限）
/ralph-loop "/research" --max-iterations 50 --completion-promise "RESEARCH_COMPLETE"

# 取消
/cancel-ralph
```

### 执行 Backend / Agent Executor

```text
默认路径：Codex / Claude Code agent executor 读取 `Vn/NEXT_ACTION.md` 并提交结构化证据。
不提供独立常驻 backend；`research_loop.py` 默认只报告 epoch contract，不伪装成 shell runner。

--legacy-controller      # 显式启用 legacy deterministic controller
--executor prompt-only   # 仅 legacy controller 的兼容槽位
```

prompt-only scaffold 不能作为实验结果或 paper binding 证据。

旧的分技能仍可手动使用：`research-prd`、`research-paper`、`research-spec`、`research-plan`、`research-audit`。但自动托管研究项目时，默认先运行 `/research`。

## 技能列表

| Skill | 用途 |
|---|---|
| [`research`](skills/research/SKILL.md) | 默认统一入口：检查 `docs/research/`，维护 state/queue，推进 PRD、Spec、Plan、执行提示、Audit、Insight、Paper 边界。 |
| [`research-explore`](skills/research-explore/SKILL.md) | 纯探索入口：讨论 idea、文献、baseline、novelty、failure analysis、paper shape、next-version framing；可保存 EXP session，但不执行。 |
| [`research-insight`](skills/research-insight/SKILL.md) | 显式解释入口：把 run、artifact、blocker、负结果、失败路径或 explore session 沉淀到当前 `Vn/wiki/*`，并把 legacy `insight_log.md` 逐步退役。 |
| [`research-init`](skills/research-init/SKILL.md) | 初始化 `docs/research/`，创建中文 LaTeX 真源 Research PRD、paper、spec、plans、audits 和 epoch scaffold。 |
| [`research-prd`](skills/research-prd/SKILL.md) | 维护专业 Research PRD，面向能够执行项目但未必熟悉完整背景的硕士生，默认图文并茂。 |
| [`research-paper`](skills/research-paper/SKILL.md) | 从 PRD 生成和打磨 planned NeurIPS / ICLR / AAAI 风格论文，并强制实验结果 placeholder 绑定。 |
| [`research-spec`](skills/research-spec/SKILL.md) | 把 PRD 编译成全局执行合同：数据集、基线、复现目标、实验、模型、指标、seed、task graph、harness、evidence contract、anti-mock 规则。 |
| [`research-plan`](skills/research-plan/SKILL.md) | 从 Spec 生成 dated 具体执行计划：`docs/research/plans/YYYY-MM-DD-purpose/`。 |
| [`research-audit`](skills/research-audit/SKILL.md) | 审计 PRD、Paper、Spec、Plans、artifacts、insight 之间的一致性与漂移。 |

不要新增独立的 `research-evidence`、`research-writing` 或 `research-goal`。证据由 Spec / Plan / Audit 字段承担；洞察解释属于 `research-insight`；写作优化属于 `research-paper`；长期执行 prompt 属于 `research-plan`。

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

### 典型全流程

```
Day 1  用户：我想研究 X 方向，核心 idea 是 Y
       AI：初始化 docs/research/，开始逐章讨论 PRD
       AI：搜索文献，帮用户理清 baseline landscape
       AI：填写 PRD 第 1-16 章（含 Gate 调度表）
       用户：审阅 PRD，确认 Gate 顺序和 pass_condition 合理
       用户：批准 → AI 添加 PRD_STATUS: HUMAN_APPROVED

Day 1-3 AI：自动 Bootstrap → 生成 Spec → Plan → TASK_QUEUE → NEXT_ACTION
       AI：按 Gate 顺序自动执行每个 task
       AI：每完成一个 task 运行 update_state.py，自动推进到下一个
       AI：跨越 Gate 时运行 research-insight 更新 wiki

Day 3  场景 A：所有 Gate 通过 → closeout → 报告研究完成
       场景 B：Gate 阻断 → 报告 blocker，等用户决策
       场景 C：负结果反驳假设 → 写 negative_result，请求 review
```

### 用户角色

用户在整个流程中只做三件事：

1. **讨论方向**：在阶段 1 与 AI 讨论研究方向，帮助 AI 理解问题
2. **审批 PRD**：检查 AI 生成的 PRD（特别是 Gate 调度表和 pass_condition）
3. **关键决策**：当执行被 blocker 阻断或核心假设被证据反驳时做决策

其他一切——文档填写、Spec 编译、Plan 生成、任务执行、状态更新、wiki 沉淀——全部由 AI 自动完成。

### 三层自动化边界

| 层级 | 内容 | AI 权限 | 人类角色 |
|------|------|---------|---------|
| **执行层** | 文档填写、Spec/Plan 生成、代码运行、实验执行、状态更新 | Codex / Claude Code 作为 agent executor；系统记录结构化证据，不提供独立常驻 backend | 无需参与 |
| **洞察层** | Insight 记录、异常分类、Pivot 提案生成 | 自动准备材料 | 做决策（Approve/Reject/Revise） |
| **战略层** | 核心 RQ、问题表述、主 Claim、论文故事线 | 辅助文本，需人类审批 | 完全控制，AI 不得单方面修改 |

> **方向由人定，PRD 由 AI 写，执行全部自动。让 AI 做你最快的实验员和诚实的记录员，但让最终的方向判断永远属于人类。**

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

真实实验数据门禁是硬条件：mock / toy / synthetic / stub / cached / proxy 只能用于 unit、smoke 或 harness plumbing。任何 full experiment、claim-supporting reproduction、benchmark comparison、ablation、Go / No-Go 或 Paper Binding 都必须绑定真实数据和真实模型/代码。Spec readiness 会检查 dataset provenance、license/usage rights、frozen split 或 benchmark manifest、`is_mock: false`、model/checkpoint/API/code provenance、`is_stub: false`、full run command、real-data/model harness checks、artifact hash 和 non-smoke execution；缺失时必须 blocker，不能用 smoke/mock 结果顶替。

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

`ai_loop_prompt.md` 会包含 Claude Code `Subagent Dispatch` 段落。需要数学、文献、复现、编码、实验、分析、论文或审计工作时，主会话应委派 `.claude/agents/research-*.md` 中的标准 Claude Code subagent；`/research` controller 仍负责 state、gate、promotion 和 audit 阻断。

## Research Audit

`research-audit` 检查：

- PRD -> Paper alignment
- PRD -> Spec alignment
- Spec -> Plan alignment
- Paper -> Spec alignment
- Plan -> Artifact alignment
- Insight -> Spec / Plan alignment

`repair_plan.md` 必须区分：

- must fix before execution
- can fix later
- recommended next `research-plan` target

## 校验器

统一校验入口：

```bash
python3 skills/research-spec/scripts/validate_research.py --repo . --mode prd-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode paper-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode spec-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode plan-ready
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
