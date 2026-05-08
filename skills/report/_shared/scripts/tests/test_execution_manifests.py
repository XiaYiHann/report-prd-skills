#!/usr/bin/env python3
"""Tests for report execution manifest scaffolds and validation."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPT_DIR = SCRIPT_DIR.parent
def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills" / "report-goal" / "scripts" / "generate_report_goal_prompt.py").exists():
            return candidate
    raise RuntimeError(f"cannot resolve repo root from {start}")


REPO_ROOT = _find_repo_root(SCRIPT_DIR)
GOAL_SCRIPT = REPO_ROOT / "skills" / "report-goal" / "scripts" / "generate_report_goal_prompt.py"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from init_report import create_workspace  # noqa: E402
from manifest_validator import validate_execution_manifests  # noqa: E402


def _load_goal_module():
    spec = importlib.util.spec_from_file_location("generate_report_goal_prompt", GOAL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load goal script: {GOAL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


class InitExecutionManifestTests(unittest.TestCase):
    def test_research_prd_scaffolds_machine_contracts_without_fake_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "research-report"

            create_workspace(
                report_dir=root,
                title="研究报告",
                topic="实验与证据链",
                report_type="research-prd",
                audience="mixed",
                author="Codex",
            )

            expected = [
                root / "report.manifest.yaml",
                root / "tasks" / "task_graph.yaml",
                root / "harness" / "harness.yaml",
                root / "evidence" / "evidence_manifest.yaml",
                root / "experiments" / "experiment_manifest.yaml",
            ]
            for path in expected:
                self.assertTrue(path.exists(), f"missing manifest scaffold: {path}")

            task_graph = yaml.safe_load((root / "tasks" / "task_graph.yaml").read_text())
            harness = yaml.safe_load((root / "harness" / "harness.yaml").read_text())
            experiments = yaml.safe_load((root / "experiments" / "experiment_manifest.yaml").read_text())
            evidence = yaml.safe_load((root / "evidence" / "evidence_manifest.yaml").read_text())

            self.assertEqual(task_graph["tasks"], [])
            self.assertEqual(harness["harnesses"], [])
            self.assertEqual(experiments["experiments"], [])
            self.assertEqual(experiments["claims"], [])
            self.assertEqual(evidence["evidence_items"], [])

    def test_engineering_prd_scaffolds_without_research_experiment_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "engineering-report"

            create_workspace(
                report_dir=root,
                title="工程报告",
                topic="执行合同",
                report_type="engineering-prd",
                audience="rookie",
                author="Codex",
            )

            self.assertTrue((root / "report.manifest.yaml").exists())
            self.assertTrue((root / "tasks" / "task_graph.yaml").exists())
            self.assertTrue((root / "harness" / "harness.yaml").exists())
            self.assertTrue((root / "evidence" / "evidence_manifest.yaml").exists())
            self.assertFalse((root / "experiments" / "experiment_manifest.yaml").exists())


class ExecutionManifestValidatorTests(unittest.TestCase):
    def test_rejects_task_without_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            create_workspace(root, "工程报告", "执行合同", "engineering-prd", "rookie", "Codex")
            _write_yaml(
                root / "tasks" / "task_graph.yaml",
                {
                    "schema_version": "1.0",
                    "gates": [{"gate_id": "G01", "tasks": ["T01"]}],
                    "tasks": [{"task_id": "T01", "title": "No harness"}],
                },
            )

            result = validate_execution_manifests(root)

            self.assertFalse(result.execution_ready)
            self.assertTrue(any("T01" in item.message and "harness" in item.message for item in result.issues))

    def test_rejects_unknown_harness_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            create_workspace(root, "工程报告", "执行合同", "engineering-prd", "rookie", "Codex")
            _write_yaml(
                root / "tasks" / "task_graph.yaml",
                {
                    "schema_version": "1.0",
                    "gates": [{"gate_id": "G01", "tasks": ["T01"]}],
                    "tasks": [{"task_id": "T01", "title": "Unknown harness", "harnesses": ["H404"]}],
                },
            )

            result = validate_execution_manifests(root)

            self.assertFalse(result.valid)
            self.assertTrue(any("H404" in item.message for item in result.issues))

    def test_rejects_harness_without_command_or_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            create_workspace(root, "工程报告", "执行合同", "engineering-prd", "rookie", "Codex")
            _write_yaml(
                root / "tasks" / "task_graph.yaml",
                {
                    "schema_version": "1.0",
                    "gates": [{"gate_id": "G01", "tasks": ["T01"]}],
                    "tasks": [{"task_id": "T01", "title": "Harness without command", "harnesses": ["H01"]}],
                },
            )
            _write_yaml(root / "harness" / "harness.yaml", {"schema_version": "1.0", "harnesses": [{"harness_id": "H01"}]})

            result = validate_execution_manifests(root)

            self.assertFalse(result.execution_ready)
            self.assertTrue(any("H01" in item.message and "command" in item.message for item in result.issues))

    def test_rejects_research_claim_without_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            create_workspace(root, "研究报告", "实验", "research-prd", "mixed", "Codex")
            _write_yaml(
                root / "experiments" / "experiment_manifest.yaml",
                {"schema_version": "1.0", "claims": [{"claim_id": "C01", "title": "Unsupported"}], "experiments": []},
            )

            result = validate_execution_manifests(root)

            self.assertFalse(result.valid)
            self.assertTrue(any("C01" in item.message and "experiment" in item.message for item in result.issues))

    def test_rejects_mock_final_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            create_workspace(root, "工程报告", "证据", "engineering-prd", "rookie", "Codex")
            _write_yaml(
                root / "evidence" / "evidence_manifest.yaml",
                {
                    "schema_version": "1.0",
                    "evidence_items": [
                        {
                            "evidence_id": "EV01",
                            "role": "final",
                            "source_kind": "mock",
                            "task_id": "T01",
                            "harness_id": "H01",
                        }
                    ],
                },
            )

            result = validate_execution_manifests(root)

            self.assertFalse(result.valid)
            self.assertTrue(any("EV01" in item.message and "mock" in item.message for item in result.issues))


class ReportGoalManifestGateTests(unittest.TestCase):
    def test_missing_manifest_generates_repair_goal_by_default(self) -> None:
        goal_module = _load_goal_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            report = repo / "docs" / "report" / "report.md"
            report.parent.mkdir(parents=True)
            report.write_text("# Test Report\n\n## Milestone\n\n- Implement feature.\n", encoding="utf-8")

            extraction = goal_module.extract_report_context(report)
            evidence = goal_module.extract_report_evidence(report, 10)
            scan = goal_module.scan_repo(repo, extraction.path_hints)
            validation = goal_module.validate_manifest_inputs(repo, report)
            prompt = goal_module.build_prompt(repo, report, evidence, extraction, scan, "short", None, validation, False)

            self.assertIn("report-repair goal", prompt)
            self.assertIn("补齐 execution manifests", prompt)
            self.assertNotIn("Gate 2..N", prompt)

    def test_valid_manifest_compiles_task_graph_and_harness_commands(self) -> None:
        goal_module = _load_goal_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            workspace = repo / "docs" / "report" / "compiled"
            create_workspace(workspace, "工程报告", "执行合同", "engineering-prd", "rookie", "Codex")
            report = repo / "docs" / "report" / "report.md"
            report.write_text("# Engineering Report\n\n## Gate\n\n- T01 must run H01.\n", encoding="utf-8")
            _write_yaml(
                workspace / "tasks" / "task_graph.yaml",
                {
                    "schema_version": "1.0",
                    "gates": [{"gate_id": "G01", "title": "Implement", "tasks": ["T01"]}],
                    "tasks": [{"task_id": "T01", "title": "Run validator", "harnesses": ["H01"]}],
                },
            )
            _write_yaml(
                workspace / "harness" / "harness.yaml",
                {
                    "schema_version": "1.0",
                    "harnesses": [
                        {
                            "harness_id": "H01",
                            "type": "unit",
                            "command": ["python3 -m pytest tests/test_manifest.py"],
                            "required_outputs": [{"path": "report-goal/evidence/gate-1-test-output.txt"}],
                        }
                    ],
                },
            )

            extraction = goal_module.extract_report_context(report)
            evidence = goal_module.extract_report_evidence(report, 10)
            scan = goal_module.scan_repo(repo, extraction.path_hints)
            validation = goal_module.validate_manifest_inputs(repo, report)
            prompt = goal_module.build_prompt(repo, report, evidence, extraction, scan, "short", None, validation, False)

            self.assertIn("manifest-gated implementation goal", prompt)
            self.assertIn("T01", prompt)
            self.assertIn("H01", prompt)
            self.assertIn("python3 -m pytest tests/test_manifest.py", prompt)


if __name__ == "__main__":
    unittest.main()
