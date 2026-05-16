#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import current_epoch_name, init_rq_spec_scaffold, init_spec_scaffold, resolve_research_dir  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the global research spec scaffold.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--rq", default="", help="Target RQ id for epoch-local RQ SPEC generation.")
    parser.add_argument("--all-rqs", action="store_true", help="Generate or repair RQ-local specs for all declared RQs.")
    parser.add_argument("--force", action="store_true", help="Overwrite spec files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    if not current_epoch_name(research_dir):
        init_spec_scaffold(research_dir, args.force)
    rq_specs = init_rq_spec_scaffold(research_dir, rq_id=args.rq or None, all_rqs=args.all_rqs, force=args.force)
    if not current_epoch_name(research_dir):
        print(f"[OK] wrote legacy research spec scaffold: {research_dir / 'spec'}")
    for path in rq_specs:
        print(f"[OK] wrote RQ spec scaffold: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
