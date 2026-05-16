#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class ResearchPaperPlanTests(unittest.TestCase):  # noqa: F405
    def test_research_paper_script_uses_full_template_and_spec_bound_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            make_execution_ready_spec(research_dir)

            result = run_cmd(["python3", str(PAPER_SCRIPT), "--research-dir", str(research_dir), "--force"], cwd=repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            paper_md = (research_dir / "paper" / "planned_paper.md").read_text(encoding="utf-8")
            paper_tex = (research_dir / "paper" / "planned_paper.tex").read_text(encoding="utf-8")
            gap_report = (research_dir / "paper" / "paper_gap_report.md").read_text(encoding="utf-8")
            placeholder_map = read_yaml(research_dir / "paper" / "placeholder_map.yaml")

            self.assertIn("## 2. Related Work and Research Gap", paper_md)
            self.assertIn("## 5. Evaluation Plan", paper_md)
            self.assertIn("## Bound Placeholder Map (Generated From Spec)", paper_md)
            self.assertIn("{{E01.OURS.primary_metric}}", paper_md)
            self.assertNotIn("TODO", paper_md)
            self.assertNotIn("Experiments show", paper_md)
            self.assertIn(r"\documentclass[UTF8,11pt]{ctexart}", paper_tex)
            self.assertIn("论文缺口报告", gap_report)
            self.assertIn("论文正文中的表格和结果段落保留 typed placeholder", gap_report)
            self.assertIn("generation_mode: `draft`", gap_report)
            self.assertEqual(placeholder_map["placeholders"][0]["experiment_id"], "E01")

    def test_research_paper_binding_mode_fails_before_gate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_closed_fast(repo)
            result = run_cmd(
                ["python3", str(PAPER_SCRIPT), "--research-dir", str(research_dir), "--mode", "binding", "--force"],
                cwd=repo,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("paper binding gate failed", result.stdout + result.stderr)

    def test_research_paper_binding_mode_succeeds_after_gate_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_closed_fast(repo)
            make_paper_binding_decision(research_dir)
            result = run_cmd(
                ["python3", str(PAPER_SCRIPT), "--research-dir", str(research_dir), "--mode", "binding", "--force"],
                cwd=repo,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            gap_report = (research_dir / "paper" / "paper_gap_report.md").read_text(encoding="utf-8")
            self.assertIn("generation_mode: `binding`", gap_report)
            self.assertIn("`paper-binding-ready` gate 已通过", gap_report)

    def test_research_paper_demo_generates_placeholder_complete_manuscript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)

            result = run_cmd(
                ["python3", str(PAPER_SCRIPT), "--research-dir", str(research_dir), "--demo", "--force"],
                cwd=repo,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            paper_md = (research_dir / "paper" / "planned_paper.md").read_text(encoding="utf-8")
            gap_report = (research_dir / "paper" / "paper_gap_report.md").read_text(encoding="utf-8")
            placeholder_map = read_yaml(research_dir / "paper" / "placeholder_map.yaml")
            experiment_manifest = read_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")

            self.assertIn("ContractGraph: Evidence-Bound Execution for LLM Coding Agents", paper_md)
            self.assertIn("## 1. Introduction", paper_md)
            self.assertIn("## 4. Method: ContractGraph", paper_md)
            self.assertIn("## 6. Planned Result Bindings and Expected Sensitivity", paper_md)
            self.assertIn("{{E01.OURS.task_success}}", paper_md)
            self.assertIn("{{E01.B01.task_success}}", paper_md)
            self.assertNotIn("【待填写", paper_md)
            self.assertNotIn("Experiments show", paper_md)
            self.assertNotRegex(paper_md, r"\b\d+\.\d+\b")
            self.assertIn("完整 placeholder-complete manuscript draft", gap_report)
            self.assertNotIn("mock planning values", gap_report)
            self.assertGreaterEqual(len(placeholder_map["placeholders"]), 4)
            self.assertEqual(len(experiment_manifest["experiments"]), 4)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "paper-ready"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            if latex_available():
                log = research_dir / "paper" / "build" / "planned_paper.log"
                self.assertTrue(log.exists())
                log_text = log.read_text(encoding="utf-8", errors="replace")
                for marker in ["Overfull \\hbox", "Underfull \\hbox", "LaTeX Warning:"]:
                    self.assertNotIn(marker, log_text)

    def test_research_plan_outputs_chinese_executor_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            make_execution_ready_spec(research_dir)

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

            plan_dir = plan_dir_for(research_dir, "2026-05-09-reproduce-b01")
            plan_yaml = read_yaml(plan_dir / "plan.yaml")
            plan_md = (plan_dir / "plan.md").read_text(encoding="utf-8")
            prompt = (plan_dir / "ai_loop_prompt.md").read_text(encoding="utf-8")
            current_state = (plan_dir / "current_state.md").read_text(encoding="utf-8")

            self.assertIn("source_versions", plan_yaml)
            self.assertIn("gates", plan_yaml)
            self.assertIn("harnesses", plan_yaml)
            self.assertIn("insight_loop", plan_yaml)
            self.assertIn("不要从 Paper 推断具体的 dataset、seed、command 或 artifact 路径", "\n".join(plan_yaml["forbidden_actions"]))
            self.assertIn("可以从 Paper 理解实验设计意图（baseline、metric、表格结构），但执行数据必须从 Spec 获取", "\n".join(plan_yaml["forbidden_actions"]))
            self.assertIn("研究执行计划", plan_md)
            self.assertIn("执行最早尚未完成的 gate", plan_md)
            self.assertIn("AI 长循环执行提示词", prompt)
            self.assertIn("可执行真源是 `docs/research/spec/`", prompt)
            self.assertIn("禁止将 mock / planning 值当作已验证结果写入证据或论文结论", prompt)
            self.assertIn("## Subagent Dispatch", prompt)
            self.assertIn("mathematical formulation or proof issue → `research-math`", prompt)
            self.assertIn("baseline reproduction → `research-reproduce`", prompt)
            self.assertIn("cross-file consistency check → `research-audit`", prompt)
            self.assertIn("The controller remains responsible for state, gates, and promotion.", prompt)
            self.assertIn("洞察问题", prompt)
            self.assertIn("有没有值得微调 15 度的方向", prompt)
            self.assertTrue((plan_dir / "insight_log.md").exists())
            self.assertIn("当前状态", current_state)

    def test_research_plan_accepts_insight_feedback_track(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            make_execution_ready_spec(research_dir)

            result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-09",
                    "--purpose",
                    "review-negative-result",
                    "--track",
                    "insight-feedback",
                ],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((plan_dir_for(research_dir, "2026-05-09-review-negative-result") / "plan.yaml").exists())
