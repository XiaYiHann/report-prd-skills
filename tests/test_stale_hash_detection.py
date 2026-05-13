#!/usr/bin/env python3
"""Stale hash detection tests for gate-aware research loop."""

from __future__ import annotations

import sys

from research_workflow_helpers import *  # noqa: F403


SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    StaleFinding,
    detect_epoch_stale_hashes,
    write_blocked_next_action_for_stale,
)


class StaleHashDetectionTests(unittest.TestCase):  # noqa: F405
    def test_prd_drift_marks_spec_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            spec = read_yaml(epoch / "SPEC.yaml")
            spec["source_prd_hash"] = "stale"
            write_yaml(epoch / "SPEC.yaml", spec)

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("SPEC_STALE", [finding.code for finding in findings])

    def test_spec_drift_marks_plan_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            plan = epoch / "PLAN.md"
            plan.write_text("---\nsource_spec_hash: stale\n---\n# Plan\n", encoding="utf-8")

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("PLAN_STALE", [finding.code for finding in findings])

    def test_plan_drift_marks_task_queue_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            queue = read_yaml(epoch / "TASK_QUEUE.yaml")
            queue["source_plan_hash"] = "stale"
            write_yaml(epoch / "TASK_QUEUE.yaml", queue)

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("TASK_QUEUE_STALE", [finding.code for finding in findings])

    def test_blocked_next_action_is_written_for_stale_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            finding = StaleFinding(
                code="SPEC_STALE",
                source_path="PRD.md",
                dependent_path="SPEC.yaml",
                expected_hash="old",
                actual_hash="new",
            )

            write_blocked_next_action_for_stale(epoch, [finding])
            text = (epoch / "NEXT_ACTION.md").read_text(encoding="utf-8")

        self.assertIn("STALE HASH BLOCKER", text)
        self.assertIn("SPEC_STALE", text)
        self.assertIn("Do not execute active tasks", text)
