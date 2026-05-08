#!/usr/bin/env python3
"""Tests for report-spec helper scripts."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills" / "report-spec" / "scripts").exists():
            return candidate
    raise RuntimeError(f"cannot resolve repo root from {start}")


REPO_ROOT = _find_repo_root(SCRIPT_DIR)
GENERATE_SCRIPT = REPO_ROOT / "skills" / "report-spec" / "scripts" / "generate_report_spec.py"
VALIDATE_SCRIPT = REPO_ROOT / "skills" / "report-spec" / "scripts" / "validate_report_spec.py"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


class ReportSpecScriptTests(unittest.TestCase):
    def test_generate_report_spec_creates_v2_spec_scaffold_without_fake_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "docs" / "report" / "slug"
            (workspace / "main").mkdir(parents=True)
            (workspace / "main" / "main.md").write_text("# Main\n\n## Task Graph\n\nTBD.\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(GENERATE_SCRIPT), "--workspace", str(workspace)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            spec_dir = workspace / "spec"
            expected = [
                "execution_spec.yaml",
                "experiment_manifest.yaml",
                "task_graph.yaml",
                "harness.yaml",
                "dataset_manifest.yaml",
                "model_manifest.yaml",
                "baseline_manifest.yaml",
                "metric_manifest.yaml",
                "seed_protocol.yaml",
                "evidence_contract.yaml",
                "anti_mock_policy.yaml",
                "codex_goal.md",
                "spec_gap_report.md",
            ]
            for relative_path in expected:
                self.assertTrue((spec_dir / relative_path).exists(), relative_path)

            task_graph = yaml.safe_load((spec_dir / "task_graph.yaml").read_text(encoding="utf-8"))
            experiments = yaml.safe_load((spec_dir / "experiment_manifest.yaml").read_text(encoding="utf-8"))
            self.assertEqual(task_graph["milestones"], [])
            self.assertEqual(task_graph["gates"], [])
            self.assertEqual(task_graph["tasks"], [])
            self.assertEqual(experiments["experiments"], [])
            self.assertEqual(experiments["claims"], [])

    def test_validate_report_spec_accepts_execution_ready_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp) / "spec"
            _write_yaml(
                spec_dir / "task_graph.yaml",
                {
                    "schema_version": "1.0",
                    "milestones": [{"milestone_id": "M01", "gate_id": "G01"}],
                    "gates": [{"gate_id": "G01", "tasks": ["T01"]}],
                    "tasks": [
                        {
                            "task_id": "T01",
                            "title": "Run harness",
                            "harnesses": ["H01"],
                            "acceptance_criteria": ["H01 passes"],
                        }
                    ],
                },
            )
            _write_yaml(
                spec_dir / "harness.yaml",
                {
                    "schema_version": "1.0",
                    "harnesses": [{"harness_id": "H01", "command": ["python3 -m pytest tests"]}],
                },
            )
            _write_yaml(
                spec_dir / "evidence_contract.yaml",
                {
                    "schema_version": "1.0",
                    "evidence_rules": {"forbidden_as_claim_evidence": ["mock_result"]},
                },
            )

            result = subprocess.run(
                ["python3", str(VALIDATE_SCRIPT), "--spec", str(spec_dir)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("execution-ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
