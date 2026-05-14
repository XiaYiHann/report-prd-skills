#!/usr/bin/env python3
"""Boundary tests between epoch contract mode and legacy controller mode."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


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
