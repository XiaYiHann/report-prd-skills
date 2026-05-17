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

## 研究智能体行为契约

1. RQ 先于行动。此处指框架要支持的研究协议问题，而不是本仓库绑定具体科研项目。
2. 复现先于提出。此处指框架行为、schema、validator 与脚本回归先于新抽象。
3. 证据先于写作。数据、日志、测试输出或审计样例先于文档宣称。
4. 手术式编辑。声明的目标文件。
5. 冲突暴露。停止并报告。
6. 长循环检查点。发生了什么变化。
7. 可见失败。明确标记。
8. 确定性工作属于脚本。脚本化。
9. 测试是证据而非装饰。验证预期。
10. 约定优于新奇。现有文件夹结构。
11. **角色分离（Role Separation）**：
    - **Controller（`research-controller`）是唯一状态管理者**：独占 `STATUS.yaml`、`TASK_QUEUE.yaml`、`EVIDENCE_GATE.yaml`、`PAPER_TYPE.yaml`、`METHOD_DEFENSE.yaml` 的写权限。Controller 不执行具体研究任务（不写实验代码、不跑训练、不做数据分析）。
    - **Specialist Subagents 只执行被分配的具体任务**：`research-experiment` 跑实验、`research-coding` 写代码、`research-audit` 做审查、`research-analysis` 做分析等。Specialist 不修改状态文件、不做调度决策、不自行判断 method validity。
    - **Method Defense Review 必须由独立 subagent 执行**：`research-audit` 作为 reviewer，`research-experiment` 作为执行者，Controller 作为调度者，三者互相制衡。
12. **Method Defense Gate 不可绕过（method paper 适用）**：若 epoch 的 `PAPER_TYPE.yaml` 声明 `paper_type: method`，任何实验失败后：
    - **Controller 接收 `research-experiment` 的 failure report 和 review package**。
    - **Controller spawn 独立 `research-audit` subagent** 做 review，输出 `runs/TASK_XXX_subagent_review.md`。
    - **Controller 按 review 结论更新状态**：若 `method_validity: maintained` 则调度下一个适用场景；若 `falsified` 则请求 human review。
    - **任何 specialist 不得擅自覆盖 review 结论**；如有异议，写入 `HUMAN_REVIEW_REQUESTS.yaml` 请求人类仲裁。
    - 最终 `METHOD_DEFENSE.yaml` 的 `reviewed_by` 字段必须为 `subagent`，`self` 被视为无效。
13. **TDD Protocol 不可绕过（所有 paper type 适用）**：任何 full experiment（L3）在首次运行前，必须先通过 L0（语法检查）、L1（公式/契约确定性测试）、L2（单 batch smoke）。L3 失败后自动回溯：若 L0-L2 从未运行 → 这是 Agent 违规，必须先补测试；若 L0-L2 通过但 L3 失败 → 由 Controller 调度 audit review。
