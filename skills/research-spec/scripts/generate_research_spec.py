#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import init_spec_scaffold, resolve_research_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the global research spec scaffold.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite spec files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    init_spec_scaffold(research_dir, args.force)
    print(f"[OK] wrote research spec scaffold: {research_dir / 'spec'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
