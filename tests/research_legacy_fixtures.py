#!/usr/bin/env python3
"""Legacy research workflow fixtures."""

from __future__ import annotations

from research_workflow_common import *  # noqa: F403


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
                    "data_source_type": "real_dataset",
                    "provenance": "public benchmark manifest for Dataset One",
                    "license": "research-use license",
                    "split_file": "data/splits/D01_frozen_split_v1.json",
                    "preprocessing_config": "configs/preprocess/D01_v1.yaml",
                    "is_mock": False,
                    "is_synthetic": False,
                    "claim_support_allowed": True,
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
        {
            "schema_version": 1,
            "models": [
                {
                    "model_id": "M_OURS",
                    "name": "Our method",
                    "model_source_type": "real_code",
                    "implementation_ref": "project.methods.ours",
                    "checkpoint_or_model_version": "repo commit under test",
                    "config_path": "configs/experiments/E01/ours.yaml",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
                {
                    "model_id": "B01",
                    "name": "Baseline One",
                    "model_source_type": "official_code",
                    "implementation_ref": "https://example.invalid/code",
                    "checkpoint_or_model_version": "abc123",
                    "config_path": "configs/reproduction/B01/full.yaml",
                    "is_mock": False,
                    "is_stub": False,
                    "claim_support_allowed": True,
                },
            ],
        },
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
            "real_data_model_gate": {
                "required_for": ["full_experiment", "full_reproduction", "paper_binding"],
                "full_experiment_required_checks": [
                    "real_dataset_provenance_verified",
                    "real_model_provenance_verified",
                    "no_synthetic_or_mock_inputs",
                    "full_run_not_smoke",
                ],
                "full_reproduction_required_checks": [
                    "real_dataset_provenance_verified",
                    "real_model_provenance_verified",
                    "official_or_declared_code_commit_verified",
                    "no_synthetic_or_mock_inputs",
                    "full_run_not_smoke",
                ],
                "block_on": ["mock", "toy", "synthetic", "stub", "cached", "proxy", "smoke_only"],
            },
        },
    )
    write_yaml(
        research_dir / "spec" / "shared" / "insight_policy.yaml",
        {
            "schema_version": 1,
            "insight_policy": {
                "prd_hypothesis_statement": "当前 PRD 是初始研究假设。",
                "auto_allowed": ["execution_fix", "spec_refinement"],
                "human_review_required": ["core_rq_change", "main_claim_change"],
                "pivot_trigger_conditions": ["baseline_already_solves_problem"],
            },
        },
    )
    write_yaml(
        research_dir / "spec" / "insights" / "insight_manifest.yaml",
        {
            "schema_version": 1,
            "insight_categories": {
                "execution_failure": [],
                "research_failure": [],
                "anomaly": [],
                "negative_result": [],
                "pivot_proposal": [],
            },
            "insights": [],
        },
    )
    write_yaml(
        research_dir / "spec" / "experiments" / "experiment_manifest.yaml",
        {
            "schema_version": 1,
            "experiments": [
                {
                    "experiment_id": "E01",
                    "experiment_type": "confirmatory",
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
                    "data_model_truth": {
                        "full_experiment_requires_real_data": True,
                        "full_experiment_requires_real_model": True,
                        "dataset_manifest_must_set_is_mock_false": True,
                        "model_manifest_must_set_is_mock_false": True,
                        "forbid_mock_toy_synthetic_stub_cached_proxy": True,
                        "mock_allowed_only_for": ["unit_test", "smoke_test", "harness_plumbing"],
                    },
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
                        "real_dataset_provenance_verified",
                        "real_model_provenance_verified",
                        "no_mock_data_used",
                        "no_synthetic_or_mock_inputs",
                        "full_run_not_smoke",
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
                    "real_data_policy": {
                        "requires_real_dataset": True,
                        "dataset_id": "D01",
                        "forbid_mock_toy_synthetic": True,
                        "allowed_mock_scope": ["smoke_test"],
                    },
                    "real_model_policy": {
                        "requires_real_model_or_code": True,
                        "baseline_model_id": "B01",
                        "requires_official_or_declared_code_commit": True,
                        "forbid_stub_or_proxy_model": True,
                    },
                    "full_reproduction_required": True,
                    "commands": {
                        "smoke": ["bash scripts/reproduction/B01/run_smoke.sh"],
                        "run": ["bash scripts/reproduction/B01/run_full.sh --seed {seed}"],
                        "aggregate": ["python -m project.reproduction.aggregate --baseline B01"],
                    },
                    "required_artifacts": ["artifacts/reproduction/B01/aggregate/summary.json"],
                    "harnesses": ["H_R_B01_SMOKE", "H_R_B01_FULL"],
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
            "tasks": [
                {
                    "task_id": "T_R_B01",
                    "harnesses": ["H_R_B01_SMOKE", "H_R_B01_FULL"],
                    "acceptance_criteria": ["smoke passes", "full reproduction uses real data and model"],
                }
            ],
            "gates": [{"gate_id": "G_R_B01", "tasks": ["T_R_B01"], "harnesses": ["H_R_B01_SMOKE", "H_R_B01_FULL"]}],
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
                },
                {
                    "harness_id": "H_R_B01_FULL",
                    "type": "full_reproduction",
                    "linked_reproduction": "R_B01",
                    "cwd": ".",
                    "command": "bash scripts/reproduction/B01/run_full.sh --seed {seed}",
                    "timeout": 7200,
                    "required_inputs": ["data/splits/D01_frozen_split_v1.json", "configs/reproduction/B01/full.yaml"],
                    "required_outputs": [{"path": "artifacts/reproduction/B01/aggregate/summary.json"}],
                    "pass_criteria": [
                        "real_dataset_provenance_verified",
                        "real_model_provenance_verified",
                        "official_or_declared_code_commit_verified",
                        "no_synthetic_or_mock_inputs",
                        "full_run_not_smoke",
                    ],
                    "evidence_capture": ["stdout", "stderr", "artifact_hashes"],
                    "may_support_research_claim": True,
                    "independent_rerun_required": True,
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

def mark_prd_human_approved(research_dir: Path, ambiguity: bool = False) -> None:
    prd_path = research_dir / "prd" / "research_prd.md"
    dataset_text = (
        "Dataset plan: use a standard dataset chosen later without selection criteria.\n"
        if ambiguity
        else "Dataset plan: D01 is selected by explicit criteria: public license, frozen split, and metric compatibility.\n"
    )
    appendix = "\n".join(
        [
            "",
            "PRD_STATUS: HUMAN_APPROVED",
            "",
            "## Readiness Appendix",
            "",
            "RQ1: Does the proposed method improve the declared primary metric under the frozen benchmark?",
            "Hypothesis H1: The proposed method improves M01 over B01 on D01.",
            "Falsification condition: H1 is falsified if M_OURS does not improve M01 over B01 under all declared seeds.",
            "Benchmark selection criteria: public benchmark, frozen split, reproducible baseline, declared license.",
            dataset_text.rstrip(),
            "Baseline plan: B01 is the required closest baseline and must be reproduced before main experiments.",
            "Metric plan: M01 is the primary metric and its direction is higher-is-better.",
            "Harness expectation: H_E01_FULL must verify all seeds, all baselines, no mock evidence, and artifact hashes.",
            "Experiment design: E01 runs M_OURS and B01 on D01 with seeds 1, 2, and 3.",
            "Gate Schedule:",
            "| gate_id | tasks | pass_condition | on_fail | status |",
            "| G01 | T01 | H_E01_FULL passes all declared seeds and artifact checks | retry or escalate with blocker | pending |",
            "",
        ]
    )
    prd_path.write_text(prd_path.read_text(encoding="utf-8") + appendix, encoding="utf-8")
