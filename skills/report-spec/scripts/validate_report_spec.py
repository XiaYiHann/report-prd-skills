#!/usr/bin/env python3
"""Validate a v2 report spec directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parents[1]
SHARED_SCRIPT_DIR = SKILLS_DIR / "report" / "_shared" / "scripts"
if SHARED_SCRIPT_DIR.exists():
    sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from manifest_validator import validate_spec_manifests  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", default="", help="Spec directory, for example docs/report/<slug>/spec.")
    parser.add_argument("--workspace", default="", help="Report workspace; uses <workspace>/spec.")
    return parser.parse_args()


def resolve_spec(args: argparse.Namespace) -> Path:
    if args.spec:
        return Path(args.spec).resolve()
    if args.workspace:
        return (Path(args.workspace).resolve() / "spec").resolve()
    raise SystemExit("error: pass --spec docs/report/<slug>/spec or --workspace docs/report/<slug>")


def main() -> int:
    args = parse_args()
    spec_dir = resolve_spec(args)
    result = validate_spec_manifests(spec_dir)
    if result.issues:
        for issue in result.issues:
            location = f" {issue.location}" if issue.location else ""
            print(f"[{issue.severity}] {issue.category}{location}: {issue.message}")
    if result.execution_ready:
        print(f"[OK] execution-ready spec: {spec_dir}")
        return 0
    print(f"[BLOCKED] spec is not execution-ready: {spec_dir}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
