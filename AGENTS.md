# AGENTS.md

Codex 每次工作先读：

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`

任务风格：

- Complete the active task.
- Run relevant tests if code changes.
- Record terminal/test evidence.
- Update research state files.
- Do not change research direction.
- Do not create paper results from unverified artifacts.
- Do not create Vn+1 before closeout.
- Git allowed: status, diff, log, add allowed files, commit current task, tag closeout / paper binding.
- Git forbidden unless explicitly authorized: git push, git reset --hard, git clean -fd, git rebase, checkout overwriting user changes, rewrite history, force push, deleting files outside task scope.

## 研究智能体行为契约

1. RQ 先于行动。研究问题。
2. 复现先于提出。已有工作。
3. 证据先于写作。数据、日志、表格或引用。
4. 手术式编辑。声明的目标文件。
5. 冲突暴露。停止并报告。
6. 长循环检查点。发生了什么变化。
7. 可见失败。明确标记。
8. 确定性工作属于脚本。脚本化。
9. 测试是证据而非装饰。验证预期。
10. 约定优于新奇。现有文件夹结构。
