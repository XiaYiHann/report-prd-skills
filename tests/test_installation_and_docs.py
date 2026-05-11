#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class InstallationAndDocsTests(unittest.TestCase):  # noqa: F405
    def test_install_docs_and_defaults_point_to_research_loop_repo(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        installer = INSTALL_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh", readme)
        self.assertIn("https://github.com/XiaYiHann/research-loop.git", installer)
        self.assertIn("~/.claude/skills", readme)
        self.assertIn(".claude/agents/", readme)
        self.assertIn("--init-workspace", readme)
        self.assertIn("--no-agents", installer)
        self.assertIn("--user-agents", installer)
        self.assertIn("--agents-only", installer)
        self.assertIn("--dry-run", installer)
        self.assertNotIn("raw.githubusercontent.com/XiaYiHann/report-prd-skills", readme)
        self.assertNotIn("https://github.com/XiaYiHann/report-prd-skills.git", installer)

    def test_readme_lists_unified_research_skill_first(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        table_start = readme.index("## 技能列表")
        table = readme[table_start : readme.index("不要新增独立", table_start)]
        rows = [line for line in table.splitlines() if line.startswith("| [`")]

        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(rows[0].startswith("| [`research`](skills/research/SKILL.md)"), rows[0])

    def test_skill_frontmatter_is_standard_yaml(self) -> None:
        for skill_path in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
            text = skill_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), skill_path)
            end = text.find("\n---\n", 4)
            self.assertGreater(end, 0, skill_path)
            metadata = yaml.safe_load(text[4:end])
            self.assertIsInstance(metadata, dict, skill_path)
            self.assertIsInstance(metadata.get("name"), str, skill_path)
            self.assertIsInstance(metadata.get("description"), str, skill_path)

    def test_claude_code_subagent_templates_are_standard_project_agents(self) -> None:
        for agent_name in CLAUDE_RESEARCH_AGENT_NAMES:
            agent_path = CLAUDE_AGENT_TEMPLATES_DIR / f"{agent_name}.md"
            self.assertTrue(agent_path.exists(), agent_name)
            text = agent_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), agent_path)
            end = text.find("\n---\n", 4)
            self.assertGreater(end, 0, agent_path)
            metadata = yaml.safe_load(text[4:end])

            self.assertEqual(metadata.get("name"), agent_name)
            self.assertIsInstance(metadata.get("description"), str, agent_path)
            self.assertIn("Use", metadata["description"], agent_path)
            self.assertIsInstance(metadata.get("tools"), str, agent_path)
            self.assertIn("Read", metadata["tools"], agent_path)
            self.assertEqual(metadata.get("model"), "sonnet", agent_path)
            self.assertIn(f"# {agent_name}", text[end + len("\n---\n") :], agent_path)
            self.assertNotIn("agent_registry.yaml", text)

    def test_research_paper_policy_forbids_plausible_mock_numeric_values(self) -> None:
        skill_text = (REPO_ROOT / "skills" / "research-paper" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("placeholder-complete manuscript", skill_text)
        for forbidden in [
            "complete mock-data manuscript",
            "reasonable mock values",
            "may contain mock values",
            "0.852",
        ]:
            self.assertNotIn(forbidden, skill_text)

    def test_research_explore_skill_exists_and_defines_boundaries(self) -> None:
        skill_path = REPO_ROOT / "skills" / "research-explore" / "SKILL.md"
        self.assertTrue(skill_path.exists())
        skill_text = skill_path.read_text(encoding="utf-8")

        self.assertIn("/research explore --mode literature", skill_text)
        self.assertIn("It must not", skill_text)
        self.assertIn("modify `RESEARCH_DIRECTION.md`", skill_text)
        self.assertIn("Do not fabricate citations", skill_text)

    def test_research_insight_skill_exists_and_retires_legacy_path(self) -> None:
        skill_path = REPO_ROOT / "skills" / "research-insight" / "SKILL.md"
        self.assertTrue(skill_path.exists())
        skill_text = skill_path.read_text(encoding="utf-8")

        self.assertIn("Interpretation Contract", skill_text)
        self.assertIn("Epoch wiki is the current source for durable insight", skill_text)
        self.assertIn("Legacy `docs/research/insights/insight_log.md` is compatibility storage only", skill_text)
        self.assertIn("Do not promote legacy insight to current claim evidence", skill_text)

    def test_readme_documents_git_explore_and_audit_modernization(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Git Memory Layer", readme)
        self.assertIn("Research Explore Skill", readme)
        self.assertIn("Research Insight Skill", readme)
        self.assertIn("Audit Modernization", readme)
        self.assertIn("Explore 负责想", readme)

    def test_installer_installs_skills_and_project_agents_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            project_agents = Path(tmp) / "project" / ".claude" / "agents"
            for old_name in [
                "report-init",
                "report-update",
                "report-audit",
                "report-goal",
                "report-paper",
                "report-spec",
                "report-brainstorming",
                "research-writing",
                "research-evidence",
            ]:
                (target / old_name).mkdir(parents=True)
                (target / old_name / "SKILL.md").write_text("old\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(project_agents)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for skill_name in SKILL_NAMES:
                self.assertTrue((target / skill_name / "SKILL.md").exists(), skill_name)
            self.assertFalse((target / "report" / "SKILL.md").exists())
            for old_name in [
                "report-init",
                "report-update",
                "report-audit",
                "report-goal",
                "report-paper",
                "report-spec",
                "report-brainstorming",
                "research-writing",
                "research-evidence",
            ]:
                self.assertTrue((target / old_name).exists(), f"non-target legacy file should not be deleted: {old_name}")
            self.assertIn("Installed research-loop skills", result.stdout)
            self.assertIn("Installed Claude Code subagents", result.stdout)
            self.assertIn("Next steps:", result.stdout)
            for agent_name in CLAUDE_RESEARCH_AGENT_NAMES:
                self.assertTrue((project_agents / f"{agent_name}.md").exists(), agent_name)

    def test_installer_respects_existing_files_without_force_and_overwrites_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            existing = target / "research"
            existing.mkdir(parents=True)
            (existing / "SKILL.md").write_text("old\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(Path(tmp) / "project" / ".claude" / "agents")

            skipped = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--no-agents"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(skipped.returncode, 0, skipped.stdout + skipped.stderr)
            self.assertEqual((existing / "SKILL.md").read_text(encoding="utf-8"), "old\n")
            self.assertIn("research exists, skipped", skipped.stdout)

            overwritten = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--no-agents", "--force"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(overwritten.returncode, 0, overwritten.stdout + overwritten.stderr)
            self.assertIn("research overwritten", overwritten.stdout)
            self.assertIn("# research", (existing / "SKILL.md").read_text(encoding="utf-8"))

    def test_installer_supports_agents_only_user_agents_and_init_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            user_agents = Path(tmp) / "claude" / "agents"
            project = Path(tmp) / "project"
            project.mkdir()
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_EXECUTION_USER_AGENTS_TARGET_DIR"] = str(user_agents)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--agents-only", "--user-agents", "--init-workspace"],
                cwd=project,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((target / "research" / "SKILL.md").exists())
            for agent_name in CLAUDE_RESEARCH_AGENT_NAMES:
                agent_path = user_agents / f"{agent_name}.md"
                self.assertTrue(agent_path.exists(), agent_name)
                text = agent_path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), agent_path)
                metadata = yaml.safe_load(text[4 : text.find("\n---\n", 4)])
                self.assertEqual(metadata.get("name"), agent_name)
            for dirname in ["prd", "paper", "spec", "plans", "audits", "insights"]:
                self.assertTrue((project / "docs" / "research" / dirname).exists(), dirname)
            self.assertEqual((project / "docs" / "research" / "CURRENT").read_text(encoding="utf-8").strip(), "V0")
            self.assertTrue((project / "docs" / "research" / "RESEARCH_DIRECTION.md").exists())
            self.assertTrue((project / "docs" / "research" / "V0" / "NEXT_ACTION.md").exists())
            self.assertTrue((project / "docs" / "research" / "agent" / "CODEX_GOAL_TEMPLATE.md").exists())
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / "CLAUDE.md").exists())

    def test_installer_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            project_agents = Path(tmp) / "project" / ".claude" / "agents"
            project = Path(tmp) / "project"
            project.mkdir()
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(project_agents)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--dry-run", "--init-workspace"],
                cwd=project,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DRY RUN", result.stdout)
            self.assertIn("would install skill research", result.stdout)
            self.assertIn("would install agent research-math", result.stdout)
            self.assertFalse(target.exists())
            self.assertFalse(project_agents.exists())
            self.assertFalse((project / "docs").exists())
