# Research Pipeline (RQ-Driven)

> 科研不是跑实验，而是按版本推进的 RQ 探索。
> 同一版本内多个 RQ 并行执行；版本结束后 insight compounding 驱动下一版本。

## 1. 核心原则

1. **版本是阶段**。每个版本（V0, V1, V2...）是一个独立的研究阶段，有明确的开始和 closeout。
2. **版本内 RQ 并行**。同一版本内的所有 RQ 独立执行，互不阻塞。没有 RQ 之间的 `depends_on`。
3. **版本间 insight compounding**。Vn 结束后，成功的 RQ、失败的 RQ、负结果都沉淀为 insight。人类审阅后，基于 insight 创建 V_{n+1} 的新 RQ 集合。
4. **实验失败 = RQ 证据状态变化**，不是任务失败。失败不会自动降级 claim，而是更新该 RQ 的终态。

## 2. 版本生命周期

```
V0 初始化
    │
    ▼
RESEARCH_SPINE.yaml 定义一组 RQ（RQ01, RQ02, RQ03...）
    │
    ▼
所有 RQ 并行执行各自的 g0 → g1 → g2 → g3 生命周期
    │
    ├─ RQ01 → completed / blocked / scope_contracted / hypothesis_weakened
    ├─ RQ02 → completed / blocked
    └─ RQ03 → scope_contracted
    │
    ▼
所有 RQ 到达终态 → 版本进入 closeout
    │
    ▼
Agent 汇总证据 → wiki/（epoch_summary, evidence_map, positive_signals, negative_results, failed_paths, next_version_seed）
    │
    ▼
等待人类介入审阅：
- 哪些 insight 有价值？
- 失败 RQ 的 negative result 是否 first-class？
- 下一版本的核心问题是什么？
    │
    ▼
人类确认 → closeout.md 锁定
    │
    ├─ paper_binding_ready? → 进入 PAPER_BINDING_DECISION.md
    └─ create_next_version? → 基于 V0 insight 生成 V1 RESEARCH_SPINE.yaml
         │
         ▼
    V1 初始化（compounding 完成）
```

## 3. RQ 生命周期（版本内）

每个 RQ 在自己的轨道上独立运行：

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
| `completed` | 结论锁定，该 RQ 的贡献进入版本 wiki |
| `scope_contracted` | 方法仍有效，但适用范围缩小。贡献进入 wiki |
| `hypothesis_weakened` | 核心假设被轻微削弱，仍可继续。贡献进入 wiki |
| `blocked` | 核心假设被 falsified。negative result 进入 wiki |

**关键规则**：一个 RQ 进入 `blocked` **不阻塞**其他 RQ。版本继续，直到所有 RQ 都到达终态。

## 4. 实验执行子流程（g3_experiment）

```
Pre-flight（语法 + mock + smoke）
    │
    ├─ 不过 → 修代码 → 重跑（RQ 状态不变: g3_experiment）
    │
    └─ 通过 → L3 Full Experiment
                │
                ├─ 成功 → 证据进入 RQ → 检查 evidence_sufficient?
                │            ├─ 是 → RQ 状态: completed
                │            └─ 否 → 继续该 RQ 的下一个实验
                │
                └─ 失败 → Worker 产出 failure_report，返回 Controller
                             │
                             ├─ Controller 判断: 代码 bug? → 修代码重跑
                             │
                             └─ Controller 判断: 方法相关? → 按需 spawn Reviewer
                                        │
                                        Reviewer 回答:
                                        "该失败是否 contradict 当前 RQ 的核心假设?"
                                        │
                                        ├─ 不影响假设，仅场景不适用
                                        │      → Controller 标记: scope_contracted
                                        ├─ 轻微削弱假设
                                        │      → Controller 标记: hypothesis_weakened
                                        └─ 核心假设被 falsified
                                               → Controller 标记: blocked
```

## 5. 版本结束与 Insight Compounding

当版本内所有 RQ 都到达终态（completed / blocked / scope_contracted / hypothesis_weakened）：

1. **Agent 自动汇总**到 `wiki/`：
   - `epoch_summary.md`：原始信念 vs 实际发现
   - `evidence_map.md`：每个 claim 的证据级别
   - `positive_signals.md`：值得保留的现象
   - `negative_results.md`：被削弱或反驳的假设
   - `failed_paths.md`：跑不通的路径及原因
   - `next_version_seed.md`：下一版本的建议

2. **等待人类审阅**：
   - Agent 不能自动创建 V_{n+1}
   - 人类决定：哪些 insight carry forward？是否创建下一版本？是否 paper binding？

3. **Compounding**：
   - 若创建 V_{n+1}：基于 Vn wiki 生成新的 `RESEARCH_SPINE.yaml`，定义新的 RQ 集合
   - 若 paper binding：人类确认哪些 claim 允许进入论文

## 6. 产出规范

- **Worker 产出** = `{bounded_goal}_output.md` + 代码/数据 diff + 日志。必须标注"这是对 RQ-X 的证据贡献"。
- **Failure report** = 日志 + 复现步骤 + pre_flight 结果。Worker 不判断失败性质，只陈述事实。
- **Reviewer 产出** = 只读日志的审查结论，不产出代码。
- **版本 wiki** = Agent 自动汇总，人类审阅确认。

## 7. 跨平台执行

- **Hermes**：Controller 读 `STATUS.yaml` + `RESEARCH_SPINE.yaml` → 用 `delegate_task` spawn Worker / Reviewer。
- **Claude Code**：Controller 读状态文件 → 用 `@agent` 或 subagent spawn Worker / Reviewer。
- **OpenCode**：Controller 读状态文件 → 用 agent tool spawn Worker / Reviewer。

行为契约写在本文件和 `AGENTS.md` 中，各平台用自己的工具实现，不绑定特定语法。
