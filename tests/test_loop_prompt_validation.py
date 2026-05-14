#!/usr/bin/env python3
"""Tests for loop-prompt-ready validation and AI loop prompt generation."""

from __future__ import annotations

import sys

from research_workflow_helpers import *  # noqa: F403

SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"  # noqa: F405
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import generate_plan  # noqa: E402


class LoopPromptValidationTests(unittest.TestCase):  # noqa: F405
    def test_loop_prompt_ready_fails_missing_clauses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:  # noqa: F405
            research_dir = init_workspace_fast(Path(tmp))  # noqa: F405
            plan_dir = research_dir / "plans" / "TEST"
            plan_dir.mkdir(parents=True, exist_ok=True)
            (plan_dir / "ai_loop_prompt.md").write_text(
                "# AI Loop Prompt\n\nSome content without required clauses.\n",
                encoding="utf-8",
            )

            result = run_cmd(  # noqa: F405
                [
                    "python3",
                    str(VALIDATE_SCRIPT),  # noqa: F405
                    "--research-dir",
                    str(research_dir),
                    "--mode",
                    "loop-prompt-ready",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing clause 'document_writing_stop_ask'", result.stdout)
        self.assertIn("missing clause 'execution_do_not_ask'", result.stdout)
        self.assertIn("missing clause 'required_info_blocker'", result.stdout)

    def test_loop_prompt_ready_passes_all_clauses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:  # noqa: F405
            research_dir = init_workspace_fast(Path(tmp))  # noqa: F405
            plan_dir = research_dir / "plans" / "TEST"
            plan_dir.mkdir(parents=True, exist_ok=True)
            prompt_text = (
                "# AI Loop Prompt\n\n"
                "文档撰写阶段遇到用户意图不明、要求自相矛盾时，必须停止并请求用户确认，不得自行推断。\n"
                "执行阶段遇到同样情况时，不得停止询问用户偏好，应自主推进并仅对确实缺失的必需信息记录 blocker。\n"
                "当 required information 缺失时，停止执行并记录 blocker，不得补造。\n"
            )
            (plan_dir / "ai_loop_prompt.md").write_text(prompt_text, encoding="utf-8")

            result = run_cmd(  # noqa: F405
                [
                    "python3",
                    str(VALIDATE_SCRIPT),  # noqa: F405
                    "--research-dir",
                    str(research_dir),
                    "--mode",
                    "loop-prompt-ready",
                ]
            )

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_generate_plan_produces_ai_loop_prompt_with_clauses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:  # noqa: F405
            research_dir = init_workspace_fast(Path(tmp))  # noqa: F405
            plan_dir = generate_plan(research_dir, "2026-05-14", "test-clauses", "reproduction")
            prompt_path = plan_dir / "ai_loop_prompt.md"
            text = prompt_path.read_text(encoding="utf-8")

        self.assertIn("文档撰写阶段", text)
        self.assertIn("停止并请求用户确认", text)
        self.assertIn("执行阶段", text)
        self.assertIn("不得停止询问", text)
        self.assertIn("自主推进", text)
        self.assertIn("required information", text)
        self.assertIn("缺失", text)
        self.assertIn("blocker", text)

    def test_generate_plan_produces_insight_loop_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:  # noqa: F405
            research_dir = init_workspace_fast(Path(tmp))  # noqa: F405
            plan_dir = generate_plan(research_dir, "2026-05-14", "test-categories", "reproduction")
            plan_yaml = read_yaml(plan_dir / "plan.yaml")  # noqa: F405
            human_review = plan_yaml.get("insight_loop", {}).get("human_review", [])

        self.assertIn("research_failure", human_review)
        self.assertIn("pivot_proposal", human_review)
        self.assertIn("anomaly", human_review)
        self.assertIn("ambiguous_user_intent", human_review)
        self.assertIn("contradictory_requirements", human_review)
        self.assertIn("scope_decision_required", human_review)
        self.assertIn("methodology_divergence", human_review)
        self.assertEqual(len(human_review), 7)

    def test_loop_prompt_ready_checks_epoch_level_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:  # noqa: F405
            research_dir = init_workspace_fast(Path(tmp))  # noqa: F405
            epoch_dir = research_dir / "V0"
            (epoch_dir / "ai_loop_prompt.md").write_text(
                "# Epoch AI Loop Prompt\n\nSome content without required clauses.\n",
                encoding="utf-8",
            )

            result = run_cmd(  # noqa: F405
                [
                    "python3",
                    str(VALIDATE_SCRIPT),  # noqa: F405
                    "--research-dir",
                    str(research_dir),
                    "--mode",
                    "loop-prompt-ready",
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("epoch ai_loop_prompt.md missing clause", result.stdout)
