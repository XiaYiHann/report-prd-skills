# research-execution-skills

`research-execution-skills` 是一组面向 Codex / Claude Code 的研究执行技能。它不是独立服务端系统，也不提供独立常驻 backend；Codex / Claude Code 是实际执行 `TASK_QUEUE.yaml` 中 active task 的 agent executor，技能族负责提供文件系统协议、状态提交入口、证据记录格式和审计门禁。

目标不是让 prompt-only 文档替代实验，而是让 agent executor 在 Git-backed epoch 协议下执行任务，并通过 `update_state.py`、run report、artifact hash 和 audit hard gate 留下可验证证据。

## 新手先读

第一次使用不要先背完整协议树。先读 [`START_HERE.md`](START_HERE.md)，只建立五层心智模型：

```text
Direction -> Goal -> Task Queue -> Evidence/Audit -> Wiki/Closeout
```

四个最小问题：

1. 我在哪里：本仓库是框架仓库，具体研究应在下游项目的 `docs/research/` 中执行。
2. 先看哪里：下游项目先看 `docs/research/RESEARCH_DIRECTION.md` 和当前 `Vn/goal.md`。
3. 先跑什么：用 `research-status` 做只读状态检查，再按 `TASK_QUEUE.yaml` 的 active task 前进。
4. 卡住看哪里：先看 `research-status` 顶部摘要，再看 `Vn/runs/`、`Vn/audits/` 和 `Vn/HUMAN_REVIEW_REQUESTS.yaml`。

高频术语见 [`GLOSSARY.md`](GLOSSARY.md)。完整设计、schema、门禁和安装说明见下文。

## 本仓库边界

本仓库是 `research-loop` 元框架仓库，只维护技能、schema、controller、installer、agent policy、测试与文档。仓库自身的 `docs/research/` 只能作为框架方向和 policy/template 说明；不得把本仓库当作具体 project-research 工作区，不得在本仓库绑定真实 dataset、baseline、metric、method、benchmark result、paper claim 或 paper binding。

`CURRENT`、`Vn/`、`PRD.tex`、`RESEARCH_SPINE.yaml`、`TASK_QUEUE.yaml`、`BASELINE_LOCK.yaml` 等 epoch 文件是下游研究仓库由 `research-init` 生成和执行的协议面，不是本仓库的本地研究真源。本仓库的验证对象是“框架能否生成、校验和守护这些协议”，不是某个具体科研项目是否成立。

## 极简科学前门

用户不应被要求手工填写 PRD、Spine、Spec、Plan、Task Queue 与 Evidence Gate。正确的用户界面是“最小科学判断”：用户只提供 Big RQ、核心假设、证伪条件、最接近基线、数据集或环境、指标或判断规则、停止规则。系统把这些 judgment 编译成内部严格协议，并把所有 claim 保持在 draft 状态，直到 `EVIDENCE_GATE.yaml` 基于真实 artifact、命令、hash、audit 和 baseline/source lock 批准。

```yaml
title: Judgment Driven Research
big_rq: Can explicit evidence gates reduce unsupported claims in agent research workflows?
core_hypothesis: Explicit evidence gates reduce unsupported claims by forcing every claim through observed artifacts and audit.
falsification_condition: If unsupported claim rate is unchanged after gate enforcement under the declared evaluation protocol.
closest_baseline: Ad-hoc prompting without a claim-to-evidence gate.
dataset_or_environment: A controlled repository fixture with scripted research tasks.
metric_or_judgment_rule: Unsupported claim rate after audit.
stop_rule: Stop if G0 search cannot define a fair baseline or if G1 reproduction remains blocked after human review.
```

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo /absolute/path/to/project \
  --judgment-file /absolute/path/to/judgment.yaml \
  --force
```

该入口生成 `SCIENTIFIC_JUDGMENT.yaml`、已批准的 `RESEARCH_DIRECTION.md`、带 binding 的 `PRD.tex`、`RESEARCH_SPINE.yaml`、RQ-local `SPEC.yaml` / `PLAN.md` / `TASKS.yaml`、`TASK_QUEUE.yaml` 与 `EVIDENCE_GATE.yaml`。同时，`BASELINE_LOCK.yaml` 保持 `needs_human_review`，`baseline-lock-ready` 必须失败，直到 G0/G1 证据真实完成。这一设计把用户友好性限制在前门，把科学严谨性落实到内部协议和门禁。

整个流程分为三个阶段：

```text
阶段 0：初始化       → research-init 创建 docs/research/ epoch 工作区
阶段 1：PRD 讨论生成  → AI 与用户逐章讨论，AI 填写 16 章 PRD（含 Gate 调度表），用户审批
阶段 2：自动执行      → AI 按 Gate 顺序自动执行所有 task，遇阻断才停，直到 closed_* 或 Paper Binding
```

核心原则：`RESEARCH_DIRECTION.md` 控制探索边界；`/research explore` 负责纯探索；当前 `Vn/PRD.tex` 是当前 epoch 的人类研究真源，并真实渲染为 `Vn/PRD.pdf`；`Vn/PRD_SUMMARY.md` 只是 agent context，不得反向覆盖 PRD；`Vn/RESEARCH_SPINE.yaml` 是证据链绑定合同（RQ → Claim → Experiment → Evidence → Figure/Table → Paper Section）；`Vn/rqs/RQxx/SPEC.yaml` 与 `Vn/rqs/RQxx/PLAN.md` 是 RQ-local 执行真源；`Vn/TASK_QUEUE.yaml` 负责全局调度；`Vn/EVIDENCE_GATE.yaml` 负责 claim admission；`update_state.py` 在每次任务完成后原子更新状态；Git 记录真实工程变化；Paper 只是表达层，不能反推实验、数据集、基线、指标、seed、任务、harness 或结果。

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

方法学名是 **Insight-Compounding RQ Loop**，中文可称为 **洞察复利式 RQ 驱动研究循环**。

这里的 compounding 不是 claim compounding，而是 insight compounding。研究进展不能通过累积更顺滑的叙事或未经验证的结论复利；它只能通过经过 Evidence Gate、Audit 与 Human Insight Verdict 的洞察复利。每一轮 `RQ_t` 的价值不只在于回答当前问题，还在于把 evidence、blocker、negative result、baseline dossier、reproduction asset、failure taxonomy 与 open question 沉淀为下一轮更尖锐的 `RQ_{t+1}`。

```text
RQ_t
  -> evidence / blocker / negative result
  -> audited insight
  -> frontier map
  -> sharper RQ_{t+1}
```

因此，research-loop 的版本推进原则是：

- 问题复利：新 RQ 必须基于上一轮已审计 insight 收缩问题空间，而不是重新发散。
- 证据复利：artifact、baseline、reproduction asset 可以 carry forward，但必须显式登记来源、hash、限制与 audit 状态。
- 失败复利：negative result、blocked path 与复现失败必须减少未来搜索空间，而不是被隐藏。
- 协议复利：每轮应留下更稳定的 harness、metric、baseline dossier、failure taxonomy 与 evidence admission rule。

核心边界：

> Research progress compounds only through audited insight, not through accumulated prose or unverified claims.

## 安装

**强制更新到最新版本（覆盖已有文件）：**

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh | bash -s -- --force
```

从本地 checkout 安装：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" bash install.sh --force
```

常用选项：

```bash
./install.sh --force             # 强制覆盖已有文件（更新到最新版本）
./install.sh --init-workspace    # 同时创建 docs/research/ epoch 工作区
./install.sh --no-agents         # 只安装 skills
./install.sh --dry-run           # 只打印计划，不写文件
```

安装后文件布局：

```text
~/.agents/skills/      # canonical skill store
  research/            # unified autonomous controller
  research-explore/    # pure exploration
  research-insight/    # evidence-grounded interpretation
  research-status/     # read-only experiment progress
  research-update/     # framework skill update and verification
  research-init/       # workspace initialization
  research-goal/       # Vn goal synthesis
  research-audit/      # cross-file consistency audit

~/.agents/skills/      # 内部 compiler module；不是用户入口
  research-paper/      # scripts only; no SKILL.md
  research-spec/       # scripts only; no SKILL.md
  research-plan/       # scripts only; no SKILL.md

~/.claude/skills -> ~/.agents/skills

~/.claude/agents/
  research-math.md     research-literature.md  research-reproduce.md
  research-coding.md   research-experiment.md  research-analysis.md
  research-paper.md    research-audit.md
```

安装器以 `~/.agents/skills` 为唯一安装真源，并把 `~/.claude/skills` 整体收敛为指向它的 symlink。`--force` 会先删除 research-loop 管理过的历史入口，再安装当前 manifest；`research-prd`、`research-ppt`、`research-evidence`、`research-writing` 会整目录删除，`research-spec`、`research-plan`、`research-paper` 只保留内部脚本且不得包含 `SKILL.md`。这样 Codex/Claude 的技能发现不会继续读到旧用户入口。

## Charter-bounded Epoch Research Loop

新版系统定义为 **Charter-bounded Epoch Research Loop**。

中文定义：

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

English definition:

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

线性循环被升级为：

```text
Research Direction
  -> V0 PRD.tex / PRD.pdf
  -> V0 RQ-local Spec
  -> V0 RQ-local Plan
  -> V0 Task Queue
  -> Claude/Codex executes active task
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
    PRD.tex
    PRD.pdf                 # 若本机缺 LaTeX，则写 render_blocker.md，不伪造 PDF
    PRD_SUMMARY.md          # agent context only，不是真源
    SCIENTIFIC_JUDGMENT.yaml # 仅 judgment-file 初始化时存在，记录用户最小科学判断
    goal.md
    GOAL_LOCK.yaml          # goal.md 的 source hash 与刷新合同
    RESEARCH_SPINE.yaml
    EVIDENCE_GATE.yaml      # claim admission gate，未审计证据只能保持 draft claim
    STATUS.yaml
    TASK_QUEUE.yaml
    rqs/
      RQ01/
        RQ.md
        SPEC.yaml           # RQ-local scientific contract
        PLAN.md             # RQ-local evidence-generation plan
        TASKS.yaml
        reproduction/
          SOURCE_LOCK.yaml
          REPRODUCTION_SPEC.yaml
          VERIFICATION.yaml
          IMMUTABLE_BASE.yaml

    LOOP_LOG.md
    GIT_STATE.yaml
    git_log.md
    AUDIT_QUEUE.yaml
    HUMAN_REVIEW_REQUESTS.yaml
    PAPER_CLAIM_LEDGER.yaml
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

关键 epoch 文件：

| 文件 | 作用 |
|------|------|
| `Vn/PRD.tex` | 当前 epoch 的 canonical Research PRD 真源，使用 16 章专业科研执行文档结构 |
| `Vn/PRD.pdf` | 从 `PRD.tex` 真实编译出的审阅产物；无 LaTeX 或编译失败时必须写 blocker |
| `Vn/PRD_SUMMARY.md` | agent 快速上下文摘要，不是真源，不得反向覆盖 `PRD.tex` |
| `Vn/SCIENTIFIC_JUDGMENT.yaml` | judgment-file 初始化时的用户最小科学判断记录；它是输入 judgment，不是 observed evidence |
| `Vn/goal.md` | 当前 epoch 的执行目标锚点：由 controller 在每次 loop 开始时读取，作为单步决策的上下文边界 |
| `Vn/GOAL_LOCK.yaml` | `goal.md` 的生成/刷新合同，记录 PRD、baseline、spine、RQ-local contracts、task queue、evidence gate 和 status 的 source hash |
| `Vn/RESEARCH_SPINE.yaml` | 证据链绑定合同：`RQ -> Claim -> Experiment -> Evidence -> Figure/Table -> Paper Section` 的硬约束映射 |
| `Vn/EVIDENCE_GATE.yaml` | claim admission gate；只有真实 artifact、命令、hash、audit 与 source/baseline gate 满足后，draft claim 才能升级为 allowed claim |
| `Vn/rqs/RQxx/SPEC.yaml` | 单个 RQ 的科学执行合同：claim boundary、reproduction、experiment、evidence、failure taxonomy |
| `Vn/rqs/RQxx/PLAN.md` | 单个 RQ 的证据生成计划，区分 TDD 工程任务与 evidence-driven 实验任务 |
| `Vn/PAPER_CLAIM_LEDGER.yaml` | 论文主张台账：记录每个 claim 的绑定状态（unbound / bound / audited / ready）和 evidence trace |
| `Vn/HUMAN_REVIEW_REQUESTS.yaml` | 人类审查请求队列：文档撰写阶段遇到歧义时记录 blocker，等待用户决策 |

关键执行工具：

| 文件 | 作用 |
|------|------|
| `skills/research/scripts/update_state.py` | 原子状态更新器：每次任务完成后一键更新 TASK_QUEUE、LOOP_LOG、GIT_STATE、STATUS、run report |
| `skills/research/scripts/research_loop.py` | 确定性状态机控制器：检测 PRD readiness、生成 Spec/Plan/TASK_QUEUE、推进 Gate |
| `skills/research-init/_shared/scripts/research_workspace.py` | 共享库：所有模板、run report schema、Gate 检测 |

每个 `Vn` 是完整研究轮次，不是 PRD minor version。旧版本 `V0...Vn-1` 只能作为 context / memory / history，不再有执行权。旧版本 artifact 不能直接支持当前版本 claim，除非当前 `Vn/PRD.tex`、`Vn/RESEARCH_SPINE.yaml` 或 RQ-local `SPEC.yaml` 显式 `carry_forward`。

## Current Version Resolution

`docs/research/CURRENT` 只包含当前版本名，例如 `V0`。读取顺序固定为：

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/goal.md`
5. `docs/research/{CURRENT}/GOAL_LOCK.yaml`
6. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
7. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
8. `docs/research/{CURRENT}/PRD.tex`
9. `docs/research/{CURRENT}/PRD_SUMMARY.md`
10. `docs/research/{CURRENT}/rqs/RQxx/SPEC.yaml`
11. `docs/research/{CURRENT}/rqs/RQxx/PLAN.md`
12. `docs/research/{CURRENT}/EVIDENCE_GATE.yaml`

## 三阶段工作流

### 阶段 0：初始化

若 `docs/research/` 不存在，`research-init` 创建 epoch 工作区：

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo . --title "项目标题" --purpose "研究目标"
```

产物包括 `RESEARCH_DIRECTION.md`、`CURRENT`、`V0/` epoch、`CLAUDE.md`、`AGENTS.md`。

### 阶段 1：PRD 讨论与生成

初始化后 `TASK_QUEUE.yaml` 的 Active Task 为 TASK_001：完善 PRD。AI 与用户逐章讨论 16 章 PRD，AI 填写所有内容：

- 第 2 章背景教程、第 3 章相关工作地图：AI 搜索文献帮助理清 landscape
- 第 4 章基准与复现计划：AI 帮助选 concrete baseline、dataset、metric
- 第 6 章研究问题与假设：AI 帮用户把模糊 idea 变成可证伪的 RQ
- 第 10 章实验设计：AI 帮助设计 experiment matrix
- **第 11.2 章 Gate 调度表（关键）**：AI 帮用户把研究拆成有序 Gate，每个 Gate 定义 task 清单和可验证的 pass_condition
- 第 12 章 Harness：AI 帮用户定义每个 task 的 harness 命令和验收标准

用户审批后，AI 在 `PRD.tex` 中添加 `PRD_STATUS: HUMAN_APPROVED` 或等价 LaTeX marker，重新渲染 `PRD.pdf`，运行 `update_state.py` 标记 TASK_001 done，进入阶段 2。

### 阶段 2：自动执行（Continuous Loop）

PRD 锁定后，控制器自动推进：

```bash
# Bootstrap：重复运行直到生成 SPEC/PLAN/TASK_QUEUE
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once
```

当 `TASK_QUEUE.yaml` 中出现具体执行任务后，进入持续循环：

```
while STATUS.yaml.status not in (closed_*, gate_blocked):
    1. 读取 `TASK_QUEUE.yaml` 中的 active task（含完整 task 执行细节）
    2. 执行 task（写代码/跑实验/复现 baseline）
    3. 完成后运行 update_state.py 原子更新 6 个状态文件
    4. `update_state.py` 已自动更新为下一个 active task
    5. 继续循环，不询问用户
```

**停止条件**：`gate_blocked`（报告 blocker 等待人工决策）、`closed_*`（报告 closeout 摘要）、实验证据反驳 PRD 核心假设（写 negative_result 请求 review）。

若要在 Codex 或 Claude Code 中驱动自动执行，使用当前版本的 `docs/research/{CURRENT}/goal.md` 作为目标模式输入；每一轮仍必须从 `TASK_QUEUE.yaml` 读取唯一 active task。

## Goal Mode Usage

Codex 使用 `docs/research/agent/CODEX_GOAL_TEMPLATE.md`：目标必须是完成当前 active task。若改代码，运行相关测试；若不能测试，写明 blocker。Codex 不修改 Research Direction，不在 closeout 前创建下一版本，不把未验证 artifact 写成 paper result。

## Task Queue and Next Action

`TASK_QUEUE.yaml` 是 Gate-aware 队列；同一时间只能有一个 `active` Task，除非显式并行且 `allowed_files` 不冲突。`TASK_QUEUE.yaml` 是 Gate-aware 状态文件。短规则：

> 工程问题留在当前版本；研究问题改变才开下一版本。

Terminology:

- Gate: 研究阶段门禁，必须有可验证的 pass/block/falsification 条件。
- Task: Gate 内的最小执行单元。
- Harness: 验证 Task 的命令、输入、输出、artifact 和判定器。
- Audit: Gate 或关键 Task 后的对抗性审查，P0/P1 失败会阻断推进。
- Insight: 从运行、阻断、失败、异常或负结果中沉淀的证据化知识；AI 只能写 draft，进入 wiki 和 paper eligibility 必须经过 human verdict。
- Frontier Map: `wiki/frontier_map.yaml` 中的版本收口综合，记录当前已知、未知、失败路径、可复用复现资产和下一版候选方向。

### 文档撰写 vs 执行自治边界

Agent 在**撰写文档阶段**（编写或修改 PRD、SPEC、PLAN、RESEARCH_SPINE、ai_loop_prompt.md、goal.md、CODEX_GOAL_TEMPLATE.md）遇到用户意图不明、要求自相矛盾、或需要做出影响研究方向/核心假设/基准选择的决定时，**必须停止并请求用户确认**，不得自行推断。

Agent 在**执行阶段**（运行实验、编写代码、执行 harness、收集 artifact、运行测试、复现 baseline）遇到同样情况时，**不得停止询问用户偏好**，应自主推进，并仅对确实缺失的必需信息（dataset、seed、command、artifact 路径）记录 blocker。

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
  frontier_map.yaml
  insight_index.yaml
```

wiki 记录成功信号、失败路径、负结果、baseline 认知、文献 blocker、human-reviewed insight 和下一版种子。`insight_index.yaml` 只登记经过人类裁决的 insight；`frontier_map.yaml` 是从当前版本走向下一版本的综合依据。

## Version Closeout

每个版本必须以 `closeout.md` 结束。关闭状态包括 `closed_success`、`closed_negative`、`closed_blocked`、`closed_falsified`、`closed_pivot_required`、`closed_stable`。`gate_blocked` 不是失败，而是合法 closeout 条件。

## When to Create Next Version

只有当前版本 `closeout.md` 完成且 status 为 `closed_*` 时，才允许创建 `Vn+1` draft。创建条件包括研究问题变化、hard gate 阻断但出现更合理 framing、核心假设被负结果反驳、baseline/metric/dataset/model 改变主 claim、exploration 结束需要进入 confirmatory/intervention/training。

不创建新版本：修 bug、补 artifact path、修测试、增加 sanity check、重跑 seed、小 baseline 补充、Spec 字段补全、Paper placeholder 修正、Plan stale 后重新生成。

## Paper Binding

Paper Binding 只能在当前版本 `status=closed_stable` 或 `paper_binding_ready` 时发生，且必须存在 `PAPER_BINDING_DECISION.md`，明确 `paper_binding_ready: true`。Allowed claim 必须绑定 experiment、run、artifact、metric、baseline、seed protocol、audit status、real data check、real model/code check 和 non-smoke full-run check。Binding 成功后状态进入 `paper_bound`，同一版本不再继续改写 binding 结果。Exploratory insight 只能进入 motivation / discussion；prompt-only scaffold 不能成为实验结果。

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

主 agent（`/research` controller）始终负责：状态推进、gate 判定、active task 执行、wiki/closeout。

## Search and Evidence Acquisition Policy

Search is a hard evidence-acquisition step, not a writing aid. 新 epoch 默认先执行 `G0_SEARCH_LOCK`，在该 gate 内完成 raw search logs、curated `baselines/INDEX.yaml` 和 version-level `BASELINE_LOCK.yaml`，再执行 `G1_REPRODUCTION_LOCK`；proposed-method experiment 不能在 search、baseline lock 和 reproduction early gates resolved 之前成为 active task，除非存在明确 human waiver 和 audit 记录。

Search 必须覆盖 literature、official code、third-party implementations、datasets、model checkpoints、known issues / forks / reproduction notes，以及 current local repository state。要求在 project start、version start、baseline lock、reproduction task、dataset/model/metric selection、unexpected strong/negative result、pivot proposal、before paper binding 检索。修 bug、补 artifact path、跑测试、更新 wiki、执行已锁定 Plan、小工程重构不需要检索。无网络时写 search blocker，不编造文献、代码仓库、数据集、指标或模型能力。

`search/`、`baselines/` 和 `BASELINE_LOCK.yaml` 分层负责。`search/` 保存 raw discovery；`baselines/` 保存 curated baseline dossier；`BASELINE_LOCK.yaml` 是版本级研究坐标系和最终决策真源：它从 web search、repo search 与 baseline dossier 中冻结本版本采用的 strongest / official / simple-control baselines、dataset、split、metric 和可复用实验设计。RQ-local reproduction 必须继承该 lock；未 locked 时不得进入 reproduction、innovation、experiment 或 analysis task。

`docs/research/Vn/baselines/INDEX.yaml` 必须索引每个 curated baseline card。推荐每个 baseline 使用 `baselines/Bxxx/{BASELINE_CARD.yaml,PAPER_CARD.yaml,DATASET_CARD.yaml,EXPERIMENT_DESIGN.yaml,REUSE_DECISION.yaml}`。`BASELINE_LOCK.yaml.selected_baselines[]`、`selected_datasets[]` 和 `borrowed_experiment_designs[]` 必须引用这些 card；audit 不允许只在 lock 中写一个名字而没有可追溯 dossier。

Reproduction failure 必须分类，不能静默忽略，也不能当作 hypothesis falsification。`blocked_missing_code`、`blocked_missing_data`、`blocked_stale_dependency`、`blocked_ambiguous_algorithm`、`failed_metric_mismatch`、`failed_unexplained` 都需要进入 `REPRODUCTION_INDEX.yaml` 和 audit；只有 valid harness output 加 adversarial audit 才能支撑研究解释。

`docs/research/Vn/reproduction/` 是 reproduction metadata 真源；`reproduction/Vn/` 是可执行 reproduction workspace，只有具体复现任务开始时才创建。旧 epoch 的 reproduction 结果不能自动支撑当前 claim；必须通过 `RESEARCH_SPINE.yaml` 或 RQ-local `SPEC.yaml` 的 `carry_forward` / `reproduction_contract` 显式继承，并满足同一研究问题、dataset/metric 兼容、artifact hash 和 audit passed。

`REPRODUCTION_LEDGER.yaml` 是跨 RQ 复用账本。每个 RQ 都必须做 reproduction coverage check，但不要求重复执行已兼容的复现资产。合法结论包括 `reuse_allowed`、`delta_check_required`、`new_reproduction_required` 和 `reuse_blocked`；setting、dataset、metric 或 task definition 变化时必须走 delta check 或新复现。

每个 `rqs/RQxx/INSIGHT_REVIEW.yaml` 是 human insight gate。AI 可以根据 evidence bundle 草拟 `ai_draft`，但 `human_verdict` 才能写入 `wiki/insight_index.yaml` 并影响 `frontier_map.yaml`、下一版 RQ 和 Paper Binding。

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

`docs/research/insights/insight_log.md` 进入逐步退役状态：它仍作为 legacy workspace 的兼容读写目标和 migration source，但在存在 `CURRENT` 与 `Vn/wiki/` 时不再是默认 insight 真源。旧 insight 只能作为候选材料，不能直接支撑当前版本 claim，除非当前 `Vn/PRD.tex`、`Vn/RESEARCH_SPINE.yaml` 或 RQ-local `SPEC.yaml` 显式 `carry_forward`。

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
- `rq-driven-ready`：检查当前 workspace 是否采用标准 RQ-driven 结构：`Vn/PRD.tex`、`Vn/RESEARCH_SPINE.yaml`、以及每个 RQ 对应的 `Vn/rqs/RQxx/` Spec/Plan/Task/Reproduction contract。
- `baseline-lock-ready`：检查当前 `Vn/BASELINE_LOCK.yaml` 是否已锁定版本级 baseline、dataset、metric 和实验设计坐标系，并验证 `Vn/baselines/INDEX.yaml` 与 selected card 引用可解析。
- `migration-ready`：识别 `epoch_v1`、`legacy_flat`、`mixed`、`unknown`，并报告 `standard`、`migration_recommended` 或 `migration_required`。
- `git-ready`：检查 `GIT_STATE.yaml`、task git policy、done task commit hash、closeout/paper-binding git 记录、dirty tree。

Audit 会显式检查 `RESEARCH_DIRECTION.md` 完整性：必备章节、Direction Status 字段、human-approved/frozen 状态、Research Corridor、Out-of-Scope、Autonomy Boundary 和 Global Stop Conditions。缺口会写入 `alignment_matrix.yaml` 的 `direction_completeness`、`drift_findings.yaml`、`audit_report.md` 和 `repair_plan.md`。

Migration audit 可以生成 `docs/research/audits/MIGRATION_AUDIT.md` 和 `docs/research/MIGRATION_PLAN.md`。若不是标准 RQ-driven 结构，audit 必须提醒用户迁移并给出迁移方案；但不能默认改写研究主张，也不能把旧 insight 直接变成 paper evidence。

## Updated Full Loop

```text
Explore
  -> Research Direction
  -> CURRENT/Vn
  -> PRD
  -> SPEC
  -> PLAN
  -> TASK_QUEUE
  -> active task
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
- `spine-ready`
- `loop-ready`
- `loop-prompt-ready`
- `closeout-ready`
- `paper-binding-ready`
- `format-ready`
- `rq-driven-ready`
- `baseline-lock-ready`
- `migration-ready`
- `git-ready`

保留 legacy readiness mode：`prd-ready`、`paper-ready`、`spec-ready`、`plan-ready`、`audit-ready`、`insight-ready`、`alignment-check`。其中 `insight-ready` 只服务旧 `docs/research/insights/` 兼容路径；新项目默认用 `research-insight` 更新当前 `Vn/wiki/*`。

## Unified `/research` Loop

`/research` 是默认入口。新版优先解析 `RESEARCH_DIRECTION.md`、`CURRENT` 和当前 `Vn`；legacy workspace 仍保留兼容。

### 三阶段自动化流程

**阶段 0：初始化。** 若 `docs/research/` 不存在，`research-init` 创建完整 epoch 工作区。

**阶段 1：AI 生成 PRD。** 用户无需手动填写 PRD。AI 与用户逐章讨论 16 章内容，AI 负责填写所有章节（包括 Gate 调度表和 Harness 表），用户只需审批。用户确认后 AI 添加 `PRD_STATUS: HUMAN_APPROVED`。

**阶段 2：自动执行。** PRD 锁定后，`/research` 控制器自动执行内部 compiler passes：Spec → Plan/TASK_QUEUE → paper draft。Spec/Plan/Paper 不再需要用户显式调用对应 skill；但每个 pass 后的 validation/audit gate 仍是硬门，不能自动跳过。之后进入持续循环：每轮执行 `TASK_QUEUE.yaml` 中的 active task，完成后运行 `update_state.py` 原子更新 5 个状态文件，active task 自动推进到下一个任务。循环不询问用户，直到：
- `STATUS.yaml.status` 为 `closed_*` 或 `paper_bound` → 研究完成
- `STATUS.yaml.status` 为 `gate_blocked` → 报告 blocker，等待人工决策
- 实验证据反驳 PRD 核心假设 → 写 negative_result，请求人工 review

### 控制器命令

```bash
# Bootstrap 状态机（内部生成 Spec/Plan/TASK_QUEUE/paper draft）
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once

# 原子状态更新（每次任务完成后执行）
python3 ~/.claude/skills/research/scripts/update_state.py \
  --repo . --task-id TASK_002 --status done --commit-hash abc123 --gate-id G01

# 标记阻塞
python3 ~/.claude/skills/research/scripts/update_state.py \
  --repo . --task-id TASK_003 --status blocked --blocker-reason "具体原因"
```

### Goal Mode 自动循环

Codex 与 Claude Code 均以当前版本的 `goal.md` 作为长程目标输入，以 `GOAL_LOCK.yaml` 校验目标是否仍匹配当前 PRD、Spine、RQ-local contracts、Task Queue、Evidence Gate 与状态文件。目标模式不引入独立循环插件；每轮执行只推进 `TASK_QUEUE.yaml` 中的唯一 active task，遇到 blocker、stale lock、human review 或 closeout 即停止。

### 执行 Backend / Agent Executor

```text
默认路径：`/research` 先推进内部 Spec/Plan/Paper compiler passes；随后 Codex / Claude Code agent executor 读取 `Vn/TASK_QUEUE.yaml` 中的 active task 并提交结构化证据。
不提供独立常驻 backend；`research_loop.py` 不伪装成 shell runner，也不运行实验 harness。

--legacy-controller      # 显式启用 legacy deterministic controller
--executor prompt-only   # 仅 legacy controller 的兼容槽位
```

prompt-only scaffold 不能作为实验结果或 paper binding 证据。

旧的内部模块仍保留脚本入口用于调试：`skills/research-paper/scripts/`、`skills/research-spec/scripts/`、`skills/research-plan/scripts/`。这些目录不再包含 `SKILL.md`，不会作为常规用户入口安装。正常托管研究项目时只运行 `/research`；不要让用户手动串联 Spec/Plan/Paper。

## 技能列表

| Skill | 用途 |
|---|---|
| [`research`](skills/research/SKILL.md) | 默认统一入口：检查 `docs/research/`，维护 state/queue，内部推进 PRD→Spec→Plan→Paper draft，执行提示、Audit、Insight、Paper Binding 边界。 |
| [`research-explore`](skills/research-explore/SKILL.md) | 纯探索入口：讨论 idea、文献、baseline、novelty、failure analysis、paper shape、next-version framing；可保存 EXP session，但不执行。 |
| [`research-insight`](skills/research-insight/SKILL.md) | 显式解释入口：把 run、artifact、blocker、负结果、失败路径或 explore session 沉淀到当前 `Vn/wiki/*`，并把 legacy `insight_log.md` 逐步退役。 |
| [`research-status`](skills/research-status/SKILL.md) | 只读实验进展入口：报告当前目标、Big RQ、当前 gate/active task、RQ-local 进展、证据缺口、blocker、可继续任务与 validator 状态；不推进任务。 |
| [`research-update`](skills/research-update/SKILL.md) | 显式更新入口：更新或重装 research-loop skill family，清理 retired skill，验证 `~/.agents/skills` 真源和 `~/.claude/skills` symlink。 |
| [`research-init`](skills/research-init/SKILL.md) | 初始化 `docs/research/`，创建中文 LaTeX 真源 Research PRD、paper、spec、plans、audits 和 epoch scaffold。 |
| [`research-goal`](skills/research-goal/SKILL.md) | 生成或刷新当前 `Vn/goal.md` 与 `Vn/GOAL_LOCK.yaml`，作为长循环执行目标锚点。 |
| [`research-audit`](skills/research-audit/SKILL.md) | 审计 PRD、Paper、Spec、Plans、artifacts、insight 之间的一致性与漂移。 |

不要新增独立的 `research-evidence` 或 `research-writing`。证据由 Spec / Plan / Audit 字段承担；洞察解释属于 `research-insight`；写作 draft 由 `/research` 内部 paper stage 触发；长期执行 prompt 的单步调度属于 `/research`、内部 plan stage 和 `TASK_QUEUE.yaml`。`research-prd`、`research-spec`、`research-plan`、`research-paper` 不再是常规用户入口；PRD、Spec、Plan、Paper 均由 `/research` 内部 compiler pipeline 生成或维护。`research-goal` 只负责 version-level goal synthesis，不执行任务、不生成证据、不替代 Plan。

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

Day 1-3 AI：自动 Bootstrap → 生成 Spec → Plan → TASK_QUEUE
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

## Internal PRD Compiler Stage

PRD 现在是 `/research` 的内部 compiler stage，而不是常规用户 skill。新 epoch 的 canonical PRD 是 `docs/research/{CURRENT}/PRD.tex`，`PRD.pdf` 是真实编译出的审阅产物，`PRD_SUMMARY.md` 只是 agent context。PRD 不是短论文，也不是占位符列表，而是专业、详细、教学友好、可执行的研究设计文档。标题采用中文 + 英文 canonical label，必须包含：

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
16. 探索与洞察策略（Exploration and Insight Policy）

PRD 要解释足够背景，使有能力但非该方向专家的硕士生可以执行；同时必须定义具体任务、benchmark、实验、harness、验收条件和证据边界。

模板质量要求：

- 每章包含章节目标、必须填写的信息、常见错误、证据边界、验收标准。
- 使用结构化中文占位符 `【待填写：...】`，不使用裸 `TODO`。
- 默认包含 TikZ 图骨架：研究问题到证据链、方法模块图、实验/复现流程图、Spec -> Plan -> Audit 执行闭环。
- 关键章节包含 RQ/Hypothesis 表、Benchmark Candidate Matrix、Experiment Matrix、Task Graph Table、Evidence Ledger、Risk Matrix。

## Internal Paper Compiler Stage

Paper 现在是 `/research` 的内部 paper stage，而不是常规用户 skill：PRD/closeout 后自动生成 planned top-conference-style manuscript draft；Paper Binding 必须等待 `PAPER_BINDING_DECISION.md` 人工批准。它可以对已经在 PRD 中设计好的对象使用强表达：

内部 paper draft 的最终产物必须是一篇完整顶会风格 manuscript draft，而不是填空模板。正文应当像 NeurIPS / ICLR / AAAI 论文一样完整叙述 Abstract、Introduction、Related Work、Problem Formulation、Method、Experiments、Results / Planned Result Bindings、Limitations 和 Conclusion。若真实实验尚未完成，只能生成 placeholder-complete manuscript：表格结构、caption、结果段落和解释逻辑可以完整，但所有未验证结果值必须保留为 Spec 绑定 typed placeholder，并在 `paper_gap_report.md` 记录投稿前必须替换的证据。不得填入 plausible mock numeric values。

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

## Internal Spec Compiler Stage

Spec 现在是 `/research` 的内部 compiler pass，而不是常规用户 skill。它把 PRD 与 Spine 编译成机器执行合同：

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

新默认是 RQ-local + Version Baseline Lock + Baseline Dossier：内部 compiler 只写入 `Vn/rqs/RQxx/SPEC.yaml`，全局 RQ 索引由 `RESEARCH_SPINE.yaml` 的 `spec_ref` / `plan_ref` 承担。它只能从 `PRD.tex`、`RESEARCH_SPINE.yaml`、`Vn/baselines/INDEX.yaml` 与已锁定的 `BASELINE_LOCK.yaml` 编译执行合同，不能从 Paper 或 `PRD_SUMMARY.md` 推断实验。PRD 缺失的执行细节必须进入 gap report 或 blocker，不能由 agent 发明。

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

## Internal Plan Compiler Stage

Plan 现在是 `/research` 的内部 compiler pass，而不是常规用户 skill。它从 RQ-local Spec 生成 bounded execution plan、RQ-local `PLAN.md` / `TASKS.yaml` 与全局 `TASK_QUEUE.yaml`。不再生成 epoch-level `Vn/PLAN.md`；`Vn/TASK_QUEUE.yaml` 只负责调度。`plan.yaml` 保持英文 key 和稳定 ID，但 `plan.md`、`ai_loop_prompt.md`、状态日志、阻塞日志、决策日志、运行日志和最终总结全部使用中文。

调试时仍可直接调用 `skills/research-plan/scripts/generate_research_plan.py`，但正常生命周期应由 `/research` 自动触发，用户不需要手动调用 plan compiler。

每个 plan 必须记录 PRD、Paper、Spec 和 git commit 的 source hash。若 Spec 在 plan 创建后改变，`plan-ready` 必须失败，直到显式生成或更新 plan。

`ai_loop_prompt.md` 会包含 Claude Code `Subagent Dispatch` 段落。需要数学、文献、复现、编码、实验、分析、论文或审计工作时，主会话应委派 `.claude/agents/research-*.md` 中的标准 Claude Code subagent；`/research` controller 仍负责 state、gate、promotion 和 audit 阻断。

## Research Goal

`research-goal` 生成或刷新当前 `Vn/goal.md`，并写入 `Vn/GOAL_LOCK.yaml`。它读取 `RESEARCH_DIRECTION.md`、`PRD.tex`、`BASELINE_LOCK.yaml`、`baselines/INDEX.yaml`、`RESEARCH_SPINE.yaml`、`rqs/`、`TASK_QUEUE.yaml`、`EVIDENCE_GATE.yaml` 和 `STATUS.yaml`，把这些合同压缩成面向 Codex / Claude Code goal mode 的长程目标。`goal.md` 不是 task queue；单步执行真源仍然是 `TASK_QUEUE.yaml`。

```bash
python3 skills/research-goal/scripts/generate_research_goal.py --repo . --target both
python3 skills/research-spec/scripts/validate_research.py --repo . --mode goal-ready
```

若上述任一 source 文件改变，`goal-ready` 必须因 stale source hash 失败，直到重新运行 `research-goal`。这保证长循环 prompt 与当前 PRD、baseline、RQ spine、Spec 和计划状态一致。

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
- recommended next internal Plan compiler target

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
python3 skills/research-spec/scripts/validate_research.py --repo . --mode rq-driven-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode baseline-lock-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode goal-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode migration-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode git-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode spine-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode loop-prompt-ready
```

readiness mode 必须硬失败。scaffold 可以存在 blocker，但不能被当成 execution-ready。

## 开发验证

运行：

```bash
python3 -m pytest tests -q
```

默认只运行纯合同与快速单测；标记为 `integration` 的工作区/子进程测试，以及标记为 `slow` 的 LaTeX 编译测试，会默认跳过。需要完整验证时使用：

```bash
python3 -m pytest tests -q --run-integration
python3 -m pytest tests -q --run-slow
python3 -m pytest tests -q --run-integration --run-slow
```

当前 GitHub 默认安装源是 `XiaYiHann/research-loop`；旧环境变量 `REPORT_PRD_SKILLS_*` 仅为兼容历史安装脚本保留。

## License

Apache 2.0
