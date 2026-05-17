#!/usr/bin/env python3
"""Gate-aware update_state transition tests."""

from __future__ import annotations

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


def write_search_evidence(epoch_dir: Path) -> None:
    (epoch_dir / "search" / "web_search_log.yaml").write_text(
        "queries:\n  - query: baseline official code\n    results: []\nabsence_claims: []\n",
        encoding="utf-8",
    )
    (epoch_dir / "search" / "repo_search_log.yaml").write_text(
        "commands:\n  - command: rg baseline\n    purpose: local search\nfindings: {}\n",
        encoding="utf-8",
    )
    (epoch_dir / "search" / "search_report.md").write_text(
        "# Search Report\n\nSearch completed for baseline and reproduction candidates.\n",
        encoding="utf-8",
    )


class UpdateStateGateFlowTests(unittest.TestCase):  # noqa: F405
    def test_completed_task_activates_next_task_without_passing_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            write_search_evidence(research_dir / "V0")
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "T_G0_001",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "completed",
                    "--executor",
                    "codex",
                    "--command",
                    "python3 -m pytest tests/test_next_action_generation.py -v",
                    "--exit-code",
                    "0",
                ],
                cwd=repo,
            )
            updated = read_yaml(queue_path)
            goal_ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "goal-ready"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(updated["current_task"], "T_G0_002")
        self.assertEqual(updated["gates"][0]["status"], "active")
        self.assertEqual(updated["tasks"][1]["status"], "active")
        self.assertEqual(goal_ready.returncode, 0, goal_ready.stdout + goal_ready.stderr)

    def test_gate_enters_audit_required_after_all_tasks_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            write_search_evidence(research_dir / "V0")
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            queue["gates"][0]["audit"]["required"] = True
            queue["gates"][0]["tasks"] = [{"task_id": "T_G0_001", "status": "active"}]
            queue["tasks"] = [task for task in queue["tasks"] if task.get("task_id") == "T_G0_001"]
            write_yaml(queue_path, queue)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "T_G0_001",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "completed",
                    "--executor",
                    "codex",
                    "--command",
                    "python3 -m pytest tests/test_next_action_generation.py -v",
                    "--exit-code",
                    "0",
                ],
                cwd=repo,
            )
            queue = read_yaml(queue_path)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["queue_status"], "audit_required")
        self.assertEqual(queue["gates"][0]["status"], "audit_required")
        self.assertIsNone(queue["current_task"])

    def test_failed_branch_task_activates_independent_runnable_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "T_G0_001",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "failed_execution",
                    "--failure-class",
                    "execution_failure",
                    "--executor",
                    "codex",
                    "--command",
                    "python missing.py",
                    "--exit-code",
                    "2",
                ],
                cwd=repo,
            )
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            report = read_yaml(research_dir / "V0" / "runs" / "T_G0_001_report.yaml")
            blocker_path = research_dir / "V0" / "runs" / "T_G0_001_blocker.md"
            status = read_yaml(research_dir / "V0" / "STATUS.yaml")
            blocker_exists = blocker_path.exists()
            blocker_text = blocker_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["current_task"], "T_G0_002")
        self.assertEqual(queue["tasks"][1]["status"], "active")
        self.assertIn("T_G0_001", queue["gates"][0]["blocked_tasks"])
        self.assertEqual(status["status"], "running")
        self.assertNotEqual(queue["gates"][0]["status"], "falsified")
        self.assertEqual(report["conclusion"]["failure_class"], "execution_failure")
        self.assertFalse(report["conclusion"]["research_interpretation_allowed"])
        self.assertTrue(blocker_exists)
        self.assertIn("code-review-first", blocker_text)
        self.assertIn("implementation defect", blocker_text)
        self.assertIn("repair and rerun", blocker_text)

    def test_blocked_dependency_stops_only_after_no_runnable_tasks_remain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch_dir = research_dir / "V0"
            write_search_evidence(epoch_dir)
            queue_path = epoch_dir / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            queue["tasks"][0]["status"] = "completed"
            queue["tasks"][1]["status"] = "completed"
            queue["tasks"][2]["status"] = "active"
            queue["current_task"] = "T_G0_003"
            queue["gates"][0]["tasks"] = [
                {"task_id": "T_G0_001", "status": "completed"},
                {"task_id": "T_G0_002", "status": "completed"},
                {"task_id": "T_G0_003", "status": "active"},
            ]
            write_yaml(queue_path, queue)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "T_G0_003",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "blocked",
                    "--failure-class",
                    "spec_gap",
                    "--blocker-reason",
                    "baseline cannot be locked without human decision",
                    "--executor",
                    "codex",
                ],
                cwd=repo,
            )
            queue = read_yaml(queue_path)
            status = read_yaml(epoch_dir / "STATUS.yaml")
            blocker_path = epoch_dir / "runs" / "T_G0_003_blocker.md"
            blocker_exists = blocker_path.exists()
            blocker_text = blocker_path.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["queue_status"], "blocked")
        self.assertEqual(queue["gates"][0]["status"], "blocked")
        self.assertIsNone(queue["current_task"])
        self.assertEqual(status["status"], "gate_blocked")
        self.assertTrue(blocker_exists)
        self.assertIn("code-review-first", blocker_text)
        self.assertIn("idea/spec defect", blocker_text)
        self.assertIn("record blocker or pivot request", blocker_text)
