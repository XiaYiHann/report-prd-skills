#!/usr/bin/env python3
"""Tests for the one-command report skill installer."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "install.sh").exists() or (candidate / "skills" / "report" / "SKILL.md").exists():
            return candidate
    raise RuntimeError(f"cannot resolve repo root from {start}")


REPO_ROOT = _find_repo_root(SCRIPT_DIR)
INSTALL_SCRIPT = REPO_ROOT / "install.sh"
SKILL_NAMES = [
    "report",
    "report-init",
    "report-brainstorming",
    "report-update",
    "report-audit",
    "report-goal",
    "report-paper",
]


class InstallScriptTests(unittest.TestCase):
    def run_installer(self, target: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["REPORT_PRD_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
        env["REPORT_PRD_SKILLS_TARGET_DIR"] = str(target)
        return subprocess.run(
            ["bash", str(INSTALL_SCRIPT)],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_installs_report_skill_family_into_empty_agents_skills_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".agents" / "skills"

            result = self.run_installer(target)

            self.assertEqual(result.returncode, 0, result.stderr)
            for skill_name in SKILL_NAMES:
                self.assertTrue((target / skill_name / "SKILL.md").exists(), f"missing {skill_name}")
            self.assertIn("Installed report skill family", result.stdout)

    def test_replaces_existing_report_skill_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            old_skill = target / "report"
            old_skill.mkdir(parents=True)
            (old_skill / "SKILL.md").write_text("old report skill\n", encoding="utf-8")
            (old_skill / "stale.txt").write_text("must be removed\n", encoding="utf-8")

            result = self.run_installer(target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("name: report", (target / "report" / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((target / "report" / "stale.txt").exists())

    def test_removes_known_obsolete_report_family_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            obsolete = target / "report-debate"
            obsolete.mkdir(parents=True)
            (obsolete / "SKILL.md").write_text("old debate skill\n", encoding="utf-8")

            result = self.run_installer(target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(obsolete.exists())

    def test_pipe_mode_clones_source_without_precloned_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            env = os.environ.copy()
            env.pop("REPORT_PRD_SKILLS_SOURCE_DIR", None)
            env["REPORT_PRD_SKILLS_REPO_URL"] = str(REPO_ROOT)
            env["REPORT_PRD_SKILLS_TARGET_DIR"] = str(target)

            result = subprocess.run(
                ["bash", "-s"],
                input=INSTALL_SCRIPT.read_text(encoding="utf-8"),
                cwd=Path(tmp),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "report" / "SKILL.md").exists())
            self.assertIn("Cloning", result.stderr)


if __name__ == "__main__":
    unittest.main()
