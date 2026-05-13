#!/usr/bin/env python3
"""Search and reproduction epoch scaffold tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class SearchReproductionScaffoldTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_search_and_reproduction_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"

            expected = [
                epoch_dir / "search" / "search_report.md",
                epoch_dir / "search" / "web_search_log.yaml",
                epoch_dir / "search" / "repo_search_log.yaml",
                epoch_dir / "search" / "candidate_baselines.yaml",
                epoch_dir / "search" / "candidate_reproductions.yaml",
                epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml",
                epoch_dir / "reproduction" / "REPRODUCTION_PLAN.md",
                epoch_dir / "reproduction" / "REPRODUCTION_DELTA.yaml",
            ]

            for path in expected:
                self.assertTrue(path.exists(), str(path))

    def test_default_task_queue_starts_with_search_lock_before_reproduction_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(queue["current_gate"], "G0_SEARCH_LOCK")
        self.assertEqual(queue["current_task"], "T_G0_001")
        gate_ids = [gate["gate_id"] for gate in queue["gates"]]
        self.assertLess(gate_ids.index("G0_SEARCH_LOCK"), gate_ids.index("G1_REPRODUCTION_LOCK"))
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["gates"][1]["status"], "pending")

    def test_default_spec_declares_reproduction_and_filesystem_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            spec = read_yaml(research_dir / "V0" / "SPEC.yaml")

        self.assertTrue(spec["reproduction_contract"]["required"])
        self.assertTrue(spec["reproduction_contract"]["search_required_before_reproduction"])
        self.assertEqual(spec["filesystem_contract"]["state_root"], "docs/research/V0")
        self.assertEqual(spec["filesystem_contract"]["reproduction_workspace_root"], "reproduction/V0")


if __name__ == "__main__":
    unittest.main()
