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
        self.assertIn("## RQ Execution Plan Matrix", goal_text)
        self.assertIn("## Outstanding Task Graph", goal_text)
        self.assertIn("## Parallel And Blocked Branch Policy", goal_text)
        self.assertIn("## Blocked Task Triage Review", goal_text)
        self.assertIn("version task dependency graph", goal_text)
        self.assertIn("rqs/RQ01/SPEC.yaml", goal_text)
        self.assertIn("rqs/RQ01/PLAN.md", goal_text)
        self.assertIn("what_to_do", goal_text)
        self.assertIn("depends_on", goal_text)
        self.assertIn("triage_mode", goal_text)
        self.assertIn("blocked_by", goal_text)
        self.assertIn("unblocks", goal_text)
        self.assertIn("independent runnable tasks", goal_text)
        self.assertIn("orthogonal runnable tasks", goal_text)
        self.assertIn("runnable_parallel_set", goal_text)
        self.assertIn("runnable unblocked task", goal_text)
        self.assertIn("code-review-first triage", goal_text)
        self.assertIn("implementation defect", goal_text)
        self.assertIn("idea/spec defect", goal_text)
        self.assertNotIn("当前下一步", goal_text)
        self.assertEqual(lock["target_executor"], "claude-code")
        self.assertEqual(lock["goal_status"], "active")
        self.assertIn("goal_hash", lock)
        self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)

    def test_research_goal_encodes_blocked_descendants_and_orthogonal_runnable_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch_dir = research_dir / "V0"
            queue_path = epoch_dir / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            for task in queue["tasks"]:
                if task["task_id"] == "T_G0_001":
                    task["status"] = "blocked"
                elif task["task_id"] == "T_G0_002":
                    task["status"] = "pending"
                elif task["task_id"] == "T_G0_003":
                    task["status"] = "pending"
                    task["depends_on"] = ["T_G0_001", "T_G0_002"]
            write_yaml(queue_path, queue)

            result = run_cmd(["python3", str(GOAL_SCRIPT), "--research-dir", str(research_dir)])
            goal_text = (epoch_dir / "goal.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("runnable_parallel_set: `T_G0_002`", goal_text)
        self.assertIn("T_G0_003(blocked_by=T_G0_001)", goal_text)
        self.assertIn("blocked_by=`T_G0_001`", goal_text)
        self.assertIn("waiting_on=`T_G0_002`", goal_text)
        self.assertIn("triage_mode=`code-review-first`", goal_text)
        self.assertIn("blocked_triage_queue: `T_G0_001`", goal_text)
        self.assertIn("parallel_class=`blocked_descendant`", goal_text)

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
