# research-execution-skills

`research-execution-skills` 是一组面向 Claude Code / Codex 的研究执行技能。它不再是通用的 `report PRD` 工具，而是把一个研究想法推进成可执行研究工作区：

```text
Research PRD   = 人类研究真源
Research Paper = 从 PRD 派生的学术论文表达
Research Spec  = 从 PRD 编译出的全局机器执行合同
Research Plan  = 从 Spec 派生的 dated 具体执行计划
Research Audit = PRD / Paper / Spec / Plan / PPT / artifacts 的漂移审计
Research PPT   = 面向 Codex + ImageGen 的 PNG/PDF 幻灯片图像工作流
```

核心原则：执行权只属于 `docs/research/spec/`。不能从论文正文反推实验、数据集、基线、指标、seed、任务、harness 或结果。

## Unified `/research` Loop

`/research` 是默认入口。用户完成并人工批准 Research PRD 后，统一控制器会检查 `docs/research/`，用文件系统事实重算当前阶段，并按 PRD / Spec / Plan / Harness / Audit / Insight 约束推进项目。

标准循环：

1. 用户填写 Research PRD，并加入 `PRD_STATUS: HUMAN_APPROVED`。
2. `/research` 检查 PRD readiness；未批准或缺少 RQ、证伪条件、benchmark、实验、dataset、baseline、metric、harness 时停止。
3. PRD ready 后，`/research` 编译或修复 `docs/research/spec/`。仅当缺口是 PRD-compatible 的执行细节时自动修；如果需要决定数据集、baseline、metric、核心 RQ 或主 claim，则写入 `docs/research/audits/YYYY-MM-DD-prd-review/` 并停止。
4. Spec ready 后，`/research` 创建或更新 `docs/research/plans/plan_queue.yaml`，选择最高优先级 pending entry，生成下一份 dated plan。
5. 执行阶段只按 Plan 和 Spec 的最早 gate 推进。当前脚本实现是 deterministic file controller：它会写状态、计划、prompt、反馈和 audit，但不会伪造 harness stdout/stderr 或实验 artifact。
6. 计划完成或阻塞后，`/research` 写 `docs/research/spec/feedback/`、追加 insight log，并生成 audit。
7. 失败会被分类为 Execution Failure、Spec Gap、PRD Ambiguity 或 Research Falsification / Insight Trigger。PRD ambiguity、核心假设失败、open pivot proposal 和未解决负结果都会阻断自动执行并请求人类审查。
8. Paper / PPT 是表达层，只能从 PRD、Spec 和已验证 artifacts 更新；不得从论文反推实验，也不得填入未验证结果。

旧的分技能仍可手动使用：`research-prd`、`research-paper`、`research-spec`、`research-plan`、`research-audit`、`research-ppt`。但自动托管研究项目时，默认先运行 `/research`。

执行 backend 目前显式保守：

```text
--executor prompt-only   # 当前已实现
--executor local-shell   # 预留，尚未执行 harness
--executor codex         # 预留
--executor hermes        # 预留
```

除 `prompt-only` 外，backend 槽位只记录意图，不代表已经能真实执行 shell、Codex goal 或 Hermes 任务。

初始化产物不是空 `TODO` 骨架。`research-init` 会生成中文顶级 Research PRD 模板：LaTeX 是真源，使用 `ctex`、TikZ、`booktabs`、`tabularx` 组织图表；Markdown 是伴随审阅稿。它也会生成 planned top-conference paper 模板和 Spec 执行合同模板。若本机有 `latexmk` 或 `xelatex`，脚本会真实渲染 PDF；否则写入中文 `render_blocker.md`，不会伪造 PDF。

## 安装与迁移

一行在线安装：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh | bash
```

安装到自定义技能目录：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh \
  | RESEARCH_EXECUTION_SKILLS_TARGET_DIR=/path/to/.agents/skills bash
```

从本地 checkout 安装：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" bash install.sh
```

默认目标目录是：

```text
~/.agents/skills
```

安装脚本还会把 `research` 和所有 `research-*` 技能从 `~/.agents/skills/` 软链接到 Claude Code 的默认技能目录：

```text
~/.claude/skills
```

如果需要自定义 Claude Code 技能目录：

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" \
RESEARCH_EXECUTION_SKILLS_CLAUDE_TARGET_DIR=/path/to/.claude/skills \
bash install.sh
```

如果主要在 Claude Code 中使用，并希望安装项目级 research subagents：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh \
  | bash -s -- --with-subagents

# 或从本地 checkout 安装
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR="$PWD" bash install.sh --with-subagents
```

这会从 repo 模板目录复制：

```text
agents/claude-code/*.md
```

到当前项目的 Claude Code 标准 subagent 目录：

```text
.claude/agents/
```

可用环境变量改写目标目录：

```bash
RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR=/path/to/project/.claude/agents \
bash install.sh --with-subagents
```

第一版安装 9 个 Claude Code project-level subagents：`research-math`、`research-literature`、`research-reproduce`、`research-coding`、`research-experiment`、`research-analysis`、`research-paper`、`research-ppt`、`research-audit`。这些文件是 Claude Code 原生的 Markdown + YAML frontmatter 格式；不要把自定义 registry 当成主 subagent 定义格式。

安装脚本会执行迁移：

- 安装新的 `research-*` 技能族。
- 用一个很小的 legacy `report` router 替换旧 `report` 入口，仅用于提示迁移方向。
- 删除旧的 `report-init`、`report-update`、`report-audit`、`report-goal`、`report-paper`、`report-spec`、`report-brainstorming` 等旧技能目录。
- 删除不应存在的 `research-evidence`、`research-writing`、`research-goal`。
- 兼容旧环境变量 `REPORT_PRD_SKILLS_SOURCE_DIR`、`REPORT_PRD_SKILLS_TARGET_DIR`、`REPORT_PRD_SKILLS_REPO_URL`、`REPORT_PRD_SKILLS_REF`，但推荐新环境变量 `RESEARCH_EXECUTION_SKILLS_*`。

迁移后，目标目录里应主要看到：

```text
report/              # legacy migration warning only
research/            # unified autonomous controller
research-init/
research-prd/
research-paper/
research-spec/
research-plan/
research-audit/
research-ppt/
```

## 技能列表

| Skill | 用途 |
|---|---|
| [`research`](skills/research/SKILL.md) | 默认统一入口：检查 `docs/research/`，维护 state/queue，推进 PRD、Spec、Plan、执行提示、Audit、Insight、Paper/PPT 边界。 |
| [`research-init`](skills/research-init/SKILL.md) | 初始化 `docs/research/`，创建中文 LaTeX 真源 Research PRD、paper、spec、plans、audits、ppt scaffold。 |
| [`research-prd`](skills/research-prd/SKILL.md) | 维护专业 Research PRD，面向能够执行项目但未必熟悉完整背景的硕士生，默认图文并茂。 |
| [`research-paper`](skills/research-paper/SKILL.md) | 从 PRD 生成和打磨 planned NeurIPS / ICLR / AAAI 风格论文，并强制实验结果 placeholder 绑定。 |
| [`research-spec`](skills/research-spec/SKILL.md) | 把 PRD 编译成全局执行合同：数据集、基线、复现目标、实验、模型、指标、seed、task graph、harness、evidence contract、anti-mock 规则。 |
| [`research-plan`](skills/research-plan/SKILL.md) | 从 Spec 生成 dated 具体执行计划：`docs/research/plans/YYYY-MM-DD-purpose/`。 |
| [`research-audit`](skills/research-audit/SKILL.md) | 审计 PRD、Paper、Spec、Plans、PPT、artifacts 之间的一致性与漂移。 |
| [`research-ppt`](skills/research-ppt/SKILL.md) | 生成 slide-image deck spec、逐页 ImageGen prompt、PNG 页面输出计划和 PDF 导出计划；不生成 `.pptx`。 |

不要新增独立的 `research-evidence`、`research-writing` 或 `research-goal`。证据由 Spec / Plan / Audit 字段承担；写作优化属于 `research-paper`；长期执行 prompt 属于 `research-plan`。

## 标准工作区

```text
docs/research/
  state.yaml

  prd/
    research_prd.tex
    research_prd.md
    research_prd.pdf
    render_blocker.md  # 仅在缺少 LaTeX 引擎或真实编译失败时出现

  paper/
    planned_paper.tex
    planned_paper.md
    planned_paper.pdf
    placeholder_map.yaml
    paper_gap_report.md

  spec/
    README.md
    global_spec.yaml
    shared/
      dataset_manifest.yaml
      metric_manifest.yaml
      model_manifest.yaml
      environment_spec.yaml
      seed_protocol.yaml
      artifact_schema.yaml
      anti_mock_policy.yaml
      evidence_contract.yaml
      insight_policy.yaml
    insights/
      insight_manifest.yaml
      insight_policy.yaml
      anomaly_schema.yaml
      pivot_proposal_schema.yaml
      diagnostic_experiment_policy.yaml
    reproduction/
      benchmark_candidate_matrix.yaml
      reproduction_manifest.yaml
      reproduction_task_graph.yaml
      reproduction_harness.yaml
      reproduction_gap_report.md
    implementation/
      module_contracts.yaml
      implementation_task_graph.yaml
      implementation_harness.yaml
    experiments/
      experiment_manifest.yaml
      experiment_task_graph.yaml
      experiment_harness.yaml
    paper/
      placeholder_map.yaml
      result_binding.yaml
    feedback/
      README.md

  plans/
    plan_queue.yaml
    YYYY-MM-DD-purpose/
      plan.md
      plan.yaml
      ai_loop_prompt.md
      current_state.md
      blocker_log.md
      decision_log.md
      run_log.md
      final_summary.md

  ppt/
    main_deck/
      deck_spec.yaml
      slide_manifest.yaml
      slide_prompts/
        01_title.md
        02_motivation.md
        ...
      slide_notes.md
      deck_gap_report.md
      render_plan.md
      pages/
        01_title.png
        02_motivation.png
        ...
      exports/
        main_deck.pdf

  audits/
    YYYY-MM-DD-audit/
      audit_report.md
      alignment_matrix.yaml
      drift_findings.yaml
      repair_plan.md

  insights/
    insight_log.md
    anomaly_reports/
    negative_results/
    pivot_proposals/
    diagnostic_experiment_proposals/
```

## 实际工作流案例

这套系统的核心不是线性执行，而是**假设驱动的研究循环**。以下是三种典型操作模式。

### 模式 A：控制器托管（适合 reproduction / implementation）

```bash
# 09:00 你启动
research-plan --date 2026-05-10 --track reproduction --purpose reproduce-b01

# 09:05 /research 生成或刷新下一步执行 prompt
# 你去做别的（读 paper、开会、写代码）

# 17:00 你回来检查
cat docs/research/plans/2026-05-10-reproduce-b01/final_summary.md
# → "全部 gate 通过，baseline 复现成功"
# → 无 Mismatch，无 Surprise
# → Action: continue original plan

# 你：确认无异常，运行 research-audit
```

**你的投入：5 分钟启动 + 5 分钟检查。**

**接入真实 executor 后的放手条件**：
- 所有命令/路径/seed 已在 spec 中完整定义
- track 是 reproduction / implementation / experiment
- 没有 open pivot proposal
- insight_log.md 的 Action = continue original plan

---

### 模式 B：诊断模式（适合 diagnostic experiment / insight-feedback）

```bash
# 09:00 你启动
cat docs/research/plans/2026-05-10-diagnose-m1/insight_log.md
# → "Observation: M1 的 attention weight 在 90% samples 上接近 uniform"

# 11:00 你：读到这个，意识到可能是关键
# 你：手动添加 follow-up experiment 到 spec，重新运行 plan

# 15:00 你：确认这是真实 insight，不是 bug
# 你：运行 research-audit
# 你：阅读 repair_plan.md 的 insight-opportunity 部分
# 你：决定是否写 pivot proposal
```

**你的投入：持续参与，但 AI 帮你做所有执行和记录。**

**介入信号**：
- insight_log.md 出现 Mismatch / Surprise
- 任何一轮执行出现了未预期的异常
- validate_research --mode insight-ready 出现警告

---

### 模式 C：Pivot 决策模式（必须人类主导）

```
Day 1  AI：提交 pivot_proposal 到 insights/pivot_proposals/
       系统状态：insight_loop.status = "pivot_proposed"
       AI 停止所有执行，等待人类决策

Day 1-3 你：深度阅读
       - 原始 PRD v1 的 Chapter 6, 8, 10
       - 所有 anomaly_reports
       - 对比 pivot proposal 中的 "Required PRD Changes"

Day 3  你：做决策
       [ ] Approve  → 进入 PRD v2，AI 辅助生成文本
       [ ] Reject   → 写回复，要求补充实验
       [ ] Revise   → 修改 pivot 角度，再 submit

Day 4  你：如果 Approve，运行 research-spec 重新编译
       AI：自动级联更新 spec → plan → audit
```

**你的投入：数小时深度思考。这是科研中不可替代的部分。**

**强制停止信号**：
- insight_log.md 的 Action = propose pivot
- blocker_log.md 出现研究类 blocker（假设矛盾）
- AI 试图修改核心 RQ / Claim / 论文故事线

---

### 三层自动化边界

| 层级 | 内容 | AI 权限 | 人类角色 |
|------|------|---------|---------|
| **执行层** | 代码运行、环境修复、实验执行、日志更新 | 当前仅 prompt-only；接入 backend 后才可自动迭代 | 定期查看 summary |
| **洞察层** | Insight 记录、异常分类、Pivot 提案生成 | ✅ 自动准备材料 | 做决策（Approve/Reject/Revise） |
| **战略层** | 核心 RQ、问题表述、主 Claim、论文故事线 | ❌ 只辅助文本 | 完全控制，AI 不得修改 |

> **执行交给 AI，洞察留给自己。让 AI 做你最快的实验员和诚实的记录员，但让最终的方向判断永远属于人类。**

## Research PRD

`research-prd` 维护人类研究真源。PRD 不是短论文，也不是占位符列表，而是专业、详细、教学友好、可执行的研究设计文档。标题采用中文 + 英文 canonical label，必须包含：

1. 执行摘要（Executive Summary）
2. 背景教程（Background Tutorial）
3. 相关工作地图（Related Work Map）
4. 基准与复现计划（Benchmark and Reproduction Plan）
5. 问题陈述（Problem Statement）
6. 研究问题与假设（Research Questions and Hypotheses）
7. 形式化定义（Formalization）
8. 拟议方法（Proposed Method）
9. 系统与实现设计（System and Implementation Design）
10. 实验设计（Experiment Design）
11. 任务图与学生工作计划（Task Graph and Student Work Plan）
12. Harness 与验收标准（Harness and Acceptance Criteria）
13. 证据台账（Evidence Ledger）
14. 论文计划（Paper Plan）
15. 风险、局限与伦理（Risks, Limitations, and Ethics）

PRD 要解释足够背景，使有能力但非该方向专家的硕士生可以执行；同时必须定义具体任务、benchmark、实验、harness、验收条件和证据边界。

模板质量要求：

- 每章包含章节目标、必须填写的信息、常见错误、证据边界、验收标准。
- 使用结构化中文占位符 `【待填写：...】`，不使用裸 `TODO`。
- 默认包含 TikZ 图骨架：研究问题到证据链、方法模块图、实验/复现流程图、Spec -> Plan -> Audit 执行闭环。
- 关键章节包含 RQ/Hypothesis 表、Benchmark Candidate Matrix、Experiment Matrix、Task Graph Table、Evidence Ledger、Risk Matrix。

## Research Paper

`research-paper` 从 PRD 派生 planned top-conference-style manuscript。它可以对已经在 PRD 中设计好的对象使用强表达：

`research-paper` 的最终产物必须是一篇完整顶会风格 manuscript draft，而不是填空模板。正文应当像 NeurIPS / ICLR / AAAI 论文一样完整叙述 Abstract、Introduction、Related Work、Problem Formulation、Method、Experiments、Results / Planned Result Bindings、Limitations 和 Conclusion。若真实实验尚未完成，只能生成 placeholder-complete manuscript：表格结构、caption、结果段落和解释逻辑可以完整，但所有未验证结果值必须保留为 Spec 绑定 typed placeholder，并在 `paper_gap_report.md` 记录投稿前必须替换的证据。不得填入 plausible mock numeric values。

- `We propose ...`
- `We formulate ...`
- `We design ...`
- `We evaluate ...`
- `Experiment E1 tests whether ...`
- `Table 1 reports ...`

但在证据验证前禁止写：

- `Experiments show that ...`
- `Our method outperforms ...`
- `We achieve state-of-the-art ...`
- `The results demonstrate ...`
- 任何没有 validated evidence 支撑的数字或比较。

未观测结果必须写成实验绑定 placeholder：

```text
{{E01.OURS.primary_metric}}
{{E01.B01.primary_metric}}
{{E02.ablation_delta}}
{{E03.latency_ms}}
```

每个 placeholder 必须注册在 `docs/research/paper/placeholder_map.yaml`，并绑定到 Spec 中的实验。

## Research Spec

`research-spec` 把 PRD 编译成全局机器执行合同：

```text
RQ
-> Hypothesis
-> Claim
-> Experiment
-> Dataset / Model / Baseline / Metric / Seed
-> Task
-> Harness
-> Evidence
-> Paper placeholder
```

`research-spec` 只能从 PRD 编译，不能从 Paper 推断实验。PRD 缺失的执行细节必须进入 gap report 或 blocker，不能由 agent 发明。

Spec 采用“英文键、中文值”策略：YAML key、ID、schema 字段保持英文，`title`、`description`、`purpose`、`blockers`、`acceptance_criteria`、`notes`、gap report 和 policy 说明使用中文。

初始化生成的 Spec 不是空 YAML。它包含教学型合同模板：

- `global_spec.yaml` 提供 RQ -> Hypothesis -> Claim -> Experiment -> Evidence -> Paper placeholder 的链路模板。
- `reproduction/reproduction_manifest.yaml` 提供 `reproduction_target_template` 和三类复现模式。
- `experiments/experiment_manifest.yaml` 提供 `experiment_template`，覆盖 support / falsification / mock policy。
- `experiments/experiment_harness.yaml` 提供 `harness_template`，要求 command 或 blocker、artifact、pass criteria、claim 支撑边界和 independent rerun。
- `paper/result_binding.yaml` 提供 `result_binding_template`。

这些 `*_template` 条目只用于指导填写，不代表已经声明了可执行实验。

复现不是单独技能，而是 Spec 和 Plan 内部的 track。复现模式必须显式声明：

- `official_code_reuse`
- `official_code_adaptation`
- `paper_based_reimplementation`

## Research Plan

`research-plan` 从 Spec 生成 dated bounded execution plan。`plan.yaml` 保持英文 key 和稳定 ID，但 `plan.md`、`ai_loop_prompt.md`、状态日志、阻塞日志、决策日志、运行日志和最终总结全部使用中文。它支持：

```text
research-plan --track reproduction
research-plan --track implementation
research-plan --track experiment
research-plan --track paper-update
research-plan --gate G_ID
research-plan --target codex
research-plan --target ralph-loop
```

每个 plan 必须记录 PRD、Paper、Spec 和 git commit 的 source hash。若 Spec 在 plan 创建后改变，`plan-ready` 必须失败，直到显式生成或更新 plan。

`ai_loop_prompt.md` 会包含 Claude Code `Subagent Dispatch` 段落。需要数学、文献、复现、编码、实验、分析、论文、PPT 或审计工作时，主会话应委派 `.claude/agents/research-*.md` 中的标准 Claude Code subagent；`/research` controller 仍负责 state、gate、promotion 和 audit 阻断。

## Research Audit

`research-audit` 检查：

- PRD -> Paper alignment
- PRD -> Spec alignment
- Spec -> Plan alignment
- Paper -> Spec alignment
- Plan -> Artifact alignment
- PRD / Paper / Spec -> PPT alignment

`repair_plan.md` 必须区分：

- must fix before execution
- can fix later
- recommended next `research-plan` target

## Research PPT

`research-ppt` 生成面向 Codex + ImageGen 的 slide-image deck spec：

- 每页幻灯片生成一个 PNG。
- 最终从 PNG 页面导出 PDF。
- 不创建传统 `.pptx`。

默认 `standard` 模式是 10 到 12 页：

1. Title
2. Background and motivation
3. Problem gap and research questions
4. Problem formulation
5. Key insight
6. Method overview
7. Method details / system design
8. Benchmark and reproduction plan
9. Experiment design
10. Expected contributions
11. Risks / challenges
12. Summary and next steps

## 校验器

统一校验入口：

```bash
python3 skills/research-spec/scripts/validate_research.py --repo . --mode prd-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode paper-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode spec-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode plan-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode ppt-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode audit-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode insight-ready
python3 skills/research-spec/scripts/validate_research.py --repo . --mode alignment-check
```

readiness mode 必须硬失败。scaffold 可以存在 blocker，但不能被当成 execution-ready。

## 开发验证

运行：

```bash
python3 -m pytest tests -q
```

当前 GitHub 默认安装源是 `XiaYiHann/research-loop`；旧环境变量 `REPORT_PRD_SKILLS_*` 仅为兼容历史安装脚本保留。

## License

Apache 2.0
