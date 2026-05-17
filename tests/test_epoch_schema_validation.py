#!/usr/bin/env python3
"""Strict schema validation tests for every epoch version."""

from __future__ import annotations

import pytest
import shutil

from research_workflow_helpers import *  # noqa: F403


def lock_default_baseline(research_dir: Path) -> None:
    baseline_dir = research_dir / "V0" / "baselines" / "B_OFFICIAL"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(
        baseline_dir / "BASELINE_CARD.yaml",
        {
            "schema_version": 1,
            "epoch": "V0",
            "baseline_id": "B_OFFICIAL",
            "paper_id": "P_TEST",
            "role": "official",
            "reproduction_mode": "official_code_reuse",
            "decision_rationale": "official code is the closest reproducible baseline",
        },
    )
    write_yaml(
        baseline_dir / "PAPER_CARD.yaml",
        {
            "schema_version": 1,
            "paper_id": "P_TEST",
            "title": "Protocol baseline paper",
            "venue_year": "Test 2026",
            "paper_url": "https://example.invalid/paper",
        },
    )
    write_yaml(
        baseline_dir / "DATASET_CARD.yaml",
        {
            "schema_version": 1,
            "dataset_id": "D_TEST",
            "source_paper": "Protocol baseline paper",
            "license": "research-use",
            "split_protocol": "frozen public split",
            "metric": "M_TEST",
        },
    )
    write_yaml(
        baseline_dir / "EXPERIMENT_DESIGN.yaml",
        {
            "schema_version": 1,
            "design_id": "ED_TEST",
            "source_paper": "Protocol baseline paper",
            "reusable_design": "baseline reproduction before innovation",
        },
    )
    write_yaml(
        baseline_dir / "REUSE_DECISION.yaml",
        {
            "schema_version": 1,
            "baseline_id": "B_OFFICIAL",
            "decision": "reuse_for_version_baseline_lock",
            "rationale": "closest reproducible baseline",
        },
    )
    baseline_index = read_yaml(research_dir / "V0" / "baselines" / "INDEX.yaml")
    baseline_index["baseline_cards"] = [
        {
            "baseline_id": "B_OFFICIAL",
            "card_ref": "baselines/B_OFFICIAL/BASELINE_CARD.yaml",
            "paper_card_ref": "baselines/B_OFFICIAL/PAPER_CARD.yaml",
            "dataset_card_ref": "baselines/B_OFFICIAL/DATASET_CARD.yaml",
            "experiment_design_ref": "baselines/B_OFFICIAL/EXPERIMENT_DESIGN.yaml",
            "reuse_decision_ref": "baselines/B_OFFICIAL/REUSE_DECISION.yaml",
        }
    ]
    write_yaml(research_dir / "V0" / "baselines" / "INDEX.yaml", baseline_index)
    baseline = read_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml")
    baseline["status"] = "locked"
    baseline["task_definition"] = {
        "target_task": "minimal research-loop scaffold validation",
        "target_input_output": "protocol state files -> validator outcomes",
        "excluded_problem_settings": [],
    }
    baseline["selected_baselines"] = [
        {
            "baseline_id": "B_OFFICIAL",
            "paper": "Protocol baseline paper",
            "venue_year": "Test 2026",
            "role": "official",
            "official_code": "https://example.invalid/repo",
            "dataset": "D_TEST",
            "metric": "M_TEST",
            "reproduction_mode": "official_code_reuse",
            "baseline_card_ref": "baselines/B_OFFICIAL/BASELINE_CARD.yaml",
            "rq_ids": ["RQ01"],
            "decision_rationale": "official code is the closest reproducible baseline",
        }
    ]
    baseline["selected_datasets"] = [
        {
            "dataset_id": "D_TEST",
            "source_paper": "Protocol baseline paper",
            "license": "research-use",
            "split_protocol": "frozen public split",
            "preprocessing": "none",
            "metric": "M_TEST",
            "dataset_card_ref": "baselines/B_OFFICIAL/DATASET_CARD.yaml",
            "known_pitfalls": [],
        }
    ]
    baseline["borrowed_experiment_designs"] = [
        {
            "paper": "Protocol baseline paper",
            "reusable_design": "baseline reproduction before innovation",
            "adopted_as": "G0/G1 gate protocol",
            "experiment_design_ref": "baselines/B_OFFICIAL/EXPERIMENT_DESIGN.yaml",
            "caveat": "template-only evidence is not paper evidence",
        }
    ]
    write_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml", baseline)

pytestmark = pytest.mark.integration


def write_meta_framework_workspace(repo: Path) -> Path:
    research_dir = repo / "docs" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    (repo / "AGENTS.md").write_text("# AGENTS.md\n\nmeta framework test\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("# CLAUDE.md\n\nmeta framework test\n", encoding="utf-8")
    (research_dir / "RESEARCH_DIRECTION.md").write_text(
        """# Research Direction

## Direction Status

- direction_id: `research-loop-scaffold`
- status: `frozen`
- created_at: `2026-05-13`
- updated_at: `2026-05-16`
- repository_role: `meta_framework`
- current_version: `none`
- final_target: `Generic research-loop framework protocol`
- owner_decision_required: `true`

## Research Seed

This repository is the research-loop framework repository.

## Research Corridor

- Framework file protocol, schema, validator, installer, and policy tests.

## Out-of-Scope Directions

- Concrete project datasets, baselines, metrics, methods, or paper claims.

## Autonomy Boundary

AI 可以自动做:

- framework tests and docs.

AI 不可以自动做:

- create repo-local project epochs.

## Global Stop Conditions

- Framework tests pass and no project-research content is bound locally.
""",
        encoding="utf-8",
    )
    return research_dir


class EpochSchemaValidationTests(unittest.TestCase):  # noqa: F405
    def test_meta_framework_workspace_does_not_require_project_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = write_meta_framework_workspace(repo)

            for mode in ["direction-ready", "format-ready", "migration-ready", "rq-driven-ready", "baseline-lock-ready", "epoch-ready"]:
                result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", mode])
                self.assertEqual(result.returncode, 0, f"{mode}\n{result.stdout}{result.stderr}")

    def test_meta_framework_workspace_rejects_repo_local_project_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = write_meta_framework_workspace(repo)
            (research_dir / "CURRENT").write_text("V0\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "direction-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repo-local project research marker", result.stdout)

    def test_rq_driven_ready_accepts_pure_epoch_rq_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            for name in ["prd", "paper", "spec", "plans", "insights"]:
                shutil.rmtree(research_dir / name)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "rq-driven-ready"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[OK] rq-driven-ready", result.stdout)

    def test_rq_driven_ready_rejects_missing_rq_contract_with_migration_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            for name in ["prd", "paper", "spec", "plans", "insights"]:
                shutil.rmtree(research_dir / name)
            (research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "rq-driven-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/rqs/RQ01/SPEC.yaml", result.stdout)
        self.assertIn("RQ-driven migration required", result.stdout)

    def test_baseline_lock_ready_requires_locked_version_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "baseline-lock-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BASELINE_LOCK.yaml must be locked", result.stdout)

    def test_baseline_lock_ready_requires_baseline_dossier_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "baselines" / "INDEX.yaml").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "baseline-lock-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline_dossier_ref does not exist", result.stdout)

    def test_baseline_lock_ready_requires_locked_selected_baseline_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            baseline = read_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml")
            baseline["status"] = "locked"
            baseline["selected_baselines"] = [
                {
                    "baseline_id": "B_MISSING_CARD",
                    "paper": "Missing Card Paper",
                    "role": "official",
                    "reproduction_mode": "official_code_reuse",
                    "baseline_card_ref": "baselines/B_MISSING_CARD/BASELINE_CARD.yaml",
                    "decision_rationale": "closest baseline",
                }
            ]
            baseline["selected_datasets"] = [
                {
                    "dataset_id": "D_TEST",
                    "source_paper": "Missing Card Paper",
                    "license": "research-use",
                    "split_protocol": "frozen split",
                    "metric": "M_TEST",
                    "dataset_card_ref": "baselines/B_MISSING_CARD/DATASET_CARD.yaml",
                }
            ]
            baseline["borrowed_experiment_designs"] = [
                {
                    "paper": "Missing Card Paper",
                    "reusable_design": "official evaluation matrix",
                    "experiment_design_ref": "baselines/B_MISSING_CARD/EXPERIMENT_DESIGN.yaml",
                }
            ]
            write_yaml(research_dir / "V0" / "BASELINE_LOCK.yaml", baseline)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "baseline-lock-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline_card_ref does not exist", result.stdout)
        self.assertIn("dataset_card_ref does not exist", result.stdout)
        self.assertIn("experiment_design_ref does not exist", result.stdout)

    def test_baseline_lock_ready_accepts_locked_baseline_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            lock_default_baseline(research_dir)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "baseline-lock-ready"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[OK] baseline-lock-ready", result.stdout)

    def test_epoch_ready_requires_rq_local_spec_for_declared_rq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/rqs/RQ01/SPEC.yaml", result.stdout)

    def test_epoch_ready_rejects_missing_preflight_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "scripts" / "pre_flight.sh").unlink()

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/scripts/pre_flight.sh", result.stdout)

    def test_epoch_ready_rejects_invalid_paper_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            paper_type = read_yaml(research_dir / "V0" / "PAPER_TYPE.yaml")
            paper_type["paper_type"] = "prototype"
            write_yaml(research_dir / "V0" / "PAPER_TYPE.yaml", paper_type)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PAPER_TYPE.yaml invalid paper_type", result.stdout)

    def test_epoch_ready_rejects_non_boolean_tdd_required_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            paper_type = read_yaml(research_dir / "V0" / "PAPER_TYPE.yaml")
            paper_type["tdd_required"]["enabled"] = "yes"
            write_yaml(research_dir / "V0" / "PAPER_TYPE.yaml", paper_type)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PAPER_TYPE.yaml tdd_required.enabled must be a boolean", result.stdout)

    def test_epoch_ready_rejects_rq_spec_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spec_path = research_dir / "V0" / "rqs" / "RQ01" / "SPEC.yaml"
            spec = read_yaml(spec_path)
            spec["rq_id"] = "RQ_OTHER"
            write_yaml(spec_path, spec)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rq_id RQ_OTHER does not match directory RQ01", result.stdout)

    def test_epoch_ready_rejects_invalid_human_insight_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            review_path = research_dir / "V0" / "rqs" / "RQ01" / "INSIGHT_REVIEW.yaml"
            review = read_yaml(review_path)
            review["human_verdict"]["verdict"] = "ai_decided"
            review["human_verdict"]["paper_eligibility"] = "publish_now"
            write_yaml(review_path, review)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid human verdict", result.stdout)
        self.assertIn("invalid paper_eligibility", result.stdout)

    def test_epoch_ready_rejects_invalid_frontier_human_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            frontier_path = research_dir / "V0" / "wiki" / "frontier_map.yaml"
            frontier = read_yaml(frontier_path)
            frontier["human_decision"]["status"] = "auto_continue"
            write_yaml(frontier_path, frontier)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid frontier human_decision status", result.stdout)

    def test_epoch_ready_rejects_global_task_missing_rq_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ01", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": "artifacts/e1.json"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            task = queue["tasks"][0]
            task["phase"] = "implementation"
            task["research_binding"] = {
                "mode": "spine_bound",
                "rq_id": "RQ01",
                "claim_ids": ["C1"],
                "experiment_ids": ["E1"],
                "evidence_ids": ["EV1"],
                "justification": "implementation task supporting declared RQ contract",
            }
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 missing rq_spec_ref", result.stdout)
        self.assertIn("task T_G0_001 missing rq_task_ref", result.stdout)

    def test_loop_ready_blocks_innovation_before_rq_reproduction_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            lock_default_baseline(research_dir)
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ01", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": "artifacts/e1.json"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)
            rq_tasks_path = research_dir / "V0" / "rqs" / "RQ01" / "TASKS.yaml"
            rq_tasks = read_yaml(rq_tasks_path)
            rq_tasks["tasks"][0]["task_id"] = "RQ01_T_IMPL"
            rq_tasks["tasks"][0]["phase"] = "implementation"
            write_yaml(rq_tasks_path, rq_tasks)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            task = queue["tasks"][0]
            task["phase"] = "implementation"
            task["allowed_files"] = ["src/module.py"]
            task["test_commands"] = ["python3 -m pytest tests/test_epoch_schema_validation.py -q"]
            task["rq_id"] = "RQ01"
            task["rq_spec_ref"] = "rqs/RQ01/SPEC.yaml"
            task["rq_task_ref"] = "rqs/RQ01/TASKS.yaml#RQ01_T_IMPL"
            task["research_binding"] = {
                "mode": "spine_bound",
                "rq_id": "RQ01",
                "claim_ids": ["C1"],
                "experiment_ids": ["E1"],
                "evidence_ids": ["EV1"],
                "justification": "implementation task supporting declared RQ contract",
            }
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "loop-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires verified reproduction for RQ01", result.stdout)

    def test_loop_ready_blocks_reproduction_before_version_baseline_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["current_gate"] = "G1_REPRODUCTION_LOCK"
            queue["current_task"] = "T_G1_001"
            for task in queue["tasks"]:
                task["status"] = "active" if task["task_id"] == "T_G1_001" else "pending"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "loop-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires locked BASELINE_LOCK.yaml before reproduction", result.stdout)

    def test_epoch_ready_rejects_task_missing_research_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0].pop("research_binding", None)
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 missing research_binding", result.stdout)

    def test_epoch_ready_rejects_spine_bound_task_unknown_rq(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["research_binding"] = {
                "mode": "spine_bound",
                "rq_id": "RQ_MISSING",
                "claim_ids": ["C1"],
                "experiment_ids": ["E1"],
                "evidence_ids": ["EV1"],
                "justification": "bind active task to a concrete research spine chain",
            }
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 research_binding references unknown rq_id: RQ_MISSING", result.stdout)

    def test_loop_ready_rejects_experiment_task_without_experiment_or_evidence_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["research_questions"] = [{"id": "RQ01", "text": "q1", "rq_dir": "rqs/RQ01", "spec_ref": "rqs/RQ01/SPEC.yaml", "plan_ref": "rqs/RQ01/PLAN.md"}]
            spine["claims"] = [{"id": "C1", "rq_id": "RQ01", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": "artifacts/e1.json"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            active_task = queue["tasks"][0]
            active_task["phase"] = "experiment"
            active_task["type"] = "experiment"
            active_task["test_commands"] = ["python -m pytest tests/test_epoch_schema_validation.py"]
            active_task["research_binding"] = {
                "mode": "spine_bound",
                "rq_id": "RQ01",
                "claim_ids": ["C1"],
                "experiment_ids": [],
                "evidence_ids": [],
                "justification": "experiment task must bind to declared evidence before execution",
            }
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "loop-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 spine_bound research_binding missing experiment_ids", result.stdout)
        self.assertIn("task T_G0_001 spine_bound research_binding missing evidence_ids", result.stdout)

    def test_epoch_ready_rejects_direction_bootstrap_outside_bootstrap_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["phase"] = "experiment"
            queue["tasks"][0]["research_binding"] = {
                "mode": "direction_bootstrap",
                "rq_id": None,
                "claim_ids": [],
                "experiment_ids": [],
                "evidence_ids": [],
                "justification": "version start search/reproduction lock before PRD-spine binding",
            }
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 direction_bootstrap is not allowed in phase: experiment", result.stdout)

    def test_epoch_ready_rejects_direction_bootstrap_outside_g0_g1_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["gate_id"] = "G2_METHOD_LOCK"
            queue["tasks"][0]["phase"] = "search"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task T_G0_001 direction_bootstrap is only allowed in G0/G1 gates: G2_METHOD_LOCK", result.stdout)

    def test_epoch_ready_rejects_missing_rq_spec_required_field_in_any_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
            shutil.copytree(research_dir / "V0", research_dir / "V1")
            (research_dir / "CURRENT").write_text("V1\n", encoding="utf-8")
            spec = read_yaml(research_dir / "V1" / "rqs" / "RQ01" / "SPEC.yaml")
            spec["version"] = "V1"
            spec.pop("claim_contract", None)
            write_yaml(research_dir / "V1" / "rqs" / "RQ01" / "SPEC.yaml", spec)
            status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            status["version"] = "V1"
            write_yaml(research_dir / "V1" / "STATUS.yaml", status)
            queue = read_yaml(research_dir / "V1" / "TASK_QUEUE.yaml")
            queue["version"] = "V1"
            write_yaml(research_dir / "V1" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V1/rqs/RQ01/SPEC.yaml missing required field: claim_contract", result.stdout)

    def test_epoch_ready_rejects_version_field_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
            shutil.copytree(research_dir / "V0", research_dir / "V1")
            (research_dir / "CURRENT").write_text("V1\n", encoding="utf-8")
            status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            status["version"] = "V0"
            write_yaml(research_dir / "V1" / "STATUS.yaml", status)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V1/STATUS.yaml version V0 does not match epoch V1", result.stdout)

    def test_epoch_ready_rejects_unexpected_wiki_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "wiki" / "extra_protocol.md").write_text("# Extra\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected epoch wiki file: V0/wiki/extra_protocol.md", result.stdout)

    def test_epoch_ready_still_rejects_v1_before_v0_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            shutil.copytree(research_dir / "V0", research_dir / "V1")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot create next version before current epoch has closed_* status", result.stdout)

    def test_epoch_ready_rejects_missing_gate_aware_queue_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue.pop("current_gate", None)
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/TASK_QUEUE.yaml missing required field: current_gate", result.stdout)

    def test_epoch_ready_rejects_invalid_gate_and_task_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["gates"][0]["status"] = "almost_done"
            queue["tasks"][0]["status"] = "working"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid gate status", result.stdout)
        self.assertIn("invalid task status", result.stdout)

    def test_epoch_ready_rejects_missing_spine_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine.pop("claims", None)
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml missing required field: claims", result.stdout)

    def test_epoch_ready_rejects_spine_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["version"] = "V99"
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml version V99 does not match epoch V0", result.stdout)

    def test_epoch_ready_rejects_missing_spine_direction_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine.pop("direction_ref", None)
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml missing required field: direction_ref", result.stdout)

    def test_spine_ready_rejects_invalid_direction_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["direction_ref"] = "../NON_EXISTENT_DIRECTION.md"
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("direction_ref points to non-existent file", result.stdout)

    def test_spine_ready_validates_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_spine_ready_rejects_broken_rq_claim_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["research_questions"] = [{"id": "RQ01", "text": "q1", "rq_dir": "rqs/RQ01", "spec_ref": "rqs/RQ01/SPEC.yaml", "plan_ref": "rqs/RQ01/PLAN.md"}]
            spine["claims"] = [{"id": "C1", "rq_id": "RQ_MISSING", "text": "c1"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine claim C1 references unknown rq_id: RQ_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_claim_experiment_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ1", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C_MISSING"], "purpose": "p1"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine experiment E1 references unknown claim_id: C_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_experiment_evidence_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E_MISSING", "artifact_path": None}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine evidence EV1 references unknown experiment_id: E_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_evidence_figure_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": None}]
            spine["figures_tables"] = [{"id": "FIG1", "evidence_ids": ["EV_MISSING"], "target_path": "f1.pdf"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine figure/table FIG1 references unknown evidence_id: EV_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_section_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ1", "text": "c1"}]
            spine["figures_tables"] = [{"id": "FIG1", "evidence_ids": ["EV1"], "target_path": "f1.pdf"}]
            spine["paper_sections"] = [
                {"id": "SEC1", "claims": ["C_MISSING"], "figures_tables": ["FIG_MISSING"]}
            ]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine paper_section SEC1 references unknown claim_id: C_MISSING", result.stdout)
        self.assertIn("spine paper_section SEC1 references unknown figure/table_id: FIG_MISSING", result.stdout)
