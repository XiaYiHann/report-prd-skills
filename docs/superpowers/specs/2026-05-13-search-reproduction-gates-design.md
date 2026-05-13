# Search and Reproduction Gates 设计规格

## 概述

本规格定义 `research-execution-skills` 的下一阶段协议升级：在已经落地的 gate-aware epoch execution protocol 基础上，把 search 和 reproduction 从辅助能力提升为每个研究 epoch 的强制前置门禁。

当前系统已经具备 Gate、Task、Harness、Audit、Insight、gate-aware `TASK_QUEUE.yaml`、结构化 `NEXT_ACTION.md`、run report、failure triage 和 audit hard gate。现存缺口不是缺少 “复现 baseline” 这个概念，而是 reproduction 与 search 尚未成为默认 epoch 编译链中的不可绕过条件。agent 仍可能在没有锁定 prior-work evidence substrate 的情况下进入 proposed-method experiment。

本规格的核心目标是把默认研究执行顺序固化为：

```text
Research Direction
  -> Vn PRD
  -> G0_SEARCH_LOCK
  -> G1_REPRODUCTION_LOCK
  -> proposed method mock / sanity run
  -> real data / model run
  -> fair baseline comparison
  -> closeout / next-version decision
```

这里的 reproduction gate 不要求所有 baseline 必须成功复现；它要求所有候选 baseline 的复现状态、证据等级、失败原因、可用于 claim 的边界都被结构化记录并通过 audit。这样既防止 agent 在没有 prior work 证据基础时过早实验，也避免第三方代码失效、数据缺失或论文细节不足把整个 research loop 永久卡死。

## 目标

- 将 `G0_SEARCH_LOCK` 和 `G1_REPRODUCTION_LOCK` 定义为每个 epoch 的默认前置 Gate。
- 将 search 从建议动作升级为 reproduction、baseline、dataset、model、metric、unexpected result、pivot proposal 和 paper binding 相关任务的 hard precondition。
- 将 reproduction 从 subagent 能力升级为 epoch-level execution contract 的必要组成部分。
- 新增 `docs/research/agent/SEARCH_POLICY.md`、`REPRODUCTION_POLICY.md` 和 `REPRODUCTION_AUDIT_POLICY.md`。
- 在 epoch manifest 中声明 `search/` 与 `reproduction/` 元数据文件，保持文件协议可初始化、可校验。
- 在 `SPEC.yaml` schema 中加入 `reproduction_contract` 与 `filesystem_contract`。
- 让默认 `TASK_QUEUE.yaml` 从 `G0_SEARCH_LOCK` 开始，而不是直接进入 PRD 后实验或普通 coding task。
- 让 `NEXT_ACTION.md` 在 `task.search.required=true` 时渲染 `Search Precondition`，并把 search log 作为 completion contract 的必要证据。
- 增加测试，验证 proposed-method experiment 不会在 search/reproduction gates 解决前成为 active task。

## 非目标

- 不在本阶段实现完整的复现项目管理系统。
- 不强制生成每篇论文的完整可执行目录树；第一轮只要求 metadata、index、policy、audit 和必要模板。
- 不要求每个 epoch 成功 full reproduce 固定数量的 baseline；失败可以被接受，但必须分类、记录、审计。
- 不新增 server、backend、数据库、daemon、远程实验调度器或 DVC/MLflow 依赖。
- 不自动 clone 外部仓库、不下载真实数据、不运行第三方复现实验。
- 不允许 mock-only、literature-only 或未审计 reproduction 支撑 paper claim。
- 不把 environment failure、dependency failure、timeout、OOM 或 harness failure 解释为方法失败或研究假设失败。
- 不在当前 epoch closeout 前自动创建 `Vn+1`。

## 架构

系统继续采用 file-based epoch protocol：

```text
epoch_v1_manifest.yaml
  -> research_workspace.py initializes Vn/
  -> Vn/SPEC.yaml declares reproduction_contract
  -> Vn/TASK_QUEUE.yaml starts at G0_SEARCH_LOCK
  -> Vn/NEXT_ACTION.md renders Search Precondition when required
  -> executor writes search logs / reproduction index / run reports
  -> update_state.py checks completion evidence
  -> audit validates reproduction claim boundary
```

默认 epoch 结构新增轻量元数据目录：

```text
docs/research/Vn/
  search/
    SEARCH_POLICY.md
    search_report.md
    web_search_log.yaml
    repo_search_log.yaml
    candidate_baselines.yaml
    candidate_reproductions.yaml

  reproduction/
    REPRODUCTION_INDEX.yaml
    REPRODUCTION_PLAN.md
    REPRODUCTION_DELTA.yaml       # Vn > V0 时生成；V0 可为空模板
```

可执行复现代码的推荐根目录是：

```text
reproduction/Vn/<PaperShortName_Year>/
```

但 P0 不强制初始化这些可执行目录。`docs/research/Vn/reproduction/` 是 metadata 和状态真源；根目录 `reproduction/Vn/` 是后续执行 workspace，只有当具体 reproduction task 真的开始时才创建。

## 组件

### Search Policy

职责：

- 定义哪些 task 必须 search。
- 定义 search 覆盖面：literature、official code、third-party code、datasets、model checkpoints、known issues/forks、current local repository。
- 定义 absence evidence：没有找到官方代码、数据或实现时，也必须记录查询、来源和置信度。
- 定义 bounded over-search：优先充分检索而非省 token，但必须有查询下限、上限和停止条件。

必要规则：

```text
Search is mandatory before:
- project start
- version start
- baseline selection
- reproduction
- dataset/model/metric selection
- unexpected positive or negative result
- pivot proposal
- paper binding

Search is not required for:
- local bug fix under locked SPEC
- rerunning the same harness
- formatting
- artifact path repair
- writing reports from existing logs
```

### Reproduction Policy

职责：

- 定义 reproduction type。
- 区分 official code、broken/stale official code、third-party code、faithful reimplementation、literature-only baseline。
- 明确 failed reproduction 的分类和可用性边界。
- 禁止把环境失败解释为方法失败。

必要 reproduction type：

```text
official_code
forked_official_code
third_party_code
faithful_reimplementation
analytical_baseline
literature_only_not_executable
```

必要 reproduction status：

```text
pending
search_done
planned
environment_ready
smoke_passed
small_scale_passed
full_passed
blocked_missing_code
blocked_missing_data
blocked_stale_dependency
blocked_ambiguous_algorithm
failed_metric_mismatch
failed_unexplained
excluded_by_human
```

必要 evidence level：

```text
official_full_reproduction
official_small_scale_reproduction
official_smoke_only
third_party_reproduction
faithful_reimplementation
analytical_baseline
literature_only
failed_but_informative
```

### Reproduction Audit Policy

职责：

- 对每个 reproduction item 回答固定审计问题。
- 判断 reproduction evidence 可以支持 paper claim、sanity check、discussion，还是完全不能支持。
- 将 reproduction failure 纳入 repair/human-review/failure-triage，而不是静默忽略。

审计必须输出：

```yaml
audit_result:
  repro_id: ""
  status: pass | repair_required | evidence_limited | reject
  claim_support_level: full | partial | sanity_only | none
  required_repairs: []
```

### SPEC Reproduction Contract

职责：

- 将 reproduction 规则编译进 `SPEC.yaml`。
- 定义 minimum reproduction evidence，而不是简单定义 minimum successful reproduction count。
- 定义 carry-forward policy，避免 V0 reproduction 自动支撑 V1 claim。

目标结构：

```yaml
reproduction_contract:
  required: true
  search_required_before_reproduction: true
  minimum_reproduction_evidence:
    closest_method_baseline_required: true
    strongest_reported_baseline_required: true
    simplest_classical_or_control_baseline_required: true
    failures_must_be_classified: true
    audit_required: true
  evidence_levels:
    official_full:
      can_support_claim: true
    official_small_scale:
      can_support_claim: partial
    faithful_reimplementation:
      can_support_claim: partial
    literature_only:
      can_support_claim: false
  carry_forward:
    allowed: true
    requires:
      - same_research_question
      - same_dataset_or_justified_proxy
      - same_metric
      - artifact_hash_available
      - audit_passed
```

### Filesystem Contract

职责：

- 明确状态文件、复现代码、实验代码、artifact 和 data manifest 的推荐位置。
- 防止 agent 把外部代码、日志、大 artifact、paper claim ledger 全部塞进 `docs/research`。

目标结构：

```yaml
filesystem_contract:
  state_root: docs/research/Vn
  search_metadata_root: docs/research/Vn/search
  reproduction_metadata_root: docs/research/Vn/reproduction
  reproduction_workspace_root: reproduction/Vn
  experiment_root: experiments/Vn
  artifact_root: artifacts/Vn
  data_manifest_root: data/manifests
  allowed_large_file_policy:
    commit_large_artifacts: false
    require_hash_manifest: true
    require_external_path_record: true
```

### TASK_QUEUE Default Gates

职责：

- 默认将新 epoch 的第一个执行 Gate 设为 `G0_SEARCH_LOCK`。
- 默认将 `G1_REPRODUCTION_LOCK` 设为 proposed-method experiment 前置 Gate。
- 保证 method experiment task 不会在 search/reproduction 解决前成为 active。

`G0_SEARCH_LOCK` 默认任务：

```yaml
gate_id: G0_SEARCH_LOCK
name: Search and Context Lock
order: 0
required: true
tasks:
  - task_id: T_G0_001
    title: Web search prior work and baselines
    type: literature_search
    search:
      required: true
  - task_id: T_G0_002
    title: Repository search for existing code/data/configs
    type: repo_search
    search:
      required: true
  - task_id: T_G0_003
    title: Lock candidate reproduction set
    type: reproduction_planning
    search:
      required: false
```

`G1_REPRODUCTION_LOCK` 默认任务：

```yaml
gate_id: G1_REPRODUCTION_LOCK
name: Reproduction Lock
order: 1
required: true
tasks:
  - task_id: T_G1_001
    title: Classify and plan selected reproductions
    type: reproduction_planning
    search:
      required: true
  - task_id: T_G1_999
    title: Audit reproduction evidence
    type: reproduction_audit
```

### NEXT_ACTION Search Precondition

职责：

- 对 `task.search.required=true` 的任务渲染硬性前置条件。
- 把 `web_search_log.yaml`、`repo_search_log.yaml`、`search_report.md` 或 absence evidence 纳入 completion contract。

目标段落：

```md
## Search Precondition

Search Required: yes

Before implementation or experiment execution:
1. Search web for official paper/project/code/data/model/metric evidence.
2. Search current repository for existing implementation, scripts, configs, tests, and prior notes.
3. Record queries, URLs, dates, commands, and findings.
4. Record absence evidence when official code/data/model cannot be found.
5. Continue only after search logs exist.
```

### Research-Literature and Research-Reproduce Agent Contracts

职责：

- `research-literature` 负责 candidate discovery，不负责随意挑 baseline 进入实验。
- `research-reproduce` 只从 locked `REPRODUCTION_INDEX.yaml` 执行或分类 reproduction item。
- 两者都必须读取 `SEARCH_POLICY.md` 与 `REPRODUCTION_POLICY.md`。

本阶段只更新 agent policy 文档和 README 描述，不要求实现新的 subagent runtime。

## 数据流

### Epoch 初始化

```text
research-init
  -> creates Vn/search/*
  -> creates Vn/reproduction/*
  -> creates default TASK_QUEUE with G0_SEARCH_LOCK active
  -> renders NEXT_ACTION for T_G0_001
```

### Search Lock

```text
T_G0_001 web/literature/code/dataset/model/metric search
  -> search/web_search_log.yaml
  -> search/search_report.md
  -> search/candidate_baselines.yaml
  -> search/candidate_reproductions.yaml

T_G0_002 local repo search
  -> search/repo_search_log.yaml

T_G0_003 reproduction set lock
  -> reproduction/REPRODUCTION_INDEX.yaml
  -> reproduction/REPRODUCTION_PLAN.md
```

### Reproduction Lock

```text
REPRODUCTION_INDEX.yaml
  -> reproduction planning/classification
  -> reproduction status / evidence level
  -> optional executable workspace under reproduction/Vn/
  -> reproduction audit
  -> gate pass / repair_required / human_review_required
```

### Method Experiment Unlock

```text
G0_SEARCH_LOCK passed
AND G1_REPRODUCTION_LOCK passed or human-waived
  -> proposed-method experiment tasks may become active
```

## 错误处理

- Web search unavailable: 写入 `search/search_blocker.md`，task 状态为 `blocked`，不得编造 paper、repo、dataset、metric 或 model capability。
- Official code not found: 记录 absence evidence，reproduction item 可进入 `blocked_missing_code` 或 `faithful_reimplementation` 路径。
- Dataset missing or restricted: 记录 `blocked_missing_data`，不得用 mock data 冒充真实数据。
- Dependency stale or environment broken: 记录 `blocked_stale_dependency`，不得解释为论文方法失败。
- Algorithm ambiguous: 记录 `blocked_ambiguous_algorithm`，请求 human decision：exclude、approximate、literature-only 或继续调查。
- Reproduction metric mismatch: 记录 `failed_metric_mismatch`，必须审计 metric definition、dataset split、preprocessing、seed 和 hardware/runtime 差异。
- Search log missing: `update_state.py` 或 audit 必须拒绝将 search-required task 标记为 completed。
- Reproduction audit failed: Gate 进入 `audit_failed` 或 `blocked`，不得激活 proposed-method experiment。

## 测试策略

- Schema validation：初始化 epoch 后必须存在 `search/`、`reproduction/` 元数据文件，且 `TASK_QUEUE.yaml` 包含 `G0_SEARCH_LOCK` 与 `G1_REPRODUCTION_LOCK`。
- NEXT_ACTION rendering：当 active task 的 `search.required=true` 时，`NEXT_ACTION.md` 必须包含 `Search Precondition`。
- Completion enforcement：缺失 required search logs 时，search-required task 不能被标记为 `completed`。
- Gate ordering：`G1_REPRODUCTION_LOCK` 未 passed 或 human-waived 前，proposed-method experiment task 不能成为 active。
- Reproduction index validation：invalid reproduction type、status、evidence level 必须被 schema validation 拒绝。
- Claim boundary audit：`literature_only`、`official_smoke_only`、`failed_but_informative` 不能支持 paper claim。
- Carry-forward check：`Vn>V0` 若声明 carry-forward，必须存在 same question/dataset/metric、artifact hash 和 audit pass 证据。
- Regression：既有 gate-aware tests、run report tests、audit tests 必须继续通过。

## 证据层映射 (Evidence Layer Mapping)

| Spec 章节 | 关键陈述 | 证据层 | 说明 |
|-----------|----------|--------|------|
| 概述 | 当前系统已有 gate-aware execution protocol | `repo-observed fact` | 基于仓库现有 spec、README 和最近 commit 的观察 |
| 概述 | search/reproduction 需要成为前置门禁 | `report synthesis` | 基于 brainstorming 结论与 reproducibility 实践的综合判断 |
| 目标 | 新增 policies、manifest 字段、default gates、NEXT_ACTION precondition | `design intent` | 本规格计划交付的协议层改动 |
| 非目标 | 不实现完整复现项目管理系统 | `design intent` | 明确收敛 P0 范围，避免过度工程 |
| 架构 | 使用 `docs/research/Vn/search` 与 `docs/research/Vn/reproduction` 存 metadata | `design intent` | 文件协议设计目标 |
| 架构 | 可执行复现代码推荐放 `reproduction/Vn` | `report synthesis` | 在状态轻量化与可执行 workspace 分离之间的折中 |
| 组件 | reproduction failure 必须分类，不能直接解释为 hypothesis falsification | `design intent` + `repo-observed fact` | 延续已落地 failure triage 协议 |
| 测试策略 | method experiment 不能早于 search/reproduction gates 激活 | `design intent` | 关键验收标准 |

## Report 对齐 (Report Alignment)

当前仓库没有 `docs/report/` 工作区，因此 report 对齐为 N/A。

对应章节：

- Report 章节：N/A
- Report 文件：N/A

进度追踪：

- 实现前状态：`design intent`
- 实现后状态：`repo-observed fact`
- 更新位置：若后续创建 project report，应在 “研究执行协议”、“复现门禁”、“证据链管理” 或 “失败分诊” 章节记录对应 commit SHA、测试命令和剩余风险。

禁止：

- 不要把本 spec 写成已经实现的事实。
- 不要把 search/reproduction policy 的目标态混同于当前仓库行为。
- 不要把未执行的 reproduction workspace 模板写成已完成复现实验。

## Harness 设计 (必需)

### 上下文工程

- **输入上下文**: `README.md`、既有 gate-aware spec/plan、`epoch_v1_manifest.yaml`、`research_workspace.py`、`update_state.py`、audit checks、相关 tests。
- **上下文组装**: 先读取当前协议真源和测试，再按 P0 范围映射需要修改的模板、schema、helper、docs 和 tests。
- **上下文限制**: 不读取外部论文全文；reproducibility 外部依据只作为 policy 设计背景，不复制进代码实现；不展开完整 reproduction executable workspace。

### 工具编排

- **可用工具**: `rg`/`sed`/`pytest`/`git diff`/`apply_patch`，以及必要时的 web search。
- **输入验证**: 写入前检查现有 spec、plan 和 README 术语，避免引入 `milestone` 或平行状态枚举。
- **输出解析**: pytest 输出必须记录通过/失败摘要；schema validation failure 必须定位到具体文件和字段。
- **错误处理**: 如果新增 policy 与现有 gate-aware enum 冲突，优先调整 policy；如果测试 fixture 依赖旧初始 task id，需要显式迁移测试期望。
- **超时管理**: 单次 pytest 子集优先运行，最终再运行全量 `python3 -m pytest tests -v`。

### 验证循环

- **模式验证**: `validate_epoch_schema()` 必须验证 search/reproduction metadata 和 reproduction enum。
- **语义验证**: audit checks 必须验证 search-required task 的 evidence、reproduction evidence level 和 paper claim boundary。
- **测试断言**: 新增 tests 覆盖 default gates、search precondition rendering、search log completion enforcement、reproduction index validation、method experiment unlock。
- **重试策略**: 先修 schema/template，再修 state transition，再修 audit；不得通过放宽测试断言掩盖协议缺口。

### 成本预算

- **预算上限**: 本 spec 不设置 token 成本硬上限；实现阶段应以 bounded search policy 控制外部检索。
- **熔断器**: 若实现阶段需要真实 clone、下载数据或运行第三方 reproduction，应停止并拆出后续 spec。
- **成本跟踪**: Search policy 应记录 query count、checked sources、absence evidence 和停止原因。

### 可观测性

- **执行追踪**: search logs 记录 query、timestamp、URL、source type、conclusion；repo search logs 记录 command、purpose、findings。
- **指标**: candidate baseline count、candidate reproduction count、classified reproduction count、audit pass/fail count、claim-supportable reproduction count。
- **评估标准**: proposed-method experiment 不能在 G0/G1 未 resolved 前激活；paper claim 不能引用 mock-only、literature-only、failed 或未审计 reproduction。
- **告警**: search unavailable、absence evidence insufficient、reproduction index missing、audit failed、paper claim uses unsupported evidence 时阻断 gate。

## 开放问题

- `G1_REPRODUCTION_LOCK` 是否允许 human waiver？本规格建议允许，但必须写入 `HUMAN_REVIEW_REQUESTS.yaml` 并由 audit 记录。
- `minimum_reproduction_evidence` 的默认数量是否应固定为 3，还是由 PRD/SPEC 根据领域决定？本规格倾向不固定成功数量，只固定 baseline role coverage。
- `REPRODUCTION_DELTA.yaml` 在 V0 是否生成空模板，还是只在 Vn>V0 生成？实现阶段可以选择更简单的一致模板策略。
- `research-literature` 和 `research-reproduce` 的 `.claude/agents/*.md` 是否在 P0 同步更新，还是作为 P1？本规格建议 P0 至少更新 policy 引用与 I/O 约束。
