#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import generate_plan, resolve_research_dir, today_string  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dated concrete research execution plan.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--date", default=today_string(), help="Plan date, YYYY-MM-DD.")
    parser.add_argument("--purpose", required=True, help="Plan purpose slug or sentence.")
    parser.add_argument(
        "--track",
        required=True,
        choices=["reproduction", "implementation", "experiment", "paper-update", "insight-feedback"],
    )
    parser.add_argument("--gate", default="", help="Optional target gate id.")
    parser.add_argument("--target", default="codex", choices=["codex", "ralph-loop"], help="Executor target.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing plan files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    plan_dir = generate_plan(
        research_dir=research_dir,
        date=args.date,
        purpose=args.purpose,
        track=args.track,
        gate=args.gate or None,
        target=args.target,
        force=args.force,
    )
    print(f"[OK] wrote research plan: {plan_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
