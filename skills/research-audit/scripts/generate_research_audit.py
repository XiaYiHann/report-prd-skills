#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    current_epoch_dir,
    generate_audit,
    generate_migration_audit,
    resolve_research_dir,
    run_epoch_audit_checks,
    today_string,
    write_audit_results_yaml,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dated cross-file research audit scaffold.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--research-dir", default="", help="Research workspace directory.")
    parser.add_argument("--date", default=today_string(), help="Audit date, YYYY-MM-DD.")
    parser.add_argument(
        "--mode",
        default="full",
        choices=["format", "migration", "epoch", "git", "evidence", "paper-binding", "full"],
        help="Audit mode. migration writes MIGRATION_AUDIT.md and MIGRATION_PLAN.md.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing audit files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = resolve_research_dir(args)
    if args.mode == "migration":
        audit_path, plan_path = generate_migration_audit(research_dir, args.force)
        print(f"[OK] wrote migration audit: {audit_path}")
        print(f"[OK] wrote migration plan: {plan_path}")
        return 0
    audit_dir = generate_audit(research_dir, args.date, args.force)
    if (research_dir / "CURRENT").exists():
        epoch_dir = current_epoch_dir(research_dir)
        if epoch_dir.exists():
            audit_mode = args.mode if args.mode in {"full", "epoch", "format", "git", "evidence", "paper-binding"} else "full"
            results = run_epoch_audit_checks(research_dir, audit_mode)
            epoch_audit_dir = epoch_dir / "audits" / f"{args.date}-audit"
            epoch_audit_dir.mkdir(parents=True, exist_ok=True)
            write_audit_results_yaml(epoch_audit_dir / "audit_results.yaml", results)
            print(f"[OK] wrote epoch audit results: {epoch_audit_dir / 'audit_results.yaml'}")
    print(f"[OK] wrote research audit: {audit_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
