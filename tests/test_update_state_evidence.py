#!/usr/bin/env python3
"""Structured evidence submission tests for update_state.py."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class UpdateStateEvidenceTests(unittest.TestCase):  # noqa: F405
    def test_update_state_records_executor_commands_exit_code_and_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            runs = research_dir / "V0" / "runs"
            artifacts = research_dir / "V0" / "artifacts"
            runs.mkdir(parents=True, exist_ok=True)
            artifacts.mkdir(parents=True, exist_ok=True)
            stdout_path = runs / "TASK_001.stdout.txt"
            stderr_path = runs / "TASK_001.stderr.txt"
            test_output = runs / "TASK_001.pytest.txt"
            artifact = artifacts / "result.json"
            stdout_path.write_text("pytest passed\n", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            test_output.write_text("1 passed\n", encoding="utf-8")
            artifact.write_text('{"metric": 1.0}\n', encoding="utf-8")

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "codex",
                    "--command",
                    "python3 -m pytest tests/test_epoch_manifest_contract.py -v",
                    "--stdout-path",
                    "docs/research/V0/runs/TASK_001.stdout.txt",
                    "--stderr-path",
                    "docs/research/V0/runs/TASK_001.stderr.txt",
                    "--exit-code",
                    "0",
                    "--test-command",
                    "python3 -m pytest tests/test_epoch_manifest_contract.py -v",
                    "--test-output-path",
                    "docs/research/V0/runs/TASK_001.pytest.txt",
                    "--tests-passed",
                    "true",
                    "--artifact",
                    "docs/research/V0/artifacts/result.json:sha256=abc123",
                    "--file-changed",
                    "skills/research-init/_shared/scripts/research_workspace.py",
                    "--dirty-tree-after-task",
                    "false",
                ],
                cwd=repo,
            )
            report = read_yaml(research_dir / "V0" / "runs" / "TASK_001_report.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["execution"]["executor"], "codex")
        self.assertEqual(report["execution"]["exit_code"], 0)
        self.assertEqual(report["execution"]["commands_run"], ["python3 -m pytest tests/test_epoch_manifest_contract.py -v"])
        self.assertEqual(report["execution"]["stdout_path"], "docs/research/V0/runs/TASK_001.stdout.txt")
        self.assertEqual(report["execution"]["stderr_path"], "docs/research/V0/runs/TASK_001.stderr.txt")
        self.assertTrue(report["evidence"]["tests"]["passed"])
        self.assertEqual(report["evidence"]["tests"]["commands"], ["python3 -m pytest tests/test_epoch_manifest_contract.py -v"])
        self.assertEqual(report["evidence"]["tests"]["output_path"], "docs/research/V0/runs/TASK_001.pytest.txt")
        self.assertEqual(report["evidence"]["artifacts"][0]["path"], "docs/research/V0/artifacts/result.json")
        self.assertEqual(report["evidence"]["artifacts"][0]["sha256"], "abc123")
        self.assertEqual(report["execution"]["files_changed"], ["skills/research-init/_shared/scripts/research_workspace.py"])
        self.assertFalse(report["git"]["dirty_tree_after_task"])

    def test_update_state_rejects_unknown_executor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace_fast(repo)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "local-shell",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_update_state_rejects_malformed_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace_fast(repo)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "codex",
                    "--artifact",
                    "docs/research/V0/artifacts/result.json",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact must use path:sha256=<digest>", result.stderr + result.stdout)
