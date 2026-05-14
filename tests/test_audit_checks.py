#!/usr/bin/env python3
"""Hard-gate audit checks for epoch research workspaces."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403
import sys


AUDIT_CHECKS_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "audit_checks.py"  # noqa: F405
SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    check_gate_evidence_completeness,
    check_paper_claim_ledger,
    check_reproduction_claim_boundaries,
)


class AuditChecksTests(unittest.TestCase):  # noqa: F405
    def test_evidence_audit_rejects_done_task_without_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
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
            research_dir = init_workspace_fast(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)
            task_id = queue["tasks"][0]["task_id"]
            write_yaml(
                research_dir / "V0" / "runs" / f"{task_id}_report.yaml",
                {
                    "task": {"version": "V0", "task_id": task_id, "status": "done"},
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
            research_dir = init_workspace_fast(repo)

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
            research_dir = init_workspace_fast(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_run_report", result.stdout)

    def test_init_workspace_writes_audit_and_review_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            self.assertTrue((epoch / "AUDIT_QUEUE.yaml").exists())
            self.assertTrue((epoch / "HUMAN_REVIEW_REQUESTS.yaml").exists())
            self.assertTrue((epoch / "PAPER_CLAIM_LEDGER.yaml").exists())
            self.assertTrue((epoch / "wiki" / "insight_index.yaml").exists())

    def test_audit_fails_completed_task_without_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            queue = read_yaml(epoch / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "completed"
            write_yaml(epoch / "TASK_QUEUE.yaml", queue)

            findings = check_gate_evidence_completeness(epoch)

        self.assertIn("missing_run_report", [finding.check_id for finding in findings])
        self.assertTrue(any(finding.severity == "P0" for finding in findings))

    def test_audit_fails_mock_backed_paper_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            write_yaml(
                epoch / "PAPER_CLAIM_LEDGER.yaml",
                {
                    "schema_version": 1,
                    "epoch": "V0",
                    "claims": [
                        {
                            "claim_id": "C1",
                            "status": "allowed",
                            "current_evidence": {"run_reports": ["runs/T_G0_001_report.yaml"]},
                        }
                    ],
                },
            )
            write_yaml(
                epoch / "runs" / "T_G0_001_report.yaml",
                {
                    "schema_version": 2,
                    "anti_mock": {"dataset_type": "mock"},
                    "conclusion": {"research_interpretation_allowed": False},
                    "command": {"exit_code": 0},
                },
            )

            findings = check_paper_claim_ledger(epoch)

        self.assertIn("mock_evidence_supports_paper_claim", [finding.check_id for finding in findings])

    def test_audit_fails_smoke_only_reproduction_backed_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            index = read_yaml(epoch / "reproduction" / "REPRODUCTION_INDEX.yaml")
            index["items"] = [
                {
                    "repro_id": "R_SMOKE",
                    "reproduction_type": "official_code",
                    "status": "smoke_passed",
                    "evidence_level": "official_smoke_only",
                    "audit_status": "passed",
                    "claim_support_level": "sanity_only",
                }
            ]
            write_yaml(epoch / "reproduction" / "REPRODUCTION_INDEX.yaml", index)
            write_yaml(
                epoch / "PAPER_CLAIM_LEDGER.yaml",
                {
                    "claims": [
                        {
                            "claim_id": "C1",
                            "status": "allowed",
                            "current_evidence": {"reproductions": ["R_SMOKE"]},
                        }
                    ]
                },
            )

            findings = check_reproduction_claim_boundaries(epoch)

        self.assertIn("unsupported_reproduction_claim_evidence", [finding.check_id for finding in findings])
