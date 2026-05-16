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
