#!/usr/bin/env python3
"""Regression tests for the research execution skill family."""

from __future__ import annotations

import atexit
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
GOAL_SCRIPT = REPO_ROOT / "skills" / "research-goal" / "scripts" / "generate_research_goal.py"
STATUS_SCRIPT = REPO_ROOT / "skills" / "research-status" / "scripts" / "research_status.py"
UPDATE_VERIFY_SCRIPT = REPO_ROOT / "skills" / "research-update" / "scripts" / "verify_research_update.py"
AUDIT_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "generate_research_audit.py"
RESEARCH_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "research_loop.py"
CREATE_EPOCH_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "create_epoch.py"
UPDATE_STATE_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "update_state.py"
INSTALL_SCRIPT = REPO_ROOT / "install.sh"
CLAUDE_AGENT_TEMPLATES_DIR = REPO_ROOT / "agents" / "claude-code"
SKILL_NAMES = [
    "research",
    "research-explore",
    "research-insight",
    "research-status",
    "research-update",
    "research-init",
    "research-goal",
    "research-audit",
]
INTERNAL_COMPILER_MODULE_NAMES = [
    "research-paper",
    "research-spec",
    "research-plan",
]
CLAUDE_RESEARCH_AGENT_NAMES = [
    "research-math",
    "research-literature",
    "research-reproduce",
    "research-coding",
    "research-experiment",
    "research-analysis",
    "research-paper",
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


_plain_template: Path | None = None


def _get_plain_template() -> Path:
    global _plain_template
    if _plain_template is None:
        tmp = Path(tempfile.mkdtemp(prefix="research_plain_template_"))
        result = subprocess.run(
            [
                "python3",
                str(INIT_SCRIPT),
                "--repo",
                str(tmp),
                "--title",
                "Test Research",
                "--purpose",
                "minimal-regression",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        _plain_template = tmp
        atexit.register(shutil.rmtree, str(tmp), ignore_errors=True)
    return _plain_template


def plan_dir_for(research_dir: Path, plan_id: str) -> Path:
    current = research_dir / "CURRENT"
    version = current.read_text(encoding="utf-8").strip() if current.exists() else ""
    if version and (research_dir / version / "plans" / plan_id / "plan.yaml").exists():
        return research_dir / version / "plans" / plan_id
    return research_dir / "plans" / plan_id


def init_workspace_fast(repo: Path) -> Path:
    template = _get_plain_template()
    shutil.copytree(template, repo, dirs_exist_ok=True)
    return repo / "docs" / "research"


def latex_available() -> bool:
    return bool(shutil.which("latexmk") or shutil.which("xelatex"))
