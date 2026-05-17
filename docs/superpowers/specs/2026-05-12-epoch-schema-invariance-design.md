# Epoch Schema Invariance 设计规格

> Historical design snapshot. Superseded by the current RQ-driven pipeline:
> `RESEARCH_SPINE.yaml` is the version-level scheduling truth,
> `rqs/RQxx/TASKS.yaml` is the RQ-local execution truth,
> `TASK_QUEUE.yaml` is a compatibility aggregate view only,
> and version compounding flows through `wiki/` + `closeout.md` into `Vn+1`.

## 概述

本规格定义 `research-loop` 技能族的 epoch 版本一致性与可审计执行协议。目标是保证 `docs/research/V0`、`docs/research/V1`、`docs/research/V2` 等每一个研究版本都是同一个协议模板下的实例，而不是每一轮临时生成一套不同结构。

当前系统面向 Codex 和 Claude Code 使用，因此不要求新增独立常驻 backend。真实执行后端由 Codex / Claude Code 承担；技能族负责提供文件系统协议、状态提交入口、证据记录格式和审计门禁。系统不能把 prompt-only scaffold、计划性文本或未验证 artifact 当作实验结果。

## 目标

- 所有 `Vn/` epoch 目录必须使用严格一致的文件集合、目录集合、字段集合和状态机协议。
- 新版本只能通过统一模板工厂创建，不能通过复制旧版本目录后手工删改得到。
- `validate_research --mode epoch-ready` 必须能检测所有版本是否符合统一 epoch schema，并在不一致时返回失败。
- Codex / Claude Code 执行任务后的证据必须通过结构化 run report 进入状态系统。
- audit 必须从“生成审计文档”升级为可失败的 hard gate，至少覆盖 epoch 结构、证据完整性、paper binding 和 carry_forward。
- legacy 路径只能作为 migration 输入，不能继续作为当前 epoch 执行真源。

## 非目标

- 不实现独立 Web backend、队列服务、数据库服务或常驻 daemon。
- 不在本阶段实现 Docker / GPU 调度 / 分布式实验资源管理。
- 不在本阶段实现密码学私钥签名；近期只要求 hash、git commit、dirty tree 和结构化 run report。
- 不让系统自动修改 `RESEARCH_DIRECTION.md` 或自动决定研究方向 pivot。
- 不允许为了兼容旧项目而降低新 epoch schema 的一致性要求。

## 架构

系统采用“统一 schema + 模板工厂 + 验证器 + 状态提交器 + 审计检查器”的架构。

`epoch_v1_manifest.yaml` 是 epoch 结构的唯一声明源。`research-init` 和后续 `create_epoch.py` 必须从该 manifest 创建 `Vn/`。`validate_research.py` 必须从同一个 manifest 校验所有 `Vn/`。任何新增文件、字段或 wiki 文件，都必须先进入 manifest 或明确进入下一版 schema。

Codex / Claude Code 不被系统包装成 backend，而被定义为 agent executor。当前执行模型是：controller 从 `RESEARCH_SPINE.yaml` 识别 non-final RQ，并读取对应 `rqs/RQxx/TASKS.yaml` 的 runnable task；`TASK_QUEUE.yaml` 仅保留为兼容聚合视图；执行完成后调用 `update_state.py` 提交任务状态、命令、测试、stdout/stderr 路径、artifact hash、git commit 和 blocker 信息。

audit 只读当前研究工作区，并输出结构化 PASS/WARN/FAIL。任何 P0 hard gate 失败都必须阻止 paper binding 和 closeout promotion。

## 组件

### Epoch Manifest

路径建议：

```text
skills/research-init/_shared/schema/epoch_v1_manifest.yaml
```

职责：

- 声明每个 `Vn/` 必须包含的文件。
- 声明每个 `Vn/` 必须包含的目录。
- 声明 `wiki/` 必须包含的固定文件集合。
- 声明 `STATUS.yaml`、`SPEC.yaml`、`TASK_QUEUE.yaml`、run report 的必要字段。
- 声明 schema 版本，例如 `epoch_v1`。

### Epoch Template Factory

职责：

- 初始化 `V0/`。
- 在当前版本 closeout 后创建 `Vn+1/`。
- 保证新版本结构来自 manifest，而不是从旧版本目录直接复制。
- 只允许继承 closeout summary、negative results、failed paths、accepted carry_forward artifacts、baseline notes、literature notes 和 next version seed。

### Epoch Validator

职责：

- 校验 `CURRENT` 指向的版本存在。
- 校验所有 `Vn/` 都满足 `epoch_v1_manifest.yaml`。
- 校验 `STATUS.yaml.version`、`SPEC.yaml.version`、`TASK_QUEUE.yaml.version` 与目录名一致。
- 校验每个版本的 wiki 文件集合完全一致。
- 校验未 closeout 的版本之前不能创建 `Vn+1`。
- 校验 legacy 路径不参与当前 epoch 的执行真源判断。

### State Updater

职责：

- 作为 Codex / Claude Code 完成任务后的唯一状态提交入口。
- 更新 `TASK_QUEUE.yaml`、`LOOP_LOG.md`、`GIT_STATE.yaml`、`STATUS.yaml`、`runs/TASK_XXX_report.yaml` 和 `NEXT_ACTION.md`。
- 接收并记录 executor、commands、stdout/stderr、exit code、test output、artifact hash、files changed、commit hash 和 blocker reason。

### Audit Checks

职责：

- 以检查器集合形式执行 hard gate。
- 每个检查返回 `check_id`、`status`、`severity`、`message` 和相关路径。
- 对 P0 失败返回非零退出码。
- 输出可被人阅读的 audit report，也输出机器可读 YAML / JSON。

## 数据流

初始化数据流：

```text
epoch_v1_manifest.yaml
  -> init_research.py
  -> docs/research/RESEARCH_DIRECTION.md
  -> docs/research/CURRENT
  -> docs/research/V0/*
```

新版本创建数据流：

```text
Vn/closeout.md + Vn/wiki/next_version_seed.md
  -> create_epoch.py
  -> epoch_v1_manifest.yaml
  -> Vn+1/*
```

任务执行数据流：

```text
Vn/NEXT_ACTION.md
  -> Codex / Claude Code 执行任务
  -> update_state.py 提交结构化证据
  -> Vn/runs/TASK_XXX_report.yaml
  -> Vn/TASK_QUEUE.yaml / STATUS.yaml / GIT_STATE.yaml / LOOP_LOG.md
  -> Vn/NEXT_ACTION.md 更新到下一任务
```

审计数据流：

```text
docs/research/*
  -> validate_research.py / audit_checks.py
  -> audits/<date>/audit_results.yaml
  -> PASS/WARN/FAIL
  -> closeout / paper binding gate
```

## 错误处理

- 如果 `CURRENT` 指向不存在的版本，`epoch-ready` 必须失败。
- 如果任意 `Vn/` 缺少 manifest 要求的文件或字段，`epoch-ready` 必须失败。
- 如果 `Vn+1` 在 `Vn` closeout 前出现，`epoch-ready` 必须失败。
- 如果 task 标记为 `done` 但缺少 run report、exit code、artifact hash 或必要测试证据，`evidence` audit 必须失败。
- 如果 paper binding 引用了 prompt-only scaffold、旧版本 artifact 且未声明 carry_forward，`paper-binding-ready` 必须失败。
- 如果状态更新过程中出现部分写入风险，必须至少写入 blocker，并要求人工审查；后续优化可以引入事务日志或 SQLite，但不是本规格第一阶段目标。

## 测试策略

- 增加 fixture：`V0` 完整、`V1` 缺少 `SPEC.yaml` 字段，验证 `epoch-ready` 失败。
- 增加 fixture：`V1` 多出未声明协议文件，验证 strict mode 失败或显式 WARN，具体行为由 manifest policy 决定。
- 增加 fixture：`V1` 从 `V0` 复制了 completed task queue，验证新版本创建检查失败。
- 增加 fixture：task `done` 但 run report 没有 exit code，验证 evidence audit 失败。
- 增加 fixture：paper binding 引用 `docs/research/V0/artifacts/*`，但当前 `V1/SPEC.yaml` 没有 carry_forward，验证失败。
- 保留现有安装与 scaffold 测试，确保 `init_research.py` 仍能生成完整 `V0`。

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
| 概述 | 系统面向 Codex / Claude Code 使用，不需要独立常驻 backend | `report synthesis` | 基于用户明确约束和当前技能族形态的综合判断 |
| 概述 | 当前仓库已有 `research_loop.py`、`update_state.py`、`validate_research.py` 等脚本 | `repo-observed fact` | 来自当前仓库文件结构 |
| 目标 | 所有 `Vn/` 必须结构同构 | `design intent` | 本规格定义的目标约束 |
| 架构 | `epoch_v1_manifest.yaml` 成为唯一 epoch 结构声明源 | `design intent` | 计划实现的结构约束 |
| 组件 | `update_state.py` 扩展为结构化证据提交入口 | `design intent` | 计划中的接口职责 |
| 错误处理 | schema 不一致必须 hard fail | `design intent` | 目标门禁行为 |
| 测试策略 | 使用 fixture 覆盖缺字段、旧 artifact、prompt-only scaffold 等失败场景 | `design intent` + `report synthesis` | 测试方案与风险判断 |

**原则：**
- 整个 Spec 默认属于 `design intent`。
- 涉及当前仓库已存在文件或脚本时，标注为 `repo-observed fact`。
- 对是否新增 backend、是否引入签名机制的取舍，标注为 `report synthesis`。

## Report 对齐 (Report Alignment)

此仓库当前没有 `docs/report` 工作区，因此本规格暂不绑定具体 report 章节。若后续生成项目报告，应将本规格对应到系统架构、执行协议、审计门禁和证据管理章节。

**对应章节：**
- Report 章节：N/A，当前仓库未提供 report 工作区。
- Report 文件：N/A，当前仓库未提供 `docs/report`。

**进度追踪：**
- 实现前状态：`design intent`
- 实现后状态：`repo-observed fact`
- 更新位置：若后续新增报告，建议更新到“架构设计”“执行协议”“审计机制”“证据链管理”相关章节。

**禁止：**
- 不要把 `design intent` 写成 `repo-observed fact`。
- 不要把未实现的 roadmap 伪装成已实现事实。

## Harness 设计 (必需)

### 上下文工程

- **输入上下文**: 当前仓库文件结构、`skills/research*` 脚本、现有 tests、用户确认的“Codex/Claude Code 是执行后端”和“所有 Vn 必须模板严格一致”要求。
- **上下文组装**: 先读取 manifest 或模板定义，再读取当前 `docs/research/CURRENT` 指向的 epoch，最后读取该 epoch 的状态文件和 task queue。
- **上下文限制**: validator 不读取大型 artifact 内容，只读取路径、hash、metadata、run report 和必要 YAML 字段；audit report 引用路径而不是复制完整输出。

### 工具编排

- **可用工具**: Python 标准库、PyYAML、git CLI、现有 `validate_research.py`、`update_state.py`、`research_loop.py`、未来的 `create_epoch.py` 和 `audit_checks.py`。
- **输入验证**: 所有版本名必须匹配 `V\d+`；所有路径必须位于 `docs/research` 或当前 task allowed files 内；所有 YAML 必须可解析。
- **输出解析**: validator 输出机器可读结果和人类可读摘要；run report 输出 YAML 为准，Markdown 只作为阅读副本。
- **错误处理**: 工具失败时返回非零退出码，并写明失败 check id、路径和修复建议。
- **超时管理**: schema validation 应为快速本地检查，不运行长实验；单次验证默认应在数秒内完成。

### 验证循环

- **模式验证**: 使用 `epoch_v1_manifest.yaml` 校验文件、目录、字段和 schema version。
- **语义验证**: 校验 `CURRENT`、版本字段、active task、NEXT_ACTION、carry_forward、paper binding evidence 的一致性。
- **测试断言**: 每个 hard gate 至少有一个正向 fixture 和一个失败 fixture。
- **重试策略**: schema 或 evidence 失败不自动重试；只有外部命令执行失败且 task 明确允许 retry 时，Codex / Claude Code 才可重试并记录 retry count。

### 成本预算

- **预算上限**: 本地 schema validation 和 audit 不应依赖 LLM；单次检查 token 成本为零。
- **熔断器**: 如果 audit 需要读取过大 stdout/stderr，应只读取摘要或 hash，并提示 artifact 过大。
- **成本跟踪**: Codex / Claude Code 执行成本由 agent runtime 记录；本规格只要求 run report 记录 executor、commands 和证据路径。

### 可观测性

- **执行追踪**: 每个 task 记录 task id、executor、commands、exit code、stdout/stderr、artifact hash、files changed、commit hash、status 和 blocker。
- **指标**: epoch schema pass rate、done task evidence completeness、paper binding claim coverage、carry_forward violations、prompt-only evidence violations。
- **评估标准**: 所有 `Vn/` 通过 strict epoch validation；所有 completed task 具备结构化证据；paper binding 无 hard gate 失败。
- **告警**: P0 audit FAIL、版本结构漂移、CURRENT 指针损坏、旧 artifact 未授权复用、prompt-only scaffold 被引用为结果时必须阻断。

## 开放问题

- 是否允许 `Vn/` 出现 manifest 之外的附加说明文件：建议第一阶段 strict fail，后续可增加 `allowed_extra_patterns`。
- 是否将多文件状态更新升级为事务日志或 SQLite：当前规格不要求，但如果出现部分写入导致状态损坏，应作为下一阶段设计。
- 是否需要 schema version migration 工具：短期建议只维护 `epoch_v1`，等首次 schema 变更再设计 migration。
- 是否把 audit checks 合并进 `validate_research.py`，还是独立为 `audit_checks.py`：两者都可行，但检查器函数应保持可单测。
