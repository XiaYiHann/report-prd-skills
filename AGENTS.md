# AGENTS.md

本仓库是 `research-loop` 元框架仓库，不承载具体 project-research。
`docs/research/` 只允许保存框架方向、tracked agent policy 或模板说明；
不得把本仓库当作下游研究项目来绑定 dataset、baseline、metric、paper claim 或
active epoch。

Codex 每次工作先读：

1. `docs/research/RESEARCH_DIRECTION.md`（若存在）
2. `README.md`
3. `skills/research*/SKILL.md` 中与当前任务相关的技能说明
4. `skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
5. 相关测试文件

任务风格：

- Complete the requested framework maintenance task.
- Run relevant tests if code changes.
- Record terminal/test evidence.
- Do not create or require repo-local `docs/research/CURRENT` or `docs/research/Vn/`.
- Do not import concrete project-research content into this repository.
- Do not create paper results, benchmark claims, dataset claims, or baseline decisions for this repository.
- Git allowed: status, diff, log, add allowed files, commit current framework task, tag framework release.
- Git forbidden unless explicitly authorized: git push, git reset --hard, git clean -fd, git rebase, checkout overwriting user changes, rewrite history, force push, deleting files outside task scope.

## 执行契约（6 条）

1. **RQ 是主线**。所有工作必须绑定到某个 RQ，每个产出必须明确"这是对哪个 RQ 的证据贡献"。
2. **角色分离，但都是 agent**。Controller 读 `STATUS.yaml` + `RESEARCH_SPINE.yaml`，识别活跃 RQ，调度任务，管理状态。Worker 执行分配任务（coding / experiment / analysis），不碰状态文件。Reviewer 按需由 Controller 临时 spawn，只读日志，判断失败是否影响 RQ 核心假设。
3. **Worker 执行，不决策**。Worker 实验失败后产出 failure_report 并返回，**不得自行判断失败性质**（不能标记 blocked / completed / method_validity）。
4. **版本内 RQ 并行，版本间 insight compounding**。同一版本内所有 RQ 独立执行，一个 RQ 的 blocked 不阻塞其他 RQ。版本结束后 Agent 汇总 wiki，等待人类审阅后决定是否创建下一版本。
5. **Pre-flight 不可绕过**。任何 L3 实验前必须先通过脚本检查（语法 + mock + smoke），过滤代码 bug 导致的伪失败。
6. **方法论文主张不因单个 RQ 失败而降级；负结果是第一等公民**。`paper_type: method` 时，单个 RQ 的 `blocked` 只更新该 RQ 的 evidence_state，不代表方法整体无效。所有终态 RQ（completed / blocked / scope_contracted / hypothesis_weakened）的产出都必须进入 `wiki/`，不得丢弃。
