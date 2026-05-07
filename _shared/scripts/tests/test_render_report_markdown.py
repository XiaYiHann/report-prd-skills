#!/usr/bin/env python3
"""Tests for Markdown export in the report renderer."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from render_report import export_markdown, latex_to_markdown  # noqa: E402


class LatexToMarkdownTests(unittest.TestCase):
    def test_common_report_latex_is_converted_to_readable_markdown(self) -> None:
        source = (
            "\\section{执行摘要}\n"
            "本节给出\\textbf{核心判断}与\\emph{证据边界}。\n\n"
            "\\begin{itemize}\n"
            "\\item 第一项\n"
            "\\item 第二项包含 \\reportchg{旧口径}{新口径}\n"
            "\\end{itemize}\n\n"
            "\\begin{enumerate}\n"
            "\\item 跑测试\n"
            "\\end{enumerate}\n\n"
            "新增：\\reportadd{确认事实} 删除：\\reportdel{预测}。\n"
            "如 \\cref{fig:arch} 所示。\n"
            "\\noindent\\emph{占位结论。}\n"
            "\\begin{figure}\n"
            "\\begin{tikzpicture}\n"
            "\\node (a) {A};\n"
            "\\end{tikzpicture}\n"
            "\\caption{机制图}\n"
            "\\end{figure}\n"
            "\\begin{xltabular}{\\textwidth}{L{0.2\\textwidth}Y}\n"
            "列一 & 列二 \\\\\n"
            "A & B \\\\\n"
            "\\end{xltabular}\n"
        )

        markdown = latex_to_markdown(source)

        self.assertIn("## 执行摘要", markdown)
        self.assertIn("**核心判断**", markdown)
        self.assertIn("*证据边界*", markdown)
        self.assertIn("- 第一项", markdown)
        self.assertIn("- 第二项包含 ~~旧口径~~ **新口径**", markdown)
        self.assertIn("1. 跑测试", markdown)
        self.assertIn("**确认事实**", markdown)
        self.assertIn("~~预测~~", markdown)
        self.assertIn("图/表 fig:arch", markdown)
        self.assertIn("*占位结论。*", markdown)
        self.assertIn("**图/表：机制图**", markdown)
        self.assertIn("| 列一 | 列二 |", markdown)
        self.assertNotIn("\\section", markdown)
        self.assertNotIn("\\reportchg", markdown)
        self.assertNotIn("\\noindent", markdown)
        self.assertNotIn("\\node", markdown)
        self.assertNotIn("L{0.2", markdown)

    def test_report_label_macro_is_converted_to_markdown_emphasis(self) -> None:
        markdown = latex_to_markdown("\\rptlabel{Audit 约束}：必须先闭合证据门禁。\n")

        self.assertIn("**Audit 约束**：必须先闭合证据门禁。", markdown)
        self.assertNotIn("\\rptlabel", markdown)

    def test_longtable_control_tokens_are_removed_from_markdown(self) -> None:
        source = (
            "\\begin{longtable}[]{@{}ll@{}}\n"
            "\\toprule\\noalign{}\n"
            "Claim & Evidence \\\\\n"
            "\\midrule\\noalign{}\n"
            "\\endhead\n"
            "\\bottomrule\\noalign{}\n"
            "\\endlastfoot\n"
            "Token & gap artifact \\\\\n"
            "\\end{longtable}\n"
        )

        markdown = latex_to_markdown(source)

        self.assertIn("| Claim | Evidence |", markdown)
        self.assertIn("| Token | gap artifact |", markdown)
        self.assertNotIn("\\noalign", markdown)
        self.assertNotIn("\\endhead", markdown)
        self.assertNotIn("\\endlastfoot", markdown)


class MarkdownExportTests(unittest.TestCase):
    def test_export_markdown_uses_metadata_title_and_sorted_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "report"
            (report_dir / "sections").mkdir(parents=True)
            (report_dir / "metadata.yaml").write_text('title: "双产物报告"\n')
            (report_dir / "sections" / "02-method.tex").write_text("\\section{方法}\n方法内容。\n")
            (report_dir / "sections" / "01-summary.tex").write_text("\\section{摘要}\n摘要内容。\n")

            output_path = Path(tmp) / "docs" / "report.md"
            exported = export_markdown(report_dir, output_path)
            markdown = output_path.read_text()

            self.assertEqual(exported, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("# 双产物报告", markdown)
            self.assertLess(markdown.index("## 摘要"), markdown.index("## 方法"))
            self.assertIn("摘要内容。", markdown)
            self.assertIn("方法内容。", markdown)


class ReportFamilyContractDocsTests(unittest.TestCase):
    def test_primary_skill_docs_name_both_rendered_artifacts(self) -> None:
        skill_root = SCRIPT_DIR.parents[3]
        docs = [
            skill_root / "report" / "SKILL.md",
            skill_root / "report-init" / "SKILL.md",
            skill_root / "report-update" / "SKILL.md",
            skill_root / "report-audit" / "SKILL.md",
            skill_root / "report-brainstorming" / "SKILL.md",
            skill_root / "report-debate" / "SKILL.md",
        ]

        for doc_path in docs:
            text = doc_path.read_text()
            self.assertIn("report.pdf", text, msg=doc_path.name)
            self.assertIn("report.md", text, msg=doc_path.name)


if __name__ == "__main__":
    unittest.main()
