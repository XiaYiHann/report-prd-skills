#!/usr/bin/env python3
"""Tests for self_check_report extensions.

Run either of:

    python3 -m pytest _shared/scripts/tests/
    python3 _shared/scripts/tests/test_self_check_extensions.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from self_check_report import (  # noqa: E402
    collect_undefined_terms_findings,
    collect_unreferenced_float_findings,
)


def _make_report(root: Path, sections: dict[str, str]) -> Path:
    (root / "sections").mkdir(parents=True)
    for filename, content in sections.items():
        (root / "sections" / filename).write_text(content)
    return root


class UndefinedTermCheckTests(unittest.TestCase):
    def test_undefined_term_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "03-terms-and-prerequisites.tex": (
                        "\\section{术语、符号与前置知识}\n\n"
                        "这里还没有列出调度器。\n"
                    ),
                    "05-core-design.tex": (
                        "\\section{核心设计}\n\n"
                        "\\textbf{协调器} 在本方案中负责分发任务。\n"
                    ),
                },
            )
            findings = collect_undefined_terms_findings(root)
            self.assertTrue(
                any("协调器" in f.message for f in findings),
                msg=f"expected a terminology warn for 协调器, got: {findings}",
            )

    def test_defined_term_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "03-terms-and-prerequisites.tex": (
                        "\\section{术语、符号与前置知识}\n\n"
                        "\\textbf{协调器}：负责分发任务的调度组件。\n"
                    ),
                    "05-core-design.tex": (
                        "\\section{核心设计}\n\n"
                        "\\textbf{协调器} 在本方案中负责分发任务。\n"
                    ),
                },
            )
            findings = collect_undefined_terms_findings(root)
            self.assertFalse(
                any("协调器" in f.message for f in findings),
                msg=f"expected no terminology warn for defined 协调器, got: {findings}",
            )

    def test_no_terms_section_skips_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "05-core-design.tex": (
                        "\\section{核心设计}\n\n"
                        "\\textbf{协调器} 在本方案中负责分发任务。\n"
                    ),
                },
            )
            findings = collect_undefined_terms_findings(root)
            self.assertEqual(findings, [])

    def test_item_bracket_definition_is_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "03-terms-and-prerequisites.tex": (
                        "\\section{术语}\n\n"
                        "\\begin{description}\n"
                        "  \\item[协调器] 负责分发任务的调度组件。\n"
                        "\\end{description}\n"
                    ),
                    "05-core-design.tex": (
                        "\\section{核心设计}\n\n"
                        "\\textbf{协调器} 在本方案中负责分发任务。\n"
                    ),
                },
            )
            findings = collect_undefined_terms_findings(root)
            self.assertFalse(any("协调器" in f.message for f in findings))


class UnreferencedFloatCheckTests(unittest.TestCase):
    def test_unreferenced_figure_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "04-system-architecture.tex": (
                        "\\section{架构}\n\n"
                        "\\begin{figure}\n"
                        "  \\caption{系统架构}\n"
                        "  \\label{fig:arch}\n"
                        "\\end{figure}\n"
                    ),
                },
            )
            findings = collect_unreferenced_float_findings(root)
            self.assertTrue(
                any("fig:arch" in f.message for f in findings),
                msg=f"expected figure-ref warn for fig:arch, got: {findings}",
            )

    def test_referenced_figure_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "04-system-architecture.tex": (
                        "\\section{架构}\n\n"
                        "\\begin{figure}\n"
                        "  \\caption{系统架构}\n"
                        "  \\label{fig:arch}\n"
                        "\\end{figure}\n"
                        "如 \\cref{fig:arch} 所示，系统分三层。\n"
                    ),
                },
            )
            findings = collect_unreferenced_float_findings(root)
            self.assertFalse(
                any("fig:arch" in f.message for f in findings),
                msg=f"expected no figure-ref warn, got: {findings}",
            )

    def test_ref_macro_is_recognized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "04-system-architecture.tex": (
                        "\\section{架构}\n\n"
                        "\\begin{figure}\n"
                        "  \\label{fig:arch}\n"
                        "\\end{figure}\n"
                        "参见图 \\ref{fig:arch}。\n"
                    ),
                },
            )
            findings = collect_unreferenced_float_findings(root)
            self.assertFalse(any("fig:arch" in f.message for f in findings))

    def test_table_label_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "07-interfaces-and-contracts.tex": (
                        "\\section{接口契约}\n\n"
                        "\\begin{table}\n"
                        "  \\label{tab:api}\n"
                        "\\end{table}\n"
                    ),
                },
            )
            findings = collect_unreferenced_float_findings(root)
            self.assertTrue(any("tab:api" in f.message for f in findings))


if __name__ == "__main__":
    unittest.main()
