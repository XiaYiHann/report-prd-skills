#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import generate_audit, resolve_research_dir, today_string  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dated cross-file research audit scaffold.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--date", default=today_string(), help="Audit date, YYYY-MM-DD.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing audit files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    audit_dir = generate_audit(research_dir, args.date, args.force)
    print(f"[OK] wrote research audit: {audit_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
