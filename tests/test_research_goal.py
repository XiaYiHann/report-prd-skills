#!/usr/bin/env python3
"""Research goal synthesis tests."""

from __future__ import annotations

import pytest
from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class ResearchGoalTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_goal_lock_and_goal_ready_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "goal-ready"])
            lock = read_yaml(research_dir / "V0" / "GOAL_LOCK.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[OK] goal-ready", result.stdout)
        self.assertEqual(lock["schema_version"], "goal_lock_v1")
        self.assertEqual(lock["goal_ref"], "goal.md")
        self.assertIn("baseline_lock", lock["source_refs"])
        self.assertIn("rq_contracts", lock["source_refs"])
        self.assertIn("task_queue", lock["source_refs"])
        self.assertNotIn("spec", lock["source_refs"])

    def test_research_goal_refreshes_goal_md_and_goal_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            goal_path = research_dir / "V0" / "goal.md"
            goal_path.write_text("stale goal\n", encoding="utf-8")

            result = run_cmd(
                [
                    "python3",
                    str(GOAL_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--target",
                    "claude-code",
                ]
            )
            goal_text = goal_path.read_text(encoding="utf-8")
            lock = read_yaml(research_dir / "V0" / "GOAL_LOCK.yaml")
            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "goal-ready"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[OK] wrote research goal", result.stdout)
        self.assertIn("TASK_QUEUE.yaml", goal_text)
        self.assertIn("BASELINE_LOCK.yaml", goal_text)
        self.assertIn("GOAL_LOCK.yaml", goal_text)
        self.assertIn("## RQ Contract Coverage", goal_text)
        self.assertIn("## Outstanding Task Graph", goal_text)
        self.assertIn("rqs/RQ01/SPEC.yaml", goal_text)
        self.assertIn("rqs/RQ01/PLAN.md", goal_text)
        self.assertIn("depends_on", goal_text)
        self.assertIn("independent runnable tasks", goal_text)
        self.assertIn("runnable unblocked task", goal_text)
        self.assertEqual(lock["target_executor"], "claude-code")
        self.assertEqual(lock["goal_status"], "active")
        self.assertIn("goal_hash", lock)
        self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_goal_ready_rejects_stale_goal_lock_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            result = run_cmd(["python3", str(GOAL_SCRIPT), "--research-dir", str(research_dir)])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            prd = research_dir / "V0" / "PRD.tex"
            prd.write_text(prd.read_text(encoding="utf-8") + "\n% changed after goal lock\n", encoding="utf-8")

            ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "goal-ready"])

        self.assertNotEqual(ready.returncode, 0)
        self.assertIn("GOAL_LOCK.yaml stale source hash for prd", ready.stdout)


if __name__ == "__main__":
    unittest.main()
