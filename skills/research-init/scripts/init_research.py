#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPT_DIR = SCRIPT_DIR.parent / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import compile_minimal_scientific_judgment, init_research_workspace  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize docs/research for the research execution skill family.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--title", default="Research Project", help="Research project title.")
    parser.add_argument("--purpose", default="initial-research-scaffold", help="Minimum viable research purpose.")
    parser.add_argument(
        "--judgment-file",
        default="",
        help="YAML file containing the minimal scientific judgment input.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite scaffold files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if args.judgment_file:
        judgment_path = Path(args.judgment_file).resolve()
        research_dir = compile_minimal_scientific_judgment(repo, judgment_path, args.force)
        print(f"[OK] compiled minimal scientific judgment workspace: {research_dir}")
    else:
        research_dir = init_research_workspace(repo, args.title, args.purpose, args.force)
        print(f"[OK] initialized research workspace: {research_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
