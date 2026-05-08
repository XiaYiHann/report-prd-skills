#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from datetime import date
from pathlib import Path

import yaml

from scan_repo import collect as collect_repo_scan


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parents[1]
SHARED_DIR = SKILL_DIR / "_shared"
TEMPLATE_DIR = SHARED_DIR / "assets" / "templates" / "common"
STYLE_TEX = TEMPLATE_DIR / "style.tex"
REFERENCE_DIR = SHARED_DIR / "references"


MAIN_TEX_TEMPLATE = r"""\documentclass[UTF8,11pt]{ctexrep}
\input{style.tex}
\title{__TITLE__}
\subtitle{__SUBTITLE__}
\author{__AUTHOR__}
\date{__DATE__}

\begin{document}
\makecustomtitle
\tableofcontents
\clearpage
\input{build/section-order.tex}
\end{document}
"""


HEADING_PATTERN = re.compile(r"\\(?:chapter|section|subsection)\{([^}]+)\}")


def placeholder_section(kind: str, title: str, prompt: str, questions: list[str]) -> str:
    lines = [f"\\{kind}{{{title}}}", "", f"\\noindent\\textit{{本节待填：{prompt}}}", ""]
    lines.append("% 待回答问题：")
    for index, question in enumerate(questions, start=1):
        lines.append(f"% {index}. {question}")
    lines.append("")
    return "\n".join(lines)


def normalize_top_level_heading(content: str) -> str:
    return re.sub(r"^\\section\{", r"\\chapter{", content, count=1)


def with_extra_placeholders(content: str, placeholders: list[str]) -> str:
    lines = [content.rstrip(), "", "% v0.3 structured evidence/readiness placeholders:"]
    for placeholder in placeholders:
        lines.append(f"% - {placeholder}")
    lines.append("")
    return "\n".join(lines)


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


def slug_token(text: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return token or "module"


def default_module_specs() -> list[dict[str, object]]:
    return [
        {
            "name": "[模块名]",
            "source_paths": [],
            "entrypoints": [],
            "test_paths": [],
            "component_signals": [],
            "reason": "Template fallback because no reliable repo module candidate was detected.",
        }
    ]


def resolve_module_specs(project_root: Path | None, module_source: str) -> list[dict[str, object]]:
    if module_source != "auto" or project_root is None or not project_root.exists():
        return default_module_specs()
    payload = collect_repo_scan(project_root)
    candidates = payload.get("module_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return default_module_specs()
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def render_module_overview_figure(modules: list[dict[str, object]]) -> str:
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "  \\node[reportnode] (input) at (0,0) {输入\\\\触发};",
    ]
    display_modules = modules[:6]
    for index, module in enumerate(display_modules):
        name = latex_escape(str(module.get("name", f"module-{index + 1}")))
        column = index % 3
        row = index // 3
        lines.append(f"  \\node[reportprocess] (m{index}) at ({3.2 + column * 3.0},{-row * 1.8}) {{{name}}};")
    lines.append("  \\node[reportnode] (output) at (12.4,0) {输出\\\\结果};")
    if display_modules:
        lines.append("  \\draw[reportarrow] (input) -- (m0);")
        for index in range(len(display_modules) - 1):
            lines.append(f"  \\draw[reportarrow] (m{index}) -- (m{index + 1});")
        lines.append(f"  \\draw[reportarrow] (m{len(display_modules) - 1}) -- (output);")
    else:
        lines.append("  \\draw[reportarrow] (input) -- (output);")
    lines.append("\\end{tikzpicture}\n")
    return "\n".join(lines)


def render_module_architecture_figure(module_name: str) -> str:
    safe_name = latex_escape(module_name)
    return "\n".join(
        [
            "\\begin{tikzpicture}[node distance=1.35cm and 1.6cm]",
            f"  \\node[reportnode] (input) {{{safe_name}\\\\输入}};",
            "  \\node[reportprocess, right=of input] (core) {职责\\\\处理};",
            "  \\node[reportnode, right=of core] (output) {输出\\\\契约};",
            "  \\node[reportdecision, below=of core] (gate) {边界\\\\校验};",
            "  \\draw[reportarrow] (input) -- (core);",
            "  \\draw[reportarrow] (core) -- (output);",
            "  \\draw[reportarrow] (core) -- (gate);",
            "  \\draw[reportarrow] (gate) -- (output);",
            "\\end{tikzpicture}\n",
        ]
    )


def render_module_sequence_figure(module_name: str) -> str:
    safe_name = latex_escape(module_name)
    return "\n".join(
        [
            "\\begin{tikzpicture}[node distance=1.1cm]",
            "  \\node[reportnode] (caller) {调用方};",
            f"  \\node[reportprocess, below=of caller] (module) {{{safe_name}\\\\模块}};",
            "  \\node[reportdecision, below=of module] (gate) {输入\\\\校验};",
            "  \\node[reportnode, below=of gate] (result) {输出\\\\返回};",
            "  \\draw[reportarrow] (caller) -- node[right]{request} (module);",
            "  \\draw[reportarrow] (module) -- node[right]{validate} (gate);",
            "  \\draw[reportarrow] (gate) -- node[right]{allow/block} (result);",
            "\\end{tikzpicture}\n",
        ]
    )


def module_design_section(modules: list[dict[str, object]], diagram_depth: str) -> str:
    lines = [
        "\\section{核心模块设计}",
        "",
        "\\noindent\\textit{本节待填：每个模块按治理思想、架构图、组件职责表、接口契约、时序图和设计决策展开。}",
        "",
        "% 待回答问题：",
        "% 1. 每个模块的治理思想（一句话定义本质）是什么？",
        "% 2. 模块内部如何 MECE 分解为组件？",
        "% 3. 模块对外提供哪些接口（输入/输出/错误码）？",
        "% 4. 模块与外部交互的主流程时序是什么？",
        "",
    ]
    if diagram_depth == "draft":
        lines.extend(
            [
                "模块总体边界先用图~\\ref{fig:module-overview} 建立全局模型；各模块的细节图回答单个模块的职责切分与 I/O 边界。",
                "",
                "\\begin{figure}[H]",
                "\\centering",
                "\\input{figures/module-overview.tex}",
                "\\caption{核心模块总览图，突出模块间的主依赖方向与输入输出边界。}",
                "\\label{fig:module-overview}",
                "\\end{figure}",
                "",
            ]
        )
    else:
        lines.extend(["% 【图 X：模块总览图】总体模块框架、依赖方向与 I/O 边界", ""])

    for module in modules:
        raw_name = str(module.get("name", "[模块名]"))
        module_name = latex_escape(raw_name)
        module_slug = slug_token(raw_name)
        source_paths = module.get("source_paths", [])
        source_hint = ", ".join(str(path) for path in source_paths[:3]) if isinstance(source_paths, list) else ""
        lines.extend(
            [
                f"\\subsection{{{module_name} 模块}}",
                "",
                f"\\textbf{{治理思想}}：{module_name} 模块的本质定义待根据源码与设计上下文确认。",
                "",
                f"% 扫描线索：{source_hint or '暂无可靠源码线索'}",
            ]
        )
        if diagram_depth == "draft":
            lines.extend(
                [
                    "",
                    "\\begin{figure}[H]",
                    "\\centering",
                    f"\\input{{figures/module-{module_slug}-architecture.tex}}",
                    f"\\caption{{{module_name} 模块架构图，突出内部职责切分与边界校验位置。}}",
                    f"\\label{{fig:module-{module_slug}-architecture}}",
                    "\\end{figure}",
                ]
            )
        else:
            lines.append("% 【图 X：模块架构图】组件 <=6 个，展示职责边界")
        lines.extend(
            [
                "",
                "\\begin{table}[H]",
                "\\centering",
                f"\\caption{{{module_name} 模块组件职责表}}",
                f"\\label{{tab:module-{module_slug}-components}}",
                "\\begin{tabularx}{\\textwidth}{p{0.22\\textwidth}p{0.42\\textwidth}X}",
                "\\toprule",
                "组件 & 职责边界 & 关键技术 \\\\",
                "\\midrule",
                "\\textit{待填} & \\textit{待填} & \\textit{待填} \\\\",
                "\\bottomrule",
                "\\end{tabularx}",
                "\\end{table}",
                "",
                "% 接口 | 输入 | 输出 | 错误码 | 调用关系",
                "\\begin{table}[H]",
                "\\centering",
                f"\\caption{{{module_name} 模块接口契约表}}",
                f"\\label{{tab:module-{module_slug}-io}}",
                "\\begin{tabularx}{\\textwidth}{L{0.16\\textwidth}Y Y L{0.14\\textwidth}Y}",
                "\\toprule",
                "接口 & 输入 & 输出 & 错误码 & 调用关系 \\\\",
                "\\midrule",
                "\\textit{待填} & \\textit{待填} & \\textit{待填} & \\textit{待填} & \\textit{待填} \\\\",
                "\\bottomrule",
                "\\end{tabularx}",
                "\\end{table}",
                "",
            ]
        )
        if diagram_depth == "draft":
            lines.extend(
                [
                    "\\begin{figure}[H]",
                    "\\centering",
                    f"\\input{{figures/module-{module_slug}-sequence.tex}}",
                    f"\\caption{{{module_name} 模块交互时序图，突出请求、校验与返回的主路径。}}",
                    f"\\label{{fig:module-{module_slug}-sequence}}",
                    "\\end{figure}",
                    "",
                ]
            )
        else:
            lines.extend(["% 【图 X：交互时序图】参与者 <=6 个，展示请求、校验与返回", ""])
        lines.extend(
            [
                "\\begin{table}[H]",
                "\\centering",
                f"\\caption{{{module_name} 模块设计决策表}}",
                f"\\label{{tab:module-{module_slug}-decisions}}",
                "\\begin{tabularx}{\\textwidth}{p{0.24\\textwidth}p{0.22\\textwidth}p{0.22\\textwidth}X}",
                "\\toprule",
                "决策 & 选择 & 备选 & 理由 \\\\",
                "\\midrule",
                "\\textit{待填} & \\textit{待填} & \\textit{待填} & \\textit{待填} \\\\",
                "\\bottomrule",
                "\\end{tabularx}",
                "\\end{table}",
                "",
                (
                    f"图~\\ref{{fig:module-{module_slug}-architecture}}、表~\\ref{{tab:module-{module_slug}-components}}、表~\\ref{{tab:module-{module_slug}-io}}、图~\\ref{{fig:module-{module_slug}-sequence}} 与表~\\ref{{tab:module-{module_slug}-decisions}} 共同限定 {module_name} 模块的结构、接口与主交互路径。"
                    if diagram_depth == "draft"
                    else "% 模块结构、接口与主交互路径应在本 subsection 内闭环说明。"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def maybe_specialize_executor_sections(
    section_specs: list[tuple[str, str]],
    modules: list[dict[str, object]],
    diagram_depth: str,
) -> list[tuple[str, str]]:
    specialized: list[tuple[str, str]] = []
    for filename, content in section_specs:
        if filename in {"05-core-module-design.tex", "05-functional-requirements.tex"}:
            section = module_design_section(modules, diagram_depth)
            if filename == "05-functional-requirements.tex":
                section = section.replace(
                    "\\section{核心模块设计}",
                    "\\section{功能需求与模块化设计}",
                    1,
                )
                section += (
                    "\n\n\\subsection{模块级 Acceptance Criteria 总表}\n\n"
                    "\\begin{table}[H]\n"
                    "\\centering\n"
                    "\\caption{Acceptance Criteria：每个功能必须有可测试验收标准。}\n"
                    "\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y}\n"
                    "\\toprule\n"
                    "功能 ID & Acceptance Criteria & 验证方式 \\\\\n"
                    "\\midrule\n"
                    "AC-1 & 待填：用户或下游 Agent 可以执行该功能并得到明确结果。 & 自动测试 / 手工验收。 \\\\\n"
                    "AC-2 & 待填：失败输入返回明确错误，不产生不可逆副作用。 & 边界测试。 \\\\\n"
                    "\\bottomrule\n"
                    "\\end{tabularx}\n"
                    "\\end{table}\n"
                )
            specialized.append((filename, section))
        else:
            specialized.append((filename, content))
    return specialized


def write_module_figures(report_dir: Path, modules: list[dict[str, object]], diagram_depth: str) -> None:
    if diagram_depth != "draft":
        return
    write_file(report_dir / "figures" / "module-overview.tex", render_module_overview_figure(modules))
    for module in modules:
        raw_name = str(module.get("name", "module"))
        module_slug = slug_token(raw_name)
        write_file(
            report_dir / "figures" / f"module-{module_slug}-architecture.tex",
            render_module_architecture_figure(raw_name),
        )
        write_file(
            report_dir / "figures" / f"module-{module_slug}-sequence.tex",
            render_module_sequence_figure(raw_name),
        )


def build_sources(modules: list[dict[str, object]], report_type: str, module_source: str) -> str:
    lines = [
        "# 资料来源",
        "",
        "- 在这里记录网页、论文、项目页面、访谈记录，以及每个关键判断背后的证据来源。",
    ]
    if report_type == "engineering-prd":
        lines.extend(
            [
                "",
                "## 初始化模块扫描",
                "",
                f"- 模块来源策略：`{module_source}`。",
                "- 以下模块仅为初始化扫描线索，写成正文事实前必须经 `report-update` 或人工审查确认。",
            ]
        )
        for module in modules:
            name = module.get("name", "[模块名]")
            source_paths = module.get("source_paths", [])
            tests = module.get("test_paths", [])
            sources = ", ".join(str(path) for path in source_paths) if isinstance(source_paths, list) else ""
            test_paths = ", ".join(str(path) for path in tests) if isinstance(tests, list) else ""
            lines.append(f"- `{name}`: source={sources or '待确认'}; tests={test_paths or '待确认'}。")
    lines.append("")
    return "\n".join(lines)


SECTION_SPECS: dict[str, list[tuple[str, str]]] = {
    "project": [
        (
            "00-executive-summary.tex",
            placeholder_section(
                "chapter",
                "执行摘要与阅读指南",
                "用 4--6 句话说明这份报告解决什么问题、建议谁阅读、先看哪几节，以及读完后应形成什么判断。",
                [
                    "这份报告的最小使命是什么？",
                    "读者是谁，他们最缺什么背景？",
                    "先读哪几节最有效？",
                    "哪些结论是当前就应知道的？",
                ],
            ),
        ),
        (
            "01-project-overview.tex",
            placeholder_section(
                "section",
                "项目概述",
                "交代项目目标、边界、主要交付物和一句话全景总结。",
                [
                    "项目要解决什么问题？",
                    "本报告不覆盖什么？",
                    "最终交付物是什么？",
                ],
            ),
        ),
        (
            "02-background-and-context.tex",
            placeholder_section(
                "section",
                "背景、冲突与上下文",
                "用 SCQA 或等价结构解释为什么要做这件事。",
                [
                    "当前背景是什么？",
                    "核心冲突或痛点是什么？",
                    "本报告的回答是什么？",
                ],
            ),
        ),
        (
            "03-terms-and-prerequisites.tex",
            placeholder_section(
                "section",
                "术语、概念与前置知识",
                "补齐中文 rookie 读者理解后续章节所需的关键概念。",
                [
                    "本报告有哪些第一次出现就必须定义的术语？",
                    "哪些概念若不解释，读者会在后文迷路？",
                ],
            ),
        ),
        (
            "04-system-architecture.tex",
            placeholder_section(
                "section",
                "整体架构与模块边界",
                "说明系统分层、模块职责、输入输出与依赖关系。",
                [
                    "系统边界在哪里？",
                    "模块之间如何交互？",
                    "哪些图或表能降低理解成本？",
                ],
            ),
        ),
        (
            "05-core-design.tex",
            placeholder_section(
                "section",
                "核心设计与关键机制",
                "逐项解释方案中最关键的设计决策、规则和约束。",
                [
                    "这里的关键机制到底是什么？",
                    "为什么这样设计？",
                    "替代方案为何未被采用？",
                ],
            ),
        ),
        (
            "06-workflow-and-execution.tex",
            placeholder_section(
                "section",
                "流程、执行路径与协作方式",
                "说明执行流程、角色分工、关键步骤与真实落地路径。",
                [
                    "执行链路从哪里开始，到哪里结束？",
                    "是否需要流程图或时序图？",
                    "下游执行者按什么顺序推进？",
                ],
            ),
        ),
        (
            "07-data-resources-and-interfaces.tex",
            placeholder_section(
                "section",
                "数据、资源与接口",
                "说明数据来源、资源依赖、接口契约与关键约束。",
                [
                    "核心输入输出是什么？",
                    "有哪些资源依赖或环境前提？",
                    "哪些接口或字段必须解释？",
                ],
            ),
        ),
        (
            "08-verification-and-acceptance.tex",
            placeholder_section(
                "section",
                "验证、测试与验收标准",
                "定义如何判断设计、实现或交付达到可接受标准。",
                [
                    "什么证据能证明这部分成立？",
                    "如何验收，做到什么算完成？",
                    "边界情况与失败条件是什么？",
                ],
            ),
        ),
        (
            "09-project-progress.tex",
            placeholder_section(
                "section",
                "项目进度",
                "集中记录当前基线、已完成事项、进行中工作、阻塞与下一检查点。",
                [
                    "当前已经确认完成了什么？",
                    "还有哪些事情正在进行中？",
                    "当前阻塞是什么，证据来源是什么？",
                    "下一次更新时间或检查点是什么？",
                ],
            ),
        ),
        (
            "10-risks-and-next-steps.tex",
            placeholder_section(
                "section",
                "风险、局限与下一步",
                "说明主要风险、已知局限、后续动作与交付边界。",
                [
                    "最大的技术或组织风险是什么？",
                    "哪些内容仍待验证？",
                    "下一步动作按什么顺序推进？",
                ],
            ),
        ),
    ],
    "research": [
        (
            "00-executive-summary.tex",
            placeholder_section(
                "chapter",
                "执行摘要与阅读指南",
                "用简洁中文说明研究问题、方法主线、证据边界与建议阅读顺序。",
                [
                    "读者先知道什么最有助于理解全文？",
                    "本研究最核心的判断是什么？",
                ],
            ),
        ),
        (
            "01-problem-statement.tex",
            placeholder_section(
                "section",
                "问题定义与研究目标",
                "明确研究问题、目标、假设或主张边界。",
                [
                    "本文到底在回答什么问题？",
                    "哪些命题属于本文范围，哪些不属于？",
                ],
            ),
        ),
        (
            "02-background-and-related-work.tex",
            placeholder_section(
                "section",
                "背景与相关工作",
                "补齐背景，并说明本文与已有方法或文献的关系。",
                [
                    "读者必须先知道哪些背景？",
                    "与已有工作相比，本文的区别在哪里？",
                ],
            ),
        ),
        (
            "03-terms-and-notation.tex",
            placeholder_section(
                "section",
                "术语、符号与前置知识",
                "给出术语、符号和后文推导所需的前置解释。",
                [
                    "哪些符号必须先定义？",
                    "哪些概念必须先建立直觉？",
                ],
            ),
        ),
        (
            "04-core-intuition.tex",
            placeholder_section(
                "section",
                "核心思想与直觉",
                "先用直觉解释方法，再为后续形式化铺路。",
                [
                    "方法到底抓住了什么结构？",
                    "为什么这个直觉值得形式化？",
                ],
            ),
        ),
        (
            "05-method-and-formulation.tex",
            placeholder_section(
                "section",
                "方法设计与形式化建模",
                "给出变量、假设、目标函数和关键建模选择。",
                [
                    "关键变量与目标是什么？",
                    "这些定义的现实含义是什么？",
                ],
            ),
        ),
        (
            "06-derivation-or-algorithm.tex",
            placeholder_section(
                "section",
                "推导、算法与执行流程",
                "说明关键推导步骤或算法流程，并解释每一步为何成立。",
                [
                    "推导分哪几步？",
                    "算法输入输出与边界条件是什么？",
                ],
            ),
        ),
        (
            "07-experiments-or-cases.tex",
            with_extra_placeholders(
                placeholder_section(
                    "section",
                    "实验设计或案例设置",
                    "说明验证方案、数据、基线、指标与案例选择。",
                    [
                        "用什么方式验证主张？",
                        "对比基线与指标是什么？",
                    ],
                ),
                [
                    "baseline matrix：方法 | 指标 | 超参数公平性 | 数据划分 | 结论",
                    "ablation matrix：消融项 | 只改变的变量 | 预期影响 | 观测结果",
                    "reproducibility table：random seed | 数据划分 | 配置 | 硬件 | 运行命令",
                ],
            ),
        ),
        (
            "08-results-and-discussion.tex",
            with_extra_placeholders(
                placeholder_section(
                    "section",
                    "结果、解释与讨论",
                    "说明观察到的结果，以及这些结果究竟支持到什么程度。",
                    [
                        "最关键的结果是什么？",
                        "哪些结论是真正被证据支持的？",
                    ],
                ),
                [
                    "claim -> evidence -> source -> limitation -> confidence",
                    "failure-case table：失败场景 | 触发条件 | 观察结果 | 结论边界",
                ],
            ),
        ),
        (
            "09-project-progress.tex",
            placeholder_section(
                "section",
                "项目进度",
                "集中记录当前实验、代码、数据和文档层面的真实进展。",
                [
                    "哪些实验或实现已经完成？",
                    "哪些结果仍在等待补证据？",
                    "当前阻塞是什么？",
                ],
            ),
        ),
        (
            "10-limitations-and-conclusion.tex",
            placeholder_section(
                "section",
                "局限、结论与下一步",
                "交代局限、结论边界与后续研究动作。",
                [
                    "本文在哪些条件下不成立？",
                    "最稳健的结论是什么？",
                    "下一步最值得补什么？",
                ],
            ),
        ),
    ],
    "teaching": [
        (
            "00-executive-summary.tex",
            placeholder_section(
                "chapter",
                "执行摘要与阅读指南",
                "说明这份教学型报告面向谁、建议如何阅读、读完后应掌握什么。",
                [
                    "读者最先需要哪一个全局判断？",
                    "阅读顺序应如何安排？",
                ],
            ),
        ),
        (
            "01-learning-goals.tex",
            placeholder_section(
                "section",
                "学习目标",
                "定义读者读完后应能解释、判断和应用什么。",
                [
                    "学完后读者应具备什么能力？",
                    "哪些能力属于本文明确不覆盖的范围？",
                ],
            ),
        ),
        (
            "02-why-it-matters.tex",
            placeholder_section(
                "section",
                "为什么这个主题重要",
                "解释这个主题在现实或工程中的意义。",
                [
                    "如果不理解这个主题，会出现什么问题？",
                    "它和读者已有经验如何连接？",
                ],
            ),
        ),
        (
            "03-prerequisites.tex",
            placeholder_section(
                "section",
                "前置知识与术语",
                "补齐后续理解所需的最小背景与术语定义。",
                [
                    "哪些术语必须先解释？",
                    "哪些前置知识需要单独回顾？",
                ],
            ),
        ),
        (
            "04-core-intuition.tex",
            placeholder_section(
                "section",
                "核心直觉",
                "先用直观方式解释概念，再进入更正式的定义。",
                [
                    "这个概念在现实里对应什么？",
                    "有没有最小例子可以先建立直觉？",
                ],
            ),
        ),
        (
            "05-formal-definitions.tex",
            placeholder_section(
                "section",
                "形式化定义与规则",
                "给出正式定义、规则、条件和边界。",
                [
                    "正式定义是什么？",
                    "每个规则背后的动机是什么？",
                ],
            ),
        ),
        (
            "06-worked-example.tex",
            placeholder_section(
                "section",
                "例题、流程与推演",
                "用一个完整案例把概念、步骤与判断串起来。",
                [
                    "最小可讲清楚的例子是什么？",
                    "读者在哪一步最容易误解？",
                ],
            ),
        ),
        (
            "07-common-mistakes.tex",
            placeholder_section(
                "section",
                "常见误解与纠偏",
                "列出最容易踩的坑，以及如何自检与纠正。",
                [
                    "最常见的误解是什么？",
                    "如何快速自检？",
                ],
            ),
        ),
        (
            "08-project-progress.tex",
            placeholder_section(
                "section",
                "项目进度",
                "集中记录当前资料整理、内容编写、示例验证和附图制作的进展。",
                [
                    "哪些教学内容已经成稿？",
                    "哪些示例或图表还待补？",
                    "当前阻塞是什么？",
                ],
            ),
        ),
        (
            "09-summary-and-next-questions.tex",
            placeholder_section(
                "section",
                "小结与下一步问题",
                "总结关键收获，并指出后续可继续深入的问题。",
                [
                    "读者读完后最应记住什么？",
                    "下一步最值得深入的问题是什么？",
                ],
            ),
        ),
    ],
    "hybrid": [
        (
            "00-executive-summary.tex",
            placeholder_section(
                "chapter",
                "执行摘要与阅读指南",
                "说明报告目标、目标读者、主线章节和预期收获。",
                [
                    "这份报告的主问题是什么？",
                    "读者是谁，建议如何阅读？",
                    "读完后应形成什么全局判断？",
                ],
            ),
        ),
        (
            "01-project-overview.tex",
            placeholder_section(
                "section",
                "项目概述与主张",
                "一句话概括项目，再补目标、边界、价值与主张。",
                [
                    "一句话怎么概括整个项目？",
                    "边界和不做什么是什么？",
                ],
            ),
        ),
        (
            "02-background-and-context.tex",
            placeholder_section(
                "section",
                "背景、冲突与上下文",
                "解释为什么现在要讨论这个问题，以及上下文里真正的约束在哪里。",
                [
                    "背景是什么？",
                    "冲突是什么？",
                    "本报告如何回答这个冲突？",
                ],
            ),
        ),
        (
            "03-terms-and-prerequisites.tex",
            placeholder_section(
                "section",
                "术语、符号与前置知识",
                "定义后文需要的术语、符号、角色和基本概念。",
                [
                    "哪些术语必须先定义？",
                    "哪些概念应先建立直觉？",
                ],
            ),
        ),
        (
            "04-core-idea.tex",
            placeholder_section(
                "section",
                "核心思想与设计原则",
                "用直觉和原则解释方案为什么成立。",
                [
                    "方案的核心思想是什么？",
                    "有哪些不应被破坏的设计原则？",
                ],
            ),
        ),
        (
            "05-method-or-formulation.tex",
            placeholder_section(
                "section",
                "方法、建模或关键规则",
                "说明形式化部分、关键规则或最重要的设计约束。",
                [
                    "关键变量、规则或假设是什么？",
                    "它们在现实里分别对应什么？",
                ],
            ),
        ),
        (
            "06-algorithm-and-workflow.tex",
            placeholder_section(
                "section",
                "算法、流程与执行路径",
                "说明主流程、输入输出、边界条件与执行路径。",
                [
                    "核心流程如何走通？",
                    "是否需要流程图或时序图？",
                ],
            ),
        ),
        (
            "07-system-and-resource-design.tex",
            placeholder_section(
                "section",
                "系统、数据与资源设计",
                "说明模块、资源、接口、实验或产品结构。",
                [
                    "系统边界在哪里？",
                    "数据、资源和接口如何组织？",
                ],
            ),
        ),
        (
            "08-examples-results-and-verification.tex",
            placeholder_section(
                "section",
                "示例、结果与验证",
                "用案例、结果或测试说明方案效果，并标清证据边界。",
                [
                    "最有代表性的例子或结果是什么？",
                    "哪些结论已被验证，哪些仍是设计意图？",
                ],
            ),
        ),
        (
            "09-project-progress.tex",
            placeholder_section(
                "section",
                "项目进度",
                "集中记录当前实现、实验、文档和阻塞状态。",
                [
                    "当前已经走到哪一步？",
                    "有哪些已完成项、进行中项和阻塞项？",
                    "下一检查点是什么？",
                ],
            ),
        ),
        (
            "10-risks-and-delivery.tex",
            placeholder_section(
                "section",
                "风险、局限与下一步交付",
                "交代主要风险、局限、交付边界与后续推进建议。",
                [
                    "最大风险在哪里？",
                    "哪些内容仍待补证据？",
                    "下一步应先做什么？",
                ],
            ),
        ),
    ],
}


EXECUTOR_HANDBOOK_SPECS: list[tuple[str, str]] = [
    (
        "00-executive-summary.tex",
        placeholder_section(
            "chapter",
            "执行摘要与阅读指南",
            "说明报告的主问题、建议阅读顺序，以及 `reading-path-map.md` 中角色与深度的对应路径。",
            [
                "这份手册的最小使命是什么？",
                "新成员、PM、工程师、测试分别应按什么顺序读？",
                "读完速览档后应形成什么最小全局判断？",
                "读完完整版后应能动手完成的第一件事是什么？",
            ],
        )
        + "\n\n% === 表格占位 ===\n"
        + "% 【表 1：阅读路径矩阵】角色 | 速览（30分钟）| 中读（2小时）| 精读\n",
    ),
    (
        "01-mental-model-overview.tex",
        placeholder_section(
            "section",
            "一张图看懂系统",
            "按 `progressive-disclosure.md` 的最简心智模型铺开，给出不超过三方的总览图。",
            [
                "本项目可以被抽象成哪三方或哪两层？",
                "最简模型里隐藏了什么？下一层要补什么？",
                "读者在本节结束前应能用一句话复述系统的主要职责划分吗？",
            ],
        )
        + "\n\n% === 图解占位 ===\n"
        + "% 【图 1：最简心智模型】三方块图，节点 ≤3\n"
        + "% 【图 2：核心拆解】分层架构图，节点 ≤6\n"
        + "% 【表 1：关键边界】边界 | 左侧 | 右侧\n",
    ),
    (
        "02-background-and-motivation.tex",
        placeholder_section(
            "section",
            "背景、冲突与本项目的回答",
            "用 SCQA 结构说明为何要做这件事。SCQA 压缩到 1 页以内，用痛点-回答对照图替代大段文字。",
            [
                "现状、冲突、问题、回答分别是什么？",
                "本项目不解决什么？",
                "为什么此刻必须做？",
            ],
        )
        + "\n\n% === 表格占位 ===\n"
        + "% 【表 1：痛点-回答对照】痛点 | Ares 回答\n",
    ),
    (
        "03-terms-and-prerequisites.tex",
        placeholder_section(
            "section",
            "术语表、符号表与前置知识",
            "给出被后文依赖的所有关键术语、符号、缩写与前置知识。术语表应使用 \\textbf{} 或 description 环境标记首次定义。",
            [
                "哪些术语在后文首次出现前必须已被定义？",
                "哪些符号、缩写、角色标签要在同一表格中列齐？",
                "哪些前置知识应只提示入门资料而不展开？",
            ],
        ),
    ),
    (
        "04-system-architecture.tex",
        placeholder_section(
            "section",
            "系统架构",
            "结论先行：系统拆为 N 层，每层职责一句话。先给总览图（层 0），再按层级展开细节图（层 1）。",
            [
                "系统拆为哪几层？每层的一句话职责是什么？",
                "总览图应展示什么（≤3 个顶层节点）？",
                "各层细节图应展示什么（每图 ≤6 个节点）？",
                "层间数据流如何标注？",
            ],
        )
        + "\n\n% === 金字塔结构占位 ===\n"
        + "% 【结论句】系统拆为 N 层：接入层负责...，执行层负责...，持久层负责...。\n"
        + "% === 图解占位 ===\n"
        + "% 【图 1：系统总览】三方块图：外部参与者 → 系统 → 外部依赖\n"
        + "% 【图 2：Web 层架构】节点 ≤6\n"
        + "% 【图 3：API 层架构】节点 ≤6\n"
        + "% 【图 4：Worker 层架构】节点 ≤6\n"
        + "% 【图 5：数据层架构】节点 ≤6\n"
        + "% 【表 1：层间接口】层级 A | 层级 B | 接口类型 | 数据格式\n",
    ),
    (
        "05-core-module-design.tex",
        placeholder_section(
            "section",
            "核心模块设计",
            "每个模块：治理思想（一句话本质）→ 架构图 → 组件职责表 → 接口契约 → 时序图 → 设计决策。",
            [
                "每个模块的治理思想（一句话定义本质）是什么？",
                "模块内部如何 MECE 分解为组件？",
                "每个组件的职责边界和关键技术是什么？",
                "模块对外提供哪些接口（输入/输出/错误码）？",
                "模块与外部交互的主流程时序是什么？",
                "关键设计决策有哪些，备选方案为何被排除？",
            ],
        )
        + "\n\n% === 模块模板占位（复制此结构为每个模块） ===\n"
        + "% \\subsection{[模块名] 模块}\n"
        + "% \\textbf{治理思想}：[一句话定义模块本质]\n\n"
        + "% 【图 X：模块架构图】组件 ≤6 个\n\n"
        + "% 【表 X：组件职责表】组件 | 职责边界 | 关键技术\n\n"
        + "% 【表 X：接口契约表】接口 | 输入 | 输出 | 错误码\n\n"
        + "% 【图 X：交互时序图】参与者 ≤6\n\n"
        + "% 【表 X：设计决策表】决策 | 选择 | 备选 | 理由\n",
    ),
    (
        "06-core-workflow.tex",
        placeholder_section(
            "section",
            "核心流程",
            "每个流程：结论（一句话输出）→ 时序图 → 步骤表 → 异常分支。超过 3 句的流程描述必须替换为图。",
            [
                "每个流程的核心输出是什么（一句话结论）？",
                "正常流程的时序是什么（参与者 ≤6）？",
                "每个步骤的输入、输出、负责模块是什么？",
                "异常分支有哪些，触发条件和处理策略是什么？",
            ],
        )
        + "\n\n% === 流程模板占位（复制此结构为每个流程） ===\n"
        + "% \\subsection{[流程名]}\n"
        + "% \\textbf{结论}：该流程将...转换为...，关键输出是...\n\n"
        + "% 【图 X：正常流程时序图】\n\n"
        + "% 【表 X：步骤表】步骤 | 参与者 | 动作 | 输出\n\n"
        + "% 【图 X：异常分支流程图】\n\n"
        + "% 【表 X：异常表】异常 | 触发条件 | 处理策略\n",
    ),
    (
        "07-interfaces-and-contracts.tex",
        placeholder_section(
            "section",
            "接口契约与数据模型",
            "数据流图 → 字段定义表 → 状态机图 → 错误码表。禁止纯字段罗列，必须先说明设计原则。",
            [
                "核心数据流如何贯穿各层（数据流图）？",
                "每个数据实体的字段、类型、约束是什么（表格）？",
                "实体状态如何转换（状态机图）？",
                "错误码如何分类，客户端如何处理（表格）？",
            ],
        )
        + "\n\n% === 图解占位 ===\n"
        + "% 【图 X：核心数据流图】从输入到持久化的完整数据流转\n"
        + "% 【表 X：数据模型表】实体 | 关键字段 | 类型 | 约束\n"
        + "% 【图 X：状态机图】关键实体的状态转换\n"
        + "% 【表 X：错误码表】错误码 | 含义 | 触发场景 | 客户端处理\n",
    ),
    (
        "08-environment-and-setup.tex",
        placeholder_section(
            "section",
            "环境搭建与工具使用",
            "依赖清单 → 一键命令 → 验证步骤。命令块占位符必须显式标记。",
            [
                "需要哪些工具？版本范围是什么？从哪里获取？",
                "需要哪些凭证？作用域、申请路径、有效期是什么？",
                "环境搭建命令是否可从上到下复制运行？",
            ],
        )
        + "\n\n% === 表格占位 ===\n"
        + "% 【表 X：依赖清单】工具 | 版本 | 用途\n"
        + "% 【表 X：凭证清单】凭证 | 作用域 | 申请路径 | 有效期\n",
    ),
    (
        "09-implementation-walkthrough.tex",
        placeholder_section(
            "section",
            "最小 Hello World 与首次上手走查",
            "给出一个可复现的最小样例：目标、输入、操作步骤、预期输出、验证方式。",
            [
                "最小能跑通的样例是什么？",
                "预期输出如何对比？",
                "若输出不符，读者应如何逐步定位？",
            ],
        ),
    ),
    (
        "10-testing-and-acceptance.tex",
        placeholder_section(
            "section",
            "测试、验收标准与 DoD",
            "给出每个交付单元的 DoD（可判定句）、核心测试类型、边界情况。",
            [
                "每个交付单元的 DoD 是否写成了可判定句？",
                "单元、集成、验收三层测试的关注点分别是什么？",
                "边界情况和失败模式有没有被覆盖？",
            ],
        ),
    ),
    (
        "11-common-pitfalls.tex",
        placeholder_section(
            "section",
            "常见误解与首次踩坑",
            "列出新读者最容易踩的坑、典型误解与对应的自检方法，尽量与 `08` 和 `09` 的操作场景对齐。",
            [
                "读者第一次尝试时最可能卡在哪一步？",
                "有哪些误解会让实现走偏？",
                "每个坑对应的自检方式是什么？",
            ],
        ),
    ),
    (
        "12-project-progress.tex",
        placeholder_section(
            "section",
            "项目进度",
            "集中记录当前基线、已完成、进行中、阻塞与下一检查点。",
            [
                "当前已经确认完成了什么？",
                "哪些仍属于 design intent，还没落进 repo？",
                "下一检查点与证据来源是什么？",
            ],
        )
        + "\n\n% === 表格占位 ===\n"
        + "% 【表 X：进度表】类别 | 内容 | 证据\n",
    ),
    (
        "13-risks-and-next-steps.tex",
        placeholder_section(
            "section",
            "风险、局限与下一步",
            "说明主要风险、已知局限、后续动作与交付边界。",
            [
                "最大技术或组织风险是什么？",
                "哪些判断仍待证据？",
                "下一步 1--3 个动作是什么，依赖哪一节的结论？",
            ],
        )
        + "\n\n% === 表格占位 ===\n"
        + "% 【表 X：运行就绪矩阵】组件 | source-of-truth | owner | interface boundary | runbook / rollback | compatibility bridge retirement\n"
        + "% 【表 X：风险矩阵】风险 | 概率 | 影响 | 应对 | 兜底\n",
    ),
]

SECTION_SPECS["executor-handbook"] = EXECUTOR_HANDBOOK_SPECS


RESEARCH_PRD_SPECS: list[tuple[str, str]] = [
    (
        "00-executive-summary.tex",
        (
            "\\chapter{标题页与执行摘要}\n\n"
            "\\noindent\\textit{结论句占位：本 Research PRD 用 What / Why / How / Expected Impact / Key Metrics 概括研究程序，并明确哪些内容是 design intent，哪些需要后续实验验证。}\n\n"
            "\\section{电梯演讲}\n\n"
            "\\begin{table}[H]\n\\centering\n\\caption{What / Why / How / So What 摘要表}\n"
            "\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y}\n\\toprule\n维度 & 待填内容 \\\\\n\\midrule\n"
            "What & 待填：研究对象与核心问题。 \\\\\nWhy & 待填：科学价值、应用价值与缺口。 \\\\\nHow & 待填：核心方法、数据与验证路径。 \\\\\nSo What & 待填：预期影响与输出。 \\\\\n"
            "\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
            "\\begin{figure}[H]\n\\centering\n\\begin{tikzpicture}[node distance=1.2cm]\n"
            "\\node[reportnode] (problem) {Research\\\\Problem};\n"
            "\\node[reportprocess, right=of problem] (method) {Method};\n"
            "\\node[reportprocess, right=of method] (eval) {Evidence\\\\Gate};\n"
            "\\node[reportnode, right=of eval] (impact) {Expected\\\\Impact};\n"
            "\\draw[reportarrow] (problem) -- (method);\n\\draw[reportarrow] (method) -- (eval);\n\\draw[reportarrow] (eval) -- (impact);\n"
            "\\end{tikzpicture}\n\\caption{Research PRD 总览图：说明研究问题、方法、证据门禁与预期影响之间的主链路。}\n\\end{figure}\n"
        ),
    ),
    (
        "01-background-and-gap.tex",
        placeholder_section(
            "chapter",
            "背景、文献综述与 Gap Analysis",
            "用最近关键工作、未解决问题和研究意义说明为什么本研究值得做。",
            ["现有工作解决了什么？", "仍然没有解决什么？", "本文机会在哪里？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Gap Analysis：现有工作、未解决问题与机会。}\n\\begin{tabularx}{\\textwidth}{L{0.24\\textwidth}Y Y}\n\\toprule\n现有工作 & 未解决的问题 & 本研究机会 \\\\\n\\midrule\n待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "02-objectives-rqs-hypotheses.tex",
        placeholder_section(
            "chapter",
            "研究目标、Research Questions 与可证伪假设",
            "把目标、RQ、Hypotheses 和 Success Metrics 写成可测、可证伪、可停止的结构。",
            ["Primary / Secondary Objectives 是什么？", "每个假设如何被证伪？", "成功指标如何测量？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Research Questions 与可证伪假设。}\n\\begin{tabularx}{\\textwidth}{L{0.14\\textwidth}Y Y Y}\n\\toprule\n编号 & Research Question / Hypothesis & 证伪条件 & 验证方法 \\\\\n\\midrule\nRQ1 / H1 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Success Metrics：指标、测量方式、基线与目标。}\n\\begin{tabularx}{\\textwidth}{L{0.2\\textwidth}Y Y Y}\n\\toprule\n指标 & 测量方式 & 基线 & 目标 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "03-scope-assumptions-constraints.tex",
        placeholder_section(
            "chapter",
            "范围、边界、假设与约束",
            "明确 In-Scope / Out-of-Scope，并把关键假设写成可监控风险。",
            ["本期明确做什么？", "本期明确不做什么？", "假设失效时如何停止或降级？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Assumptions \\& Constraints。}\n\\begin{tabularx}{\\textwidth}{L{0.24\\textwidth}Y Y Y}\n\\toprule\n假设 / 约束 & 来源 & 若失效的影响 & 监控方式 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "04-methodology-and-technical-route.tex",
        placeholder_section(
            "chapter",
            "方法论与技术路线",
            "给出整体研究设计、数据来源、工具方法、Pilot / Feasibility 分析。",
            ["整体研究设计如何闭环？", "数据从哪里来？", "可行性如何先验证？"],
        )
        + "\n\n\\begin{figure}[H]\n\\centering\n\\begin{tikzpicture}[node distance=1.2cm]\n\\node[reportnode] (data) {Data};\n\\node[reportprocess, right=of data] (method) {Method};\n\\node[reportprocess, right=of method] (pilot) {Pilot};\n\\node[reportnode, right=of pilot] (evidence) {Evidence};\n\\draw[reportarrow] (data) -- (method);\n\\draw[reportarrow] (method) -- (pilot);\n\\draw[reportarrow] (pilot) -- (evidence);\n\\end{tikzpicture}\n\\caption{研究设计框架图：从数据到方法、可行性验证和证据输出。}\n\\end{figure}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{数据来源与预处理。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y Y}\n\\toprule\n数据类型 & 来源 & 规模 & 预处理 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "05-formulation-and-algorithm.tex",
        placeholder_section(
            "chapter",
            "数学建模、算法与推导",
            "按定义、公式、推导、正确性或局限分析组织形式化内容。",
            ["核心变量是什么？", "算法输入输出是什么？", "公式的适用条件是什么？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{算法接口：输入、输出、失败条件。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y}\n\\toprule\n项目 & 内容 \\\\\n\\midrule\n输入 & 待填 \\\\\n输出 & 待填 \\\\\n失败条件 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "06-experimental-design.tex",
        placeholder_section(
            "chapter",
            "实验设计、基线与消融",
            "定义实验设置、代表性基线、评估指标与单变量消融。",
            ["实验设置是否可复现？", "baseline 是否公平？", "每个 ablation 是否只改变一个变量？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Baseline Matrix。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y Y}\n\\toprule\n方法 & 指标 & 数据划分 / 公平性 & 结论 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Ablation Matrix。}\n\\begin{tabularx}{\\textwidth}{L{0.22\\textwidth}Y Y Y}\n\\toprule\n消融项 & 单一变量变化 & 预期影响 & 观测结果 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Reproducibility Table。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y}\n\\toprule\n字段 & 必填内容 \\\\\n\\midrule\nrandom seed & 待填 \\\\\n数据划分 & 待填 \\\\\n配置 & 待填 \\\\\n硬件 & 待填 \\\\\n运行命令 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "07-results-evidence-and-failures.tex",
        placeholder_section(
            "chapter",
            "结果、Evidence Ledger 与失败案例",
            "先标记 planned / observed evidence，再解释结果；禁止把未运行实验写成事实。",
            ["哪些 claim 已有证据？", "哪些只是 planned evidence？", "负结果如何影响主张？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Evidence Ledger：claim -> evidence -> source -> limitation -> confidence。}\n\\begin{tabularx}{\\textwidth}{L{0.2\\textwidth}Y Y Y L{0.14\\textwidth}}\n\\toprule\nClaim & Evidence & Source & Limitation & Confidence \\\\\n\\midrule\n待填 & planned / observed 待填 & 待填 & 待填 & low / medium / high \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Failure-case Table。}\n\\begin{tabularx}{\\textwidth}{L{0.2\\textwidth}Y Y Y}\n\\toprule\n失败条件 & 观察行为 & 对主张的影响 & 下一步验证 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "08-project-progress.tex",
        placeholder_section(
            "chapter",
            "项目进度",
            "集中记录 repo-observed fact：当前基线、已完成、进行中、阻塞与下一检查点。",
            ["哪些已经真实完成？", "证据路径是什么？", "下一步需要什么产物？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{项目进度表。}\n\\begin{tabularx}{\\textwidth}{L{0.16\\textwidth}Y Y}\n\\toprule\n类别 & 内容 & 证据 \\\\\n\\midrule\n基线 & 待填 & 待填 \\\\\n已完成 & 待填 & 待填 \\\\\n阻塞 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "09-resources-timeline-risk-ethics.tex",
        placeholder_section(
            "chapter",
            "资源、时间线、风险伦理与 Go / No-Go",
            "定义团队、预算、里程碑、风险、伦理与停止条件。",
            ["谁负责什么？", "资源是否现实？", "何时 Go / No-Go？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Go / No-Go Gate。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y}\n\\toprule\nGate & Go 条件 & No-Go / 降级条件 \\\\\n\\midrule\nG1 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{风险与伦理矩阵。}\n\\begin{tabularx}{\\textwidth}{L{0.24\\textwidth}L{0.12\\textwidth}L{0.12\\textwidth}Y}\n\\toprule\n风险 / 伦理项 & 概率 & 影响 & 缓解策略 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "10-impact-monitoring-and-appendices.tex",
        placeholder_section(
            "chapter",
            "预期产出、影响、监测与附录",
            "定义论文、数据集、原型、传播计划、监测机制与附录入口。",
            ["最终产出是什么？", "影响如何衡量？", "哪些细节放入附录？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Expected Outputs and Impact Plan。}\n\\begin{tabularx}{\\textwidth}{L{0.22\\textwidth}Y Y}\n\\toprule\n输出 & 衡量方式 & 传播 / 交付路径 \\\\\n\\midrule\n待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
]


ENGINEERING_PRD_SPECS: list[tuple[str, str]] = [
    (
        "00-executive-summary.tex",
        placeholder_section(
            "chapter",
            "执行摘要、Vibe Pitch 与 Success Metrics",
            "用 Vibe Pitch、核心价值和 Success Metrics 说明这个工程项目要交付什么。",
            ["产品给人的感觉是什么？", "用户获得什么？", "成功如何衡量？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{核心价值矩阵。}\n\\begin{tabularx}{\\textwidth}{L{0.24\\textwidth}Y}\n\\toprule\n价值维度 & 具体描述 \\\\\n\\midrule\n用户获得什么 & 待填 \\\\\n解决什么痛点 & 待填 \\\\\n区别在哪里 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "01-problem-opportunity-user-stories.tex",
        placeholder_section(
            "chapter",
            "问题、机会与用户故事",
            "定义用户痛点、当前 workaround、机会窗口和关键用户故事。",
            ["用户痛点是什么？", "为什么现在值得做？", "核心用户故事是什么？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{用户痛点与机会窗口。}\n\\begin{tabularx}{\\textwidth}{L{0.2\\textwidth}Y Y}\n\\toprule\n痛点 & 当前 workaround & 代价 / 机会 \\\\\n\\midrule\n待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "02-goals-and-non-goals.tex",
        placeholder_section(
            "chapter",
            "Goals \\& Non-Goals",
            "明确本期必须实现和明确不做的内容，防止范围蔓延。",
            ["P0 goals 是什么？", "Non-Goals 是什么？", "每个 goal 如何验收？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Goals。}\n\\begin{tabularx}{\\textwidth}{L{0.12\\textwidth}Y L{0.16\\textwidth}Y}\n\\toprule\n编号 & 目标 & 优先级 & 验收标准 \\\\\n\\midrule\nG1 & 待填 & P0 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Non-Goals。}\n\\begin{tabularx}{\\textwidth}{L{0.12\\textwidth}Y Y}\n\\toprule\n编号 & 非目标 & 原因 / 未来时机 \\\\\n\\midrule\nNG1 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "03-personas-and-journeys.tex",
        placeholder_section(
            "chapter",
            "用户画像与关键场景",
            "用 personas、happy path、异常分支和边界场景定义体验。",
            ["谁使用？", "核心 happy path 是什么？", "主要异常分支是什么？"],
        )
        + "\n\n\\begin{figure}[H]\n\\centering\n\\begin{tikzpicture}[node distance=1.2cm]\n\\node[reportnode] (user) {User};\n\\node[reportprocess, right=of user] (action) {Action};\n\\node[reportprocess, right=of action] (system) {System\\\\Response};\n\\node[reportnode, right=of system] (value) {Value};\n\\draw[reportarrow] (user) -- (action);\n\\draw[reportarrow] (action) -- (system);\n\\draw[reportarrow] (system) -- (value);\n\\end{tikzpicture}\n\\caption{关键用户旅程图：从用户动作到系统响应和价值结果。}\n\\end{figure}\n",
    ),
    (
        "04-system-and-technical-architecture.tex",
        placeholder_section(
            "chapter",
            "技术栈、系统架构与 Agent Rules",
            "定义技术栈、架构总览、分层边界和 AI Agent 实现规则。",
            ["技术栈是什么？", "系统如何分层？", "Agent 生成代码时必须遵守什么？"],
        )
        + "\n\n\\begin{figure}[H]\n\\centering\n\\begin{tikzpicture}[node distance=1.2cm]\n\\node[reportnode] (web) {Web / UI};\n\\node[reportprocess, right=of web] (api) {API};\n\\node[reportprocess, right=of api] (worker) {Worker};\n\\node[reportnode, right=of worker] (data) {Data};\n\\draw[reportarrow] (web) -- (api);\n\\draw[reportarrow] (api) -- (worker);\n\\draw[reportarrow] (worker) -- (data);\n\\end{tikzpicture}\n\\caption{系统架构总览图：展示主要层级和依赖方向。}\n\\end{figure}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Tech Stack。}\n\\begin{tabularx}{\\textwidth}{L{0.16\\textwidth}Y Y}\n\\toprule\n层级 & 技术 / 版本 & 选择理由 \\\\\n\\midrule\n待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "05-functional-requirements.tex",
        placeholder_section(
            "chapter",
            "功能需求与模块化设计",
            "每个模块包含一句话本质、架构图、组件表、功能清单、Acceptance Criteria、接口契约、时序图和设计决策。",
            ["模块如何拆分？", "每个功能如何验收？", "模块接口和依赖是什么？"],
        )
        + "\n\n% 当 --module-source auto 启用时，本章会被 repo 模块扫描结果替换为模块级 PRD 草图。\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Acceptance Criteria 总表。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y}\n\\toprule\n功能 ID & Acceptance Criteria & 验证方式 \\\\\n\\midrule\nAC-1 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "06-non-functional-requirements.tex",
        placeholder_section(
            "chapter",
            "非功能需求",
            "定义性能、安全、可扩展性、可靠性、编码标准和可观测性。",
            ["P95 / 可用性目标是什么？", "安全边界是什么？", "编码和测试标准是什么？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{NFR Matrix。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y}\n\\toprule\n类别 & 指标 & 目标 / 测量方式 \\\\\n\\midrule\n性能 & 待填 & 待填 \\\\\n安全 & 待填 & 待填 \\\\\n可靠性 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "07-data-interfaces-and-contracts.tex",
        placeholder_section(
            "chapter",
            "数据模型、接口契约与错误语义",
            "用数据流图、字段表、状态机和错误码表定义实现边界。",
            ["核心数据如何流动？", "接口输入输出是什么？", "错误和状态如何处理？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{接口契约表。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y Y}\n\\toprule\n接口 & 输入 & 输出 & 错误语义 \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "08-testing-acceptance-and-release.tex",
        placeholder_section(
            "chapter",
            "测试、验收与发布计划",
            "定义测试矩阵、验收场景、DoD、发布门禁和回滚条件。",
            ["什么测试必须过？", "验收场景是什么？", "发布失败如何回滚？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{测试与验收矩阵。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y}\n\\toprule\n测试层级 & 场景 & 验收标准 \\\\\n\\midrule\n单元测试 & 待填 & 待填 \\\\\n集成测试 & 待填 & 待填 \\\\\n验收测试 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "09-project-progress.tex",
        placeholder_section(
            "chapter",
            "项目进度",
            "集中记录 repo-observed fact：当前基线、已完成、进行中、阻塞和下一检查点。",
            ["当前真实完成什么？", "证据路径是什么？", "下一检查点是什么？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{项目进度表。}\n\\begin{tabularx}{\\textwidth}{L{0.16\\textwidth}Y Y}\n\\toprule\n类别 & 内容 & 证据 \\\\\n\\midrule\n基线 & 待填 & 待填 \\\\\n已完成 & 待填 & 待填 \\\\\n阻塞 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
    (
        "10-roadmap-risks-and-operations.tex",
        placeholder_section(
            "chapter",
            "路线图、风险与运行就绪",
            "定义 phased MVP roadmap、风险矩阵和 Operational Readiness Matrix。",
            ["短周期 roadmap 如何安排？", "最大风险是什么？", "运行责任和回滚路径是什么？"],
        )
        + "\n\n\\begin{table}[H]\n\\centering\n\\caption{Operational Readiness Matrix。}\n\\begin{tabularx}{\\textwidth}{L{0.18\\textwidth}Y Y Y}\n\\toprule\n组件 & source-of-truth / owner & interface boundary & runbook / rollback / bridge retirement \\\\\n\\midrule\n待填 & 待填 & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n"
        + "\\begin{table}[H]\n\\centering\n\\caption{Phased MVP Roadmap。}\n\\begin{tabularx}{\\textwidth}{L{0.14\\textwidth}Y Y}\n\\toprule\n阶段 & 目标 & 验收证据 \\\\\n\\midrule\nMVP & 待填 & 待填 \\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table}\n",
    ),
]


SECTION_SPECS = {
    "research-prd": RESEARCH_PRD_SPECS,
    "engineering-prd": ENGINEERING_PRD_SPECS,
}


def slugify(text: str) -> str:
    normalized = text.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or f"report-{date.today().strftime('%Y%m%d')}"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def fill_template(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def extract_heading(body: str) -> str:
    match = HEADING_PATTERN.search(body)
    return match.group(1).strip() if match else "未命名章节"


def build_outline(section_specs: list[tuple[str, str]]) -> str:
    lines = ["# 报告大纲", ""]
    for index, (_, body) in enumerate(section_specs, start=1):
        lines.append(f"{index}. {extract_heading(body)}")
    lines.extend(
        [
            "",
            "## 金字塔结构检查",
            "",
            "- 每章开头是否有明确结论句？",
            "- 支撑结论的要点是否 MECE（相互独立、完全穷尽）？",
            "- 细节是否按层次展开，而非一次性堆砌？",
            "- 是否有无结论支撑的细节罗列？",
            "",
            "## 图解覆盖率检查",
            "",
            "- 系统架构章节是否有总览图 + 各层细节图？",
            "- 每个模块介绍是否有架构图 + 组件职责表？",
            "- 跨模块交互是否有时序图？",
            "- 核心流程是否有流程图或时序图？",
            "- 接口契约是否有数据流图？",
            "- 每张图前是否有引导（说明图回答什么问题）？",
            "- 每张图后是否有结论（说明读者应带走什么判断）？",
            "- 是否有与主题无关的装饰性图表？",
            "- 是否有超过 9 个节点的过度拥挤图？",
            "",
            "## 信息密度检查",
            "",
            "- 是否清理了低信息密度句式（`不是……而是……`、`真正重要的不是……`）？",
            "- 是否有纯描述性段落（无判断）？",
            "- 术语表已定义的概念是否在正文中重复解释？",
            "- SCQA 背景是否压缩到 1 页以内？",
            "- 是否有超过 8 句的段落？",
            "- 显式分点是否使用了 `itemize` / `enumerate` + `\\item`？",
            "",
            "## 模块级细节检查",
            "",
            "- 每个模块是否有一句话本质定义（治理思想）？",
            "- 每个模块是否有组件职责表？",
            "- 每个模块是否有接口契约？",
            "- 每个模块是否有设计决策说明？",
            "",
            "## 编译与一致性检查",
            "",
            "- 是否检查了 XeLaTeX 编译 warning？",
            "- 是否生成并查看了 `build/compile-review.md`？",
            "- 是否生成并查看了 `build/self-check.md`？",
            "- 摘要、术语、图注、表头和正文口径是否一致？",
        ]
    )
    return "\n".join(lines) + "\n"


def build_section_order(section_specs: list[tuple[str, str]]) -> str:
    lines = ["% Auto-generated section include file. Re-generated by render_report.py.", ""]
    for filename, _ in section_specs:
        lines.append(f"\\input{{sections/{Path(filename).stem}.tex}}")
    lines.append("")
    return "\n".join(lines)


def write_yaml_file(path: Path, payload: dict[str, object]) -> None:
    write_file(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_execution_manifest_scaffold(report_dir: Path, report_type: str, title: str, topic: str) -> None:
    (report_dir / "tasks").mkdir()
    (report_dir / "harness").mkdir()
    (report_dir / "evidence").mkdir()

    manifests: dict[str, str] = {
        "task_graph": "tasks/task_graph.yaml",
        "harness": "harness/harness.yaml",
        "evidence": "evidence/evidence_manifest.yaml",
    }
    if report_type == "research-prd":
        (report_dir / "experiments").mkdir()
        manifests["experiments"] = "experiments/experiment_manifest.yaml"

    write_yaml_file(
        report_dir / "report.manifest.yaml",
        {
            "schema_version": "1.0",
            "report_id": report_dir.name,
            "report_type": report_type,
            "title": title,
            "topic": topic,
            "status": "scaffold",
            "source": {
                "latex": "main.tex",
                "markdown": "../report.md",
                "pdf": "../report.pdf",
            },
            "manifests": manifests,
            "execution_readiness": {
                "state": "not_ready",
                "reason": "Populate concrete module, task, harness, and evidence contracts through report-update --mode deep-spec.",
            },
        },
    )
    write_yaml_file(
        report_dir / "tasks" / "task_graph.yaml",
        {
            "schema_version": "1.0",
            "status": "scaffold",
            "gates": [],
            "tasks": [],
            "placeholder_policy": {
                "no_fake_tasks": True,
                "next_step": "Use report-update --mode deep-spec to add real task contracts before report-goal execution.",
            },
        },
    )
    write_yaml_file(
        report_dir / "harness" / "harness.yaml",
        {
            "schema_version": "1.0",
            "status": "scaffold",
            "harnesses": [],
            "mock_policy": {
                "allowed_for_unit_or_smoke": True,
                "forbidden_for_final_or_research_claim": True,
            },
        },
    )
    write_yaml_file(
        report_dir / "evidence" / "evidence_manifest.yaml",
        {
            "schema_version": "1.0",
            "status": "scaffold",
            "evidence_items": [],
            "integrity_policy": {
                "forbidden_final_evidence_kinds": ["mock", "toy", "synthetic", "cached", "stub", "proxy"],
                "required_links": ["task_id", "harness_id", "artifact_path", "command", "git_commit"],
            },
        },
    )
    if report_type == "research-prd":
        write_yaml_file(
            report_dir / "experiments" / "experiment_manifest.yaml",
            {
                "schema_version": "1.0",
                "status": "scaffold",
                "claims": [],
                "experiments": [],
                "mock_policy": {
                    "allowed_for_smoke_test": True,
                    "allowed_for_claim_evidence": False,
                },
            },
        )


def create_workspace(
    report_dir: Path,
    title: str,
    topic: str,
    report_type: str,
    audience: str,
    author: str,
    project_root: Path | None = None,
    module_source: str = "auto",
    diagram_depth: str = "draft",
) -> None:
    if report_type not in SECTION_SPECS:
        allowed = ", ".join(sorted(SECTION_SPECS))
        raise ValueError(
            f"Unsupported report_type '{report_type}'. The report family now supports only: {allowed}."
        )
    section_specs = list(SECTION_SPECS[report_type])
    modules = default_module_specs()
    if report_type == "engineering-prd":
        modules = resolve_module_specs(project_root, module_source)
        section_specs = maybe_specialize_executor_sections(section_specs, modules, diagram_depth)

    report_dir.mkdir(parents=True, exist_ok=False)
    (report_dir / "sections").mkdir()
    (report_dir / "figures").mkdir()
    (report_dir / "build").mkdir()

    replacements = {
        "__TITLE__": title,
        "__SUBTITLE__": "",
        "__AUTHOR__": author,
        "__DATE__": date.today().isoformat(),
        "__REPORT_TYPE__": report_type,
        "__AUDIENCE__": audience,
        "__TOPIC__": topic,
        "__DECISION_GATES_REF__": str(REFERENCE_DIR / "decision-gates.md"),
        "__EXECUTOR_STYLE_REF__": str(REFERENCE_DIR / "executor-report-style.md"),
        "__ANTI_PATTERNS_REF__": str(REFERENCE_DIR / "anti-patterns.md"),
        "__PROGRESS_POLICY_REF__": str(REFERENCE_DIR / "progress-chapter-policy.md"),
        "__MENTAL_MODEL_CHECKLIST_REF__": str(REFERENCE_DIR / "mental-model-checklist.md"),
        "__IMPLEMENTATION_READINESS_REF__": str(REFERENCE_DIR / "implementation-readiness-checklist.md"),
        "__RESEARCH_EVIDENCE_REF__": str(REFERENCE_DIR / "research-evidence-checklist.md"),
        "__OPERATIONAL_READINESS_REF__": str(REFERENCE_DIR / "operational-readiness-checklist.md"),
        "__READING_PATH_MAP_REF__": str(REFERENCE_DIR / "reading-path-map.md"),
        "__PROGRESSIVE_DISCLOSURE_REF__": str(REFERENCE_DIR / "progressive-disclosure.md"),
        "__FULL_REPORT_TEMPLATE_REF__": str(REFERENCE_DIR / "full-report-template.md"),
        "__REPORT_STRUCTURES_REF__": str(REFERENCE_DIR / "report-structures.md"),
        "__DIAGRAM_GUIDE_REF__": str(REFERENCE_DIR / "diagram-guide.md"),
    }

    write_file(
        report_dir / "metadata.yaml",
        fill_template((TEMPLATE_DIR / "metadata.yaml").read_text(), replacements),
    )
    write_file(
        report_dir / "brief.yaml",
        fill_template((TEMPLATE_DIR / "brief.yaml").read_text(), replacements),
    )
    write_file(report_dir / "outline.md", build_outline(section_specs))
    write_file(
        report_dir / "sources.md",
        build_sources(modules, report_type, module_source),
    )
    write_file(
        report_dir / "sources.bib",
        "% Add BibTeX entries here when formal citations are needed.\n",
    )
    write_file(
        report_dir / "figures" / "README.md",
        "# Figures\n\n- 这套 report family 默认追求图文并茂；架构、流程、协议、机制、实验等高密度内容应优先配图。\n- 最终成稿优先使用 TikZ / PGFPlots，使图形保持矢量、可编辑、与正文字体一致。\n- Mermaid 适合作为 brainstorming 或快速草图；若要进入最终 PDF，通常应转成 TikZ 定稿图。\n- 一张图只回答一个核心问题；如果图已经承载多个主结论，应拆成总览图 + 细节图。\n- 图前写用途，图后写结论；表格优先压缩定义、对比、证据与检查清单。\n- 每次调整图表后，都应重新查看 `build/compile-review.md` 与 `build/self-check.md`。\n",
    )

    shutil.copy2(STYLE_TEX, report_dir / "style.tex")
    write_file(report_dir / "main.tex", fill_template(MAIN_TEX_TEMPLATE, replacements))
    write_file(report_dir / "build" / "section-order.tex", build_section_order(section_specs))

    for filename, content in section_specs:
        write_file(report_dir / "sections" / filename, normalize_top_level_heading(content))

    if report_type == "engineering-prd":
        write_module_figures(report_dir, modules, diagram_depth)

    write_execution_manifest_scaffold(report_dir, report_type, title, topic)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a reusable LaTeX report workspace.")
    parser.add_argument(
        "report_dir",
        nargs="?",
        help="Optional explicit path to the report workspace. If omitted, use <project-root>/docs/report/<slug>.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used when report_dir is omitted. Default: current directory.",
    )
    parser.add_argument("--slug", help="Optional report folder name when report_dir is omitted. Default: slugified title.")
    parser.add_argument("--title", required=True, help="Report title.")
    parser.add_argument("--topic", default="", help="Short topic description.")
    parser.add_argument(
        "--type",
        dest="report_type",
        choices=sorted(SECTION_SPECS),
        default="research-prd",
        help="PRD structure to generate. Supported values: research-prd or engineering-prd.",
    )
    parser.add_argument(
        "--audience",
        choices=["students", "engineers", "mixed", "rookie"],
        default="mixed",
        help="Primary audience. Use `rookie` for engineering-prd onboarding depth.",
    )
    parser.add_argument(
        "--module-source",
        choices=["auto", "template"],
        default="auto",
        help="Module source for engineering-prd functional requirements. `auto` scans the repo; `template` emits a fixed template.",
    )
    parser.add_argument(
        "--diagram-depth",
        choices=["draft", "placeholder"],
        default="draft",
        help="Diagram depth for engineering-prd module design. `draft` emits compilable TikZ drafts.",
    )
    parser.add_argument("--author", default="Codex", help="Author name for metadata.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.report_dir:
        report_dir = Path(args.report_dir).resolve()
    else:
        project_root = Path(args.project_root).resolve()
        slug = args.slug or slugify(args.title)
        report_dir = project_root / "docs" / "report" / slug

    if report_dir.exists():
        print(f"[ERROR] Report workspace already exists: {report_dir}")
        return 1

    topic = args.topic or args.title
    create_workspace(
        report_dir=report_dir,
        title=args.title,
        topic=topic,
        report_type=args.report_type,
        audience=args.audience,
        author=args.author,
        project_root=Path(args.project_root).resolve(),
        module_source=args.module_source,
        diagram_depth=args.diagram_depth,
    )
    print(f"[OK] Created LaTeX report workspace: {report_dir}")
    print("[OK] This is a fixed semi-empty template. Use report-brainstorming before report-update when the writing direction is still unsettled.")
    print("[OK] Next step: review brief.yaml defaults, fill sections/*.tex after user confirmation, then run render_report.py to emit report.pdf and report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
