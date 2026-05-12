#!/usr/bin/env python3
"""Hard-gate audit checks for epoch research workspaces."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


AUDIT_CHECKS_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "audit_checks.py"  # noqa: F405


class AuditChecksTests(unittest.TestCase):  # noqa: F405
    def test_evidence_audit_rejects_done_task_without_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(
                ["python3", str(AUDIT_CHECKS_SCRIPT), "--research-dir", str(research_dir), "--mode", "evidence"],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_run_report", result.stdout)

    def test_evidence_audit_rejects_done_report_without_exit_code_and_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)
            write_yaml(
                research_dir / "V0" / "runs" / "TASK_001_report.yaml",
                {
                    "task": {"version": "V0", "task_id": "TASK_001", "status": "done"},
                    "execution": {"executor": "codex", "commands_run": [], "exit_code": None},
                    "evidence": {"tests": {"passed": False, "output_path": None}, "artifacts": []},
                },
            )

            result = run_cmd(
                ["python3", str(AUDIT_CHECKS_SCRIPT), "--research-dir", str(research_dir), "--mode", "evidence"],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_exit_code", result.stdout)
        self.assertIn("evidence.done_task_has_artifact_hash", result.stdout)

    def test_generate_research_audit_writes_machine_readable_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(AUDIT_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-12",
                    "--mode",
                    "full",
                    "--force",
                ],
                cwd=repo,
            )
            audit_results = research_dir / "V0" / "audits" / "2026-05-12-audit" / "audit_results.yaml"
            audit_results_exists = audit_results.exists()
            payload = read_yaml(audit_results) if audit_results_exists else {}

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(audit_results_exists)
        self.assertIn("checks", payload)

    def test_audit_ready_fails_when_evidence_hard_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_run_report", result.stdout)
