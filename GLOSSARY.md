# Glossary

本术语表只解释 `research-loop` 新手最容易混淆的词。机器字段、schema key 和稳定 ID 仍以源码与 validator 为准。

## RQ

Research Question。它是一个可证伪、可执行、可被 evidence gate 检查的问题，不是泛泛的研究方向。

## PRD

当前版本的研究设计真源。新版 epoch 中 canonical PRD 是 `Vn/PRD.tex`，`PRD.pdf` 是审阅产物，`PRD_SUMMARY.md` 只是 agent context。

## Goal

`Vn/goal.md`。它描述整个版本的长期目标、RQ 计划/任务绑定、任务依赖图、并行边界和停止条件。它不是 task queue，也不是实验结果。

## Goal Lock

`Vn/GOAL_LOCK.yaml`。它记录 `goal.md` 依赖的 source hash。PRD、Spine、RQ-local contract 或 Task Queue 改动后，goal lock 可能 stale，需要刷新。

## Task Queue

`Vn/TASK_QUEUE.yaml`。它是 task 调度真源，记录每个 task 的状态、依赖、文件范围和证据要求。默认串行推进 active task；若依赖满足且文件范围不冲突，正交 runnable tasks 可以并行推进。

## Spine

`Vn/RESEARCH_SPINE.yaml`。它把 RQ、claim、experiment、evidence、figure/table 和 paper section 连接起来，防止 paper claim 脱离实验合同。

## Gate

推进条件。Gate 可以是 search lock、baseline lock、reproduction lock、evidence gate、audit gate 或 paper binding gate。Gate 未通过时不能把后续结论写成已验证事实。

## Evidence Gate

`Vn/EVIDENCE_GATE.yaml`。它决定 claim 是 draft、allowed 还是 forbidden。只有真实 artifact、命令、hash、audit 和 source/baseline lock 满足后，draft claim 才能升级。

## Baseline Lock

`Vn/BASELINE_LOCK.yaml`。它冻结当前版本的 baseline、dataset、metric 和 borrowed experiment design。它引用 `Vn/baselines/INDEX.yaml` 中的 dossier，而不是保存 raw search candidate。

## Run Report

`Vn/runs/TASK_XXX_report.yaml` 和 `TASK_XXX_report.md`。它们记录命令、退出码、stdout/stderr 摘要、artifact hash、测试和结论，是任务完成后的基本证据。

## Audit

跨文件一致性和证据资格检查。Audit 是 hard gate，不是文档润色步骤。P0/P1 audit failure 会阻断 closeout 或 paper binding。

## Insight

从真实 run、artifact、blocker、negative result 或 failed path 中解释出的研究认识。AI 可以 draft，进入 durable wiki 需要 human verdict。

## Wiki

`Vn/wiki/`。它保存 human-reviewed durable insight，包括 evidence map、negative results、failed paths、open questions 和 frontier map。

## Closeout

当前版本结束判断。Closeout 可以走成功、负结果、阻断、证伪、需要 pivot 或 stable。只有 closeout 完成后才考虑下一版或 paper binding。

## Paper Binding

把 allowed claim 绑定进论文表达层。它只能在 `closed_stable` 或 `paper_binding_ready` 后发生，并且需要 `PAPER_BINDING_DECISION.md` 明确批准。

## Mock / Toy / Smoke

只能用于 plumbing、unit 或 smoke check，不能支持 paper claim、full experiment、benchmark comparison、ablation 或 Go/No-Go 结论。
