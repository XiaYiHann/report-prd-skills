# Research Pipeline (RQ-Driven)

> 科研不是跑实验，而是回答一个递进的问题链（RQ chain）。
> 每个实验只是某个 RQ 的证据收集手段。

## 1. 核心原则

1. **RQ 是主线**。所有工作（coding / experiment / analysis）必须绑定到某个 RQ。
2. **RQ compounding**。RQ1 的结论成为 RQ2 的前提；RQ2 的发现修正 RQ3 的设计。
3. **实验失败 = RQ 证据状态变化**，不是任务失败。失败不会自动降级 claim，而是触发状态更新。

## 2. RQ 生命周期（状态机）

```
draft → g0_search → g1_reproduce → g2_harness → g3_experiment → evidence_sufficient → completed
                ↑______________________________________________|
                |  failure: code bug → 修代码重跑（状态不变）
                |  failure: method related → review → scope_contracted / hypothesis_weakened / blocked
```

| 状态 | 含义 |
|------|------|
| `draft` | 只有问题，无证据 |
| `g0_search` | 文献/基线搜索中 |
| `g1_reproduce` | 基线复现中 |
| `g2_harness` | 实验框架（代码+测试）构建中 |
| `g3_experiment` | 实验执行中 |
| `evidence_sufficient` | 证据足以支撑该 RQ 的核心 claim |
| `completed` | 结论锁定，自动成为后续 RQ 的 compounding 输入 |
| `scope_contracted` | 方法仍有效，但适用范围缩小 |
| `hypothesis_weakened` | 核心假设被轻微削弱，仍可继续 |
| `blocked` | 核心假设被 falsified，compounding 链必须中断 |

## 3. Compounding 规则

- **RQ 完成**（`completed`）→ 自动激活所有 `depends_on: [该RQ]` 的 RQ。
- **RQ 阻断**（`blocked`）→ 自动冻结所有 `depends_on: [该RQ]` 的 RQ，请求人类决策。
- **RQ 收缩**（`scope_contracted`）→ 依赖它的 RQ 需要同步收缩 scope，但不冻结。

## 4. 实验执行子流程（g3_experiment）

```
Pre-flight（语法 + mock + smoke）
    │
    ├─ 不过 → 修代码 → 重跑（RQ 状态不变: g3_experiment）
    │
    └─ 通过 → L3 Full Experiment
                │
                ├─ 成功 → 证据进入 RQ → 检查 evidence_sufficient?
                │            ├─ 是 → RQ 状态: completed → 触发 compounding
                │            └─ 否 → 继续该 RQ 的下一个实验
                │
                └─ 失败 → Worker 产出 failure_report，返回 Controller
                             │
                             ├─ Controller 判断: 代码 bug? → 修代码重跑
                             │
                             └─ Controller 判断: 方法相关? → 按需 spawn Reviewer
                                        │
                                        Reviewer 回答:
                                        "该失败是否 contradict RQ 的核心假设?"
                                        │
                                        ├─ 不影响假设，仅场景不适用
                                        │      → Controller 标记: scope_contracted
                                        ├─ 轻微削弱假设
                                        │      → Controller 标记: hypothesis_weakened
                                        └─ 核心假设被 falsified
                                               → Controller 标记: blocked
                                               → 冻结后续所有 dependent RQ
```

## 5. 产出规范

- **Worker 产出** = `{bounded_goal}_output.md` + 代码/数据 diff + 日志。必须标注"这是对 RQ-X 的证据贡献"。
- **Failure report** = 日志 + 复现步骤 + pre_flight 结果。Worker 不判断失败性质，只陈述事实。
- **Reviewer 产出** = 只读日志的审查结论，不产出代码。

## 6. 跨平台执行

- **Hermes**：Controller 读 `STATUS.yaml` + `RESEARCH_SPINE.yaml` → 用 `delegate_task` spawn Worker / Reviewer。
- **Claude Code**：Controller 读状态文件 → 用 `@agent` 或 subagent spawn Worker / Reviewer。
- **OpenCode**：Controller 读状态文件 → 用 agent tool spawn Worker / Reviewer。

行为契约写在本文件和 `AGENTS.md` 中，各平台用自己的工具实现，不绑定特定语法。
