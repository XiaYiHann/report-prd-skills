#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

import pytest

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

    def test_readme_has_beginner_onboarding_surface(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        start_here = (REPO_ROOT / "START_HERE.md").read_text(encoding="utf-8")
        glossary = (REPO_ROOT / "GLOSSARY.md").read_text(encoding="utf-8")

        self.assertIn("## 新手先读", readme)
        self.assertIn("START_HERE.md", readme)
        self.assertIn("GLOSSARY.md", readme)
        self.assertIn("Direction -> Goal -> Task Queue -> Evidence/Audit -> Wiki/Closeout", readme)
        self.assertIn("先回答四个问题", start_here)
        self.assertIn("Beginner Summary", start_here)
        self.assertIn("## Baseline Lock", glossary)
        self.assertIn("## Evidence Gate", glossary)

    def test_goal_mode_docs_are_version_graph_not_single_next_step(self) -> None:
        docs = "\n".join(
            [
                (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "skills" / "research-goal" / "SKILL.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "skills" / "research-init" / "SKILL.md").read_text(encoding="utf-8"),
            ]
        )

        self.assertIn("task dependency graph", docs)
        self.assertIn("runnable_parallel_set", docs)
        self.assertIn("blocked-branch", docs)
        self.assertIn("Blocked Task Triage Review", docs)
        self.assertIn("code-review-first triage", docs)
        self.assertIn("implementation defect", docs)
        self.assertIn("idea/spec defect", docs)
        self.assertIn("TASK_XXX_blocker.md", docs)
        self.assertIn("正交 runnable tasks", docs)
        self.assertIn("repair-then-execute", docs)
        self.assertIn("latest approved design source", docs)
        self.assertIn("do not stop after a repair-only pass", docs)
        self.assertIn("Subagent Execution Contract", docs)
        self.assertIn("prefer_subagents", docs)
        self.assertIn("优先使用 subagent", docs)
        self.assertIn("main controller remains responsible for state updates", docs)
        for forbidden in [
            "当前下一步",
            "current-next-step",
            "唯一 active task",
            "每轮只能执行",
            "每轮执行只推进",
            "目标必须是完成当前 active task",
        ]:
            self.assertNotIn(forbidden, docs)

    def test_spec_plan_paper_are_documented_as_internal_research_stages(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        research = (REPO_ROOT / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Internal Compiler Pipeline", research)
        self.assertIn("Spec/Plan/Paper can be implicit, but their gates cannot be implicit", research)
        for module_name in INTERNAL_COMPILER_MODULE_NAMES:  # noqa: F405
            self.assertFalse((REPO_ROOT / "skills" / module_name / "SKILL.md").exists(), module_name)
        self.assertFalse((REPO_ROOT / "skills" / "research-prd" / "SKILL.md").exists())
        self.assertTrue((REPO_ROOT / "skills" / "research-spec" / "scripts" / "validate_research.py").exists())
        self.assertTrue((REPO_ROOT / "skills" / "research-plan" / "scripts" / "generate_research_plan.py").exists())
        self.assertTrue((REPO_ROOT / "skills" / "research-paper" / "scripts" / "generate_research_paper.py").exists())
        self.assertIn("内部 compiler module", readme)
        self.assertIn("Spec/Plan/Paper 不再需要用户显式调用", readme)
        self.assertNotIn("旧的分技能仍可手动使用", readme)

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
        policy_text = "\n".join(
            [
                (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
                (REPO_ROOT / "skills" / "research-paper" / "scripts" / "generate_research_paper.py").read_text(encoding="utf-8"),
            ]
        )

        self.assertIn("placeholder-complete manuscript", policy_text)
        for forbidden in [
            "complete mock-data manuscript",
            "reasonable mock values",
            "may contain mock values",
            "0.852",
        ]:
            self.assertNotIn(forbidden, policy_text)

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

    def test_failure_triage_policy_exists_and_defines_research_falsification_boundary(self) -> None:
        path = REPO_ROOT / "docs" / "research" / "agent" / "FAILURE_TRIAGE_POLICY.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "Environment Failure",
            "Execution Failure",
            "Harness Failure",
            "Research Falsification Candidate",
            "Confirmed Research Falsification",
            "Allowed only after adversarial audit",
        ]:
            self.assertIn(phrase, text)

    def test_search_and_reproduction_policy_docs_define_boundaries(self) -> None:
        search = (REPO_ROOT / "docs" / "research" / "agent" / "SEARCH_POLICY.md").read_text(encoding="utf-8")
        reproduction = (REPO_ROOT / "docs" / "research" / "agent" / "REPRODUCTION_POLICY.md").read_text(encoding="utf-8")
        audit = (REPO_ROOT / "docs" / "research" / "agent" / "REPRODUCTION_AUDIT_POLICY.md").read_text(encoding="utf-8")

        self.assertIn("Search is mandatory", search)
        self.assertIn("Absence evidence", search)
        self.assertIn("bounded", search.lower())
        self.assertIn("official_code", reproduction)
        self.assertIn("faithful_reimplementation", reproduction)
        self.assertIn("Environment failure", reproduction)
        self.assertIn("claim_support_level", audit)
        self.assertIn("literature_only", audit)

    def test_readme_documents_gate_aware_terms(self) -> None:
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in ["Gate", "Task", "Harness", "Audit", "Insight"]:
            self.assertIn(phrase, text)
        self.assertIn("failed_execution", text)
        self.assertIn("failed_harness", text)

    def test_readme_documents_search_and_reproduction_gates(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Search and Evidence Acquisition Policy", readme)
        self.assertIn("G0_SEARCH_LOCK", readme)
        self.assertIn("G1_REPRODUCTION_LOCK", readme)
        self.assertIn("reproduction failure", readme.lower())
        self.assertIn("docs/research/Vn/reproduction", readme)
        self.assertIn("reproduction/Vn", readme)

    def test_research_skills_reference_search_and_reproduction_policies(self) -> None:
        research_skill = (REPO_ROOT / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8")
        audit_skill = (REPO_ROOT / "skills" / "research-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("SEARCH_POLICY.md", research_skill)
        self.assertIn("REPRODUCTION_POLICY.md", research_skill)
        self.assertIn("G0_SEARCH_LOCK", research_skill)
        self.assertIn("REPRODUCTION_AUDIT_POLICY.md", audit_skill)
        self.assertIn("claim_support_level", audit_skill)

    def test_docs_and_skills_document_baseline_dossier_lock(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        compiler_code = (REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts" / "research_workspace.py").read_text(encoding="utf-8")
        audit_skill = (REPO_ROOT / "skills" / "research-audit" / "SKILL.md").read_text(encoding="utf-8")
        search_policy = (REPO_ROOT / "docs" / "research" / "agent" / "SEARCH_POLICY.md").read_text(encoding="utf-8")

        for text in [readme, compiler_code, audit_skill, search_policy]:
            self.assertIn("baselines/INDEX.yaml", text)
            self.assertIn("BASELINE_LOCK.yaml", text)

    @pytest.mark.integration
    def test_installer_installs_skills_and_project_agents_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents" / "skills"
            claude_skills = Path(tmp) / "claude" / "skills"
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
                "research-ppt",
            ]:
                (target / old_name).mkdir(parents=True)
                (target / old_name / "SKILL.md").write_text("old\n", encoding="utf-8")
            for module_name in INTERNAL_COMPILER_MODULE_NAMES:  # noqa: F405
                (target / module_name).mkdir(parents=True)
                (target / module_name / "SKILL.md").write_text("old visible skill\n", encoding="utf-8")
            (target / "research-prd").mkdir(parents=True)
            (target / "research-prd" / "SKILL.md").write_text("old visible skill\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(claude_skills)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(project_agents)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--project-agents"],
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
            for module_name in INTERNAL_COMPILER_MODULE_NAMES:  # noqa: F405
                self.assertTrue((target / module_name).exists(), module_name)
                self.assertFalse((target / module_name / "SKILL.md").exists(), module_name)
            self.assertFalse((target / "research-prd").exists())
            self.assertTrue((target / "research-spec" / "scripts" / "validate_research.py").exists())
            self.assertTrue((target / "research-plan" / "scripts" / "generate_research_plan.py").exists())
            self.assertTrue((target / "research-paper" / "scripts" / "generate_research_paper.py").exists())
            self.assertTrue(claude_skills.is_symlink())
            self.assertEqual(os.readlink(claude_skills), str(target))
            self.assertFalse((target / "report" / "SKILL.md").exists())
            for old_name in [
                "report-init",
                "report-update",
                "report-audit",
                "report-goal",
                "report-paper",
                "report-spec",
                "report-brainstorming",
            ]:
                self.assertTrue((target / old_name).exists(), f"non-target legacy file should not be deleted: {old_name}")
            for retired_name in ["research-prd", "research-ppt", "research-writing", "research-evidence"]:
                self.assertFalse((target / retired_name).exists(), retired_name)
            self.assertIn("Installed research-loop skills", result.stdout)
            self.assertIn("Installed internal compiler modules", result.stdout)
            self.assertIn("Installed Claude Code subagents", result.stdout)
            self.assertIn("Next steps:", result.stdout)
            for agent_name in CLAUDE_RESEARCH_AGENT_NAMES:
                self.assertTrue((project_agents / f"{agent_name}.md").exists(), agent_name)

    @pytest.mark.integration
    def test_installer_respects_existing_files_without_force_and_overwrites_with_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            existing = target / "research"
            existing.mkdir(parents=True)
            (existing / "SKILL.md").write_text("old\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(Path(tmp) / "claude-link" / "skills")
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
            self.assertIn("Removing existing research-loop managed skill entries before reinstall", overwritten.stdout)
            self.assertIn("# research", (existing / "SKILL.md").read_text(encoding="utf-8"))

    @pytest.mark.integration
    def test_installer_relinks_claude_skills_to_agents_canonical_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claude_root = Path(tmp) / "claude"
            claude_skills = claude_root / "skills"
            target = Path(tmp) / "agents" / "skills"
            target.mkdir(parents=True)
            claude_root.mkdir(parents=True)
            (claude_skills / "local-only-skill").mkdir(parents=True)
            (claude_skills / "local-only-skill" / "SKILL.md").write_text("keep\n", encoding="utf-8")
            for name in [*SKILL_NAMES, *INTERNAL_COMPILER_MODULE_NAMES, "research-prd", "research-ppt"]:
                (target / name).mkdir(parents=True)
                (target / name / "SKILL.md").write_text("old agents skill\n", encoding="utf-8")
            (claude_skills / "research-ppt").mkdir(parents=True)
            (claude_skills / "research-ppt" / "SKILL.md").write_text("old claude skill\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(claude_skills)
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(Path(tmp) / "project" / ".claude" / "agents")

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--no-agents", "--force"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(claude_skills.is_symlink())
            self.assertEqual(os.readlink(claude_skills), str(target))
            self.assertTrue((target / "local-only-skill" / "SKILL.md").exists())
            for name in SKILL_NAMES:
                self.assertTrue((target / name).exists(), name)
                self.assertTrue((target / name / "SKILL.md").exists(), name)
            for name in INTERNAL_COMPILER_MODULE_NAMES:
                self.assertTrue((target / name).exists(), name)
                self.assertFalse((target / name / "SKILL.md").exists(), name)
            self.assertFalse((target / "research-prd").exists())
            self.assertFalse((target / "research-ppt").exists())
            self.assertIn("Linked", result.stdout)

    @pytest.mark.integration
    def test_installer_supports_agents_only_user_agents_and_init_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            user_agents = Path(tmp) / "claude" / "agents"
            project = Path(tmp) / "project"
            project.mkdir()
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(Path(tmp) / "claude-link" / "skills")
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
            self.assertTrue((project / "docs" / "research" / "agent" / "CODEX_GOAL_TEMPLATE.md").exists())
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / "CLAUDE.md").exists())

    @pytest.mark.integration
    def test_installer_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "claude" / "skills"
            project_agents = Path(tmp) / "project" / ".claude" / "agents"
            project = Path(tmp) / "project"
            project.mkdir()
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)
            env["RESEARCH_LOOP_CLAUDE_SKILLS_DIR"] = str(Path(tmp) / "claude-link" / "skills")
            env["RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR"] = str(project_agents)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT), "--dry-run", "--init-workspace", "--project-agents"],
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
