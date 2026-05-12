#!/usr/bin/env python3
"""Tests for creating same-schema research epochs."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class CreateEpochTests(unittest.TestCase):  # noqa: F405
    def test_create_epoch_rejects_next_version_before_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source epoch V0 is not closed", result.stderr + result.stdout)

    def test_create_epoch_from_closed_v0_creates_manifest_complete_v1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_epoch_closeout_complete(research_dir, final_status="closed_stable")

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )
            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])
            current = (research_dir / "CURRENT").read_text(encoding="utf-8").strip()
            v1_prd_exists = (research_dir / "V1" / "PRD.md").exists()
            v1_binding_exists = (research_dir / "V1" / "PAPER_BINDING_DECISION.md").exists()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(current, "V1")
        self.assertTrue(v1_prd_exists)
        self.assertTrue(v1_binding_exists)

    def test_create_epoch_does_not_copy_completed_queue_runs_or_binding_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_epoch_closeout_complete(research_dir, final_status="closed_stable")
            write_yaml(
                research_dir / "V0" / "runs" / "TASK_999_report.yaml",
                {"task": {"version": "V0", "task_id": "TASK_999", "status": "done"}},
            )
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)
            make_paper_binding_decision(research_dir)

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )
            v1_queue = read_yaml(research_dir / "V1" / "TASK_QUEUE.yaml")
            v1_status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            v1_binding = (research_dir / "V1" / "PAPER_BINDING_DECISION.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(list((research_dir / "V1" / "runs").glob("*_report.yaml")))
        self.assertEqual(v1_queue["version"], "V1")
        self.assertEqual(v1_queue["tasks"][0]["status"], "active")
        self.assertEqual(v1_status["status"], "initialized")
        self.assertIn("paper_binding_ready: false", v1_binding)
