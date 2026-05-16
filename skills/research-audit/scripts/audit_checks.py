#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    audit_results_payload,
    has_blocking_audit_failures,
    run_epoch_audit_checks,
    write_audit_results_yaml,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hard-gate research audit checks.")
    parser.add_argument("--research-dir", required=True, help="Research workspace directory.")
    parser.add_argument("--mode", default="full", choices=["full", "epoch", "evidence", "paper-binding"], help="Audit mode.")
    parser.add_argument("--format", default="text", choices=["text", "yaml"], help="Output format.")
    parser.add_argument("--output", default="", help="Optional YAML output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    research_dir = Path(args.research_dir).resolve()
    results = run_epoch_audit_checks(research_dir, args.mode)
    if args.output:
        write_audit_results_yaml(Path(args.output).resolve(), results)
    if args.format == "yaml":
        print(yaml.safe_dump(audit_results_payload(results), sort_keys=False, allow_unicode=True))
    else:
        for result in results:
            print(f"{result.status} {result.severity} {result.check_id}: {result.message}")
    return 1 if has_blocking_audit_failures(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
