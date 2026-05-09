#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import print_validation, resolve_research_dir, validate_research  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate docs/research readiness modes.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["prd-ready", "paper-ready", "spec-ready", "plan-ready", "ppt-ready", "audit-ready", "alignment-check"],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    validation = validate_research(research_dir, args.mode)
    return print_validation(validation, args.mode, research_dir)


if __name__ == "__main__":
    raise SystemExit(main())
