#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import create_epoch  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new docs/research/Vn epoch from invariant templates.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--version", required=True, help="Target epoch version, e.g. V1.")
    parser.add_argument("--from-version", default="", help="Source closed epoch version. Defaults to CURRENT.")
    parser.add_argument("--force", action="store_true", help="Overwrite target epoch if allowed by helper.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    research_dir = repo / "docs" / "research"
    try:
        epoch_dir = create_epoch(
            research_dir,
            args.version,
            from_version=args.from_version.strip() or None,
            force=args.force,
        )
    except (OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] created epoch: {epoch_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
