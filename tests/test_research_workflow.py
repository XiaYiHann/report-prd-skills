#!/usr/bin/env python3
"""Regression tests for the research execution skill family."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
import os
import shutil
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = REPO_ROOT / "skills" / "research-init" / "scripts" / "init_research.py"
VALIDATE_SCRIPT = REPO_ROOT / "skills" / "research-spec" / "scripts" / "validate_research.py"
PAPER_SCRIPT = REPO_ROOT / "skills" / "research-paper" / "scripts" / "generate_research_paper.py"
PLAN_SCRIPT = REPO_ROOT / "skills" / "research-plan" / "scripts" / "generate_research_plan.py"
PPT_SCRIPT = REPO_ROOT / "skills" / "research-ppt" / "scripts" / "generate_research_ppt.py"
AUDIT_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "generate_research_audit.py"
RESEARCH_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "research_loop.py"
INSTALL_SCRIPT = REPO_ROOT / "install.sh"
SKILL_NAMES = [
    "report",
    "research",
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
            "",
        ]
    )
    prd_path.write_text(prd_path.read_text(encoding="utf-8") + appendix, encoding="utf-8")


def latex_available() -> bool:
    return bool(shutil.which("latexmk") or shutil.which("xelatex"))


class ResearchWorkflowTests(unittest.TestCase):
    def test_installer_installs_research_family_and_removes_old_report_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "skills"
            claude_target = Path(tmp) / "claude" / "skills"
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
            env["RESEARCH_EXECUTION_SKILLS_CLAUDE_TARGET_DIR"] = str(claude_target)

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
            for skill_name in [name for name in SKILL_NAMES if name == "research" or name.startswith("research-")]:
                link = claude_target / skill_name
                self.assertTrue(link.is_symlink(), skill_name)
                self.assertEqual(link.resolve(), (target / skill_name).resolve())
            self.assertFalse((claude_target / "report").exists())
            self.assertIn("Linked research skills for Claude Code", result.stdout)

    def test_research_init_scaffolds_docs_research_tree_and_required_prd_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))

            expected_dirs = ["prd", "paper", "spec", "plans", "ppt", "audits", "insights"]
            for dirname in expected_dirs:
                self.assertTrue((research_dir / dirname).exists(), dirname)
            self.assertTrue((research_dir / "insights" / "anomaly_reports").exists())
            self.assertTrue((research_dir / "insights" / "pivot_proposals").exists())
            self.assertTrue((research_dir / "insights" / "negative_results").exists())
            self.assertTrue((research_dir / "insights" / "insight_log.md").exists())
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

            self.assertIn("全局机器可读执行契约", readme)
            self.assertIn("不要从论文反推实验", readme)
            self.assertIn("复现缺口报告", gap)
            self.assertIn("【阻塞】", gap)
            self.assertIn("schema_version", global_spec)
            self.assertEqual(global_spec["authority"], "compile_from_prd_not_paper")
            self.assertIn("只能从 Research PRD 编译", global_spec["notes"][0])
            self.assertIn("科研主张", anti_mock["forbidden_for_description"]["research_claim"])

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
            self.assertIn("manuscript draft 中的 mock 数值必须在 gap report 中登记替换条件", gap_report)

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
            self.assertIn("harness_template", experiment_harness)
            self.assertIn("independent_rerun_required", experiment_harness["harness_template"])
            self.assertIn("reproduction_target_template", reproduction_manifest)
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

    def test_research_paper_script_uses_full_template_and_spec_bound_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
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
            self.assertIn("论文正文中的表格和结果段落已使用 mock 数值填充，以呈现完整 manuscript", gap_report)
            self.assertEqual(placeholder_map["placeholders"][0]["experiment_id"], "E01")

    def test_research_paper_demo_generates_complete_mock_data_manuscript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

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
            self.assertIn("## 6. Mock Planning Data and Expected Sensitivity", paper_md)
            self.assertIn("0.46", paper_md)
            self.assertIn("{{E01.OURS.task_success}}", paper_md)
            self.assertNotIn("【待填写", paper_md)
            self.assertNotIn("Experiments show", paper_md)
            self.assertIn("完整 mock-data manuscript draft", gap_report)
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
            research_dir = init_workspace(repo)
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

            plan_dir = research_dir / "plans" / "2026-05-09-reproduce-b01"
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
            self.assertIn("洞察问题", prompt)
            self.assertIn("有没有值得微调 15 度的方向", prompt)
            self.assertTrue((plan_dir / "insight_log.md").exists())
            self.assertIn("当前状态", current_state)

    def test_research_plan_accepts_insight_feedback_track(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
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
            self.assertTrue((research_dir / "plans" / "2026-05-09-review-negative-result" / "plan.yaml").exists())

    def test_research_loop_empty_workspace_initializes_state_and_prd_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            research_dir = repo / "docs" / "research"
            self.assertTrue((research_dir / "state.yaml").exists())
            self.assertTrue((research_dir / "plans" / "plan_queue.yaml").exists())
            self.assertTrue((research_dir / "prd" / "research_prd.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S1_PRD_NOT_READY")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertFalse(state["prd"]["human_approved"])

    def test_research_loop_prd_not_approved_stops_before_spec_automation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S1_PRD_NOT_READY")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertIsNone(state["plans"]["active"])
            self.assertIn("human approval", state["project_status"]["block_reason"])

    def test_research_loop_prd_ready_spec_missing_generates_spec_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            shutil.rmtree(research_dir / "spec")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((research_dir / "spec" / "global_spec.yaml").exists())
            self.assertTrue((research_dir / "spec" / "feedback" / "README.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["spec"]["status"], "not_ready")
            self.assertTrue(state["project_status"]["blocked"])

    def test_research_loop_spec_ready_no_plan_generates_queue_and_next_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            queue = read_yaml(research_dir / "plans" / "plan_queue.yaml")
            self.assertGreaterEqual(len(queue["queue"]), 1)
            state = read_yaml(research_dir / "state.yaml")
            active_plan = state["plans"]["active"]
            self.assertIsNotNone(active_plan)
            self.assertTrue((research_dir / "plans" / active_plan / "plan.yaml").exists())
            self.assertEqual(state["project_status"]["current_stage"], "S4_EXECUTING_PLAN")

    def test_research_loop_active_plan_complete_writes_feedback_insight_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            plan_result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-10",
                    "--purpose",
                    "reproduce-b01",
                    "--track",
                    "reproduction",
                ],
                cwd=repo,
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stdout + plan_result.stderr)
            plan_dir = research_dir / "plans" / "2026-05-10-reproduce-b01"
            plan_yaml = read_yaml(plan_dir / "plan.yaml")
            plan_yaml["status"] = "complete"
            write_yaml(plan_dir / "plan.yaml", plan_yaml)
            (plan_dir / "final_summary.md").write_text(
                "# 最终总结\n\nPLAN_STATUS: COMPLETE\nHARNESS_EVIDENCE: documented in run_log.md\n",
                encoding="utf-8",
            )
            (plan_dir / "run_log.md").write_text(
                "# 运行日志\n\n- harness stdout/stderr paths recorded by executor.\n",
                encoding="utf-8",
            )

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((research_dir / "spec" / "feedback" / "2026-05-10-reproduce-b01_lessons.md").exists())
            self.assertTrue((research_dir / "audits" / "2026-05-10-audit" / "audit_report.md").exists())
            insight_log = (research_dir / "insights" / "insight_log.md").read_text(encoding="utf-8")
            self.assertIn("2026-05-10-reproduce-b01", insight_log)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["last_audit"], "docs/research/audits/2026-05-10-audit")

    def test_research_loop_prd_ambiguity_writes_human_review_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir, ambiguity=True)
            shutil.rmtree(research_dir / "spec")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            review_dir = research_dir / "audits" / "2026-05-10-prd-review"
            self.assertTrue((review_dir / "prd_change_request.md").exists())
            self.assertTrue((review_dir / "repair_plan.md").exists())
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S6_INSIGHT_REVIEW_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])

    def test_research_loop_open_pivot_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            pivot = research_dir / "insights" / "pivot_proposals" / "p01.md"
            pivot.write_text("# Pivot Proposal\n\n## Human Decision Required\nApprove / reject / revise\n", encoding="utf-8")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S6_INSIGHT_REVIEW_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])
            self.assertEqual(state["insights"]["open_pivot_proposals"], ["docs/research/insights/pivot_proposals/p01.md"])

    def test_research_loop_stale_plan_blocks_execution_with_audit_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            mark_prd_human_approved(research_dir)
            make_execution_ready_spec(research_dir)
            plan_result = run_cmd(
                [
                    "python3",
                    str(PLAN_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-10",
                    "--purpose",
                    "run-e01-main-experiment",
                    "--track",
                    "experiment",
                ],
                cwd=repo,
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stdout + plan_result.stderr)
            spec = research_dir / "spec" / "global_spec.yaml"
            spec.write_text(spec.read_text(encoding="utf-8") + "\n# drift after plan creation\n", encoding="utf-8")

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--date", "2026-05-10", "--json"],
                cwd=repo,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = read_yaml(research_dir / "state.yaml")
            self.assertEqual(state["project_status"]["current_stage"], "S5_AUDIT_REQUIRED")
            self.assertTrue(state["project_status"]["blocked"])
            repair = (research_dir / "audits" / "2026-05-10-audit" / "repair_plan.md").read_text(encoding="utf-8")
            self.assertIn("stale spec hash", repair)

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

    def test_insight_ready_validates_insight_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_execution_ready_spec(research_dir)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "insight-ready"])
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

            # Delete insight_policy.yaml and assert failure
            (research_dir / "spec" / "shared" / "insight_policy.yaml").unlink()
            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "insight-ready"])
            self.assertNotEqual(check.returncode, 0)
            self.assertIn("insight_policy.yaml", check.stdout + check.stderr)

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

            matrix = read_yaml(audit_dir / "alignment_matrix.yaml")
            self.assertIn("prd_to_insight", matrix.get("dimensions", {}))
            self.assertIn("insight_to_spec", matrix.get("dimensions", {}))
            repair = (audit_dir / "repair_plan.md").read_text(encoding="utf-8")
            self.assertIn("Insight opportunity", repair)

            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
