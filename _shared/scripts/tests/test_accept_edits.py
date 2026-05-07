#!/usr/bin/env python3
"""Tests for accept_edits.accept_markup.

Run either of:

    python3 -m pytest _shared/scripts/tests/
    python3 _shared/scripts/tests/test_accept_edits.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from accept_edits import accept_markup, process_report  # noqa: E402


class AcceptMarkupTransformTests(unittest.TestCase):
    def test_reportadd_keeps_content(self) -> None:
        source = r"本节讨论 \reportadd{新方法} 的优势。"
        result = accept_markup(source)
        self.assertEqual(result, "本节讨论 新方法 的优势。")

    def test_reportdel_removes_content(self) -> None:
        source = r"本节讨论 \reportdel{旧方法} 的优势。"
        result = accept_markup(source)
        self.assertEqual(result, "本节讨论  的优势。")

    def test_reportchg_keeps_new(self) -> None:
        source = r"本节讨论 \reportchg{旧方法}{新方法} 的优势。"
        result = accept_markup(source)
        self.assertEqual(result, "本节讨论 新方法 的优势。")

    def test_nested_braces_in_add(self) -> None:
        source = r"本节使用 \reportadd{\textbf{新模型} 与其变体}。"
        result = accept_markup(source)
        self.assertEqual(result, r"本节使用 \textbf{新模型} 与其变体。")

    def test_nested_braces_in_chg(self) -> None:
        source = r"\reportchg{原有 \textit{A} 方案}{改用 \textbf{B} 方案}"
        result = accept_markup(source)
        self.assertEqual(result, r"改用 \textbf{B} 方案")

    def test_multiline_content(self) -> None:
        source = "第一行。\n\\reportadd{新内容\n跨行。}\n结尾。"
        result = accept_markup(source)
        self.assertEqual(result, "第一行。\n新内容\n跨行。\n结尾。")

    def test_multiple_occurrences(self) -> None:
        source = (
            r"\reportadd{A} 和 \reportdel{B}，"
            r"以及 \reportchg{C}{D}。"
        )
        result = accept_markup(source)
        self.assertEqual(result, "A 和 ，以及 D。")

    def test_no_markup_unchanged(self) -> None:
        source = "本节没有任何 diff 宏，应原样返回。\\textbf{正常粗体}"
        self.assertEqual(accept_markup(source), source)

    def test_unbalanced_braces_raises(self) -> None:
        source = r"\reportadd{未闭合"
        with self.assertRaises(ValueError):
            accept_markup(source)

    def test_reportchg_missing_second_arg_raises(self) -> None:
        source = r"\reportchg{只有一个参数}"
        with self.assertRaises(ValueError):
            accept_markup(source)


class ProcessReportTests(unittest.TestCase):
    def _make_sections(self, root: Path, files: dict[str, str]) -> None:
        (root / "sections").mkdir(parents=True)
        (root / "build").mkdir()
        for filename, content in files.items():
            (root / "sections" / filename).write_text(content)

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = r"\section{X}\reportadd{新}."
            self._make_sections(root, {"05-demo.tex": original})
            changed = process_report(root, dry_run=True, backup=False)
            self.assertEqual(changed, ["sections/05-demo.tex"])
            self.assertEqual((root / "sections" / "05-demo.tex").read_text(), original)

    def test_writes_back_and_backs_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = r"\section{X}\reportadd{新} \reportdel{旧}"
            self._make_sections(root, {"05-demo.tex": original})
            changed = process_report(root, dry_run=False, backup=True)
            self.assertEqual(changed, ["sections/05-demo.tex"])
            new_text = (root / "sections" / "05-demo.tex").read_text()
            self.assertIn("新", new_text)
            self.assertNotIn("旧", new_text)
            self.assertNotIn("reportadd", new_text)
            backups = list((root / "build").glob("accept-edits-backup-*"))
            self.assertEqual(len(backups), 1)
            backed_up = (backups[0] / "sections" / "05-demo.tex").read_text()
            self.assertEqual(backed_up, original)

    def test_unchanged_file_not_listed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unchanged = r"\section{X} 没有任何 diff 宏。"
            self._make_sections(root, {"01.tex": unchanged, "02.tex": r"\reportadd{Y}"})
            changed = process_report(root, dry_run=False, backup=False)
            self.assertEqual(changed, ["sections/02.tex"])


if __name__ == "__main__":
    unittest.main()
