#!/usr/bin/env python3
"""Manifest contract tests for strict epoch schema invariance."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    EPOCH_MANIFEST_PATH,
    EPOCH_REQUIRED_FILES,
    EPOCH_WIKI_FILES,
    epoch_required_files,
    epoch_reproduction_files,
    epoch_search_files,
    epoch_wiki_files,
    load_epoch_manifest,
)


class EpochManifestContractTests(unittest.TestCase):
    def test_manifest_exists_and_declares_epoch_v1_schema(self) -> None:
        self.assertTrue(EPOCH_MANIFEST_PATH.exists())

        manifest = load_epoch_manifest()

        self.assertEqual(manifest["schema_version"], "epoch_v1")
        self.assertEqual(manifest["epoch_dir_pattern"], r"V\d+")

    def test_manifest_required_files_match_runtime_constants(self) -> None:
        required = epoch_required_files()

        self.assertEqual(required, EPOCH_REQUIRED_FILES)
        self.assertEqual(
            required,
            [
                "PRD.tex",
                "PRD_SUMMARY.md",
                "goal.md",
                "RESEARCH_SPINE.yaml",
                "SPEC.yaml",
                "PLAN.md",
                "STATUS.yaml",
                "TASK_QUEUE.yaml",
                "LOOP_LOG.md",
                "GIT_STATE.yaml",
                "git_log.md",
                "AUDIT_QUEUE.yaml",
                "HUMAN_REVIEW_REQUESTS.yaml",
                "PAPER_CLAIM_LEDGER.yaml",
                "closeout.md",
                "PAPER_BINDING_DECISION.md",
            ],
        )

    def test_manifest_wiki_files_match_runtime_constants(self) -> None:
        wiki_files = epoch_wiki_files()

        self.assertEqual(wiki_files, EPOCH_WIKI_FILES)
        self.assertEqual(
            wiki_files,
            [
                "epoch_summary.md",
                "evidence_map.md",
                "positive_signals.md",
                "negative_results.md",
                "failed_paths.md",
                "baseline_landscape.md",
                "literature_notes.md",
                "open_questions.md",
                "next_version_seed.md",
                "insight_index.yaml",
            ],
        )

    def test_manifest_declares_search_and_reproduction_metadata_files(self) -> None:
        self.assertEqual(
            epoch_search_files(),
            [
                "search_report.md",
                "web_search_log.yaml",
                "repo_search_log.yaml",
                "candidate_baselines.yaml",
                "candidate_reproductions.yaml",
            ],
        )
        self.assertEqual(
            epoch_reproduction_files(),
            [
                "REPRODUCTION_INDEX.yaml",
                "REPRODUCTION_PLAN.md",
                "REPRODUCTION_DELTA.yaml",
            ],
        )

    def test_missing_manifest_fails_with_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing_manifest.yaml"

            with self.assertRaises(FileNotFoundError) as raised:
                load_epoch_manifest(missing)

        self.assertIn("epoch manifest not found", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
