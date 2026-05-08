#!/usr/bin/env python3
"""Generate a v2 report spec scaffold without inventing execution facts."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


SCHEMA_VERSION = "1.0"
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "assets" / "templates"


def write_yaml_if_missing(path: Path, payload: dict, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_text_if_missing(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def infer_workspace(args: argparse.Namespace) -> Path:
    if args.workspace:
        return Path(args.workspace).resolve()
    repo = Path(args.repo).resolve()
    docs_report = repo / "docs" / "report"
    candidates = [path for path in docs_report.glob("*") if path.is_dir()] if docs_report.exists() else []
    candidates = [path for path in candidates if any((path / name).exists() for name in ("main", "sections", "report.tex"))]
    if len(candidates) == 1:
        return candidates[0].resolve()
    raise SystemExit("error: pass --workspace docs/report/<slug> when the active report workspace is ambiguous")


YAML_TEMPLATES = [
    "execution_spec.yaml",
    "experiment_manifest.yaml",
    "task_graph.yaml",
    "harness.yaml",
    "dataset_manifest.yaml",
    "model_manifest.yaml",
    "baseline_manifest.yaml",
    "metric_manifest.yaml",
    "seed_protocol.yaml",
    "evidence_contract.yaml",
    "anti_mock_policy.yaml",
]


def generate_spec(workspace: Path, force: bool) -> Path:
    spec_dir = workspace / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    for relative_path in YAML_TEMPLATES:
        template_path = TEMPLATE_DIR / relative_path
        payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        write_yaml_if_missing(spec_dir / relative_path, payload, force)
    codex_goal_template = (TEMPLATE_DIR / "codex_goal.md").read_text(encoding="utf-8")
    write_text_if_missing(
        spec_dir / "codex_goal.md",
        codex_goal_template,
        force,
    )
    write_text_if_missing(
        spec_dir / "spec_gap_report.md",
        "\n".join(
            [
                "# Spec Gap Report",
                "",
                "- [BLOCKED] Compile concrete RQ / claim / experiment / task / harness / evidence contracts from `main/`.",
                "- [BLOCKED] Keep `paper/` placeholders mapped to spec experiments or evidence contracts.",
                "",
            ]
        ),
        force,
    )
    return spec_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="", help="Report workspace, for example docs/report/<slug>.")
    parser.add_argument("--repo", default=".", help="Repository root used only when --workspace is omitted.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing spec files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = infer_workspace(args)
    spec_dir = generate_spec(workspace, args.force)
    print(f"[OK] wrote report spec scaffold: {spec_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
