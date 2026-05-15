#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

import re

from research_workflow_helpers import *  # noqa: F403


class EpochResearchLoopTests(unittest.TestCase):  # noqa: F405
    def test_epoch_init_creates_direction_current_agent_docs_and_v0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)

            self.assertTrue((research_dir / "RESEARCH_DIRECTION.md").exists())
            self.assertEqual((research_dir / "CURRENT").read_text(encoding="utf-8").strip(), "V0")
            self.assertTrue((research_dir / "INDEX.md").exists())
            for name in [
                "RUNBOOK.md",
                "CLAUDE_LOOP_PROMPT.md",
                "CODEX_GOAL_TEMPLATE.md",
                "SUBAGENT_POLICY.md",
                "LITERATURE_POLICY.md",
                "GIT_POLICY.md",
            ]:
                self.assertTrue((research_dir / "agent" / name).exists(), name)
            for name in [
                "PRD.tex",
                "PRD_SUMMARY.md",
                "SPEC.yaml",
                "PLAN.md",
                "STATUS.yaml",
                "TASK_QUEUE.yaml",
                "LOOP_LOG.md",
                "GIT_STATE.yaml",
                "git_log.md",
                "closeout.md",
                "PAPER_BINDING_DECISION.md",
            ]:
                self.assertTrue((research_dir / "V0" / name).exists(), name)
            summary = (research_dir / "V0" / "PRD_SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("不是研究真源", summary)
            self.assertTrue((research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml").exists())
            self.assertTrue((research_dir / "V0" / "rqs" / "RQ01" / "PLAN.md").exists())
            self.assertTrue((research_dir / "V0" / "rqs" / "RQ01" / "TASKS.yaml").exists())
            self.assertTrue((research_dir / "V0" / "rqs" / "RQ01" / "reproduction" / "VERIFICATION.yaml").exists())
            for name in [
                "epoch_summary.md",
                "evidence_map.md",
                "positive_signals.md",
                "negative_results.md",
                "failed_paths.md",
                "baseline_landscape.md",
                "literature_notes.md",
                "open_questions.md",
                "next_version_seed.md",
            ]:
                self.assertTrue((research_dir / "V0" / "wiki" / name).exists(), name)
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertTrue((repo / "CLAUDE.md").exists())
            self.assertTrue((research_dir / "explore" / "sessions" / "EXP_0001.md").exists())
            self.assertTrue((research_dir / "explore" / "syntheses" / "EXP_SYNTHESIS.md").exists())
            self.assertTrue((research_dir / "explore" / "proposals" / "LITERATURE_BLOCKER.md").exists())

    def test_epoch_current_and_status_version_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            current = (research_dir / "CURRENT").read_text(encoding="utf-8").strip()
            status = read_yaml(research_dir / current / "STATUS.yaml")

            self.assertEqual(current, "V0")
            self.assertEqual(status["version"], current)
            self.assertEqual(status["status"], "initialized")

    def test_direction_ready_requires_human_approved_or_frozen_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            draft = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "direction-ready"])
            self.assertNotEqual(draft.returncode, 0)
            self.assertIn("human_approved or frozen", draft.stdout)

            approve_research_direction(research_dir)
            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "direction-ready"])
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_epoch_ready_requires_current_epoch_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "PRD.tex").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("V0/PRD.tex", result.stdout)

    def test_loop_ready_requires_single_active_task_and_matching_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            queue["tasks"].append({**queue["tasks"][0], "id": "TASK_002", "status": "active"})
            write_yaml(queue_path, queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "loop-ready"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one active task", result.stdout)

            queue["tasks"] = [queue["tasks"][0]]
            write_yaml(queue_path, queue)

    def test_loop_ready_requires_test_commands_for_code_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["research_questions"] = [{"id": "RQ01", "text": "q1"}]
            spine["claims"] = [{"id": "C1", "rq_id": "RQ01", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": "artifacts/e1.json"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)
            queue = read_yaml(queue_path)
            queue["tasks"][0]["phase"] = "implementation"
            queue["tasks"][0]["allowed_files"] = ["src/module.py"]
            queue["tasks"][0]["test_commands"] = []
            queue["tasks"][0]["research_binding"] = {
                "mode": "spine_bound",
                "rq_id": "RQ01",
                "claim_ids": ["C1"],
                "experiment_ids": ["E1"],
                "evidence_ids": ["EV1"],
                "justification": "implementation task supporting a declared RQ; no result claim is produced before tests pass",
            }
            queue["tasks"][0]["rq_id"] = "RQ01"
            queue["tasks"][0]["rq_spec_ref"] = "rqs/RQ01/SPEC.yaml"
            rq_tasks_path = research_dir / "V0" / "rqs" / "RQ01" / "TASKS.yaml"
            rq_tasks = read_yaml(rq_tasks_path)
            rq_tasks["tasks"][0]["task_id"] = "RQ01_T_IMPL"
            rq_tasks["tasks"][0]["phase"] = "implementation"
            write_yaml(rq_tasks_path, rq_tasks)
            queue["tasks"][0]["rq_task_ref"] = "rqs/RQ01/TASKS.yaml#RQ01_T_IMPL"
            write_yaml(queue_path, queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "loop-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must define test_commands", result.stdout)

    def test_git_memory_templates_are_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            task = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")["tasks"][0]
            closeout = (research_dir / "V0" / "closeout.md").read_text(encoding="utf-8")
            binding = (research_dir / "V0" / "PAPER_BINDING_DECISION.md").read_text(encoding="utf-8")
            git_state = read_yaml(research_dir / "V0" / "GIT_STATE.yaml")

            self.assertIn("git", task)
            self.assertEqual(task["git"]["commit_message"], "research(V0): complete search lock task")
            self.assertIn("## 12. Git Closeout", closeout)
            self.assertIn("## Git Binding", binding)
            self.assertFalse(git_state["commit_policy"]["allow_push"])
            self.assertIn("git push", (research_dir / "agent" / "GIT_POLICY.md").read_text(encoding="utf-8"))

    def test_explore_templates_are_initialized_without_bare_todo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            for path in (research_dir / "explore").rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("TODO", text, path)
            session = (research_dir / "explore" / "sessions" / "EXP_0001.md").read_text(encoding="utf-8")
            self.assertIn("type: explore_session", session)
            self.assertIn("## Web / Literature Findings", session)

    def test_epoch_ready_blocks_v1_before_v0_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V1").mkdir()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot create next version", result.stdout)

    def test_closeout_ready_requires_complete_wiki_and_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            initial = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "closeout-ready"])
            self.assertNotEqual(initial.returncode, 0)
            self.assertIn("final_status", initial.stdout)

            make_epoch_closeout_complete(research_dir)
            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "closeout-ready"])
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_paper_binding_ready_requires_stable_status_and_real_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))

            initial = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])
            self.assertNotEqual(initial.returncode, 0)
            self.assertIn("closed_stable or paper_binding_ready", initial.stdout)

            make_paper_binding_decision(research_dir)
            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_paper_binding_rejects_prompt_only_scaffold_as_result_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
            make_paper_binding_decision(research_dir, artifact_path="prompt_only_scaffold")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("prompt_only_scaffold", result.stdout)

    def test_paper_binding_requires_real_data_model_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
            make_paper_binding_decision(research_dir)
            decision = research_dir / "V0" / "PAPER_BINDING_DECISION.md"
            text = decision.read_text(encoding="utf-8")
            text = re.sub(r"\n\s+real_data_check:.*", "", text)
            text = re.sub(r"\n\s+real_model_check:.*", "", text)
            text = re.sub(r"\n\s+non_smoke_full_run:.*", "", text)
            decision.write_text(text, encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("real_data_check", result.stdout)
            self.assertIn("real_model_check", result.stdout)
            self.assertIn("non_smoke_full_run", result.stdout)

    def test_old_version_artifact_requires_current_carry_forward(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
            make_paper_binding_decision(research_dir, artifact_path="docs/research/V0/artifacts/run_001.json")
            v1 = research_dir / "V1"
            shutil.copytree(research_dir / "V0", v1)
            (research_dir / "CURRENT").write_text("V1\n", encoding="utf-8")
            status = read_yaml(v1 / "STATUS.yaml")
            status["version"] = "V1"
            status["status"] = "closed_stable"
            status["direction_ref"] = "../RESEARCH_DIRECTION.md"
            write_yaml(v1 / "STATUS.yaml", status)
            spec = read_yaml(v1 / "SPEC.yaml")
            spec["version"] = "V1"
            write_yaml(v1 / "SPEC.yaml", spec)
            baseline_lock = read_yaml(v1 / "BASELINE_LOCK.yaml")
            baseline_lock["version"] = "V1"
            write_yaml(v1 / "BASELINE_LOCK.yaml", baseline_lock)
            rq_spec = read_yaml(v1 / "rqs" / "RQ01" / "SPEC.yaml")
            rq_spec["version"] = "V1"
            write_yaml(v1 / "rqs" / "RQ01" / "SPEC.yaml", rq_spec)
            queue = read_yaml(v1 / "TASK_QUEUE.yaml")
            queue["version"] = "V1"
            write_yaml(v1 / "TASK_QUEUE.yaml", queue)
            spine = read_yaml(v1 / "RESEARCH_SPINE.yaml")
            spine["version"] = "V1"
            write_yaml(v1 / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without explicit carry_forward", result.stdout)

            spec = read_yaml(v1 / "SPEC.yaml")
            spec["version"] = "V1"
            spec["carry_forward"] = [{"from_version": "V0", "artifact_path": "docs/research/V0/artifacts/run_001.json"}]
            write_yaml(v1 / "SPEC.yaml", spec)
            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-binding-ready"])
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_initialized_epoch_templates_do_not_contain_bare_todo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            for path in research_dir.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".yaml", ".yml", ".txt", ""}:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    self.assertNotIn("TODO", text, path)

    def test_readme_documents_charter_bounded_epoch_research_loop(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Charter-bounded Epoch Research Loop", readme)
        self.assertIn("Auto research is not automatic paper writing", readme)
        self.assertIn("Research Direction", readme)
        self.assertIn("Paper Binding", readme)

    def test_agents_and_claude_rules_are_created_and_reference_current_next_action(self) -> None:
        root_agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        root_claude = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("docs/research/CURRENT", root_agents)
        self.assertNotIn("NEXT_ACTION.md", root_agents)
        self.assertIn("docs/research/CURRENT", root_claude)
        self.assertNotIn("NEXT_ACTION.md", root_claude)
        for forbidden in ["git push", "git reset --hard", "git clean -fd", "git rebase", "force push"]:
            self.assertIn(forbidden, root_agents)
            self.assertIn(forbidden, root_claude)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace_fast(repo)
            self.assertIn("docs/research/CURRENT", (repo / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertNotIn("NEXT_ACTION.md", (repo / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_subagent_and_literature_policies_include_required_roles_and_search_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            subagent = (research_dir / "agent" / "SUBAGENT_POLICY.md").read_text(encoding="utf-8")
            literature = (research_dir / "agent" / "LITERATURE_POLICY.md").read_text(encoding="utf-8")

            for role in [
                "literature_scout",
                "repo_explorer",
                "experiment_engineer",
                "debugger",
                "artifact_auditor",
                "wiki_synthesizer",
                "paper_binder",
            ]:
                self.assertIn(role, subagent)
            self.assertIn("Mandatory Search Points", literature)
            self.assertIn("No-search Situations", literature)
            self.assertIn("Project start", literature)
            self.assertIn("Before paper binding", literature)

    def test_new_validator_modes_are_runnable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            for mode in [
                "direction-ready",
                "epoch-ready",
                "loop-ready",
                "closeout-ready",
                "paper-binding-ready",
                "format-ready",
                "rq-driven-ready",
                "baseline-lock-ready",
                "migration-ready",
                "git-ready",
            ]:
                result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", mode])
                self.assertIn(mode, result.stdout + result.stderr)

    def test_format_ready_detects_missing_epoch_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "CURRENT").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "format-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CURRENT", result.stdout)

    def test_git_ready_detects_missing_git_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run_cmd(["git", "init"], cwd=repo)
            research_dir = init_workspace_fast(repo)
            (research_dir / "V0" / "GIT_STATE.yaml").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "git-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("GIT_STATE.yaml", result.stdout)
