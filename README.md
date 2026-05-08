# report-prd-skills

一套面向 Codex / Claude Code 的 report skill family，用于把研究或工程 idea 转成可迭代的 PRD 报告、顶会论文草稿，以及带 milestone / gate / harness 的 AI 执行 prompt。

当前定位是 **report-driven execution compiler**：

```text
main  = human design truth
paper = academic expression truth
spec  = machine execution truth
```

核心原则：执行权只能属于 `spec`。milestone 顺序、gate、task、harness、artifact path 和 evidence 准入必须来自 `spec`，不能从 paper prose 里反推。

## 一键在线安装

在任意终端直接运行下面这一行。**不需要先 clone 本仓库**：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/report-prd-skills/main/install.sh | bash
```

默认安装位置：

```text
~/.agents/skills
```

安装脚本会在缺失时自动创建 `~/.agents/skills`。如果用户电脑上已经安装过旧版 report skill family，脚本会替换当前 report skills，并清理已废弃的拆分 skill，例如 `report-debate`、`report-paper-plan`、`report-paper-draft`、`report-ingest-results`、`report-spec`。

在线安装脚本依赖 `bash` 和 `git`。原因是它会先把本仓库 clone 到临时目录，再把 skill 目录复制到 `~/.agents/skills`。

安装到自定义 skill 目录：

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/report-prd-skills/main/install.sh \
  | REPORT_PRD_SKILLS_TARGET_DIR=/path/to/.agents/skills bash
```

开发本仓库时，从本地 checkout 安装：

```bash
REPORT_PRD_SKILLS_SOURCE_DIR="$PWD" bash install.sh
```

## Skills 列表

| Skill | 用途 |
|-------|---------|
| [`report`](skills/report/SKILL.md) | 路由入口，根据用户意图转到更窄的 sub-skill。 |
| [`report-init`](skills/report-init/SKILL.md) | 初始化半空 PRD LaTeX workspace，并渲染 `report.pdf` + `report.md`。 |
| [`report-brainstorming`](skills/report-brainstorming/SKILL.md) | 写回前讨论、比较、澄清和结构化 PRD。 |
| [`report-update`](skills/report-update/SKILL.md) | 把已确认内容写回 PRD，重新渲染并运行一致性检查。 |
| [`report-audit`](skills/report-audit/SKILL.md) | 审计 PRD 结构、证据、争议 claim、执行就绪度和修复顺序。 |
| [`report-goal`](skills/report-goal/SKILL.md) | 基于 `main` / `paper` / `spec` 生成三产物门禁的长期 AI 执行 prompt。 |
| [`report-paper`](skills/report-paper/SKILL.md) | 从 report workspace 和 evidence ledger 生成顶会风格 CS 论文。 |

## 架构

```
用户意图
    │
    ▼
┌─────────────────────────┐
│   report (router)       │  路由到最窄的匹配 skill
└────┬────────┬────────┬──┘
     │        │        │
     ▼        ▼        ▼
 init    brainstorm  update    audit    goal    paper
     │        │        │
     └────────┴────────┘
              │
              ▼
    ┌──────────────────┐
    │   _shared/       │  Python scripts, reference docs,
    │                  │  LaTeX templates, checklists
    └──────────────────┘
              │
              ▼
    main / paper / spec
    ├── main: 报告设计真源
    ├── paper: 顶会论文表达产物
    └── spec: task graph + harness + evidence contract
```

## PRD 类型

### `research-prd`

用于学术研究项目。必须包含：

- Research Questions and falsifiable hypotheses
- Evidence Ledger: `claim → evidence → source → limitation → confidence`
- Baseline Matrix, Ablation Matrix, Reproducibility Table, Failure-case Table
- Risks, ethics, and Go / No-Go gates
- `experiments/experiment_manifest.yaml` linking claims to planned experiments

### `engineering-prd`

用于工程 / 产品 / 系统规格。必须包含：

- Goals & Non-Goals
- Modular functional requirements with Acceptance Criteria
- NFR matrix, interface/data contracts
- Testing / acceptance / release plan
- Operational Readiness Matrix, phased MVP roadmap
- `tasks/task_graph.yaml`, `harness/harness.yaml`, and `evidence/evidence_manifest.yaml`

## 执行模型

`report-goal` 优先使用三产物布局：

```text
docs/report/<slug>/main/
docs/report/<slug>/paper/
docs/report/<slug>/spec/
```

生成 goal prompt 时按下面顺序判断：

1. `spec/` 缺失或无效 -> 生成 `spec 修复目标`。
2. `spec/` 有效，但 `main/` / `paper/` 缺失或不一致 -> 生成 `三产物对齐目标`。
3. `main` / `paper` / `spec` 全部有效且对齐 -> 生成 `三产物执行目标`。

只有 `spec` 可以定义可执行 milestone、gate、task、harness command、artifact 和 evidence contract。`main` 只解释设计，`paper` 只表达论文叙事和 placeholder。agent 不能从 `paper` 推断 experiment、baseline、metric、dataset、seed 或 result。

仍使用 `report.manifest.yaml`、`tasks/task_graph.yaml`、`harness/harness.yaml`、`evidence/evidence_manifest.yaml` 的旧 workspace 保留兼容路径。`--allow-legacy-prose-goal` 只作为显式逃生口。

## Paper 输出

本 family 只有一个 paper 专用 skill：[`report-paper`](skills/report-paper/SKILL.md)。它是 agent-driven，不是 parser-driven：用户可以用自然语言要求生成顶会论文，agent 会读取 report workspace、manifest 和 evidence ledger，判断应该在 `docs/report/<slug>/paper/` 下生成 planned manuscript 还是 observed-results paper。

不要把 paper 工作拆成 `report-paper-plan`、`report-paper-draft` 或 venue-specific skills。本 family 也有意不保留独立 `report-debate`；争议 claim 通过 `report-audit` 的 multi-agent audit mode 审计。

## Shared Resources 共享资源

`_shared/` 是 skill 内共享资源的镜像面：

- **`_shared/scripts/`** — Python tools for initialization, rendering, repo scanning, self-check
- **`_shared/references/`** — PRD templates, style guides, checklists, writing guidelines
- **`_shared/assets/templates/`** — LaTeX templates, metadata schemas, outline files

## Contributing

提交 skill 改动前：

1. 确认 `SKILL.md` 有合法 YAML frontmatter（`name` + `description`）。
2. 尽量保持 `SKILL.md` 正文低于 500 行。
3. 运行 `python3 -m pytest skills/report/_shared/scripts/tests` 验证共享脚本。
4. 提交前检查是否误包含个人路径或 PII。

## License

Apache 2.0
