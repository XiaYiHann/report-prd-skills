#!/usr/bin/env python3
"""Search and reproduction epoch scaffold tests."""

from __future__ import annotations

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class SearchReproductionScaffoldTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_search_and_reproduction_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch_dir = research_dir / "V0"

            expected = [
                epoch_dir / "search" / "search_report.md",
                epoch_dir / "search" / "web_search_log.yaml",
                epoch_dir / "search" / "repo_search_log.yaml",
                epoch_dir / "search" / "candidate_baselines.yaml",
                epoch_dir / "search" / "dataset_candidates.yaml",
                epoch_dir / "search" / "paper_experiment_designs.yaml",
                epoch_dir / "search" / "candidate_reproductions.yaml",
                epoch_dir / "baselines" / "INDEX.yaml",
                epoch_dir / "BASELINE_LOCK.yaml",
                epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml",
                epoch_dir / "reproduction" / "REPRODUCTION_LEDGER.yaml",
                epoch_dir / "reproduction" / "REPRODUCTION_PLAN.md",
                epoch_dir / "reproduction" / "REPRODUCTION_DELTA.yaml",
                epoch_dir / "rqs" / "RQ01" / "SPEC.yaml",
                epoch_dir / "rqs" / "RQ01" / "PLAN.md",
                epoch_dir / "rqs" / "RQ01" / "TASKS.yaml",
                epoch_dir / "rqs" / "RQ01" / "INSIGHT_REVIEW.yaml",
                epoch_dir / "rqs" / "RQ01" / "reproduction" / "SOURCE_LOCK.yaml",
                epoch_dir / "rqs" / "RQ01" / "reproduction" / "VERIFICATION.yaml",
                epoch_dir / "wiki" / "frontier_map.yaml",
            ]

            for path in expected:
                self.assertTrue(path.exists(), str(path))

    def test_default_task_queue_starts_with_search_lock_before_reproduction_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(queue["current_gate"], "G0_SEARCH_LOCK")
        self.assertEqual(queue["current_task"], "T_G0_001")
        gate_ids = [gate["gate_id"] for gate in queue["gates"]]
        self.assertLess(gate_ids.index("G0_SEARCH_LOCK"), gate_ids.index("G1_REPRODUCTION_LOCK"))
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["gates"][1]["status"], "pending")
        baseline_task = next(task for task in queue["tasks"] if task["task_id"] == "T_G0_003")
        self.assertEqual(baseline_task["phase"], "baseline_lock")
        self.assertIn("BASELINE_LOCK.yaml", baseline_task["output_refs"])
        self.assertIn("baselines/INDEX.yaml", baseline_task["output_refs"])

    def test_spine_and_rq_spec_declare_reproduction_and_filesystem_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            rq_spec = read_yaml(research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml")

        self.assertEqual(spine["research_questions"][0]["spec_ref"], "rqs/RQ01/SPEC.yaml")
        self.assertEqual(spine["research_questions"][0]["plan_ref"], "rqs/RQ01/PLAN.md")
        self.assertTrue(rq_spec["reproduction_contract"]["required"])
        self.assertTrue(rq_spec["reproduction_contract"]["pass_before_innovation"])
        self.assertEqual(rq_spec["reproduction_contract"]["source_lock_ref"], "reproduction/SOURCE_LOCK.yaml")

    def test_default_scaffold_declares_human_governed_pipeline_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            rq_spec = read_yaml(research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml")
            insight_review = read_yaml(research_dir / "V0" / "rqs" / "RQ01" / "INSIGHT_REVIEW.yaml")
            ledger = read_yaml(research_dir / "V0" / "reproduction" / "REPRODUCTION_LEDGER.yaml")
            frontier = read_yaml(research_dir / "V0" / "wiki" / "frontier_map.yaml")

        self.assertEqual(rq_spec["human_approval"]["status"], "proposed")
        self.assertTrue(rq_spec["insight_contract"]["human_verdict_required"])
        self.assertEqual(insight_review["human_verdict"]["verdict"], "pending_human_review")
        self.assertTrue(ledger["reuse_policy"]["coverage_check_required_for_every_rq"])
        self.assertEqual(frontier["human_decision"]["status"], "pending")

    def test_generate_research_spec_writes_rq_local_spec_and_spine_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            spec_path = research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml"
            spec_path.unlink()

            result = run_cmd(["python3", str(REPO_ROOT / "skills" / "research-spec" / "scripts" / "generate_research_spec.py"), "--repo", str(repo), "--rq", "RQ01"])
            rq_spec = read_yaml(spec_path)
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(rq_spec["rq_id"], "RQ01")
        self.assertIn("claim_contract", rq_spec)
        self.assertFalse((research_dir / "V0" / "SPEC.yaml").exists())
        self.assertEqual(spine["research_questions"][0]["spec_ref"], "rqs/RQ01/SPEC.yaml")

    def test_generate_research_plan_writes_rq_local_plan_and_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)

            result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--repo",
                    str(repo),
                    "--date",
                    "2026-05-15",
                    "--purpose",
                    "rq01-reproduction",
                    "--track",
                    "reproduction",
                    "--rq",
                    "RQ01",
                ]
            )
            plan = (research_dir / "V0" / "rqs" / "RQ01" / "PLAN.md").read_text(encoding="utf-8")
            tasks = read_yaml(research_dir / "V0" / "rqs" / "RQ01" / "TASKS.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Evidence-Generation Plan", plan)
        self.assertEqual(tasks["tasks"][0]["phase"], "reproduction")
        self.assertIn("expected_artifacts", tasks["tasks"][0])


if __name__ == "__main__":
    unittest.main()
