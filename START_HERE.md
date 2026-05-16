# Start Here

本页是 `research-loop` 的新手入口。它只解释第一次使用时必须理解的路径；完整协议仍以 `README.md`、`skills/research*/SKILL.md` 和 validator 为准。

## 先回答四个问题

1. 我现在在哪里？

   如果你在 `/home/xyh/code/research-loop`，这里是框架仓库，只维护 skill、schema、controller、installer、测试和模板。不要在这里绑定具体 dataset、baseline、metric 或 paper claim。

2. 我应该先看哪个文件？

   下游研究项目先看 `docs/research/RESEARCH_DIRECTION.md`，再看 `docs/research/CURRENT` 指向的 `Vn/goal.md`。`goal.md` 是当前版本目标和依赖图，`TASK_QUEUE.yaml` 才是 task 调度真源。

3. 我现在该跑什么命令？

   已有 research workspace 时，先跑只读状态检查：

   ```bash
   python3 ~/.claude/skills/research-status/scripts/research_status.py --repo /absolute/path/to/project
   ```

   没有 workspace 时，用最小科学判断初始化：

   ```bash
   python3 ~/.claude/skills/research-init/scripts/init_research.py \
     --repo /absolute/path/to/project \
     --judgment-file /absolute/path/to/judgment.yaml \
     --force
   ```

4. 卡住以后看哪里？

   先看 `research-status` 输出顶部的 `Beginner Summary`。它会告诉你当前状态、缺什么、下一步动作和验证命令。再看 `Vn/runs/`、`Vn/audits/`、`Vn/HUMAN_REVIEW_REQUESTS.yaml`。

## 最小心智模型

```text
Direction  决定研究边界
Goal       决定当前 Vn 的长期目标
Task Queue 决定依赖边、可运行 task 集合和默认 active task
Evidence   决定哪些结果可以支持 claim
Audit      决定是否允许推进或绑定论文
Wiki       沉淀 human-reviewed insight，服务下一版 RQ
```

## 暂时不用先理解的内容

第一次使用时，不需要先读完所有 schema、paper binding、migration audit、legacy controller 和内部 compiler 细节。先让 `research-status` 告诉你当前状态，再按 `TASK_QUEUE.yaml` 中当前可运行 task 前进；默认串行，只有依赖满足且文件范围不冲突的正交任务才可并行。

## 不能省略的硬边界

- 不能把 mock、toy、smoke 或 prompt-only scaffold 当成 claim evidence。
- 不能让 paper 反推实验、baseline、metric 或结果。
- 不能把 AI draft insight 直接写成 durable knowledge；需要 human verdict。
- 不能在 `BASELINE_LOCK.yaml` 未 locked 或未显式 human-waived 时进入 reproduction、innovation 或 experiment task。

更多术语见 `GLOSSARY.md`。
