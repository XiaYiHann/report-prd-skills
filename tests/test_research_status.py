#!/usr/bin/env python3
"""Research status skill tests."""

from __future__ import annotations

import json

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class ResearchStatusTests(unittest.TestCase):  # noqa: F405
    def test_research_status_reports_active_epoch_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            queue_before = (research_dir / "V0" / "TASK_QUEUE.yaml").read_text(encoding="utf-8")

            result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(repo), "--json"])  # noqa: F405
            queue_after = (research_dir / "V0" / "TASK_QUEUE.yaml").read_text(encoding="utf-8")
            payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue_before, queue_after)
        self.assertEqual(payload["workspace_role"], "research_workspace")
        self.assertEqual(payload["current_version"], "V0")
        self.assertEqual(payload["current_gate"], "G0_SEARCH_LOCK")
        self.assertEqual(payload["active_task"]["id"], "T_G0_001")
        self.assertEqual(payload["baseline_lock_status"], "pending")
        self.assertEqual(payload["evidence_gate"]["next_required_gate"], "G0_SEARCH_LOCK")
        self.assertIn("RQ01", payload["declared_rqs"])
        self.assertEqual(payload["research_goal"]["minimum_viable_purpose"], "minimal-regression")
        self.assertEqual(payload["epoch_progress"]["task_counts"]["active"], 1)
        self.assertEqual(payload["rq_progress"][0]["id"], "RQ01")
        self.assertIn("statement", payload["rq_progress"][0])
        self.assertEqual(payload["current_experiment"]["active_task"]["id"], "T_G0_001")
        self.assertIn("success_criteria", payload["current_experiment"]["active_task"])
        self.assertIn("project_summary", payload)
        self.assertIn("background", payload["project_summary"])
        self.assertIn("goal", payload["project_summary"])
        self.assertIn("completed", payload["project_summary"])
        self.assertIn("remaining", payload["project_summary"])
        self.assertIn("blockers", payload["project_summary"])
        self.assertIn("next_step", payload["project_summary"])
        self.assertTrue(payload["next_actions"])
        self.assertIn("plain_language_summary", payload)
        self.assertIn("current_state", payload["plain_language_summary"])
        self.assertIn("T_G0_001", payload["plain_language_summary"]["current_state"])
        self.assertIn("next_step", payload["plain_language_summary"])
        self.assertIn("loop-ready", payload["validators"])

    def test_research_status_markdown_is_concise_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace_fast(repo)

            result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(repo), "--no-validators"])  # noqa: F405

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("# Research Status", result.stdout)
        self.assertIn("## Project Overview", result.stdout)
        self.assertIn("## Beginner Summary", result.stdout)
        self.assertIn("completed_examples", result.stdout)
        self.assertIn("remaining_examples", result.stdout)
        self.assertIn("missing_or_blocked", result.stdout)
        self.assertIn("next_step", result.stdout)
        self.assertIn("## Current Goal", result.stdout)
        self.assertIn("## Experiment Progress", result.stdout)
        self.assertIn("## RQ Progress", result.stdout)
        self.assertIn("## Wiki And Compounding", result.stdout)
        self.assertIn("## Next Actions", result.stdout)
        self.assertIn("T_G0_001", result.stdout)
        self.assertIn("Web search prior work and baselines", result.stdout)

    def test_research_status_blockers_include_repair_and_verify_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            baseline = read_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml")
            baseline["status"] = "needs_human_review"
            write_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml", baseline)

            result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(repo), "--json", "--no-validators"])  # noqa: F405
            payload = json.loads(result.stdout)
            baseline_blocker = next(item for item in payload["blockers"] if item["type"] == "baseline_lock")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("problem", baseline_blocker)
        self.assertIn("repair", baseline_blocker)
        self.assertIn("verify", baseline_blocker)
        self.assertIn("BASELINE_LOCK.yaml", payload["plain_language_summary"]["missing"])
        self.assertIn("baseline-lock-ready", payload["plain_language_summary"]["verify"])

    def test_research_status_prefers_rq_local_active_task_over_stale_queue_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            queue["current_task"] = "T_G0_001"
            for task in queue["tasks"]:
                task["status"] = "pending"
            write_yaml(queue_path, queue)

            rq_tasks_path = research_dir / "V0" / "rqs" / "RQ01" / "TASKS.yaml"
            rq_tasks = read_yaml(rq_tasks_path)
            rq_tasks["tasks"][0]["status"] = "active"
            write_yaml(rq_tasks_path, rq_tasks)

            result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(repo), "--json", "--no-validators"])  # noqa: F405
            payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(payload["active_task"]["id"], "RQ01_T001")
        self.assertEqual(payload["active_task"]["rq_id"], "RQ01")
        self.assertEqual(payload["current_experiment"]["active_task"]["id"], "RQ01_T001")
        self.assertEqual(payload["epoch_progress"]["task_counts"]["active"], 1)
        self.assertIn("RQ01_T001", payload["project_summary"]["remaining"]["active_tasks"][0])
        self.assertEqual(payload["next_actions"][0]["type"], "continue_active_task")
        self.assertEqual(payload["next_actions"][0]["target"], "RQ01_T001")
        self.assertIn("docs/research/V0/rqs/RQ01/TASKS.yaml", payload["plain_language_summary"]["read_first"])

    def test_research_status_blocked_task_prioritizes_code_review_triage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            for task in queue["tasks"]:
                if task["id"] == "T_G0_001":
                    task["status"] = "blocked"
                elif task["id"] != "T_G0_001":
                    task["status"] = "pending"
            write_yaml(queue_path, queue)

            result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(repo), "--json", "--no-validators"])  # noqa: F405
            payload = json.loads(result.stdout)
            task_blocker = next(item for item in payload["blockers"] if item["type"] == "task")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(task_blocker["triage"], "code-review-first")
        self.assertIn("code-review-first triage", task_blocker["problem"])
        self.assertIn("implementation defect", task_blocker["repair"])
        self.assertEqual(payload["next_actions"][0]["type"], "review_blocked_code")
        self.assertIn("implementation/harness defect", payload["next_actions"][0]["description"])
        self.assertIn("code-review-first triage", payload["plain_language_summary"]["next_step"])
        self.assertIn("triage", result.stdout)
        self.assertIn("review_blocked_code", result.stdout)

    def test_research_status_meta_framework_validators_are_not_applicable(self) -> None:
        result = run_cmd(["python3", str(STATUS_SCRIPT), "--repo", str(REPO_ROOT), "--json"])  # noqa: F405
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(payload["workspace_role"], "meta_framework")
        self.assertEqual(payload["validators"]["goal-ready"]["ok"], None)
        self.assertFalse(payload["validators"]["goal-ready"]["applicable"])
        self.assertEqual(payload["validators"]["goal-ready"]["reason"], "meta_framework_workspace")
        self.assertIn("framework 合同", payload["project_summary"]["next_step"])


if __name__ == "__main__":
    unittest.main()
