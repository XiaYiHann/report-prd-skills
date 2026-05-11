#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class ResearchLegacyValidatorTests(unittest.TestCase):  # noqa: F405
    def test_valid_paper_placeholders_pass_paper_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("[OK] paper-ready", result.stdout)

    def test_invalid_paper_fake_results_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            paper = research_dir / "paper" / "planned_paper.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\nExperiments show that our method outperforms B01.\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unvalidated empirical result language", result.stdout)

    def test_invalid_paper_unbound_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            paper = research_dir / "paper" / "planned_paper.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\nTable 2 reports {{E99.OURS.primary_metric}}.\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unregistered placeholder", result.stdout)

    def test_spec_ready_rejects_missing_experiment_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            harness_path = research_dir / "spec" / "experiments" / "experiment_harness.yaml"
            harness_payload = read_yaml(harness_path)
            harness_payload["harnesses"] = []
            write_yaml(harness_path, harness_payload)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spec-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("H_E01_FULL", result.stdout)

    def test_plan_ready_rejects_stale_spec_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-09",
                    "--purpose",
                    "reproduce-b01",
                    "--track",
                    "reproduction",
                ],
                cwd=repo,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            spec = research_dir / "spec" / "global_spec.yaml"
            spec.write_text(spec.read_text(encoding="utf-8") + "\n# drift after plan creation\n", encoding="utf-8")

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "plan-ready"])

            self.assertNotEqual(check.returncode, 0)
            self.assertIn("stale spec hash", check.stdout)

    def test_ppt_ready_rejects_missing_slide_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            result = run_cmd(["python3", str(PPT_SCRIPT), "--research-dir", str(research_dir), "--mode", "standard"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (research_dir / "ppt" / "main_deck" / "slide_prompts" / "03_rq.md").unlink()

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "ppt-ready"])

            self.assertNotEqual(check.returncode, 0)
            self.assertIn("missing slide prompt", check.stdout)

    def test_insight_ready_validates_insight_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "insight-ready"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

            # Delete insight_policy.yaml and assert failure
            (research_dir / "spec" / "shared" / "insight_policy.yaml").unlink()
            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "insight-ready"])
            self.assertNotEqual(check.returncode, 0)
            self.assertIn("insight_policy.yaml", check.stdout + check.stderr)

    def test_audit_generation_produces_required_alignment_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            run_cmd(["python3", str(PPT_SCRIPT), "--research-dir", str(research_dir), "--mode", "standard"])
            result = run_cmd(["python3", str(AUDIT_SCRIPT), "--research-dir", str(research_dir), "--date", "2026-05-09"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            audit_dir = research_dir / "audits" / "2026-05-09-audit"
            for name in ["audit_report.md", "alignment_matrix.yaml", "drift_findings.yaml", "repair_plan.md"]:
                self.assertTrue((audit_dir / name).exists(), name)

            matrix = read_yaml(audit_dir / "alignment_matrix.yaml")
            self.assertIn("prd_to_insight", matrix.get("dimensions", {}))
            self.assertIn("insight_to_spec", matrix.get("dimensions", {}))
            repair = (audit_dir / "repair_plan.md").read_text(encoding="utf-8")
            self.assertIn("Insight opportunity", repair)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
