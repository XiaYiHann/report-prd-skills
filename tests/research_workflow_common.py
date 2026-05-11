#!/usr/bin/env python3
"""Regression tests for the research execution skill family."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
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
CLAUDE_AGENT_TEMPLATES_DIR = REPO_ROOT / "agents" / "claude-code"
SKILL_NAMES = [
    "research",
    "research-init",
    "research-prd",
    "research-paper",
    "research-spec",
    "research-plan",
    "research-audit",
    "research-ppt",
]
CLAUDE_RESEARCH_AGENT_NAMES = [
    "research-math",
    "research-literature",
    "research-reproduce",
    "research-coding",
    "research-experiment",
    "research-analysis",
    "research-paper",
    "research-ppt",
    "research-audit",
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


def latex_available() -> bool:
    return bool(shutil.which("latexmk") or shutil.which("xelatex"))
