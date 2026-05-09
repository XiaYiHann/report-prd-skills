#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPT_DIR = SCRIPT_DIR.parent / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import init_research_workspace  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize docs/research for the research execution skill family.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--title", default="Research Project", help="Research project title.")
    parser.add_argument("--purpose", default="initial-research-scaffold", help="Minimum viable research purpose.")
    parser.add_argument("--force", action="store_true", help="Overwrite scaffold files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = init_research_workspace(Path(args.repo).resolve(), args.title, args.purpose, args.force)
    print(f"[OK] initialized research workspace: {research_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
