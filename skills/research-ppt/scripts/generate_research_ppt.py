#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import generate_ppt, resolve_research_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate slide-image research deck specs for PNG/PDF output.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--mode", default="standard", choices=["short", "standard", "long", "pitch", "defense"])
    parser.add_argument("--force", action="store_true", help="Overwrite existing deck files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "standard" if args.mode in {"pitch", "defense"} else args.mode
    research_dir = resolve_research_dir(args)
    deck_dir = generate_ppt(research_dir, mode, args.force)
    print(f"[OK] wrote research slide-image deck spec: {deck_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
