#!/usr/bin/env python3
"""Stale hash detection tests for gate-aware research loop."""

from __future__ import annotations

import sys

import pytest

from research_workflow_helpers import *  # noqa: F403


SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    StaleFinding,
    detect_epoch_stale_hashes,
)

pytestmark = pytest.mark.integration


class StaleHashDetectionTests(unittest.TestCase):  # noqa: F405
    def test_spine_drift_marks_task_queue_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            queue = read_yaml(epoch / "TASK_QUEUE.yaml")
            queue["source_spine_hash"] = "stale"
            write_yaml(epoch / "TASK_QUEUE.yaml", queue)

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("TASK_QUEUE_STALE", [finding.code for finding in findings])

    def test_prd_drift_marks_spine_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            spine = read_yaml(epoch / "RESEARCH_SPINE.yaml")
            spine["source_prd_hash"] = "stale"
            write_yaml(epoch / "RESEARCH_SPINE.yaml", spine)

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("SPINE_STALE", [finding.code for finding in findings])
