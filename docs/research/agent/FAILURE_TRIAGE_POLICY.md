# Failure Triage Policy

A failed task must be classified before any research conclusion is made.

## Classes

### 1. Environment Failure

- dependency missing
- CUDA/device unavailable
- file path invalid
- permission or local toolchain unavailable

### 2. Execution Failure

- script crash
- exception
- timeout
- OOM
- process exits before producing declared outputs

### 3. Harness Failure

- test predicate failed
- output missing
- artifact schema invalid
- success predicate cannot be evaluated

### 4. Spec Gap

- command undefined
- dataset unspecified
- metric not operationalized
- baseline source unclear
- allowed files or artifact paths missing

### 5. PRD Ambiguity

- research question unclear
- hypothesis is not falsifiable
- pass, block, or falsification condition missing
- Gate schedule or Harness table is underspecified

### 6. Research Falsification Candidate

Allowed only if:

- harness ran successfully;
- outputs are valid;
- artifacts and hashes are recorded;
- the result contradicts a predefined falsification condition;
- no execution, harness, environment, spec, or PRD ambiguity is still unresolved.

### 7. Confirmed Research Falsification

Allowed only after adversarial audit.

The audit must rule out code defects, data leakage, metric bugs, harness bugs, environment failures, and PRD/SPEC ambiguity before the gate can be marked `falsified`.

## State Mapping

`failed_execution` maps to environment or execution repair.  
`failed_harness` maps to harness repair or task-level failure.  
`research_falsification_candidate` maps to audit required.  
`confirmed_research_falsification` maps to gate `falsified` only after audit.

Never interpret `failed_execution` or `failed_harness` as confirmed research falsification.

---

## 7. Method-Related Failure → RQ 状态更新

> 详见 `PIPELINE.md` §4 "实验执行子流程"。
> 本节只保留 triage 入口，详细流程在 PIPELINE.md 中统一维护。

### 入口判断

当实验失败且排除 environment/execution/harness 修复后仍失败：

1. Worker 产出 `failure_report`（日志 + diff + pre_flight 结果），返回 Controller。
2. Controller 判断：是否涉及 RQ 核心假设？
   - 否（代码 bug）→ 修代码重跑（RQ 状态不变）。
   - 是 → 按需 spawn Reviewer。
3. Reviewer 只读日志，回答：**该失败是否 contradict 当前 RQ 的核心假设？**
   - 不影响假设，仅场景不适用 → Controller 标记 RQ: `scope_contracted`
   - 轻微削弱假设 → Controller 标记 RQ: `hypothesis_weakened`
   - 核心假设被 falsified → Controller 标记 RQ: `blocked`
  # blocked 只影响该 RQ，不阻塞版本内其他并行 RQ

### 硬规则

- Worker **不得**自行标记 `blocked` / `completed` / `method_validity`。
- Controller **不得**在 subagent review 完成前擅自更新 RQ 状态。
- 一个 RQ 进入 `blocked`**不阻塞**版本内其他 RQ 的继续执行。
- 方法论文的 stop 条件：**subagent review 结论为 falsified** 或 **人类显式喊停**，不是"失败两次"。
