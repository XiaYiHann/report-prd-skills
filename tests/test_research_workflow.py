#!/usr/bin/env python3
"""Regression tests for the research execution skill family."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
import os
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = REPO_ROOT / "skills" / "research-init" / "scripts" / "init_research.py"
VALIDATE_SCRIPT = REPO_ROOT / "skills" / "research-spec" / "scripts" / "validate_research.py"
PLAN_SCRIPT = REPO_ROOT / "skills" / "research-plan" / "scripts" / "generate_research_plan.py"
PPT_SCRIPT = REPO_ROOT / "skills" / "research-ppt" / "scripts" / "generate_research_ppt.py"
AUDIT_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "generate_research_audit.py"
INSTALL_SCRIPT = REPO_ROOT / "install.sh"
SKILL_NAMES = [
    "report",
    "research-init",
    "research-prd",
    "research-paper",
    "research-spec",
    "research-plan",
    "research-audit",
    "research-ppt",
]


def run_cmd(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd or REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def init_workspace(repo: Path) -> Path:
    result = run_cmd(
        [
            "python3",
            str(INIT_SCRIPT),
            "--repo",
            str(repo),
            "--title",
            "Test Research",
            "--purpose",
            "minimal-regression",
        ]
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return repo / "docs" / "research"


def make_execution_ready_spec(research_dir: Path) -> None:
    write_yaml(
        research_dir / "spec" / "global_spec.yaml",
        {
            "schema_version": 1,
            "source": {"prd": "docs/research/prd/research_prd.md"},
            "rq_chain": [
                {
                    "rq_id": "RQ1",
                    "hypothesis_id": "HYP1",
                    "claim_id": "C01",
                    "experiment_id": "E01",
                    "dataset_id": "D01",
                    "model_id": "M_OURS",
                    "baseline_id": "B01",
                    "metric_id": "M01",
                    "seed_protocol_id": "S01",
                    "task_id": "T_E01",
                    "harness_id": "H_E01_FULL",
                    "evidence_id": "EV_E01",
                    "paper_placeholder": "{{E01.OURS.primary_metric}}",
                }
            ],
        },
    )
    write_yaml(
        research_dir / "spec" / "shared" / "dataset_manifest.yaml",
        {
            "schema_version": 1,
            "datasets": [
                {
                    "dataset_id": "D01",
                    "name": "Dataset One",
                    "split_file": "data/splits/D01_frozen_split_v1.json",
                    "preprocessing_config": "configs/preprocess/D01_v1.yaml",
                }
            ],
        },
    )
    write_yaml(
        research_dir / "spec" / "shared" / "metric_manifest.yaml",
        {"schema_version": 1, "metrics": [{"metric_id": "M01", "name": "primary_metric"}]},
    )
    write_yaml(
        research_dir / "spec" / "shared" / "model_manifest.yaml",
        {"schema_version": 1, "models": [{"model_id": "M_OURS", "name": "Our method"}]},
    )
    write_yaml(
        research_dir / "spec" / "shared" / "seed_protocol.yaml",
        {"schema_version": 1, "seed_protocols": [{"seed_protocol_id": "S01", "seeds": [1, 2, 3]}]},
    )
    write_yaml(
        research_dir / "spec" / "shared" / "evidence_contract.yaml",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C01",
                    "required_experiments": ["E01"],
                    "required_harnesses": ["H_E01_FULL"],
                    "paper_placeholders": ["{{E01.OURS.primary_metric}}"],
                }
            ],
            "evidence_rules": {
                "forbidden_as_claim_evidence": [
                    "mock_result",
                    "toy_result",
                    "smoke_test_only",
                    "synthetic_data_unless_declared",
                ]
            },
        },
    )
    write_yaml(
        research_dir / "spec" / "shared" / "anti_mock_policy.yaml",
        {
            "schema_version": 1,
            "forbidden_for": [
                "research_claim",
                "benchmark_result",
                "ablation_result",
                "paper_table",
                "paper_figure",
                "go_no_go_decision",
            ],
        },
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_manifest.yaml",
        {
            "schema_version": 1,
            "experiments": [
                {
                    "experiment_id": "E01",
                    "title": "Main comparison",
                    "linked_rq": "RQ1",
                    "hypothesis": "HYP1",
                    "claim": "C01",
                    "purpose": "Test whether the proposed method improves the primary metric.",
                    "status": "planned",
                    "dataset": "D01",
                    "split_file": "data/splits/D01_frozen_split_v1.json",
                    "preprocessing_config": "configs/preprocess/D01_v1.yaml",
                    "models": ["M_OURS"],
                    "proposed_method_config": "configs/experiments/E01/ours.yaml",
                    "baselines": ["B01"],
                    "seeds": [1, 2, 3],
                    "metrics": ["M01"],
                    "statistical_protocol": "paired bootstrap over frozen splits",
                    "commands": {
                        "run": "python -m project.experiments.run --experiment E01 --seed {seed}",
                        "aggregate": "python -m project.experiments.aggregate --experiment E01",
                    },
                    "required_artifacts": [
                        "artifacts/experiments/E01/raw/{seed}/metrics.json",
                        "artifacts/experiments/E01/aggregate/summary.json",
                    ],
                    "harnesses": ["H_E01_FULL"],
                    "support_condition": "OURS improves M01 under declared seeds.",
                    "falsification_condition": "OURS does not improve M01 or confidence interval crosses zero.",
                    "mock_policy": "mock outputs may only support unit or smoke tests",
                }
            ],
            "claims": [{"claim_id": "C01", "experiment_ids": ["E01"]}],
        },
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        {
            "schema_version": 1,
            "tasks": [
                {
                    "task_id": "T_E01",
                    "title": "Run E01",
                    "harnesses": ["H_E01_FULL"],
                    "acceptance_criteria": ["all declared seeds completed"],
                }
            ],
            "gates": [{"gate_id": "G_E01", "tasks": ["T_E01"], "harnesses": ["H_E01_FULL"]}],
        },
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        {
            "schema_version": 1,
            "harnesses": [
                {
                    "harness_id": "H_E01_FULL",
                    "type": "full_experiment",
                    "linked_experiment": "E01",
                    "purpose": "Validate full E01 evidence.",
                    "cwd": ".",
                    "command": "python -m project.harness verify E01",
                    "timeout": 7200,
                    "required_inputs": ["data/splits/D01_frozen_split_v1.json"],
                    "required_outputs": [
                        {"path": "artifacts/experiments/E01/aggregate/summary.json", "schema": "artifact_schema"}
                    ],
                    "pass_criteria": [
                        "all_declared_seeds_completed",
                        "all_declared_baselines_completed",
                        "no_mock_data_used",
                        "no_missing_metric",
                        "no_test_tuning",
                        "artifact_hashes_recorded",
                    ],
                    "evidence_capture": ["stdout", "stderr", "artifact_hashes"],
                    "may_support_research_claim": True,
                    "independent_rerun_required": True,
                    "mock_policy": {"may_support_research_claim": False},
                }
            ],
        },
    )
    write_yaml(
        research_dir / "spec" / "reproduction" / "reproduction_manifest.yaml",
        {
            "schema_version": 1,
            "reproduction_targets": [
                {
                    "reproduction_id": "R_B01",
                    "baseline_id": "B01",
                    "paper_id": "P01",
                    "title": "Baseline One",
                    "role": ["main_baseline"],
                    "reproduction_mode": "official_code_reuse",
                    "source": {
                        "paper_url": "https://example.invalid/paper",
                        "code_url": "https://example.invalid/code",
                        "code_commit": "abc123",
                        "license": "PLACEHOLDER_LICENSE",
                    },
                    "dataset": {"dataset_id": "D01"},
                    "metrics": [{"metric_id": "M01"}],
                    "commands": {"smoke": ["bash scripts/reproduction/B01/run_smoke.sh"]},
                    "required_artifacts": ["artifacts/reproduction/B01/aggregate/summary.json"],
                    "harnesses": ["H_R_B01_SMOKE"],
                    "acceptance_criteria": ["official_code_commit_recorded"],
                    "can_support_main_experiment": True,
                }
            ],
        },
    )
    write_yaml(
        research_dir / "spec" / "reproduction" / "reproduction_task_graph.yaml",
        {
            "schema_version": 1,
            "tasks": [{"task_id": "T_R_B01", "harnesses": ["H_R_B01_SMOKE"], "acceptance_criteria": ["smoke passes"]}],
            "gates": [{"gate_id": "G_R_B01", "tasks": ["T_R_B01"], "harnesses": ["H_R_B01_SMOKE"]}],
        },
    )
    write_yaml(
        research_dir / "spec" / "reproduction" / "reproduction_harness.yaml",
        {
            "schema_version": 1,
            "harnesses": [
                {
                    "harness_id": "H_R_B01_SMOKE",
                    "type": "reproduction_smoke",
                    "linked_reproduction": "R_B01",
                    "cwd": ".",
                    "command": "bash scripts/reproduction/B01/run_smoke.sh",
                    "timeout": 600,
                    "required_inputs": [],
                    "required_outputs": [{"path": "artifacts/reproduction/B01/raw/smoke/metrics.json"}],
                    "pass_criteria": ["declared_dataset_and_metric_used"],
                    "evidence_capture": ["stdout", "stderr"],
                    "may_support_research_claim": False,
                    "independent_rerun_required": False,
                }
            ],
        },
    )


def make_valid_paper(research_dir: Path) -> None:
    (research_dir / "paper").mkdir(parents=True, exist_ok=True)
    (research_dir / "paper" / "planned_paper.md").write_text(
        "\n".join(
            [
                "# Test Research",
                "",
                "We propose a method for the declared research problem.",
                "Experiment E01 tests whether the method improves the primary metric.",
                "Table 1 reports {{E01.OURS.primary_metric}} after execution.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_yaml(
        research_dir / "paper" / "placeholder_map.yaml",
        {
            "placeholders": [
                {
                    "placeholder": "{{E01.OURS.primary_metric}}",
                    "experiment_id": "E01",
                    "method_id": "OURS",
                    "metric": "primary_metric",
                    "source_after_execution": "artifacts/experiments/E01/aggregate/summary.json",
                    "paper_location": "Table 1 / Main Results",
                }
            ]
        },
    )


class ResearchWorkflowTests(unittest.TestCase):
    def test_installer_installs_research_family_and_removes_old_report_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            for old_name in [
                "report",
                "report-init",
                "report-update",
                "report-audit",
                "report-goal",
                "report-paper",
                "report-spec",
                "report-brainstorming",
                "research-writing",
                "research-evidence",
            ]:
                (target / old_name).mkdir(parents=True)
                (target / old_name / "SKILL.md").write_text("old\n", encoding="utf-8")
            env = os.environ.copy()
            env["RESEARCH_EXECUTION_SKILLS_SOURCE_DIR"] = str(REPO_ROOT)
            env["RESEARCH_EXECUTION_SKILLS_TARGET_DIR"] = str(target)

            result = subprocess.run(
                ["bash", str(INSTALL_SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for skill_name in SKILL_NAMES:
                self.assertTrue((target / skill_name / "SKILL.md").exists(), skill_name)
            for old_name in [
                "report-init",
                "report-update",
                "report-audit",
                "report-goal",
                "report-paper",
                "report-spec",
                "report-brainstorming",
                "research-writing",
                "research-evidence",
            ]:
                self.assertFalse((target / old_name).exists(), old_name)
            self.assertIn("Legacy Report Router", (target / "report" / "SKILL.md").read_text(encoding="utf-8"))
            self.assertIn("Migrated existing skill directories to research-*", result.stdout)
            self.assertIn("report -> legacy research migration router", result.stdout)
            self.assertIn("report-init -> removed", result.stdout)
            self.assertIn("Installed research execution skill family", result.stdout)

    def test_research_init_scaffolds_docs_research_tree_and_required_prd_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))

            expected_dirs = ["prd", "paper", "spec", "plans", "ppt", "audits"]
            for dirname in expected_dirs:
                self.assertTrue((research_dir / dirname).exists(), dirname)
            prd = (research_dir / "prd" / "research_prd.md").read_text(encoding="utf-8")
            self.assertIn("# Research PRD", prd)
            self.assertIn("## 4. Benchmark and Reproduction Plan", prd)
            self.assertIn("## 11. Task Graph and Student Work Plan", prd)
            self.assertIn("## 13. Evidence Ledger", prd)
            self.assertNotIn("Reader Model and Usage", prd)

    def test_valid_paper_placeholders_pass_paper_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("[OK] paper-ready", result.stdout)

    def test_invalid_paper_fake_results_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            paper = research_dir / "paper" / "planned_paper.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\nExperiments show that our method outperforms B01.\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unvalidated empirical result language", result.stdout)

    def test_invalid_paper_unbound_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            paper = research_dir / "paper" / "planned_paper.md"
            paper.write_text(paper.read_text(encoding="utf-8") + "\nTable 2 reports {{E99.OURS.primary_metric}}.\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unregistered placeholder", result.stdout)

    def test_spec_ready_rejects_missing_experiment_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            harness_path = research_dir / "spec" / "experiments" / "experiment_harness.yaml"
            harness_payload = read_yaml(harness_path)
            harness_payload["harnesses"] = []
            write_yaml(harness_path, harness_payload)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spec-ready"])

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("H_E01_FULL", result.stdout)

    def test_plan_ready_rejects_stale_spec_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-09",
                    "--purpose",
                    "reproduce-b01",
                    "--track",
                    "reproduction",
                ],
                cwd=repo,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            spec = research_dir / "spec" / "global_spec.yaml"
            spec.write_text(spec.read_text(encoding="utf-8") + "\n# drift after plan creation\n", encoding="utf-8")

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "plan-ready"])

            self.assertNotEqual(check.returncode, 0)
            self.assertIn("stale spec hash", check.stdout)

    def test_ppt_ready_rejects_missing_slide_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            result = run_cmd(["python3", str(PPT_SCRIPT), "--research-dir", str(research_dir), "--mode", "standard"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (research_dir / "ppt" / "main_deck" / "slide_prompts" / "03_rq.md").unlink()

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "ppt-ready"])

            self.assertNotEqual(check.returncode, 0)
            self.assertIn("missing slide prompt", check.stdout)

    def test_audit_generation_produces_required_alignment_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)
            make_valid_paper(research_dir)
            run_cmd(["python3", str(PPT_SCRIPT), "--research-dir", str(research_dir), "--mode", "standard"])
            result = run_cmd(["python3", str(AUDIT_SCRIPT), "--research-dir", str(research_dir), "--date", "2026-05-09"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            audit_dir = research_dir / "audits" / "2026-05-09-audit"
            for name in ["audit_report.md", "alignment_matrix.yaml", "drift_findings.yaml", "repair_plan.md"]:
                self.assertTrue((audit_dir / name).exists(), name)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
