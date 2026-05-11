#!/usr/bin/env python3
"""Business-focused regression tests for the research workflow."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class ResearchInitScaffoldTests(unittest.TestCase):  # noqa: F405
    def test_research_init_scaffolds_docs_research_tree_and_required_prd_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))

            expected_dirs = ["prd", "paper", "spec", "plans", "audits", "insights"]
            for dirname in expected_dirs:
                self.assertTrue((research_dir / dirname).exists(), dirname)
            self.assertTrue((research_dir / "insights" / "anomaly_reports").exists())
            self.assertTrue((research_dir / "insights" / "pivot_proposals").exists())
            self.assertTrue((research_dir / "insights" / "negative_results").exists())
            self.assertTrue((research_dir / "insights" / "insight_log.md").exists())
            insight_log = (research_dir / "insights" / "insight_log.md").read_text(encoding="utf-8")
            self.assertIn("Legacy compatibility note", insight_log)
            self.assertIn("research-insight", insight_log)
            prd = (research_dir / "prd" / "research_prd.md").read_text(encoding="utf-8")
            self.assertIn("# Research PRD", prd)
            self.assertIn("## 4. 基准与复现计划（Benchmark and Reproduction Plan）", prd)
            self.assertIn("## 11. 任务图与学生工作计划（Task Graph and Student Work Plan）", prd)
            self.assertIn("## 13. 证据台账（Evidence Ledger）", prd)
            self.assertIn("## 16. 探索与洞察策略（Exploration and Insight Policy）", prd)
            self.assertNotIn("PRD_STATUS: HUMAN_APPROVED", prd)
            self.assertIn("章节目标", prd)
            self.assertIn("常见错误", prd)
            self.assertIn("证据边界", prd)
            self.assertIn("验收标准", prd)
            self.assertIn("RQ / Hypothesis / Claim 映射表", prd)
            self.assertIn("Benchmark Candidate Matrix", prd)
            self.assertNotIn("TODO", prd)
            self.assertNotIn("Reader Model and Usage", prd)

    def test_research_init_generates_chinese_latex_tikz_prd_without_fake_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            prd_dir = research_dir / "prd"
            tex = (prd_dir / "research_prd.tex").read_text(encoding="utf-8")

            self.assertIn(r"\documentclass[UTF8,11pt]{ctexrep}", tex)
            self.assertIn(r"\usepackage{booktabs,tabularx,array,longtable}", tex)
            self.assertIn(r"\usepackage{tikz}", tex)
            self.assertGreaterEqual(tex.count(r"\begin{tikzpicture}"), 4)
            self.assertIn("研究问题到证据链", tex)
            self.assertIn("方法模块图", tex)
            self.assertIn("实验与复现流程图", tex)
            self.assertIn("Spec、Plan 与 Audit 执行闭环", tex)
            self.assertIn("【待填写：", tex)

            pdf = prd_dir / "research_prd.pdf"
            blocker = prd_dir / "render_blocker.md"
            self.assertTrue(pdf.exists() or blocker.exists())
            if blocker.exists():
                blocker_text = blocker.read_text(encoding="utf-8")
                self.assertIn("未生成 PDF", blocker_text)
                self.assertIn("未检测到可用的 LaTeX 引擎", blocker_text)
                self.assertFalse(pdf.exists(), "LaTeX 缺失时不得生成伪造 PDF")
            else:
                pdf_header = pdf.read_bytes()[:8]
                self.assertTrue(pdf_header.startswith(b"%PDF-"))

    @unittest.skipUnless(latex_available(), "LaTeX engine is not available")
    def test_research_prd_latex_template_compiles_without_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            log = research_dir / "prd" / "build" / "research_prd.log"
            self.assertTrue(log.exists())
            log_text = log.read_text(encoding="utf-8", errors="replace")
            forbidden = [
                "Overfull \\hbox",
                "Underfull \\hbox",
                "LaTeX Warning:",
                "may be unreliable inside tabularx",
            ]
            for marker in forbidden:
                self.assertNotIn(marker, log_text)

    @unittest.skipUnless(latex_available(), "LaTeX engine is not available")
    def test_research_paper_latex_template_compiles_without_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            log = research_dir / "paper" / "build" / "planned_paper.log"
            self.assertTrue(log.exists())
            log_text = log.read_text(encoding="utf-8", errors="replace")
            forbidden = [
                "Overfull \\hbox",
                "Underfull \\hbox",
                "LaTeX Warning:",
            ]
            for marker in forbidden:
                self.assertNotIn(marker, log_text)

    def test_spec_scaffold_uses_chinese_values_with_english_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))

            readme = (research_dir / "spec" / "README.md").read_text(encoding="utf-8")
            gap = (research_dir / "spec" / "reproduction" / "reproduction_gap_report.md").read_text(encoding="utf-8")
            global_spec = read_yaml(research_dir / "spec" / "global_spec.yaml")
            anti_mock = read_yaml(research_dir / "spec" / "shared" / "anti_mock_policy.yaml")
            dataset_manifest = read_yaml(research_dir / "spec" / "shared" / "dataset_manifest.yaml")
            model_manifest = read_yaml(research_dir / "spec" / "shared" / "model_manifest.yaml")

            self.assertIn("全局机器可读执行契约", readme)
            self.assertIn("不要从论文反推实验", readme)
            self.assertIn("复现缺口报告", gap)
            self.assertIn("【阻塞】", gap)
            self.assertIn("schema_version", global_spec)
            self.assertEqual(global_spec["authority"], "compile_from_prd_not_paper")
            self.assertIn("只能从 Research PRD 编译", global_spec["notes"][0])
            self.assertIn("科研主张", anti_mock["forbidden_for_description"]["research_claim"])
            self.assertIn("real_data_model_gate", anti_mock)
            self.assertFalse(dataset_manifest["dataset_template"]["is_mock"])
            self.assertFalse(model_manifest["model_template"]["is_mock"])

    def test_research_init_generates_top_conference_paper_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            paper_md = (research_dir / "paper" / "planned_paper.md").read_text(encoding="utf-8")
            paper_tex = (research_dir / "paper" / "planned_paper.tex").read_text(encoding="utf-8")
            gap_report = (research_dir / "paper" / "paper_gap_report.md").read_text(encoding="utf-8")

            for heading in [
                "## Abstract",
                "## 1. Introduction",
                "## 2. Related Work and Research Gap",
                "## 3. Problem Formulation",
                "## 4. Method",
                "## 5. Evaluation Plan",
                "## 6. Planned Results and Placeholder Discipline",
                "## 7. Limitations and Ethics",
                "## Appendix Plan",
            ]:
                self.assertIn(heading, paper_md)
            self.assertIn("NeurIPS / ICLR / AAAI", paper_md)
            self.assertIn("We propose", paper_md)
            self.assertIn("Do not write empirical conclusions before evidence", paper_md)
            self.assertIn("PLACEHOLDER_PATTERN", paper_md)
            self.assertNotIn("TODO", paper_md)
            self.assertNotIn("Experiments show", paper_md)
            self.assertIn(r"\documentclass[UTF8,11pt]{ctexart}", paper_tex)
            self.assertIn(r"\usepackage{booktabs,tabularx,array}", paper_tex)
            self.assertIn("Planned Research Paper", paper_tex)
            self.assertIn("论文缺口报告", gap_report)
            self.assertIn("【阻塞】", gap_report)
            self.assertIn("未验证结果必须保留为 typed placeholder", gap_report)

    def test_spec_scaffold_contains_execution_contract_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            global_spec = read_yaml(research_dir / "spec" / "global_spec.yaml")
            experiment_manifest = read_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
            experiment_harness = read_yaml(research_dir / "spec" / "experiments" / "experiment_harness.yaml")
            reproduction_manifest = read_yaml(research_dir / "spec" / "reproduction" / "reproduction_manifest.yaml")
            result_binding = read_yaml(research_dir / "spec" / "paper" / "result_binding.yaml")

            self.assertIn("rq_chain_template", global_spec)
            self.assertIn("experiment_id", global_spec["rq_chain_template"])
            self.assertEqual(experiment_manifest["experiments"], [])
            self.assertIn("experiment_template", experiment_manifest)
            self.assertIn("experiment_type", experiment_manifest["experiment_template"])
            self.assertIn("support_condition", experiment_manifest["experiment_template"])
            self.assertIn("falsification_condition", experiment_manifest["experiment_template"])
            self.assertIn("data_model_truth", experiment_manifest["experiment_template"])
            self.assertIn("harness_template", experiment_harness)
            self.assertIn("independent_rerun_required", experiment_harness["harness_template"])
            self.assertIn("real_dataset_provenance_verified", experiment_harness["harness_template"]["pass_criteria"])
            self.assertIn("real_model_provenance_verified", experiment_harness["harness_template"]["pass_criteria"])
            self.assertIn("reproduction_target_template", reproduction_manifest)
            self.assertTrue(reproduction_manifest["reproduction_target_template"]["full_reproduction_required"])
            self.assertIn("official_code_reuse", reproduction_manifest["allowed_reproduction_modes"])
            self.assertIn("result_binding_template", result_binding)
            self.assertIn("所有说明性 value 使用中文", global_spec["language_policy"]["values"])
            self.assertTrue((research_dir / "spec" / "shared" / "insight_policy.yaml").exists())
            self.assertTrue((research_dir / "spec" / "insights" / "insight_policy.yaml").exists())
            self.assertTrue((research_dir / "spec" / "insights" / "anomaly_schema.yaml").exists())
            self.assertTrue((research_dir / "spec" / "insights" / "pivot_proposal_schema.yaml").exists())
            self.assertTrue((research_dir / "spec" / "insights" / "diagnostic_experiment_policy.yaml").exists())
            self.assertTrue((research_dir / "spec" / "insights" / "insight_manifest.yaml").exists())
            self.assertTrue((research_dir / "spec" / "feedback" / "README.md").exists())
