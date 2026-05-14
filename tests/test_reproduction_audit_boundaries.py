#!/usr/bin/env python3
"""Reproduction audit boundary tests."""

from __future__ import annotations

import sys

from research_workflow_helpers import *  # noqa: F403


SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import run_epoch_audit_checks  # noqa: E402


class ReproductionAuditBoundaryTests(unittest.TestCase):  # noqa: F405
    def test_literature_only_reproduction_cannot_support_allowed_paper_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch_dir = research_dir / "V0"
            index_path = epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [
                {
                    "repro_id": "R_LIT",
                    "short_name": "LitOnly",
                    "reproduction_type": "literature_only_not_executable",
                    "status": "planned",
                    "evidence_level": "literature_only",
                    "audit_status": "passed",
                    "claim_support_level": "none",
                }
            ]
            write_yaml(index_path, index)
            write_yaml(
                epoch_dir / "PAPER_CLAIM_LEDGER.yaml",
                {
                    "claims": [
                        {
                            "claim_id": "C1",
                            "status": "allowed",
                            "required_evidence": {"reproductions": ["R_LIT"]},
                            "current_evidence": {"reproductions": ["R_LIT"]},
                        }
                    ]
                },
            )

            findings = run_epoch_audit_checks(research_dir, mode="evidence")

        self.assertTrue(any(item.check_id == "unsupported_reproduction_claim_evidence" for item in findings))

    def test_reproduction_without_passed_audit_cannot_support_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch_dir = research_dir / "V0"
            index_path = epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [
                {
                    "repro_id": "R_FULL",
                    "short_name": "Full",
                    "reproduction_type": "official_code",
                    "status": "full_passed",
                    "evidence_level": "official_full_reproduction",
                    "audit_status": "pending",
                    "claim_support_level": "full",
                }
            ]
            write_yaml(index_path, index)
            write_yaml(
                epoch_dir / "PAPER_CLAIM_LEDGER.yaml",
                {
                    "claims": [
                        {
                            "claim_id": "C1",
                            "status": "allowed",
                            "current_evidence": {"reproductions": ["R_FULL"]},
                        }
                    ]
                },
            )

            findings = run_epoch_audit_checks(research_dir, mode="evidence")

        self.assertTrue(any(item.check_id == "reproduction_audit_not_passed" for item in findings))


if __name__ == "__main__":
    unittest.main()
