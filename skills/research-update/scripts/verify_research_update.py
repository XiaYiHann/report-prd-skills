#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


VISIBLE_SKILLS = [
    "research",
    "research-explore",
    "research-insight",
    "research-status",
    "research-update",
    "research-init",
    "research-goal",
    "research-audit",
]

INTERNAL_MODULES = [
    "research-paper",
    "research-spec",
    "research-plan",
]

RETIRED_SKILLS = [
    "research-prd",
    "research-ppt",
    "research-evidence",
    "research-writing",
    "research-brainstorming",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the installed research-loop skill surface.")
    parser.add_argument("--skills-dir", default=str(Path.home() / ".agents" / "skills"))
    parser.add_argument("--claude-skills", default=str(Path.home() / ".claude" / "skills"))
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    return parser.parse_args()


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _visible_skill_names(skills_dir: Path) -> list[str]:
    if not skills_dir.exists():
        return []
    return sorted(path.parent.name for path in skills_dir.glob("*/SKILL.md"))


def inspect_surface(skills_dir: Path, claude_skills: Path) -> dict[str, Any]:
    issues: list[str] = []
    visible_found = _visible_skill_names(skills_dir)
    visible_set = set(visible_found)
    expected_set = set(VISIBLE_SKILLS)

    if not skills_dir.exists() or not skills_dir.is_dir():
        issues.append(f"canonical skills dir missing or not a directory: {skills_dir}")

    if not claude_skills.is_symlink():
        issues.append(f"claude skills path is not a symlink: {claude_skills}")
    else:
        target = os.path.realpath(claude_skills)
        canonical = os.path.realpath(skills_dir)
        if target != canonical:
            issues.append(f"claude skills symlink points to {target}, expected {canonical}")

    for name in VISIBLE_SKILLS:
        if name not in visible_set:
            issues.append(f"missing visible skill: {name}")

    for name in sorted(visible_set - expected_set):
        if name.startswith("research"):
            issues.append(f"unexpected visible research skill: {name}")

    internal_status: dict[str, dict[str, bool]] = {}
    for name in INTERNAL_MODULES:
        path = skills_dir / name
        has_dir = path.exists() and path.is_dir()
        has_skill = (path / "SKILL.md").exists()
        internal_status[name] = {"exists": has_dir, "has_skill_md": has_skill}
        if not has_dir:
            issues.append(f"missing internal compiler module: {name}")
        if has_skill:
            issues.append(f"internal compiler module still exposes SKILL.md: {name}")

    retired_status: dict[str, bool] = {}
    for name in RETIRED_SKILLS:
        present = _path_exists(skills_dir / name)
        retired_status[name] = present
        if present:
            issues.append(f"retired skill path still exists: {name}")

    return {
        "ok": not issues,
        "skills_dir": str(skills_dir),
        "claude_skills": str(claude_skills),
        "claude_skills_target": os.path.realpath(claude_skills) if _path_exists(claude_skills) else "",
        "expected_visible_skills": VISIBLE_SKILLS,
        "visible_skills": visible_found,
        "internal_modules": internal_status,
        "retired_present": retired_status,
        "issues": issues,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    marker = "OK" if payload["ok"] else "BLOCKED"
    lines = [
        "# Research Update Verification",
        "",
        f"- status: `{marker}`",
        f"- skills_dir: `{payload['skills_dir']}`",
        f"- claude_skills: `{payload['claude_skills']}`",
        f"- claude_skills_target: `{payload['claude_skills_target'] or 'N/A'}`",
        "",
        "## Visible Skills",
    ]
    for name in payload["visible_skills"]:
        lines.append(f"- `{name}`")

    lines.extend(["", "## Internal Modules"])
    for name, state in payload["internal_modules"].items():
        marker = "OK" if state["exists"] and not state["has_skill_md"] else "BLOCKED"
        lines.append(f"- `{name}`: {marker} exists={state['exists']} has_skill_md={state['has_skill_md']}")

    lines.extend(["", "## Retired Entries"])
    for name, present in payload["retired_present"].items():
        marker = "present" if present else "absent"
        lines.append(f"- `{name}`: {marker}")

    lines.extend(["", "## Issues"])
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    payload = inspect_surface(Path(args.skills_dir).expanduser(), Path(args.claude_skills).expanduser())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(payload), end="")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
