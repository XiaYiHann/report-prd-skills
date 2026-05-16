#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import resolve_research_dir, write_research_goal  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or refresh the active epoch research goal.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--target", default="both", choices=["codex", "claude-code", "both"], help="Executor target.")
    parser.add_argument("--no-force", action="store_true", help="Do not overwrite an existing goal.md.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    goal_path, lock_path = write_research_goal(research_dir, target_executor=args.target, force=not args.no_force)
    print(f"[OK] wrote research goal: {goal_path}")
    print(f"[OK] wrote research goal lock: {lock_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
