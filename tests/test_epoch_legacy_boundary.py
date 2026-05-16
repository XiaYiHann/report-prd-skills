#!/usr/bin/env python3
"""Boundary tests between epoch contract mode and legacy controller mode."""

from __future__ import annotations

import pytest
from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class EpochLegacyBoundaryTests(unittest.TestCase):  # noqa: F405
    def test_research_loop_defaults_to_epoch_contract_when_epoch_workspace_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            legacy_state = research_dir / "state.yaml"
            if legacy_state.exists():
                legacy_state.unlink()

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)
            legacy_state_exists = legacy_state.exists()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["controller_mode"], "epoch_contract")
        self.assertEqual(summary["current_version"], "V0")
        self.assertEqual(summary["execution_backend"]["mode"], "codex_or_claude_code_agent")
        self.assertFalse(legacy_state_exists)

    def test_epoch_research_controller_compiles_spec_as_internal_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            make_execution_ready_spec(research_dir)
            epoch = research_dir / "V0"
            status = read_yaml(epoch / "STATUS.yaml")
            status["status"] = "prd_locked"
            write_yaml(epoch / "STATUS.yaml", status)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)
            updated_status = read_yaml(epoch / "STATUS.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["controller_mode"], "epoch_contract")
        self.assertEqual(summary["actions"][0]["action"], "compiled_spec")
        self.assertEqual(updated_status["status"], "spec_ready")

    def test_epoch_research_controller_compiles_plan_as_internal_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            epoch = research_dir / "V0"
            status = read_yaml(epoch / "STATUS.yaml")
            status["status"] = "spec_ready"
            write_yaml(epoch / "STATUS.yaml", status)
            (epoch / "TASK_QUEUE.yaml").unlink()

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)
            updated_status = read_yaml(epoch / "STATUS.yaml")
            queue_exists = (epoch / "TASK_QUEUE.yaml").exists()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["actions"][0]["action"], "compiled_plan")
        self.assertEqual(updated_status["status"], "plan_ready")
        self.assertFalse((epoch / "PLAN.md").exists())
        self.assertTrue(queue_exists)

    def test_epoch_research_controller_auto_drafts_paper_but_waits_for_human_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_closed_fast(repo)
            epoch = research_dir / "V0"
            status = read_yaml(epoch / "STATUS.yaml")
            status["status"] = "closed_stable"
            write_yaml(epoch / "STATUS.yaml", status)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)
            status = read_yaml(epoch / "STATUS.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["actions"][0]["action"], "generated_paper_draft_waiting_human_binding_decision")
        self.assertEqual(status["status"], "closed_stable")

    def test_epoch_research_controller_binds_paper_only_after_human_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_closed_fast(repo)
            make_paper_binding_decision(research_dir)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "2", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)
            status = read_yaml(research_dir / "V0" / "STATUS.yaml")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual([action["action"] for action in summary["actions"]], ["paper_binding_gate_ready", "generated_binding_ready_manuscript"])
            self.assertEqual(status["status"], "paper_bound")
            gap_report = (research_dir / "paper" / "paper_gap_report.md").read_text(encoding="utf-8")
            self.assertIn("generation_mode: `binding`", gap_report)
            self.assertIn("`paper-binding-ready` gate 已通过", gap_report)

    def test_legacy_controller_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = run_cmd(
                [
                    "python3",
                    str(RESEARCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--max-steps",
                    "1",
                    "--json",
                    "--legacy-controller",
                ],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["controller_mode"], "legacy_controller")
        self.assertEqual(summary["execution_backend"]["mode"], "prompt-only")

    def test_readme_names_codex_claude_as_agent_executors_not_backend(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")  # noqa: F405

        self.assertIn("Codex / Claude Code", readme)
        self.assertIn("agent executor", readme)
        self.assertIn("不提供独立常驻 backend", readme)
        self.assertNotIn("backend 空壳", readme)
