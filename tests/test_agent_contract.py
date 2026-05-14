#!/usr/bin/env python3
"""Tests for Research Agent Behavior Contract validation and repair."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    AGENT_CONTRACT_RULES,
    repair_agent_contracts,
    validate_agent_contracts,
)
from tests.research_workflow_common import init_workspace_fast, write_yaml  # noqa: E402


class AgentContractTests(unittest.TestCase):
    def test_contract_section_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            claude_path = repo / "CLAUDE.md"
            agents_path = repo / "AGENTS.md"
            if claude_path.exists():
                claude_path.unlink()
            if agents_path.exists():
                agents_path.unlink()
            validation = validate_agent_contracts(research_dir)
        self.assertFalse(validation.ok)
        self.assertTrue(any("missing" in issue.lower() for issue in validation.issues))

    def test_contract_rules_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            claude_path = repo / "CLAUDE.md"
            agents_path = repo / "AGENTS.md"
            claude_path.write_text("# CLAUDE.md\n\n## Research Agent Behavior Contract\n\n1. RQ before action. Every task must map to a Research Question.\n", encoding="utf-8")
            agents_path.write_text("# AGENTS.md\n\n## 研究智能体行为契约\n\n1. RQ 先于行动。每个任务必须对应一个研究问题。\n", encoding="utf-8")
            validation = validate_agent_contracts(research_dir)
        self.assertFalse(validation.ok)
        missing_rules = [issue for issue in validation.issues if "missing rule" in issue.lower()]
        self.assertGreaterEqual(len(missing_rules), 1)

    def test_contract_all_present_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            actions = repair_agent_contracts(repo)
            validation = validate_agent_contracts(research_dir)
        self.assertTrue(validation.ok, f"Issues: {validation.issues}")
        self.assertEqual(len(validation.issues), 0)

    def test_repair_appends_missing_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            claude_path = repo / "CLAUDE.md"
            agents_path = repo / "AGENTS.md"
            claude_path.write_text("# CLAUDE.md\n\n- Basic rule.\n", encoding="utf-8")
            agents_path.write_text("# AGENTS.md\n\n- 基本规则。\n", encoding="utf-8")
            actions = repair_agent_contracts(repo)
            claude_text = claude_path.read_text(encoding="utf-8")
            agents_text = agents_path.read_text(encoding="utf-8")
        self.assertIn("## Research Agent Behavior Contract", claude_text)
        self.assertIn("## 研究智能体行为契约", agents_text)
        self.assertIn("1. RQ before action", claude_text)
        self.assertIn("10. Convention beats novelty", claude_text)
        self.assertTrue(any("CLAUDE.md" in a for a in actions))
        self.assertTrue(any("AGENTS.md" in a for a in actions))

    def test_repair_appends_missing_rules_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            claude_path = repo / "CLAUDE.md"
            agents_path = repo / "AGENTS.md"
            claude_path.write_text(
                "# CLAUDE.md\n\n## Research Agent Behavior Contract\n\n1. RQ before action. Every task must map to a Research Question.\n"
                "2. Reproduce before propose. Before claiming novelty.\n",
                encoding="utf-8",
            )
            agents_path.write_text(
                "# AGENTS.md\n\n## 研究智能体行为契约\n\n1. RQ 先于行动。每个任务必须对应一个研究问题。\n"
                "2. 复现先于提出。在声称新颖性之前。\n",
                encoding="utf-8",
            )
            actions = repair_agent_contracts(repo)
            claude_text = claude_path.read_text(encoding="utf-8")
            agents_text = agents_path.read_text(encoding="utf-8")
        self.assertIn("3. Evidence before writing", claude_text)
        self.assertIn("10. Convention beats novelty", claude_text)
        self.assertIn("3. 证据先于写作", agents_text)
        self.assertIn("10. 约定优于新奇", agents_text)
        self.assertTrue(any("missing" in a.lower() for a in actions))

    def test_repair_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace_fast(repo)
            claude_path = repo / "CLAUDE.md"
            agents_path = repo / "AGENTS.md"
            # Strip existing contract sections to simulate missing rules
            claude_text = claude_path.read_text(encoding="utf-8")
            agents_text = agents_path.read_text(encoding="utf-8")
            contract_start = claude_text.find("## Research Agent Behavior Contract")
            if contract_start != -1:
                claude_path.write_text(claude_text[:contract_start].rstrip() + "\n", encoding="utf-8")
            contract_start = agents_text.find("## 研究智能体行为契约")
            if contract_start != -1:
                agents_path.write_text(agents_text[:contract_start].rstrip() + "\n", encoding="utf-8")
            actions1 = repair_agent_contracts(repo)
            actions2 = repair_agent_contracts(repo)
            self.assertGreater(len(actions1), 0)
            self.assertEqual(len(actions2), 0)
            validation = validate_agent_contracts(research_dir)
            self.assertTrue(validation.ok, f"Validation failed with issues: {validation.issues}")


if __name__ == "__main__":
    unittest.main()
