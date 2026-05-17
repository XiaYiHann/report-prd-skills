# Gate-Aware Research Loop 设计规格

> Historical design snapshot. Superseded by the current RQ-driven pipeline:
> `RESEARCH_SPINE.yaml` is the version-level scheduling truth,
> `rqs/RQxx/TASKS.yaml` is the RQ-local execution truth,
> `TASK_QUEUE.yaml` is a compatibility aggregate view only,
> and version compounding flows through `wiki/` + `closeout.md` into `Vn+1`.

## 概述

本规格定义 `research-execution-skills` 的下一阶段协议升级：在现有 epoch schema、manifest-driven workspace、结构化 run report、audit hard gate 的基础上，把研究执行链升级为 gate-aware 的机器可验证合同。

当前系统已经具备 `epoch_v1_manifest.yaml`、`research_workspace.py`、`update_state.py`、`research_loop.py`、audit checks 和 epoch schema 测试。该设计稿中的 `NEXT_ACTION.md`/单 active task 控制模型已经被当前实现淘汰；当前协议以 `RESEARCH_SPINE.yaml` + `rqs/RQxx/TASKS.yaml` 为执行真源，`TASK_QUEUE.yaml` 仅作兼容聚合视图，`wiki/` + `closeout.md` 负责版本 compounding。

本规格的核心目标是把：

```text
PRD -> RESEARCH_SPINE -> RQ-local TASKS -> RUN_REPORT -> AUDIT -> WIKI -> CLOSEOUT
```

固定为一条可验证、可审计、可阻断的文件协议。Codex / Claude Code 仍然是实际 executor；本仓库只提供文件系统协议、状态提交入口、证据格式、审计门禁和控制器规则。

## 目标

- 统一研究执行术语：只使用 Gate、Task、Harness、Audit、Insight，避免 milestone/gate 混用。
- 将 `TASK_QUEUE.yaml` 从 task-level 队列升级为 gate-aware 队列，显式记录 `current_gate`、`current_task`、`gates[].status`、`gates[].audit` 和 task/gate 状态枚举。
- 将 `NEXT_ACTION.md` 固化为单步不可发散指令，包含 active gate/task、objective、allowed files、forbidden actions、harness、completion contract 和 blocked protocol。
- 将 run report schema 升级为可证明执行来源、命令、退出码、stdout/stderr 摘要、artifact hash、环境、anti-mock 状态和 research interpretation boundary 的证据记录。
- 将 `update_state.py` 升级为 gate-aware 状态提交器，确保 task 完成不会直接越过 gate evaluation 或 audit。
- 引入失败分诊协议，严格区分 environment failure、execution failure、harness failure、spec gap、PRD ambiguity、research falsification candidate 和 confirmed research falsification。
- 引入 audit queue、insight index、human review request 和 paper claim ledger 的机器可读结构，支持负结果沉淀与人工接管。
- 将 `research_loop.py` 从 legacy deterministic controller 逐步升级为 PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION 编译器和 stale hash 控制器。
- 保持现有 manifest-driven epoch 架构，不新增独立 backend、数据库、常驻 daemon 或分布式实验调度系统。

## 非目标

- 不新增 Web backend、数据库队列、常驻服务、Docker/GPU 调度或远程实验资源管理。
- 不把 Paper、PPT、README、报告文本或聊天总结作为实验真源。
- 不允许 AI 在当前 epoch closeout 前自动创建 `Vn+1`。
- 不允许 mock、synthetic、toy、smoke-only 结果支持 paper claim 或 benchmark claim。
- 不允许 failed execution、dependency missing、timeout、OOM、测试脚本错误被解释为研究假设失败。
- 不在本阶段引入密码学签名、SLSA 级 attestation 或外部 provenance service；当前只要求 hash、git commit、run report 和 audit hard gate。
- 不重写现有 research skill family 的总体哲学；本规格只把已有 epoch loop 升级为更严格的 gate-aware 执行协议。

## 架构

系统继续采用文件协议架构：

```text
epoch_v1_manifest.yaml
  -> research_workspace.py
  -> Vn/PRD.md
  -> Vn/SPEC.yaml
  -> Vn/PLAN.md
  -> Vn/TASK_QUEUE.yaml
  -> Vn/NEXT_ACTION.md
  -> Codex / Claude Code 执行
  -> update_state.py
  -> Vn/runs/*.yaml
  -> Vn/AUDIT_QUEUE.yaml
  -> Vn/audits/*
  -> Vn/wiki/insight_index.yaml
  -> Vn/HUMAN_REVIEW_REQUESTS.yaml
  -> Vn/closeout.md
```

`epoch_v1_manifest.yaml` 仍是 epoch 结构声明源。新增 schema 字段必须优先进入 manifest 或由 manifest 引用的固定 schema 文档，不能在 README、模板和脚本中各自定义一套平行协议。

`SPEC.yaml` 是机器执行合同，不是 PRD 摘要。`PLAN.md` 是 Gate runbook，不允许新增 PRD/SPEC 未声明的 dataset、baseline、metric、claim、harness。当前执行模型中，`RESEARCH_SPINE.yaml` 是版本级 RQ 调度真源，`rqs/RQxx/TASKS.yaml` 是 RQ-local 执行真源，`TASK_QUEUE.yaml` 只是兼容聚合视图。

状态推进必须经过三个层级：

```text
Task outcome -> Gate evaluation -> Audit decision
```

task completed 只能说明执行单元完成；gate passed 必须由 gate pass condition 和 audit decision 共同确认。research falsification 只能在 harness 有效、输出有效、audit 排除代码/数据/指标缺陷后成立。

## 组件

### Terminology Protocol

职责：

- 在 README、PRD 模板、PLAN 模板、TASK_QUEUE 模板和 NEXT_ACTION 模板中统一术语。
- 禁止 milestone 作为机器字段；若需要面向人类说明，只能写为 “milestone is an informal alias for Gate”。

固定定义：

```text
Gate: 具有可证伪 pass/block/falsification 条件的研究阶段门禁。
Task: Gate 内最小可执行单元。
Harness: 验证 Task 的命令、输入、输出和判定协议。
Audit: Gate 或关键 Task 后的对抗性审查。
Insight: 从运行、阻断、失败、异常或负结果中沉淀的证据化知识。
```

### PRD Compile-Friendly Sections

职责：

- 将 PRD 第 11 章固定为 Gate Schedule。
- 将 PRD 第 12 章固定为 Harness and Acceptance Criteria。
- 明确 `pass_condition != block_condition != falsification_condition`。

PRD 第 11 章必须包含结构化 Gate Schedule 表，至少包括：

```text
Gate ID, Gate Name, Purpose, Hypothesis Tested, Required Inputs,
Required Outputs, Pass Condition, Block Condition, Falsification Condition,
Required Audit, Human Decision Required
```

PRD 第 12 章必须包含 Harness 表，至少包括：

```text
Task ID, Harness Type, Command, Timeout, Required Artifacts,
Success Predicate, Anti-mock Check, Reproducibility Check
```

### SPEC Execution Contract

职责：

- 将 `SPEC.yaml` 定义为机器执行合同。
- 绑定 PRD hash、Research Direction hash、research question、hypothesis、allowed claims、datasets、baselines、metrics、gates、harnesses 和 evidence contract。
- 明确 mock result 的允许用途和禁止用途。

必要字段建议进入 manifest 或 schema：

```yaml
schema_version: 2
epoch: V0
source_prd_hash: ""
research_direction_hash: ""
contract: {}
datasets: []
baselines: []
metrics: []
gates: []
evidence_contract: {}
anti_mock_policy: {}
```

### PLAN Gate Runbook

职责：

- 将 `PLAN.md` 从泛化 todo 改为 Gate runbook。
- 每个 Gate 必须有 objective、entry criteria、task list、exit criteria、audit required、pass/blocked/falsified 出口。

每个 Gate 必须包含三类出口：

```text
Exit: Pass
Exit: Blocked
Exit: Falsified
```

### TASK_QUEUE Gate State

职责：

- 表达 gate-level 状态和 task-level 聚合状态。
- 作为兼容视图投影当前 RQ-local runnable set，而不是充当唯一执行真源。

必要结构：

```yaml
schema_version: 2
epoch: V0
current_gate: G0
current_task: T_G0_001
gates:
  - gate_id: G0
    status: active
    tasks: []
    audit:
      required: true
      status: pending
      modes: []
tasks: []
```

task status enum：

```text
pending, active, completed, blocked, failed_execution, failed_harness, skipped
```

gate status enum：

```text
pending, active, audit_required, audit_failed, passed, blocked, falsified
```

### RQ-Local Execution Contract

职责：

- 让 executor 每轮从 `RESEARCH_SPINE.yaml` 选择 non-final RQ，并读取对应 `rqs/RQxx/TASKS.yaml` 的 active/runnable task。
- 允许正交 runnable RQ 并行推进；单个 blocked RQ 不阻塞其它 RQ。
- 明确 allowed files、forbidden actions、required steps、harness 和 completion contract 必须落在 RQ-local task 或其 run report 中。

禁止动作至少包括：

- 不修改 `RESEARCH_DIRECTION.md`。
- 不修改已批准 PRD，除非明确进入 PRD review flow。
- 不创建 `Vn+1`。
- 不更新 paper claim。
- 不把 failed execution 标记为 research falsification。

### Run Report Schema

职责：

- 记录每次 task 执行的可审计证据。
- 明确 task result 和 research interpretation 是否允许。

必要字段：

```yaml
schema_version: 2
epoch: V0
gate_id: G0
task_id: T_G0_001
executor: codex
started_at: ""
ended_at: ""
status: completed
git: {}
environment: {}
command: {}
stdout_summary: ""
stderr_summary: ""
artifacts: []
metrics: []
reproducibility: {}
anti_mock: {}
conclusion:
  task_result: pass
  research_interpretation_allowed: false
```

### Failure Triage Policy

职责：

- 在任何研究结论前强制分类失败。
- 防止 agent 把工程失败、环境失败或 harness 失败误判为研究假设失败。

分类：

```text
environment_failure
execution_failure
harness_failure
spec_gap
prd_ambiguity
research_falsification_candidate
confirmed_research_falsification
```

`confirmed_research_falsification` 只能在 adversarial audit 后成立。

### State Updater

职责：

- `update_state.py` 是唯一状态提交入口。
- 支持 `--gate-id`、`--harness-exit-code`、`--run-report`、`--artifact-hash-file`、`--failure-class`。
- 将所有 task outcome 映射为 gate-aware transition。

关键规则：

```text
completed task != passed gate
all tasks completed -> audit_required if audit.required
failed_execution -> repairable/blocker path
failed_harness -> harness repair or task failure path
research_falsification_candidate -> audit_required
confirmed falsification -> gate falsified + insight + human review
```

### Research Loop Compiler

职责：

- 将 `research_loop.py` 从阶段检测器升级为编译器和 stale hash 控制器。

编译步骤：

```python
compile_prd_to_spec()
compile_spec_to_plan()
compile_plan_to_task_queue()
compile_task_to_next_action()
```

stale 检查：

```text
PRD hash drift -> SPEC stale
SPEC hash drift -> PLAN stale
PLAN hash drift -> TASK_QUEUE stale
TASK_QUEUE active task drift -> NEXT_ACTION stale
```

### Audit Queue

职责：

- Gate 完成后生成明确的 audit queue。
- audit 输出必须机器可读。

`AUDIT_QUEUE.yaml` 必须记录：

```yaml
audits:
  - audit_id: A_G0_001
    gate_id: G0
    trigger: gate_completed
    modes: []
    status: pending
    required_for_gate_pass: true
    input_reports: []
    output: {}
```

audit result enum：

```text
pass, repair_required, human_review_required, falsification_confirmed
```

### Insight and Human Review

职责：

- 将负结果、异常、失败路径和 pivot candidate 结构化。
- 将人工接管点从自然语言说明升级为状态文件。

新增或强化文件：

```text
wiki/insight_index.yaml
HUMAN_REVIEW_REQUESTS.yaml
PAPER_CLAIM_LEDGER.yaml
```

`PAPER_CLAIM_LEDGER.yaml` 只能绑定已验证证据，不能从 mock run、prompt-only scaffold 或未审计 artifact 生成 claim。

## 数据流

### 初始化流

```text
research-init
  -> epoch_v1_manifest.yaml
  -> docs/research/RESEARCH_DIRECTION.md
  -> docs/research/CURRENT
  -> docs/research/V0/*
```

### PRD 到执行合同流

```text
Vn/PRD.md + RESEARCH_DIRECTION.md
  -> compile_prd_to_spec
  -> Vn/SPEC.yaml + source_prd_hash + research_direction_hash
```

若 PRD hash 改变，`SPEC.yaml` 必须 stale，不能继续执行旧 SPEC。

### SPEC 到计划流

```text
Vn/SPEC.yaml
  -> compile_spec_to_plan
  -> Vn/PLAN.md + source_spec_hash
```

PLAN 只能安排 SPEC 已声明的 Gate、Task、Harness、Dataset、Baseline、Metric、Claim。

### PLAN 到队列流

```text
Vn/PLAN.md
  -> compile_plan_to_task_queue
  -> Vn/TASK_QUEUE.yaml + source_plan_hash
```

TASK_QUEUE 记录 gate-level 与 task-level 状态。

### 队列到单步指令流

```text
Vn/TASK_QUEUE.yaml
  -> compile_task_to_next_action
  -> Vn/NEXT_ACTION.md
```

NEXT_ACTION 只表达当前 active task。

### 执行证据流

```text
Vn/NEXT_ACTION.md
  -> Codex / Claude Code 执行
  -> update_state.py
  -> Vn/runs/<task>_report.yaml
  -> Vn/TASK_QUEUE.yaml
  -> Vn/STATUS.yaml
  -> Vn/GIT_STATE.yaml
  -> Vn/LOOP_LOG.md
```

### Gate 审计流

```text
all tasks in gate completed
  -> gate status = audit_required
  -> AUDIT_QUEUE.yaml
  -> audits/<audit_id>/findings.yaml
  -> gate decision
```

### Insight 和 Closeout 流

```text
audit repair_required / falsification_confirmed / human_review_required
  -> wiki/insight_index.yaml
  -> HUMAN_REVIEW_REQUESTS.yaml
  -> closeout.md when epoch stops or completes
```

## 错误处理

- 如果 `TASK_QUEUE.yaml` 没有 `current_gate` 或 `current_task`，epoch validation 必须失败。
- 如果 active task 的 gate 不存在，epoch validation 必须失败。
- 如果 task status 不在枚举内，schema validation 必须失败。
- 如果 gate status 不在枚举内，schema validation 必须失败。
- 如果 task 标记为 `completed` 但缺少 run report、command、exit code 或 stdout/stderr 摘要，evidence audit 必须失败。
- 如果 task 修改代码但没有 TDD 或 harness 记录，audit 必须失败，除非 task type 明确是 documentation-only。
- 如果 task outcome 是 `failed_execution` 或 `failed_harness`，系统不得生成 research falsification。
- 如果出现 `research_falsification_candidate`，必须触发 audit，不得自动 closeout。
- 如果 audit 返回 `falsification_confirmed`，gate 标记为 `falsified`，写 insight，并生成 human review request。
- 如果 PRD/SPEC/PLAN/TASK_QUEUE hash 不匹配，控制器必须停止或重新生成下游文件，不能继续执行 stale next action。
- 如果 mock artifact 被 paper claim 引用，paper-binding audit 必须失败。
- 如果状态写入出现部分失败，必须写 blocker 并要求人工审查；不得继续推进 gate。

## 测试策略

### Schema Validation Tests

- `tests/test_epoch_schema_validation.py` 扩展 gate-aware 必填字段。
- 新增 fixture：缺失 `current_gate` 时 validation 失败。
- 新增 fixture：gate status 非法时 validation 失败。
- 新增 fixture：task status 非法时 validation 失败。

### Task Queue Transition Tests

- 新增 `tests/test_task_queue_gate_transitions.py`。
- 覆盖 active task completed 后同 gate 下一个 pending task 被激活。
- 覆盖 gate 所有 task completed 后 gate 进入 `audit_required`。
- 覆盖 audit not required 时 gate evaluation 可进入 `passed`。

### Update State Gate Flow Tests

- 新增 `tests/test_update_state_gate_flow.py`。
- 覆盖 `completed` 不直接标记 gate passed。
- 覆盖 `failed_execution` 进入 repair/blocker path。
- 覆盖 `failed_harness` 不触发 falsification。
- 覆盖 `research_falsification_candidate` 需要 audit。

### Stale Hash Detection Tests

- 新增 `tests/test_stale_hash_detection.py`。
- 覆盖 PRD drift 使 SPEC stale。
- 覆盖 SPEC drift 使 PLAN stale。
- 覆盖 PLAN drift 使 TASK_QUEUE stale。
- 覆盖 TASK_QUEUE drift 使 NEXT_ACTION stale。

### NEXT_ACTION Generation Tests

- 新增 `tests/test_next_action_generation.py`。
- 覆盖 active gate/task、allowed files、forbidden actions、harness、completion contract、blocked protocol 均被渲染。
- 覆盖不存在 active task 时生成 blocked next action，而不是空白或发散指令。

### Audit and Insight Tests

- 扩展 `tests/test_audit_checks.py`。
- 覆盖 missing run report、missing exit code、mock result supports paper claim、missing artifact hash、missing TDD evidence。
- 新增 insight index 和 human review request schema tests。

## 证据层映射 (Evidence Layer Mapping)

每个 Spec 必须明确标注其关键陈述所属的证据层。这保证 report 写作时不会混淆 "计划要做的" 和 "已经实现的"。

**证据层定义（来自 report brief）：**
- `source claim`: 外部资料、论文、标准、官方文档明确说了什么
- `design intent`: 本报告拟采用、拟建设、拟交付的目标态方案
- `repo-observed fact`: 当前仓库、系统或实验产物真实已经显示了什么
- `report synthesis`: 在以上证据基础上的综合判断、折中和建议

**映射表格：**

| Spec 章节 | 关键陈述 | 证据层 | 说明 |
|-----------|----------|--------|------|
| 概述 | 当前仓库已有 `epoch_v1_manifest.yaml`、`update_state.py`、`research_loop.py`、audit checks 和 epoch schema tests | `repo-observed fact` | 来自当前仓库文件结构和测试文件 |
| 概述 | 当前系统需要升级为 gate-aware 机器可验证合同 | `report synthesis` | 基于 brainstorming 结论和当前实现缺口的综合判断 |
| 目标 | `TASK_QUEUE.yaml` 需要支持 gate-level 状态 | `design intent` | 本规格计划实现的目标态协议 |
| 架构 | `epoch_v1_manifest.yaml` 仍是 epoch 结构声明源 | `repo-observed fact` + `design intent` | 当前已存在 manifest；后续新增字段仍应通过 manifest 收敛 |
| 组件 | `SPEC.yaml` 是机器执行合同，不是 PRD 摘要 | `design intent` | 本规格定义的执行合同边界 |
| 组件 | failed execution 不得被解释为 research falsification | `design intent` + `report synthesis` | 科研严谨性约束和失败分诊判断 |
| 数据流 | PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION 需要 hash stale 检查 | `design intent` | 计划实现的控制器行为 |
| 错误处理 | mock artifact 被 paper claim 引用时 audit 必须失败 | `design intent` | evidence contract 的硬门禁 |
| 测试策略 | 新增 gate transition、stale hash、NEXT_ACTION generation 测试 | `design intent` | 计划中的测试覆盖 |

**原则：**
- 本规格默认属于 `design intent`。
- 引用当前仓库已存在文件、脚本和测试时，标注为 `repo-observed fact`。
- 对协议复杂度、阶段拆分和优先级的判断，标注为 `report synthesis`。

## Report 对齐 (Report Alignment)

当前仓库没有 `docs/report` 工作区，因此本规格不绑定具体 report 章节，也不创建或修改 report 文件。

**对应章节：**
- Report 章节：N/A，当前仓库未提供 `docs/report`。
- Report 文件：N/A，当前仓库未提供 report workspace。

**进度追踪：**
- 实现前状态：`design intent`。
- 实现后状态：对应代码、模板和测试可标记为 `repo-observed fact`。
- 更新位置：若后续生成项目报告，应更新到“执行协议”“状态机控制”“审计门禁”“证据链管理”“失败分诊与负结果沉淀”章节。

**禁止：**
- 不要把本规格中的未来字段写成当前已实现事实。
- 不要把 mock、prompt-only scaffold 或未审计 artifact 写成实验结果。
- 不要把 gate-aware 设计当作已完成，除非有测试和 run report 证据。

## Harness 设计 (必需)

### 上下文工程

- **输入上下文**: 当前仓库文件结构、`README.md`、`docs/superpowers/specs/2026-05-12-epoch-schema-invariance-design.md`、`docs/superpowers/plans/2026-05-12-epoch-schema-invariance.md`、`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`、`research_workspace.py`、`update_state.py`、`research_loop.py`、现有 tests。
- **上下文组装**: 先读取 manifest 和共享 workspace helper，再读取 state updater 和 controller，最后读取测试，避免从 README 的理念描述直接推导实现状态。
- **上下文限制**: 不读取大型 artifacts；不把旧 legacy workspace 当作当前 epoch 真源；只读取 schema、模板、状态文件、测试和短日志摘要。

### 工具编排

- **可用工具**: Python 标准库、PyYAML、pytest、git CLI、现有 `validate_research.py`、`update_state.py`、`research_loop.py`、`audit_checks.py`。
- **输入验证**: 所有版本名必须匹配 `V\d+`；所有 gate id 必须匹配 `G\d+`；所有 task id 必须能映射到 gate；所有路径必须在 repo 内或当前 task allowed files 内。
- **输出解析**: YAML 为机器真源；Markdown 只作为人类阅读副本。stdout/stderr 不全文内联到状态文件，只记录摘要、路径和 hash。
- **错误处理**: CLI 返回非零退出码时必须写入 failure class、evidence path 和 proposed repair。不能静默降级为 warning。
- **超时管理**: schema validation 和 stale hash checks 必须是快速本地检查；长实验 timeout 由 task harness 声明。

### 验证循环

- **模式验证**: 使用 manifest 校验 epoch 文件、目录、YAML 必填字段、task/gate status enum、run report schema。
- **语义验证**: 校验 active gate/task 一致性、gate tasks 完成条件、audit required 状态、mock/paper claim 禁止关系、hash stale 关系。
- **测试断言**: 每个 gate transition、failure class、audit result、stale hash condition 至少有一个正向 fixture 和一个失败 fixture。
- **重试策略**: schema、evidence 和 audit 失败不自动重试；只有 harness 明确允许 retry 且 failure class 为 transient execution failure 时，executor 才可重试并记录 retry count。

### 成本预算

- **预算上限**: schema validation、state transition、hash stale detection 和 audit hard gate 应为本地 deterministic checks，token 成本为零。
- **熔断器**: 如果 run report、stdout/stderr 或 artifact 过大，只记录摘要、路径、size 和 sha256；超过阈值时 audit 提示 artifact too large，不复制全文。
- **成本跟踪**: Codex / Claude Code 的 LLM 成本由 executor runtime 记录；本协议只要求 run report 记录 executor、command、start/end time 和 evidence paths。

### 可观测性

- **执行追踪**: 每个 task 记录 task id、gate id、executor、command、exit code、stdout/stderr summary、artifact hash、changed files、git pre/post commit、failure class 和 research interpretation boundary。
- **指标**: gate pass rate、audit repair rate、completed task evidence completeness、stale hash detection count、mock claim violation count、human review request count。
- **评估标准**: 所有 epoch 通过 strict validation；所有 completed task 有 run report；所有 gate passed 都有 audit 或明确 audit-not-required 证据；paper claim ledger 无 mock 或 stale evidence。
- **告警**: P0 audit fail、hash stale、missing run report、mock claim violation、confirmed falsification、attempted Vn+1 before closeout 时必须阻断执行并要求人工审查。

## 开放问题

- `epoch_v1_manifest.yaml` 是否继续承载所有新增 schema，还是引入 manifest 引用的 `schemas/*.yaml`：建议短期保持 manifest 为唯一入口，但允许复杂 schema 拆到同目录并由 manifest 引用。
- task id 是否统一从 `TASK_001` 迁移到 `T_G0_001`：建议新增 gate-aware 格式，但需要兼容已有 fixture 和 legacy tests。
- `research_loop.py` 的编译器是否直接覆盖当前 default controller，还是先作为 `--gate-aware-controller` 实验模式：建议先实验模式，测试稳定后再设为默认。
- audit 是否允许 LLM adversarial review 作为补充：建议第一阶段只做 deterministic hard gate，LLM review 只能作为附加报告，不能替代机器检查。
- run report 是否强制记录完整 environment package lock hash：建议先记录 Python version、OS、lockfile hash；完整 dependency snapshot 可作为后续增强。
