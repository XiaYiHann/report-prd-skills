#!/usr/bin/env python3
"""Shared helpers for the research execution skill family."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
TEMPLATE_FAMILY = "research_loop"
TEMPLATE_VERSION = "epoch_v1"
DEFAULT_RESEARCH_DIR = Path("docs") / "research"
EPOCH_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
EPOCH_MANIFEST_PATH = EPOCH_SCHEMA_DIR / "epoch_v1_manifest.yaml"
FORBIDDEN_RESULT_PHRASES = [
    "experiments show",
    "our method outperforms",
    "we achieve state-of-the-art",
    "state-of-the-art",
    "the results demonstrate",
    "results demonstrate",
]
REPRODUCTION_MODES = {"official_code_reuse", "official_code_adaptation", "paper_based_reimplementation"}
REPRODUCTION_TYPES = {
    "official_code",
    "forked_official_code",
    "third_party_code",
    "faithful_reimplementation",
    "analytical_baseline",
    "literature_only_not_executable",
}
REPRODUCTION_STATUSES = {
    "pending",
    "search_done",
    "planned",
    "environment_ready",
    "smoke_passed",
    "small_scale_passed",
    "full_passed",
    "blocked_missing_code",
    "blocked_missing_data",
    "blocked_stale_dependency",
    "blocked_ambiguous_algorithm",
    "failed_metric_mismatch",
    "failed_unexplained",
    "excluded_by_human",
}
REPRODUCTION_EVIDENCE_LEVELS = {
    "official_full_reproduction",
    "official_small_scale_reproduction",
    "official_smoke_only",
    "third_party_reproduction",
    "faithful_reimplementation",
    "analytical_baseline",
    "literature_only",
    "failed_but_informative",
}


PRD_SECTIONS = [
    "## 1. 执行摘要（Executive Summary）",
    "## 2. 背景教程（Background Tutorial）",
    "## 3. 相关工作地图（Related Work Map）",
    "## 4. 基准与复现计划（Benchmark and Reproduction Plan）",
    "## 5. 问题陈述（Problem Statement）",
    "## 6. 研究问题与假设（Research Questions and Hypotheses）",
    "## 7. 形式化定义（Formalization）",
    "## 8. 拟议方法（Proposed Method）",
    "## 9. 系统与实现设计（System and Implementation Design）",
    "## 10. 实验设计（Experiment Design）",
    "## 11. 任务图与学生工作计划（Task Graph and Student Work Plan）",
    "## 12. Harness 与验收标准（Harness and Acceptance Criteria）",
    "## 13. 证据台账（Evidence Ledger）",
    "## 14. 论文计划（Paper Plan）",
    "## 15. 风险、局限与伦理（Risks, Limitations, and Ethics）",
    "## 16. 探索与洞察策略（Exploration and Insight Policy）",
]


SPEC_FILES = [
    "global_spec.yaml",
    "shared/dataset_manifest.yaml",
    "shared/metric_manifest.yaml",
    "shared/model_manifest.yaml",
    "shared/environment_spec.yaml",
    "shared/seed_protocol.yaml",
    "shared/artifact_schema.yaml",
    "shared/anti_mock_policy.yaml",
    "shared/evidence_contract.yaml",
    "shared/insight_policy.yaml",
    "insights/insight_manifest.yaml",
    "insights/insight_policy.yaml",
    "insights/anomaly_schema.yaml",
    "insights/pivot_proposal_schema.yaml",
    "insights/diagnostic_experiment_policy.yaml",
    "feedback/README.md",
    "reproduction/benchmark_candidate_matrix.yaml",
    "reproduction/reproduction_manifest.yaml",
    "reproduction/reproduction_task_graph.yaml",
    "reproduction/reproduction_harness.yaml",
    "reproduction/reproduction_gap_report.md",
    "implementation/module_contracts.yaml",
    "implementation/implementation_task_graph.yaml",
    "implementation/implementation_harness.yaml",
    "experiments/experiment_manifest.yaml",
    "experiments/experiment_task_graph.yaml",
    "experiments/experiment_harness.yaml",
    "paper/placeholder_map.yaml",
    "paper/result_binding.yaml",
]

def load_epoch_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or EPOCH_MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"epoch manifest not found: {manifest_path}")
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"epoch manifest must be a mapping: {manifest_path}")
    if payload.get("schema_version") != TEMPLATE_VERSION:
        raise ValueError(f"epoch manifest schema_version must be {TEMPLATE_VERSION}")
    return payload


def epoch_manifest_list(key: str, manifest: dict[str, Any] | None = None) -> list[str]:
    payload = manifest or load_epoch_manifest()
    values = payload.get(key)
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise ValueError(f"epoch manifest key {key} must be a string list")
    return list(values)


def epoch_required_files(manifest: dict[str, Any] | None = None) -> list[str]:
    return epoch_manifest_list("required_files", manifest)


def epoch_wiki_files(manifest: dict[str, Any] | None = None) -> list[str]:
    return epoch_manifest_list("required_wiki_files", manifest)


def epoch_search_files(manifest: dict[str, Any] | None = None) -> list[str]:
    return epoch_manifest_list("required_search_files", manifest)


def epoch_reproduction_files(manifest: dict[str, Any] | None = None) -> list[str]:
    return epoch_manifest_list("required_reproduction_files", manifest)


EPOCH_REQUIRED_FILES = epoch_required_files()

EPOCH_WIKI_FILES = epoch_wiki_files()

TASK_STATUSES = set(epoch_manifest_list("task", load_epoch_manifest().get("status_enums", {})))
GATE_STATUSES = set(epoch_manifest_list("gate", load_epoch_manifest().get("status_enums", {})))

CLOSED_VERSION_STATUSES = {
    "closed_success",
    "closed_negative",
    "closed_blocked",
    "closed_falsified",
    "closed_pivot_required",
    "closed_stable",
}

PAPER_BINDING_STATUSES = {"closed_stable", "paper_binding_ready"}
AUDIT_RESULT_STATUSES = {"pass", "repair_required", "human_review_required", "falsification_confirmed"}

AGENT_REQUIRED_FILES = [
    "RUNBOOK.md",
    "CLAUDE_LOOP_PROMPT.md",
    "CODEX_GOAL_TEMPLATE.md",
    "SUBAGENT_POLICY.md",
    "LITERATURE_POLICY.md",
    "GIT_POLICY.md",
]


AUDIT_MATRIX_KEYS = [
    "direction_completeness",
    "prd_to_paper",
    "prd_to_spec",
    "spec_to_plan",
    "paper_to_spec",
    "plan_to_artifact",
    "prd_to_insight",
    "insight_to_spec",
    "insight_to_plan",
]

MOCK_SOURCE_TYPES = {"mock", "toy", "synthetic", "stub", "cached", "proxy", "smoke_only"}

FULL_EXPERIMENT_REAL_CRITERIA = {
    "real_dataset_provenance_verified",
    "real_model_provenance_verified",
    "no_synthetic_or_mock_inputs",
    "full_run_not_smoke",
}

FULL_REPRODUCTION_REAL_CRITERIA = {
    "real_dataset_provenance_verified",
    "real_model_provenance_verified",
    "official_or_declared_code_commit_verified",
    "no_synthetic_or_mock_inputs",
    "full_run_not_smoke",
}


def today_string() -> str:
    return dt.date.today().isoformat()


def template_metadata() -> dict[str, Any]:
    return {
        "template_family": TEMPLATE_FAMILY,
        "template_version": TEMPLATE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_by": "research-init",
    }


def markdown_template(content: str) -> str:
    frontmatter = "\n".join(
        [
            "---",
            f"template_family: {TEMPLATE_FAMILY}",
            f"template_version: {TEMPLATE_VERSION}",
            f"schema_version: {SCHEMA_VERSION}",
            "generated_by: research-init",
            "---",
            "",
        ]
    )
    return frontmatter + content


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def write_text(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml(path: Path, payload: dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(read_text(path))
    return payload if isinstance(payload, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "research-run"


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def render_pdf_from_tex(tex_path: Path, pdf_path: Path, force: bool = False) -> bool:
    """Render a real PDF when a LaTeX engine exists; otherwise write a blocker."""
    if pdf_path.exists() and not force:
        return True
    if pdf_path.exists() and force:
        pdf_path.unlink()
    blocker_path = tex_path.parent / "render_blocker.md"
    latexmk = shutil.which("latexmk")
    xelatex = shutil.which("xelatex")
    if not latexmk and not xelatex:
        write_text(
            blocker_path,
            "\n".join(
                [
                    "# PDF 渲染阻塞",
                    "",
                    "未生成 PDF：未检测到可用的 LaTeX 引擎。",
                    "",
                    "需要安装 `latexmk` 或 `xelatex` 后重新渲染。本初始化器不会写入伪造 PDF，因为 PDF 必须来自 `research_prd.tex` 或 `planned_paper.tex` 的真实编译结果。",
                    "",
                ]
            ),
            force=True,
        )
        return False

    build_dir = tex_path.parent / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    if latexmk:
        commands = [[latexmk, "-xelatex", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={build_dir}", tex_path.name]]
    else:
        commands = [
            [xelatex, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={build_dir}", tex_path.name],
            [xelatex, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={build_dir}", tex_path.name],
        ]

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=tex_path.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=90,
        )
        stdout_parts.append(result.stdout)
        stderr_parts.append(result.stderr)
        if result.returncode != 0:
            write_text(
                blocker_path,
                "# PDF 渲染阻塞\n\n"
                "检测到 LaTeX 引擎，但真实编译失败。请根据下方日志修复 `.tex` 后重新渲染。\n\n"
                "## stdout\n\n```text\n"
                + "\n".join(stdout_parts)[-8000:]
                + "\n```\n\n## stderr\n\n```text\n"
                + "\n".join(stderr_parts)[-4000:]
                + "\n```\n",
                force=True,
            )
            return False

    rendered_pdf = build_dir / f"{tex_path.stem}.pdf"
    if rendered_pdf.exists():
        shutil.copy2(rendered_pdf, pdf_path)
        if blocker_path.exists():
            blocker_path.unlink()
        return True
    write_text(
        blocker_path,
        "# PDF 渲染阻塞\n\nLaTeX 命令结束但未找到预期 PDF 输出，请检查构建目录。\n",
        force=True,
    )
    return False


def _insight_log_template() -> str:
    return """# Insight Log

> Legacy compatibility note: 新版 epoch workspace 的当前 insight 真源是 `docs/research/{CURRENT}/wiki/*`。
> 本文件只作为旧 `docs/research/insights/` 路径的兼容日志、迁移来源或用户显式要求的 legacy 记录。
> 旧 insight 不能直接支撑当前版本 claim，除非当前 `Vn/PRD.md` 或 `Vn/SPEC.yaml` 显式 carry_forward。

> 本文件记录从 Plan 执行中产生的洞察、异常、负结果和 pivot 提案。
> legacy dated plan 执行完毕后，可以在这里追加一个 entry，而不是只写"任务完成"。
> 新版 epoch task 完成后，优先使用 `research-insight` 更新当前 `Vn/wiki/*`。

## 待填写 Entry 模板

### Source
- Plan: `docs/research/plans/YYYY-MM-DD-purpose/`
- Experiment: `E01`
- Harness: `H_E01_FULL`
- Artifacts:
  - `artifacts/experiments/E01/aggregate/summary.json`

### Observation
What happened?

### Expected Behavior from PRD
What did the PRD expect?

### Mismatch / Surprise
What was surprising, wrong, unstable, or unexpectedly simple?

### Possible Explanation
What might explain the observation?

### Research Value
Is this merely an implementation bug, or does it reveal something about the problem?

### Action Recommendation
- [ ] continue original plan
- [ ] repair spec
- [ ] add diagnostic experiment
- [ ] narrow claim
- [ ] propose PRD pivot
- [ ] stop and request human review

### Confidence
low / medium / high
"""


def goal_markdown(title: str, purpose: str) -> str:
    return f"""---
version: V0
language: zh-CN
style: formal_academic
evidence_rule: no_fabrication
gate_strategy: sequential_only
commit_policy: per_gate_or_blocker
---

# V0 Goal — {title}

> **本文件是版本总纲（version-level anchor），不是当前任务（task-level）文件。**
> 它定义整个 `V0` 的总体使命、全局约束和成功标准。只有在版本核心问题或范围发生偏移时才修改。

## 工作目录
在 `{{repo_path}}` 工作。

## 全局约束
- 全程中文、正式学术风格。
- 遵守 AGENTS.md：TDD、最小实现、证据分层。
- 禁止伪造实验、stdout、artifact、hash。
- 禁止把 design intent 写成 repo-observed fact。
- 不要手改 generated artifacts。

## 版本目标（Overall Mission for V0）
{purpose}

**核心研究问题**：【待填写：用一句可证伪命题表达。这是整个 V0 要回答的问题，不是当前任务。】

**预期交付物**：【待填写：方法、基准、系统、理论或分析贡献】

**版本成功标准**：【待填写：什么条件下 V0 可以 closeout】

## 总规则
- 每次只推进最早未完成 gate，不跳 gate。
- 每个 gate 流程：preflight → execution → audit → wiki/state update → commit。
- 失败要分类为 blocked / failed_execution / failed_harness / diagnostic。
- 不要直接说研究假设被证伪，除非有完整 harness 与审计。

## Gate 序列
【待填写：G0, G1, G2, ... 及其前置条件】

## 测试要求
- 每个新增脚本先写测试。
- 至少运行已有的 gate 测试和 harness 测试。
- 运行 `git diff --check`。

## 提交要求
- 每完成一个 gate 或明确 blocker，提交一次 commit。
- Commit 格式：`type(scope): description`
- 示例：`test(research): add v0 g1 preflight gate`

## 最终回复格式
每次任务完成后必须报告：
- current gate
- verdict（pass / blocked / failed）
- artifact paths
- tests run
- commit hash
- next gate / blocker

必须以文件和证据为准，不要空泛建议。
"""


def prd_markdown(title: str, purpose: str) -> str:
    return f"""# Research PRD

> 本文件是中文 Research PRD 伴随稿。LaTeX 真源是 `research_prd.tex`；Markdown 用于快速审阅、搜索和给 AI agent 提供轻量上下文。
> 当前模板面向能够执行研究项目但不一定熟悉完整背景的硕士学生。模板只提供结构化占位，不发明数据集、基线、实验结果或论文结论。

## 1. 执行摘要（Executive Summary）

**章节目标**：用一页说明研究想解决什么问题、为什么值得做、最低可行研究目标是什么，以及哪些结论仍需要证据。

**必须填写的信息**
- 项目一句话摘要：`{title}`。
- 核心研究问题：`【待填写：核心研究问题，用一句可证伪命题表达】`。
- 预期贡献：`【待填写：方法、基准、系统、理论或分析贡献】`。
- 最低可行研究目标：`{purpose}`。
- 当前状态：`【待填写：scaffold / planning / implementation / experiment / paper-update】`。

**推荐图表**：研究问题到证据链图；What / Why / How / So What 摘要表。

| 维度 | 内容 |
| --- | --- |
| What | 【待填写：研究对象与核心问题】 |
| Why | 【待填写：科学缺口、应用价值、审稿人会关心的理由】 |
| How | 【待填写：核心方法、数据、复现与实验路径】 |
| So What | 【待填写：预期学术贡献和可交付物】 |

**常见错误**：把愿景写成已经证明的结论；把论文宣传语当成研究问题；不说明最小可行目标。

**证据边界**：本章只能写设计意图、研究假设和计划贡献；未执行实验不得写成经验结论。

**验收标准**：读者能用两句话复述项目问题、方法方向、最小目标和当前证据状态。

## 2. 背景教程（Background Tutorial）

**章节目标**：补齐学生理解后续章节所需的领域背景、基本概念、数学或系统知识。

**必须填写的信息**
- 领域背景：`【待填写：最近 3 到 5 年的关键上下文】`。
- 基本概念：`【待填写：术语表，包含大白话解释和正式定义】`。
- 必备数学 / 系统 / ML / 安全背景：`【待填写：只列后文真正会用到的知识】`。
- 常见初学者误解：`【待填写：至少 3 条误解及纠正】`。
- 为什么值得做：`【待填写：问题未解决会造成什么科学或工程代价】`。

| 概念 | 大白话解释 | 正式定义 | 后文用途 |
| --- | --- | --- | --- |
| 【待填写：概念 A】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：背景只堆论文名；公式前不解释直觉；术语首次出现没有定义。

**证据边界**：背景中的事实需要在 `sources.md` 或文献表中登记；本章不提出未经验证的新 claim。

**验收标准**：学生读完后能解释关键术语，并知道每个概念会在方法或实验中承担什么角色。

## 3. 相关工作地图（Related Work Map）

**章节目标**：把研究谱系、代表方法、未解决问题和最接近基线组织成 reviewer 可检查的地图。

**必须填写的信息**
- Research lineage：`【待填写：问题从哪些工作演化而来】`。
- Representative methods：`【待填写：代表性方法及其解决的问题】`。
- Closest baselines：`【待填写：最接近且必须比较的 baseline】`。
- Difference from prior work：`【待填写：我们的边界差异，不夸大 novelty】`。

| 工作 / 方法 | 解决了什么 | 没解决什么 | 与本研究的关系 |
| --- | --- | --- | --- |
| 【待填写：P01】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：只写“我们不同”；没有说明为什么这些 baseline 对审稿人是公平的。

**证据边界**：相关工作只能支持“已有方法声称什么”和“仍缺什么”，不能替代本项目实验证据。

**验收标准**：读者能指出最接近的 3 个 baseline，以及本项目与它们的最小可辩护差异。

## 4. 基准与复现计划（Benchmark and Reproduction Plan）

**章节目标**：定义 benchmark 选择标准、候选论文矩阵、复现模式和复现失败时的降级策略。

**必须填写的信息**
- Benchmark selection criteria：`【待填写：数据集、任务、指标、代码可得性、审稿预期】`。
- Selected reproduction targets：`【待填写：R_B01 / R_B02 等复现目标】`。
- Reproduction mode：`official_code_reuse` / `official_code_adaptation` / `paper_based_reimplementation`。
- Reproduction protocol：`【待填写：环境、命令、seed、metric tolerance、artifact schema】`。
- Scaffold reuse plan：`【待填写：哪些 official code 只作为 baseline，哪些可复用为 harness】`。

**Benchmark Candidate Matrix**

| paper_id | baseline_id | 选择理由 | 复现模式 | 主要风险 | 进入主实验条件 |
| --- | --- | --- | --- | --- | --- |
| 【待填写：P01】 | 【待填写：B01】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：把 paper-based reimplementation 写成 official reproduction；悄悄改 baseline 核心算法；没有记录 commit 和 license。

**证据边界**：复现证据支持 baseline comparability，不直接证明我们的方法 claim。

**验收标准**：每个 baseline 都有复现模式、输入数据、metric tolerance、命令、artifact 和失败解释路径。

## 5. 问题陈述（Problem Statement）

**章节目标**：把研究问题从直觉陈述收敛为可形式化、可实验、可证伪的问题定义。

**必须填写的信息**
- Informal problem：`【待填写：用学生能理解的语言描述问题】`。
- Formal problem：`【待填写：输入、输出、约束、目标函数或系统目标】`。
- Scope：`【待填写：本 PRD 覆盖的任务和数据边界】`。
- Non-goals：`【待填写：明确不做什么以及原因】`。
- Threat model / assumptions：`【待填写：适用场景与失效场景】`。

| 边界项 | In Scope | Out of Scope | 原因 |
| --- | --- | --- | --- |
| 【待填写：任务边界】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：问题定义过宽；Non-goals 缺失；把实现便利性当成研究边界。

**证据边界**：问题定义可以来自理论和文献，但主张有效性仍必须由后续实验或证明支持。

**验收标准**：学生能判断一个新任务、新数据集或新 claim 是否属于本项目范围。

## 6. 研究问题与假设（Research Questions and Hypotheses）

**章节目标**：把 RQ、Hypothesis、Expected Claim、Experiment、Falsification 绑定起来。

**RQ / Hypothesis / Claim 映射表**

| rq_id | research_question | hypothesis_id | expected_claim | falsification_condition | planned_experiment |
| --- | --- | --- | --- | --- | --- |
| RQ1 | 【待填写：开放但可回答的问题】 | H1 | 【待填写：预期 claim】 | 【待填写：何种结果推翻该 claim】 | E01 |

**常见错误**：RQ 写成 yes/no 宣传句；假设不可证伪；expected claim 没有实验绑定。

**证据边界**：Expected claim 只表示计划主张；执行前不得写成 “results show”。

**验收标准**：每个 RQ 都能追踪到 hypothesis、claim、experiment 或 proof task。

## 7. 形式化定义（Formalization）

**章节目标**：给出 notation、objective、constraints、optimization target / system target 和理论直觉。

| 符号 | 含义 | 取值范围 | 直觉解释 |
| --- | --- | --- | --- |
| 【待填写：x】 | 【待填写】 | 【待填写】 | 【待填写】 |

**必须填写的信息**：目标函数、约束、理论依据、预期性质、适用条件和不适用条件。

**常见错误**：公式没有解释每个符号；理论直觉与实验设计脱节。

**证据边界**：形式化提供可检验结构，不自动证明方法有效。

**验收标准**：学生能从符号表读到目标函数，并解释每个约束如何影响实现或实验。

## 8. 拟议方法（Proposed Method）

**章节目标**：描述 method overview、key idea、module breakdown、algorithm / workflow、complexity 和 failure modes。

| module_id | 模块职责 | 输入 | 输出 | 失败模式 | 验收方式 |
| --- | --- | --- | --- | --- | --- |
| M01 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**推荐图表**：方法模块图。

**常见错误**：只写概念不写模块接口；忽略复杂度和失败模式；把工程 trick 写成主要科学贡献。

**证据边界**：方法可以用 “我们提出 / 我们设计”，但不得声称优于 baseline。

**验收标准**：学生能按模块拆分实现任务，并知道每个模块的输入输出和失败条件。

## 9. 系统与实现设计（System and Implementation Design）

**章节目标**：把方法转换成可实现的代码结构、数据流、配置系统和可复现工程边界。

| component | path_hint | responsibility | input | output | test_or_harness |
| --- | --- | --- | --- | --- | --- |
| 【待填写：组件】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：实验脚本、训练代码和评估代码职责混乱；没有配置版本；artifact schema 不稳定。

**证据边界**：实现完成不等于研究 claim 成立，claim 仍由 harness 和 evidence contract 决定。

**验收标准**：学生能据此创建模块、配置、日志、artifact，并知道哪些文件不能手工伪造。

## 10. 实验设计（Experiment Design）

**章节目标**：定义 dataset、baseline、metric、main experiments、ablation、sensitivity、failure-case 和 statistical protocol。

| experiment_id | linked_rq | dataset | baselines | metrics | seeds | support_condition | falsification_condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | RQ1 | D01 | B01 | M01 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：没有 frozen split；只跑一个 seed；ablation 同时改变多个变量；失败案例不记录。

**证据边界**：smoke test 不能支持 research claim；主实验必须完成所有声明 seed、baseline、metric 和 artifact hash。

**验收标准**：每个实验都有可执行命令、artifact、harness、统计协议和证伪条件。

## 11. 任务图与学生工作计划（Task Graph and Student Work Plan）

**章节目标**：把研究拆成可执行 phase、task、dependencies、acceptance criteria、weekly milestones 和 Go / No-Go checkpoint。本版本必须包含 Gate 调度表，定义每个 Gate 的 task 清单、harness 绑定和通过条件。

### 11.1 任务表（Task Table）

| task_id | phase | gate_id | dependency | input | output | acceptance_criteria | owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | 【待填写】 | G01 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

### 11.2 Gate 调度表（Gate Schedule）

**定义规则**：
- 每个 Gate 必须包含 `gate_id`、`tasks`（关联的 task_id 列表）、`pass_condition`（明确的通过条件）、`on_fail`（失败时的处理方式）
- gate_id 格式：`G_XX`（如 `G01`、`G02`），按执行顺序排列
- tasks 字段引用 11.1 表中定义的 task_id
- pass_condition 必须可验证（不能写"结果看起来不错"）
- 系统按 gate_id 顺序执行，前一个 Gate 未通过不得进入下一个

| gate_id | order | tasks | pass_condition | on_fail | status |
| --- | --- | --- | --- | --- | --- |
| G01 | 1 | 【待填写：例如 T01, T02】 | 【待填写：可验证的通过条件】 | 【待填写：retry / escalate / block】 | planned |
| G02 | 2 | 【待填写】 | 【待填写】 | 【待填写】 | planned |

**常见错误**：任务只写动作没有产物；任务之间没有依赖；学生不知道先做哪一个 gate；pass_condition 不可验证；Gate 之间的依赖未声明。

**证据边界**：任务完成只能由对应 harness、artifact 和日志证明。Gate 通过需要该 Gate 下所有 task 完成 + harness 通过或产生 documented blocker。

**验收标准**：学生能按 Gate 顺序执行任务，并在阻塞时写出 blocker 而不是编造结果。每个 Gate 的 pass_condition 在 PRD 审查时可被独立验证。

## 12. Harness 与验收标准（Harness and Acceptance Criteria）

**章节目标**：定义 unit、integration、experiment、reproduction harness，每个 harness 必须绑定到至少一个 gate_id 和 task_id。以及证据要求和 anti-mock policy。

### 12.1 Harness 表（Harness Table）

| harness_id | type | gate_id | task_id | command_or_blocker | required_output | pass_criteria | may_support_claim |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H01 | 【待填写：unit / integration / experiment / reproduction】 | G01 | T01 | 【待填写：可执行命令，或无法自动化的 blocker 原因】 | 【待填写：stdout/stderr/artifact 路径】 | 【待填写：可验证的通过条件】 | false |

### 12.2 Harness 类型要求（Harness Type Requirements）

| harness_type | min_seeds | require_independent_rerun | require_artifact_hash | may_support_claim |
| --- | --- | --- | --- | --- |
| unit | 1 | false | false | false |
| integration | 1 | false | false | false |
| reproduction | all_declared_seeds | true | true | true |
| experiment | all_declared_seeds | true | true | true |

### 12.3 Anti-Mock 政策（Anti-Mock Policy）

- mock / toy / synthetic / stub / cached / proxy output 只能用于 unit、smoke 或 harness plumbing。
- reproduction 和 experiment harness 必须使用真实数据、真实模型或真实代码、真实 baseline、真实 metric。
- claim-supporting harness 必须检查 `real_dataset_provenance_verified`、`real_model_provenance_verified`、`no_synthetic_or_mock_inputs` 和 `full_run_not_smoke`。
- 任何使用 mock 数据的 harness，其 `may_support_claim` 必须为 false。
- Engineering gate `G_NO_FAKE_ARTIFACTS` 和 `G_REAL_DATA_MODEL` 在 claim-supporting gate 执行前自动检查。

**常见错误**：harness 没有命令也没有 explicit blocker；full experiment 不要求 independent rerun；mock 被用于 claim；harness 不绑定 gate_id。

**证据边界**：mock / toy / synthetic / cached / proxy output 只能用于 unit 或 smoke，不能用于论文表格或 Go / No-Go。

**验收标准**：每个 task 和 experiment 都有 harness；每个 harness 都有 gate_id、task_id、输入、输出、schema、pass criteria 和 evidence capture。

## 13. 证据台账（Evidence Ledger）

**章节目标**：维护 claim-to-evidence、experiment-to-claim、current evidence status、missing evidence 和 paper admission rule。

**Evidence Ledger**

| claim_id | claim | evidence_status | required_experiment | source_artifact | limitation | paper_allowed |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | 【待填写】 | planned | E01 | 【待填写】 | 【待填写】 | false |

**常见错误**：paper claim 先于 evidence；缺失证据没有进入 gap report；负结果被隐藏。

**证据边界**：只有 evidence_status 为 observed 且通过独立复跑要求的结果，才可进入论文实证结论。

**验收标准**：任何论文 claim 都能追踪到实验、artifact、harness、限制和是否允许入文。

## 14. 论文计划（Paper Plan）

**章节目标**：规划 title、abstract logic、contributions、figures/tables、experiment-to-section mapping 和哪些内容必须等证据。

| paper_section | planned_content | required_evidence | placeholder |
| --- | --- | --- | --- |
| Main Results | 【待填写】 | E01 | `{{{{E01.OURS.primary_metric}}}}` |

**常见错误**：把 planned paper 写成 observed paper；使用未注册 placeholder；发明实验数值。

**证据边界**：可以写 “We propose / formulate / design / evaluate”，不能写 “Experiments show / outperforms / state-of-the-art”。

**验收标准**：每个未观察结果都绑定 placeholder_map.yaml，缺失内容进入 paper_gap_report.md。

## 15. 风险、局限与伦理（Risks, Limitations, and Ethics）

**章节目标**：记录 technical、experiment、theory、academic integrity、data / ethics / reproducibility risks，并给出 limitation plan。

| risk_id | risk | probability | impact | mitigation | fallback |
| --- | --- | --- | --- | --- | --- |
| RISK01 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**常见错误**：只写工程风险，不写学术诚信和可复现风险；没有降级路径；伦理风险空泛。

**证据边界**：风险章节不能用来掩盖证据不足，必须明确哪些 claim 因风险只能降级。

**验收标准**：每个高风险项都有监控信号、缓解动作、fallback 和 Go / No-Go 影响。

## 16. 探索与洞察策略（Exploration and Insight Policy）

**章节目标**：明确 PRD 是初始研究假设而非终局真理；定义执行失败与研究失败的分层；规定哪些调整可由 agent 自动完成，哪些必须请求人类确认；建立负结果记录和异常转化为新实验的机制。

**必须填写的信息**
- 初始假设声明：`【待填写：当前 idea 是初始假设，不是不可修改的真理】`。
- 可自动调整范围：`【待填写：执行修复、spec 细化、harness 改进、diagnostic experiment 提议、claim support 状态更新、负结果记录】`。
- 必须人类确认的范围：`【待填写：核心 RQ 修改、问题表述变更、主 claim 变更、论文故事线变更、宣称发现新现象、删除原始 baseline】`。
- Pivot 触发条件：`【待填写：哪些现象会触发 15 度微转向】`。
- 负结果策略：`【待填写：负结果必须记录到 docs/research/insights/negative_results/】`。
- 异常到实验的管道：`【待填写：异常 → insight log → anomaly report → diagnostic experiment proposal → human review】`。
- Insight 进入论文叙事的方式：`【待填写：洞察如何转化为论文的 insight-driven narrative】`。

| 调整类型 | 是否可自动执行 | 需要人类确认 | 记录位置 |
| --- | --- | --- | --- |
| 执行修复（代码/环境/路径） | 是 | 否 | plan/blocker_log.md |
| Spec 细化（命令/artifact/schema） | 是 | 否 | spec/ 对应文件 |
| Diagnostic experiment 提议 | 是 | 否（不改变核心假设时） | spec/experiments/ |
| 核心 RQ / 问题表述变更 | 否 | 是 | insights/pivot_proposals/ |
| 主 claim / 论文故事变更 | 否 | 是 | insights/pivot_proposals/ |
| 负结果记录 | 是 | 否 | insights/negative_results/ |
| Anomaly report | 是 | 否 | insights/anomaly_reports/ |

**常见错误**：把 PRD 当成不可修改的圣经；负结果被隐藏；agent 擅自修改核心 RQ；洞察不被记录。

**证据边界**：本章只定义策略和边界，不声称任何实验结果。

**验收标准**：读者能清楚说出哪些修改可以自动做、哪些必须等人批、负结果放哪里、异常怎么变成新实验。
"""


def research_prd_tex(title: str, purpose: str) -> str:
    escaped_title = latex_escape(title)
    escaped_purpose = latex_escape(purpose)
    placeholder_tex = r"\makecell[l]{\texttt{\{\{E01.OURS.}\\\texttt{primary\_metric\}\}}}"
    return rf"""% template_family: {TEMPLATE_FAMILY}
% template_version: {TEMPLATE_VERSION}
\documentclass[UTF8,11pt]{{ctexrep}}
\usepackage[a4paper,left=25mm,right=25mm,top=24mm,bottom=26mm]{{geometry}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs,tabularx,array,longtable}}
\usepackage{{makecell}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{tikz}}
\usepackage{{float}}
\usetikzlibrary{{arrows.meta,positioning,fit,shapes.geometric}}
\definecolor{{ResearchBlue}}{{HTML}}{{1F4E79}}
\definecolor{{ResearchGreen}}{{HTML}}{{E7F4EC}}
\definecolor{{ResearchSoftBlue}}{{HTML}}{{E9F1F8}}
\definecolor{{ResearchYellow}}{{HTML}}{{F8F1D9}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\tikzset{{
  researchnode/.style={{rectangle, rounded corners=2pt, draw=ResearchBlue, fill=ResearchSoftBlue, align=center, minimum height=8mm, minimum width=20mm, text width=20mm, font=\scriptsize}},
  researchprocess/.style={{researchnode, fill=ResearchGreen}},
  researchdecision/.style={{diamond, aspect=2, draw=ResearchBlue, fill=ResearchYellow, align=center, inner sep=1.5pt, font=\small}},
  researcharrow/.style={{-{{Latex[length=2.6mm,width=1.8mm]}}, thick, draw=ResearchBlue}}
}}
\hypersetup{{colorlinks=true, linkcolor=ResearchBlue, urlcolor=ResearchBlue, citecolor=ResearchBlue}}
\title{{{escaped_title}}}
\author{{Research Execution Skills}}
\date{{\today}}
\begin{{document}}
\maketitle
\tableofcontents
\clearpage

\chapter{{执行摘要（Executive Summary）}}
\textbf{{章节目标}}：用一页说明研究问题、预期贡献、最低可行目标与当前证据状态。

\begin{{table}}[H]
\centering
\caption{{What / Why / How / So What 摘要表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.18\textwidth}}Y}}
\toprule
维度 & 内容 \\
\midrule
What & 【待填写：研究对象与核心问题】 \\
Why & 【待填写：科学缺口、应用价值、审稿人会关心的理由】 \\
How & 【待填写：核心方法、数据、复现与实验路径】 \\
So What & 【待填写：预期学术贡献和可交付物】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

图 \ref{{fig:problem-evidence-chain}} 回答从研究问题到证据准入的主链路，并突出 Insight Loop：实验中的失败、异常和负结果可以反馈回假设，驱动 15 度微转向。
\begin{{figure}}[H]
\centering
\begin{{tikzpicture}}[node distance=0.65cm]
\node[researchnode] (problem) {{研究问题}};
\node[researchprocess, right=of problem] (hypothesis) {{可证伪假设}};
\node[researchprocess, right=of hypothesis] (experiment) {{实验 / 复现}};
\node[researchdecision, right=of experiment] (gate) {{Evidence\\Gate}};
\node[researchnode, right=of gate] (paper) {{论文主张}};
\node[researchprocess, below=of experiment, yshift=-0.3cm] (insight) {{Insight\\Loop}};
\draw[researcharrow] (problem) -- (hypothesis);
\draw[researcharrow] (hypothesis) -- (experiment);
\draw[researcharrow] (experiment) -- (gate);
\draw[researcharrow] (gate) -- (paper);
\draw[researcharrow, dashed, color=ResearchBlue] (experiment) -- (insight);
\draw[researcharrow, dashed, color=ResearchBlue] (insight) -- (hypothesis);
\end{{tikzpicture}}
\caption{{研究问题到证据链：突出论文主张必须通过证据门禁，且实验反馈可通过 Insight Loop 微调假设。}}
\label{{fig:problem-evidence-chain}}
\end{{figure}}

\textbf{{常见错误}}：把愿景写成已证明结论；把论文宣传语当成研究问题；不说明最低可行目标。

\textbf{{证据边界}}：本章只能写设计意图、研究假设和计划贡献；未执行实验不得写成经验结论。

\textbf{{验收标准}}：读者能用两句话复述项目问题、方法方向、最低目标和当前证据状态。最低可行研究目标：{escaped_purpose}。

\chapter{{背景教程（Background Tutorial）}}
\textbf{{章节目标}}：补齐学生理解后续章节所需的领域背景、基本概念、数学或系统知识。

\begin{{table}}[H]
\centering
\caption{{术语与前置知识表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.18\textwidth}}Y Y Y}}
\toprule
概念 & 大白话解释 & 正式定义 & 后文用途 \\
\midrule
【待填写：概念 A】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{必须填写的信息}}：领域背景、基本概念、必备数学 / 系统 / ML / 安全背景、常见初学者误解和研究价值。

\textbf{{常见错误}}：背景只堆论文名；公式前不解释直觉；术语首次出现没有定义。

\textbf{{证据边界}}：背景事实需要登记来源；本章不提出未经验证的新 claim。

\textbf{{验收标准}}：学生读完后能解释关键术语，并知道每个概念在方法或实验中的角色。

\chapter{{相关工作地图（Related Work Map）}}
\textbf{{章节目标}}：把研究谱系、代表方法、未解决问题和最接近基线组织成 reviewer 可检查的地图。

\begin{{table}}[H]
\centering
\caption{{相关工作差异表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.2\textwidth}}Y Y Y}}
\toprule
工作 / 方法 & 解决了什么 & 没解决什么 & 与本研究的关系 \\
\midrule
【待填写：P01】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：只写“我们不同”；没有说明为什么 baseline 对审稿人是公平的。
\textbf{{证据边界}}：相关工作支持已有方法边界，不能替代本项目实验证据。
\textbf{{验收标准}}：读者能指出最接近的 baseline 及本项目的最小可辩护差异。

\chapter{{基准与复现计划（Benchmark and Reproduction Plan）}}
\textbf{{章节目标}}：定义 benchmark 选择标准、候选论文矩阵、复现模式和失败降级策略。

\begin{{table}}[H]
\centering
\caption{{Benchmark Candidate Matrix}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.12\textwidth}}L{{0.12\textwidth}}Y L{{0.18\textwidth}}Y}}
\toprule
paper\_id & baseline\_id & 选择理由 & 复现模式 & 主要风险 \\
\midrule
【待填写：P01】 & 【待填写：B01】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

图 \ref{{fig:reproduction-flow}} 将 baseline 复现和主实验分开。读者应注意：复现证据只证明 baseline comparability，不直接证明我们的方法 claim。
\begin{{figure}}[H]
\centering
\begin{{tikzpicture}}[node distance=1.15cm]
\node[researchnode] (paper) {{候选论文}};
\node[researchprocess, right=of paper] (mode) {{复现模式\\分类}};
\node[researchprocess, right=of mode] (run) {{运行官方 / 适配代码}};
\node[researchprocess, below=of run] (convert) {{转换到\\artifact schema}};
\node[researchdecision, left=of convert] (tolerance) {{metric\\tolerance}};
\node[researchnode, left=of tolerance] (ready) {{可比较\\baseline}};
\draw[researcharrow] (paper) -- (mode);
\draw[researcharrow] (mode) -- (run);
\draw[researcharrow] (run) -- (convert);
\draw[researcharrow] (convert) -- (tolerance);
\draw[researcharrow] (tolerance) -- (ready);
\end{{tikzpicture}}
\caption{{实验与复现流程图：突出复现证据与主实验 claim 的边界。}}
\label{{fig:reproduction-flow}}
\end{{figure}}

\textbf{{常见错误}}：把 paper-based reimplementation 写成 official reproduction；悄悄改 baseline 核心算法。
\textbf{{证据边界}}：复现证据支持 baseline comparability，不直接证明我们的方法 claim。
\textbf{{验收标准}}：每个 baseline 都有复现模式、输入数据、metric tolerance、命令、artifact 和失败解释路径。

\chapter{{问题陈述（Problem Statement）}}
\textbf{{章节目标}}：把研究问题从直觉陈述收敛为可形式化、可实验、可证伪的问题定义。

\begin{{table}}[H]
\centering
\caption{{范围与非目标表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.18\textwidth}}Y Y Y}}
\toprule
边界项 & In Scope & Out of Scope & 原因 \\
\midrule
【待填写：任务边界】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：问题定义过宽；Non-goals 缺失；把实现便利性当成研究边界。
\textbf{{证据边界}}：问题定义可以来自理论和文献，但有效性由实验或证明支持。
\textbf{{验收标准}}：学生能判断一个新任务、新数据集或新 claim 是否属于本项目范围。

\chapter{{研究问题与假设（Research Questions and Hypotheses）}}
\textbf{{章节目标}}：把 RQ、Hypothesis、Expected Claim、Experiment、Falsification 绑定起来。

\begin{{table}}[H]
\centering
\caption{{RQ / Hypothesis / Claim 映射表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.09\textwidth}}Y L{{0.1\textwidth}}Y Y L{{0.12\textwidth}}}}
\toprule
RQ & 研究问题 & 假设 & 预期 claim & 证伪条件 & 实验 \\
\midrule
RQ1 & 【待填写：开放但可回答的问题】 & H1 & 【待填写】 & 【待填写】 & E01 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：RQ 写成 yes/no 宣传句；假设不可证伪；expected claim 没有实验绑定。
\textbf{{证据边界}}：Expected claim 只表示计划主张；执行前不得写成经验结论。
\textbf{{验收标准}}：每个 RQ 都能追踪到 hypothesis、claim、experiment 或 proof task。

\chapter{{形式化定义（Formalization）}}
\textbf{{章节目标}}：给出 notation、objective、constraints、optimization target / system target 和理论直觉。

\begin{{table}}[H]
\centering
\caption{{符号表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.14\textwidth}}Y Y Y}}
\toprule
符号 & 含义 & 取值范围 & 直觉解释 \\
\midrule
【待填写：x】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：公式没有解释符号；理论直觉与实验设计脱节。
\textbf{{证据边界}}：形式化提供可检验结构，不自动证明方法有效。
\textbf{{验收标准}}：学生能从符号表读到目标函数，并解释约束如何影响实现或实验。

\chapter{{拟议方法（Proposed Method）}}
\textbf{{章节目标}}：描述 method overview、key idea、module breakdown、algorithm / workflow、complexity 和 failure modes。

图 \ref{{fig:method-modules}} 展示方法模块拆分。读者应关注模块输入输出，而不是把方法当成一个不可拆的黑盒。
\begin{{figure}}[H]
\centering
\begin{{tikzpicture}}[node distance=0.65cm]
\node[researchnode] (input) {{输入数据}};
\node[researchprocess, right=of input] (encoder) {{模块 M01\\表示 / 解析}};
\node[researchprocess, right=of encoder] (reasoner) {{模块 M02\\优化 / 推理}};
\node[researchprocess, right=of reasoner] (validator) {{模块 M03\\验证 / 约束}};
\node[researchnode, right=of validator] (output) {{输出 artifact}};
\draw[researcharrow] (input) -- (encoder);
\draw[researcharrow] (encoder) -- (reasoner);
\draw[researcharrow] (reasoner) -- (validator);
\draw[researcharrow] (validator) -- (output);
\end{{tikzpicture}}
\caption{{方法模块图：突出拟议方法的输入、模块边界与输出 artifact。}}
\label{{fig:method-modules}}
\end{{figure}}

\begin{{table}}[H]
\centering
\caption{{方法模块契约表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.14\textwidth}}Y Y Y Y}}
\toprule
module\_id & 模块职责 & 输入 & 输出 & 失败模式 \\
\midrule
M01 & 【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：只写概念不写模块接口；忽略复杂度和失败模式；把工程 trick 写成主要科学贡献。
\textbf{{证据边界}}：方法可以用“我们提出 / 我们设计”，但不得声称优于 baseline。
\textbf{{验收标准}}：学生能按模块拆分实现任务，并知道每个模块的输入输出和失败条件。

\chapter{{系统与实现设计（System and Implementation Design）}}
\textbf{{章节目标}}：把方法转换成可实现的代码结构、数据流、配置系统和可复现工程边界。

\begin{{table}}[H]
\centering
\caption{{组件实现契约表}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.16\textwidth}}Y Y Y Y}}
\toprule
component & path\_hint & responsibility & input / output & harness \\
\midrule
【待填写：组件】 & 【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：实验脚本、训练代码和评估代码职责混乱；没有配置版本；artifact schema 不稳定。
\textbf{{证据边界}}：实现完成不等于研究 claim 成立，claim 由 harness 和 evidence contract 决定。
\textbf{{验收标准}}：学生能据此创建模块、配置、日志、artifact，并知道哪些文件不能手工伪造。

\chapter{{实验设计（Experiment Design）}}
\textbf{{章节目标}}：定义 dataset、baseline、metric、main experiments、ablation、sensitivity、failure-case 和 statistical protocol。

\begin{{table}}[H]
\centering
\caption{{Experiment Matrix}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.12\textwidth}}L{{0.1\textwidth}}L{{0.12\textwidth}}Y Y Y}}
\toprule
experiment & rq & dataset & baselines & metrics / seeds & support / falsification \\
\midrule
E01 & RQ1 & D01 & B01 & M01 / 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：没有 frozen split；只跑一个 seed；ablation 同时改变多个变量；失败案例不记录。
\textbf{{证据边界}}：smoke test 不能支持 research claim；主实验必须完成所有声明 seed、baseline、metric 和 artifact hash。
\textbf{{验收标准}}：每个实验都有可执行命令、artifact、harness、统计协议和证伪条件。

\chapter{{任务图与学生工作计划（Task Graph and Student Work Plan）}}
\textbf{{章节目标}}：把研究拆成 phase、task、dependencies、acceptance criteria、weekly milestones 和 Go / No-Go checkpoint。本版本必须包含 Gate 调度表。

\subsection*{{任务表（Task Table）}}

\begin{{table}}[H]
\centering
\caption{{Task Graph Table}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.10\textwidth}}L{{0.10\textwidth}}L{{0.10\textwidth}}Y Y Y}}
\toprule
task\_id & phase & gate\_id & 依赖 & 输出 & 验收 \\
\midrule
T01 & 【待填写】 & G01 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\subsection*{{Gate 调度表（Gate Schedule）}}

\textbf{{定义规则}}：每个 Gate 必须包含 gate\_id、tasks（关联的 task\_id 列表）、pass\_condition（明确的通过条件）、on\_fail（失败时的处理方式）。gate\_id 格式为 G\_XX，按执行顺序排列。系统按 gate\_id 顺序执行，前一个 Gate 未通过不得进入下一个。pass\_condition 必须可验证。

\begin{{table}}[H]
\centering
\caption{{Gate Schedule Table}}
{{\footnotesize
\setlength{{\tabcolsep}}{{3pt}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.09\textwidth}}L{{0.07\textwidth}}L{{0.16\textwidth}}Y Y L{{0.12\textwidth}}}}
\toprule
\makecell[l]{{gate\\id}} & order & tasks & \makecell[l]{{pass\\condition}} & \makecell[l]{{on\\fail}} & status \\
\midrule
G01 & 1 & 【待填写：例如 T01, T02】 & 【待填写：可验证的通过条件】 & 【待填写：retry / escalate / block】 & planned \\
G02 & 2 & 【待填写】 & 【待填写】 & 【待填写】 & planned \\
\bottomrule
\end{{tabularx}}
}}
\end{{table}}

图 \ref{{fig:spec-plan-audit-loop}} 说明 Spec、Plan 与 Audit 的执行闭环。读者应注意：Plan 是 dated run，不得替代全局 Spec。
\begin{{figure}}[H]
\centering
\begin{{tikzpicture}}[node distance=1.4cm]
\node[researchnode] (prd) {{Research PRD\\人类真源}};
\node[researchprocess, right=of prd] (spec) {{Research Spec\\全局执行契约}};
\node[researchprocess, right=of spec] (plan) {{Research Plan\\日期化执行}};
\node[researchdecision, below=of plan] (audit) {{Research\\Audit}};
\node[researchnode, left=of audit] (artifacts) {{Artifacts\\Evidence}};
\draw[researcharrow] (prd) -- (spec);
\draw[researcharrow] (spec) -- (plan);
\draw[researcharrow] (plan) -- (artifacts);
\draw[researcharrow] (artifacts) -- (audit);
\draw[researcharrow] (audit) -- (spec);
\end{{tikzpicture}}
\caption{{Spec、Plan 与 Audit 执行闭环：突出全局契约、日期化执行和漂移修复之间的关系。}}
\label{{fig:spec-plan-audit-loop}}
\end{{figure}}

\textbf{{常见错误}}：任务只写动作没有产物；任务之间没有依赖；学生不知道先做哪一个 gate；pass condition 不可验证；Gate 之间的依赖未声明。
\textbf{{证据边界}}：任务完成只能由对应 harness、artifact 和日志证明。Gate 通过需要该 Gate 下所有 task 完成 + harness 通过或产生 documented blocker。
\textbf{{验收标准}}：学生能按 Gate 顺序执行任务，并在阻塞时写 blocker 而不是编造结果。每个 Gate 的 pass\_condition 在 PRD 审查时可被独立验证。

\chapter{{Harness 与验收标准（Harness and Acceptance Criteria）}}
\textbf{{章节目标}}：定义 unit、integration、experiment、reproduction harness，每个 harness 必须绑定到至少一个 gate\_id 和 task\_id。以及证据要求和 anti-mock policy。

\begin{{table}}[H]
\centering
\caption{{Harness Acceptance Table}}
{{\footnotesize
\setlength{{\tabcolsep}}{{3pt}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.10\textwidth}}L{{0.11\textwidth}}L{{0.08\textwidth}}L{{0.08\textwidth}}Y Y L{{0.08\textwidth}}}}
\toprule
\makecell[l]{{harness\\id}} & type & \makecell[l]{{gate\\id}} & \makecell[l]{{task\\id}} & 命令 / 阻塞 & 输出 & 支撑 claim \\
\midrule
H01 & 【待填写】 & G01 & T01 & 【待填写】 & 【待填写】 & false \\
\bottomrule
\end{{tabularx}}
}}
\end{{table}}

\textbf{{Harness 类型要求}}：unit / integration 不要求多 seed 或 independent rerun。reproduction / experiment 必须使用所有声明的 seed、真实 baseline 和 metric，要求 independent rerun，并记录 artifact hash。

\begin{{flushleft}}
\textbf{{Anti-Mock 政策}}：mock / toy / synthetic / stub / cached / proxy output 只能用于 unit、smoke 或 harness plumbing。reproduction 和 experiment harness 必须使用真实数据、真实模型或真实代码，并检查 real dataset / real model provenance、no synthetic or mock inputs 和 full run not smoke。工程门禁 G\_NO\_FAKE\_ARTIFACTS 与 G\_REAL\_DATA\_MODEL 在 claim-supporting gate 执行前检查。
\end{{flushleft}}

\textbf{{常见错误}}：harness 没有命令也没有 explicit blocker；full experiment 不要求 independent rerun；mock 被用于 claim。
\textbf{{证据边界}}：mock / toy / synthetic / cached / proxy output 只能用于 unit 或 smoke，不能用于论文表格或 Go / No-Go。
\textbf{{验收标准}}：每个 task 和 experiment 都有 harness；每个 harness 都有输入、输出、schema、pass criteria 和 evidence capture。

\chapter{{证据台账（Evidence Ledger）}}
\textbf{{章节目标}}：维护 claim-to-evidence、experiment-to-claim、current evidence status、missing evidence 和 paper admission rule。

\begin{{table}}[H]
\centering
\caption{{Evidence Ledger}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.12\textwidth}}Y L{{0.14\textwidth}}L{{0.16\textwidth}}Y L{{0.1\textwidth}}}}
\toprule
Claim & 内容 & 状态 & artifact & 限制 & 入文 \\
\midrule
C01 & 【待填写】 & planned & 【待填写】 & 【待填写】 & false \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：paper claim 先于 evidence；缺失证据没有进入 gap report；负结果被隐藏。
\textbf{{证据边界}}：只有 evidence\_status 为 observed 且通过独立复跑要求的结果，才可进入论文实证结论。
\textbf{{验收标准}}：任何论文 claim 都能追踪到实验、artifact、harness、限制和是否允许入文。

\chapter{{论文计划（Paper Plan）}}
\textbf{{章节目标}}：规划 title、abstract logic、contributions、figures/tables、experiment-to-section mapping 和哪些内容必须等证据。

\begin{{table}}[H]
\centering
\caption{{Paper Placeholder Plan}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.18\textwidth}}Y Y Y}}
\toprule
章节 & 内容 & 证据 & placeholder \\
\midrule
Main Results & 【待填写】 & E01 & {placeholder_tex} \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：把 planned paper 写成 observed paper；使用未注册 placeholder；发明实验数值。
\textbf{{证据边界}}：可以写 “We propose / formulate / design / evaluate”，不能写 “Experiments show / outperforms / state-of-the-art”。
\textbf{{验收标准}}：每个未观察结果都绑定 placeholder\_map.yaml，缺失内容进入 paper\_gap\_report.md。

\chapter{{风险、局限与伦理（Risks, Limitations, and Ethics）}}
\textbf{{章节目标}}：记录 technical、experiment、theory、academic integrity、data / ethics / reproducibility risks，并给出 limitation plan。

\begin{{table}}[H]
\centering
\caption{{Risk Matrix}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.12\textwidth}}Y L{{0.12\textwidth}}L{{0.12\textwidth}}Y}}
\toprule
risk\_id & risk & probability & impact & mitigation / fallback \\
\midrule
RISK01 & 【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\textbf{{常见错误}}：只写工程风险，不写学术诚信和可复现风险；没有降级路径；伦理风险空泛。
\textbf{{证据边界}}：风险章节不能用来掩盖证据不足，必须明确哪些 claim 因风险只能降级。
\textbf{{验收标准}}：每个高风险项都有监控信号、缓解动作、fallback 和 Go / No-Go 影响。

\end{{document}}
"""


def planned_paper_markdown(title: str) -> str:
    return f"""# {title}

> Planned Research Paper Template for NeurIPS / ICLR / AAAI style writing.
> This is a planned manuscript derived from the Research PRD. It may use assertive present-tense language for designed artifacts, but it must not claim unvalidated empirical findings.

## Abstract

We propose 【待填写：method name or research program】 for 【待填写：problem setting】. The paper formulates 【待填写：formal problem】, designs 【待填写：method or system】, and defines an evaluation protocol grounded in the Research PRD and Research Spec. Do not write empirical conclusions before evidence. Unobserved values must remain experiment-bound placeholders after registration.

## 1. Introduction

**Purpose**: Establish motivation, research gap, and contribution logic with a top-conference narrative.

**Template paragraphs**

1. Problem pressure: 【待填写：why the problem matters now】.
2. Limitation of prior work: 【待填写：specific gap from Related Work Map】.
3. Key idea: We propose 【待填写：core idea】.
4. Contributions:
   - We formulate 【待填写：formalization contribution】.
   - We design 【待填写：method/system contribution】.
   - We evaluate through 【待填写：planned experiments from Spec, not invented from Paper】.

**Evidence boundary**: This section can motivate and propose; it cannot report empirical superiority.

## 2. Related Work and Research Gap

**Purpose**: Convert PRD related-work map into a concise reviewer-facing comparison.

| Thread | Representative work | What it solves | Remaining gap | Our boundary |
| --- | --- | --- | --- | --- |
| 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**Writing rule**: Do not use vague novelty language. State exact differences in task setting, objective, evidence, or system assumptions.

## 3. Problem Formulation

**Purpose**: Translate PRD formalization into paper notation.

| Symbol | Meaning | Domain | Used in |
| --- | --- | --- | --- |
| 【待填写】 | 【待填写】 | 【待填写】 | Objective / Constraint |

**Required content**

- Informal problem definition.
- Formal input/output definition.
- Objective or system target.
- Assumptions and scope.
- Falsification-relevant constraints.

## 4. Method

**Purpose**: Present the proposed method with a clean method narrative.

**Allowed assertive language**

- We propose 【待填写】.
- We formulate 【待填写】.
- We design 【待填写】.
- We introduce 【待填写】.

| Module | Role | Input | Output | Failure mode |
| --- | --- | --- | --- | --- |
| 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

**Method figure plan**: 【待填写：which figure from PRD should become Figure 1】.

## 5. Evaluation Plan

**Purpose**: Describe the planned evaluation without fabricating results.

| Experiment | Linked RQ | Dataset | Baselines | Metrics | Placeholder pattern |
| --- | --- | --- | --- | --- | --- |
| E01 | RQ1 | D01 | B01 | M01 | PLACEHOLDER_PATTERN: E01.OURS.primary_metric |

**Required content**

- Dataset and split protocol from Spec.
- Baseline and reproduction modes from Spec.
- Metrics and statistical protocol from Spec.
- Main experiments, ablations, sensitivity, and failure-case analysis.

## 6. Planned Results and Placeholder Discipline

**Purpose**: Reserve result locations while preventing fake empirical claims.

| Paper location | Required experiment | Metric | Source after execution |
| --- | --- | --- | --- |
| Table 1 / Main Results | E01 | primary_metric | artifacts/experiments/E01/aggregate/summary.json |

**Rules**

- Before execution, use registered placeholders only after the corresponding experiment exists in Spec.
- Use phrasing such as “Table 1 reports PLACEHOLDER_PATTERN after execution.”
- Do not write empirical conclusions before evidence.
- If a claim, dataset, baseline, metric, formula, or table is missing, record it in `paper_gap_report.md`.

## 7. Limitations and Ethics

**Purpose**: Preserve academic integrity by stating what the planned study cannot yet claim.

| Limitation | Why it matters | Evidence needed | Paper handling |
| --- | --- | --- | --- |
| 【待填写】 | 【待填写】 | 【待填写】 | 【待填写】 |

## Appendix Plan

- Reproducibility checklist.
- Additional benchmark details.
- Hyperparameter and seed protocol.
- Full placeholder map.
- Extended limitations and negative-result policy.
"""


def planned_paper_tex(title: str) -> str:
    escaped_title = latex_escape(title)
    return rf"""\documentclass[UTF8,11pt]{{ctexart}}
\usepackage[a4paper,left=24mm,right=24mm,top=24mm,bottom=26mm]{{geometry}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs,tabularx,array}}
\usepackage{{hyperref}}
\usepackage{{xcolor}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\hypersetup{{colorlinks=true, linkcolor=blue, urlcolor=blue, citecolor=blue}}
\emergencystretch=2em
\title{{Planned Research Paper\\\large {escaped_title}}}
\author{{Research Execution Skills}}
\date{{\today}}
\begin{{document}}
\maketitle

\begin{{abstract}}
We propose 【待填写：method name or research program】 for 【待填写：problem setting】. The paper formulates 【待填写：formal problem】, designs 【待填写：method or system】, and defines an evaluation protocol grounded in the Research PRD and Research Spec. Do not write empirical conclusions before evidence. Unobserved values must remain experiment-bound placeholders after registration.
\end{{abstract}}

\section{{Introduction}}
\textbf{{Purpose}}: Establish motivation, research gap, and contribution logic with a NeurIPS / ICLR / AAAI style narrative.

\begin{{itemize}}
\item Problem pressure: 【待填写：why the problem matters now】.
\item Limitation of prior work: 【待填写：specific gap from Related Work Map】.
\item Key idea: We propose 【待填写：core idea】.
\item Contributions: formulate, design, and evaluate only through PRD/Spec-bound experiments.
\end{{itemize}}

\section{{Related Work and Research Gap}}
\begin{{table}}[htbp]
\centering
\caption{{Related-work gap map}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.16\textwidth}}Y Y Y Y}}
\toprule
Thread & Work & Solves & Gap & Boundary \\
\midrule
【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\section{{Problem Formulation}}
\begin{{table}}[htbp]
\centering
\caption{{Notation table}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.16\textwidth}}Y Y Y}}
\toprule
Symbol & Meaning & Domain & Used in \\
\midrule
【待填写】 & 【待填写】 & 【待填写】 & Objective / Constraint \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\section{{Method}}
We propose 【待填写】, formulate 【待填写】, and design 【待填写】.

\begin{{table}}[htbp]
\centering
\caption{{Method module contract}}
\begin{{tabularx}}{{\textwidth}}{{L{{0.16\textwidth}}Y Y Y Y}}
\toprule
Module & Role & Input & Output & Failure mode \\
\midrule
【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\section{{Evaluation Plan}}
\begin{{table}}[htbp]
\centering
\caption{{Planned experiment map}}
\begin{{tabularx}}{{\textwidth}}{{@{{}}L{{0.12\textwidth}}L{{0.16\textwidth}}L{{0.2\textwidth}}Y@{{}}}}
\toprule
Exp. & RQ / Data & Baseline / Metric & Placeholder \\
\midrule
E01 & RQ1 / D01 & B01 / M01 & \shortstack[l]{{PLACEHOLDER\\E01.OURS.metric}} \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\section{{Planned Results and Placeholder Discipline}}
\begin{{itemize}}
\item Before execution, reserve result locations but do not write empirical conclusions.
\item Missing claims, datasets, baselines, metrics, formulas, or tables must be recorded in the paper gap report.
\item A placeholder can enter the paper only after the corresponding experiment exists in Spec.
\end{{itemize}}

\section{{Limitations and Ethics}}
\begin{{table}}[htbp]
\centering
\caption{{Limitation plan}}
\begin{{tabularx}}{{\textwidth}}{{Y Y Y Y}}
\toprule
Limitation & Why it matters & Evidence needed & Paper handling \\
\midrule
【待填写】 & 【待填写】 & 【待填写】 & 【待填写】 \\
\bottomrule
\end{{tabularx}}
\end{{table}}

\appendix
\section{{Appendix Plan}}
Reproducibility checklist, benchmark details, hyperparameter and seed protocol, full placeholder map, and negative-result policy.

\end{{document}}
"""


def latex_from_markdown(markdown: str) -> str:
    lines = [
        r"\documentclass[UTF8,11pt]{ctexart}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{hyperref}",
        r"\title{Research Artifact}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
    ]
    for line in markdown.splitlines():
        if line.startswith("# "):
            lines.append(r"\section*{" + latex_escape(line[2:]) + "}")
        elif line.startswith("## "):
            lines.append(r"\subsection*{" + latex_escape(line[3:]) + "}")
        elif line.strip():
            lines.append(latex_escape(line) + r"\par")
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def research_direction_template(title: str, purpose: str) -> str:
    today = today_string()
    return f"""# Research Direction

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

## 0. Direction Status

- direction_id: `DIR-{slugify(title).upper()}`
- status: draft
- created_at: {today}
- updated_at: {today}
- current_version: V0
- final_target: paper_binding
- owner_decision_required: true

## 1. Research Seed

### A. ad hoc idea

- seed_summary: `【待填写：尚未验证的研究直觉、机制假设或方法想法】`
- minimum_viable_purpose: `{purpose}`

### B. follow-up from existing paper

- source_type: `【待填写：如不基于已有论文，写 none】`
- gap_or_limitation: `【待填写：已有论文中的 gap、limitation、unanswered question、unfair baseline 或未充分验证机制】`

## 2. Research Corridor

- `【待填写：允许探索方向 1，例如 MoE routing analysis】`
- `【待填写：允许探索方向 2，例如 expert-DAG / expert-subgraph representation】`
- `【待填写：允许探索方向 3，例如 routing trace / routing intervention】`

## 3. Out-of-Scope Directions

- 与核心研究问题无关的普通 prompt engineering
- 与 Research Corridor 无关的普通工程优化
- 纯产品化工具但没有科研 claim
- 没有证据链的论文叙事重写
- 超出用户授权的全新研究主题

## 4. Prior Work Basis

- paper_id: `【待填写：如无则写 none】`
- title: `【待填写：论文标题或 none】`
- citation_or_url: `【待填写：文献占位或 literature blocker】`
- relationship_to_project: `【待填写：与本项目的关系】`
- inherited_claims: `【待填写：继承哪些 claim；没有则写 none】`
- questioned_claims: `【待填写：质疑哪些 claim；没有则写 none】`
- follow_up_gaps: `【待填写：继续研究哪些 gap】`
- must_compare_baselines: `【待填写：必须比较的 baseline】`
- novelty_risk: `【待填写：novelty risk 或 literature blocker】`

> 如果当前环境无法联网或未完成检索，必须写入 literature blocker，不得编造文献。

## 5. Desired Paper Shape

优先级从高到低：

1. mechanism analysis paper
2. method paper
3. causal intervention paper
4. benchmark / tooling paper
5. diagnostic paper
6. negative result paper

## 6. Autonomy Boundary

### AI 可以自动做

- 起草 Vn/PRD.md
- 编译 Vn/SPEC.yaml
- 生成 Vn/PLAN.md
- 维护 TASK_QUEUE.yaml
- 实现代码 scaffold
- 写测试
- 写 run report
- 写 wiki
- 写 closeout
- 在研究走廊内起草 Vn+1/PRD.md

### AI 不可以自动做

- 修改 RESEARCH_DIRECTION.md 的核心方向
- pivot 到 Out-of-Scope Directions
- 把 exploratory insight 写成 paper result
- 伪造实验、benchmark、harness、stdout/stderr 或 artifact
- 宣称未验证 claim 已稳定
- 在当前版本未 closeout 前创建下一版本
- 在 closed_stable 前进行 Paper Binding

## 7. Global Stop Conditions

- 连续两个版本没有产生任何可复用 insight
- 核心机制被反复反驳
- 所有可行版本都被 hard gate 阻断
- 需要超出预算的数据、算力或权限
- novelty risk 无法解决
- paper binding 已完成
"""


def research_index_template() -> str:
    return """# Research Workspace Index

## Authority Chain

```text
RESEARCH_DIRECTION.md
  -> CURRENT
  -> Vn/PRD.md
  -> Vn/SPEC.yaml
  -> Vn/PLAN.md
  -> Vn/TASK_QUEUE.yaml
  -> Vn/runs + Vn/artifacts
  -> Vn/audits
  -> research-insight
  -> Vn/wiki
  -> Vn/closeout.md
  -> Vn+1/PRD.md 或 paper binding
```

## Current Epoch

读取 `CURRENT` 得到当前版本。旧版本只作为 context / memory / history，不再有执行权。

## Legacy Workspace

旧目录 `prd/`、`paper/`、`spec/`、`plans/`、`audits/`、`insights/` 保留为 legacy workspace。新版默认采用 `V0/`、`V1/`、`V2/` 的 epoch 结构，当前 insight 真源是 `Vn/wiki/*`。
"""


def agent_runbook_template() -> str:
    return """# Research Agent Runbook

## Definition

自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

## Read Order

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.md`
7. `docs/research/{CURRENT}/SPEC.yaml`
8. `docs/research/{CURRENT}/PLAN.md`

旧版本只读 `closeout.md` 和 `wiki/` 中的 `epoch_summary.md`、`evidence_map.md`、`positive_signals.md`、`negative_results.md`、`failed_paths.md`、`next_version_seed.md`。禁止让旧版本 PRD 覆盖当前版本 PRD。

## Epoch Loop

Frame -> Contract -> Plan -> Execute -> Gate -> Interpret -> Wiki -> Closeout -> Next Version or Paper Binding

## Explore / Git / Audit Closure

Explore 负责想，Vn 负责做，Git 负责记，Insight 负责解释，Wiki 负责沉淀，Audit 负责守门，Closeout 负责进入下一轮或论文绑定。

- `/research explore` 是纯探索入口：可以讨论 idea、文献、baseline、novelty、next-version framing；可以保存 explore session；不能直接改 PRD、Spec、Plan、Paper Binding。
- `research-insight` 是显式解释入口：只把已有 run、artifact、blocker、negative result、failed path 或 explore session 沉淀到当前 `Vn/wiki/*`。
- Git Memory Layer 记录每个 task、gate、closeout、paper binding 的 branch、commit、diff、tag 和 dirty-tree 状态；禁止 push、reset、clean、rebase、force push，除非用户明确授权。
- Audit Modernization 覆盖 format、migration、epoch、git、evidence、paper-binding、full modes；audit 可以检测、分类、生成 migration plan，但不能默认改写研究主张或把旧 insight 变成 paper evidence。

## Status Handling

- `initialized`：完善并人工批准 Direction 与 PRD。
- `prd_locked`：从 PRD 编译 SPEC。
- `spec_ready`：从 SPEC 生成 PLAN、TASK_QUEUE、ai_loop_prompt。
- `plan_ready` / `running`：只执行 TASK_QUEUE 中的 active task。
- `gate_blocked`：解释 blocker，更新 wiki，准备 closeout。
- `interpreting`：写 wiki 与 closeout。
- `closed_*`：根据 closeout 决定 Vn+1 或停止。
- `closed_stable` / `paper_binding_ready`：允许 Paper Binding。

## Next Version Rule

工程问题留在当前版本；研究问题改变才开下一版本。

创建 Vn+1 的条件：当前 closeout 完成，且 `create_next_version: true`；或计划完成后研究问题变化；或 hard gate 阻断后 wiki 给出更合理 framing；或核心假设被负结果反驳；或 baseline、metric、dataset、model 选择改变主 claim；或 exploration 结束需要进入 confirmatory/intervention/training 阶段。

不创建 Vn+1：修 bug、补 artifact path、修测试、增加 sanity check、重跑 seed、小 baseline 补充、Spec 字段补全、Paper placeholder 修正、Plan stale 后重新生成。

## Paper Binding

只有当前版本 `status=closed_stable` 或 `paper_binding_ready`，且 `PAPER_BINDING_DECISION.md` 明确允许，才能把结果绑定到 paper。Exploratory insight 只能进入 motivation / discussion，不能写成 main result。
"""


def claude_loop_prompt_template() -> str:
    return """# Claude Code Ralph-loop Prompt

你处于 ralph-loop 持续循环中。每轮收到相同的提示词，但通过读取持久化的状态文件来推进研究。每轮只执行一个原子任务。

## Per-Iteration Workflow

### Step 1: Read state files

严格按顺序读取：

1. `docs/research/RESEARCH_DIRECTION.md` — 研究走廊边界
2. `docs/research/CURRENT` — 当前 epoch 版本号
3. `docs/research/{CURRENT}/STATUS.yaml` — 当前状态
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml` — 任务详情（success_criteria、test_commands、evidence_required）

### Step 2: Check termination conditions

读取 STATUS.yaml 后，先检查是否该停止：

- 若 `status` 为 `closed_success`、`closed_negative`、`closed_blocked`、`closed_falsified`、`closed_pivot_required`、`closed_stable` 或 `paper_binding_ready`：
  输出 `<promise>RESEARCH_COMPLETE</promise>` 并停止。
- 若 `status` 为 `gate_blocked` 且 `runs/TASK_XXX_blocker.md` 存在：
  输出 `<promise>RESEARCH_BLOCKED</promise>` 并停止。

### Step 3: Execute the task


- 若任务是**代码实现**：写代码、写测试、运行测试、记录 terminal 输出
- 若任务是**实验执行**：运行声明 harness、保存 stdout/stderr、记录 artifact hash
- 若任务是**文献调研**：搜索、阅读、写 literature_notes.md
- 若任务是**文档撰写**：编辑 PRD/wiki/closeout 等文件
- 若任务引用 subagent（如 `research-coding`、`research-experiment`），用 Agent 工具委派

### Step 4: Record evidence

- 代码变更：运行 `git status --short` 和 `git diff --stat`
- 实验执行：保存 stdout/stderr 到 `runs/` 目录
- 所有任务：写 `runs/TASK_XXX_report.md`

run report 最小格式：
```markdown
# TASK_XXX Report
- task_id: TASK_XXX
- status: done | blocked
- command_or_action: 执行过的命令或动作
- evidence: stdout/stderr/artifact 路径
- diff_summary: git diff --stat 输出（如有代码变更）
- commit_hash: abc123（如有提交）
- next_action: 下一个原子动作建议
```

### Step 5: Update state files

更新以下文件以推进状态：

1. `LOOP_LOG.md` — 追加一条 loop entry
2. `TASK_QUEUE.yaml` — 当前 task status 改为 `done` 或 `blocked`；下一个 task status 改为 `active`
4. `STATUS.yaml` — 若 gate 通过或阻塞，更新 status
5. `GIT_STATE.yaml` — 若有 commit，记录 commit hash

### Step 6: Check for gate boundary

若刚完成的任务是一个 gate 的最后一个 task，调用 `research-insight` 更新 `Vn/wiki/*`（epoch_summary、evidence_map、positive_signals 或 negative_results）。

## Document-Writing vs Execution Boundary

- When the active task involves **writing, editing, or compiling research documents** (PRD, SPEC, PLAN, RESEARCH_SPINE, ai_loop_prompt.md, goal.md, CODEX_GOAL_TEMPLATE.md), and you detect ambiguity, contradiction, or a decision that would change the research direction, core hypothesis, baseline selection, metric choice, or evidence boundary: **stop and ask the user before proceeding**. Do not choose the most convenient interpretation. Record the request in `HUMAN_REVIEW_REQUESTS.yaml`.
- When the active task involves **execution** (running harnesses, writing implementation code, running tests, collecting artifacts, reproducing baselines): **do not stop to ask for preference clarification**. Proceed autonomously. Record blockers only for missing required data (dataset paths, commands, seeds, artifacts), not for ambiguous design choices.

## Rules

- Stay inside Research Corridor（不得超越 RESEARCH_DIRECTION.md 定义的边界）。
- Do not modify `RESEARCH_DIRECTION.md` unless the user explicitly asks.
- Do not create the next version unless current version is closed and closeout exists.
- Do not fabricate execution result, artifact, benchmark, stdout/stderr, or paper result.
- Never rely on previous chat memory as evidence — only persisted files are authoritative.
- If the same task fails twice with the same cause, escalate to `gate_blocked` in STATUS.yaml.
- If code changes are required, run the relevant tests and record terminal evidence.
- If literature is required but web access is unavailable, write `docs/research/{CURRENT}/runs/LITERATURE_REQUIRED_BLOCKER.md`.
"""


def codex_goal_template() -> str:
    return """# Codex Goal

## Goal


## Context

Read:

- `docs/research/RESEARCH_DIRECTION.md`
- `docs/research/CURRENT`
- `docs/research/{CURRENT}/STATUS.yaml`
- `docs/research/{CURRENT}/TASK_QUEUE.yaml`
- `docs/research/{CURRENT}/PRD.md`
- `docs/research/{CURRENT}/SPEC.yaml`
- `docs/research/{CURRENT}/PLAN.md`

## Deliverables

- `【待填写：必须改动或生成的文件】`

## Constraints

- Stay inside Research Corridor.
- Do not modify `RESEARCH_DIRECTION.md`.
- Do not create next version unless current version is closed.
- Do not write paper results.
- Do not claim real benchmark execution unless actually run.
- If prompt-only, explicitly mark `prompt_only_scaffold`.

## Ask vs Autonomy Boundary

- If this goal requires **writing or modifying PRD, SPEC, PLAN, RESEARCH_SPINE, or goal.md**, and you encounter ambiguity about the user's intent, contradictory requirements, or a scope/hypothesis/methodology decision: **stop and ask the user** before proceeding. Record the ambiguity in `HUMAN_REVIEW_REQUESTS.yaml`.
- If this goal requires **implementation or experiment execution** (code, harness, test, artifact collection), proceed autonomously. Do not ask for preference clarification. Record blockers only for missing required files or commands.

## Validation

Run:

```bash
python3 -m pytest tests -q
```

如当前任务不需要测试，必须写明原因。

## Done When

- success_criteria 全部满足；
- 测试通过或 blocker 明确；
- `LOOP_LOG.md` 更新；
- `TASK_QUEUE.yaml` 更新；
- 如产生 insight，`wiki/` 已更新。
"""


def subagent_policy_template() -> str:
    return """# Subagent Policy

主 agent 是 controller。Subagent 只能承担局部工作，不能替代主 controller。

## Main Agent Responsibilities

- 读取 `RESEARCH_DIRECTION.md`
- 判断是否仍在 Research Corridor 内
- 读取 `CURRENT`
- 管理 Vn 状态
- 执行或委派 TASK_QUEUE active task
- 判断是否 closeout
- 决定是否生成 Vn+1 draft
- 阻止 paper claim 越权

## literature_scout

触发：version_start、baseline_lock_needed、new novelty claim appears、unexpected strong/negative result、paper_binding_related_work。
能做：搜文献，写 `literature_notes.md`，更新 `baseline_landscape.md`，标记 novelty risk。
不能做：改 PRD 主 claim，宣称 result，修改 `RESEARCH_DIRECTION.md`。

## repo_explorer

触发：需要定位代码文件；需要理解现有模块；read-only codebase mapping 超过 5 files。
能做：只读搜索代码，总结模块关系。
不能做：编辑文件。

## experiment_engineer

触发：实现 hook、harness、evaluator、artifact parser、schema。
能做：写代码，写测试，更新 run report。
不能做：写论文结论，改 Research Direction。

## debugger

触发：同一测试失败两次；gate 被可复现错误阻断。
能做：分析错误，提出最小修复，修复当前 task 范围内问题。
不能做：扩大研究范围，新开版本。

## artifact_auditor

触发：closeout 前；paper binding 前；task 声称实验完成时。
能做：检查 artifact、run record、hash、mock 泄漏。
不能做：创造 evidence。

## wiki_synthesizer

触发：每个 gate 后；closeout 前；negative result 出现时。
能做：更新 wiki，写 `next_version_seed.md`。
不能做：宣称 paper-ready。

## paper_binder

触发：`status=closed_stable` 或 `paper_binding_ready`。
能做：从稳定版本 closeout 和 artifacts 绑定 paper placeholder。
不能做：使用 exploratory result 当主结果。
"""


def literature_policy_template() -> str:
    return """# Literature Policy

## Mandatory Search Points

1. Project start：写 `RESEARCH_DIRECTION.md` 或 `V0/PRD.md` 前后，确认问题是否已被做过。
2. Version start：每个 `Vn/PRD.md` lock 前，确认本版本 RQ / baseline / method 合理。
3. Baseline lock：任何 method superiority claim 出现前，确认必须比较的强 baseline。
4. Unexpected strong/negative result：实验结果和预期冲突时，确认是否已有解释或类似现象。
5. Before paper binding：补齐 related work、novelty risk、concurrent work。

必须 web search：

- 新方向 / 新 idea
- 文献综述
- baseline lock
- novelty claim
- related work
- paper binding 前
- 用户明确问是否已有类似工作
- 用户提到不确定的新术语、论文、repo、作者、模型、方法

## No-search Situations

- 修代码 bug
- 补 artifact path
- 跑测试
- 更新 wiki
- 执行已锁定 Plan
- 小的工程重构
- 写 task queue
- 更新 next action
- 格式迁移 audit
- 纯整理当前 wiki

## Output Contract

检索输出必须写入：

- `docs/research/Vn/wiki/literature_notes.md`
- `docs/research/Vn/wiki/baseline_landscape.md`

每条记录包含：

- query
- date
- source
- relevance
- must_compare
- novelty_risk
- action_required

如果没有 web access，不要编造，写：

- `docs/research/Vn/runs/LITERATURE_REQUIRED_BLOCKER.md`
- `docs/research/explore/proposals/LITERATURE_BLOCKER.md`
"""


def git_policy_template() -> str:
    return """# Git Policy

Git 是 research-loop 的 checkpoint system，用于记录 task、gate、closeout 和 Paper Binding 对应的真实工程状态。

## AI 可以

- `git status`
- `git diff`
- `git log`
- `git add` allowed files
- `git commit` 当前 task
- `git tag` closeout / paper binding

## AI 不可以

- `git push`
- `git reset --hard`
- `git clean -fd`
- `git rebase`
- `git checkout` 覆盖用户修改
- rewrite history
- force push
- 删除 task 范围外文件

除非用户明确授权，否则所有破坏性 Git 操作都禁止。

## Task Protocol

Before work:

- Run `git status --short` if git is available.
- Record current commit hash.

After completion:

- Run tests if code changed.
- Run `git diff --stat`.
- Write diff summary to `LOOP_LOG.md`.
- Commit if task is done and commit policy allows.
- Record commit hash in `GIT_STATE.yaml` and task report.
- Do not push unless explicitly instructed.

## Closeout Protocol

Closeout requires a clean git tree or explicit dirty-tree justification. If `tag_policy.tag_on_closeout=true`, create a tag such as `research/V0/closed_success` only after closeout is complete.

## Paper Binding Protocol

Paper Binding requires a clean git tree and a stable source commit. If `tag_policy.tag_on_paper_binding=true`, create `research/paper_binding/Vn` only when `PAPER_BINDING_DECISION.md` allows binding.
"""


def epoch_prd_template(version: str, title: str, purpose: str) -> str:
    return f"""# {version} Research PRD

> 最新版本 `{version}/PRD.md` 是当前研究真源；`RESEARCH_DIRECTION.md` 是上位边界。

## 1. Version Frame

- version: {version}
- source_direction: `../RESEARCH_DIRECTION.md`
- epoch_goal: `{purpose}`

## 2. Research Spine Matrix

> 本表是 PRD 的 agent-facing 执行合同。每个 RQ 必须产生 Claim；每个 Claim 必须绑定 Experiment；每个 Experiment 必须产出 Evidence；Evidence 必须进入 Figure/Table；Figure/Table 必须支撑 Paper Section。

| RQ ID | Research Question | Claim ID | Claim | Experiment ID | Evidence Required | Figure/Table | Paper Section | Status |
|---|---|---|---|---|---|---|---|---|
| RQ1 | `【待填写】` | C1 | `【待填写】` | E1 | `【待填写】` | Fig. 1 | Sec. 3.1 | planned |

- status 枚举: `planned` / `running` / `supported` / `missing` / `blocked`
- 任何 claim 没有绑定 experiment 时，系统视为 `blocked`
- 任何 experiment 没有产出 evidence 时，系统视为 `missing`

## 3. Core Question

`【待填写：本轮核心问题是什么】`

## 4. Core Hypothesis

`【待填写：本轮核心假设是什么】`

## 5. Validation Target

`【待填写：本轮要验证什么】`

## 6. Minimal Experiment

`【待填写：本轮最小实验是什么】`

## 7. Success Conditions

- `【待填写：本轮成功条件】`

## 8. Failure Conditions

- `【待填写：本轮失败条件】`

## 9. Non-goals

- `【待填写：本轮不做什么】`

## 10. Stop / Next / Paper Binding Decision

- stop_condition: `【待填写：何时停止项目】`
- next_version_condition: `【待填写：何时创建下一版本】`
- paper_binding_condition: `【待填写：何时允许 Paper Binding】`

## 11. Carry Forward From Older Versions

- carry_forward: []
- rule: 旧版本 artifact 不能直接支持当前版本 claim，除非本节或 `SPEC.yaml` 显式登记。
"""


def epoch_spec_payload(version: str) -> dict[str, Any]:
    return {
        **template_metadata(),
        "version": version,
        "direction_ref": "../RESEARCH_DIRECTION.md",
        "prd_ref": "PRD.tex",
        "prd_summary_ref": "PRD_SUMMARY.md",
        "role": "epoch_aggregate_index",
        "rq_specs": [{"rq_id": "RQ01", "spec_ref": "rqs/RQ01/SPEC.yaml", "plan_ref": "rqs/RQ01/PLAN.md"}],
        "experiments": [],
        "datasets": [],
        "models": [],
        "baselines": [],
        "metrics": [],
        "seeds": [],
        "harnesses": [],
        "artifact_schemas": [],
        "gates": [],
        "anti_mock_policy": {
            "allow_mock_for_unit_or_smoke": True,
            "allow_mock_results_as_claim_evidence": False,
            "allow_fake_execution": False,
            "mock_allowed_only_for": ["unit_test", "smoke_test", "harness_plumbing"],
            "real_data_and_model_required_for": [
                "full_experiment",
                "full_reproduction",
                "benchmark_result",
                "baseline_comparison",
                "ablation_result",
                "paper_binding",
                "go_no_go_decision",
            ],
            "full_experiment_required_checks": sorted(FULL_EXPERIMENT_REAL_CRITERIA),
            "full_reproduction_required_checks": sorted(FULL_REPRODUCTION_REAL_CRITERIA),
        },
        "runtime_backend_truth": {
            "executor": "prompt-only",
            "notes": ["当前模板不实现真实 local-shell executor；执行报告必须由真实命令、artifact 或 prompt-only 标记支撑。"],
        },
        "runtime_contract": {
            "supported_agents": ["claude_code_ralph_loop", "codex_goal"],
            "execution_truth": [
                "Spec defines executable research tasks.",
                "Agent reports are not evidence unless backed by commands, artifacts, or explicit prompt-only status.",
                "Full experiments and full reproductions must use real datasets, real models or declared code commits, and recorded provenance.",
                "Mock, toy, synthetic, stub, cached, or proxy outputs may only support unit/smoke/plumbing checks.",
            ],
            "prompt_only_policy": {
                "allow_scaffold": True,
                "allow_fake_execution": False,
                "allow_mock_results_as_claim_evidence": False,
            },
        },
        "agent_autonomy": {
            "can_update_task_queue": True,
            "can_write_wiki": True,
            "can_close_version": True,
            "can_create_next_version_draft": True,
            "can_modify_research_direction": False,
            "can_bind_paper_results": "only_if_closed_stable",
        },
        "literature_policy": {
            "required_at": ["project_start", "version_start", "baseline_lock", "unexpected_result", "paper_binding"],
            "block_if_missing_for": ["new_method_claim", "baseline_superiority_claim", "related_work_section"],
        },
        "reproduction_contract": default_reproduction_contract(version),
        "filesystem_contract": default_filesystem_contract(version),
        "subagent_policy": {
            "allow_subagents": True,
            "allowed_subagents": [
                "literature_scout",
                "repo_explorer",
                "experiment_engineer",
                "debugger",
                "artifact_auditor",
                "wiki_synthesizer",
                "paper_binder",
            ],
            "forbidden_subagent_actions": [
                "modify_RESEARCH_DIRECTION",
                "declare_paper_admissible_claim",
                "fake_execution_result",
                "create_next_version_without_closeout",
            ],
        },
        "version_transition_policy": {
            "create_next_version_when": [
                "core_hypothesis_changed",
                "main_research_question_changed",
                "hard_gate_blocks_current_version",
                "exploration_complete_and_confirmatory_phase_needed",
                "baseline_landscape_changes_claim",
                "metric_dataset_model_invalid",
            ],
            "do_not_create_next_version_for": [
                "code_bug",
                "missing_path",
                "rerun_needed",
                "minor_spec_field_fix",
                "paper_placeholder_fix",
            ],
        },
        "engineering_gates": [
            {"id": "G_TESTS_PASS", "command": "python3 -m pytest tests -q", "required_for": "code_change"},
            {"id": "G_NO_FAKE_ARTIFACTS", "required_for": "all"},
            {"id": "G_WIKI_UPDATED", "required_for": "version_closeout"},
            {"id": "G_CLOSEOUT_COMPLETE", "required_for": "next_version_creation"},
            {"id": "G_PAPER_BINDING_ALLOWED", "required_for": "paper_binding"},
        ],
        "carry_forward": [],
    }


def epoch_spine_payload(version: str) -> dict[str, Any]:
    return {
        **template_metadata(),
        "version": version,
        "direction_ref": "../RESEARCH_DIRECTION.md",
        "source_prd_hash": None,
        "research_questions": [
            {
                "id": "RQ01",
                "text": "【待填写：当前版本的第一个可证伪研究问题】",
                "rq_dir": "rqs/RQ01",
                "spec_ref": "rqs/RQ01/SPEC.yaml",
                "plan_ref": "rqs/RQ01/PLAN.md",
            }
        ],
        "claims": [],
        "experiments": [],
        "evidence": [],
        "figures_tables": [],
        "paper_sections": [],
    }


def epoch_prd_summary_template(version: str, title: str, purpose: str) -> str:
    return f"""---
template_family: {TEMPLATE_FAMILY}
template_version: {TEMPLATE_VERSION}
version: {version}
source_prd: PRD.tex
canonical: false
---

# {version} PRD Summary — Agent Context Only

> 本文件不是研究真源，仅为 agent 快速读取 `PRD.tex` 的上下文摘要。
> 不得从本文件反向覆盖、扩写或修正 `PRD.tex`。

## Canonical Source

- canonical_prd: `PRD.tex`
- review_pdf: `PRD.pdf`
- title: `{title}`
- purpose: `{purpose}`

## RQ Index

| RQ ID | RQ Dir | Spec | Plan | Status |
|---|---|---|---|---|
| RQ01 | `rqs/RQ01` | `rqs/RQ01/SPEC.yaml` | `rqs/RQ01/PLAN.md` | planned |

## Claim Boundary

- 不得把本摘要中的占位符当作已验证 claim。
- 所有 claim 必须回到 `PRD.tex`、`RESEARCH_SPINE.yaml` 与 RQ-local `SPEC.yaml` 校验。

## Gate Summary

- G0: Source / literature / repository search lock.
- G1: Reproduction verification lock.
- G2+: RQ-local implementation、experiment、analysis 与 audit。
"""


def rq_markdown_template(version: str, rq_id: str) -> str:
    return f"""---
template_family: {TEMPLATE_FAMILY}
template_version: {TEMPLATE_VERSION}
version: {version}
rq_id: {rq_id}
---

# {rq_id} Research Question

## Statement

【待填写：用一句可证伪命题描述该 RQ】

## Parent / Lineage

- parent_version: none
- parent_rq_id: none
- relation: root

## Boundary

- allowed_claim_scope: 【待填写：该 RQ 允许支持的 claim 边界】
- forbidden_claims:
  - 【待填写：该 RQ 不允许支持的过强 claim】
"""


def rq_spec_payload(version: str, rq_id: str) -> dict[str, Any]:
    return {
        **template_metadata(),
        "version": version,
        "rq_id": rq_id,
        "source_prd": "../../PRD.tex",
        "source_prd_summary": "../../PRD_SUMMARY.md",
        "research_question": {
            "statement": "【待填写：当前 RQ 的可证伪问题陈述】",
            "motivation": "【待填写：为什么该 RQ 对当前版本必要】",
            "null_hypothesis": "【待填写：零假设】",
            "alternative_hypothesis": "【待填写：备择假设】",
            "falsification_condition": "【待填写：何种证据会反驳该 RQ】",
        },
        "claim_contract": {
            "claim_ids": [],
            "allowed_claim_scope": "【待填写：该 RQ 最多允许声称什么】",
            "forbidden_claims": ["不得声称超出 PRD.tex 与本 RQ evidence contract 的结论。"],
        },
        "reproduction_contract": {
            "required": True,
            "source_lock_ref": "reproduction/SOURCE_LOCK.yaml",
            "reproduction_spec_ref": "reproduction/REPRODUCTION_SPEC.yaml",
            "verification_ref": "reproduction/VERIFICATION.yaml",
            "immutable_base_ref": "reproduction/IMMUTABLE_BASE.yaml",
            "pass_before_innovation": True,
        },
        "experiment_contract": {
            "datasets": [],
            "models": [],
            "baselines": [],
            "metrics": [],
            "seeds": [],
            "harnesses": [],
        },
        "evidence_contract": {
            "required_artifacts": [],
            "required_commands": [],
            "artifact_hash_required": True,
            "audit_required": True,
            "paper_admissible_condition": "full run + artifact hash + audit passed + no mock evidence",
        },
        "failure_taxonomy": {
            "reproduction_failed": "复现失败；不得进入 innovation，需记录 blocker 或负结果。",
            "implementation_failed": "工程实现失败；不得解释为研究假设被证伪。",
            "hypothesis_falsified": "只有在 full harness 与 audit 后才能标记。",
            "inconclusive": "证据不足；保持 claim blocked。",
        },
    }


def rq_plan_template(version: str, rq_id: str) -> str:
    return f"""---
template_family: {TEMPLATE_FAMILY}
template_version: {TEMPLATE_VERSION}
version: {version}
rq_id: {rq_id}
source_spec: SPEC.yaml
---

# {rq_id} Evidence-Generation Plan

## Scientific Contract

- RQ: 【待填写：从 SPEC.yaml 导入】
- null_hypothesis: 【待填写】
- claim_boundary: 【待填写】
- reproduction_prerequisite: required
- falsification_condition: 【待填写】

## Evidence Gate Graph

G0 Source Lock -> G1 Reproduction Verification -> G2 Innovation Implementation -> G3 Main Experiment -> G4 Analysis and Audit -> G5 RQ Closeout

## Workflow Rules

- coding task 使用 Red -> Green -> Refactor。
- reproduction / experiment task 使用 Pre-register -> Smoke run -> Full run -> Artifact verify -> Analysis。
- 未通过 reproduction verification 前，不得执行 innovation / experiment / analysis task。
"""


def rq_tasks_payload(version: str, rq_id: str) -> dict[str, Any]:
    task_id = f"{rq_id}_T001"
    return {
        **template_metadata(),
        "version": version,
        "rq_id": rq_id,
        "source_spec": "SPEC.yaml",
        "tasks": [
            {
                "task_id": task_id,
                "phase": "reproduction",
                "status": "pending",
                "title": "Lock and verify baseline reproduction prerequisite",
                "preconditions": ["PRD.tex exists", "SPEC.yaml declares reproduction_contract.required=true"],
                "commands": [],
                "expected_artifacts": ["reproduction/VERIFICATION.yaml"],
                "pass_criteria": ["VERIFICATION.yaml status is verified or blocker is explicit"],
                "blocker_criteria": ["missing official code", "missing dataset", "metric mismatch"],
                "evidence_level_on_pass": "reproduced",
                "evidence_level_on_fail": "failed_but_informative",
                "claim_support_allowed": False,
            }
        ],
    }


def rq_reproduction_payloads(version: str, rq_id: str) -> dict[str, dict[str, Any]]:
    return {
        "SOURCE_LOCK.yaml": {
            "schema_version": SCHEMA_VERSION,
            "version": version,
            "rq_id": rq_id,
            "status": "pending",
            "sources": [],
            "notes": "Lock paper/code/dataset/metric sources before reproduction.",
        },
        "REPRODUCTION_SPEC.yaml": {
            "schema_version": SCHEMA_VERSION,
            "version": version,
            "rq_id": rq_id,
            "mode": None,
            "commands": [],
            "expected_metrics": [],
            "tolerance": None,
        },
        "VERIFICATION.yaml": {
            "schema_version": SCHEMA_VERSION,
            "version": version,
            "rq_id": rq_id,
            "status": "pending",
            "allowed_status": ["pending", "verified", "blocked", "failed"],
            "artifact_refs": [],
            "audit_status": "pending",
        },
        "IMMUTABLE_BASE.yaml": {
            "schema_version": SCHEMA_VERSION,
            "version": version,
            "rq_id": rq_id,
            "status": "pending",
            "base_refs": [],
            "read_only_after_verified": True,
        },
    }


def init_rq_scaffold(epoch_dir: Path, version: str, rq_id: str = "RQ01", force: bool = False) -> None:
    rq_dir = epoch_dir / "rqs" / rq_id
    for dirname in ["reproduction", "runs", "artifacts", "audits"]:
        (rq_dir / dirname).mkdir(parents=True, exist_ok=True)
    write_text(rq_dir / "RQ.md", markdown_template(rq_markdown_template(version, rq_id)), force)
    write_yaml(rq_dir / "SPEC.yaml", rq_spec_payload(version, rq_id), force)
    write_text(rq_dir / "PLAN.md", markdown_template(rq_plan_template(version, rq_id)), force)
    write_yaml(rq_dir / "TASKS.yaml", rq_tasks_payload(version, rq_id), force)
    for filename, payload in rq_reproduction_payloads(version, rq_id).items():
        write_yaml(rq_dir / "reproduction" / filename, payload, force)


def default_reproduction_contract(version: str) -> dict[str, Any]:
    return {
        "required": True,
        "search_required_before_reproduction": True,
        "minimum_reproduction_evidence": {
            "closest_method_baseline_required": True,
            "strongest_reported_baseline_required": True,
            "simplest_classical_or_control_baseline_required": True,
            "failures_must_be_classified": True,
            "audit_required": True,
        },
        "evidence_levels": {
            "official_full": {"can_support_claim": True},
            "official_small_scale": {"can_support_claim": "partial"},
            "faithful_reimplementation": {"can_support_claim": "partial"},
            "literature_only": {"can_support_claim": False},
        },
        "carry_forward": {
            "allowed": True,
            "requires": [
                "same_research_question",
                "same_dataset_or_justified_proxy",
                "same_metric",
                "artifact_hash_available",
                "audit_passed",
            ],
        },
    }


def default_filesystem_contract(version: str) -> dict[str, Any]:
    return {
        "state_root": f"docs/research/{version}",
        "search_metadata_root": f"docs/research/{version}/search",
        "reproduction_metadata_root": f"docs/research/{version}/reproduction",
        "rq_contract_root": f"docs/research/{version}/rqs",
        "reproduction_workspace_root": f"reproduction/{version}",
        "experiment_root": f"experiments/{version}",
        "artifact_root": f"artifacts/{version}",
        "data_manifest_root": "data/manifests",
        "allowed_large_file_policy": {
            "commit_large_artifacts": False,
            "require_hash_manifest": True,
            "require_external_path_record": True,
        },
    }


def epoch_plan_template(version: str) -> str:
    return f"""# {version} Research Plan

```yaml
version: {version}
loop_target: paper_binding
loop_mode:
  claude_code: ralph_loop
  codex: goal_driven
active_task_source: TASK_QUEUE.yaml
loop_rules:
  - "Each loop may complete at most one active task."
  - "After each loop, update LOOP_LOG.md."
  - "If blocked twice by same cause, escalate to gate_blocked."
  - "If no active task exists, generate one from PLAN.md or close version."
  - "Do not start a new version unless current version is closed."
  - "Stay inside RESEARCH_DIRECTION.md."
  - "文档撰写阶段遇到用户意图不明或要求自相矛盾时，必须停止并请求用户确认；执行阶段不得停止询问，应自主推进并仅对确实缺失的必需信息记录 blocker。"
codex_goal_rules:
  - "Codex goal must name one concrete deliverable."
  - "Codex must run tests when code changes."
  - "Codex must cite terminal/test evidence in run report."
  - "Codex should not perform broad literature search unless task phase=literature and network is available."
claude_ralph_rules:
  - "Do not expand scope mid-loop."
  - "Use subagents for large search or audit work."
  - "Write compact persistent state after each loop."
  - "Never rely on previous chat memory."
subagent_triggers:
  literature_scout:
    when:
      - "version_start"
      - "baseline_lock_needed"
      - "new novelty claim appears"
      - "paper_binding_related_work"
  repo_explorer:
    when:
      - "need to locate files/modules"
      - "read-only codebase mapping larger than 5 files"
  experiment_engineer:
    when:
      - "implementing harness, hook, evaluator, artifact parser"
  debugger:
    when:
      - "same test fails twice"
      - "gate blocked by reproducible error"
  artifact_auditor:
    when:
      - "before closeout"
      - "before paper binding"
  wiki_synthesizer:
    when:
      - "after every completed gate"
      - "before closeout"
  paper_binder:
    when:
      - "status=closed_stable"
```

## Execution Phases

Frame -> Contract -> Plan -> Execute -> Gate -> Interpret -> Wiki -> Closeout -> Next Version or Paper Binding
"""


def epoch_goal_template(version: str, title: str, purpose: str) -> str:
    return f"""---
version: {version}
language: zh-CN
style: formal_academic
evidence_rule: no_fabrication
gate_strategy: sequential_only
commit_policy: per_gate_or_blocker
---

# {version} Goal — {title}

> **本文件是版本总纲（version-level anchor），不是当前任务（task-level）文件。**
> 它定义整个 `{version}` 的总体使命、全局约束和成功标准。只有在版本核心问题或范围发生偏移时才修改。

## 工作目录
在 `{{repo_path}}` 工作。

## 全局约束
- 全程中文、正式学术风格。
- 遵守 AGENTS.md：TDD、最小实现、证据分层。
- 禁止伪造实验、stdout、artifact、hash。
- 禁止把 design intent 写成 repo-observed fact。
- 不要手改 generated artifacts。

## 版本目标（Overall Mission for {version}）
{purpose}

**核心研究问题**：【待填写：用一句可证伪命题表达。这是整个 {version} 要回答的问题，不是当前任务。】

**预期交付物**：【待填写：方法、基准、系统、理论或分析贡献】

**版本成功标准**：【待填写：什么条件下 {version} 可以 closeout】

## 总规则
- 每次只推进最早未完成 gate，不跳 gate。
- 每个 gate 流程：preflight → execution → audit → wiki/state update → commit。
- 失败要分类为 blocked / failed_execution / failed_harness / diagnostic。
- 不要直接说研究假设被证伪，除非有完整 harness 与审计。
"""


def epoch_status_payload(version: str) -> dict[str, Any]:
    return {
        **template_metadata(),
        "version": version,
        "status": "initialized",
        "allowed_status": [
            "initialized",
            "prd_locked",
            "spec_ready",
            "plan_ready",
            "running",
            "gate_blocked",
            "interpreting",
            "closed_success",
            "closed_negative",
            "closed_blocked",
            "closed_falsified",
            "closed_pivot_required",
            "closed_stable",
            "paper_binding_ready",
        ],
        "direction_ref": "../RESEARCH_DIRECTION.md",
        "current_prd": "PRD.tex",
        "current_prd_summary": "PRD_SUMMARY.md",
        "current_spine": "RESEARCH_SPINE.yaml",
        "current_spec": "SPEC.yaml",
        "current_plan": "PLAN.md",
        "current_task_queue": "TASK_QUEUE.yaml",
        "current_gate": None,
        "last_completed_task": None,
        "last_loop_report": "LOOP_LOG.md",
        "close_reason": None,
        "paper_binding": {"allowed": False, "reason": "当前版本尚未 closed_stable。"},
    }


def default_search_metadata(version: str) -> dict[str, dict[str, Any] | str]:
    return {
        "search_report.md": "",
        "web_search_log.yaml": "",
        "repo_search_log.yaml": "",
        "candidate_baselines.yaml": {
            "schema_version": 1,
            "epoch": version,
            "candidates": [],
        },
        "candidate_reproductions.yaml": {
            "schema_version": 1,
            "epoch": version,
            "candidates": [],
        },
    }


def default_reproduction_metadata(version: str) -> dict[str, dict[str, Any] | str]:
    return {
        "REPRODUCTION_INDEX.yaml": {
            "schema_version": 1,
            "epoch": version,
            "source_prd_hash": "",
            "source_spec_hash": "",
            "reproduction_policy": {
                "required_before_own_experiments": True,
                "allow_literature_only_baseline": False,
                "allow_failed_reproduction_as_evidence": True,
                "failed_reproduction_requires_audit": True,
            },
            "items": [],
        },
        "REPRODUCTION_PLAN.md": "# Reproduction Plan\n\nNo reproduction item has been locked yet.\n",
        "REPRODUCTION_DELTA.yaml": {
            "schema_version": 1,
            "epoch": version,
            "previous_epoch": None,
            "delta_check": {},
            "carry_forward_from_previous": [],
            "new_reproductions_required": [],
            "decision": {
                "reproduction_gate_required": True,
                "can_skip_full_reproduction": False,
            },
        },
    }


def default_search_reproduction_gates(version: str) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "G0_SEARCH_LOCK",
            "name": "Search and Context Lock",
            "order": 0,
            "status": "active",
            "tasks": [
                {"task_id": "T_G0_001", "status": "active"},
                {"task_id": "T_G0_002", "status": "pending"},
                {"task_id": "T_G0_003", "status": "pending"},
            ],
            "audit": {
                "required": True,
                "status": "pending",
                "modes": ["literature", "search"],
            },
        },
        {
            "gate_id": "G1_REPRODUCTION_LOCK",
            "name": "Reproduction Lock",
            "order": 1,
            "status": "pending",
            "tasks": [
                {"task_id": "T_G1_001", "status": "pending"},
                {"task_id": "T_G1_999", "status": "pending"},
            ],
            "audit": {
                "required": True,
                "status": "pending",
                "modes": ["reproduction", "artifact"],
            },
        },
    ]


def direction_bootstrap_research_binding() -> dict[str, Any]:
    return {
        "mode": "direction_bootstrap",
        "rq_id": None,
        "claim_ids": [],
        "experiment_ids": [],
        "evidence_ids": [],
        "justification": "version start search/reproduction lock before PRD-spine binding",
    }


def default_gate_aware_task_queue(version: str) -> dict[str, Any]:
    task_id = "T_G0_001"
    gates = default_search_reproduction_gates(version)
    return {
        **template_metadata(),
        "version": version,
        "queue_status": "active",
        "current_gate": "G0_SEARCH_LOCK",
        "current_task": task_id,
        "gates": gates,
        "tasks": [
            {
                "id": task_id,
                "task_id": task_id,
                "gate_id": "G0_SEARCH_LOCK",
                "phase": "search",
                "title": "Web search prior work and baselines",
                "status": "active",
                "type": "literature_search",
                "research_binding": direction_bootstrap_research_binding(),
                "agent_mode": ["main", "research-literature"],
                "search": {
                    "required": True,
                    "reason": "version start and baseline discovery",
                    "output": {
                        "search_log": "search/web_search_log.yaml",
                        "repo_search_log": "search/repo_search_log.yaml",
                        "summary": "search/search_report.md",
                    },
                },
                "allowed_files": [
                    f"docs/research/{version}/search/search_report.md",
                    f"docs/research/{version}/search/web_search_log.yaml",
                    f"docs/research/{version}/search/repo_search_log.yaml",
                    f"docs/research/{version}/search/candidate_baselines.yaml",
                    f"docs/research/{version}/search/candidate_reproductions.yaml",
                    f"docs/research/{version}/LOOP_LOG.md",
                    f"docs/research/{version}/TASK_QUEUE.yaml",
                ],
                "forbidden_files": [],
                "input_refs": ["../RESEARCH_DIRECTION.md", "PRD.tex", "PRD_SUMMARY.md", "SPEC.yaml"],
                "output_refs": [
                    "search/search_report.md",
                    "search/web_search_log.yaml",
                    "search/repo_search_log.yaml",
                    "search/candidate_baselines.yaml",
                    "search/candidate_reproductions.yaml",
                ],
                "success_criteria": [
                    "Prior work, baseline, dataset, model, and metric search has been logged.",
                    "Candidate baselines and reproductions are recorded or scarcity is justified.",
                    "Absence evidence is recorded when official code or data cannot be found.",
                ],
                "test_commands": [],
                "harness": {
                    "command": "",
                    "timeout_sec": 0,
                    "success_predicate": "search logs and report exist",
                    "artifact_paths": [
                        "search/search_report.md",
                        "search/web_search_log.yaml",
                        "search/repo_search_log.yaml",
                    ],
                },
                "evidence_required": ["web_search_log", "repo_search_log", "search_report"],
                "git": {
                    "require_clean_before_start": False,
                    "commit_after_done": True,
                    "commit_message": f"research({version}): complete search lock task",
                    "include_diff_summary": True,
                    "record_commit_hash": True,
                },
                "after_completion": {
                },
            },
            {
                "id": "T_G0_002",
                "task_id": "T_G0_002",
                "gate_id": "G0_SEARCH_LOCK",
                "phase": "search",
                "title": "Repository search for existing code/data/configs",
                "status": "pending",
                "type": "repo_search",
                "research_binding": direction_bootstrap_research_binding(),
                "search": {"required": True, "reason": "local repository evidence discovery"},
                "allowed_files": [
                    f"docs/research/{version}/search/repo_search_log.yaml",
                    f"docs/research/{version}/LOOP_LOG.md",
                    f"docs/research/{version}/TASK_QUEUE.yaml",
                ],
                "forbidden_files": [],
                "input_refs": ["../../"],
                "output_refs": ["search/repo_search_log.yaml"],
                "success_criteria": ["Repository search commands and findings are logged."],
                "test_commands": [],
                "harness": {
                    "command": "",
                    "timeout_sec": 0,
                    "success_predicate": "repo_search_log exists",
                    "artifact_paths": ["search/repo_search_log.yaml"],
                },
                "evidence_required": ["repo_search_log"],
            },
            {
                "id": "T_G0_003",
                "task_id": "T_G0_003",
                "gate_id": "G0_SEARCH_LOCK",
                "phase": "reproduction_planning",
                "title": "Lock candidate reproduction set",
                "status": "pending",
                "type": "reproduction_planning",
                "research_binding": direction_bootstrap_research_binding(),
                "search": {"required": False},
                "allowed_files": [
                    f"docs/research/{version}/reproduction/REPRODUCTION_INDEX.yaml",
                    f"docs/research/{version}/reproduction/REPRODUCTION_PLAN.md",
                    f"docs/research/{version}/LOOP_LOG.md",
                    f"docs/research/{version}/TASK_QUEUE.yaml",
                ],
                "forbidden_files": [],
                "input_refs": ["search/candidate_reproductions.yaml", "search/candidate_baselines.yaml"],
                "output_refs": ["reproduction/REPRODUCTION_INDEX.yaml", "reproduction/REPRODUCTION_PLAN.md"],
                "success_criteria": ["Candidate reproduction set is locked or blocker is recorded."],
                "test_commands": [],
                "harness": {
                    "command": "",
                    "timeout_sec": 0,
                    "success_predicate": "REPRODUCTION_INDEX.yaml exists",
                    "artifact_paths": ["reproduction/REPRODUCTION_INDEX.yaml"],
                },
                "evidence_required": ["reproduction_index"],
            },
            {
                "id": "T_G1_001",
                "task_id": "T_G1_001",
                "gate_id": "G1_REPRODUCTION_LOCK",
                "phase": "reproduction",
                "title": "Classify and plan selected reproductions",
                "status": "pending",
                "type": "reproduction_planning",
                "research_binding": direction_bootstrap_research_binding(),
                "search": {"required": True, "reason": "reproduction task"},
                "allowed_files": [
                    f"docs/research/{version}/reproduction/REPRODUCTION_INDEX.yaml",
                    f"docs/research/{version}/reproduction/REPRODUCTION_PLAN.md",
                    f"docs/research/{version}/search/web_search_log.yaml",
                    f"docs/research/{version}/search/repo_search_log.yaml",
                    f"docs/research/{version}/LOOP_LOG.md",
                    f"docs/research/{version}/TASK_QUEUE.yaml",
                ],
                "forbidden_files": [],
                "input_refs": ["reproduction/REPRODUCTION_INDEX.yaml"],
                "output_refs": ["reproduction/REPRODUCTION_INDEX.yaml", "reproduction/REPRODUCTION_PLAN.md"],
                "success_criteria": ["Reproduction items are classified with status and evidence level."],
                "test_commands": [],
                "harness": {
                    "command": "",
                    "timeout_sec": 0,
                    "success_predicate": "all reproduction items classified or blocker recorded",
                    "artifact_paths": ["reproduction/REPRODUCTION_INDEX.yaml"],
                },
                "evidence_required": ["reproduction_index", "search_log"],
            },
            {
                "id": "T_G1_999",
                "task_id": "T_G1_999",
                "gate_id": "G1_REPRODUCTION_LOCK",
                "phase": "audit",
                "title": "Audit reproduction evidence",
                "status": "pending",
                "type": "reproduction_audit",
                "research_binding": direction_bootstrap_research_binding(),
                "search": {"required": False},
                "allowed_files": [
                    f"docs/research/{version}/audits/**",
                    f"docs/research/{version}/AUDIT_QUEUE.yaml",
                    f"docs/research/{version}/LOOP_LOG.md",
                    f"docs/research/{version}/TASK_QUEUE.yaml",
                ],
                "forbidden_files": [],
                "input_refs": ["reproduction/REPRODUCTION_INDEX.yaml", "PAPER_CLAIM_LEDGER.yaml"],
                "output_refs": ["AUDIT_QUEUE.yaml", "audits/"],
                "success_criteria": ["Reproduction evidence is audited before method experiments."],
                "test_commands": [],
                "harness": {
                    "command": "",
                    "timeout_sec": 0,
                    "success_predicate": "reproduction audit pass, repair, or human review decision recorded",
                    "artifact_paths": ["AUDIT_QUEUE.yaml"],
                },
                "evidence_required": ["audit_report"],
            },
        ],
    }


def epoch_task_queue_payload(version: str) -> dict[str, Any]:
    return default_gate_aware_task_queue(version)


def default_audit_queue(version: str) -> dict[str, Any]:
    return {"schema_version": 1, "epoch": version, "audits": []}


def default_insight_index(version: str) -> dict[str, Any]:
    return {"schema_version": 1, "epoch": version, "insights": []}


def default_human_review_requests(version: str) -> dict[str, Any]:
    return {"schema_version": 1, "epoch": version, "requests": []}


def default_paper_claim_ledger(version: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "epoch": version,
        "claims": [],
        "_comment": "This is the Paper Binding gate, not the planning spine. Only claims with status=allowed and compatible reproduction evidence may enter the paper. RQ→Claim→Experiment chains belong in RESEARCH_SPINE.yaml.",
    }


def active_task_from_gate_queue(queue: dict[str, Any]) -> dict[str, Any] | None:
    current_task = str(queue.get("current_task") or "")
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    if current_task:
        for task in tasks:
            if str(task.get("task_id") or task.get("id") or "") == current_task and str(task.get("status")) == "active":
                return task
    active = [task for task in tasks if str(task.get("status")) == "active"]
    return active[0] if len(active) == 1 else None


def validate_gate_queue_shape(queue: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in ["current_gate", "current_task", "gates", "tasks"]:
        if field not in queue:
            issues.append(f"TASK_QUEUE.yaml missing required field: {field}")
    gates = [gate for gate in as_list(queue.get("gates")) if isinstance(gate, dict)]
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    for gate in gates:
        status = str(gate.get("status") or "")
        if status not in GATE_STATUSES:
            issues.append(f"invalid gate status: {status}")
    for task in tasks:
        status = str(task.get("status") or "")
        if status not in TASK_STATUSES:
            issues.append(f"invalid task status: {status}")
    current_gate = queue.get("current_gate")
    if current_gate and not any(str(gate.get("gate_id") or "") == str(current_gate) for gate in gates):
        issues.append(f"current_gate {current_gate} does not exist in gates")
    current_task = queue.get("current_task")
    if current_task and not any(str(task.get("task_id") or task.get("id") or "") == str(current_task) for task in tasks):
        issues.append(f"current_task {current_task} does not exist in tasks")
    return issues


RESEARCH_BINDING_MODES = {"direction_bootstrap", "spine_bound", "maintenance", "paper_binding"}
DIRECTION_BOOTSTRAP_GATE_IDS = {"G0_SEARCH_LOCK", "G1_REPRODUCTION_LOCK"}
DIRECTION_BOOTSTRAP_PHASES = {"search", "reproduction_planning", "reproduction", "audit"}
MAINTENANCE_PHASES = {"maintenance", "format", "path_repair", "test_repair", "test", "repair", "artifact_repair"}
PAPER_BINDING_PHASES = {"paper_binding", "paper", "binding"}
EVIDENCE_BOUND_TASK_TYPES = {
    "experiment",
    "experiment_execution",
    "analysis",
    "result_analysis",
    "result_binding",
    "evaluation",
}


def _binding_list(binding: dict[str, Any], key: str) -> list[str]:
    return [str(item) for item in as_list(binding.get(key)) if str(item)]


def _spine_claims_by_id(spine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(claim.get("id")): claim
        for claim in as_list(spine.get("claims"))
        if isinstance(claim, dict) and claim.get("id")
    }


def _spine_experiments_by_id(spine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(exp.get("id")): exp
        for exp in as_list(spine.get("experiments"))
        if isinstance(exp, dict) and exp.get("id")
    }


def _spine_evidence_by_id(spine: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(evidence.get("id")): evidence
        for evidence in as_list(spine.get("evidence"))
        if isinstance(evidence, dict) and evidence.get("id")
    }


def validate_task_research_binding(epoch_dir: Path, queue: dict[str, Any], spine: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    rqs = {str(rq.get("id")) for rq in as_list(spine.get("research_questions")) if isinstance(rq, dict) and rq.get("id")}
    claims = _spine_claims_by_id(spine)
    experiments = _spine_experiments_by_id(spine)
    evidence_items = _spine_evidence_by_id(spine)

    for task in tasks:
        task_id = _task_identifier(task) or "<missing>"
        binding = task.get("research_binding")
        if not isinstance(binding, dict):
            issues.append(f"task {task_id} missing research_binding")
            continue

        mode = str(binding.get("mode") or "")
        if mode not in RESEARCH_BINDING_MODES:
            issues.append(f"task {task_id} has invalid research_binding mode: {mode}")
            continue

        justification = str(binding.get("justification") or "").strip()
        if not justification or "【待填写" in justification:
            issues.append(f"task {task_id} research_binding missing concrete justification")

        gate_id = str(task.get("gate_id") or "")
        phase = str(task.get("phase") or "")
        if mode == "direction_bootstrap":
            if gate_id not in DIRECTION_BOOTSTRAP_GATE_IDS:
                issues.append(f"task {task_id} direction_bootstrap is only allowed in G0/G1 gates: {gate_id}")
            if phase not in DIRECTION_BOOTSTRAP_PHASES:
                issues.append(f"task {task_id} direction_bootstrap is not allowed in phase: {phase}")
            continue

        if mode == "maintenance":
            if phase not in MAINTENANCE_PHASES:
                issues.append(f"task {task_id} maintenance binding is not allowed in phase: {phase}")
            if "claim" not in justification.lower() and "主张" not in justification:
                issues.append(f"task {task_id} maintenance binding must justify why it produces no research claim")
            continue

        if mode == "paper_binding":
            if phase not in PAPER_BINDING_PHASES:
                issues.append(f"task {task_id} paper_binding mode is not allowed in phase: {phase}")
            if not (epoch_dir / "PAPER_CLAIM_LEDGER.yaml").exists():
                issues.append(f"task {task_id} paper_binding requires PAPER_CLAIM_LEDGER.yaml")
            if not (epoch_dir / "PAPER_BINDING_DECISION.md").exists():
                issues.append(f"task {task_id} paper_binding requires PAPER_BINDING_DECISION.md")
            continue

        rq_id = str(binding.get("rq_id") or "")
        if not rq_id:
            issues.append(f"task {task_id} spine_bound research_binding missing rq_id")
        elif rq_id not in rqs:
            issues.append(f"task {task_id} research_binding references unknown rq_id: {rq_id}")

        claim_ids = _binding_list(binding, "claim_ids")
        if not claim_ids:
            issues.append(f"task {task_id} spine_bound research_binding missing claim_ids")
        for claim_id in claim_ids:
            claim = claims.get(claim_id)
            if claim is None:
                issues.append(f"task {task_id} research_binding references unknown claim_id: {claim_id}")
                continue
            claim_rq_id = str(claim.get("rq_id") or "")
            if rq_id and claim_rq_id != rq_id:
                issues.append(f"task {task_id} claim {claim_id} belongs to rq_id {claim_rq_id}, not {rq_id}")

        experiment_ids = _binding_list(binding, "experiment_ids")
        if not experiment_ids:
            issues.append(f"task {task_id} spine_bound research_binding missing experiment_ids")
        bound_claims_from_experiments: set[str] = set()
        for experiment_id in experiment_ids:
            experiment = experiments.get(experiment_id)
            if experiment is None:
                issues.append(f"task {task_id} research_binding references unknown experiment_id: {experiment_id}")
                continue
            bound_claims_from_experiments.update(str(cid) for cid in as_list(experiment.get("claim_ids")) if str(cid))
        if experiment_ids and claim_ids and not set(claim_ids).issubset(bound_claims_from_experiments):
            missing = ", ".join(sorted(set(claim_ids) - bound_claims_from_experiments))
            issues.append(f"task {task_id} experiment_ids do not cover claim_ids: {missing}")

        evidence_ids = _binding_list(binding, "evidence_ids")
        if not evidence_ids:
            issues.append(f"task {task_id} spine_bound research_binding missing evidence_ids")
        for evidence_id in evidence_ids:
            evidence = evidence_items.get(evidence_id)
            if evidence is None:
                issues.append(f"task {task_id} research_binding references unknown evidence_id: {evidence_id}")
                continue
            evidence_experiment_id = str(evidence.get("experiment_id") or "")
            if experiment_ids and evidence_experiment_id not in experiment_ids:
                issues.append(f"task {task_id} evidence {evidence_id} belongs to experiment_id {evidence_experiment_id}, not bound experiment_ids")
    return issues


def validate_active_task_research_binding(active_task: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    task_id = _task_identifier(active_task) or "<missing>"
    binding = active_task.get("research_binding")
    if not isinstance(binding, dict):
        return [f"active task {task_id} missing research_binding"]

    mode = str(binding.get("mode") or "")
    if mode not in {"direction_bootstrap", "maintenance", "paper_binding", "spine_bound"}:
        issues.append(f"active task {task_id} has invalid research_binding mode: {mode}")
        return issues

    task_kind = str(active_task.get("type") or "")
    phase = str(active_task.get("phase") or "")
    if task_kind in EVIDENCE_BOUND_TASK_TYPES or phase in EVIDENCE_BOUND_TASK_TYPES:
        if not _binding_list(binding, "experiment_ids"):
            issues.append(f"active experiment task {task_id} must bind experiment_ids")
        if not _binding_list(binding, "evidence_ids"):
            issues.append(f"active experiment task {task_id} must bind evidence_ids")
    return issues


def _fmt_list(items: list[str] | None, indent: str = "- ") -> str:
    if not items:
        return "（无）"
    return "\n".join(f"{indent}{item}" for item in items)


def _fmt_git_protocol(task: dict[str, Any]) -> str:
    git = task.get("git", {}) if isinstance(task.get("git"), dict) else {}
    require_clean = git.get("require_clean_before_start", False)
    commit_after = git.get("commit_after_done", True)
    commit_msg = git.get("commit_message", f"research: complete {task.get('id', 'TASK')}")
    record_hash = git.get("record_commit_hash", True)
    return f"""Before work:
- Run `git status --short` if git is available.
- Record current commit hash.
- Working tree must be clean: {'YES' if require_clean else 'no'}

After completion:
- Run tests if code changed.
- Run `git diff --stat`.
- Write diff summary to `LOOP_LOG.md`.
- Commit after done: {'YES' if commit_after else 'no'}
- Commit message: `{commit_msg}`
- Record commit hash in GIT_STATE.yaml: {'YES' if record_hash else 'no'}
- Do not push unless explicitly instructed."""


def _task_identifier(task: dict[str, Any]) -> str:
    return str(task.get("task_id") or task.get("id") or "")


def task_search_required(task: dict[str, Any]) -> bool:
    search = task.get("search")
    if isinstance(search, dict):
        return search.get("required") is True
    return task.get("search_required") is True


def required_search_outputs(task: dict[str, Any]) -> list[str]:
    search = task.get("search") if isinstance(task.get("search"), dict) else {}
    output = search.get("output") if isinstance(search.get("output"), dict) else {}
    paths = [
        str(output.get("search_log") or "search/web_search_log.yaml"),
        str(output.get("repo_search_log") or "search/repo_search_log.yaml"),
        str(output.get("summary") or "search/search_report.md"),
    ]
    return [path for path in dict.fromkeys(paths) if path]


def missing_search_outputs(epoch_dir: Path, task: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not task_search_required(task):
        return missing
    for relative in required_search_outputs(task):
        path = epoch_dir / relative
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        substantive = "\n".join(line for line in text.splitlines() if line.strip() and line.strip() != "---" and not line.startswith("template_") and not line.startswith("schema_version:") and not line.startswith("generated_by:"))
        if not path.exists() or not substantive.strip():
            missing.append(relative)
    return missing


def _resolve_gate_for_task(epoch_dir: Path, task: dict[str, Any]) -> str:
    gate_id = str(task.get("gate_id") or "")
    if gate_id:
        return gate_id
    spec = load_yaml(epoch_dir / "SPEC.yaml")
    gates = as_list(spec.get("gates"))
    task_id = _task_identifier(task)
    for gate in gates:
        if not isinstance(gate, dict):
            continue
        gate_tasks = as_list(gate.get("tasks"))
        if task_id in [str(t) for t in gate_tasks]:
            return str(gate.get("gate_id") or gate.get("id") or "")
        for gt in gate_tasks:
            if isinstance(gt, dict) and str(gt.get("task_id") or "") == task_id:
                return str(gate.get("gate_id") or gate.get("id") or "")
    return "ungated"


def _resolve_harness_for_task(epoch_dir: Path, task: dict[str, Any]) -> str:
    harness_ref = str(task.get("harness") or "")
    if harness_ref:
        return harness_ref
    spec = load_yaml(epoch_dir / "SPEC.yaml")
    task_id = _task_identifier(task)
    for key in ("harnesses", "experiment_harnesses", "reproduction_harnesses"):
        for h in as_list(spec.get(key)):
            if not isinstance(h, dict):
                continue
            h_tasks = as_list(h.get("tasks"))
            if task_id in [str(t) for t in h_tasks]:
                h_path = str(h.get("path") or h.get("harness_path") or "")
                h_cmd = str(h.get("command") or h.get("run") or "")
                if h_path and h_cmd:
                    return f"路径: {h_path}\n- 调用方式: {h_cmd}"
                if h_path:
                    return f"路径: {h_path}"
                if h_cmd:
                    return f"调用方式: {h_cmd}"
                return str(h.get("id") or h.get("harness_id") or "unnamed")
    return "N/A"




def epoch_loop_log_template(version: str) -> str:
    return f"""# {version} Loop Log

## Entry Template

- task_id: `TASK_001`
- status: `【待填写：done / blocked / skipped】`
- command_or_action: `【待填写：执行过的命令或 prompt-only action】`
- evidence: `【待填写：terminal output 路径、artifact 路径或 blocker】`
- next_action: `【待填写：下一个原子动作】`
"""


def epoch_closeout_template(version: str) -> str:
    return f"""# {version} Closeout

## 1. Version Status

- version: {version}
- final_status: `【待填写：closed_success / closed_negative / closed_blocked / closed_falsified / closed_pivot_required / closed_stable】`
- close_reason: `【待填写：关闭原因】`
- closed_at: `【待填写：YYYY-MM-DD】`

## 2. Original Hypothesis

本版本原本相信什么？

`【待填写：原始假设】`

## 3. What Was Executed

- actually_executed: `【待填写：真实执行的 plan / task / run / artifact】`
- prompt_only_scaffold: `【待填写：只完成提示或 scaffold 的部分】`
- blocked: `【待填写：被阻断的部分】`
- not_started: `【待填写：未开始的部分】`

## 4. What Failed or Blocked

- blocker_id: `【待填写：blocker ID】`
- category: `【待填写：execution_failure / environment_failure / spec_gap / prd_gap / data_unavailable / compute_unavailable / metric_mismatch / research_falsification / insight_trigger】`
- detail: `【待填写：具体 blocker】`

## 5. What We Learned

- fact: `【待填写：事实】`
- artifact: `【待填写：artifact 路径】`
- interpretation: `【待填写：解释】`
- speculation: `【待填写：推测】`

## 6. Positive Signals

- `【待填写：值得保留的现象；如无，写明确无】`

## 7. Negative Results

- `【待填写：被削弱或反驳的假设；如无，写明确无】`

## 8. Carry Forward

- artifact: []
- baseline: []
- code_module: []
- insight: []
- open_question: []
- dataset: []
- metric: []
- harness: []

## 9. Drop

- hypothesis: []
- claim: []
- baseline: []
- experiment_path: []
- method_variant: []
- metric: []

## 10. Next Version Decision

- create_next_version: false
- next_version_type: `【待填写：exploration / intervention / training / confirmatory / reproduction / paper_binding / stop】`
- next_core_question: `【待填写：下一版核心问题；如不创建，写 none】`
- next_minimal_experiments: `【待填写：下一版最小实验；如不创建，写 none】`
- next_stop_conditions: `【待填写：下一版停止条件；如不创建，写 none】`
- must_stay_inside_research_corridor: true

## 11. Paper Binding Decision

- paper_binding_ready: false
- reason: `【待填写：为何可以或不可以绑定论文】`
- allowed_claims: []
- blocked_claims: []

## 12. Git Closeout

- base_commit: `【待填写：epoch 起点 commit】`
- closeout_commit: `【待填写：closeout commit】`
- task_commits:
  - TASK_001: `【待填写：commit hash 或 blocker】`
- final_diff_summary: `【待填写：git diff --stat 摘要】`
- closeout_tag: `【待填写：research/V0/closed_status 或 none】`
- dirty_tree: `【待填写：false 或 dirty-tree justification】`
"""


def paper_binding_decision_template(version: str) -> str:
    return f"""# Paper Binding Decision

## Status

- paper_binding_ready: false
- source_version: {version}
- decision_reason: `当前版本尚未 closed_stable。`

## Allowed Claims

- `【待填写：允许写入论文结果的 claim；未 ready 时写 none】`

## Blocked Claims

- claim: `【待填写：不能写入论文结果的 claim】`
- blocker: `【待填写：证据、baseline、metric、seed、artifact 或 audit blocker】`

## Evidence Requirements

每个 allowed claim 必须绑定：

- experiment_id
- run_id
- artifact_path
- metric
- baseline
- seed_protocol
- audit_status
- real_data_check
- real_model_check
- non_smoke_full_run

## Git Binding

- source_version: {version}
- source_commit: `【待填写：支撑 Paper Binding 的 source commit】`
- paper_binding_commit: `【待填写：Paper Binding commit】`
- paper_binding_tag: `【待填写：research/paper_binding/{version} 或 none】`
- dirty_tree_allowed: false

## Forbidden

- 不使用 exploratory-only insight 作为 main result。
- 不使用 prompt-only scaffold 作为 result。
- 不从 paper 反推实验。
- 不填入 plausible but unverified numbers。
"""


def wiki_templates(version: str) -> dict[str, str]:
    return {
        "epoch_summary.md": f"""# {version} Epoch Summary

## Original Belief

`【待填写：这一版原本相信什么】`

## What Was Done

`【待填写：实际做了什么】`

## Observations

`【待填写：观察到什么】`

## Supported Hypotheses

- `【待填写：被支持的假设；如无，写明确无】`

## Weakened Hypotheses

- `【待填写：被削弱的假设；如无，写明确无】`

## Failed or Blocked Paths

- `【待填写：跑不通的路径；如无，写明确无】`
""",
        "evidence_map.md": f"""# {version} Evidence Map

## Claim Evidence Entries

- hypothesis_or_claim: `【待填写：hypothesis / claim ID】`
  - supported_by: []
  - challenged_by: []
  - falsified_by: []
  - unresolved: `【待填写：未解决问题】`
  - evidence_level: exploratory

允许值：exploratory | diagnostic | confirmatory | reproduced | paper_admissible
""",
        "positive_signals.md": f"""# {version} Positive Signals

- signal_id: `【待填写：signal ID；如无，写 NONE】`
  source_task: `【待填写】`
  source_run: `【待填写】`
  source_artifact: `【待填写】`
  evidence_level: exploratory
  why_it_matters: `【待填写】`
  next_validation: `【待填写】`
""",
        "negative_results.md": f"""# {version} Negative Results

- result_id: `【待填写：negative result ID；如无，写 NONE】`
  category: unresolved
  source_task: `【待填写】`
  source_run: `【待填写】`
  interpretation: `【待填写】`

允许分类：execution_bug | spec_gap | metric_problem | data_problem | research_falsification | limitation | unresolved
""",
        "failed_paths.md": f"""# {version} Failed Paths

- failed_path: `【待填写：失败路径；如无，写 NONE】`
  why_failed: `【待填写】`
  cost: `【待填写】`
  future_avoidance_rule: `【待填写】`
""",
        "baseline_landscape.md": f"""# {version} Baseline Landscape

- must_compare: []
- strong_baseline: []
- weak_baseline: []
- unfair_baseline: []
- appendix_only: []
- novelty_risk: `【待填写：novelty risk 或 literature blocker】`
""",
        "literature_notes.md": f"""# {version} Literature Notes

## Search Records

- query: `【待填写：检索 query；如无网络，写 literature blocker】`
  date: `【待填写：YYYY-MM-DD】`
  source: `【待填写：source URL / citation / blocker】`
  relevance: `【待填写】`
  must_compare: false
  novelty_risk: `【待填写】`
  action_required: `【待填写】`

如果没有网络，不要编造，写入 `{version}/runs/LITERATURE_REQUIRED_BLOCKER.md`。
""",
        "open_questions.md": f"""# {version} Open Questions

- question_id: `【待填写：Q1】`
  question: `【待填写：下一轮还没解决的问题】`
  why_open: `【待填写】`
  needed_evidence: `【待填写】`
""",
        "next_version_seed.md": f"""# {version} Next Version Seed

- should_create_next_version: false
- why: `【待填写：为什么创建或不创建下一版】`
- keep: []
- drop: []
- new_core_question: `【待填写：新核心问题；如无，写 none】`
- minimal_next_experiments: `【待填写：最小下一版实验；如无，写 none】`
- next_stop_conditions: `【待填写：下一版停止条件；如无，写 none】`
- out_of_scope_risk: `【待填写：是否有越过 Research Corridor 的风险】`
- required_human_review: true
""",
    }


def git_state_payload(version: str) -> dict[str, Any]:
    return {
        **template_metadata(),
        "version": version,
        "git_enabled": True,
        "epoch_branch": f"research/{version}",
        "base_commit": None,
        "current_commit": None,
        "last_task_commit": None,
        "last_gate_commit": None,
        "closeout_commit": None,
        "paper_binding_commit": None,
        "commit_policy": {
            "commit_after_task_done": True,
            "commit_after_gate_passed": True,
            "commit_after_closeout": True,
            "commit_after_paper_binding": True,
            "allow_commit_on_blocker": True,
            "allow_push": False,
        },
        "tag_policy": {
            "tag_on_closeout": True,
            "tag_on_paper_binding": True,
            "closeout_tag_format": f"research/{version}/closed_{{status}}",
            "paper_tag_format": f"research/paper_binding/{version}",
        },
        "dirty_tree_policy": {
            "before_next_action": "warn",
            "before_closeout": "block",
            "before_paper_binding": "block",
        },
    }


def git_log_template(version: str) -> str:
    return f"""# {version} Git Log

## Entry Template

- task_id: `TASK_001`
- branch: `【待填写：git branch】`
- pre_commit: `【待填写：执行前 commit】`
- post_commit: `【待填写：执行后 commit】`
- diff_stat: `【待填写：git diff --stat 摘要】`
- commit_created: `【待填写：true / false】`
- commit_hash: `【待填写：commit hash 或 none】`
- dirty_tree_after_task: `【待填写：true / false】`
"""


def task_run_report_template(version: str, task_id: str = "TASK_001") -> str:
    return f"""# {task_id} Run Report

## Task

- version: {version}
- task_id: {task_id}
- status: `【待填写：done / blocked / failed / skipped】`

## Git State

- branch: `【待填写】`
- pre_commit: `【待填写】`
- post_commit: `【待填写】`
- commit_created: `【待填写：true / false】`
- commit_hash: `【待填写】`
- dirty_tree_after_task: `【待填写：true / false】`

## Files Changed

`【待填写：粘贴 git diff --stat 摘要】`

## Commands Run

`【待填写：真实命令和结果；没有运行则说明原因】`

## Evidence

- tests: `【待填写】`
- artifacts: `【待填写】`
- blockers: `【待填写】`

## Interpretation

这一步完成了什么？它是否产生 insight？是否需要更新 wiki？

## Next Action

`【待填写：下一步建议】`
"""


def task_run_report_payload(version: str, task_id: str = "TASK_001") -> dict[str, Any]:
    """Generate the machine-readable YAML run report for a completed task execution."""
    return {
        **template_metadata(),
        "report_version": 1,
        "task": {
            "version": version,
            "task_id": task_id,
            "status": "pending",
            "gate_id": None,
        },
        "git": {
            "branch": None,
            "pre_commit": None,
            "post_commit": None,
            "commit_created": False,
            "commit_hash": None,
            "dirty_tree_after_task": False,
        },
        "execution": {
            "commands_run": [],
            "stdout_path": None,
            "stderr_path": None,
            "exit_code": None,
            "files_changed": [],
        },
        "evidence": {
            "tests": {"passed": False, "output_path": None},
            "artifacts": [],
            "blockers": [],
        },
        "gate_outcome": {
            "gate_passed": False,
            "gate_blocked": False,
            "blocker_reason": None,
        },
        "next_action": {
            "recommendation": None,
            "wiki_update_needed": False,
            "insight_generated": False,
        },
    }


def write_task_run_report(epoch_dir: Path, version: str, task_id: str, report: dict[str, Any] | None = None) -> tuple[Path, Path]:
    """Write both the YAML (machine-readable) and MD (human-readable) task run report.

    If report is None, writes a fresh template. Otherwise writes the completed report.
    Returns (yaml_path, md_path).
    """
    runs_dir = epoch_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = runs_dir / f"{task_id}_report.yaml"
    md_path = runs_dir / f"{task_id}_report.md"
    if report is None:
        report = task_run_report_payload(version, task_id)
    write_yaml(yaml_path, report, force=True)
    md_content = f"""# {task_id} Run Report

## Task

- version: {version}
- task_id: {task_id}
- status: {report.get('task', {}).get('status', 'pending')}
- gate_id: {report.get('task', {}).get('gate_id', 'N/A')}

## Git State

- branch: `{report.get('git', {}).get('branch', 'N/A')}`
- pre_commit: `{report.get('git', {}).get('pre_commit', 'N/A')}`
- post_commit: `{report.get('git', {}).get('post_commit', 'N/A')}`
- commit_created: {report.get('git', {}).get('commit_created', False)}
- commit_hash: `{report.get('git', {}).get('commit_hash', 'N/A')}`
- dirty_tree_after_task: {report.get('git', {}).get('dirty_tree_after_task', False)}

## Commands Run

{chr(10).join('- ' + c for c in report.get('execution', {}).get('commands_run', [])) or '（无）'}

## Evidence

- tests_passed: {report.get('evidence', {}).get('tests', {}).get('passed', False)}
- artifacts: {report.get('evidence', {}).get('artifacts', [])}
- blockers: {report.get('evidence', {}).get('blockers', [])}

## Gate Outcome

- gate_passed: {report.get('gate_outcome', {}).get('gate_passed', False)}
- gate_blocked: {report.get('gate_outcome', {}).get('gate_blocked', False)}
- blocker_reason: {report.get('gate_outcome', {}).get('blocker_reason', 'N/A')}

## Next Action

- recommendation: {report.get('next_action', {}).get('recommendation', 'N/A')}
- wiki_update_needed: {report.get('next_action', {}).get('wiki_update_needed', False)}
- insight_generated: {report.get('next_action', {}).get('insight_generated', False)}
"""
    write_text(md_path, md_content, force=True)
    return yaml_path, md_path


def read_task_run_report(epoch_dir: Path, task_id: str) -> dict[str, Any]:
    """Read the machine-readable YAML run report for a task."""
    yaml_path = epoch_dir / "runs" / f"{task_id}_report.yaml"
    if not yaml_path.exists():
        return {}
    return load_yaml(yaml_path)


def explore_session_template(version: str = "V0") -> str:
    return f"""---
id: EXP_0001
type: explore_session
version: {version}
mode: baseline
created_at: {today_string()}
web_search_used: false
status: saved
template_family: {TEMPLATE_FAMILY}
template_version: {TEMPLATE_VERSION}
schema_version: {SCHEMA_VERSION}
generated_by: research-init
---

# EXP_0001

## User Question

`【待填写：用户问了什么】`

## Current Context

`【待填写：当前版本、当前 PRD、当前 open questions】`

## Research Direction Boundary

`【待填写：本次探索必须停留在哪些 Research Corridor 内】`

## Discussion Summary

`【待填写：简要总结讨论，不写隐藏推理链】`

## Web / Literature Findings

- query: `【待填写：检索 query；如未使用 web search 写 none】`
- source: `【待填写：source 或 LITERATURE_BLOCKER】`
- relevance: `【待填写】`
- claim_supported: `【待填写】`
- uncertainty: `【待填写】`

如果无 web access，写 `LITERATURE_BLOCKER`，不要编造。

## Implications for Current Version

- no_change
- update_wiki
- add_task_candidate
- closeout_consideration
- next_version_seed_candidate
- out_of_scope_escalation

## Proposed Actions

只提出建议，不执行。

## Save Targets

- `Vn/wiki/literature_notes.md`
- `Vn/wiki/baseline_landscape.md`
- `Vn/wiki/open_questions.md`
- `Vn/wiki/next_version_seed.md`
"""


def explore_synthesis_template() -> str:
    return """# Explore Synthesis

## Scope

`【待填写：汇总哪些 EXP session】`

## Stable Takeaways

- `【待填写：可沉淀到 wiki 的稳定认识；如无，写明确无】`

## Proposed Updates

- `【待填写：建议更新的 wiki / task / next_version_seed；只建议，不执行】`
"""


def explore_proposal_template(title: str) -> str:
    return f"""# {title}

## Proposal Status

- status: draft
- human_review_required: true

## Rationale

`【待填写：建议原因】`

## Proposed Change

`【待填写：建议内容；不得直接当作已执行修改】`

## Evidence / Sources

- `【待填写：EXP session、文献、run、artifact 或 blocker】`

## Boundary

Explore 只能建议，不能直接修改 PRD、RESEARCH_DIRECTION、Spec、Plan、Paper Binding。
"""


def claude_root_template() -> str:
    return """# CLAUDE.md

## 核心指令

你是本项目的自动科研执行器。用户只负责与你讨论研究方向并做关键决策，所有文档和实验由你自动完成。

整个流程分为三个阶段：**初始化 → PRD 生成 → 自动执行**。

---

### 阶段 0：初始化（若 workspace 不存在）

若 `docs/research/` 不存在，运行：

```bash
python3 ~/.claude/skills/research-init/scripts/init_research.py \
  --repo . --title "与用户讨论后确定的项目标题" \
  --purpose "与用户讨论后确定的研究目标"
```

初始化完成后跳转到阶段 1。

---

### 阶段 1：PRD 讨论与生成


**你需要做**：

1. 读取 `docs/research/{CURRENT}/PRD.md` 模板（16 章结构）。
2. 逐章与用户讨论：
   - 第 2 章背景教程、第 3 章相关工作地图：你需要搜索文献帮用户理清 landscape
   - 第 4 章基准与复现计划：你需要帮用户选 concrete baseline、dataset、metric
   - 第 6 章研究问题与假设：帮用户把模糊 idea 变成可证伪的 RQ
   - 第 10 章实验设计：帮用户设计 experiment matrix
   - **第 11.2 章 Gate 调度表（最关键）**：帮用户把研究拆成有序 Gate，每个 Gate 定义 task 清单和可验证的 pass_condition
   - 第 12 章 Harness：帮用户定义每个 task 的 harness 命令和验收标准
3. 填写 PRD.md 时将 `【待填写：...】` 替换为具体内容。
4. 第 11.2 章 Gate 调度表**不可留空**——必须定义至少 2 个 Gate，每个 Gate 绑定具体 task_id。
5. PRD 全部填完后，**请用户审阅并确认**。
6. 用户确认后，在 PRD.md 末尾添加 `PRD_STATUS: HUMAN_APPROVED`。
7. 运行 `python3 ~/.claude/skills/research/scripts/update_state.py --repo . --task-id TASK_001 --status done`。
8. 进入阶段 2。

**注意**：PRD 讨论阶段不要跳过任何一章。每章都要确保用户理解并同意。

---

### 阶段 2：自动执行（Continuous Loop）

PRD 锁定后，Bootstrap 控制器推进：

```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once
```


```
while STATUS.yaml.status not in (closed_*, gate_blocked):
    2. 执行 task（写代码/跑实验/复现 baseline）
    3. 完成后：
       python3 ~/.claude/skills/research/scripts/update_state.py \
         --repo . --task-id <ID> --status done \
         --commit-hash <HASH> --gate-id <GATE>
    4. 若任务被阻塞（同原因两次失败）：
       python3 ~/.claude/skills/research/scripts/update_state.py \
         --repo . --task-id <ID> --status blocked \
         --blocker-reason "具体原因"
    5. 若跨越 Gate 边界 → research-insight → wiki
    7. 继续循环，不询问用户
```

**不要停下来问用户是否继续**，除非命中停止条件。

---

### 停止条件

| 触发条件 | 行为 |
|----------|------|
| STATUS.yaml → `gate_blocked` | 报告 blocker，等待人工决策 |
| STATUS.yaml → `closed_*` | 报告 closeout 摘要，若 closeout 指示创建下一版本则进入阶段 1 起草 Vn+1/PRD.md |
| 实验证据反驳 PRD 核心假设 | 写 negative_result，请求人工 review |
| 需要修改 RESEARCH_DIRECTION.md | 请求人工批准 |
| 所有 Gate 通过 + closeout 完成 | 报告研究完成，若 closeout 允许 Paper Binding 则继续 |

---

### 子代理调度

| 场景 | 子代理 |
|------|--------|
| 数学公式、符号检查 | research-math |
| 文献搜索、baseline 分析 | research-literature |
| 复现 baseline | research-reproduce |
| 实现方法代码 | research-coding |
| 运行声明实验 | research-experiment |
| 结果分析、异常检测 | research-analysis |
| 论文更新 | research-paper |
| 跨文件一致性检查 | research-audit |

主 agent 始终负责：状态推进、gate 判定、active task 执行、wiki/closeout。

---

### 硬规则

- Keep all exploration inside Research Corridor.
- Never fabricate execution, artifact, benchmark, or paper result.
- Never create Vn+1 before Vn closeout.
- Never modify `RESEARCH_DIRECTION.md` without explicit user instruction.
- Never use mock/toy/synthetic output as claim evidence.
- Git allowed: `git status`, `git diff`, `git log`, `git add` allowed files, `git commit` current task, `git tag` closeout/paper binding.
- Git forbidden unless explicitly authorized: `git push`, `git reset --hard`, `git clean -fd`, `git rebase`, checkout that overwrites user changes, history rewrite, force push, deleting files outside task scope.

## Research Agent Behavior Contract

1. RQ before action. Every task must map to a Research Question, Claim, Experiment, Evidence, Figure/Table, or Paper Section.
2. Reproduce before propose. Before claiming novelty or designing experiments, search prior work and inspect the current repo.
3. Evidence before writing. Do not write paper claims unless the corresponding data, log, table, or citation exists.
4. Surgical edits. Modify only the current version folder or declared target files. Do not silently rewrite unrelated artifacts.
5. Conflict surfacing. If PRD, spec, task, paper, or code disagree, stop and report the conflict instead of averaging them.
6. Checkpoint long loops. After each major stage, write what changed, what evidence was produced, and what remains blocked.
7. Fail visibly. Missing data, failed reproduction, skipped experiment, or unverifiable claim must be explicitly marked.
8. Deterministic work belongs to scripts. Formatting checks, table generation, metric computation, and file routing should be scripted, not decided by LLM judgment.
9. Tests are evidence, not decoration. Passing tests only count if they verify the intended scientific or system behavior.
10. Convention beats novelty. Follow the project's existing folder structure, naming, template, and artifact format unless explicitly asked to migrate.
"""


def agents_root_template() -> str:
    return """# AGENTS.md

Codex / Claude Code 每次工作：

## Read First

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/goal.md`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.md`
7. `docs/research/{CURRENT}/SPEC.yaml`

## Bootstrap

If `docs/research/{CURRENT}/SPEC.yaml` is missing or has empty gates, run:
```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo . --once
```

## Continuous Loop


```bash
python3 ~/.claude/skills/research/scripts/update_state.py \
  --repo . --task-id <TASK_ID> --status done \
  --commit-hash <HASH> --gate-id <GATE_ID>
```

## Stop Conditions

- STATUS.yaml status is `gate_blocked` or `closed_*`
- PRD core hypothesis is contradicted by evidence
- RESEARCH_DIRECTION.md modification is needed (human approval required)
- All gates complete and closeout done

## Rules

- Run relevant tests if code changes.
- Record terminal/test evidence in run report.
- Do not change research direction without human approval.
- Do not create paper results from unverified artifacts.
- Do not fabricate execution, artifact, benchmark, or paper result.
- Do not create Vn+1 before closeout.
- Git allowed: status, diff, log, add allowed files, commit current task, tag closeout / paper binding.
- Git forbidden unless explicitly authorized: git push, git reset --hard, git clean -fd, git rebase, checkout overwriting user changes, rewrite history, force push, deleting files outside task scope.

## 研究智能体行为契约

1. RQ 先于行动。每个任务必须对应一个研究问题、主张、实验、证据、图表或论文章节。
2. 复现先于提出。在声称新颖性或设计实验之前，搜索已有工作并检查当前仓库。
3. 证据先于写作。除非存在相应的数据、日志、表格或引用，否则不要撰写论文主张。
4. 手术式编辑。只修改当前版本文件夹或声明的目标文件。不要静默重写无关工件。
5. 冲突暴露。如果 PRD、规范、任务、论文或代码不一致，停止并报告冲突，而不是取平均值。
6. 长循环检查点。每个主要阶段之后，写下发生了什么变化、产生了什么证据以及什么仍然受阻。
7. 可见失败。缺失的数据、失败的复现、跳过的实验或无法验证的主张必须明确标记。
8. 确定性工作属于脚本。格式化检查、表格生成、指标计算和文件路由应该脚本化，而不是由 LLM 判断决定。
9. 测试是证据而非装饰。只有通过验证预期科学或系统行为的测试才算数。
10. 约定优于新奇。遵循项目的现有文件夹结构、命名、模板和工件格式，除非明确要求迁移。
"""


def init_epoch_scaffold(repo: Path, research_dir: Path, title: str, purpose: str, force: bool = False) -> None:
    version = "V0"
    write_text(research_dir / "RESEARCH_DIRECTION.md", markdown_template(research_direction_template(title, purpose)), force)
    write_text(research_dir / "CURRENT", version + "\n", force)
    write_text(research_dir / "INDEX.md", markdown_template(research_index_template()), force)

    explore_dir = research_dir / "explore"
    for dirname in ["sessions", "syntheses", "proposals"]:
        (explore_dir / dirname).mkdir(parents=True, exist_ok=True)
    write_text(explore_dir / "sessions" / "EXP_0001.md", explore_session_template(version), force)
    write_text(explore_dir / "syntheses" / "EXP_SYNTHESIS.md", markdown_template(explore_synthesis_template()), force)
    write_text(explore_dir / "proposals" / "DIRECTION_UPDATE_PROPOSAL.md", markdown_template(explore_proposal_template("Direction Update Proposal")), force)
    write_text(explore_dir / "proposals" / "NEXT_VERSION_PROPOSAL.md", markdown_template(explore_proposal_template("Next Version Proposal")), force)
    write_text(explore_dir / "proposals" / "BASELINE_UPDATE_PROPOSAL.md", markdown_template(explore_proposal_template("Baseline Update Proposal")), force)
    write_text(explore_dir / "proposals" / "LITERATURE_BLOCKER.md", markdown_template(explore_proposal_template("Literature Blocker")), force)

    agent_dir = research_dir / "agent"
    write_text(agent_dir / "RUNBOOK.md", markdown_template(agent_runbook_template()), force)
    write_text(agent_dir / "CLAUDE_LOOP_PROMPT.md", markdown_template(claude_loop_prompt_template()), force)
    write_text(agent_dir / "CODEX_GOAL_TEMPLATE.md", markdown_template(codex_goal_template()), force)
    write_text(agent_dir / "SUBAGENT_POLICY.md", markdown_template(subagent_policy_template()), force)
    write_text(agent_dir / "LITERATURE_POLICY.md", markdown_template(literature_policy_template()), force)
    write_text(agent_dir / "GIT_POLICY.md", markdown_template(git_policy_template()), force)

    epoch_dir = research_dir / version
    for dirname in ["plans", "runs", "artifacts", "audits", "search", "reproduction", "rqs", "wiki"]:
        (epoch_dir / dirname).mkdir(parents=True, exist_ok=True)
    prd_tex = epoch_dir / "PRD.tex"
    write_text(prd_tex, research_prd_tex(title, purpose), force)
    render_pdf_from_tex(prd_tex, epoch_dir / "PRD.pdf", force)
    write_text(epoch_dir / "PRD_SUMMARY.md", markdown_template(epoch_prd_summary_template(version, title, purpose)), force)
    write_yaml(epoch_dir / "SPEC.yaml", epoch_spec_payload(version), force)
    write_text(epoch_dir / "PLAN.md", markdown_template(epoch_plan_template(version)), force)
    write_text(epoch_dir / "goal.md", markdown_template(epoch_goal_template(version, title, purpose)), force)
    write_yaml(epoch_dir / "STATUS.yaml", epoch_status_payload(version), force)
    write_yaml(epoch_dir / "RESEARCH_SPINE.yaml", epoch_spine_payload(version), force)
    write_yaml(epoch_dir / "TASK_QUEUE.yaml", epoch_task_queue_payload(version), force)
    write_text(epoch_dir / "LOOP_LOG.md", markdown_template(epoch_loop_log_template(version)), force)
    write_yaml(epoch_dir / "GIT_STATE.yaml", git_state_payload(version), force)
    write_text(epoch_dir / "git_log.md", markdown_template(git_log_template(version)), force)
    write_yaml(epoch_dir / "AUDIT_QUEUE.yaml", default_audit_queue(version), force)
    write_yaml(epoch_dir / "HUMAN_REVIEW_REQUESTS.yaml", default_human_review_requests(version), force)
    write_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml", default_paper_claim_ledger(version), force)
    init_rq_scaffold(epoch_dir, version, "RQ01", force)
    for filename, content in default_search_metadata(version).items():
        path = epoch_dir / "search" / filename
        if isinstance(content, str):
            write_text(path, markdown_template(content), force)
        else:
            write_yaml(path, content, force)
    for filename, content in default_reproduction_metadata(version).items():
        path = epoch_dir / "reproduction" / filename
        if isinstance(content, str):
            write_text(path, markdown_template(content), force)
        else:
            write_yaml(path, content, force)
    write_text(epoch_dir / "closeout.md", markdown_template(epoch_closeout_template(version)), force)
    write_text(epoch_dir / "PAPER_BINDING_DECISION.md", markdown_template(paper_binding_decision_template(version)), force)
    write_text(epoch_dir / "runs" / "TASK_001_report.md", markdown_template(task_run_report_template(version)), force)
    write_yaml(epoch_dir / "runs" / "TASK_001_report.yaml", task_run_report_payload(version), force)
    for filename, content in wiki_templates(version).items():
        write_text(epoch_dir / "wiki" / filename, markdown_template(content), force)
    write_yaml(epoch_dir / "wiki" / "insight_index.yaml", default_insight_index(version), force)
    for path in [
        epoch_dir / "plans" / ".gitkeep",
        epoch_dir / "runs" / ".gitkeep",
        epoch_dir / "artifacts" / ".gitkeep",
        epoch_dir / "audits" / ".gitkeep",
        epoch_dir / "search" / ".gitkeep",
        epoch_dir / "reproduction" / ".gitkeep",
        epoch_dir / "rqs" / ".gitkeep",
    ]:
        write_text(path, "", force)

    write_text(repo / "CLAUDE.md", claude_root_template(), force)
    write_text(repo / "AGENTS.md", agents_root_template(), force)


def source_epoch_is_closed(epoch_dir: Path) -> bool:
    status = load_yaml(epoch_dir / "STATUS.yaml")
    if str(status.get("status")) in CLOSED_VERSION_STATUSES or str(status.get("status")) == "paper_binding_ready":
        return True
    closeout = epoch_dir / "closeout.md"
    if closeout.exists() and closeout_final_status(read_text(closeout)) in CLOSED_VERSION_STATUSES:
        return True
    return False


def assert_can_create_epoch(research_dir: Path, from_version: str, target_version: str) -> None:
    if not re.fullmatch(r"V\d+", target_version):
        raise ValueError(f"target epoch version must match V\\d+: {target_version}")
    if not re.fullmatch(r"V\d+", from_version):
        raise ValueError(f"source epoch version must match V\\d+: {from_version}")
    source_dir = research_dir / from_version
    if not source_dir.exists():
        raise ValueError(f"source epoch {from_version} does not exist")
    if not source_epoch_is_closed(source_dir):
        raise ValueError(f"source epoch {from_version} is not closed")
    target_dir = research_dir / target_version
    if target_dir.exists():
        raise ValueError(f"target epoch {target_version} already exists")
    if version_sort_key(target_dir) <= version_sort_key(source_dir):
        raise ValueError(f"target epoch {target_version} must be after source epoch {from_version}")


def create_epoch(
    research_dir: Path,
    version: str,
    from_version: str | None = None,
    force: bool = False,
) -> Path:
    source_version = from_version or current_epoch_name(research_dir)
    assert_can_create_epoch(research_dir, source_version, version)
    epoch_dir = research_dir / version
    if force and epoch_dir.exists():
        shutil.rmtree(epoch_dir)

    manifest = load_epoch_manifest()
    for dirname in epoch_manifest_list("required_dirs", manifest):
        (epoch_dir / dirname).mkdir(parents=True, exist_ok=True)

    title = "Research Project"
    purpose = f"next-epoch-from-{source_version}"
    prd_tex = epoch_dir / "PRD.tex"
    write_text(prd_tex, research_prd_tex(title, purpose), force)
    render_pdf_from_tex(prd_tex, epoch_dir / "PRD.pdf", force)
    write_text(epoch_dir / "PRD_SUMMARY.md", markdown_template(epoch_prd_summary_template(version, title, purpose)), force)
    write_yaml(epoch_dir / "SPEC.yaml", epoch_spec_payload(version), force)
    write_text(epoch_dir / "PLAN.md", markdown_template(epoch_plan_template(version)), force)
    write_text(epoch_dir / "goal.md", markdown_template(epoch_goal_template(version, title, purpose)), force)
    write_yaml(epoch_dir / "STATUS.yaml", epoch_status_payload(version), force)
    write_yaml(epoch_dir / "RESEARCH_SPINE.yaml", epoch_spine_payload(version), force)
    write_yaml(epoch_dir / "TASK_QUEUE.yaml", epoch_task_queue_payload(version), force)
    write_text(epoch_dir / "LOOP_LOG.md", markdown_template(epoch_loop_log_template(version)), force)
    write_yaml(epoch_dir / "GIT_STATE.yaml", git_state_payload(version), force)
    write_text(epoch_dir / "git_log.md", markdown_template(git_log_template(version)), force)
    write_yaml(epoch_dir / "AUDIT_QUEUE.yaml", default_audit_queue(version), force)
    write_yaml(epoch_dir / "HUMAN_REVIEW_REQUESTS.yaml", default_human_review_requests(version), force)
    write_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml", default_paper_claim_ledger(version), force)
    init_rq_scaffold(epoch_dir, version, "RQ01", force)
    for filename, content in default_search_metadata(version).items():
        path = epoch_dir / "search" / filename
        if isinstance(content, str):
            write_text(path, markdown_template(content), force)
        else:
            write_yaml(path, content, force)
    for filename, content in default_reproduction_metadata(version).items():
        path = epoch_dir / "reproduction" / filename
        if isinstance(content, str):
            write_text(path, markdown_template(content), force)
        else:
            write_yaml(path, content, force)
    write_text(epoch_dir / "closeout.md", markdown_template(epoch_closeout_template(version)), force)
    write_text(epoch_dir / "PAPER_BINDING_DECISION.md", markdown_template(paper_binding_decision_template(version)), force)
    for filename, content in wiki_templates(version).items():
        write_text(epoch_dir / "wiki" / filename, markdown_template(content), force)
    write_yaml(epoch_dir / "wiki" / "insight_index.yaml", default_insight_index(version), force)
    for path in [
        epoch_dir / "plans" / ".gitkeep",
        epoch_dir / "runs" / ".gitkeep",
        epoch_dir / "artifacts" / ".gitkeep",
        epoch_dir / "audits" / ".gitkeep",
        epoch_dir / "search" / ".gitkeep",
        epoch_dir / "reproduction" / ".gitkeep",
        epoch_dir / "rqs" / ".gitkeep",
    ]:
        write_text(path, "", force)
    write_text(research_dir / "CURRENT", version + "\n", force=True)
    return epoch_dir


def init_spec_scaffold(research_dir: Path, force: bool = False) -> None:
    spec = research_dir / "spec"
    write_text(
        spec / "README.md",
        "\n".join(
            [
                "# Research Spec",
                "",
                "本目录是从 Research PRD 编译出来的全局机器可读执行契约。",
                "",
                "规则：",
                "- PRD 是人类研究真源。",
                "- Spec 是 AI 执行真源。",
                "- Paper 只提供叙事目标与 placeholder，不提供实验定义。",
                "- 不要从论文反推实验、数据集、基线、指标、seed 或结果。",
                "- 缺失信息必须写入 gap report 或 blocker，不能补造。",
                "",
            ]
        ),
        force,
    )
    write_yaml(
        spec / "global_spec.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "scaffold",
            "source": {"prd": "docs/research/prd/research_prd.md"},
            "authority": "compile_from_prd_not_paper",
            "rq_chain": [],
            "language_policy": {
                "keys": "YAML keys、schema 字段和稳定 ID 保持英文，便于脚本和 agent 解析。",
                "values": "所有说明性 value 使用中文，包括 title、description、purpose、notes、blockers、acceptance_criteria 和 repair。",
            },
            "rq_chain_template": {
                "rq_id": "RQ1",
                "hypothesis_id": "H1",
                "claim_id": "C01",
                "experiment_id": "E01",
                "dataset_id": "D01",
                "model_id": "M_OURS",
                "baseline_id": "B01",
                "metric_id": "M01",
                "seed_protocol_id": "S01",
                "task_id": "T_E01",
                "harness_id": "H_E01_FULL",
                "evidence_id": "EV_E01",
                "paper_placeholder": "PLACEHOLDER_PATTERN: E01.OURS.primary_metric",
                "description": "模板字段，不代表已声明实验；真实条目必须从 PRD 编译后写入 rq_chain。",
            },
            "title": "全局研究执行契约",
            "description": "从 Research PRD 编译 RQ、Hypothesis、Claim、Experiment、Task、Harness、Evidence 和 Paper placeholder 的稳定机器契约。",
            "notes": [
                "只能从 Research PRD 编译，不得从 Planned Paper 反推实验。",
                "所有缺失数据集、基线、指标、seed、命令和结果都必须登记为 blocker。",
            ],
            "insight_loop": {
                "status": "not_started",
                "latest_insight_id": None,
                "open_pivot_proposals": [],
                "cumulative_negative_results": [],
            },
            "epoch_loop_contract": {
                "default_structure": "docs/research/V0/",
                "current_epoch_pointer": "docs/research/CURRENT",
                "direction_ref": "docs/research/RESEARCH_DIRECTION.md",
                "task_queue_file": "TASK_QUEUE.yaml",
                "paper_binding_allowed_only_when": ["closed_stable", "paper_binding_ready"],
            },
            "runtime_contract": {
                "supported_agents": ["claude_code_ralph_loop", "codex_goal"],
                "execution_truth": [
                    "Spec defines executable research tasks.",
                    "Agent reports are not evidence unless backed by commands, artifacts, or explicit prompt-only status.",
                    "Full experiments and claim-supporting reproductions must use real datasets and real models or declared code commits.",
                    "Mock, toy, synthetic, stub, cached, or proxy outputs may only support unit/smoke/plumbing checks.",
                ],
                "prompt_only_policy": {
                    "allow_scaffold": True,
                    "allow_fake_execution": False,
                    "allow_mock_results_as_claim_evidence": False,
                },
            },
            "agent_autonomy": {
                "can_update_task_queue": True,
                "can_write_wiki": True,
                "can_close_version": True,
                "can_create_next_version_draft": True,
                "can_modify_research_direction": False,
                "can_bind_paper_results": "only_if_closed_stable",
            },
            "literature_policy": {
                "required_at": ["project_start", "version_start", "baseline_lock", "unexpected_result", "paper_binding"],
                "block_if_missing_for": ["new_method_claim", "baseline_superiority_claim", "related_work_section"],
            },
            "subagent_policy": {
                "allow_subagents": True,
                "allowed_subagents": [
                    "literature_scout",
                    "repo_explorer",
                    "experiment_engineer",
                    "debugger",
                    "artifact_auditor",
                    "wiki_synthesizer",
                    "paper_binder",
                ],
                "forbidden_subagent_actions": [
                    "modify_RESEARCH_DIRECTION",
                    "declare_paper_admissible_claim",
                    "fake_execution_result",
                    "create_next_version_without_closeout",
                ],
            },
            "version_transition_policy": {
                "create_next_version_when": [
                    "core_hypothesis_changed",
                    "main_research_question_changed",
                    "hard_gate_blocks_current_version",
                    "exploration_complete_and_confirmatory_phase_needed",
                    "baseline_landscape_changes_claim",
                    "metric_dataset_model_invalid",
                ],
                "do_not_create_next_version_for": [
                    "code_bug",
                    "missing_path",
                    "rerun_needed",
                    "minor_spec_field_fix",
                    "paper_placeholder_fix",
                ],
            },
            "engineering_gates": [
                {"id": "G_TESTS_PASS", "command": "python3 -m pytest tests -q", "required_for": "code_change"},
                {"id": "G_NO_FAKE_ARTIFACTS", "required_for": "all"},
                {"id": "G_REAL_DATA_MODEL", "required_for": ["full_experiment", "full_reproduction", "paper_binding"]},
                {"id": "G_WIKI_UPDATED", "required_for": "version_closeout"},
                {"id": "G_CLOSEOUT_COMPLETE", "required_for": "next_version_creation"},
                {"id": "G_PAPER_BINDING_ALLOWED", "required_for": "paper_binding"},
            ],
            "blockers": ["【阻塞】尚未从 PRD 填入 RQ -> Hypothesis -> Claim -> Experiment -> Harness -> Evidence 链。"],
        },
        force,
    )
    shared_payloads = {
        "dataset_manifest.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "数据集清单：只登记 PRD 已定义的数据集、冻结划分和预处理配置。",
            "datasets": [],
            "dataset_template": {
                "dataset_id": "D01",
                "name": "【待填写：真实数据集名称】",
                "data_source_type": "real_dataset",
                "provenance": "【待填写：公开来源 / 内部采集记录 / 官方 benchmark manifest】",
                "license": "【待填写：数据许可证或使用授权】",
                "split_file": "data/splits/D01_frozen_split_v1.json",
                "preprocessing_config": "configs/preprocess/D01_v1.yaml",
                "is_mock": False,
                "is_synthetic": False,
                "mock_allowed_only_for": ["unit_test", "smoke_test"],
                "claim_support_allowed": True,
            },
            "blockers": ["【阻塞】PRD 尚未声明可执行数据集。"],
        },
        "metric_manifest.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "指标清单：每个指标必须说明方向、计算方式和适用实验。",
            "metrics": [],
            "blockers": ["【阻塞】PRD 尚未声明主指标和辅助指标。"],
        },
        "model_manifest.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "模型清单：登记 proposed method、baseline 和复现目标的稳定 ID。",
            "models": [],
            "model_template": {
                "model_id": "M_OURS",
                "name": "【待填写：真实模型或方法名称】",
                "model_source_type": "real_model_or_code",
                "implementation_ref": "【待填写：代码模块、官方仓库、API model id 或 checkpoint 路径】",
                "checkpoint_or_model_version": "【待填写：checkpoint / model version / code commit】",
                "config_path": "configs/experiments/E01/ours.yaml",
                "is_mock": False,
                "is_stub": False,
                "claim_support_allowed": True,
            },
        },
        "environment_spec.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "环境规格：记录 Python、CUDA、系统依赖、官方代码 commit 和 license。",
            "environments": [],
        },
        "seed_protocol.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "随机种子协议：声明每个 claim-supporting experiment 必须运行的 seed 集合。",
            "seed_protocols": [],
            "blockers": ["【阻塞】PRD 尚未声明 seed 协议。"],
        },
        "artifact_schema.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "Artifact schema：统一 raw、aggregate、log、hash 和 reproduction note 的保存格式。",
            "artifact_schemas": [],
        },
        "anti_mock_policy.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "Anti-mock policy：mock/toy/synthetic/stub/cached/proxy 输出只能用于 unit、smoke 和 harness plumbing，不能支持科研主张，也不能作为未验证论文数值。",
            "allowed_for": ["unit_test", "smoke_test", "harness_plumbing", "placeholder_manuscript_structure"],
            "allowed_for_description": {
                "unit_test": "单元测试可以使用显式标记的 mock。",
                "smoke_test": "冒烟测试可以使用小样本或 stub 验证管线连通性。",
                "harness_plumbing": "harness 管道调试可以使用代理输出，但不得进入证据台账。",
                "placeholder_manuscript_structure": "论文草稿可以完整呈现表格结构、caption、结果段落和 placeholder binding，但未验证结果值必须保留为 typed placeholder，不得填入 plausible mock numeric values。",
            },
            "forbidden_for": [
                "research_claim",
                "benchmark_result",
                "baseline_comparison",
                "ablation_result",
                "final_task_completion",
                "paper_table_as_validated",
                "paper_figure_as_validated",
                "go_no_go_decision",
            ],
            "forbidden_for_description": {
                "research_claim": "科研主张必须来自真实执行、完整 seed、声明数据集、真实模型或真实代码、声明指标和可复跑 artifact。",
                "benchmark_result": "基准结果不得来自 mock、toy、synthetic、cached、stub 或 proxy 输出，必须绑定真实数据集、真实模型或官方代码 commit。",
                "ablation_result": "消融结果必须来自真实实验、真实数据和真实模型，不得使用 smoke 结果替代。",
                "paper_table_as_validated": "论文表格中呈现为已验证发现的数值，必须来自真实实验；未验证结果必须保留 typed placeholder。",
                "paper_figure_as_validated": "论文图不得展示伪造或未登记证据；未验证图表只能展示结构和 placeholder，不得展示 plausible mock numeric values。",
                "go_no_go_decision": "Go / No-Go 只能基于真实 harness、真实数据/模型检查和 evidence contract。",
            },
            "real_data_model_gate": {
                "required_for": [
                    "full_experiment",
                    "full_reproduction",
                    "benchmark_result",
                    "baseline_comparison",
                    "ablation_result",
                    "paper_binding",
                    "go_no_go_decision",
                ],
                "full_experiment_required_checks": sorted(FULL_EXPERIMENT_REAL_CRITERIA),
                "full_reproduction_required_checks": sorted(FULL_REPRODUCTION_REAL_CRITERIA),
                "block_on": ["mock", "toy", "synthetic", "stub", "cached", "proxy", "smoke_only"],
            },
        },
        "evidence_contract.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "证据契约：每个 claim 必须绑定 experiment、harness、artifact、命令、commit 和限制说明。",
            "claims": [],
            "evidence_rules": {
                "forbidden_as_claim_evidence": [
                    "mock_result",
                    "toy_result",
                    "smoke_test_only",
                    "synthetic_data_without_human_approved_exception",
                    "stub_model_result",
                    "proxy_model_result",
                    "cached_metric_without_raw_runs",
                ],
                "notes": ["【规则】只有通过 declared harness、真实数据/模型检查且记录 artifact hash 的 evidence 才能支持论文主张。"],
            },
        },
        "insight_policy.yaml": {
            "schema_version": SCHEMA_VERSION,
            "description": "Insight Feedback Loop 策略：定义执行失败与研究失败的分层、自动化边界和 pivot 触发条件。",
            "insight_policy": {
                "prd_hypothesis_statement": "当前 PRD 是初始研究假设，不是不可修改的真理。",
                "auto_allowed": [
                    "execution_fix",
                    "spec_refinement",
                    "harness_repair",
                    "diagnostic_experiment_proposal",
                    "claim_support_status_update",
                    "negative_result_recording",
                ],
                "human_review_required": [
                    "core_rq_change",
                    "problem_formulation_change",
                    "main_claim_change",
                    "paper_story_change",
                    "new_phenomenon_claim",
                    "delete_original_baseline",
                ],
                "pivot_trigger_conditions": [
                    "baseline_already_solves_problem",
                    "core_module_ablation_no_effect",
                    "phenomenon_only_in_toy_setting",
                    "scaling_invalidates_idea",
                    "loss_curve_contradicts_hypothesis",
                    "method_complex_but_low_gain",
                    "experiment_reveals_more_important_problem",
                ],
                "negative_result_policy": "负结果必须记录，不得隐藏。",
                "anomaly_to_experiment_pipeline": "异常 → insight log → anomaly report → diagnostic experiment proposal → human review",
            },
        },
    }
    for filename, payload in shared_payloads.items():
        write_yaml(spec / "shared" / filename, payload, force)

    write_yaml(
        spec / "reproduction" / "benchmark_candidate_matrix.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "候选 benchmark 论文矩阵：用于选择必须复现或比较的 baseline。",
            "candidate_papers": [],
        },
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "复现目标清单：每个 target 必须声明 reproduction_mode、source、commands、artifacts 和 acceptance criteria。",
            "allowed_reproduction_modes": [
                "official_code_reuse",
                "official_code_adaptation",
                "paper_based_reimplementation",
            ],
            "reproduction_target_template": {
                "reproduction_id": "R_B01",
                "baseline_id": "B01",
                "paper_id": "P01",
                "title": "【待填写：baseline 论文标题】",
                "role": ["main_baseline"],
                "reproduction_mode": "official_code_reuse",
                "source": {
                    "paper_url": "【待填写】",
                    "code_url": "【待填写】",
                    "code_commit": "【待填写】",
                    "license": "【待填写】",
                    "official_result_reference": "【待填写：表格或章节】",
                },
                "reason_for_selection": ["【待填写：closest_problem_setting / expected_by_reviewers / compatible_metric】"],
                "real_data_policy": {
                    "requires_real_dataset": True,
                    "dataset_id": "D01",
                    "forbid_mock_toy_synthetic": True,
                    "allowed_mock_scope": ["smoke_test"],
                },
                "real_model_policy": {
                    "requires_real_model_or_code": True,
                    "baseline_model_id": "B01",
                    "requires_official_or_declared_code_commit": True,
                    "forbid_stub_or_proxy_model": True,
                },
                "full_reproduction_required": True,
                "commands": {
                    "setup": ["bash scripts/reproduction/B01/setup_official.sh"],
                    "smoke": ["bash scripts/reproduction/B01/run_smoke.sh"],
                    "run": ["bash scripts/reproduction/B01/run_full.sh --seed {seed}"],
                    "convert": ["python -m project.reproduction.convert --baseline B01"],
                    "aggregate": ["python -m project.reproduction.aggregate --baseline B01"],
                },
                "required_artifacts": [
                    "artifacts/reproduction/B01/source/code_commit.txt",
                    "artifacts/reproduction/B01/aggregate/summary.json",
                    "artifacts/reproduction/B01/reproduction_note.md",
                ],
                "acceptance_criteria": [
                    "记录官方代码 URL、commit 和 license",
                    "使用声明的真实数据集和指标",
                    "使用真实 baseline 模型、checkpoint 或官方代码 commit",
                    "full reproduction 不得使用 mock / toy / synthetic / stub / cached / proxy 输出",
                    "输出符合项目 artifact schema",
                    "若未达到官方结果，需要解释 mismatch",
                ],
                "description": "模板字段，不代表真实复现目标；真实目标必须从 PRD 编译。",
            },
            "reproduction_targets": [],
            "blockers": ["【阻塞】尚未从 PRD 填入复现目标。"],
        },
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "复现任务图：定义 baseline 复现的 task、gate 和依赖。", "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_harness.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "复现 harness：与主实验 harness 分离，只证明 baseline comparability。", "harnesses": []},
        force,
    )
    write_text(
        spec / "reproduction" / "reproduction_gap_report.md",
        "# 复现缺口报告\n\n- 【阻塞】尚未从 PRD 填入 benchmark target、reproduction mode、官方代码 URL、commit、license、命令和 artifact。\n- 【规则】不要从 Planned Paper 反推复现实验；缺失信息必须回到 Research PRD 补齐。\n",
        force,
    )
    write_yaml(
        spec / "implementation" / "module_contracts.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "实现模块契约：登记模块职责、输入输出、配置、artifact 和 harness。", "modules": []},
        force,
    )
    write_yaml(
        spec / "implementation" / "implementation_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "实现任务图：用于从 Spec 派生 dated Research Plan。", "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "implementation" / "implementation_harness.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "实现 harness：验证模块和集成边界，不直接支持论文 claim。", "harnesses": []},
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "实验清单：每个 experiment 必须绑定 RQ、hypothesis、claim、dataset、baseline、metric、seed、command、artifact 和 harness。",
            "experiment_template": {
                "experiment_id": "E01",
                "experiment_type": "confirmatory",
                "title": "【待填写：主实验标题】",
                "linked_rq": "RQ1",
                "hypothesis": "H1",
                "claim": "C01",
                "purpose": "【待填写：该实验要验证什么】",
                "status": "planned",
                "dataset": "D01",
                "split_file": "data/splits/D01_frozen_split_v1.json",
                "preprocessing_config": "configs/preprocess/D01_v1.yaml",
                "models": ["M_OURS"],
                "proposed_method_config": "configs/experiments/E01/ours.yaml",
                "baselines": ["B01"],
                "data_model_truth": {
                    "full_experiment_requires_real_data": True,
                    "full_experiment_requires_real_model": True,
                    "dataset_manifest_must_set_is_mock_false": True,
                    "model_manifest_must_set_is_mock_false": True,
                    "forbid_mock_toy_synthetic_stub_cached_proxy": True,
                    "mock_allowed_only_for": ["unit_test", "smoke_test", "harness_plumbing"],
                },
                "seeds": [1, 2, 3],
                "metrics": ["M01"],
                "statistical_protocol": "【待填写：paired bootstrap / t-test / confidence interval 等】",
                "commands": {
                    "run": "python -m project.experiments.run --experiment E01 --seed {seed}",
                    "aggregate": "python -m project.experiments.aggregate --experiment E01",
                },
                "required_artifacts": [
                    "artifacts/experiments/E01/raw/{seed}/metrics.json",
                    "artifacts/experiments/E01/aggregate/summary.json",
                ],
                "harnesses": ["H_E01_FULL"],
                "support_condition": "【待填写：什么结果支持 claim】",
                "falsification_condition": "【待填写：什么结果推翻或降级 claim】",
                "mock_policy": "mock 输出只能用于 unit/smoke/plumbing；full experiment 必须使用真实数据和真实模型，不能支持科研主张",
                "description": "模板字段，不代表真实实验；真实实验必须从 PRD 编译。",
            },
            "experiments": [],
            "claims": [],
            "blockers": ["【阻塞】PRD 尚未声明可执行实验。"],
        },
        force,
    )
    write_yaml(
        spec / "insights" / "insight_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "Insight 全局索引：从机器可读角度登记所有洞察、异常、负结果和 pivot 提案。",
            "insight_categories": {
                "execution_failure": [],
                "research_failure": [],
                "anomaly": [],
                "negative_result": [],
                "pivot_proposal": [],
            },
            "insight_chain_template": {
                "insight_id": "I_E02_M1_NO_EFFECT",
                "source_plan": "plans/2026-05-10-run-e01/",
                "source_experiment": "E02",
                "insight_type": "negative_result",
                "observation": "【待填写：观察到了什么】",
                "expected_from_prd": "【待填写：PRD 原本期望什么】",
                "mismatch": "【待填写：哪里出乎意料】",
                "possible_explanation": "【待填写：可能解释】",
                "research_value": "【待填写：是 bug 还是真 insight】",
                "action_recommendation": "continue_original_plan",
                "confidence": "medium",
                "may_trigger_pivot": False,
                "requires_human_review": False,
                "related_pivot_proposal": None,
            },
            "insights": [],
        },
        force,
    )
    write_yaml(
        spec / "insights" / "insight_policy.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "Insight Feedback Loop 的 spec-local 策略副本，用于 plan/audit 不读取 shared 文件时仍能定位自动化边界。",
            "policy_source": "docs/research/spec/shared/insight_policy.yaml",
            "human_review_required": [
                "core_rq_change",
                "problem_formulation_change",
                "main_claim_change",
                "paper_story_change",
                "delete_original_baseline",
                "pivot_changes_prd_core_story",
            ],
            "auto_allowed": [
                "execution_fix",
                "spec_refinement",
                "harness_repair",
                "negative_result_recording",
                "diagnostic_experiment_proposal_without_core_prd_change",
            ],
        },
        force,
    )
    write_yaml(
        spec / "insights" / "anomaly_schema.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "required_fields": [
                "anomaly_id",
                "source_plan",
                "source_harness",
                "observation",
                "expected_from_prd",
                "mismatch",
                "possible_explanation",
                "research_value",
                "recommended_action",
                "confidence",
            ],
            "confidence_values": ["low", "medium", "high"],
            "notes": ["异常报告不得把未验证观察写成论文 claim；只记录现象、证据路径和下一步诊断建议。"],
        },
        force,
    )
    write_yaml(
        spec / "insights" / "pivot_proposal_schema.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "required_sections": [
                "Original PRD Claim",
                "New Observation",
                "Proposed 15-Degree Pivot",
                "Why This May Be Better",
                "Required PRD Changes",
                "Required Spec Changes",
                "Required New Experiments",
                "Human Decision Required",
            ],
            "human_decision_values": ["approve", "reject", "revise"],
            "notes": ["Pivot proposal 只能请求人类决策；agent 不得静默修改核心 PRD。"],
        },
        force,
    )
    write_yaml(
        spec / "insights" / "diagnostic_experiment_policy.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "诊断实验策略：只有不改变核心 RQ、问题表述或主 claim 的诊断实验可自动加入 exploratory/diagnostic track。",
            "auto_add_allowed_when": [
                "anomaly_has_artifact_or_log_source",
                "diagnostic_experiment_preserves_prd_core_claim",
                "dataset_metric_baseline_are_already_declared_or_explicitly_blocked",
            ],
            "human_review_required_when": [
                "diagnostic_experiment_changes_core_rq",
                "diagnostic_experiment_replaces_declared_baseline",
                "diagnostic_experiment_changes_main_metric",
                "diagnostic_experiment_reframes_paper_story",
            ],
        },
        force,
    )
    write_text(
        spec / "feedback" / "README.md",
        "\n".join(
            [
                "# Spec Feedback",
                "",
                "本目录记录每个 dated plan 完成或阻塞后可复用的执行经验。",
                "",
                "规则：",
                "- 这里只能记录环境、harness、artifact、转换器、数据路径和执行顺序经验。",
                "- 不得在这里修改 PRD 核心 RQ、主假设或主 claim。",
                "- 如果经验触及 PRD 方向，写入 `docs/research/audits/YYYY-MM-DD-prd-review/` 并等待人类决策。",
                "",
            ]
        ),
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "description": "实验任务图：定义主实验、消融、敏感性和失败案例分析的执行依赖。", "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_harness.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "实验 harness：full_experiment 必须要求完整 seed、完整 baseline、真实数据/模型、无 mock、artifact hash 和 independent rerun。",
            "harness_template": {
                "harness_id": "H_E01_FULL",
                "type": "full_experiment",
                "linked_experiment": "E01",
                "purpose": "【待填写：验证 E01 是否满足 claim-supporting evidence】",
                "cwd": ".",
                "command": "python -m project.harness verify E01",
                "timeout": 7200,
                "required_inputs": ["data/splits/D01_frozen_split_v1.json"],
                "required_outputs": [
                    {"path": "artifacts/experiments/E01/aggregate/summary.json", "schema": "artifact_schema"}
                ],
                "pass_criteria": [
                    "all_declared_seeds_completed",
                    "all_declared_baselines_completed",
                    "real_dataset_provenance_verified",
                    "real_model_provenance_verified",
                    "no_mock_data_used",
                    "no_synthetic_or_mock_inputs",
                    "full_run_not_smoke",
                    "no_missing_metric",
                    "no_test_tuning",
                    "artifact_hashes_recorded",
                ],
                "evidence_capture": ["stdout", "stderr", "artifact_hashes"],
                "may_support_research_claim": True,
                "independent_rerun_required": True,
                "description": "模板字段，不代表真实 harness；真实 harness 必须从 Spec 任务图声明。",
            },
            "harnesses": [],
        },
        force,
    )
    write_yaml(spec / "paper" / "placeholder_map.yaml", {"description": "论文 placeholder 映射：未观察结果必须绑定实验和 artifact。", "placeholders": []}, force)
    write_yaml(
        spec / "paper" / "result_binding.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "description": "结果绑定：把 observed artifact 安全绑定到论文 placeholder。",
            "result_binding_template": {
                "placeholder": "PLACEHOLDER_PATTERN: E01.OURS.primary_metric",
                "experiment_id": "E01",
                "source_artifact": "artifacts/experiments/E01/aggregate/summary.json",
                "binding_status": "blocked_until_observed",
                "required_checks": [
                    "harness_passed",
                    "artifact_hash_recorded",
                    "independent_rerun_completed",
                    "real_dataset_provenance_verified",
                    "real_model_provenance_verified",
                    "no_mock_data_used",
                    "no_synthetic_or_mock_inputs",
                    "full_run_not_smoke",
                ],
                "paper_location": "Table 1 / Main Results",
                "description": "模板字段，不代表真实结果绑定；真实 binding 必须来自 observed evidence。",
            },
            "bindings": [],
        },
        force,
    )


def current_epoch_rq_ids(research_dir: Path) -> list[str]:
    version = current_epoch_name(research_dir)
    if not version:
        return []
    spine_path = research_dir / version / "RESEARCH_SPINE.yaml"
    if spine_path.exists():
        spine = load_yaml(spine_path)
        ids = [
            str(item.get("id"))
            for item in as_list(spine.get("research_questions"))
            if isinstance(item, dict) and item.get("id")
        ]
        if ids:
            return ids
    rqs_root = research_dir / version / "rqs"
    ids = sorted(path.name for path in rqs_root.glob("RQ*") if path.is_dir()) if rqs_root.exists() else []
    return ids or ["RQ01"]


def sync_epoch_rq_spec_index(research_dir: Path, force: bool = True) -> None:
    version = current_epoch_name(research_dir)
    if not version:
        return
    epoch_dir = research_dir / version
    spec_path = epoch_dir / "SPEC.yaml"
    spec = load_yaml(spec_path) if spec_path.exists() else epoch_spec_payload(version)
    spec["prd_ref"] = "PRD.tex"
    spec["prd_summary_ref"] = "PRD_SUMMARY.md"
    spec["role"] = "epoch_aggregate_index"
    spec["rq_specs"] = [
        {"rq_id": rq_id, "spec_ref": f"rqs/{rq_id}/SPEC.yaml", "plan_ref": f"rqs/{rq_id}/PLAN.md"}
        for rq_id in current_epoch_rq_ids(research_dir)
    ]
    write_yaml(spec_path, spec, force=force)


def init_rq_spec_scaffold(research_dir: Path, rq_id: str | None = None, all_rqs: bool = False, force: bool = False) -> list[Path]:
    version = current_epoch_name(research_dir)
    if not version:
        return []
    epoch_dir = research_dir / version
    rq_ids = current_epoch_rq_ids(research_dir) if all_rqs else [rq_id or current_epoch_rq_ids(research_dir)[0]]
    written: list[Path] = []
    for rid in rq_ids:
        init_rq_scaffold(epoch_dir, version, rid, force=force)
        written.append(epoch_dir / "rqs" / rid / "SPEC.yaml")
    sync_epoch_rq_spec_index(research_dir, force=True)
    return written


def init_research_workspace(repo: Path, title: str, purpose: str, force: bool = False) -> Path:
    research_dir = repo / DEFAULT_RESEARCH_DIR
    for dirname in ["prd", "paper", "spec", "plans", "audits", "insights"]:
        (research_dir / dirname).mkdir(parents=True, exist_ok=True)
    for sub in ["anomaly_reports", "pivot_proposals", "negative_results"]:
        (research_dir / "insights" / sub).mkdir(parents=True, exist_ok=True)

    goal = goal_markdown(title, purpose)
    write_text(research_dir / "V0" / "goal.md", goal, force)

    prd = prd_markdown(title, purpose)
    write_text(research_dir / "prd" / "research_prd.md", prd, force)
    prd_tex = research_dir / "prd" / "research_prd.tex"
    write_text(prd_tex, research_prd_tex(title, purpose), force)
    render_pdf_from_tex(prd_tex, research_dir / "prd" / "research_prd.pdf", force)

    paper_md = planned_paper_markdown(title)
    write_text(research_dir / "paper" / "planned_paper.md", paper_md, force)
    paper_tex = research_dir / "paper" / "planned_paper.tex"
    write_text(paper_tex, planned_paper_tex(title), force)
    render_pdf_from_tex(paper_tex, research_dir / "paper" / "planned_paper.pdf", force)
    write_yaml(research_dir / "paper" / "placeholder_map.yaml", {"placeholders": []}, force)
    write_text(
        research_dir / "paper" / "paper_gap_report.md",
        "# 论文缺口报告\n\n- 【阻塞】如果 PRD 或 Spec 缺少 claim、experiment、dataset、baseline、metric、formula、table 或 placeholder binding，写在这里，不要在论文中发明。\n- 【规则】未验证结果必须保留为 typed placeholder；不得用 plausible mock numeric values 填充论文表格、图或结果段落。\n",
        force,
    )
    init_spec_scaffold(research_dir, force)
    write_text(research_dir / "insights" / "insight_log.md", _insight_log_template(), force)
    for path in [
        research_dir / "plans" / ".gitkeep",
        research_dir / "audits" / ".gitkeep",
        research_dir / "insights" / "anomaly_reports" / ".gitkeep",
        research_dir / "insights" / "pivot_proposals" / ".gitkeep",
        research_dir / "insights" / "negative_results" / ".gitkeep",
    ]:
        write_text(path, "", force)
    init_epoch_scaffold(repo, research_dir, title, purpose, force)
    return research_dir


def hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return "missing"
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def epoch_prd_source_path(epoch_dir: Path) -> Path:
    tex = epoch_dir / "PRD.tex"
    if tex.exists():
        return tex
    return epoch_dir / "PRD.md"


def git_commit(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return "UNKNOWN"
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "UNKNOWN"


def collect_spec_ids(research_dir: Path) -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {"experiments": set(), "harnesses": set(), "tasks": set(), "gates": set()}
    version = current_epoch_name(research_dir)
    epoch_spec = research_dir / version / "SPEC.yaml" if version else None
    if epoch_spec and epoch_spec.exists():
        spec = load_yaml(epoch_spec)
        for experiment in as_list(spec.get("experiments")):
            if isinstance(experiment, dict) and experiment.get("experiment_id"):
                ids["experiments"].add(str(experiment["experiment_id"]))
        for harness in as_list(spec.get("harnesses")):
            if isinstance(harness, dict) and harness.get("harness_id"):
                ids["harnesses"].add(str(harness["harness_id"]))
        for gate in as_list(spec.get("gates")):
            if isinstance(gate, dict) and gate.get("gate_id"):
                ids["gates"].add(str(gate["gate_id"]))
        queue = load_yaml(research_dir / version / "TASK_QUEUE.yaml")
        for task in as_list(queue.get("tasks")):
            if isinstance(task, dict) and task.get("task_id"):
                ids["tasks"].add(str(task["task_id"]))
        for gate in as_list(queue.get("gates")):
            if isinstance(gate, dict) and gate.get("gate_id"):
                ids["gates"].add(str(gate["gate_id"]))
        return ids
    # Fallback to legacy flat spec paths
    exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    for experiment in as_list(exp_manifest.get("experiments")):
        if isinstance(experiment, dict) and experiment.get("experiment_id"):
            ids["experiments"].add(str(experiment["experiment_id"]))
    for graph_path in [
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_task_graph.yaml",
        research_dir / "spec" / "implementation" / "implementation_task_graph.yaml",
    ]:
        graph = load_yaml(graph_path)
        for task in as_list(graph.get("tasks")):
            if isinstance(task, dict) and task.get("task_id"):
                ids["tasks"].add(str(task["task_id"]))
        for gate in as_list(graph.get("gates")):
            if isinstance(gate, dict) and gate.get("gate_id"):
                ids["gates"].add(str(gate["gate_id"]))
    for harness_path in [
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_harness.yaml",
        research_dir / "spec" / "implementation" / "implementation_harness.yaml",
    ]:
        harness_doc = load_yaml(harness_path)
        for harness in as_list(harness_doc.get("harnesses")):
            if isinstance(harness, dict) and harness.get("harness_id"):
                ids["harnesses"].add(str(harness["harness_id"]))
    return ids


def latest_child(parent: Path) -> Path | None:
    children = sorted([path for path in parent.iterdir() if path.is_dir()]) if parent.exists() else []
    return children[-1] if children else None


def generate_plan(
    research_dir: Path,
    date: str,
    purpose: str,
    track: str,
    gate: str | None = None,
    target: str = "codex",
    rq_id: str | None = None,
    force: bool = False,
) -> Path:
    plan_id = f"{date}-{slugify(purpose)}"
    version = current_epoch_name(research_dir)
    if version:
        plan_dir = research_dir / version / "plans" / plan_id
    else:
        plan_dir = research_dir / "plans" / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    ids = collect_spec_ids(research_dir)
    selected_gates = [gate] if gate else sorted(ids["gates"])
    harnesses = sorted(ids["harnesses"])
    repo = research_dir.parents[1] if research_dir.name == "research" and research_dir.parent.name == "docs" else research_dir.parent
    payload = {
        "plan_id": plan_id,
        "version": (version or "legacy"),
        "created_at": date,
        "purpose": f"执行目标：{purpose}",
        "loop_target": "paper_binding",
        "loop_mode": {"claude_code": "ralph_loop", "codex": "goal_driven"},
        "active_task_source": "TASK_QUEUE.yaml",
        "source_versions": {
            "prd_hash": hash_path(epoch_prd_source_path(research_dir / version)) if version else hash_path(research_dir / "prd"),
            "paper_hash": hash_path(research_dir / "paper"),
            "spec_hash": hash_path(research_dir / version / "SPEC.yaml" if version else research_dir / "spec"),
            "git_commit": git_commit(repo),
        },
        "track": track,
        "target": target,
        "source_spec": (
            [f"docs/research/{version}/SPEC.yaml"] if version else [
                "docs/research/spec/reproduction/reproduction_manifest.yaml",
                "docs/research/spec/reproduction/reproduction_harness.yaml",
                "docs/research/spec/experiments/experiment_manifest.yaml",
                "docs/research/spec/experiments/experiment_harness.yaml",
            ]
        ),
        "allowed_scope": [
            f"docs/research/{version}/plans/{plan_id}/**" if version else f"docs/research/plans/{plan_id}/**",
            "artifacts/**",
            "scripts/reproduction/**" if track == "reproduction" else "src/**",
        ],
        "forbidden_actions": [
            "不要从 Paper 推断具体的 dataset、seed、command 或 artifact 路径",
            "可以从 Paper 理解实验设计意图（baseline、metric、表格结构），但执行数据必须从 Spec 获取",
            "不要把未验证经验结论写入论文",
            "不要静默修改 baseline 核心算法",
        ],
        "gates": selected_gates,
        "harnesses": harnesses,
        "artifacts": ["artifacts/**"],
        "loop_rules": [
            "Each loop may complete at most one active task.",
            "Every TASK_QUEUE.yaml task must declare research_binding.",
            "Experiment, analysis, and result-binding tasks must use spine_bound binding with experiment_ids and evidence_ids.",
            "After each loop, update LOOP_LOG.md.",
            "If blocked twice by same cause, escalate to gate_blocked.",
            "If no active task exists, generate one from PLAN.md or close version.",
            "Do not start a new version unless current version is closed.",
            "Stay inside RESEARCH_DIRECTION.md.",
        ],
        "codex_goal_rules": [
            "Codex goal must name one concrete deliverable.",
            "Codex must run tests when code changes.",
            "Codex must cite terminal/test evidence in run report.",
            "Codex should not perform broad literature search unless task phase=literature and network is available.",
        ],
        "claude_ralph_rules": [
            "Do not expand scope mid-loop.",
            "Use subagents for large search or audit work.",
            "Write compact persistent state after each loop.",
            "Never rely on previous chat memory.",
        ],
        "subagent_triggers": {
            "literature_scout": {"when": ["version_start", "baseline_lock_needed", "new novelty claim appears", "paper_binding_related_work"]},
            "repo_explorer": {"when": ["need to locate files/modules", "read-only codebase mapping larger than 5 files"]},
            "experiment_engineer": {"when": ["implementing harness, hook, evaluator, artifact parser"]},
            "debugger": {"when": ["same test fails twice", "gate blocked by reproducible error"]},
            "artifact_auditor": {"when": ["before closeout", "before paper binding"]},
            "wiki_synthesizer": {"when": ["after every completed gate", "before closeout"]},
            "paper_binder": {"when": ["status=closed_stable"]},
        },
        "insight_loop": {
            "required": True,
            "output_file": f"docs/research/{version}/plans/{plan_id}/insight_log.md" if version else f"docs/research/plans/{plan_id}/insight_log.md",
            "epoch_output": "docs/research/{CURRENT}/wiki/* via research-insight",
            "legacy_status": "compatibility_only",
            "auto_classify": ["execution_failure", "spec_gap"],
            "human_review": [
                "research_failure",
                "pivot_proposal",
                "anomaly",
                "ambiguous_user_intent",
                "contradictory_requirements",
                "scope_decision_required",
                "methodology_divergence",
            ],
        },
        "completion_condition": [
            "所有选定 gate 通过，或阻塞原因已写入 blocker_log.md",
            "声明的 harness stdout/stderr 已保存",
            "current_state.md、blocker_log.md、decision_log.md、run_log.md、final_summary.md 已更新；epoch workspace 还需要 research-insight 更新 Vn/wiki/*",
        ],
    }
    write_yaml(plan_dir / "plan.yaml", payload, force)
    write_text(
        plan_dir / "plan.md",
        "\n".join(
            [
                f"# 研究执行计划：{plan_id}",
                "",
                f"- 目的：{purpose}",
                f"- 执行轨道：{track}",
                f"- 目标执行器：{target}",
                "",
                "## 执行规则",
                "",
                "- 可执行真源是 `docs/research/spec/`；执行时以 Spec 为准，Paper 为辅助参考。",
                "- PRD 是人类研究真源，用于解释意图和背景。",
                "- Paper 提供实验设计叙事和上下文参考（baseline、metric、表格结构），帮助 AI 理解预期结果形态。",
                "- 若 Paper 与 Spec 冲突，以 Spec 为准。",
                "- 始终执行最早尚未完成的 gate。",
                "- `TASK_QUEUE.yaml` 中每个 task 必须包含 `research_binding`；实验、分析和结果绑定任务必须通过 `spine_bound` 绑定到 `RESEARCH_SPINE.yaml` 的 RQ、claim、experiment 与 evidence。",
                "- 如果 required dataset、baseline、metric、seed、command 或 artifact 缺失，停止并记录 blocker。",
                "",
            ]
        ),
        force,
    )
    write_text(
        plan_dir / "ai_loop_prompt.md",
        "\n".join(
            [
                f"# AI 长循环执行提示词：{plan_id}",
                "",
                "可执行真源是 `docs/research/spec/`；执行时以 Spec 为准，Paper 为辅助参考。",
                "Research PRD 是人类研究真源，用于解释研究目标、背景、假设和证据边界。",
                "Research Paper 是上下文参考与实验设计叙事，帮助理解 baseline、表格结构和预期结果形态。",
                "可以从 Paper 读取实验设计意图（baseline、metric、表格结构、叙事逻辑），但具体的 dataset、seed、command、artifact 路径必须从 Spec 获取。",
                "若 Paper 与 Spec 冲突，以 Spec 为准。",
                "始终执行最早尚未完成的 gate。",
                "执行任何 task 前先检查 `TASK_QUEUE.yaml` 的 `research_binding`；缺失绑定则停止并记录 blocker。",
                "`spine_bound` task 必须能在 `RESEARCH_SPINE.yaml` 中解析 rq_id、claim_ids、experiment_ids 与 evidence_ids；实验、分析和结果绑定 task 不得缺少 experiment_ids 或 evidence_ids。",
                "运行 Spec 声明的 harness，并保存 stdout/stderr、artifact hash 和日志路径。",
                "每轮执行后更新 current_state.md、blocker_log.md、decision_log.md、run_log.md、final_summary.md；legacy dated plan 可继续写 insight_log.md。",
                "若存在 CURRENT/Vn，正式 insight promotion 交给 research-insight 写入当前 Vn/wiki/*。",
                "禁止将 mock / planning 值当作已验证结果写入证据或论文结论。",
                "当 required information 缺失时，停止执行并记录 blocker，不得补造。",
                "文档撰写阶段（编写或修改 PRD、SPEC、PLAN、RESEARCH_SPINE、ai_loop_prompt.md、goal.md）遇到用户意图不明、要求自相矛盾、或需要做出影响研究方向/核心假设/基准选择的决定时，必须停止并请求用户确认，不得自行推断。",
                "执行阶段（运行实验、编写代码、执行 harness、收集 artifact、运行测试）遇到同样情况时，不得停止询问用户偏好，应自主推进并仅对确实缺失的必需信息（dataset、seed、command、artifact 路径）记录 blocker。",
                "",
                "## Subagent Dispatch",
                "",
                "When the current gate requires specialized work, delegate to the matching Claude Code project subagent:",
                "",
                "- mathematical formulation or proof issue → `research-math`",
                "- literature / benchmark selection → `research-literature`",
                "- baseline reproduction → `research-reproduce`",
                "- method implementation → `research-coding`",
                "- full experiment execution → `research-experiment`",
                "- result analysis / anomaly / pivot → `research-analysis`",
                "- paper writing/update → `research-paper`",
            "- cross-file consistency check → `research-audit`",
                "",
                "The controller remains responsible for state, gates, and promotion.",
                "Subagents must not modify PRD core claims or bypass Spec/Plan constraints.",
                "",
                "执行每轮后，除了更新常规日志，还必须回答以下洞察问题；新项目交给 research-insight 写入当前 Vn/wiki/*，legacy dated plan 才写入 insight_log.md：",
                "- 我们理解到了什么？",
                "- 有没有异常？",
                "- 有没有与 PRD 假设冲突的现象？",
                "- 有没有比原始 idea 更简单的解释？",
                "- 有没有新的研究问题出现？",
                "- 有没有值得微调 15 度的方向？",
            ]
        )
        + "\n",
        force,
    )
    log_titles = {
        "current_state.md": "当前状态",
        "blocker_log.md": "阻塞日志",
        "decision_log.md": "决策日志",
        "run_log.md": "运行日志",
        "insight_log.md": "洞察日志",
        "final_summary.md": "最终总结",
    }
    for name, title_text in log_titles.items():
        if name == "final_summary.md":
            content = f"""# {title_text}

## 执行结果
【待填写：任务完成状态、通过的 gate、失败的 harness。】

## 关键观察（Observation）
【待填写：我们理解到了什么？有什么意外发现？】

## PRD 预期 vs 实际（Mismatch / Surprise）
【待填写：与 PRD 假设冲突的现象？】

## 可能解释
【待填写：为什么出现这个现象？】

## 研究价值判断
【待填写：是 implementation bug 还是真 insight？】

## 行动建议
- [ ] continue original plan
- [ ] repair spec
- [ ] add diagnostic experiment
- [ ] narrow claim
- [ ] propose 15-degree pivot
- [ ] request human review

## 置信度
low / medium / high
"""
        else:
            content = f"# {title_text}\n\n【待填写：本文件由执行循环持续更新。】\n"
        write_text(plan_dir / name, content, force)
    if version and rq_id:
        epoch_dir = research_dir / version
        init_rq_scaffold(epoch_dir, version, rq_id, force=False)
        write_text(epoch_dir / "rqs" / rq_id / "PLAN.md", markdown_template(rq_plan_template(version, rq_id)), force=True)
        tasks = rq_tasks_payload(version, rq_id)
        task = tasks["tasks"][0]
        task["task_id"] = f"{rq_id}_T_{slugify(track).upper().replace('-', '_')}"
        task["phase"] = track
        task["title"] = f"{track} task for {rq_id}"
        write_yaml(epoch_dir / "rqs" / rq_id / "TASKS.yaml", tasks, force=True)
        sync_epoch_rq_spec_index(research_dir, force=True)
    return plan_dir

def generate_audit(research_dir: Path, date: str, force: bool = False) -> Path:
    audit_dir = research_dir / "audits" / f"{date}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    direction_validation = validate_direction_ready(research_dir)
    direction_findings = direction_validation.issues or ["RESEARCH_DIRECTION.md completeness gate passed."]
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "dimensions": {
            key: {"status": "unchecked", "findings": []}
            for key in AUDIT_MATRIX_KEYS
        },
    }
    matrix["dimensions"]["direction_completeness"] = {
        "status": "pass" if direction_validation.ok else "blocker",
        "findings": direction_findings,
    }
    write_yaml(audit_dir / "alignment_matrix.yaml", matrix, force)
    write_yaml(
        audit_dir / "drift_findings.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "findings": [
                {"category": "direction_completeness", "severity": "blocker", "message": issue}
                for issue in direction_validation.issues
            ],
        },
        force,
    )
    direction_report_lines = ["## Research Direction Completeness", "", f"- status: {matrix['dimensions']['direction_completeness']['status']}"]
    direction_report_lines.extend(f"- {issue}" for issue in direction_findings)
    write_text(
        audit_dir / "audit_report.md",
        "# Research Audit Report\n\n"
        "This audit checks Research Direction, PRD, Paper, Spec, Plans, artifacts, and insight records for alignment drift.\n\n"
        + "\n".join(direction_report_lines)
        + "\n",
        force,
    )
    direction_repair = "\n".join(f"- [ ] {issue}" for issue in direction_validation.issues) or "- No Research Direction completeness blocker."
    write_text(
        audit_dir / "repair_plan.md",
        "# Repair Plan\n\n"
        "## Must fix before execution（执行失败）\n\n"
        "### Research Direction completeness\n\n"
        f"{direction_repair}\n\n"
        "## Insight opportunity（研究失败 / 异常 / 诊断实验）\n\n"
        "- 优先检查当前 Vn/wiki/* 中未纳入 spec/plan 的 positive signal、negative result、failed path 或 next_version_seed。\n"
        "- legacy docs/research/insights/ 只作为迁移候选，不直接当作当前 evidence。\n\n"
        "## Can fix later\n\n- TBD.\n\n"
        "## Recommended next research-plan target\n\n- TBD.\n\n"
        "## Recommended next research-insight target\n\n- TBD.\n",
        force,
    )
    return audit_dir


def generate_paper(research_dir: Path, force: bool = False) -> Path:
    version = current_epoch_name(research_dir)
    epoch_spec = research_dir / version / "SPEC.yaml" if version else None
    if epoch_spec and epoch_spec.exists():
        exp_manifest = load_yaml(epoch_spec)
        source_label = f"`docs/research/{version}/SPEC.yaml`"
    else:
        exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
        source_label = "`docs/research/spec/experiments/experiment_manifest.yaml`"
    experiments = [item for item in as_list(exp_manifest.get("experiments")) if isinstance(item, dict)]
    if not experiments and epoch_spec and epoch_spec.exists():
        # Fallback to legacy spec if epoch spec experiments are empty
        exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
        experiments = [item for item in as_list(exp_manifest.get("experiments")) if isinstance(item, dict)]
        if experiments:
            source_label = "`docs/research/spec/experiments/experiment_manifest.yaml` (epoch spec empty, legacy fallback)"

    placeholders = []
    paper = planned_paper_markdown("Planned Research Paper")
    bound_lines = [
        "",
        "## Bound Placeholder Map (Generated From Spec)",
        "",
        f"This section is generated from {source_label}. It reserves result locations only; it does not report empirical findings.",
        "",
        "| Placeholder | Experiment | Method | Metric | Source after execution |",
        "| --- | --- | --- | --- | --- |",
    ]
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id", "")).strip()
        if not experiment_id:
            continue
        placeholder = f"{{{{{experiment_id}.OURS.primary_metric}}}}"
        bound_lines.append(
            f"| `{placeholder}` | {experiment_id} | OURS | primary_metric | artifacts/experiments/{experiment_id}/aggregate/summary.json |"
        )
        placeholders.append(
            {
                "placeholder": placeholder,
                "experiment_id": experiment_id,
                "method_id": "OURS",
                "metric": "primary_metric",
                "source_after_execution": f"artifacts/experiments/{experiment_id}/aggregate/summary.json",
                "paper_location": "Table 1 / Main Results",
            }
        )
    if not placeholders:
        bound_lines.append("| 【阻塞：Spec 尚未声明可绑定实验】 | - | - | - | - |")
    paper = paper.rstrip() + "\n" + "\n".join(bound_lines) + "\n"
    write_text(research_dir / "paper" / "planned_paper.md", paper, force)
    paper_tex = research_dir / "paper" / "planned_paper.tex"
    write_text(paper_tex, planned_paper_tex("Planned Research Paper"), force)
    write_yaml(research_dir / "paper" / "placeholder_map.yaml", {"placeholders": placeholders}, force)
    gap_lines = [
        "# 论文缺口报告",
        "",
        "本文件记录 manuscript draft 中所有 typed placeholder 的位置、替换条件和真实证据来源。论文正文不得用 plausible mock numeric values 代替未验证结果。",
        "",
    ]
    if placeholders:
        gap_lines.extend(
            [
                "## 当前状态",
                "",
                "- 已从 Spec 中发现可绑定实验 placeholder。",
                "- 论文正文中的表格和结果段落保留 typed placeholder，以呈现完整 manuscript 结构且避免数值污染。",
                "- 以下 placeholder 对应位置必须在获得真实证据后替换：",
                "",
            ]
        )
        for ph in placeholders:
            gap_lines.append(
                f"- `{ph['placeholder']}` → 论文位置：{ph['paper_location']} → 证据来源：{ph['source_after_execution']}"
            )
        gap_lines.extend(
            [
                "",
                "## 替换条件",
                "",
                "- 对应 harness 已通过并生成 artifact。",
                "- 数值已人工复核并与 PRD 中的实验设计一致。",
                "- 替换后更新 `placeholder_map.yaml` 并删除本报告中对应条目。",
            ]
        )
    else:
        gap_lines.extend(
            [
                "## 【阻塞】缺少可绑定实验",
                "",
                "- `spec/experiments/experiment_manifest.yaml` 尚未声明可用于论文结果位置的实验。",
                "- 在补全 PRD 与 Spec 前，论文 Results 部分只能保留空表格框架，不能填入任何数值。",
            ]
        )
    write_text(research_dir / "paper" / "paper_gap_report.md", "\n".join(gap_lines) + "\n", force)
    render_pdf_from_tex(paper_tex, research_dir / "paper" / "planned_paper.pdf", force)
    return research_dir / "paper"


DEMO_PLACEHOLDERS = [
    {
        "placeholder": "{{E01.B01.task_success}}",
        "experiment_id": "E01",
        "method_id": "B01",
        "metric": "task_success",
        "source_after_execution": "artifacts/experiments/E01/aggregate/summary.json",
        "paper_location": "Table 2 / Main task success baseline",
    },
    {
        "placeholder": "{{E01.OURS.task_success}}",
        "experiment_id": "E01",
        "method_id": "OURS",
        "metric": "task_success",
        "source_after_execution": "artifacts/experiments/E01/aggregate/summary.json",
        "paper_location": "Table 2 / Main task success",
    },
    {
        "placeholder": "{{E02.OURS.evidence_coverage}}",
        "experiment_id": "E02",
        "method_id": "OURS",
        "metric": "evidence_coverage",
        "source_after_execution": "artifacts/experiments/E02/aggregate/summary.json",
        "paper_location": "Table 2 / Evidence coverage",
    },
    {
        "placeholder": "{{E03.OURS.invalid_claim_rate}}",
        "experiment_id": "E03",
        "method_id": "OURS",
        "metric": "invalid_claim_rate",
        "source_after_execution": "artifacts/experiments/E03/aggregate/summary.json",
        "paper_location": "Table 3 / Claim safety",
    },
    {
        "placeholder": "{{E04.OURS.planner_overhead_sec}}",
        "experiment_id": "E04",
        "method_id": "OURS",
        "metric": "planner_overhead_sec",
        "source_after_execution": "artifacts/experiments/E04/aggregate/summary.json",
        "paper_location": "Table 4 / Runtime overhead",
    },
]


def demo_paper_markdown() -> str:
    return """# ContractGraph: Evidence-Bound Execution for LLM Coding Agents

## Abstract

LLM coding agents increasingly solve repository-scale tasks by mixing natural-language planning, tool calls, code edits, tests, and self-review. The central failure mode is not only that an agent writes incorrect code, but that it loses the contract between the research question, the implementation task, the harness that validates the task, and the evidence allowed to support a paper claim. We propose **ContractGraph**, an execution framework that represents agentic coding research as a typed graph over claims, tasks, harnesses, artifacts, evidence, and manuscript result bindings. ContractGraph does not attempt to make the language model intrinsically truthful; instead, it constrains the execution loop so that every claim must be backed by a declared harness and every paper result location must be bound to an artifact schema. We formulate evidence-bound agent execution, design a graph scheduler with anti-mock gates, and define a benchmark protocol for repository repair tasks. Empirical result slots remain visible as typed placeholders until the declared harnesses pass and real artifacts are bound.

## 1. Introduction

Modern coding agents are no longer single-turn code generators. A practical agent reads a repository, builds an internal plan, edits files, runs tests, interprets failures, updates its plan, and may repeat this loop for hours. This makes agentic coding a systems problem: success depends on how tasks are decomposed, how evidence is captured, and how claims are prevented from drifting away from the artifacts that actually support them.

The research gap addressed by this paper is the absence of a strict evidence contract for long-running coding agents. Existing agent workflows often separate the narrative layer from the execution layer: the paper describes research questions and expected contributions, while the implementation loop operates over ad hoc TODO lists, shell commands, and logs. This separation creates three failure modes. First, a task can be marked complete because a local test passes even though the declared research harness was never run. Second, mock or smoke-test outputs can accidentally enter tables that look like empirical results. Third, the paper can accumulate claims that no longer correspond to the current specification.

We propose ContractGraph, a graph-structured control plane that keeps the paper, specification, execution plan, harnesses, artifacts, and evidence ledger synchronized. The key idea is simple: every paper claim must be represented as a path from research question to hypothesis, experiment, task, harness, evidence artifact, and result placeholder. If any edge is missing, the agent is allowed to continue engineering work, but it is not allowed to bind the result into the manuscript.

This paper makes four contributions. First, we formulate evidence-bound agent execution as a typed graph consistency problem. Second, we design a scheduler that executes the earliest incomplete gate while preserving source hashes and blocker logs. Third, we introduce anti-mock evidence rules that distinguish smoke-test utility from claim-supporting evidence. Fourth, we provide a placeholder-complete evaluation protocol that specifies what must be measured before the manuscript can make empirical claims.

## 2. Related Work and Research Gap

LLM tool-use agents show that language models can call external tools and use observations to update their next actions. Coding agents extend this idea to repositories, tests, and issue-resolution workflows. Reflection-based agents add self-critique, while benchmark-driven systems measure success on issue-fixing or code-generation suites. These directions improve action selection, but they usually leave the evidence contract implicit.

ContractGraph is orthogonal to stronger base models and better prompting. It asks a systems question: given an agent that can edit, run commands, and reason, how do we prevent the execution state from drifting away from the research specification and the manuscript? The closest baseline is a plan-then-code agent that writes a plan and executes tasks sequentially. The limitation is that the plan often lacks typed links to evidence artifacts, paper placeholders, and anti-mock policies. ContractGraph makes those links first-class.

| Research thread | Representative capability | Remaining gap | ContractGraph response |
| --- | --- | --- | --- |
| Tool-use agents | Use shell, tests, search, and code-edit tools | Tool observations are not automatically claim evidence | Require artifact schemas and harness IDs |
| Coding benchmarks | Measure issue-resolution or code-generation success | Benchmark pass/fail does not explain paper-claim provenance | Bind metrics to claim-specific evidence paths |
| Reflection agents | Critique and revise plans | Self-critique can accept weak evidence | Add anti-mock gates and independent rerun requirements |
| Reproducibility checklists | Record environment and seeds | Checklist is often outside the execution loop | Make checklist fields executable graph nodes |

## 3. Problem Formulation

Let a repository task be \(x \\in \\mathcal{X}\), an agent action sequence be \(a_{1:T}\), and an execution trace be \(\\tau = (s_0, a_1, o_1, \\ldots, s_T)\). A conventional coding agent optimizes for task success, such as passing tests or resolving an issue. ContractGraph adds a research constraint: a claim \(c\) is admissible only if there exists a valid evidence path
\[
RQ \\rightarrow H \\rightarrow c \\rightarrow E \\rightarrow D,M,B,S \\rightarrow T \\rightarrow HN \\rightarrow A \\rightarrow P,
\]
where \(RQ\) is a research question, \(H\) a hypothesis, \(E\) an experiment, \(D/M/B/S\) dataset, model, baseline, and seed declarations, \(T\) a task, \(HN\) a harness, \(A\) an artifact, and \(P\) a paper placeholder.

The optimization target is not only task success. We want to maximize completed claim-supporting evidence while minimizing invalid claim bindings:
\[
\\max \\; \\mathrm{Success}(a_{1:T}) + \\lambda \\mathrm{EvidenceCoverage}(G) - \\mu \\mathrm{InvalidBinding}(G).
\]
The graph \(G\) is valid only when every full-experiment harness requires all declared seeds, all declared baselines, no mock data, no missing metrics, artifact hashes, and an independent rerun before supporting a paper claim.

## 4. Method: ContractGraph

ContractGraph consists of four modules.

The **Spec Compiler** converts a Research PRD into stable YAML manifests: datasets, metrics, models, seed protocols, reproduction targets, experiments, tasks, harnesses, and result bindings. The compiler does not read the paper as an experiment source. This prevents the manuscript from inventing executable work.

The **Gate Scheduler** selects the earliest incomplete gate from the task graph. A gate is complete only when its tasks are done, its declared harnesses pass or produce documented blockers, and stdout, stderr, artifact hashes, and decision logs are saved. If a required dataset or baseline is missing, the scheduler stops and writes a blocker instead of fabricating data.

The **Evidence Ledger** records which artifacts may support which claims. Unit tests and smoke tests can validate engineering plumbing, but they cannot support research claims. Full experiment harnesses must enforce all declared seeds, baselines, metrics, and independent reruns.

The **Paper Binder** replaces manuscript placeholders only after the evidence ledger marks the source artifact as claim-supporting. Until then, placeholders remain visible in the paper and the gap report lists what must be executed.

Algorithmically, ContractGraph runs a bounded loop: load Spec, select the earliest incomplete gate, execute its harness, capture artifacts, update the state logs, validate evidence eligibility, and only then update paper bindings. The design intentionally treats paper writing as a downstream binding step, not as a source of experiments.

## 5. Experimental Protocol

The planned evaluation uses a repository-repair benchmark with frozen issue splits. The benchmark is intentionally scoped for the first phase because the study targets execution correctness and evidence integrity, not model scaling. The candidate split size and composition remain placeholders until replaced by the final benchmark manifest.

We compare four systems. **B01 Direct Agent** reads the issue and edits code without an explicit graph contract. **B02 Plan-then-Code Agent** writes a task plan and executes it sequentially. **B03 Reflection Agent** adds self-review after failures. **OURS ContractGraph Agent** uses the typed execution graph, anti-mock gates, evidence ledger, and paper binder.

| ID | Research question | Metric | Planned protocol | Result binding |
| --- | --- | --- | --- | --- |
| E01 | Does graph-constrained execution improve task completion discipline? | task_success | 3 seeds over frozen issue splits | {{E01.OURS.task_success}} |
| E02 | Does explicit evidence tracking increase claim coverage? | evidence_coverage | Audit each completed task for artifact-backed claims | {{E02.OURS.evidence_coverage}} |
| E03 | Does anti-mock gating reduce invalid manuscript bindings? | invalid_claim_rate | Inject mock artifacts and measure rejection rate | {{E03.OURS.invalid_claim_rate}} |
| E04 | What overhead does the control plane introduce? | planner_overhead_sec | Measure scheduler and validation runtime per gate | {{E04.OURS.planner_overhead_sec}} |

## 6. Planned Result Bindings and Expected Sensitivity

Table 2 is placeholder-complete: it defines the result slots and comparison structure without inserting plausible numeric values. No cell can enter a submission until the corresponding artifacts exist under `artifacts/experiments/**` and the full harnesses pass.

| Metric | Baseline binding | ContractGraph binding | Admission condition |
| --- | --- | --- | --- |
| Task success | {{E01.B01.task_success}} | {{E01.OURS.task_success}} | full harness pass and independent rerun |
| Evidence coverage | baseline audit placeholder | {{E02.OURS.evidence_coverage}} | artifact-backed claim audit |
| Invalid claim rate | injected-invalid-artifact placeholder | {{E03.OURS.invalid_claim_rate}} | anti-mock gate rejects invalid bindings |
| Planner overhead | baseline runtime placeholder | {{E04.OURS.planner_overhead_sec}} | scheduler runtime captured from logs |

The planned interpretation is as follows. E01 tests whether typed gate execution improves completion discipline. E02 tests whether the evidence ledger increases the fraction of claims with valid artifact support. E03 tests the safety function of anti-mock gates by injecting invalid artifacts. E04 measures whether the added control plane remains operationally acceptable for long-running coding tasks. The final paper may discuss trade-offs only after these placeholders are replaced by validated summaries.

## 7. Execution Plan and Evidence Contract

Each experiment has a full harness. A full harness must complete all declared seeds, complete all declared baselines, verify that no mock data is used as claim evidence, check that no metric is missing, record artifact hashes, and require an independent rerun before paper binding. Smoke tests are still useful, but they can only support implementation readiness, not research claims.

The first execution plan should target E03 because invalid-claim rejection is the core safety property and can be tested before expensive benchmark runs. The second plan should target E01 on a five-issue smoke subset only to validate infrastructure. The third plan should run the full frozen split. The final paper update should occur only after the evidence ledger marks E01 through E04 as claim-supporting.

## 8. Limitations and Ethics

ContractGraph can prevent a class of evidence-binding errors, but it cannot make an incorrect benchmark representative. If the frozen issue split is narrow, the paper must limit its claims to that split. ContractGraph also adds engineering overhead; if E04 shows excessive planner latency, the method may be useful only for high-stakes research runs rather than everyday coding assistance. Ethically, the system is designed to reduce accidental fabrication by making mock artifacts ineligible for claims, but it does not remove the need for human review of benchmark selection, baseline fairness, and negative results.

## 9. Conclusion

This paper presents ContractGraph, a graph-based execution contract for LLM coding-agent research. The central idea is to make the path from research question to paper result explicit and executable. The current manuscript is complete as a placeholder-complete research draft: it defines the method, formalization, evaluation protocol, result slots, and evidence rules. Its empirical claims remain intentionally unbound until the declared experiments run and their artifacts pass the full harnesses.
"""


def demo_paper_tex() -> str:
    return r"""\documentclass[UTF8,11pt]{ctexart}
\usepackage[a4paper,left=23mm,right=23mm,top=23mm,bottom=25mm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs,tabularx,array}
\usepackage{hyperref}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue, citecolor=blue}
\emergencystretch=2em
\title{ContractGraph: Evidence-Bound Execution for LLM Coding Agents}
\author{Research Execution Skills Demo}
\date{\today}
\begin{document}
\maketitle

\begin{abstract}
LLM coding agents increasingly solve repository-scale tasks by mixing planning, tool calls, code edits, tests, and self-review. The central failure mode is not only incorrect code, but loss of the contract between research questions, implementation tasks, harnesses, and evidence. We propose ContractGraph, an execution framework that represents agentic coding research as a typed graph over claims, tasks, harnesses, artifacts, evidence, and manuscript result bindings. Empirical result slots remain typed placeholders until declared harnesses pass.
\end{abstract}

\section{Introduction}
Practical coding agents read repositories, plan edits, run tests, interpret failures, and repeat this loop for hours. This makes agentic coding a systems problem: success depends on task decomposition, evidence capture, and prevention of drift between the specification and the manuscript. ContractGraph keeps paper claims, execution plans, harnesses, and artifact schemas synchronized through a typed evidence graph.

\section{Problem Formulation}
Let a repository task be \(x \in \mathcal{X}\), an action sequence be \(a_{1:T}\), and an execution trace be \(\tau\). A claim \(c\) is admissible only if there exists a path from research question to hypothesis, experiment, dataset, task, harness, artifact, and paper placeholder. The target is to maximize task success and evidence coverage while minimizing invalid result bindings.

\section{Method}
ContractGraph has four modules: a Spec Compiler, a Gate Scheduler, an Evidence Ledger, and a Paper Binder. The compiler turns the PRD into stable manifests. The scheduler executes the earliest incomplete gate. The ledger records which artifacts may support which claims. The binder updates manuscript placeholders only after the evidence ledger marks the source artifact as claim-supporting.

\begin{table}[htbp]
\centering
\caption{ContractGraph module contract}
\begin{tabularx}{\textwidth}{@{}L{0.18\textwidth}Y Y@{}}
\toprule
Module & Responsibility & Claim boundary \\
\midrule
Spec Compiler & Builds typed manifests from PRD & Cannot infer experiments from paper \\
Gate Scheduler & Executes earliest incomplete gate & Stops on missing required inputs \\
Evidence Ledger & Tracks artifact eligibility & Mock outputs cannot support claims \\
Paper Binder & Connects artifacts to result slots & Binds only after full harness pass \\
\bottomrule
\end{tabularx}
\end{table}

\section{Experimental Protocol}
The planned study uses a repository-repair benchmark with frozen issue splits. We compare a direct agent, a plan-then-code agent, a reflection agent, and the ContractGraph agent.

\begin{table}[htbp]
\centering
\small
\caption{Experiment map}
\begin{tabularx}{\textwidth}{@{}L{0.09\textwidth}Y L{0.16\textwidth}L{0.2\textwidth}@{}}
\toprule
ID & Question & Metric & Binding \\
\midrule
E01 & Completion discipline & success & E01.task \\
E02 & Evidence tracking & coverage & E02.coverage \\
E03 & Anti-mock safety & invalid rate & E03.invalid \\
E04 & Control overhead & overhead & E04.time \\
\bottomrule
\end{tabularx}
\end{table}

\section{Planned Result Bindings}
Table 3 is placeholder-complete, not empirical evidence. It defines expected result bindings for later experiments without plausible numeric values.

\begin{table}[htbp]
\centering
\small
\caption{Placeholder result bindings}
\begin{tabularx}{\textwidth}{@{}Ylll@{}}
\toprule
Metric & Baseline binding & ContractGraph binding & Admission condition \\
\midrule
Task success & E01.B01 & E01.OURS & full harness \\
Evidence coverage & audit baseline & E02.OURS & artifact audit \\
Invalid claim rate & invalid binding & E03.OURS & anti-mock gate \\
Planner overhead & runtime baseline & E04.OURS & captured logs \\
\bottomrule
\end{tabularx}
\end{table}

\section{Limitations and Ethics}
ContractGraph prevents evidence-binding errors, but it cannot make a narrow benchmark representative. If the frozen issue split is weak, the paper must limit its claims. The method also adds overhead and therefore may be appropriate mainly for high-stakes research execution. The anti-mock policy reduces accidental fabrication by making mock artifacts ineligible for paper claims.

\section{Conclusion}
ContractGraph makes the path from research question to paper result explicit and executable. This draft is complete as a placeholder-complete manuscript: it defines the method, formalization, protocol, result slots, and evidence rules. Empirical claims remain intentionally unbound until the declared experiments run and their artifacts pass full harnesses.

\chapter{探索与洞察策略（Exploration and Insight Policy）}
\textbf{章节目标}：明确 PRD 是初始研究假设而非终局真理；定义执行失败与研究失败的分层；规定哪些调整可由 agent 自动完成，哪些必须请求人类确认。

\begin{table}[H]
\centering
\caption{自动调整与人类确认边界表}
\begin{tabularx}{\textwidth}{L{0.22\textwidth}Y Y Y}
\toprule
调整类型 & 可自动执行 & 需人类确认 & 记录位置 \\
\midrule
执行修复（代码/环境/路径） & 是 & 否 & plan/blocker\_log.md \\
Spec 细化（命令/artifact/schema） & 是 & 否 & spec/ 对应文件 \\
Diagnostic experiment 提议 & 是 & 否（不改变核心假设时） & spec/experiments/ \\
核心 RQ / 问题表述变更 & 否 & 是 & insights/pivot\_proposals/ \\
主 claim / 论文故事变更 & 否 & 是 & insights/pivot\_proposals/ \\
负结果记录 & 是 & 否 & insights/negative\_results/ \\
Anomaly report & 是 & 否 & insights/anomaly\_reports/ \\
\bottomrule
\end{tabularx}
\end{table}

\textbf{常见错误}：把 PRD 当成不可修改的圣经；负结果被隐藏；agent 擅自修改核心 RQ；洞察不被记录。

\textbf{证据边界}：本章只定义策略和边界，不声称任何实验结果。

\textbf{验收标准}：读者能清楚说出哪些修改可以自动做、哪些必须等人批、负结果放哪里、异常怎么变成新实验。

\end{document}
"""


def write_demo_spec(research_dir: Path, force: bool = False) -> None:
    experiments = [
        ("E01", "RQ1", "H1", "C01", "task_success", "测试 typed gate 是否提升任务完成纪律。"),
        ("E02", "RQ2", "H2", "C02", "evidence_coverage", "测试 evidence ledger 是否提升 claim-to-artifact 覆盖率。"),
        ("E03", "RQ3", "H3", "C03", "invalid_claim_rate", "测试 anti-mock gate 是否降低无效 claim binding。"),
        ("E04", "RQ4", "H4", "C04", "planner_overhead_sec", "测试控制平面带来的执行开销。"),
    ]
    write_yaml(
        research_dir / "spec" / "global_spec.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "demo_placeholder_complete",
            "authority": "demo_placeholder_complete_without_numeric_results",
            "source": {"prd": "docs/research/prd/research_prd.md"},
            "rq_chain": [
                {
                    "rq_id": rq,
                    "hypothesis_id": hyp,
                    "claim_id": claim,
                    "experiment_id": exp,
                    "dataset_id": "D01",
                    "model_id": "M_OURS",
                    "baseline_id": "B01",
                    "metric_id": metric,
                    "seed_protocol_id": "S01",
                    "task_id": f"T_{exp}",
                    "harness_id": f"H_{exp}_FULL",
                    "evidence_id": f"EV_{exp}",
                    "paper_placeholder": next(item["placeholder"] for item in DEMO_PLACEHOLDERS if item["experiment_id"] == exp),
                }
                for exp, rq, hyp, claim, metric, _purpose in experiments
            ],
            "notes": [
                "这是 placeholder-complete demo spec，用于展示 research-paper 应生成完整论文结构，而不是填空模板。",
                "未验证结果必须保留为 typed placeholder，不能使用 plausible mock numeric values。",
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "shared" / "dataset_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "datasets": [
                {
                    "dataset_id": "D01",
                    "name": "RepoRepair candidate placeholder split",
                    "data_source_type": "real_dataset",
                    "provenance": "公开 repository repair benchmark manifest；demo scaffold 需在真实项目中替换为冻结清单。",
                    "license": "【待填写：真实 benchmark license】",
                    "split_file": "data/splits/reporepair_120_frozen_v0.json",
                    "preprocessing_config": "configs/preprocess/reporepair_v0.yaml",
                    "is_mock": False,
                    "is_synthetic": False,
                    "claim_support_allowed": True,
                    "description": "候选 repository repair split；最终实验必须替换为真实冻结 benchmark manifest。",
                }
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "shared" / "metric_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "metrics": [
                {"metric_id": "task_success", "name": "task_success", "description": "issue 是否被完整解决。"},
                {"metric_id": "evidence_coverage", "name": "evidence_coverage", "description": "claim 是否有合格 artifact 支撑。"},
                {"metric_id": "invalid_claim_rate", "name": "invalid_claim_rate", "description": "无效 claim binding 占比。"},
                {"metric_id": "planner_overhead_sec", "name": "planner_overhead_sec", "description": "每个 gate 的控制平面额外开销。"},
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "shared" / "model_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "models": [
                {
                    "model_id": "M_OURS",
                    "name": "ContractGraph Agent",
                    "model_source_type": "real_code",
                    "implementation_ref": "project/contractgraph",
                    "checkpoint_or_model_version": "repo commit recorded by Git Memory Layer",
                    "config_path": "configs/experiments/contractgraph.yaml",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
                {
                    "model_id": "B01",
                    "name": "Direct Agent",
                    "model_source_type": "real_code",
                    "implementation_ref": "configs/baselines/direct_agent.yaml",
                    "checkpoint_or_model_version": "repo commit recorded by Git Memory Layer",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
                {
                    "model_id": "B02",
                    "name": "Plan-then-Code Agent",
                    "model_source_type": "real_code",
                    "implementation_ref": "configs/baselines/plan_then_code.yaml",
                    "checkpoint_or_model_version": "repo commit recorded by Git Memory Layer",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
                {
                    "model_id": "B03",
                    "name": "Reflection Agent",
                    "model_source_type": "real_code",
                    "implementation_ref": "configs/baselines/reflection_agent.yaml",
                    "checkpoint_or_model_version": "repo commit recorded by Git Memory Layer",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "shared" / "seed_protocol.yaml",
        {"schema_version": SCHEMA_VERSION, "seed_protocols": [{"seed_protocol_id": "S01", "seeds": [11, 23, 37]}]},
        force,
    )
    write_yaml(
        research_dir / "spec" / "shared" / "evidence_contract.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "claims": [
                {
                    "claim_id": claim,
                    "required_experiments": [exp],
                    "required_harnesses": [f"H_{exp}_FULL"],
                    "paper_placeholders": [
                        next(item["placeholder"] for item in DEMO_PLACEHOLDERS if item["experiment_id"] == exp)
                    ],
                }
                for exp, _rq, _hyp, claim, _metric, _purpose in experiments
            ],
            "evidence_rules": {
                "placeholder_result_policy": "未验证结果必须保持 typed placeholder，不能用 plausible mock numeric values 预填论文表格或结果段落。",
                "forbidden_as_claim_evidence": [
                    "mock_result",
                    "toy_result",
                    "smoke_test_only",
                    "synthetic_data_without_human_approved_exception",
                    "stub_model_result",
                    "proxy_model_result",
                    "cached_proxy_result",
                ],
            },
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_manifest.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "experiments": [
                {
                    "experiment_id": exp,
                    "experiment_type": "confirmatory",
                    "title": purpose,
                    "linked_rq": rq,
                    "hypothesis": hyp,
                    "claim": claim,
                    "purpose": purpose,
                    "status": "planned_with_placeholder_bindings",
                    "dataset": "D01",
                    "split_file": "data/splits/reporepair_120_frozen_v0.json",
                    "preprocessing_config": "configs/preprocess/reporepair_v0.yaml",
                    "models": ["M_OURS"],
                    "proposed_method_config": f"configs/experiments/{exp}/contractgraph.yaml",
                    "baselines": ["B01", "B02", "B03"],
                    "data_model_truth": {
                        "full_experiment_requires_real_data": True,
                        "full_experiment_requires_real_model": True,
                        "dataset_manifest_must_set_is_mock_false": True,
                        "model_manifest_must_set_is_mock_false": True,
                        "forbid_mock_toy_synthetic_stub_cached_proxy": True,
                        "mock_allowed_only_for": ["unit_test", "smoke_test", "harness_plumbing"],
                    },
                    "seeds": [11, 23, 37],
                    "metrics": [metric],
                    "statistical_protocol": "三 seed 聚合；最终 claim 需要 bootstrap confidence interval 与 independent rerun。",
                    "commands": {
                        "run": f"python -m project.experiments.run --experiment {exp} --seed {{seed}}",
                        "aggregate": f"python -m project.experiments.aggregate --experiment {exp}",
                    },
                    "required_artifacts": [
                        f"artifacts/experiments/{exp}/raw/{{seed}}/metrics.json",
                        f"artifacts/experiments/{exp}/aggregate/summary.json",
                    ],
                    "harnesses": [f"H_{exp}_FULL"],
                    "support_condition": f"{metric} 满足预注册 support rule，且 independent rerun 不改变结论方向。",
                    "falsification_condition": f"{metric} 未达到预注册阈值，或 mock / missing artifact 被检测到。",
                    "mock_policy": "full harness 必须拒绝 mock claim evidence；full experiment 必须使用真实数据和真实模型；论文未验证结果必须保留 typed placeholder。",
                }
                for exp, rq, hyp, claim, metric, purpose in experiments
            ],
            "claims": [{"claim_id": claim, "experiment_ids": [exp]} for exp, _rq, _hyp, claim, _metric, _purpose in experiments],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "tasks": [
                {
                    "task_id": f"T_{exp}",
                    "title": f"执行 {exp} 并生成 claim-bound artifact",
                    "harnesses": [f"H_{exp}_FULL"],
                    "acceptance_criteria": ["所有 seed 完成", "所有 baseline 完成", "aggregate summary 存在"],
                }
                for exp, *_rest in experiments
            ],
            "gates": [
                {"gate_id": f"G_{exp}", "tasks": [f"T_{exp}"], "harnesses": [f"H_{exp}_FULL"]} for exp, *_rest in experiments
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "harnesses": [
                {
                    "harness_id": f"H_{exp}_FULL",
                    "type": "full_experiment",
                    "linked_experiment": exp,
                    "purpose": f"验证 {exp} 的 artifact 是否可支持论文 claim。",
                    "cwd": ".",
                    "command": f"python -m project.harness verify {exp}",
                    "timeout": 7200,
                    "required_inputs": ["data/splits/reporepair_120_frozen_v0.json"],
                    "required_outputs": [
                        {"path": f"artifacts/experiments/{exp}/aggregate/summary.json", "schema": "artifact_schema"}
                    ],
                    "pass_criteria": [
                        "all_declared_seeds_completed",
                        "all_declared_baselines_completed",
                        "real_dataset_provenance_verified",
                        "real_model_provenance_verified",
                        "no_mock_data_used",
                        "no_synthetic_or_mock_inputs",
                        "full_run_not_smoke",
                        "no_missing_metric",
                        "no_test_tuning",
                        "artifact_hashes_recorded",
                    ],
                    "evidence_capture": ["stdout", "stderr", "artifact_hashes"],
                    "may_support_research_claim": True,
                    "independent_rerun_required": True,
                }
                for exp, *_rest in experiments
            ],
        },
        force,
    )
    write_yaml(
        research_dir / "spec" / "paper" / "result_binding.yaml",
        {"schema_version": SCHEMA_VERSION, "bindings": DEMO_PLACEHOLDERS, "status": "placeholder_until_execution"},
        force,
    )


def generate_demo_paper(research_dir: Path, force: bool = False) -> Path:
    write_demo_spec(research_dir, force)
    paper_dir = research_dir / "paper"
    write_text(paper_dir / "planned_paper.md", demo_paper_markdown(), force)
    paper_tex = paper_dir / "planned_paper.tex"
    write_text(paper_tex, demo_paper_tex(), force)
    write_yaml(paper_dir / "placeholder_map.yaml", {"placeholders": DEMO_PLACEHOLDERS}, force)
    write_text(
        paper_dir / "paper_gap_report.md",
        "\n".join(
            [
                "# 论文缺口报告",
                "",
                "当前论文是完整 placeholder-complete manuscript draft，不是填空模板。",
                "",
                "## 必须在投稿前替换",
                "",
                "- 表中的 typed placeholders 不能作为 empirical claim，必须等待真实 artifact 绑定。",
                "- `{{E01.OURS.task_success}}`、`{{E02.OURS.evidence_coverage}}`、`{{E03.OURS.invalid_claim_rate}}`、`{{E04.OURS.planner_overhead_sec}}` 必须由真实 artifact 绑定。",
                "- `RepoRepair candidate placeholder split` 必须替换为真实冻结 benchmark manifest。",
                "- 所有 full harness 必须通过，并完成 independent rerun。",
            ]
        )
        + "\n",
        force,
    )
    render_pdf_from_tex(paper_tex, paper_dir / "planned_paper.pdf", force)
    return paper_dir


class Validation:
    def __init__(self) -> None:
        self.issues: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.issues

    def error(self, message: str) -> None:
        self.issues.append(message)

    def require_file(self, path: Path, label: str) -> bool:
        if not path.exists():
            self.error(f"missing {label}: {path.as_posix()}")
            return False
        return True


def non_placeholder_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
        and "【待填写" not in line
        and not line.strip().startswith(">")
        and "TODO" not in line
    ]


def markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+\d*\.?\s*{re.escape(heading)}.*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_match = re.search(r"^##\s+", text[match.end() :], re.MULTILINE)
    if not next_match:
        return text[match.end() :]
    return text[match.end() : match.end() + next_match.start()]


def markdown_status_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*-?\s*{re.escape(key)}\s*:\s*`?([^`\n]+)`?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def current_epoch_name(research_dir: Path) -> str:
    current = research_dir / "CURRENT"
    return read_text(current).strip() if current.exists() else ""


def current_epoch_dir(research_dir: Path) -> Path:
    return research_dir / current_epoch_name(research_dir)


def version_sort_key(path: Path) -> int:
    match = re.fullmatch(r"V(\d+)", path.name)
    return int(match.group(1)) if match else -1


def epoch_versions(research_dir: Path) -> list[Path]:
    return sorted(
        [path for path in research_dir.iterdir() if path.is_dir() and re.fullmatch(r"V\d+", path.name)]
        if research_dir.exists()
        else [],
        key=version_sort_key,
    )


def direction_path_from_epoch(epoch_dir: Path, status: dict[str, Any]) -> Path:
    ref = str(status.get("direction_ref") or "../RESEARCH_DIRECTION.md")
    return (epoch_dir / ref).resolve()



def task_changes_code(task: dict[str, Any]) -> bool:
    if task.get("code_change") is True:
        return True
    phase = str(task.get("phase", "")).strip()
    if phase in {"implementation", "experiment", "evaluation"}:
        return True
    files = " ".join(str(item) for item in as_list(task.get("allowed_files")))
    return bool(re.search(r"\b(src|app|apps|packages|tests|scripts)/", files))


@dataclass
class EpochSchemaIssue:
    path: str
    message: str
    severity: str = "FAIL"


@dataclass
class AuditCheckResult:
    check_id: str
    status: str
    severity: str
    message: str
    paths: list[str]


@dataclass
class StaleFinding:
    code: str
    source_path: str
    dependent_path: str
    expected_hash: str | None
    actual_hash: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frontmatter_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    text = read_text(path)
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    payload = yaml.safe_load(parts[1])
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    return str(value) if value is not None else None


def _hash_from_yaml(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    value = load_yaml(path).get(key)
    return str(value) if value is not None else None


def _append_stale_if_needed(
    findings: list[StaleFinding],
    code: str,
    source: Path,
    dependent: Path,
    expected_hash: str | None,
) -> None:
    if not expected_hash or not source.exists() or not dependent.exists():
        return
    actual = sha256_file(source)
    if expected_hash != actual:
        findings.append(
            StaleFinding(
                code=code,
                source_path=source.name,
                dependent_path=dependent.name,
                expected_hash=expected_hash,
                actual_hash=actual,
            )
        )


def detect_epoch_stale_hashes(epoch_dir: Path) -> list[StaleFinding]:
    findings: list[StaleFinding] = []
    prd = epoch_prd_source_path(epoch_dir)
    spine = epoch_dir / "RESEARCH_SPINE.yaml"
    spec = epoch_dir / "SPEC.yaml"
    plan = epoch_dir / "PLAN.md"
    queue = epoch_dir / "TASK_QUEUE.yaml"
    _append_stale_if_needed(findings, "SPINE_STALE", prd, spine, _hash_from_yaml(spine, "source_prd_hash"))
    _append_stale_if_needed(findings, "SPEC_STALE", prd, spec, _hash_from_yaml(spec, "source_prd_hash"))
    _append_stale_if_needed(findings, "PLAN_STALE", spec, plan, _frontmatter_value(plan, "source_spec_hash"))
    _append_stale_if_needed(findings, "TASK_QUEUE_STALE", plan, queue, _hash_from_yaml(queue, "source_plan_hash"))
    return findings



def audit_pass(check_id: str, message: str, paths: list[str] | None = None) -> AuditCheckResult:
    return AuditCheckResult(check_id, "PASS", "P2", message, paths or [])


def audit_fail(check_id: str, message: str, paths: list[str] | None = None, severity: str = "P0") -> AuditCheckResult:
    return AuditCheckResult(check_id, "FAIL", severity, message, paths or [])


def audit_results_payload(results: list[AuditCheckResult]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "checks": [asdict(result) for result in results]}


def has_blocking_audit_failures(results: list[AuditCheckResult]) -> bool:
    return any(result.status == "FAIL" and result.severity in {"P0", "P1"} for result in results)


def completed_tasks(epoch_dir: Path) -> list[dict[str, Any]]:
    queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    return [task for task in tasks if str(task.get("status")) in {"done", "completed"}]


def check_gate_evidence_completeness(epoch_dir: Path) -> list[AuditCheckResult]:
    results: list[AuditCheckResult] = []
    for task in completed_tasks(epoch_dir):
        task_id = str(task.get("task_id") or task.get("id") or "")
        if not task_id:
            continue
        report_path = epoch_dir / "runs" / f"{task_id}_report.yaml"
        report_label = f"{epoch_dir.name}/runs/{task_id}_report.yaml"
        if not report_path.exists():
            results.append(audit_fail("missing_run_report", f"completed task {task_id} has no run report", [report_label]))
            continue
        report = load_yaml(report_path)
        execution = report.get("execution", {}) if isinstance(report.get("execution"), dict) else {}
        command = report.get("command", {}) if isinstance(report.get("command"), dict) else {}
        exit_code = execution.get("exit_code", command.get("exit_code"))
        if exit_code is None:
            results.append(audit_fail("missing_exit_code", f"completed task {task_id} run report has no exit_code", [report_label]))
    return results


def _report_is_mock_backed(report: dict[str, Any]) -> bool:
    anti_mock = report.get("anti_mock", {}) if isinstance(report.get("anti_mock"), dict) else {}
    dataset_type = str(anti_mock.get("dataset_type") or "").lower()
    if dataset_type in MOCK_SOURCE_TYPES:
        return True
    conclusion = report.get("conclusion", {}) if isinstance(report.get("conclusion"), dict) else {}
    return conclusion.get("research_interpretation_allowed") is False


def reproduction_items_by_id(epoch_dir: Path) -> dict[str, dict[str, Any]]:
    index = load_yaml(epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml")
    items: dict[str, dict[str, Any]] = {}
    for item in as_list(index.get("items")):
        if not isinstance(item, dict):
            continue
        repro_id = str(item.get("repro_id") or item.get("id") or "")
        if repro_id:
            items[repro_id] = item
    return items


def _claim_reproduction_refs(claim: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for field in ("current_evidence", "required_evidence"):
        payload = claim.get(field) if isinstance(claim.get(field), dict) else {}
        refs.extend(str(item) for item in as_list(payload.get("reproductions")) if str(item))
    return list(dict.fromkeys(refs))


def check_reproduction_claim_boundaries(epoch_dir: Path) -> list[AuditCheckResult]:
    ledger = load_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml")
    reproduction_items = reproduction_items_by_id(epoch_dir)
    findings: list[AuditCheckResult] = []
    unsupported_levels = {"literature_only", "official_smoke_only", "failed_but_informative"}
    for claim in as_list(ledger.get("claims")):
        if not isinstance(claim, dict) or str(claim.get("status")) != "allowed":
            continue
        claim_id = str(claim.get("claim_id") or "<missing>")
        for repro_id in _claim_reproduction_refs(claim):
            item = reproduction_items.get(repro_id)
            if item is None:
                findings.append(
                    audit_fail(
                        "missing_reproduction_claim_evidence",
                        f"allowed claim {claim_id} references missing reproduction evidence {repro_id}",
                        [f"{epoch_dir.name}/reproduction/REPRODUCTION_INDEX.yaml"],
                    )
                )
                continue
            evidence_level = str(item.get("evidence_level") or "")
            claim_support = str(item.get("claim_support_level") or "")
            audit_status = str(item.get("audit_status") or "")
            if evidence_level in unsupported_levels or claim_support in {"sanity_only", "none"}:
                findings.append(
                    audit_fail(
                        "unsupported_reproduction_claim_evidence",
                        f"allowed claim {claim_id} uses unsupported reproduction evidence {repro_id}",
                        [f"{epoch_dir.name}/reproduction/REPRODUCTION_INDEX.yaml"],
                    )
                )
            if audit_status != "passed":
                findings.append(
                    audit_fail(
                        "reproduction_audit_not_passed",
                        f"allowed claim {claim_id} uses reproduction evidence {repro_id} without passed audit",
                        [f"{epoch_dir.name}/reproduction/REPRODUCTION_INDEX.yaml"],
                    )
                )
            if claim_support == "partial":
                findings.append(
                    audit_fail(
                        "partial_reproduction_claim_support",
                        f"allowed claim {claim_id} uses partial reproduction evidence {repro_id}; mark claim as partial or keep placeholder",
                        [f"{epoch_dir.name}/reproduction/REPRODUCTION_INDEX.yaml"],
                        severity="P1",
                    )
                )
    return findings


def check_paper_claim_ledger(epoch_dir: Path) -> list[AuditCheckResult]:
    ledger = load_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml")
    findings: list[AuditCheckResult] = []
    for claim in as_list(ledger.get("claims")):
        if not isinstance(claim, dict) or str(claim.get("status")) != "allowed":
            continue
        evidence = claim.get("current_evidence", {}) if isinstance(claim.get("current_evidence"), dict) else {}
        for report_ref in as_list(evidence.get("run_reports")):
            report_path = epoch_dir / str(report_ref)
            report = load_yaml(report_path)
            if _report_is_mock_backed(report):
                findings.append(
                    audit_fail(
                        "mock_evidence_supports_paper_claim",
                        f"allowed claim {claim.get('claim_id')} uses mock or interpretation-forbidden evidence",
                        [f"{epoch_dir.name}/{report_ref}"],
                    )
                )
    findings.extend(check_reproduction_claim_boundaries(epoch_dir))
    return findings


def run_evidence_audit_checks(research_dir: Path) -> list[AuditCheckResult]:
    results: list[AuditCheckResult] = []
    epoch_dir = current_epoch_dir(research_dir)
    tasks = completed_tasks(epoch_dir)
    if not tasks:
        ledger_findings = check_paper_claim_ledger(epoch_dir)
        return ledger_findings or [audit_pass("evidence.no_completed_tasks", "No completed tasks require evidence checks yet.", [epoch_dir.name])]
    for task in tasks:
        task_id = str(task.get("task_id") or task.get("id") or "")
        report_path = epoch_dir / "runs" / f"{task_id}_report.yaml"
        report_label = f"{epoch_dir.name}/runs/{task_id}_report.yaml"
        if not report_path.exists():
            results.append(audit_fail("evidence.done_task_has_run_report", f"completed task {task_id} has no run report", [report_label]))
            continue
        report = load_yaml(report_path)
        report_status = report.get("task", {}).get("status") if isinstance(report.get("task"), dict) else None
        if not isinstance(report, dict) or str(report_status) not in {"done", "completed"}:
            results.append(audit_fail("evidence.done_task_has_run_report", f"completed task {task_id} has no done-status run report", [report_label]))
            continue
        execution = report.get("execution", {}) if isinstance(report.get("execution"), dict) else {}
        evidence = report.get("evidence", {}) if isinstance(report.get("evidence"), dict) else {}
        if execution.get("exit_code") is None:
            results.append(audit_fail("evidence.done_task_has_exit_code", f"completed task {task_id} run report has no exit_code", [report_label]))
        if not as_list(execution.get("commands_run")):
            results.append(audit_fail("evidence.done_task_has_commands", f"completed task {task_id} run report has no commands_run", [report_label]))
        artifacts = [artifact for artifact in as_list(evidence.get("artifacts")) if isinstance(artifact, dict)]
        if not any(artifact.get("path") and artifact.get("sha256") for artifact in artifacts):
            results.append(audit_fail("evidence.done_task_has_artifact_hash", f"completed task {task_id} run report has no artifact sha256", [report_label]))
    if not results:
        results.append(audit_pass("evidence.completed_tasks_have_structured_reports", "Completed tasks have structured run reports."))
    results.extend(check_paper_claim_ledger(epoch_dir))
    return results


def run_paper_binding_audit_checks(research_dir: Path) -> list[AuditCheckResult]:
    validation = validate_paper_binding_ready(research_dir)
    if validation.ok:
        return [audit_pass("paper_binding.ready", "Paper binding evidence checks passed.")]
    return [
        audit_fail("paper_binding.ready", issue, [current_epoch_dir(research_dir).name], severity="P0")
        for issue in validation.issues
    ]


def run_epoch_audit_checks(research_dir: Path, mode: str = "full") -> list[AuditCheckResult]:
    results: list[AuditCheckResult] = []
    if mode in {"full", "epoch", "format"}:
        schema_issues = validate_epoch_schema(research_dir, strict=True)
        if schema_issues:
            results.extend(
                audit_fail("epoch.schema_invariance", issue.message, [issue.path], severity="P0")
                for issue in schema_issues
            )
        else:
            results.append(audit_pass("epoch.schema_invariance", "All epoch directories match the epoch manifest."))
    if mode in {"full", "format"}:
        format_validation = validate_format_ready(research_dir)
        for issue in format_validation.issues:
            results.append(audit_fail("format." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P1"))
        direction_validation = validate_direction_ready(research_dir)
        for issue in direction_validation.issues:
            results.append(audit_fail("direction." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P0"))
        spine_validation = validate_spine(research_dir)
        for issue in spine_validation.issues:
            results.append(audit_fail("spine." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P0"))
        loop_prompt_validation = validate_loop_prompt_ready(research_dir)
        for issue in loop_prompt_validation.issues:
            results.append(audit_fail("loop_prompt." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P1"))
        contract_validation = validate_agent_contracts(research_dir)
        for issue in contract_validation.issues:
            results.append(audit_fail("format.contract." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P1"))
        if not any(
            r.status == "FAIL" and r.check_id.startswith(("format.", "direction.", "spine.", "loop_prompt."))
            for r in results
        ) and contract_validation.ok:
            results.append(audit_pass("format.compliance", "Format, direction, spine, loop-prompt, and agent contract checks passed."))
    if mode == "git":
        git_validation = validate_git_ready(research_dir)
        for issue in git_validation.issues:
            results.append(audit_fail("git." + issue.replace(" ", "_")[:50], issue, [research_dir.name], severity="P1"))
        if not any(r.status == "FAIL" and r.check_id.startswith("git.") for r in results):
            results.append(audit_pass("git.compliance", "Git state and commit policy checks passed."))
    if mode in {"full", "evidence"}:
        results.extend(run_evidence_audit_checks(research_dir))
    if mode == "paper-binding":
        results.extend(run_paper_binding_audit_checks(research_dir))
    return results


def write_audit_results_yaml(path: Path, results: list[AuditCheckResult]) -> None:
    write_yaml(path, audit_results_payload(results), force=True)


def validate_epoch_yaml_fields(epoch_dir: Path, manifest: dict[str, Any]) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    required = manifest.get("yaml_required_fields", {})
    if not isinstance(required, dict):
        return [EpochSchemaIssue(epoch_dir.name, "epoch manifest yaml_required_fields must be a mapping")]
    version = epoch_dir.name
    for filename, fields in required.items():
        path = epoch_dir / str(filename)
        label = f"{version}/{filename}"
        if not path.exists():
            continue
        payload = load_yaml(path)
        if not isinstance(payload, dict):
            issues.append(EpochSchemaIssue(label, f"{label} must be a YAML mapping"))
            continue
        if not isinstance(fields, list):
            issues.append(EpochSchemaIssue(label, f"manifest fields for {filename} must be a list"))
            continue
        for field in fields:
            if str(field) not in payload:
                issues.append(EpochSchemaIssue(label, f"{label} missing required field: {field}"))
        if "version" in fields and payload.get("version") != version:
            issues.append(EpochSchemaIssue(label, f"{label} version {payload.get('version')} does not match epoch {version}"))
    return issues


def validate_epoch_wiki_set(epoch_dir: Path, manifest: dict[str, Any], strict: bool = True) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    version = epoch_dir.name
    wiki_dir = epoch_dir / "wiki"
    required = set(epoch_manifest_list("required_wiki_files", manifest))
    for filename in sorted(required):
        path = wiki_dir / filename
        if not path.exists():
            issues.append(EpochSchemaIssue(f"{version}/wiki/{filename}", f"missing {version}/wiki/{filename}: {path.as_posix()}"))
    if strict and wiki_dir.exists():
        for path in sorted(wiki_dir.glob("*.md")):
            if path.name not in required:
                rel = f"{version}/wiki/{path.name}"
                issues.append(EpochSchemaIssue(rel, f"unexpected epoch wiki file: {rel}"))
    return issues


def validate_epoch_search_reproduction_files(epoch_dir: Path, manifest: dict[str, Any]) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    version = epoch_dir.name
    for filename in epoch_manifest_list("required_search_files", manifest):
        path = epoch_dir / "search" / filename
        if not path.exists():
            issues.append(EpochSchemaIssue(f"{version}/search/{filename}", f"missing {version}/search/{filename}: {path.as_posix()}"))
    for filename in epoch_manifest_list("required_reproduction_files", manifest):
        path = epoch_dir / "reproduction" / filename
        if not path.exists():
            issues.append(EpochSchemaIssue(f"{version}/reproduction/{filename}", f"missing {version}/reproduction/{filename}: {path.as_posix()}"))
    return issues


def validate_reproduction_index_shape(index: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    items = as_list(index.get("items"))
    for item in items:
        if not isinstance(item, dict):
            issues.append("reproduction item must be a mapping")
            continue
        repro_id = str(item.get("repro_id") or item.get("id") or "<missing>")
        reproduction_type = str(item.get("reproduction_type") or "")
        if reproduction_type and reproduction_type not in REPRODUCTION_TYPES:
            issues.append(f"invalid reproduction_type for {repro_id}: {reproduction_type}")
        status = str(item.get("status") or "")
        if status and status not in REPRODUCTION_STATUSES:
            issues.append(f"invalid reproduction status for {repro_id}: {status}")
        evidence_level = str(item.get("evidence_level") or "")
        if evidence_level and evidence_level not in REPRODUCTION_EVIDENCE_LEVELS:
            issues.append(f"invalid evidence_level for {repro_id}: {evidence_level}")
    return issues


def validate_epoch_search_reproduction_shape(epoch_dir: Path) -> list[str]:
    issues: list[str] = []
    index_path = epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml"
    if index_path.exists():
        issues.extend(validate_reproduction_index_shape(load_yaml(index_path)))
    return issues


RQ_REQUIRED_FILES = ["RQ.md", "SPEC.yaml", "PLAN.md", "TASKS.yaml"]
RQ_REQUIRED_REPRODUCTION_FILES = [
    "SOURCE_LOCK.yaml",
    "REPRODUCTION_SPEC.yaml",
    "VERIFICATION.yaml",
    "IMMUTABLE_BASE.yaml",
]
RQ_TASK_REQUIRED_FIELDS = [
    "task_id",
    "phase",
    "status",
    "preconditions",
    "commands",
    "expected_artifacts",
    "pass_criteria",
    "blocker_criteria",
    "evidence_level_on_pass",
]


def validate_rq_task_shape(rq_id: str, tasks_doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not isinstance(tasks_doc.get("tasks"), list):
        return [f"{rq_id}/TASKS.yaml missing tasks list"]
    for task in as_list(tasks_doc.get("tasks")):
        if not isinstance(task, dict):
            issues.append(f"{rq_id}/TASKS.yaml task must be a mapping")
            continue
        task_id = str(task.get("task_id") or "<missing>")
        for field in RQ_TASK_REQUIRED_FIELDS:
            if field not in task:
                issues.append(f"{rq_id}/TASKS.yaml task {task_id} missing required field: {field}")
    return issues


def validate_rq_contracts(epoch_dir: Path, spine: dict[str, Any]) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    version = epoch_dir.name
    rqs_root = epoch_dir / "rqs"
    if not rqs_root.is_dir():
        return [EpochSchemaIssue(f"{version}/rqs", f"missing {version}/rqs: {rqs_root.as_posix()}")]

    declared = [
        str(rq.get("id"))
        for rq in as_list(spine.get("research_questions"))
        if isinstance(rq, dict) and rq.get("id")
    ]
    if not declared and (rqs_root / "RQ01").exists():
        declared = ["RQ01"]

    for rq_id in declared:
        rq_dir = rqs_root / rq_id
        if not rq_dir.is_dir():
            issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}", f"missing {version}/rqs/{rq_id}: {rq_dir.as_posix()}"))
            continue
        for filename in RQ_REQUIRED_FILES:
            path = rq_dir / filename
            if not path.exists():
                issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/{filename}", f"missing {version}/rqs/{rq_id}/{filename}: {path.as_posix()}"))
        for filename in RQ_REQUIRED_REPRODUCTION_FILES:
            path = rq_dir / "reproduction" / filename
            if not path.exists():
                issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/reproduction/{filename}", f"missing {version}/rqs/{rq_id}/reproduction/{filename}: {path.as_posix()}"))

        spec_path = rq_dir / "SPEC.yaml"
        if spec_path.exists():
            spec = load_yaml(spec_path)
            if spec.get("version") != version:
                issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/SPEC.yaml", f"{version}/rqs/{rq_id}/SPEC.yaml version {spec.get('version')} does not match epoch {version}"))
            if spec.get("rq_id") != rq_id:
                issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/SPEC.yaml", f"{version}/rqs/{rq_id}/SPEC.yaml rq_id {spec.get('rq_id')} does not match directory {rq_id}"))
            for field in ["research_question", "claim_contract", "reproduction_contract", "experiment_contract", "evidence_contract", "failure_taxonomy"]:
                if field not in spec:
                    issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/SPEC.yaml", f"{version}/rqs/{rq_id}/SPEC.yaml missing required field: {field}"))

        tasks_path = rq_dir / "TASKS.yaml"
        if tasks_path.exists():
            tasks_doc = load_yaml(tasks_path)
            for issue in validate_rq_task_shape(rq_id, tasks_doc):
                issues.append(EpochSchemaIssue(f"{version}/rqs/{rq_id}/TASKS.yaml", f"{version}/rqs/{issue}"))
    return issues


def _rq_task_by_ref(epoch_dir: Path, ref: str) -> dict[str, Any] | None:
    if "#" not in ref:
        return None
    rel_path, task_id = ref.split("#", 1)
    task_path = epoch_dir / rel_path
    if not task_path.exists():
        return None
    payload = load_yaml(task_path)
    for task in as_list(payload.get("tasks")):
        if isinstance(task, dict) and str(task.get("task_id") or "") == task_id:
            return task
    return None


def validate_global_task_rq_refs(epoch_dir: Path, queue: dict[str, Any]) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    version = epoch_dir.name
    for task in [item for item in as_list(queue.get("tasks")) if isinstance(item, dict)]:
        task_id = _task_identifier(task) or "<missing>"
        binding = task.get("research_binding") if isinstance(task.get("research_binding"), dict) else {}
        if binding.get("mode") == "direction_bootstrap":
            continue
        for field in ["rq_id", "rq_spec_ref", "rq_task_ref"]:
            if not task.get(field):
                issues.append(EpochSchemaIssue(f"{version}/TASK_QUEUE.yaml", f"{version}/task {task_id} missing {field}"))
        rq_spec_ref = str(task.get("rq_spec_ref") or "")
        if rq_spec_ref and not (epoch_dir / rq_spec_ref).exists():
            issues.append(EpochSchemaIssue(f"{version}/TASK_QUEUE.yaml", f"{version}/task {task_id} rq_spec_ref does not exist: {rq_spec_ref}"))
        rq_task_ref = str(task.get("rq_task_ref") or "")
        if rq_task_ref:
            rq_task = _rq_task_by_ref(epoch_dir, rq_task_ref)
            if rq_task is None:
                issues.append(EpochSchemaIssue(f"{version}/TASK_QUEUE.yaml", f"{version}/task {task_id} rq_task_ref does not resolve: {rq_task_ref}"))
            elif str(rq_task.get("phase") or "") != str(task.get("phase") or ""):
                issues.append(
                    EpochSchemaIssue(
                        f"{version}/TASK_QUEUE.yaml",
                        f"{version}/task {task_id} phase {task.get('phase')} does not match rq_task_ref phase {rq_task.get('phase')}",
                    )
                )
    return issues


def rq_reproduction_status(epoch_dir: Path, rq_id: str) -> str:
    verification = epoch_dir / "rqs" / rq_id / "reproduction" / "VERIFICATION.yaml"
    if not verification.exists():
        return "missing"
    payload = load_yaml(verification)
    return str(payload.get("status") or "")


def validate_epoch_schema(research_dir: Path, strict: bool = True) -> list[EpochSchemaIssue]:
    issues: list[EpochSchemaIssue] = []
    manifest = load_epoch_manifest()
    required_files = epoch_manifest_list("required_files", manifest)
    required_dirs = epoch_manifest_list("required_dirs", manifest)
    for epoch_dir in epoch_versions(research_dir):
        version = epoch_dir.name
        for filename in required_files:
            path = epoch_dir / filename
            if not path.exists():
                issues.append(EpochSchemaIssue(f"{version}/{filename}", f"missing {version}/{filename}: {path.as_posix()}"))
        for dirname in required_dirs:
            path = epoch_dir / dirname
            if not path.is_dir():
                issues.append(EpochSchemaIssue(f"{version}/{dirname}", f"missing {version}/{dirname}: {path.as_posix()}"))
        issues.extend(validate_epoch_yaml_fields(epoch_dir, manifest))
        queue_path = epoch_dir / "TASK_QUEUE.yaml"
        if queue_path.exists():
            queue = load_yaml(queue_path)
            for issue in validate_gate_queue_shape(queue):
                issues.append(EpochSchemaIssue(f"{version}/TASK_QUEUE.yaml", f"{version}/{issue}"))
            spine = load_yaml(epoch_dir / "RESEARCH_SPINE.yaml")
            for issue in validate_task_research_binding(epoch_dir, queue, spine):
                issues.append(EpochSchemaIssue(f"{version}/TASK_QUEUE.yaml", f"{version}/{issue}"))
            issues.extend(validate_global_task_rq_refs(epoch_dir, queue))
            issues.extend(validate_rq_contracts(epoch_dir, spine))
        issues.extend(validate_epoch_search_reproduction_files(epoch_dir, manifest))
        for issue in validate_epoch_search_reproduction_shape(epoch_dir):
            issues.append(EpochSchemaIssue(f"{version}/reproduction/REPRODUCTION_INDEX.yaml", f"{version}/{issue}"))
        issues.extend(validate_epoch_wiki_set(epoch_dir, manifest, strict=strict))
    return issues


def markdown_has_real_value(text: str, label: str) -> bool:
    value = markdown_status_value(text, label)
    return bool(value and "【待填写" not in value and value.lower() not in {"none", "null", "false"})


RESEARCH_DIRECTION_REQUIRED_SECTIONS = [
    "Direction Status",
    "Research Seed",
    "Research Corridor",
    "Out-of-Scope Directions",
    "Prior Work Basis",
    "Desired Paper Shape",
    "Autonomy Boundary",
    "Global Stop Conditions",
]

RESEARCH_DIRECTION_STATUS_FIELDS = [
    "direction_id",
    "status",
    "created_at",
    "updated_at",
    "current_version",
    "final_target",
    "owner_decision_required",
]


def validate_direction_ready(research_dir: Path) -> Validation:
    validation = Validation()
    path = research_dir / "RESEARCH_DIRECTION.md"
    if not validation.require_file(path, "RESEARCH_DIRECTION.md"):
        return validation
    text = read_text(path)
    for section in RESEARCH_DIRECTION_REQUIRED_SECTIONS:
        if not markdown_section(text, section):
            validation.error(f"RESEARCH_DIRECTION.md missing section: {section}")
    for field in RESEARCH_DIRECTION_STATUS_FIELDS:
        if not markdown_status_value(text, field):
            validation.error(f"RESEARCH_DIRECTION.md Direction Status missing field: {field}")
    status = markdown_status_value(text, "status")
    if status not in {"human_approved", "frozen"}:
        validation.error("RESEARCH_DIRECTION.md status must be human_approved or frozen")
    corridor = markdown_section(text, "Research Corridor")
    out_of_scope = markdown_section(text, "Out-of-Scope Directions")
    autonomy = markdown_section(text, "Autonomy Boundary")
    stop_conditions = markdown_section(text, "Global Stop Conditions")
    if len([line for line in non_placeholder_lines(corridor) if line.startswith("-")]) == 0:
        validation.error("Research Corridor must contain at least one concrete allowed direction")
    if len([line for line in non_placeholder_lines(out_of_scope) if line.startswith("-")]) == 0:
        validation.error("Out-of-Scope Directions must contain at least one concrete forbidden direction")
    if "AI 可以自动做" not in autonomy or "AI 不可以自动做" not in autonomy:
        validation.error("Autonomy Boundary must define what AI can and cannot do")
    if len([line for line in non_placeholder_lines(stop_conditions) if line.startswith("-")]) == 0:
        validation.error("Global Stop Conditions must contain concrete stop conditions")
    return validation


def validate_epoch_ready(research_dir: Path) -> Validation:
    validation = Validation()
    current_path = research_dir / "CURRENT"
    if not validation.require_file(current_path, "CURRENT"):
        return validation
    version = current_epoch_name(research_dir)
    if not version:
        validation.error("CURRENT is empty")
        return validation
    epoch_dir = research_dir / version
    if not epoch_dir.exists():
        validation.error(f"missing current epoch directory: {epoch_dir.as_posix()}")
        return validation
    for issue in validate_epoch_schema(research_dir, strict=True):
        validation.error(issue.message)
    for name in EPOCH_REQUIRED_FILES:
        validation.require_file(epoch_dir / name, f"{version}/{name}")
    status = load_yaml(epoch_dir / "STATUS.yaml")
    if status.get("version") != version:
        validation.error(f"STATUS.yaml version {status.get('version')} does not match CURRENT {version}")
    direction_ref = direction_path_from_epoch(epoch_dir, status)
    if not direction_ref.exists():
        validation.error(f"direction_ref does not exist: {direction_ref.as_posix()}")
    current_status = str(status.get("status", "")).strip()
    later_versions = [path.name for path in epoch_versions(research_dir) if version_sort_key(path) > version_sort_key(epoch_dir)]
    if later_versions and current_status not in CLOSED_VERSION_STATUSES and current_status != "paper_binding_ready":
        validation.error("cannot create next version before current epoch has closed_* status")
    out_of_scope_section = markdown_section(read_text(direction_ref), "Out-of-Scope Directions") if direction_ref.exists() else ""
    forbidden_terms = [
        re.sub(r"^[`'\"]|[`'\"]$", "", line.lstrip("- ").strip())
        for line in non_placeholder_lines(out_of_scope_section)
        if line.startswith("-")
    ]
    current_text = "\n".join(
        read_text(path)
        for path in [epoch_prd_source_path(epoch_dir), epoch_dir / "PLAN.md"]
        if path.exists()
    )
    for term in forbidden_terms:
        if term and term in current_text and "out-of-scope" not in current_text.lower():
            validation.error(f"current epoch may cross Research Direction out-of-scope term: {term}")
    return validation


def validate_loop_ready(research_dir: Path) -> Validation:
    validation = validate_epoch_ready(research_dir)
    if not validation.ok:
        return validation
    epoch_dir = current_epoch_dir(research_dir)
    queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
    tasks = [task for task in as_list(queue.get("tasks")) if isinstance(task, dict)]
    active = [task for task in tasks if str(task.get("status")) == "active"]
    if len(active) != 1:
        validation.error("TASK_QUEUE.yaml must have exactly one active task")
        return validation
    active_task = active[0]
    if not as_list(active_task.get("success_criteria")):
        validation.error(f"active task {active_task.get('id')} has no success_criteria")
    if not as_list(active_task.get("allowed_files")):
        validation.error(f"active task {active_task.get('id')} has no allowed_files")
    if "forbidden_files" not in active_task:
        validation.error(f"active task {active_task.get('id')} has no forbidden_files")
    if task_changes_code(active_task) and not as_list(active_task.get("test_commands")):
        validation.error(f"code-changing active task {active_task.get('id')} must define test_commands")
    for issue in validate_active_task_research_binding(active_task):
        validation.error(issue)
    phase = str(active_task.get("phase") or "")
    if phase in {"implementation", "experiment", "analysis", "result_analysis", "evaluation"}:
        binding = active_task.get("research_binding") if isinstance(active_task.get("research_binding"), dict) else {}
        rq_id = str(active_task.get("rq_id") or binding.get("rq_id") or "")
        if rq_id:
            status = rq_reproduction_status(epoch_dir, rq_id)
            if status != "verified":
                validation.error(f"active task {active_task.get('id')} requires verified reproduction for {rq_id}; current status: {status}")
    return validation


def closeout_final_status(text: str) -> str:
    match = re.search(r"final_status\s*:\s*`?([^`\n]+)`?", text)
    return match.group(1).strip() if match else ""


def closeout_create_next_version(text: str) -> bool:
    match = re.search(r"create_next_version\s*:\s*(true|false)", text, flags=re.IGNORECASE)
    return bool(match and match.group(1).lower() == "true")


def validate_closeout_ready(research_dir: Path) -> Validation:
    validation = validate_epoch_ready(research_dir)
    if not validation.ok:
        return validation
    epoch_dir = current_epoch_dir(research_dir)
    wiki_dir = epoch_dir / "wiki"
    for name in EPOCH_WIKI_FILES:
        path = wiki_dir / name
        if validation.require_file(path, f"wiki/{name}") and not read_text(path).strip():
            validation.error(f"wiki/{name} is empty")
    for name in ["positive_signals.md", "negative_results.md", "failed_paths.md"]:
        text = read_text(wiki_dir / name) if (wiki_dir / name).exists() else ""
        if "NONE" not in text and "明确无" not in text and not re.search(r"-\s+(signal_id|result_id|failed_path)\s*:", text):
            validation.error(f"wiki/{name} must contain a structured entry or an explicit none statement")
    closeout = epoch_dir / "closeout.md"
    if not validation.require_file(closeout, "closeout.md"):
        return validation
    text = read_text(closeout)
    final_status = closeout_final_status(text)
    if final_status not in CLOSED_VERSION_STATUSES:
        validation.error("closeout.md final_status must be an allowed closed status")
    required_labels = ["close_reason", "closed_at", "next_version_type"]
    for label in required_labels:
        if not markdown_has_real_value(text, label):
            validation.error(f"closeout.md missing concrete {label}")
    if closeout_create_next_version(text):
        if not markdown_has_real_value(text, "next_core_question"):
            validation.error("create_next_version=true requires next_core_question")
        if not markdown_has_real_value(text, "next_minimal_experiments"):
            validation.error("create_next_version=true requires next_minimal_experiments")
    return validation


def allowed_claim_blocks(text: str) -> list[str]:
    section = re.search(r"## Allowed Claims(?P<body>.*?)(?:^## |\Z)", text, flags=re.MULTILINE | re.DOTALL)
    if not section:
        return []
    body = section.group("body")
    blocks = re.split(r"\n(?=-\s+claim_id\s*:)", body)
    return [block.strip() for block in blocks if "claim_id" in block]


def current_has_carry_forward(research_dir: Path, old_version: str, artifact_path: str) -> bool:
    epoch_dir = current_epoch_dir(research_dir)
    haystack = ""
    for path in [epoch_prd_source_path(epoch_dir), epoch_dir / "SPEC.yaml"]:
        if path.exists():
            haystack += "\n" + read_text(path)
    if "carry_forward" not in haystack:
        return False
    if artifact_path in haystack:
        return True
    return bool(re.search(rf"(from_version|source_version|from)\s*:\s*`?{re.escape(old_version)}`?", haystack))


def validate_paper_binding_ready(research_dir: Path) -> Validation:
    validation = validate_epoch_ready(research_dir)
    if not validation.ok:
        return validation
    epoch_dir = current_epoch_dir(research_dir)
    version = epoch_dir.name
    status = load_yaml(epoch_dir / "STATUS.yaml")
    if str(status.get("status")) not in PAPER_BINDING_STATUSES:
        validation.error("STATUS.yaml status must be closed_stable or paper_binding_ready")
    decision = epoch_dir / "PAPER_BINDING_DECISION.md"
    if not validation.require_file(decision, "PAPER_BINDING_DECISION.md"):
        return validation
    text = read_text(decision)
    if "paper_binding_ready: true" not in text:
        validation.error("PAPER_BINDING_DECISION.md must set paper_binding_ready: true")
    blocks = allowed_claim_blocks(text)
    if not blocks:
        validation.error("Allowed Claims must contain at least one claim_id")
    for block in blocks:
        claim_match = re.search(r"claim_id\s*:\s*`?([^`\n]+)`?", block)
        claim_id = claim_match.group(1).strip() if claim_match else "<missing>"
        for field in [
            "experiment_id",
            "run_id",
            "artifact_path",
            "metric",
            "baseline",
            "seed_protocol",
            "audit_status",
            "real_data_check",
            "real_model_check",
            "non_smoke_full_run",
        ]:
            if not re.search(rf"{field}\s*:\s*`?([^`\n]+)`?", block):
                validation.error(f"allowed claim {claim_id} missing evidence field {field}")
        if re.search(r"prompt_only_scaffold", block, flags=re.IGNORECASE):
            validation.error(f"allowed claim {claim_id} uses prompt_only_scaffold as result evidence")
        if re.search(r"exploratory(?:-only)?", block, flags=re.IGNORECASE) and not re.search(r"evidence_level\s*:\s*`?(paper_admissible|confirmatory|reproduced)", block):
            validation.error(f"allowed claim {claim_id} uses exploratory-only evidence as main result")
        artifact_match = re.search(r"artifact_path\s*:\s*`?([^`\n]+)`?", block)
        artifact_path = artifact_match.group(1).strip() if artifact_match else ""
        old_match = re.search(r"(?:docs/research/|\.\./)?(V\d+)/", artifact_path)
        if old_match and old_match.group(1) != version and not current_has_carry_forward(research_dir, old_match.group(1), artifact_path):
            validation.error(f"allowed claim {claim_id} uses old-version artifact without explicit carry_forward: {artifact_path}")
    return validation


def template_version_ok(path: Path) -> bool:
    if not path.exists():
        return False
    if path.suffix in {".yaml", ".yml"}:
        return load_yaml(path).get("template_version") == TEMPLATE_VERSION
    return f"template_version: {TEMPLATE_VERSION}" in read_text(path)


def validate_format_ready(research_dir: Path) -> Validation:
    validation = Validation()
    validation.require_file(research_dir / "RESEARCH_DIRECTION.md", "RESEARCH_DIRECTION.md")
    validation.require_file(research_dir / "CURRENT", "CURRENT")
    version = current_epoch_name(research_dir)
    if not version:
        validation.error("CURRENT missing or empty")
        return validation
    epoch_dir = research_dir / version
    if not epoch_dir.exists():
        validation.error(f"missing current epoch directory: {epoch_dir.as_posix()}")
        return validation
    for name in EPOCH_REQUIRED_FILES + ["closeout.md", "PAPER_BINDING_DECISION.md"]:
        validation.require_file(epoch_dir / name, f"{version}/{name}")
    for name in EPOCH_WIKI_FILES:
        validation.require_file(epoch_dir / "wiki" / name, f"{version}/wiki/{name}")
    for name in AGENT_REQUIRED_FILES:
        validation.require_file(research_dir / "agent" / name, f"agent/{name}")
    repo_root = research_dir.parents[1] if research_dir.name == "research" and research_dir.parent.name == "docs" else research_dir.parent
    validation.require_file(repo_root / "CLAUDE.md", "CLAUDE.md")
    validation.require_file(repo_root / "AGENTS.md", "AGENTS.md")
    key_template_files = [
        research_dir / "RESEARCH_DIRECTION.md",
        research_dir / "INDEX.md",
        epoch_dir / "PRD.tex",
        epoch_dir / "PRD_SUMMARY.md",
        epoch_dir / "SPEC.yaml",
        epoch_dir / "PLAN.md",
        epoch_dir / "STATUS.yaml",
        epoch_dir / "TASK_QUEUE.yaml",
        epoch_dir / "GIT_STATE.yaml",
        epoch_dir / "closeout.md",
        epoch_dir / "PAPER_BINDING_DECISION.md",
        research_dir / "agent" / "RUNBOOK.md",
        research_dir / "agent" / "GIT_POLICY.md",
    ]
    for path in key_template_files:
        if path.exists() and not template_version_ok(path):
            validation.error(f"{path.relative_to(research_dir).as_posix()} missing template_version {TEMPLATE_VERSION}")
    return validation


def detect_workspace_type(research_dir: Path) -> str:
    has_epoch = (research_dir / "RESEARCH_DIRECTION.md").exists() and (research_dir / "CURRENT").exists() and bool(epoch_versions(research_dir))
    legacy_markers = [
        research_dir / "prd",
        research_dir / "spec",
        research_dir / "plans",
        research_dir / "insights",
        research_dir / "audits",
    ]
    has_legacy = any(path.exists() for path in legacy_markers)
    if has_epoch and has_legacy:
        return "mixed"
    if has_epoch:
        return "epoch_v1"
    if has_legacy:
        return "legacy_flat"
    return "unknown"


def legacy_files(research_dir: Path) -> list[str]:
    candidates = [
        "prd/research_prd.md",
        "prd/research_prd.tex",
        "spec/global_spec.yaml",
        "plans/plan_queue.yaml",
        "insights/insight_log.md",
        "audits",
    ]
    return [f"docs/research/{name}" for name in candidates if (research_dir / name).exists()]


def missing_epoch_files(research_dir: Path) -> list[str]:
    missing = []
    if not (research_dir / "RESEARCH_DIRECTION.md").exists():
        missing.append("docs/research/RESEARCH_DIRECTION.md")
    if not (research_dir / "CURRENT").exists():
        missing.append("docs/research/CURRENT")
    version = current_epoch_name(research_dir) or "V0"
    epoch_dir = research_dir / version
    for name in EPOCH_REQUIRED_FILES + ["closeout.md", "PAPER_BINDING_DECISION.md"]:
        if not (epoch_dir / name).exists():
            missing.append(f"docs/research/{version}/{name}")
    for name in EPOCH_WIKI_FILES:
        if not (epoch_dir / "wiki" / name).exists():
            missing.append(f"docs/research/{version}/wiki/{name}")
    return missing


def migration_audit_text(research_dir: Path) -> str:
    workspace_type = detect_workspace_type(research_dir)
    found = legacy_files(research_dir)
    missing = missing_epoch_files(research_dir)
    has_direction = (research_dir / "RESEARCH_DIRECTION.md").exists()
    has_current = (research_dir / "CURRENT").exists()
    lines = [
        "# Migration Audit",
        "",
        "## Detected Layout",
        "",
        f"- workspace_type: `{workspace_type}`",
        f"- has RESEARCH_DIRECTION.md: {has_direction}",
        f"- has CURRENT: {has_current}",
        "",
    ]
    lines.extend(
        [
            "## Found Legacy / Existing Files",
            "",
            *(f"- {item}" for item in found),
            *(["- none"] if not found else []),
            "",
            "## Missing Epoch Files",
            "",
            *(f"- {item}" for item in missing),
            *(["- none"] if not missing else []),
            "",
        ]
    )
    if workspace_type == "unknown":
        lines.extend(
            [
                "## Diagnosis: New / Uninitialized Project",
                "",
                "No recognizable research workspace found. This is either a brand-new project or a repository that has never set up `docs/research/`.",
                "",
                "## Recommended Migration Steps",
                "",
                "### Phase 1 — Initialize Research Corridor",
                "",
                "1. Run `research-init` to scaffold `docs/research/`.",
                "2. Write `RESEARCH_DIRECTION.md` with the 8 required sections: Direction Status, Research Seed, Research Corridor, Out-of-Scope Directions, Prior Work Basis, Desired Paper Shape, Autonomy Boundary, Global Stop Conditions.",
                "3. Set `CURRENT` to `V0`.",
                "",
                "### Phase 2 — Bootstrap First Epoch",
                "",
                "4. Run `generate_research_spec.py` to create `V0/SPEC.yaml` from an initial PRD draft.",
                "5. Ensure `V0/RESEARCH_SPINE.yaml` sets `direction_ref: ../RESEARCH_DIRECTION.md` and defines at least one RQ.",
                "6. Run `validate_research.py --mode format-ready` to verify structure.",
                "",
                "## Human Review Required",
                "",
                "Yes — especially for `RESEARCH_DIRECTION.md` scope and first RQ wording.",
                "",
            ]
        )
    elif workspace_type == "legacy_flat":
        lines.extend(
            [
                "## Diagnosis: Legacy Flat Layout",
                "",
                "The workspace has legacy files (`prd/`, `spec/`, `plans/`, `insights/`) but no epoch structure (`CURRENT`, `Vn/`).",
                "",
                "## Recommended Migration Steps",
                "",
                "### Phase 1 — Establish Direction",
                "",
                "1. Create `RESEARCH_DIRECTION.md` from the legacy PRD summary. It must define the research corridor boundary.",
                "2. Set `CURRENT=V0`.",
                "",
                "### Phase 2 — Migrate Content into Epoch",
                "",
                "3. Copy `prd/research_prd.md` → `V0/PRD.md`.",
                "4. Copy `spec/global_spec.yaml` → `V0/SPEC.yaml`.",
                "5. Convert `plans/plan_queue.yaml` → `V0/TASK_QUEUE.yaml`.",
                "6. Convert `insights/insight_log.md` → `V0/wiki/epoch_summary.md` and `V0/wiki/open_questions.md`.",
                "",
                "### Phase 3 — Bind the Spine",
                "",
                "7. Create `V0/RESEARCH_SPINE.yaml` with `direction_ref: ../RESEARCH_DIRECTION.md`.",
                "8. Map existing RQs from the legacy PRD into `research_questions`.",
                "9. Map existing claims/experiments into the spine chain: `RQ -> Claim -> Experiment -> Evidence -> Figure/Table -> Paper Section`.",
                "10. Mark all migrated artifacts as `carry_forward_candidates`, not paper evidence.",
                "",
                "### Phase 4 — Validate",
                "",
                "11. Run `validate_research.py --mode format-ready`.",
                "12. Run `validate_research.py --mode epoch-ready`.",
                "13. Run `validate_research.py --mode spine-ready`.",
                "",
                "## Human Review Required",
                "",
                "Yes — direction scope, RQ boundary, and claim mapping must be human-approved.",
                "",
            ]
        )
    elif workspace_type == "mixed":
        lines.extend(
            [
                "## Diagnosis: Mixed Layout (Epoch + Legacy)",
                "",
                "Both epoch files (`Vn/`, `CURRENT`) and legacy folders (`prd/`, `spec/`, `plans/`) exist. The legacy content may be stale or redundant.",
                "",
                "## Recommended Migration Steps",
                "",
                "1. Determine whether legacy files are superseded by current epoch files. If yes, archive legacy folders (do not delete without human confirmation).",
                "2. If the epoch is missing `RESEARCH_SPINE.yaml`, create it from the current PRD and bind `direction_ref: ../RESEARCH_DIRECTION.md`.",
                "3. Populate `RESEARCH_SPINE.yaml` with the full evidence chain (`RQ -> Claim -> Experiment -> Evidence -> Figure/Table -> Paper Section`).",
                "4. Run `validate_research.py --mode spine-ready` to verify chain integrity.",
                "5. Run `validate_research.py --mode format-ready`.",
                "",
                "## Human Review Required",
                "",
                "Yes — legacy archive decision and spine mapping.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Diagnosis: Epoch v1 Present",
                "",
                "The workspace already has an epoch structure. Migration is only needed if `format-ready` or `spine-ready` reports issues.",
                "",
                "## Recommended Action",
                "",
                "Run `validate_research.py --mode format-ready` and fix any reported issues.",
                "",
            ]
        )
    lines.extend(
        [
            "## Blockers",
            "",
            "- Legacy evidence may not satisfy current paper-binding rules.",
            "- Audit must not rewrite research claims or promote old insight to paper evidence by default.",
            "- RQ must not exceed the scope declared in `RESEARCH_DIRECTION.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def migration_plan_text(research_dir: Path) -> str:
    workspace_type = detect_workspace_type(research_dir)
    if workspace_type == "unknown":
        steps = [
            "1. 运行 `research-init` 创建 `docs/research/` 目录结构。",
            "2. 撰写 `RESEARCH_DIRECTION.md`，包含 8 个必需章节。",
            "3. 设置 `CURRENT=V0`。",
            "4. 创建初始 PRD 并写入 `V0/PRD.md`。",
            "5. 创建 `V0/RESEARCH_SPINE.yaml`，设置 `direction_ref: ../RESEARCH_DIRECTION.md`。",
            "6. 在 Spine 中定义第一个 RQ。",
            "7. 运行 `format-ready`、`epoch-ready`、`spine-ready` 验证。",
        ]
    elif workspace_type == "legacy_flat":
        steps = [
            "1. 创建 `RESEARCH_DIRECTION.md`（基于 legacy PRD 摘要）。",
            "2. 设置 `CURRENT=V0`。",
            "3. 复制 `prd/research_prd.md` → `V0/PRD.md`。",
            "4. 复制 `spec/global_spec.yaml` → `V0/SPEC.yaml`。",
            "5. 转换 `plans/plan_queue.yaml` → `V0/TASK_QUEUE.yaml`。",
            "6. 转换 `insights/insight_log.md` → `V0/wiki/epoch_summary.md` 和 `open_questions.md`。",
            "7. 创建 `V0/RESEARCH_SPINE.yaml`，设置 `direction_ref: ../RESEARCH_DIRECTION.md`。",
            "8. 将 legacy 中的 RQ/Claim/Experiment 映射进 Spine Matrix。",
            "9. 标记所有迁移 artifact 为 `carry_forward_candidates`，不作为论文证据。",
            "10. 运行 `format-ready`、`epoch-ready`、`spine-ready` 验证。",
        ]
    elif workspace_type == "mixed":
        steps = [
            "1. 评估 legacy 文件是否被当前 epoch 文件取代；若已取代，归档 legacy 目录。",
            "2. 若 `Vn/RESEARCH_SPINE.yaml` 缺失，从当前 PRD 创建并设置 `direction_ref: ../RESEARCH_DIRECTION.md`。",
            "3. 补全 Spine Matrix（RQ → Claim → Experiment → Evidence → Figure/Table → Paper Section）。",
            "4. 运行 `format-ready`、`epoch-ready`、`spine-ready` 验证。",
        ]
    else:
        steps = [
            "1. 运行 `validate_research.py --mode format-ready` 检查现有 epoch 格式合规性。",
            "2. 运行 `validate_research.py --mode spine-ready` 检查证据链完整性。",
            "3. 修复所有 reported issues。",
        ]
    return "\n".join(
        [
            "# Migration Plan",
            "",
            "## Goal",
            "",
            "把当前 workspace 迁移到 research-loop 规定的格式：",
            "",
            "```",
            "RESEARCH_DIRECTION.md (研究走廊边界)",
            "  └─> Vn/RESEARCH_SPINE.yaml (direction_ref 必须指向它)",
            "        └─> RQ1, RQ2, ... (必须落在 RESEARCH_DIRECTION.md 范围内)",
            "              └─> Claim -> Experiment -> Evidence ...",
            "```",
            "",
            "## Detected Workspace Type",
            "",
            f"`{workspace_type}`",
            "",
            "## Steps",
            "",
            *(f"{step}" for step in steps),
            "",
            "## Constraints",
            "",
            "- 不得改写研究主张。",
            "- 迁移的 artifact 只能标记为 `carry_forward_candidates`，不能自动提升为论文证据。",
            "- `RESEARCH_DIRECTION.md` 是研究走廊边界；所有 RQ 必须落在其范围内。",
            "- `RESEARCH_SPINE.yaml` 必须设置 `direction_ref: ../RESEARCH_DIRECTION.md`。",
            "",
        ]
    )


def generate_migration_audit(research_dir: Path, force: bool = False) -> tuple[Path, Path]:
    audit_path = research_dir / "audits" / "MIGRATION_AUDIT.md"
    plan_path = research_dir / "MIGRATION_PLAN.md"
    write_text(audit_path, markdown_template(migration_audit_text(research_dir)), force)
    write_text(plan_path, markdown_template(migration_plan_text(research_dir)), force)
    return audit_path, plan_path


def validate_migration_ready(research_dir: Path) -> Validation:
    validation = Validation()
    workspace_type = detect_workspace_type(research_dir)
    if workspace_type in {"legacy_flat", "mixed"}:
        validation.error(f"workspace_type: {workspace_type}; migration plan required before epoch-ready")
    elif workspace_type == "unknown":
        validation.error("workspace_type: unknown; run research-init or migration audit")
    return validation


def git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def git_status_short(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.splitlines() if result.returncode == 0 else []


def validate_git_ready(research_dir: Path) -> Validation:
    validation = validate_epoch_ready(research_dir)
    if not validation.ok:
        return validation
    repo_root = research_dir.parents[1] if research_dir.name == "research" and research_dir.parent.name == "docs" else research_dir.parent
    if not (repo_root / ".git").exists():
        validation.error("not a git repository")
    epoch_dir = current_epoch_dir(research_dir)
    git_state_path = epoch_dir / "GIT_STATE.yaml"
    if not validation.require_file(git_state_path, "GIT_STATE.yaml"):
        return validation
    git_state = load_yaml(git_state_path)
    if git_state.get("git_enabled") is not True:
        validation.error("GIT_STATE.yaml git_enabled must be true")
    commit_policy = git_state.get("commit_policy", {}) if isinstance(git_state.get("commit_policy"), dict) else {}
    if commit_policy.get("allow_push") is not False:
        validation.error("GIT_STATE.yaml commit_policy.allow_push must be false by default")
    queue = load_yaml(epoch_dir / "TASK_QUEUE.yaml")
    for task in [item for item in as_list(queue.get("tasks")) if isinstance(item, dict)]:
        task_id = str(task.get("id", "<missing>"))
        git_block = task.get("git") if isinstance(task.get("git"), dict) else {}
        if not git_block:
            validation.error(f"task {task_id} missing git policy")
        if task.get("status") == "done" and git_block.get("record_commit_hash") and not git_block.get("commit_hash"):
            validation.error(f"done task {task_id} has no commit hash")
    closeout_text = read_text(epoch_dir / "closeout.md") if (epoch_dir / "closeout.md").exists() else ""
    status = str(load_yaml(epoch_dir / "STATUS.yaml").get("status", ""))
    if status in CLOSED_VERSION_STATUSES and "closeout_commit:" not in closeout_text:
        validation.error("closed epoch closeout.md must record closeout_commit")
    paper_text = read_text(epoch_dir / "PAPER_BINDING_DECISION.md") if (epoch_dir / "PAPER_BINDING_DECISION.md").exists() else ""
    if status in PAPER_BINDING_STATUSES and "paper_binding_commit:" not in paper_text:
        validation.error("paper binding must record paper_binding_commit")
    if status in CLOSED_VERSION_STATUSES | PAPER_BINDING_STATUSES:
        dirty = git_status_short(repo_root)
        if dirty:
            validation.error("closeout or paper binding requires clean git tree or explicit dirty-tree justification")
    return validation


def validate_prd(research_dir: Path) -> Validation:
    validation = Validation()
    epoch_dir = current_epoch_dir(research_dir) if (research_dir / "CURRENT").exists() else None
    if epoch_dir and (epoch_dir / "PRD.tex").exists():
        prd = epoch_dir / "PRD.tex"
        prd_label = f"{epoch_dir.name}/PRD.tex"
    else:
        prd = research_dir / "prd" / "research_prd.md"
        prd_label = "Research PRD"
    if not validation.require_file(prd, prd_label):
        return validation
    text = read_text(prd)
    for section in PRD_SECTIONS:
        label = section.split(". ", 1)[1] if ". " in section else section.lstrip("# ")
        if section not in text and label not in text:
            validation.error(f"missing PRD section: {section}")
    if prd.suffix == ".tex":
        pdf = prd.with_suffix(".pdf")
        blocker = prd.parent / "render_blocker.md"
        if not pdf.exists():
            if blocker.exists():
                validation.error(f"PRD PDF render blocked: {blocker.as_posix()}")
            else:
                validation.error(f"missing PRD PDF generated from {prd_label}: {pdf.as_posix()}")
        summary = prd.parent / "PRD_SUMMARY.md"
        if validation.require_file(summary, f"{epoch_dir.name}/PRD_SUMMARY.md"):
            summary_text = read_text(summary)
            if "不是研究真源" not in summary_text and "not canonical" not in summary_text.lower():
                validation.error("PRD_SUMMARY.md must state that it is not the canonical research source")
            if re.search(r"canonical\s*:\s*true", summary_text, flags=re.IGNORECASE):
                validation.error("PRD_SUMMARY.md must not declare itself canonical")
    if epoch_dir and (epoch_dir / "STATUS.yaml").exists():
        state = load_yaml(epoch_dir / "STATUS.yaml")
    else:
        state = load_yaml(research_dir / "state.yaml")
    prd_state = state.get("prd", {}) if isinstance(state.get("prd"), dict) else {}
    if "PRD_STATUS: HUMAN_APPROVED" not in text and prd_state.get("human_approved") is not True:
        validation.error("PRD missing human approval marker: PRD_STATUS: HUMAN_APPROVED")
    concrete_rq_lines = [
        line
        for line in text.splitlines()
        if re.search(r"\bRQ\d+\b", line) and "待填写" not in line and "template" not in line.lower()
    ]
    if not concrete_rq_lines:
        validation.error("PRD has no concrete RQ definition")
    concrete_falsification_lines = [
        line
        for line in text.splitlines()
        if "falsification" in line.lower() and "待填写" not in line and "template" not in line.lower()
    ]
    if not concrete_falsification_lines:
        validation.error("PRD hypotheses have no concrete falsification condition")
    lower_text = text.lower()
    if "benchmark selection criteria" not in lower_text and "benchmark candidate matrix" not in lower_text:
        validation.error("PRD missing benchmark selection criteria")
    for label in ["dataset", "baseline", "metric", "harness"]:
        if label not in lower_text:
            validation.error(f"PRD missing {label} plan")
    if "Reader Model and Usage" in text:
        validation.error("PRD must not expose a Reader Model and Usage section")
    return validation


def collect_placeholders(text: str) -> set[str]:
    return {match.group(0) for match in re.finditer(r"\{\{[^{}]+\}\}", text)}


def placeholder_experiment_id(placeholder: str) -> str:
    return placeholder.strip("{} ").split(".", 1)[0]


def spec_experiment_ids(research_dir: Path) -> set[str]:
    manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    ids = set()
    for experiment in as_list(manifest.get("experiments")):
        if isinstance(experiment, dict) and experiment.get("experiment_id"):
            ids.add(str(experiment["experiment_id"]))
    return ids


def validate_paper(research_dir: Path) -> Validation:
    validation = Validation()
    paper_paths = [research_dir / "paper" / "planned_paper.md", research_dir / "paper" / "planned_paper.tex"]
    if not validation.require_file(paper_paths[0], "planned paper markdown"):
        return validation
    text = "\n".join(read_text(path) for path in paper_paths if path.exists())
    lower_text = text.lower()
    for phrase in FORBIDDEN_RESULT_PHRASES:
        if phrase in lower_text:
            validation.error(f"unvalidated empirical result language: `{phrase}`")
    map_path = research_dir / "paper" / "placeholder_map.yaml"
    if not validation.require_file(map_path, "placeholder_map.yaml"):
        return validation
    mapping = load_yaml(map_path)
    entries = [item for item in as_list(mapping.get("placeholders")) if isinstance(item, dict)]
    registered = {str(item.get("placeholder", "")).strip() for item in entries if item.get("placeholder")}
    for placeholder in collect_placeholders(text):
        if placeholder not in registered:
            validation.error(f"unregistered placeholder: {placeholder}")
    experiment_ids = spec_experiment_ids(research_dir)
    for entry in entries:
        placeholder = str(entry.get("placeholder", "")).strip()
        experiment_id = str(entry.get("experiment_id", "")).strip() or placeholder_experiment_id(placeholder)
        if placeholder and placeholder not in collect_placeholders(text):
            validation.error(f"placeholder registered but unused in paper: {placeholder}")
        if experiment_ids and experiment_id not in experiment_ids:
            validation.error(f"placeholder maps to unknown spec experiment: {placeholder} -> {experiment_id}")
    return validation


def has_command_or_blocker(harness: dict[str, Any]) -> bool:
    command = harness.get("command")
    blocker = harness.get("blocker") or harness.get("explicit_blocker")
    if isinstance(command, str) and command.strip():
        return True
    if isinstance(command, list) and any(str(item).strip() for item in command):
        return True
    if isinstance(blocker, str) and blocker.strip():
        return True
    if isinstance(blocker, dict) and blocker:
        return True
    return False


def manifest_index(items: list[Any], id_field: str) -> dict[str, dict[str, Any]]:
    return {
        str(item[id_field]): item
        for item in items
        if isinstance(item, dict) and item.get(id_field)
    }


def source_type_is_mockish(value: Any) -> bool:
    return str(value or "").strip().lower() in MOCK_SOURCE_TYPES


def has_real_reference(payload: dict[str, Any], fields: list[str]) -> bool:
    for field in fields:
        value = payload.get(field)
        if isinstance(value, str) and value.strip() and "【待填写" not in value:
            return True
        if isinstance(value, (int, float)) or value is True:
            return True
    return False


def validate_real_dataset(dataset_id: str, datasets: dict[str, dict[str, Any]], validation: Validation, context: str) -> None:
    dataset = datasets.get(dataset_id)
    if not dataset:
        validation.error(f"{context} references dataset {dataset_id} missing from dataset_manifest.yaml")
        return
    if dataset.get("is_mock") is not False:
        validation.error(f"{context} dataset {dataset_id} must explicitly set is_mock: false")
    if dataset.get("is_synthetic") is True:
        validation.error(f"{context} dataset {dataset_id} is synthetic and cannot support full experiment/reproduction evidence")
    if not str(dataset.get("data_source_type", "")).strip():
        validation.error(f"{context} dataset {dataset_id} must declare data_source_type")
    if source_type_is_mockish(dataset.get("data_source_type")):
        validation.error(f"{context} dataset {dataset_id} data_source_type cannot be mock/toy/synthetic/stub/cached/proxy")
    if not has_real_reference(dataset, ["provenance", "source", "manifest_path"]):
        validation.error(f"{context} dataset {dataset_id} must declare real data provenance")
    if not has_real_reference(dataset, ["license", "usage_rights"]):
        validation.error(f"{context} dataset {dataset_id} must declare license or usage_rights")
    if not has_real_reference(dataset, ["split_file", "frozen_split", "benchmark_manifest"]):
        validation.error(f"{context} dataset {dataset_id} must declare frozen split or benchmark manifest")


def validate_real_model(model_id: str, models: dict[str, dict[str, Any]], validation: Validation, context: str) -> None:
    model = models.get(model_id)
    if not model:
        validation.error(f"{context} references model/baseline {model_id} missing from model_manifest.yaml")
        return
    if model.get("is_mock") is not False:
        validation.error(f"{context} model/baseline {model_id} must explicitly set is_mock: false")
    if model.get("is_stub") is True:
        validation.error(f"{context} model/baseline {model_id} is a stub and cannot support full experiment/reproduction evidence")
    if not str(model.get("model_source_type", "")).strip():
        validation.error(f"{context} model/baseline {model_id} must declare model_source_type")
    if source_type_is_mockish(model.get("model_source_type")):
        validation.error(f"{context} model/baseline {model_id} model_source_type cannot be mock/toy/synthetic/stub/cached/proxy")
    if not has_real_reference(
        model,
        [
            "implementation_ref",
            "checkpoint_or_model_version",
            "checkpoint",
            "model_version",
            "api_model_id",
            "code_commit",
            "official_code_commit",
        ],
    ):
        validation.error(f"{context} model/baseline {model_id} must declare checkpoint, model version, API model id, implementation ref, or code commit")


def validate_task_graph(
    research_dir: Path,
    graph_path: Path,
    harness_path: Path,
    validation: Validation,
    required: bool = True,
) -> None:
    if required:
        validation.require_file(graph_path, "task graph")
        validation.require_file(harness_path, "harness manifest")
    graph = load_yaml(graph_path)
    harness_doc = load_yaml(harness_path)
    tasks = [item for item in as_list(graph.get("tasks")) if isinstance(item, dict)]
    gates = [item for item in as_list(graph.get("gates")) if isinstance(item, dict)]
    harnesses = [item for item in as_list(harness_doc.get("harnesses")) if isinstance(item, dict)]
    harness_ids = {str(item.get("harness_id")) for item in harnesses if item.get("harness_id")}
    task_ids = {str(item.get("task_id")) for item in tasks if item.get("task_id")}
    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        for harness_id in [str(item).strip() for item in as_list(task.get("harnesses")) if str(item).strip()]:
            if harness_id not in harness_ids:
                validation.error(f"task {task_id} references missing harness {harness_id}")
        if not as_list(task.get("harnesses")):
            validation.error(f"task {task_id} has no harness")
    for gate in gates:
        gate_id = str(gate.get("gate_id", "")).strip()
        for task_id in [str(item).strip() for item in as_list(gate.get("tasks")) if str(item).strip()]:
            if task_id not in task_ids:
                validation.error(f"gate {gate_id} references missing task {task_id}")
    for harness in harnesses:
        harness_id = str(harness.get("harness_id", "")).strip()
        if not has_command_or_blocker(harness):
            validation.error(f"harness {harness_id} has no command or explicit blocker")
        if harness.get("type") == "full_experiment":
            if harness.get("independent_rerun_required") is not True:
                validation.error(f"full experiment harness {harness_id} must require independent rerun")
            pass_criteria = {str(item) for item in as_list(harness.get("pass_criteria"))}
            required_criteria = {
                "all_declared_seeds_completed",
                "all_declared_baselines_completed",
                "no_mock_data_used",
                "no_missing_metric",
                "no_test_tuning",
                "artifact_hashes_recorded",
            } | FULL_EXPERIMENT_REAL_CRITERIA
            missing = sorted(required_criteria - pass_criteria)
            if missing:
                validation.error(f"full experiment harness {harness_id} missing pass criteria: {', '.join(missing)}")
            if harness.get("may_support_research_claim") and not FULL_EXPERIMENT_REAL_CRITERIA.issubset(pass_criteria):
                validation.error(f"full experiment harness {harness_id} lacks real data/model checks for research claim")
        if harness.get("type") in {"full_reproduction", "reproduction_full"}:
            if harness.get("independent_rerun_required") is not True:
                validation.error(f"full reproduction harness {harness_id} must require independent rerun")
            pass_criteria = {str(item) for item in as_list(harness.get("pass_criteria"))}
            missing = sorted(FULL_REPRODUCTION_REAL_CRITERIA - pass_criteria)
            if missing:
                validation.error(f"full reproduction harness {harness_id} missing pass criteria: {', '.join(missing)}")


def validate_spec(research_dir: Path) -> Validation:
    validation = Validation()
    for relative_path in SPEC_FILES:
        validation.require_file(research_dir / "spec" / relative_path, f"spec/{relative_path}")
    global_spec = load_yaml(research_dir / "spec" / "global_spec.yaml")
    if not as_list(global_spec.get("rq_chain")):
        validation.error("global_spec.yaml has no RQ -> Hypothesis -> Claim -> Experiment chain")

    exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    experiments = [item for item in as_list(exp_manifest.get("experiments")) if isinstance(item, dict)]
    if not experiments:
        validation.error("experiment_manifest.yaml has no experiments")
    dataset_manifest = load_yaml(research_dir / "spec" / "shared" / "dataset_manifest.yaml")
    model_manifest = load_yaml(research_dir / "spec" / "shared" / "model_manifest.yaml")
    datasets = manifest_index(as_list(dataset_manifest.get("datasets")), "dataset_id")
    models = manifest_index(as_list(model_manifest.get("models")), "model_id")
    required_exp_fields = [
        "experiment_id",
        "title",
        "linked_rq",
        "hypothesis",
        "claim",
        "purpose",
        "status",
        "dataset",
        "split_file",
        "preprocessing_config",
        "models",
        "proposed_method_config",
        "baselines",
        "data_model_truth",
        "seeds",
        "metrics",
        "statistical_protocol",
        "commands",
        "required_artifacts",
        "harnesses",
        "support_condition",
        "falsification_condition",
        "mock_policy",
    ]
    experiment_harnesses = {
        str(item.get("harness_id"))
        for item in as_list(load_yaml(research_dir / "spec" / "experiments" / "experiment_harness.yaml").get("harnesses"))
        if isinstance(item, dict) and item.get("harness_id")
    }
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id", "")).strip() or "<missing>"
        for field in required_exp_fields:
            if not experiment.get(field):
                validation.error(f"experiment {experiment_id} missing {field}")
        data_model_truth = experiment.get("data_model_truth") if isinstance(experiment.get("data_model_truth"), dict) else {}
        if data_model_truth.get("full_experiment_requires_real_data") is not True:
            validation.error(f"experiment {experiment_id} must require real data for full experiments")
        if data_model_truth.get("full_experiment_requires_real_model") is not True:
            validation.error(f"experiment {experiment_id} must require real model/code for full experiments")
        dataset_id = str(experiment.get("dataset", "")).strip()
        if dataset_id:
            validate_real_dataset(dataset_id, datasets, validation, f"experiment {experiment_id}")
        for model_id in [str(item).strip() for item in as_list(experiment.get("models")) + as_list(experiment.get("baselines")) if str(item).strip()]:
            validate_real_model(model_id, models, validation, f"experiment {experiment_id}")
        for harness_id in [str(item).strip() for item in as_list(experiment.get("harnesses")) if str(item).strip()]:
            if harness_id not in experiment_harnesses:
                validation.error(f"experiment {experiment_id} references missing harness {harness_id}")

    validate_task_graph(
        research_dir,
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        validation,
    )
    validate_task_graph(
        research_dir,
        research_dir / "spec" / "reproduction" / "reproduction_task_graph.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_harness.yaml",
        validation,
        required=False,
    )
    validate_task_graph(
        research_dir,
        research_dir / "spec" / "implementation" / "implementation_task_graph.yaml",
        research_dir / "spec" / "implementation" / "implementation_harness.yaml",
        validation,
        required=False,
    )

    reproduction_manifest = load_yaml(research_dir / "spec" / "reproduction" / "reproduction_manifest.yaml")
    reproduction_harness_doc = load_yaml(research_dir / "spec" / "reproduction" / "reproduction_harness.yaml")
    reproduction_harnesses = {
        str(item.get("harness_id")): item
        for item in as_list(reproduction_harness_doc.get("harnesses"))
        if isinstance(item, dict) and item.get("harness_id")
    }
    for target in as_list(reproduction_manifest.get("reproduction_targets")):
        if not isinstance(target, dict):
            continue
        reproduction_id = str(target.get("reproduction_id", "")).strip() or "<missing>"
        mode = str(target.get("reproduction_mode", "")).strip()
        if mode not in REPRODUCTION_MODES:
            validation.error(f"reproduction target {reproduction_id} has invalid reproduction_mode {mode}")
        if mode == "paper_based_reimplementation" and "paper_based_reimplementation" not in target:
            validation.error(f"paper-based reproduction {reproduction_id} missing paper_based_reimplementation detail")
        if target.get("can_support_main_experiment") is True:
            real_data_policy = target.get("real_data_policy") if isinstance(target.get("real_data_policy"), dict) else {}
            real_model_policy = target.get("real_model_policy") if isinstance(target.get("real_model_policy"), dict) else {}
            if real_data_policy.get("requires_real_dataset") is not True:
                validation.error(f"reproduction target {reproduction_id} must require real dataset before supporting main experiments")
            if real_model_policy.get("requires_real_model_or_code") is not True:
                validation.error(f"reproduction target {reproduction_id} must require real model/code before supporting main experiments")
            dataset_ref = target.get("dataset") if isinstance(target.get("dataset"), dict) else {}
            dataset_id = str(real_data_policy.get("dataset_id") or dataset_ref.get("dataset_id") or "").strip()
            if dataset_id:
                validate_real_dataset(dataset_id, datasets, validation, f"reproduction target {reproduction_id}")
            else:
                validation.error(f"reproduction target {reproduction_id} missing real dataset_id")
            baseline_model_id = str(real_model_policy.get("baseline_model_id") or target.get("baseline_id") or "").strip()
            if baseline_model_id:
                validate_real_model(baseline_model_id, models, validation, f"reproduction target {reproduction_id}")
            else:
                validation.error(f"reproduction target {reproduction_id} missing baseline_model_id")
            commands = target.get("commands") if isinstance(target.get("commands"), dict) else {}
            if not as_list(commands.get("run")):
                validation.error(f"reproduction target {reproduction_id} must define full run command, not only smoke")
            harness_ids = [str(item).strip() for item in as_list(target.get("harnesses")) if str(item).strip()]
            full_harnesses = [
                reproduction_harnesses[harness_id]
                for harness_id in harness_ids
                if harness_id in reproduction_harnesses
                and reproduction_harnesses[harness_id].get("type") in {"full_reproduction", "reproduction_full"}
            ]
            if not full_harnesses:
                validation.error(f"reproduction target {reproduction_id} must include a full_reproduction harness before supporting main experiments")

    evidence_contract = load_yaml(research_dir / "spec" / "shared" / "evidence_contract.yaml")
    if not evidence_contract.get("claims") and not evidence_contract.get("evidence_rules"):
        validation.error("evidence_contract.yaml has no claim contract or evidence rules")
    anti_mock_policy = load_yaml(research_dir / "spec" / "shared" / "anti_mock_policy.yaml")
    real_gate = anti_mock_policy.get("real_data_model_gate") if isinstance(anti_mock_policy.get("real_data_model_gate"), dict) else {}
    if not real_gate:
        validation.error("anti_mock_policy.yaml missing real_data_model_gate")
    for gate_field in ["full_experiment_required_checks", "full_reproduction_required_checks"]:
        if not as_list(real_gate.get(gate_field)):
            validation.error(f"anti_mock_policy.yaml real_data_model_gate missing {gate_field}")

    insight_policy = load_yaml(research_dir / "spec" / "shared" / "insight_policy.yaml")
    if not insight_policy.get("insight_policy"):
        validation.error("insight_policy.yaml missing insight_policy section")

    insight_manifest = load_yaml(research_dir / "spec" / "insights" / "insight_manifest.yaml")
    if not insight_manifest.get("insight_categories"):
        validation.error("insight_manifest.yaml missing insight_categories")

    valid_experiment_types = {"confirmatory", "exploratory", "diagnostic", "reproduction", "ablation", "stress"}
    for experiment in experiments:
        exp_type = str(experiment.get("experiment_type", "")).strip()
        if exp_type and exp_type not in valid_experiment_types:
            validation.error(f"experiment {experiment.get('experiment_id', '<missing>')} has invalid experiment_type: {exp_type}")

    return validation


def validate_plan(research_dir: Path) -> Validation:
    validation = Validation()
    plan_dirs: list[Path] = []
    legacy_plans = research_dir / "plans"
    if legacy_plans.exists():
        plan_dirs.extend(path for path in legacy_plans.iterdir() if path.is_dir())
    version = current_epoch_name(research_dir)
    if version:
        epoch_plans = research_dir / version / "plans"
        if epoch_plans.exists():
            plan_dirs.extend(path for path in epoch_plans.iterdir() if path.is_dir())
    if not plan_dirs:
        validation.error("no dated research plan exists")
        return validation
    ids = collect_spec_ids(research_dir)
    current_spec_hash = hash_path(research_dir / version / "SPEC.yaml") if version else hash_path(research_dir / "spec")
    current_paper_hash = hash_path(research_dir / "paper")
    for plan_dir in plan_dirs:
        plan_yaml = plan_dir / "plan.yaml"
        if not validation.require_file(plan_yaml, "plan.yaml"):
            continue
        payload = load_yaml(plan_yaml)
        versions = payload.get("source_versions", {}) if isinstance(payload.get("source_versions"), dict) else {}
        if not versions.get("spec_hash"):
            validation.error(f"plan {plan_dir.name} missing source_versions.spec_hash")
        elif versions.get("spec_hash") != current_spec_hash:
            validation.error(f"plan {plan_dir.name} has stale spec hash")
        if not versions.get("prd_hash") or not versions.get("paper_hash") or not versions.get("git_commit"):
            validation.error(f"plan {plan_dir.name} missing PRD/paper/git source hash")
        elif versions.get("paper_hash") != current_paper_hash:
            validation.error(f"plan {plan_dir.name} has stale paper hash")
        for key in ["allowed_scope", "forbidden_actions", "gates", "harnesses", "artifacts", "completion_condition"]:
            if not as_list(payload.get(key)):
                validation.error(f"plan {plan_dir.name} missing {key}")
        for gate_id in [str(item).strip() for item in as_list(payload.get("gates")) if str(item).strip()]:
            if gate_id not in ids["gates"]:
                validation.error(f"plan {plan_dir.name} references missing spec gate {gate_id}")
        for harness_id in [str(item).strip() for item in as_list(payload.get("harnesses")) if str(item).strip()]:
            if harness_id not in ids["harnesses"]:
                validation.error(f"plan {plan_dir.name} references missing spec harness {harness_id}")
        for name in ["ai_loop_prompt.md", "current_state.md", "blocker_log.md", "decision_log.md", "run_log.md", "insight_log.md", "final_summary.md"]:
            validation.require_file(plan_dir / name, f"plan {plan_dir.name}/{name}")
    return validation


LOOP_PROMPT_REQUIRED_CLAUSES = [
    ("document_writing_stop_ask", ["文档撰写阶段", "停止并请求用户确认"]),
    ("execution_do_not_ask", ["执行阶段", "不得停止询问", "自主推进"]),
    ("required_info_blocker", ["required information", "缺失", "blocker"]),
]

AGENT_CONTRACT_RULES: list[tuple[str, str, str]] = [
    ("rq_before_action", "RQ before action", "Every task must map to a Research Question, Claim, Experiment, Evidence, Figure/Table, or Paper Section."),
    ("reproduce_before_propose", "Reproduce before propose", "Before claiming novelty or designing experiments, search prior work and inspect the current repo."),
    ("evidence_before_writing", "Evidence before writing", "Do not write paper claims unless the corresponding data, log, table, or citation exists."),
    ("surgical_edits", "Surgical edits", "Modify only the current version folder or declared target files. Do not silently rewrite unrelated artifacts."),
    ("conflict_surfacing", "Conflict surfacing", "If PRD, spec, task, paper, or code disagree, stop and report the conflict instead of averaging them."),
    ("checkpoint_long_loops", "Checkpoint long loops", "After each major stage, write what changed, what evidence was produced, and what remains blocked."),
    ("fail_visibly", "Fail visibly", "Missing data, failed reproduction, skipped experiment, or unverifiable claim must be explicitly marked."),
    ("deterministic_work_scripts", "Deterministic work belongs to scripts", "Formatting checks, table generation, metric computation, and file routing should be scripted, not decided by LLM judgment."),
    ("tests_are_evidence", "Tests are evidence, not decoration", "Passing tests only count if they verify the intended scientific or system behavior."),
    ("convention_beats_novelty", "Convention beats novelty", "Follow the project's existing folder structure, naming, template, and artifact format unless explicitly asked to migrate."),
]

CLAUDE_CONTRACT_REQUIRED_CLAUSES: list[tuple[str, list[str]]] = [
    ("rq_before_action", ["RQ before action", "Research Question"]),
    ("reproduce_before_propose", ["Reproduce before propose", "prior work"]),
    ("evidence_before_writing", ["Evidence before writing", "data, log, table, or citation"]),
    ("surgical_edits", ["Surgical edits", "declared target files"]),
    ("conflict_surfacing", ["Conflict surfacing", "stop and report"]),
    ("checkpoint_long_loops", ["Checkpoint long loops", "what changed"]),
    ("fail_visibly", ["Fail visibly", "explicitly marked"]),
    ("deterministic_work_scripts", ["Deterministic work belongs to scripts", "scripted"]),
    ("tests_are_evidence", ["Tests are evidence, not decoration", "verify the intended"]),
    ("convention_beats_novelty", ["Convention beats novelty", "existing folder structure"]),
]

AGENTS_CONTRACT_REQUIRED_CLAUSES: list[tuple[str, list[str]]] = [
    ("rq_before_action", ["RQ 先于行动", "研究问题"]),
    ("reproduce_before_propose", ["复现先于提出", "已有工作"]),
    ("evidence_before_writing", ["证据先于写作", "数据、日志、表格或引用"]),
    ("surgical_edits", ["手术式编辑", "声明的目标文件"]),
    ("conflict_surfacing", ["冲突暴露", "停止并报告"]),
    ("checkpoint_long_loops", ["长循环检查点", "发生了什么变化"]),
    ("fail_visibly", ["可见失败", "明确标记"]),
    ("deterministic_work_scripts", ["确定性工作属于脚本", "脚本化"]),
    ("tests_are_evidence", ["测试是证据而非装饰", "验证预期"]),
    ("convention_beats_novelty", ["约定优于新奇", "现有文件夹结构"]),
]


def validate_agent_contracts(research_dir: Path) -> Validation:
    validation = Validation()
    repo_root = research_dir.parents[1] if research_dir.name == "research" and research_dir.parent.name == "docs" else research_dir.parent
    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"
    if not claude_path.exists():
        validation.error("CLAUDE.md missing: cannot verify Research Agent Behavior Contract")
        return validation
    if not agents_path.exists():
        validation.error("AGENTS.md missing: cannot verify Research Agent Behavior Contract")
        return validation
    claude_text = read_text(claude_path)
    agents_text = read_text(agents_path)
    claude_section = markdown_section(claude_text, "Research Agent Behavior Contract")
    agents_section = markdown_section(agents_text, "研究智能体行为契约")
    if not claude_section:
        validation.error("CLAUDE.md missing '## Research Agent Behavior Contract' section")
    else:
        for check_id, required_substrings in CLAUDE_CONTRACT_REQUIRED_CLAUSES:
            if not all(s in claude_section for s in required_substrings):
                missing = ", ".join(s for s in required_substrings if s not in claude_section)
                validation.error(f"CLAUDE.md contract missing rule '{check_id}' (missing: {missing})")
    if not agents_section:
        validation.error("AGENTS.md missing '## 研究智能体行为契约' section")
    else:
        for check_id, required_substrings in AGENTS_CONTRACT_REQUIRED_CLAUSES:
            if not all(s in agents_section for s in required_substrings):
                missing = ", ".join(s for s in required_substrings if s not in agents_section)
                validation.error(f"AGENTS.md contract missing rule '{check_id}' (missing: {missing})")
    return validation


def repair_agent_contracts(repo_root: Path, force: bool = False) -> list[str]:
    actions: list[str] = []
    claude_path = repo_root / "CLAUDE.md"
    agents_path = repo_root / "AGENTS.md"
    if not claude_path.exists() and not agents_path.exists():
        return actions
    claude_header = "## Research Agent Behavior Contract"
    agents_header = "## 研究智能体行为契约"
    claude_rules = "\n".join(f"{i}. {name}. {desc}" for i, (_, name, desc) in enumerate(AGENT_CONTRACT_RULES, start=1))
    agents_rules = "\n".join(
        f"{i}. " + "。".join(AGENTS_CONTRACT_REQUIRED_CLAUSES[i-1][1]) + "。"
        for i in range(1, len(AGENT_CONTRACT_RULES) + 1)
    )
    if claude_path.exists():
        claude_text = read_text(claude_path)
        if claude_header not in claude_text:
            new_section = f"\n\n{claude_header}\n\n{claude_rules}\n"
            claude_path.write_text(claude_text.rstrip() + new_section, encoding="utf-8")
            actions.append("Added Research Agent Behavior Contract section to CLAUDE.md")
        else:
            section = markdown_section(claude_text, "Research Agent Behavior Contract") or ""
            added_rules: list[str] = []
            for check_id, required_substrings in CLAUDE_CONTRACT_REQUIRED_CLAUSES:
                if not all(s in section for s in required_substrings):
                    rule = next((r for r in AGENT_CONTRACT_RULES if r[0] == check_id), None)
                    if rule:
                        idx = next((i for i, (cid, _) in enumerate(CLAUDE_CONTRACT_REQUIRED_CLAUSES) if cid == check_id), 0)
                        added_rules.append(f"{idx + 1}. {rule[1]}. {rule[2]}")
            if added_rules:
                lines = claude_text.rstrip().splitlines()
                insert_idx = len(lines)
                for i, line in enumerate(lines):
                    if claude_header in line:
                        insert_idx = i + 1
                        for j in range(i + 1, len(lines)):
                            if lines[j].startswith("## "):
                                insert_idx = j
                                break
                            insert_idx = j + 1
                        break
                lines.insert(insert_idx, "")
                for rule in added_rules:
                    lines.insert(insert_idx + 1, rule)
                claude_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                actions.append(f"Added {len(added_rules)} missing contract rules to CLAUDE.md")
    if agents_path.exists():
        agents_text = read_text(agents_path)
        if agents_header not in agents_text:
            new_section = f"\n\n{agents_header}\n\n{agents_rules}\n"
            agents_path.write_text(agents_text.rstrip() + new_section, encoding="utf-8")
            actions.append("Added 研究智能体行为契约 section to AGENTS.md")
        else:
            section = markdown_section(agents_text, "研究智能体行为契约") or ""
            added_rules: list[str] = []
            for check_id, required_substrings in AGENTS_CONTRACT_REQUIRED_CLAUSES:
                if not all(s in section for s in required_substrings):
                    idx = next((i for i, (cid, _) in enumerate(AGENTS_CONTRACT_REQUIRED_CLAUSES) if cid == check_id), None)
                    if idx is not None:
                        added_rules.append(f"{idx + 1}. {AGENTS_CONTRACT_REQUIRED_CLAUSES[idx][1][0]}")
            if added_rules:
                lines = agents_text.rstrip().splitlines()
                insert_idx = len(lines)
                for i, line in enumerate(lines):
                    if agents_header in line:
                        insert_idx = i + 1
                        for j in range(i + 1, len(lines)):
                            if lines[j].startswith("## "):
                                insert_idx = j
                                break
                            insert_idx = j + 1
                        break
                lines.insert(insert_idx, "")
                for rule in added_rules:
                    lines.insert(insert_idx + 1, rule)
                agents_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                actions.append(f"Added {len(added_rules)} missing contract rules to AGENTS.md")
    return actions


def validate_loop_prompt_ready(research_dir: Path) -> Validation:
    validation = Validation()
    plans_dir = research_dir / "plans"
    plan_dirs = sorted(path for path in plans_dir.iterdir() if path.is_dir()) if plans_dir.exists() else []
    for plan_dir in plan_dirs:
        prompt_path = plan_dir / "ai_loop_prompt.md"
        if not prompt_path.exists():
            continue
        text = prompt_path.read_text(encoding="utf-8")
        for check_id, required_substrings in LOOP_PROMPT_REQUIRED_CLAUSES:
            if not all(s in text for s in required_substrings):
                missing = ", ".join(s for s in required_substrings if s not in text)
                validation.error(
                    f"plan {plan_dir.name} ai_loop_prompt.md missing clause '{check_id}' (missing: {missing})"
                )
    epoch_dir = current_epoch_dir(research_dir)
    if epoch_dir:
        epoch_prompt = epoch_dir / "ai_loop_prompt.md"
        if epoch_prompt.exists():
            text = epoch_prompt.read_text(encoding="utf-8")
            for check_id, required_substrings in LOOP_PROMPT_REQUIRED_CLAUSES:
                if not all(s in text for s in required_substrings):
                    missing = ", ".join(s for s in required_substrings if s not in text)
                    validation.error(
                        f"epoch ai_loop_prompt.md missing clause '{check_id}' (missing: {missing})"
                    )
    return validation


def validate_insight(research_dir: Path) -> Validation:
    validation = Validation()
    validation.require_file(research_dir / "insights" / "insight_log.md", "insights/insight_log.md")
    validation.require_file(research_dir / "spec" / "shared" / "insight_policy.yaml", "spec/shared/insight_policy.yaml")
    validation.require_file(research_dir / "spec" / "insights" / "insight_manifest.yaml", "spec/insights/insight_manifest.yaml")
    validation.require_file(research_dir / "spec" / "insights" / "insight_policy.yaml", "spec/insights/insight_policy.yaml")
    validation.require_file(research_dir / "spec" / "insights" / "anomaly_schema.yaml", "spec/insights/anomaly_schema.yaml")
    validation.require_file(research_dir / "spec" / "insights" / "pivot_proposal_schema.yaml", "spec/insights/pivot_proposal_schema.yaml")
    validation.require_file(
        research_dir / "spec" / "insights" / "diagnostic_experiment_policy.yaml",
        "spec/insights/diagnostic_experiment_policy.yaml",
    )
    validation.require_file(research_dir / "spec" / "feedback" / "README.md", "spec/feedback/README.md")
    manifest = load_yaml(research_dir / "spec" / "insights" / "insight_manifest.yaml")
    for insight in as_list(manifest.get("insights")):
        if not isinstance(insight, dict):
            continue
        insight_id = str(insight.get("insight_id", "<missing>")).strip()
        for field in ["insight_type", "observation", "action_recommendation", "confidence"]:
            if not insight.get(field):
                validation.error(f"insight {insight_id} missing {field}")
        confidence = str(insight.get("confidence", "")).strip()
        if confidence and confidence not in {"low", "medium", "high"}:
            validation.error(f"insight {insight_id} has invalid confidence: {confidence}")
    return validation


def validate_audit(research_dir: Path) -> Validation:
    validation = Validation()
    audit_results = run_epoch_audit_checks(research_dir, mode="full")
    for result in audit_results:
        if result.status == "FAIL" and result.severity in {"P0", "P1"}:
            validation.error(f"{result.check_id}: {result.message}")
    epoch_audit_dir = None
    if current_epoch_dir(research_dir).exists():
        epoch_audit_dir = latest_child(current_epoch_dir(research_dir) / "audits")
    audit_dir = latest_child(research_dir / "audits")
    if audit_dir is None:
        if epoch_audit_dir is not None:
            validation.require_file(epoch_audit_dir / "audit_results.yaml", "audit_results.yaml")
            return validation
        validation.error("no dated research audit exists")
        return validation
    for name in ["audit_report.md", "alignment_matrix.yaml", "drift_findings.yaml", "repair_plan.md"]:
        validation.require_file(audit_dir / name, name)
    matrix = load_yaml(audit_dir / "alignment_matrix.yaml")
    dimensions = matrix.get("dimensions", {}) if isinstance(matrix.get("dimensions"), dict) else {}
    for key in AUDIT_MATRIX_KEYS:
        if key not in dimensions:
            validation.error(f"alignment matrix missing dimension: {key}")
    return validation


def validate_alignment(research_dir: Path) -> Validation:
    validation = Validation()
    for child_validation in [validate_prd(research_dir), validate_paper(research_dir), validate_spec(research_dir)]:
        validation.issues.extend(child_validation.issues)
    return validation


def validate_spine(research_dir: Path) -> Validation:
    validation = Validation()
    epoch_dir = current_epoch_dir(research_dir)
    if not epoch_dir:
        validation.error("no current epoch")
        return validation
    spine_path = epoch_dir / "RESEARCH_SPINE.yaml"
    if not validation.require_file(spine_path, "RESEARCH_SPINE.yaml"):
        return validation
    spine = load_yaml(spine_path)
    if not isinstance(spine, dict):
        validation.error("RESEARCH_SPINE.yaml must be a YAML mapping")
        return validation
    version = epoch_dir.name
    if spine.get("version") != version:
        validation.error(f"RESEARCH_SPINE.yaml version {spine.get('version')} does not match epoch {version}")
    direction_ref = spine.get("direction_ref")
    if not direction_ref:
        validation.error("RESEARCH_SPINE.yaml missing required field: direction_ref")
    else:
        direction_path = epoch_dir / str(direction_ref)
        if not direction_path.exists():
            validation.error(f"RESEARCH_SPINE.yaml direction_ref points to non-existent file: {direction_ref}")
    for list_key in ["research_questions", "claims", "experiments", "evidence", "figures_tables", "paper_sections"]:
        if list_key not in spine:
            validation.error(f"RESEARCH_SPINE.yaml missing required field: {list_key}")
        elif not isinstance(spine.get(list_key), list):
            validation.error(f"RESEARCH_SPINE.yaml field {list_key} must be a list")

    rqs = {str(r.get("id")) for r in as_list(spine.get("research_questions")) if isinstance(r, dict) and r.get("id")}
    claims = {str(c.get("id")) for c in as_list(spine.get("claims")) if isinstance(c, dict) and c.get("id")}
    experiments = {str(e.get("id")) for e in as_list(spine.get("experiments")) if isinstance(e, dict) and e.get("id")}
    evidence = {str(ev.get("id")) for ev in as_list(spine.get("evidence")) if isinstance(ev, dict) and ev.get("id")}
    figures = {str(f.get("id")) for f in as_list(spine.get("figures_tables")) if isinstance(f, dict) and f.get("id")}

    for claim in as_list(spine.get("claims")):
        if not isinstance(claim, dict):
            continue
        rq_id = str(claim.get("rq_id") or "")
        if rq_id and rq_id not in rqs:
            validation.error(f"spine claim {claim.get('id')} references unknown rq_id: {rq_id}")

    for exp in as_list(spine.get("experiments")):
        if not isinstance(exp, dict):
            continue
        for cid in as_list(exp.get("claim_ids")):
            if str(cid) not in claims:
                validation.error(f"spine experiment {exp.get('id')} references unknown claim_id: {cid}")

    for ev in as_list(spine.get("evidence")):
        if not isinstance(ev, dict):
            continue
        eid = str(ev.get("experiment_id") or "")
        if eid and eid not in experiments:
            validation.error(f"spine evidence {ev.get('id')} references unknown experiment_id: {eid}")

    for fig in as_list(spine.get("figures_tables")):
        if not isinstance(fig, dict):
            continue
        for eid in as_list(fig.get("evidence_ids")):
            if str(eid) not in evidence:
                validation.error(f"spine figure/table {fig.get('id')} references unknown evidence_id: {eid}")

    for sec in as_list(spine.get("paper_sections")):
        if not isinstance(sec, dict):
            continue
        for cid in as_list(sec.get("claims")):
            if str(cid) not in claims:
                validation.error(f"spine paper_section {sec.get('id')} references unknown claim_id: {cid}")
        for fid in as_list(sec.get("figures_tables")):
            if str(fid) not in figures:
                validation.error(f"spine paper_section {sec.get('id')} references unknown figure/table_id: {fid}")

    spec_path = epoch_dir / "SPEC.yaml"
    if spec_path.exists():
        spec = load_yaml(spec_path)
        spec_experiments = {str(e.get("id")) for e in as_list(spec.get("experiments")) if isinstance(e, dict) and e.get("id")}
        for eid in experiments:
            if eid not in spec_experiments:
                validation.error(f"spine experiment {eid} missing from SPEC.yaml experiments")
        for seid in spec_experiments:
            if seid not in experiments:
                validation.warn(f"SPEC.yaml experiment {seid} not declared in RESEARCH_SPINE.yaml")

    return validation


def validate_research(research_dir: Path, mode: str) -> Validation:
    validators = {
        "direction-ready": validate_direction_ready,
        "epoch-ready": validate_epoch_ready,
        "loop-ready": validate_loop_ready,
        "spine-ready": validate_spine,
        "loop-prompt-ready": validate_loop_prompt_ready,
        "closeout-ready": validate_closeout_ready,
        "paper-binding-ready": validate_paper_binding_ready,
        "format-ready": validate_format_ready,
        "migration-ready": validate_migration_ready,
        "git-ready": validate_git_ready,
        "prd-ready": validate_prd,
        "paper-ready": validate_paper,
        "spec-ready": validate_spec,
        "plan-ready": validate_plan,
        "audit-ready": validate_audit,
        "insight-ready": validate_insight,
        "alignment-check": validate_alignment,
    }
    if mode not in validators:
        raise ValueError(f"unknown validation mode: {mode}")
    return validators[mode](research_dir)


def print_validation(validation: Validation, mode: str, research_dir: Path) -> int:
    if validation.ok:
        print(f"[OK] {mode}: {research_dir}")
        return 0
    for issue in validation.issues:
        print(f"[ERROR] {issue}")
    print(f"[BLOCKED] {mode}: {research_dir}")
    return 1


def resolve_research_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "research_dir", ""):
        return Path(args.research_dir).resolve()
    repo = Path(getattr(args, "repo", ".")).resolve()
    return (repo / DEFAULT_RESEARCH_DIR).resolve()
