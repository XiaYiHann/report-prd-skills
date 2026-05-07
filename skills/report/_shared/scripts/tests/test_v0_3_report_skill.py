#!/usr/bin/env python3
"""Regression tests for report skill family v0.3 hardening."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from accept_edits import process_report  # noqa: E402
from init_report import create_workspace  # noqa: E402
from scan_repo import collect as collect_repo_scan  # noqa: E402
from self_check_report import (  # noqa: E402
    collect_module_design_findings,
    collect_operational_readiness_findings,
    collect_research_evidence_findings,
)


SKILL_DIR = SCRIPT_DIR.parents[2]


def _make_report(root: Path, sections: dict[str, str]) -> Path:
    (root / "sections").mkdir(parents=True)
    for filename, content in sections.items():
        (root / "sections" / filename).write_text(content)
    return root


class AcceptEditsSectionScopeTests(unittest.TestCase):
    def test_process_report_can_accept_only_one_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sections").mkdir()
            (root / "build").mkdir()
            (root / "sections" / "01-a.tex").write_text(r"\reportadd{A}")
            (root / "sections" / "02-b.tex").write_text(r"\reportadd{B}")

            changed = process_report(root, dry_run=False, backup=False, section="01-a.tex")

            self.assertEqual(changed, ["sections/01-a.tex"])
            self.assertEqual((root / "sections" / "01-a.tex").read_text(), "A")
            self.assertEqual((root / "sections" / "02-b.tex").read_text(), r"\reportadd{B}")


class EvidenceAndOperationalReadinessTests(unittest.TestCase):
    def test_research_report_without_evidence_ledger_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "01-problem-statement.tex": "\\section{问题定义}\n本文提出一个 hypothesis。\n",
                    "06-experiments.tex": "\\section{实验}\n本文比较 baseline，并给出 ablation。\n",
                },
            )

            findings = collect_research_evidence_findings(root)

            self.assertTrue(any("evidence ledger" in f.message for f in findings))
            self.assertTrue(any("failure" in f.message.lower() for f in findings))

    def test_engineering_report_without_operational_readiness_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "04-system-architecture.tex": "\\section{系统架构}\nAPI 与 Worker 协作完成执行。\n",
                    "07-interfaces-and-contracts.tex": "\\section{接口契约}\n接口返回任务状态。\n",
                },
            )

            findings = collect_operational_readiness_findings(root)

            self.assertTrue(any("source-of-truth" in f.message for f in findings))
            self.assertTrue(any("runbook" in f.message.lower() for f in findings))


class InitReportTemplateTests(unittest.TestCase):
    def test_research_prd_template_contains_required_prd_gates(self) -> None:
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

            joined_sections = "\n".join(path.read_text() for path in sorted((root / "sections").glob("*.tex")))
            brief = (root / "brief.yaml").read_text()

            self.assertIn('report_type: "research-prd"', brief)
            self.assertIn("Research Questions", joined_sections)
            self.assertIn("可证伪假设", joined_sections)
            self.assertIn("Go / No-Go", joined_sections)
            self.assertIn("claim -> evidence -> source -> limitation -> confidence", joined_sections)
            self.assertIn("Baseline Matrix", joined_sections)
            self.assertIn("Failure-case Table", joined_sections)
            self.assertIn("/report/_shared/references/", brief)

    def test_engineering_prd_auto_modules_emit_module_figures_acceptance_and_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "repo"
            report_root = project_root / "docs" / "report" / "engineering-prd"
            (project_root / "src" / "api").mkdir(parents=True)
            (project_root / "src" / "worker").mkdir(parents=True)
            (project_root / "apps" / "web").mkdir(parents=True)
            (project_root / "tests").mkdir(parents=True)
            (project_root / "src" / "api" / "service.py").write_text("class ApiService:\n    pass\n")
            (project_root / "src" / "worker" / "tasks.py").write_text("def run_task():\n    return None\n")
            (project_root / "apps" / "web" / "page.tsx").write_text("export function Page() { return null }\n")
            (project_root / "tests" / "test_api.py").write_text("def test_api():\n    assert True\n")

            create_workspace(
                report_dir=report_root,
                title="工程 PRD",
                topic="模块级设计",
                report_type="engineering-prd",
                audience="rookie",
                author="Codex",
                project_root=project_root,
                module_source="auto",
                diagram_depth="draft",
            )

            module_section = (report_root / "sections" / "05-functional-requirements.tex").read_text()
            joined_sections = "\n".join(path.read_text() for path in sorted((report_root / "sections").glob("*.tex")))

            self.assertIn("\\input{figures/module-overview.tex}", module_section)
            self.assertIn("\\subsection{api 模块}", module_section)
            self.assertIn("\\subsection{worker 模块}", module_section)
            self.assertIn("接口 | 输入 | 输出 | 错误码 | 调用关系", module_section)
            self.assertIn("Acceptance Criteria", module_section)
            self.assertIn("Goals \\& Non-Goals", joined_sections)
            self.assertIn("Operational Readiness Matrix", joined_sections)
            self.assertTrue((report_root / "figures" / "module-overview.tex").exists())
            self.assertTrue((report_root / "figures" / "module-api-architecture.tex").exists())
            self.assertTrue((report_root / "figures" / "module-api-sequence.tex").exists())

    def test_legacy_report_types_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "legacy-report"
            with self.assertRaises(ValueError):
                create_workspace(
                    report_dir=root,
                    title="旧报告",
                    topic="旧类型",
                    report_type="research",
                    audience="mixed",
                    author="Codex",
                )


class ScanRepoModuleDiscoveryTests(unittest.TestCase):
    def test_collect_discovers_candidate_modules_from_repo_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "api").mkdir(parents=True)
            (root / "src" / "worker").mkdir(parents=True)
            (root / "packages" / "core").mkdir(parents=True)
            (root / "apps" / "web").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "src" / "api" / "service.py").write_text("class ApiService:\n    pass\n")
            (root / "src" / "worker" / "tasks.py").write_text("def run_task():\n    return None\n")
            (root / "packages" / "core" / "index.ts").write_text("export const core = true;\n")
            (root / "apps" / "web" / "page.tsx").write_text("export function Page() { return null }\n")
            (root / "tests" / "test_api.py").write_text("def test_api():\n    assert True\n")

            payload = collect_repo_scan(root)
            modules = {module["name"]: module for module in payload["module_candidates"]}

            self.assertIn("api", modules)
            self.assertIn("worker", modules)
            self.assertIn("core", modules)
            self.assertIn("web", modules)
            self.assertIn("src/api/service.py", modules["api"]["source_paths"])
            self.assertIn("tests/test_api.py", modules["api"]["test_paths"])


class ModuleDesignSelfCheckTests(unittest.TestCase):
    def test_module_design_without_required_module_artifacts_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_report(
                root,
                {
                    "05-core-module-design.tex": (
                        "\\section{核心模块设计}\n"
                        "\\subsection{api 模块}\n"
                        "这里只说明 api 模块的职责。\n"
                    )
                },
            )

            findings = collect_module_design_findings(root)

            self.assertTrue(any("模块总览图" in finding.message for finding in findings))
            self.assertTrue(any("接口契约表" in finding.message for finding in findings))
            self.assertTrue(any("时序图" in finding.message for finding in findings))


class LegacyReferenceWrapperTests(unittest.TestCase):
    def test_legacy_references_are_wrappers_to_shared_sources(self) -> None:
        legacy_dir = SKILL_DIR / "references"
        shared_dir = SKILL_DIR / "_shared" / "references"
        legacy_files = sorted(legacy_dir.glob("*.md"))
        self.assertTrue(legacy_files, "expected legacy compatibility reference files")

        for legacy in legacy_files:
            shared = shared_dir / legacy.name
            self.assertTrue(shared.exists(), f"missing shared source for {legacy.name}")
            text = legacy.read_text()
            self.assertIn("Compatibility wrapper", text, msg=legacy.name)
            self.assertIn(f"_shared/references/{legacy.name}", text, msg=legacy.name)


if __name__ == "__main__":
    unittest.main()
