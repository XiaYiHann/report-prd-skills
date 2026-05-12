#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class ResearchLoopControllerTests(unittest.TestCase):  # noqa: F405
    def test_research_loop_empty_workspace_initializes_state_and_prd_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = run_cmd(
                [
                    "python3",
                    str(RESEARCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--max-steps",
                    "1",
                    "--date",
                    "2026-05-10",
                    "--executor",
                    "prompt-only",
                    "--json",
                    "--legacy-controller",
                ],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = yaml.safe_load(result.stdout)
            self.assertEqual(summary["execution_backend"]["mode"], "prompt-only")
            self.assertTrue(summary["execution_backend"]["implemented"])
            research_dir = repo / "docs" / "research"
            self.assertTrue((research_dir / "state.yaml").exists())
            self.assertTrue((research_dir / "plans" / "plan_queue.yaml").exists())
            self.assertTrue((research_dir / "prd" / "research_prd.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S1_PRD_NOT_READY")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertFalse(state["prd"]["human_approved"])

    def test_research_loop_prd_not_approved_stops_before_spec_automation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S1_PRD_NOT_READY")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertIsNone(state["plans"]["active"])
            self.assertIn("human approval", state["project_status"]["block_reason"])

    def test_research_loop_prd_ready_spec_missing_generates_spec_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            shutil.rmtree(research_dir / "spec")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((research_dir / "spec" / "global_spec.yaml").exists())
            self.assertTrue((research_dir / "spec" / "feedback" / "README.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["spec"]["status"], "not_ready")
            self.assertTrue(state["project_status"]["blocked"])

    def test_research_loop_spec_ready_no_plan_generates_queue_and_next_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            queue = read_yaml(research_dir / "plans" / "plan_queue.yaml")
            self.assertGreaterEqual(len(queue["queue"]), 1)
            state = read_yaml(research_dir / "state.yaml")
            active_plan = state["plans"]["active"]
            self.assertIsNotNone(active_plan)
            self.assertTrue((research_dir / "plans" / active_plan / "plan.yaml").exists())
            self.assertEqual(state["project_status"]["current_stage"], "S4_EXECUTING_PLAN")

    def test_research_loop_active_plan_complete_writes_feedback_insight_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            plan_result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-10",
                    "--purpose",
                    "reproduce-b01",
                    "--track",
                    "reproduction",
                ],
                cwd=repo,
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stdout + plan_result.stderr)
            plan_dir = research_dir / "plans" / "2026-05-10-reproduce-b01"
            plan_yaml = read_yaml(plan_dir / "plan.yaml")
            plan_yaml["status"] = "complete"
            write_yaml(plan_dir / "plan.yaml", plan_yaml)
            (plan_dir / "final_summary.md").write_text(
                "# 最终总结\n\nPLAN_STATUS: COMPLETE\nHARNESS_EVIDENCE: documented in run_log.md\n",
                encoding="utf-8",
            )
            (plan_dir / "run_log.md").write_text(
                "# 运行日志\n\n- harness stdout/stderr paths recorded by executor.\n",
                encoding="utf-8",
            )

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((research_dir / "spec" / "feedback" / "2026-05-10-reproduce-b01_lessons.md").exists())
            self.assertTrue((research_dir / "audits" / "2026-05-10-audit" / "audit_report.md").exists())
            insight_log = (research_dir / "insights" / "insight_log.md").read_text(encoding="utf-8")
            self.assertIn("2026-05-10-reproduce-b01", insight_log)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["last_audit"], "docs/research/audits/2026-05-10-audit")

    def test_research_loop_prd_ambiguity_writes_human_review_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir, ambiguity=True)
            shutil.rmtree(research_dir / "spec")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            review_dir = research_dir / "audits" / "2026-05-10-prd-review"
            self.assertTrue((review_dir / "prd_change_request.md").exists())
            self.assertTrue((review_dir / "repair_plan.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S6_INSIGHT_REVIEW_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])

    def test_research_loop_open_pivot_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            pivot = research_dir / "insights" / "pivot_proposals" / "p01.md"
            pivot.write_text("# Pivot Proposal\n\n## Human Decision Required\nApprove / reject / revise\n", encoding="utf-8")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S6_INSIGHT_REVIEW_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertEqual(state["insights"]["open_pivot_proposals"], ["docs/research/insights/pivot_proposals/p01.md"])

    def test_research_loop_stale_plan_blocks_execution_with_audit_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            plan_result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-10",
                    "--purpose",
                    "run-e01-main-experiment",
                    "--track",
                    "experiment",
                ],
                cwd=repo,
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stdout + plan_result.stderr)
            spec = research_dir / "spec" / "global_spec.yaml"
            spec.write_text(spec.read_text(encoding="utf-8") + "\n# drift after plan creation\n", encoding="utf-8")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json", "--legacy-controller"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S5_AUDIT_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])
            repair = (research_dir / "audits" / "2026-05-10-audit" / "repair_plan.md").read_text(encoding="utf-8")
            self.assertIn("stale spec hash", repair)
