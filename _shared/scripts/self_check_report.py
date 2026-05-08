#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from manifest_validator import validate_execution_manifests


SECTION_HEADING_PATTERN = re.compile(r"\\(?:chapter|section|subsection)\{([^}]+)\}")
PLACEHOLDER_PATTERN = re.compile(r"本节待填")
REPO_FACT_PATTERN = re.compile(r"(当前仓库|当前实现|现有代码|代码库|\brepo\b|代码路径)", re.IGNORECASE)
REPO_FACT_SKIP_LINE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*\\report(add|del|chg)\b"),
    re.compile(r"\\(node|draw|path|fill)\["),
    re.compile(r"^\s*\\item\s*\\report(add|del|chg)\b"),
]
REPO_FACT_SKIP_CONTENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"&"),  # table rows contain &
]
IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9._/-]{2,}\b")
TERMS_SECTION_HEADING_PATTERN = re.compile(r"术语|符号表|terms?|prerequisites?", re.IGNORECASE)
TERMS_SECTION_STEM_PREFIXES = ("03-terms", "terms-and-prerequisites", "03-terms-and-notation")
CJK_RANGE = r"\u4e00-\u9fff"
CJK_BOLD_TERM_PATTERN = re.compile(r"\\textbf\{([^}]*[" + CJK_RANGE + r"][^}]*)\}")
CJK_ITEM_BRACKET_PATTERN = re.compile(r"\\item\[([^\]]*[" + CJK_RANGE + r"][^\]]*)\]")
FLOAT_LABEL_PATTERN = re.compile(r"\\label\{((?:fig|tab|table|figure):[^}]+)\}")
FLOAT_REF_PATTERN = re.compile(r"\\(?:ref|cref|Cref|autoref|vref|eqref)\{([^}]+)\}")
VISUAL_KEYWORDS = (
    "架构",
    "框架",
    "流程",
    "工作流",
    "协议",
    "机制",
    "算法",
    "模块边界",
    "系统",
    "实验",
    "结果",
    "pipeline",
    "workflow",
    "architecture",
    "framework",
    "protocol",
)
LATEX_VISUAL_PATTERN = re.compile(
    r"\\begin\{(?:figure|table|longtable|tikzpicture|axis)\}|\\includegraphics|\\begin\{tabularx?\}|\\begin\{longtable\}"
)
TIKZ_PATTERN = re.compile(r"\\begin\{tikzpicture\}|\\begin\{axis\}|\\input\{figures/[^}]+\.tex\}")
MERMAID_PATTERN = re.compile(r"```mermaid|\\input\{figures/[^}]+\.mmd\}|\.mmd", re.IGNORECASE)
MODULE_SUBSECTION_PATTERN = re.compile(r"\\subsection\{([^}]*模块[^}]*)\}")
MODULE_SECTION_PATTERN = re.compile(r"\\section\{([^}]*模块[^}]*)\}")
RESEARCH_MARKERS = re.compile(
    r"\b(hypothesis|baseline|ablation|experiment|metric|methodology)\b|假设|基线|消融|实验|指标|方法",
    re.IGNORECASE,
)
ENGINEERING_MARKERS = re.compile(
    r"\b(api|architecture|deploy|runbook|rollback|worker|service|interface)\b|架构|接口|部署|回滚|运维|模块|服务",
    re.IGNORECASE,
)
PSEUDO_LIST_PATTERN = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)")
LOW_DENSITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("对照否定句", re.compile(r"(?:并)?不是[^。\n]{0,48}而是")),
    ("空泛强调句", re.compile(r"真正(?:重要|决定|关注|关键|难点)[^。\n]{0,24}(?:不是|不在)")),
    ("空转换述", re.compile(r"换句话说[，,]?")),
    ("模糊转义句", re.compile(r"从某种意义上说")),
    ("空泛本质句", re.compile(r"本质上(?=[^。\n]{0,24})")),
]
IDENTIFIER_STOPWORDS = {
    "chapter",
    "section",
    "subsection",
    "textwidth",
    "textit",
    "paragraph",
    "begin",
    "end",
    "centering",
    "caption",
    "arraybackslash",
    "raggedright",
    "documentclass",
    "input",
    "tableofcontents",
    "maketitle",
    "clearpage",
    "text",
}
# Normalized identifiers that are intentionally allowed to have multiple forms
# (e.g. kebab-case for prose vs camelCase for code references)
VARIANT_ALLOWLIST_NORMALIZED = {"fanout", "signaldelivery"}
STRUCTURAL_LABELS = {
    "一句话定位",
    "核心判断",
    "阅读路径",
    "速览后应带走的最小判断",
    "精读后应能完成的第一件事",
    "结论",
    "职责",
    "信号流",
    "读模型流",
    "治理思想",
    "边界",
    "左侧",
    "右侧",
    "左侧职责",
    "右侧职责",
    "本阶段实现",
    "痛点",
    "Ares 回答",
    "对应章节",
    "现状",
    "冲突",
    "问题",
    "回答",
    "边界声明",
    "为什么此刻必须做",
    "决策与执行分离",
    "事件优先于请求",
    "读写分离",
    "风控是执行主路径的阻塞点",
    "当前限定沙盒",
    "脚本拼接",
    "追踪断裂",
    "安全补丁化",
    "信号生成者与执行者职责不清",
    "风险控制与执行主路径竞争",
    "不做策略研究",
    "不做真实资金交易",
    "不做高频交易优化",
    "不替代交易所",
    "幂等优先",
    "状态不可绕过",
    "错误分层",
}


def _read_latex_braced_argument(text: str, start: int) -> tuple[str, int] | None:
    if start >= len(text) or text[start] != "{":
        return None

    depth = 0
    buffer: list[str] = []
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            if depth >= 1:
                buffer.append(char)
                buffer.append(text[index + 1])
            index += 2
            continue
        if char == "{":
            depth += 1
            if depth > 1:
                buffer.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(buffer), index + 1
            if depth > 0:
                buffer.append(char)
        elif depth >= 1:
            buffer.append(char)
        index += 1
    return None


def strip_report_preview_deletions(text: str) -> str:
    """Return the report preview text that should count as current prose."""
    output: list[str] = []
    index = 0
    commands = {
        "\\reportadd": "keep-first",
        "\\reportdel": "drop-first",
        "\\reportchg": "keep-second",
    }

    while index < len(text):
        matched_command = None
        for command in commands:
            if text.startswith(command, index):
                matched_command = command
                break
        if matched_command is None:
            output.append(text[index])
            index += 1
            continue

        mode = commands[matched_command]
        cursor = index + len(matched_command)
        first = _read_latex_braced_argument(text, cursor)
        if first is None:
            output.append(text[index])
            index += 1
            continue
        first_arg, cursor = first

        if mode == "keep-first":
            output.append(first_arg)
            index = cursor
            continue
        if mode == "drop-first":
            index = cursor
            continue

        second = _read_latex_braced_argument(text, cursor)
        if second is None:
            output.append(text[index])
            index += 1
            continue
        second_arg, cursor = second
        output.append(second_arg)
        index = cursor

    return "".join(output)


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    location: str | None = None


def load_section_texts(report_dir: Path) -> list[tuple[Path, str]]:
    section_dir = report_dir / "sections"
    files = sorted(section_dir.glob("*.tex"))
    if not files:
        raise RuntimeError(f"No section files found in {section_dir}")
    return [(path, path.read_text()) for path in files]


def extract_heading(text: str, fallback: str) -> str:
    match = SECTION_HEADING_PATTERN.search(text)
    return match.group(1).strip() if match else fallback


def non_comment_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        body = raw_line.split("%", 1)[0].strip()
        if body:
            lines.append(body)
    return lines


def non_comment_paragraphs(text: str) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    buffer: list[str] = []
    start_line: int | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        body = raw_line.split("%", 1)[0].strip()
        if not body:
            if buffer and start_line is not None:
                paragraphs.append((start_line, " ".join(buffer)))
                buffer = []
                start_line = None
            continue
        if start_line is None:
            start_line = line_number
        buffer.append(body)

    if buffer and start_line is not None:
        paragraphs.append((start_line, " ".join(buffer)))
    return paragraphs


def is_placeholder_only(text: str) -> bool:
    lines = [line for line in non_comment_lines(text) if not line.startswith(("\\chapter{", "\\section{", "\\subsection{"))]
    if not lines:
        return True
    if all(PLACEHOLDER_PATTERN.search(line) for line in lines):
        return True
    return False


def collect_structure_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    section_texts = load_section_texts(report_dir)
    progress_sections: list[str] = []
    placeholder_sections: list[str] = []

    for path, text in section_texts:
        heading = extract_heading(text, path.name)
        if "项目进度" in heading or "project-progress" in path.stem:
            progress_sections.append(heading)
        if is_placeholder_only(text):
            placeholder_sections.append(heading)

    if not progress_sections:
        findings.append(Finding("error", "structure", "缺少 `项目进度` 章节。"))

    for heading in placeholder_sections:
        findings.append(Finding("info", "template", f"章节仍为模板占位状态：{heading}"))

    return findings


def collect_low_density_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in load_section_texts(report_dir):
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            body = strip_report_preview_deletions(raw_line.split("%", 1)[0])
            if not body.strip():
                continue
            if PSEUDO_LIST_PATTERN.search(body):
                findings.append(
                    Finding(
                        "warn",
                        "style",
                        f"检测到伪列表，请改用 LaTeX 列表环境和 \\item：{body.strip()}",
                        f"{path.name}:{line_number}",
                    )
                )
            for label, pattern in LOW_DENSITY_PATTERNS:
                if pattern.search(body):
                    snippet = body.strip()
                    findings.append(
                        Finding(
                            "warn",
                            "style",
                            f"{label}：{snippet}",
                            f"{path.name}:{line_number}",
                        )
                    )
        for line_number, paragraph in non_comment_paragraphs(strip_report_preview_deletions(text)):
            if paragraph.startswith(("\\chapter{", "\\section{", "\\subsection{")):
                continue
            inline_order_markers = ["第一，", "第二，", "第三，", "第四，"]
            inline_observation_markers = ["其一，", "其二，"]
            if sum(marker in paragraph for marker in inline_order_markers) >= 2:
                findings.append(
                    Finding(
                        "warn",
                        "style",
                        f"行内顺序分点：已分点内容仍被压在同一自然段中，建议改成总括句后接 itemize / enumerate + \\item：{paragraph}",
                        f"{path.name}:{line_number}",
                    )
                )
            if sum(marker in paragraph for marker in inline_observation_markers) >= 2:
                findings.append(
                    Finding(
                        "warn",
                        "style",
                        f"行内观察点分点：已分点内容仍被压在同一自然段中，建议改成总括句后接 itemize / enumerate + \\item：{paragraph}",
                        f"{path.name}:{line_number}",
                    )
                )
    return findings


def collect_repo_leakage_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path, text in load_section_texts(report_dir):
        heading = extract_heading(text, path.name)
        if "项目进度" in heading or "project-progress" in path.stem:
            continue
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            body = raw_line.split("%", 1)[0]
            if not body.strip():
                continue
            if any(p.search(body) for p in REPO_FACT_SKIP_LINE_PATTERNS):
                continue
            if any(p.search(body) for p in REPO_FACT_SKIP_CONTENT_PATTERNS):
                continue
            if REPO_FACT_PATTERN.search(body):
                findings.append(
                    Finding(
                        "warn",
                        "repo-fact",
                        f"非 `项目进度` 章节出现仓库现状表述：{body.strip()}",
                        f"{path.name}:{line_number}",
                    )
                )
    return findings


def section_needs_visual(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in VISUAL_KEYWORDS)


def section_has_visual(text: str) -> bool:
    return bool(LATEX_VISUAL_PATTERN.search(text))


def collect_visual_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    section_texts = load_section_texts(report_dir)
    non_placeholder_sections = 0
    tikz_figures = 0

    for path, text in section_texts:
        heading = extract_heading(text, path.name)
        placeholder = is_placeholder_only(text)
        if not placeholder:
            non_placeholder_sections += 1
        if TIKZ_PATTERN.search(text):
            tikz_figures += 1
        if placeholder:
            continue
        if section_needs_visual(text) and not section_has_visual(text):
            findings.append(
                Finding(
                    "warn",
                    "visual",
                    f"该章节涉及架构、流程、机制或实验，但尚未包含图表：{heading}",
                    path.name,
                )
            )

    if non_placeholder_sections > 0 and tikz_figures == 0:
        findings.append(
            Finding(
                "warn",
                "visual",
                "报告正文尚未包含 TikZ / PGFPlots 图。若这是最终成稿，应补至少一张 TikZ 图。",
            )
        )

    return findings


def collect_module_design_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    section_path = report_dir / "sections" / "05-core-module-design.tex"
    if not section_path.exists():
        return findings

    text = section_path.read_text()
    if "\\input{figures/module-overview.tex}" not in text and "\\input{figures/module-topology.tex}" not in text and "模块总览图" not in text and "模块拓扑" not in text:
        findings.append(
            Finding(
                "warn",
                "module-design",
                "核心模块设计缺少模块总览图：请先说明总体模块框架、依赖方向与 I/O 边界。",
                section_path.name,
            )
        )

    matches = list(MODULE_SUBSECTION_PATTERN.finditer(text))
    if not matches:
        # Fallback: some reports use \section{} for module names (e.g., "Signal Delivery 模块")
        matches = list(MODULE_SECTION_PATTERN.finditer(text))
    if not matches:
        findings.append(
            Finding(
                "warn",
                "module-design",
                "核心模块设计缺少模块 subsection：请为每个核心模块单独展开设计。",
                section_path.name,
            )
        )
        return findings

    required_markers: list[tuple[str, tuple[str, ...], str]] = [
        ("架构图", ("模块架构图", "-architecture.tex", "architecture", "tikzpicture"), "模块架构图"),
        ("组件职责表", ("组件职责表", "组件职责", "职责边界", "components"), "组件职责表"),
        ("接口契约表", ("接口契约表", "接口契约", "核心接口", "输入 & 输出", "接口 | 输入 | 输出"), "接口契约表"),
        ("时序图/交互流程", ("交互时序图", "交互流程", "-sequence.tex", "sequence"), "时序图"),
        ("设计决策表", ("设计决策表", "设计决策", "备选", "decisions"), "设计决策表"),
    ]

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        heading = match.group(1)
        for _, markers, label in required_markers:
            if not any(marker in block for marker in markers):
                findings.append(
                    Finding(
                        "warn",
                        "module-design",
                        f"{heading} 缺少{label}。",
                        section_path.name,
                    )
                )
    return findings


def _joined_section_text(report_dir: Path) -> str:
    return "\n".join(text for _, text in load_section_texts(report_dir))


def report_type(report_dir: Path) -> str:
    brief_path = report_dir / "brief.yaml"
    if not brief_path.exists():
        return ""
    text = brief_path.read_text(errors="ignore")
    match = re.search(r"report_type:\s*['\"]?([^'\"\n]+)", text)
    return match.group(1).strip() if match else ""


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def collect_research_evidence_findings(report_dir: Path) -> list[Finding]:
    current_type = report_type(report_dir)
    if current_type in {"engineering-prd"}:
        return []
    text = _joined_section_text(report_dir)
    if current_type != "research-prd" and not RESEARCH_MARKERS.search(text):
        return []

    checks: list[tuple[str, tuple[str, ...], str]] = [
        (
            "research-prd",
            ("Research Questions", "研究问题", "RQ1"),
            "Research PRD 缺少 Research Questions：请明确核心 RQ。",
        ),
        (
            "research-prd",
            ("可证伪假设", "Hypotheses", "证伪条件"),
            "Research PRD 缺少可证伪假设：请写出预期结果、证伪条件与验证方法。",
        ),
        (
            "research-evidence",
            ("claim -> evidence -> source -> limitation -> confidence", "证据台账", "evidence ledger"),
            "科研型报告缺少 evidence ledger：请补 `claim -> evidence -> source -> limitation -> confidence` 台账。",
        ),
        (
            "research-evidence",
            ("baseline matrix", "基线矩阵", "baseline 对比"),
            "科研型报告缺少 baseline matrix：请显式记录对比方法、指标与公平性约束。",
        ),
        (
            "research-evidence",
            ("ablation matrix", "消融矩阵", "ablation"),
            "科研型报告缺少 ablation matrix：请说明每个消融只改变哪一个变量。",
        ),
        (
            "research-evidence",
            ("reproducibility table", "可复现性表", "random seed", "随机种子"),
            "科研型报告缺少 reproducibility table：请记录随机种子、数据划分、配置、硬件与运行命令。",
        ),
        (
            "research-evidence",
            ("failure-case table", "失败案例", "failure case", "negative result"),
            "科研型报告缺少 failure-case table：请记录失败案例、负结果和适用边界。",
        ),
        (
            "research-prd",
            ("Go / No-Go", "Go/No-Go", "No-Go"),
            "Research PRD 缺少 Go / No-Go gate：请定义继续、停止或降级条件。",
        ),
        (
            "research-prd",
            ("风险", "伦理", "ethics", "risk"),
            "Research PRD 缺少风险 / 伦理矩阵：请前置风险、伦理与缓解策略。",
        ),
    ]

    findings: list[Finding] = []
    for category, markers, message in checks:
        if not _has_any(text, markers):
            findings.append(Finding("warn", category, message))
    return findings


def collect_operational_readiness_findings(report_dir: Path) -> list[Finding]:
    current_type = report_type(report_dir)
    text = _joined_section_text(report_dir)
    if current_type != "engineering-prd" and not ENGINEERING_MARKERS.search(text):
        return []

    checks: list[tuple[str, tuple[str, ...], str]] = [
        (
            "engineering-prd",
            ("Goals & Non-Goals", "Goals \\& Non-Goals", "Non-Goals", "非目标"),
            "Engineering PRD 缺少 Goals & Non-Goals：请明确本期目标与非目标。",
        ),
        (
            "engineering-prd",
            ("Acceptance Criteria", "验收标准", "AC-"),
            "Engineering PRD 缺少 Acceptance Criteria：每个功能必须有可测试验收标准。",
        ),
        (
            "engineering-prd",
            ("Priority", "优先级", "P0", "P1"),
            "Engineering PRD 缺少 priority：请为目标或功能标注 P0/P1/P2。",
        ),
        (
            "engineering-prd",
            ("Non-functional", "非功能", "NFR", "可靠性", "性能"),
            "Engineering PRD 缺少非功能需求：请覆盖性能、安全、可靠性与编码标准。",
        ),
        (
            "engineering-prd",
            ("接口契约", "数据模型", "错误语义", "interface"),
            "Engineering PRD 缺少接口 / 数据契约：请定义输入输出、状态和错误语义。",
        ),
        (
            "engineering-prd",
            ("测试", "验收", "DoD", "release"),
            "Engineering PRD 缺少测试、验收或发布门禁。",
        ),
        (
            "operational-readiness",
            ("source-of-truth", "source of truth", "真源", "单一真源"),
            "工程型报告缺少 source-of-truth 说明：请标明每个关键状态和数据的可信写入面。",
        ),
        (
            "operational-readiness",
            ("owner", "维护者", "责任归属"),
            "工程型报告缺少 owner / 责任归属：请标明关键组件的维护责任。",
        ),
        (
            "operational-readiness",
            ("runbook", "rollback", "回滚", "故障处置"),
            "工程型报告缺少 runbook / rollback：请说明故障定位、恢复和回滚路径。",
        ),
        (
            "operational-readiness",
            ("interface boundary", "接口边界", "边界契约"),
            "工程型报告缺少 interface boundary：请说明 API、模块和数据契约的边界。",
        ),
        (
            "operational-readiness",
            ("bridge retirement", "退役条件", "compatibility bridge"),
            "工程型报告缺少 compatibility bridge 退役条件：请说明兼容层退出标准。",
        ),
    ]

    findings: list[Finding] = []
    for category, markers, message in checks:
        if not _has_any(text, markers):
            findings.append(Finding("warn", category, message))
    return findings


def collect_execution_manifest_findings(report_dir: Path) -> list[Finding]:
    result = validate_execution_manifests(report_dir)
    findings: list[Finding] = []
    for issue in result.issues:
        findings.append(
            Finding(
                "warn",
                "execution-readiness",
                issue.message,
                issue.location,
            )
        )
    return findings


def normalized_identifier(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def is_terms_section(path: Path, text: str) -> bool:
    stem = path.stem.lower()
    if any(stem.startswith(prefix) for prefix in TERMS_SECTION_STEM_PREFIXES):
        return True
    heading = extract_heading(text, "")
    return bool(TERMS_SECTION_HEADING_PATTERN.search(heading))


def extract_defined_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for match in CJK_BOLD_TERM_PATTERN.finditer(text):
        terms.add(match.group(1).strip())
    for match in CJK_ITEM_BRACKET_PATTERN.finditer(text):
        terms.add(match.group(1).strip())
    return terms


def collect_undefined_terms_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    section_texts = load_section_texts(report_dir)

    defined_terms: set[str] = set()
    has_terms_section = False

    for path, text in section_texts:
        if is_terms_section(path, text):
            has_terms_section = True
            defined_terms |= extract_defined_terms(text)

    if not has_terms_section:
        return findings

    for path, text in section_texts:
        if is_terms_section(path, text):
            continue
        if is_placeholder_only(text):
            continue
        seen_in_file: set[str] = set()
        in_table = False
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            body = raw_line.split("%", 1)[0]
            if not body.strip():
                continue
            # Track table environment boundaries (simple string check for robustness)
            if "\\begin{tabular" in body or "\\begin{longtable}" in body:
                in_table = True
            if "\\end{tabular" in body or "\\end{longtable}" in body:
                in_table = False
            if in_table:
                continue
            for match in CJK_BOLD_TERM_PATTERN.finditer(body):
                term = match.group(1).strip()
                if not term or term in defined_terms or term in seen_in_file or term in STRUCTURAL_LABELS:
                    continue
                seen_in_file.add(term)
                findings.append(
                    Finding(
                        "warn",
                        "terminology",
                        f"术语 `{term}` 在正文被加粗强调，但未出现在术语表的定义集合中。请在术语章节补上首次定义，或核对是否属于不需定义的通用词。",
                        f"{path.name}:{line_number}",
                    )
                )
    return findings


def collect_unreferenced_float_findings(report_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    section_texts = load_section_texts(report_dir)

    labels: dict[str, str] = {}
    refs: set[str] = set()

    for path, text in section_texts:
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            body = raw_line.split("%", 1)[0]
            if not body.strip():
                continue
            for match in FLOAT_LABEL_PATTERN.finditer(body):
                label = match.group(1).strip()
                if label and label not in labels:
                    labels[label] = f"{path.name}:{line_number}"
            for match in FLOAT_REF_PATTERN.finditer(body):
                refs.add(match.group(1).strip())

    for label, location in sorted(labels.items()):
        if label in refs:
            continue
        findings.append(
            Finding(
                "warn",
                "figure-ref",
                f"图表 label `{label}` 未被正文引用。请用 \\ref / \\cref / \\autoref 在正文中至少引用一次，或删除未使用的 label。",
                location,
            )
        )
    return findings


def collect_identifier_variants(report_dir: Path) -> list[Finding]:
    variants: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for _, text in load_section_texts(report_dir):
        text = strip_report_preview_deletions(text)
        for token in IDENTIFIER_PATTERN.findall(text):
            lowered = token.lower()
            if lowered in IDENTIFIER_STOPWORDS or lowered.startswith("label"):
                continue
            normalized = normalized_identifier(token)
            if len(normalized) < 4:
                continue
            variants[normalized][token] += 1

    findings: list[Finding] = []
    for normalized, counter in sorted(variants.items()):
        if normalized in VARIANT_ALLOWLIST_NORMALIZED:
            continue
        raw_variants = [token for token in counter if token.lower() not in {"codex", "latex", "mermaid"}]
        if len(raw_variants) < 2:
            continue
        if len({token.lower() for token in raw_variants}) == 1:
            continue
        display = ", ".join(f"`{token}`×{counter[token]}" for token in sorted(raw_variants)[:5])
        findings.append(
            Finding(
                "warn",
                "consistency",
                f"检测到可能的术语或标识写法漂移：{display}",
            )
        )
    return findings


def collect_compile_review_findings(report_dir: Path) -> list[Finding]:
    review_path = report_dir / "build" / "compile-review.md"
    if not review_path.exists():
        return [Finding("error", "compile-review", "缺少 compile-review.md，编译审查未生成。", "compile-review.md")]

    findings: list[Finding] = []
    in_warning_section = False
    for line_number, raw_line in enumerate(review_path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if line == "## 编译警告":
            in_warning_section = True
            continue
        if line.startswith("## "):
            in_warning_section = False
        if line.startswith("- [WARN]"):
            message = line[len("- [WARN]") :].strip()
            findings.append(Finding("error", "compile-review", f"编译审查 warning 必须清理：{message}", f"compile-review.md:{line_number}"))
            continue
        if in_warning_section and line.startswith("- ") and line != "- 无。":
            message = line[2:].strip()
            if message:
                findings.append(Finding("error", "compile-review", f"编译审查 warning 必须清理：{message}", f"compile-review.md:{line_number}"))
    return findings


def compile_review_summary(report_dir: Path) -> list[str]:
    review_path = report_dir / "build" / "compile-review.md"
    if not review_path.exists():
        return ["[ERROR] 尚未生成 compile review。"]
    warnings = [line.strip() for line in review_path.read_text().splitlines() if line.strip().startswith("- [WARN]")]
    if not warnings:
        return ["compile review 未发现 warning。"]
    return [warning.replace("- [WARN]", "[ERROR]", 1).strip() for warning in warnings[:8]]


def build_report(report_dir: Path, findings: list[Finding]) -> str:
    counts = Counter(finding.severity for finding in findings)
    lines = [
        "# Self Check",
        "",
        f"- 报告工作区: `{report_dir}`",
        f"- error: {counts.get('error', 0)}",
        f"- warn: {counts.get('warn', 0)}",
        f"- info: {counts.get('info', 0)}",
        "",
        "## 编译审查摘要",
        "",
    ]

    for item in compile_review_summary(report_dir):
        lines.append(f"- {item}")

    grouped: defaultdict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.category].append(finding)

    lines.extend(
        [
            "",
            "## 金字塔结构报告",
            "",
            "| 检查项 | 命中数 | 状态 |",
            "| --- | ---: | --- |",
            f"| 结构 / 项目进度 | {len(grouped.get('structure', []))} | {'需处理' if grouped.get('structure') else '通过'} |",
            f"| 模板占位 | {len(grouped.get('template', []))} | {'仍有占位' if grouped.get('template') else '通过'} |",
            "",
            "## 图解覆盖率报告",
            "",
            "| 检查项 | 命中数 | 状态 |",
            "| --- | ---: | --- |",
            f"| 图表 / TikZ / PGFPlots | {len(grouped.get('visual', []))} | {'需补图或说明例外' if grouped.get('visual') else '通过'} |",
            f"| 图表引用 | {len(grouped.get('figure-ref', []))} | {'需补正文引用' if grouped.get('figure-ref') else '通过'} |",
            "",
            "## 信息密度报告",
            "",
            "| 检查项 | 命中数 | 状态 |",
            "| --- | ---: | --- |",
            f"| 低密度句式 / 伪列表 | {len(grouped.get('style', []))} | {'需改写' if grouped.get('style') else '通过'} |",
            f"| 术语漂移 | {len(grouped.get('consistency', []))} | {'需统一' if grouped.get('consistency') else '通过'} |",
            "",
            "## 模块级细节与证据报告",
            "",
            "| 检查项 | 命中数 | 状态 |",
            "| --- | ---: | --- |",
            f"| 科研证据链 | {len(grouped.get('research-evidence', []))} | {'需补证据台账' if grouped.get('research-evidence') else '通过或不适用'} |",
            f"| 工程运行就绪 | {len(grouped.get('operational-readiness', []))} | {'需补运行矩阵' if grouped.get('operational-readiness') else '通过或不适用'} |",
            f"| 执行 manifest / harness | {len(grouped.get('execution-readiness', []))} | {'需补机器合同' if grouped.get('execution-readiness') else '通过或不适用'} |",
            f"| 模块级设计 | {len(grouped.get('module-design', []))} | {'需补模块图表' if grouped.get('module-design') else '通过或不适用'} |",
            f"| Repo 事实外溢 | {len(grouped.get('repo-fact', []))} | {'需收回项目进度' if grouped.get('repo-fact') else '通过'} |",
        ]
    )

    category_titles = {
        "compile-review": "编译审查问题",
        "structure": "结构问题",
        "template": "模板占位提醒",
        "style": "低信息密度句式命中",
        "repo-fact": "仓库现状渗透提醒",
        "visual": "图文并茂与 TikZ 检查",
        "research-evidence": "科研证据链检查",
        "operational-readiness": "工程运行就绪检查",
        "execution-readiness": "执行 manifest 与 harness 检查",
        "module-design": "模块级设计检查",
        "terminology": "术语首次定义检查",
        "figure-ref": "图表引用检查",
        "consistency": "术语与概念一致性提醒",
    }

    for category in [
        "compile-review",
        "structure",
        "template",
        "style",
        "repo-fact",
        "visual",
        "research-evidence",
        "operational-readiness",
        "execution-readiness",
        "module-design",
        "terminology",
        "figure-ref",
        "consistency",
    ]:
        lines.extend(["", f"## {category_titles[category]}", ""])
        items = grouped.get(category, [])
        if not items:
            lines.append("- 无。")
            continue
        for item in items:
            prefix = item.location + " " if item.location else ""
            lines.append(f"- [{item.severity.upper()}] {prefix}{item.message}")

    lines.extend(
        [
            "",
            "## 建议动作",
            "",
            "- 先修复 error；编译审查里的 warning 也按 error 处理，不能作为可发布状态。",
            "- 若命中了低信息密度句式，优先改成直接陈述信息的写法。",
            "- 若一段中已经出现多个小点，优先改成“总括句 + itemize / enumerate + \\item”或分段小点，而不是继续堆叠 `第一，第二，第三`。",
            "- 若命中了伪列表，直接改成 LaTeX 列表环境，不要在 `.tex` 正文里保留 `- `、`* `、`1. ` 这类写法。",
            "- 若 repo 现状扩散到非 `项目进度` 章节，优先把状态事实收回 `项目进度`。",
            "- 若关键章节尚未配图，优先补 TikZ / PGFPlots 图，而不是把结构信息继续压回长段落。",
            "- 若科研证据链缺口存在，先补 claim/evidence/source/limitation/confidence 台账，再补 baseline、ablation、reproducibility 与 failure-case 表。",
            "- 若工程运行就绪缺口存在，先补 source-of-truth、owner、runbook/rollback、接口边界与 compatibility bridge 退役条件。",
            "- 若执行 manifest 或 harness 缺口存在，先用 `report-update --mode deep-spec` 补 task graph、harness command、artifact path 和 evidence link，再生成 implementation goal。",
            "- 若术语存在多种写法，统一摘要、标题、图注、表头和正文中的版本。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report self checks for structure, style, and consistency.")
    parser.add_argument("report_dir", help="Path to the report workspace.")
    parser.add_argument("--output", help="Optional output path. Default: <report_dir>/build/self-check.md")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any error or warning is detected.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        print(f"[ERROR] Report workspace not found: {report_dir}")
        return 1

    findings = []
    findings.extend(collect_compile_review_findings(report_dir))
    findings.extend(collect_structure_findings(report_dir))
    findings.extend(collect_low_density_findings(report_dir))
    findings.extend(collect_repo_leakage_findings(report_dir))
    findings.extend(collect_visual_findings(report_dir))
    findings.extend(collect_research_evidence_findings(report_dir))
    findings.extend(collect_operational_readiness_findings(report_dir))
    findings.extend(collect_execution_manifest_findings(report_dir))
    findings.extend(collect_module_design_findings(report_dir))
    findings.extend(collect_undefined_terms_findings(report_dir))
    findings.extend(collect_unreferenced_float_findings(report_dir))
    findings.extend(collect_identifier_variants(report_dir))

    output_path = Path(args.output).resolve() if args.output else report_dir / "build" / "self-check.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(report_dir, findings))

    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warn")
    if errors:
        print(f"[FAIL] Wrote self check: {output_path}")
        print(f"[FAIL] error={errors}, warn={warnings}, info={sum(1 for finding in findings if finding.severity == 'info')}")
        return 1

    if warnings:
        print(f"[WARN] Wrote self check: {output_path}")
        print(f"[WARN] error=0, warn={warnings}, info={sum(1 for finding in findings if finding.severity == 'info')}")
        if args.strict:
            return 1
        return 0

    print(f"[OK] Wrote self check: {output_path}")
    print("[OK] error=0, warn=0, info=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
