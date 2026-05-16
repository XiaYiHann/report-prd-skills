#!/usr/bin/env python3
"""Reproduction index schema validation tests."""

from __future__ import annotations

import sys

import pytest

from research_workflow_helpers import *  # noqa: F403


SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import validate_epoch_schema  # noqa: E402

pytestmark = pytest.mark.integration


class ReproductionIndexValidationTests(unittest.TestCase):  # noqa: F405
    def test_default_reproduction_index_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            issues = validate_epoch_schema(research_dir)

        self.assertEqual([], [issue for issue in issues if "reproduction" in str(issue).lower()])

    def test_invalid_reproduction_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            index_path = research_dir / "V0" / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [
                {
                    "repro_id": "R_BAD",
                    "short_name": "Bad",
                    "reproduction_type": "guessed_baseline",
                    "status": "pending",
                    "evidence_level": "literature_only",
                }
            ]
            write_yaml(index_path, index)

            issues = validate_epoch_schema(research_dir)

        self.assertTrue(any("invalid reproduction_type" in str(issue) for issue in issues))

    def test_invalid_reproduction_status_and_evidence_level_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            index_path = research_dir / "V0" / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [
                {
                    "repro_id": "R_BAD",
                    "short_name": "Bad",
                    "reproduction_type": "official_code",
                    "status": "paper_disproved",
                    "evidence_level": "claim_ready_without_audit",
                }
            ]
            write_yaml(index_path, index)

            issues = validate_epoch_schema(research_dir)

        self.assertTrue(any("invalid reproduction status" in str(issue) for issue in issues))
        self.assertTrue(any("invalid evidence_level" in str(issue) for issue in issues))

    def test_invalid_reproduction_reuse_status_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            ledger_path = research_dir / "V0" / "reproduction" / "REPRODUCTION_LEDGER.yaml"
            ledger = read_yaml(ledger_path)
            ledger["assets"] = [{"asset_id": "REPRO_BAD", "reuse_status": "trust_me"}]
            ledger["coverage_checks"] = [{"rq_id": "RQ01", "status": "already_good"}]
            write_yaml(ledger_path, ledger)

            issues = validate_epoch_schema(research_dir)

        self.assertTrue(any("invalid reproduction reuse_status" in str(issue) for issue in issues))
        self.assertTrue(any("invalid reproduction coverage status" in str(issue) for issue in issues))


if __name__ == "__main__":
    unittest.main()
