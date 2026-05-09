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

初始化产物不是空 `TODO` 骨架。`research-init` 会生成中文顶级 Research PRD 模板：LaTeX 是真源，使用 `ctex`、TikZ、`booktabs`、`tabularx` 组织图表；Markdown 是伴随审阅稿。它也会生成 planned top-conference paper 模板和 Spec 执行合同模板。若本机有 `latexmk` 或 `xelatex`，脚本会真实渲染 PDF；否则写入中文 `render_blocker.md`，不会伪造 PDF。

## 安装与迁移

一行在线安装：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/report-prd-skills/main/install.sh | bash
```

安装到自定义技能目录：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/report-prd-skills/main/install.sh \
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

安装脚本会执行迁移：

- 安装新的 `research-*` 技能族。
- 用一个很小的 legacy `report` router 替换旧 `report` 入口，仅用于提示迁移方向。
- 删除旧的 `report-init`、`report-update`、`report-audit`、`report-goal`、`report-paper`、`report-spec`、`report-brainstorming` 等旧技能目录。
- 删除不应存在的 `research-evidence`、`research-writing`、`research-goal`。
- 兼容旧环境变量 `REPORT_PRD_SKILLS_SOURCE_DIR`、`REPORT_PRD_SKILLS_TARGET_DIR`、`REPORT_PRD_SKILLS_REPO_URL`、`REPORT_PRD_SKILLS_REF`，但推荐新环境变量 `RESEARCH_EXECUTION_SKILLS_*`。

迁移后，目标目录里应主要看到：

```text
report/              # legacy migration warning only
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

  plans/
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
```

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

`research-paper` 的最终产物必须是一篇完整顶会风格 manuscript draft，而不是填空模板。正文应当像 NeurIPS / ICLR / AAAI 论文一样完整叙述 Abstract、Introduction、Related Work、Problem Formulation、Method、Experiments、Results / Planned Result Bindings、Limitations 和 Conclusion。若真实实验尚未完成，可以生成 clearly labeled mock-data manuscript：用 mock planning values 指导实验设计，但最终结果位置必须保留为 Spec 绑定 placeholder，并在 `paper_gap_report.md` 记录投稿前必须替换的证据。

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
python3 skills/research-spec/scripts/validate_research.py --repo . --mode alignment-check
```

readiness mode 必须硬失败。scaffold 可以存在 blocker，但不能被当成 execution-ready。

## 开发验证

运行：

```bash
python3 -m pytest tests -q
```

历史 GitHub 路径仍是 `XiaYiHann/report-prd-skills`；当前产品身份是 `research-execution-skills`。

## License

Apache 2.0
