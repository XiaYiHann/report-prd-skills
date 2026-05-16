#!/usr/bin/env python3
"""Research update skill tests."""

from __future__ import annotations

import json

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class ResearchUpdateTests(unittest.TestCase):  # noqa: F405
    def test_research_update_verify_passes_after_installer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents" / "skills"
            claude_skills = Path(tmp) / "claude" / "skills"
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(claude_skills)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(Path(tmp) / "project" / ".claude" / "agents")

            install = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--force", "--no-agents"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            verify = subprocess.run(
                [
                    "python3",
                    str(UPDATE_VERIFY_SCRIPT),
                    "--skills-dir",
                    str(target),
                    "--claude-skills",
                    str(claude_skills),
                    "--json",
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            payload = json.loads(verify.stdout)

        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertTrue(payload["ok"])
        self.assertIn("research-update", payload["visible_skills"])
        self.assertEqual(set(payload["visible_skills"]) & {"research-prd", "research-ppt"}, set())
        self.assertFalse(payload["internal_modules"]["research-spec"]["has_skill_md"])

    def test_research_update_verify_fails_on_retired_visible_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents" / "skills"
            claude_root = Path(tmp) / "claude"
            claude_skills = claude_root / "skills"
            target.mkdir(parents=True)
            claude_root.mkdir(parents=True)
            os.symlink(target, claude_skills)
            for name in SKILL_NAMES:
                (target / name).mkdir(parents=True)
                (target / name / "SKILL.md").write_text("---\nname: x\ndescription: x\n---\n", encoding="utf-8")
            for name in INTERNAL_COMPILER_MODULE_NAMES:
                (target / name / "scripts").mkdir(parents=True)
            (target / "research-ppt").mkdir(parents=True)
            (target / "research-ppt" / "SKILL.md").write_text("---\nname: research-ppt\ndescription: old\n---\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "python3",
                    str(UPDATE_VERIFY_SCRIPT),
                    "--skills-dir",
                    str(target),
                    "--claude-skills",
                    str(claude_skills),
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired skill path still exists: research-ppt", result.stdout)
        self.assertIn("unexpected visible research skill: research-ppt", result.stdout)


if __name__ == "__main__":
    unittest.main()
