#!/usr/bin/env python3
"""Gate-aware update_state transition tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


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

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(updated["current_task"], "T_G0_002")
        self.assertEqual(updated["gates"][0]["status"], "active")
        self.assertEqual(updated["tasks"][1]["status"], "active")

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

    def test_failed_execution_does_not_falsify_gate(self) -> None:
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

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["gates"][0]["status"], "blocked")
        self.assertNotEqual(queue["gates"][0]["status"], "falsified")
        self.assertEqual(report["conclusion"]["failure_class"], "execution_failure")
        self.assertFalse(report["conclusion"]["research_interpretation_allowed"])
