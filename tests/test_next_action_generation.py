#!/usr/bin/env python3
"""Gate-aware NEXT_ACTION and TASK_QUEUE template tests."""

from __future__ import annotations

import sys

from research_workflow_helpers import *  # noqa: F403


SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import render_next_action  # noqa: E402


class NextActionGenerationTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_gate_aware_task_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(queue["current_gate"], "G0")
        self.assertEqual(queue["current_task"], "T_G0_001")
        self.assertEqual(queue["gates"][0]["gate_id"], "G0")
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["gates"][0]["audit"]["status"], "pending")
        self.assertEqual(queue["tasks"][0]["task_id"], "T_G0_001")
        self.assertEqual(queue["tasks"][0]["id"], "T_G0_001")
        self.assertEqual(queue["tasks"][0]["status"], "active")

    def test_next_action_contains_single_step_execution_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            next_action = (research_dir / "V0" / "NEXT_ACTION.md").read_text(encoding="utf-8")

        self.assertIn("## Active Task", next_action)
        self.assertIn("- Gate: G0", next_action)
        self.assertIn("- Task ID: T_G0_001", next_action)
        self.assertIn("## Forbidden Actions", next_action)
        self.assertIn("Do not modify Research Direction", next_action)
        self.assertIn("## Harness", next_action)
        self.assertIn("## Completion Contract", next_action)
        self.assertIn("## If Blocked", next_action)

    def test_next_action_blocks_when_no_active_task_exists(self) -> None:
        queue = {
            "template_version": "epoch_v1",
            "version": "V0",
            "queue_status": "blocked",
            "current_gate": None,
            "current_task": None,
            "gates": [],
            "tasks": [],
        }

        rendered = render_next_action(None, queue, "V0")

        self.assertIn("NO ACTIVE TASK", rendered)
        self.assertIn("Do not invent a task", rendered)
