#!/usr/bin/env python3
"""Shared helpers for the research execution skill family."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


SCHEMA_VERSION = 1
DEFAULT_RESEARCH_DIR = Path("docs") / "research"
FORBIDDEN_RESULT_PHRASES = [
    "experiments show",
    "our method outperforms",
    "we achieve state-of-the-art",
    "state-of-the-art",
    "the results demonstrate",
    "results demonstrate",
]
REPRODUCTION_MODES = {"official_code_reuse", "official_code_adaptation", "paper_based_reimplementation"}


PRD_SECTIONS = [
    "## 1. Executive Summary",
    "## 2. Background Tutorial",
    "## 3. Related Work Map",
    "## 4. Benchmark and Reproduction Plan",
    "## 5. Problem Statement",
    "## 6. Research Questions and Hypotheses",
    "## 7. Formalization",
    "## 8. Proposed Method",
    "## 9. System and Implementation Design",
    "## 10. Experiment Design",
    "## 11. Task Graph and Student Work Plan",
    "## 12. Harness and Acceptance Criteria",
    "## 13. Evidence Ledger",
    "## 14. Paper Plan",
    "## 15. Risks, Limitations, and Ethics",
]


SPEC_FILES = [
    "global_spec.yaml",
    "shared/dataset_manifest.yaml",
    "shared/metric_manifest.yaml",
    "shared/model_manifest.yaml",
    "shared/environment_spec.yaml",
    "shared/seed_protocol.yaml",
    "shared/artifact_schema.yaml",
    "shared/anti_mock_policy.yaml",
    "shared/evidence_contract.yaml",
    "reproduction/benchmark_candidate_matrix.yaml",
    "reproduction/reproduction_manifest.yaml",
    "reproduction/reproduction_task_graph.yaml",
    "reproduction/reproduction_harness.yaml",
    "reproduction/reproduction_gap_report.md",
    "implementation/module_contracts.yaml",
    "implementation/implementation_task_graph.yaml",
    "implementation/implementation_harness.yaml",
    "experiments/experiment_manifest.yaml",
    "experiments/experiment_task_graph.yaml",
    "experiments/experiment_harness.yaml",
    "paper/placeholder_map.yaml",
    "paper/result_binding.yaml",
]


AUDIT_MATRIX_KEYS = [
    "prd_to_paper",
    "prd_to_spec",
    "spec_to_plan",
    "paper_to_spec",
    "plan_to_artifact",
    "prd_paper_spec_to_ppt",
]


STANDARD_SLIDES = [
    ("S01", "01_title.png", "01_title.md", "Title", "Introduce the project and one-sentence thesis"),
    (
        "S02",
        "02_motivation.png",
        "02_motivation.md",
        "Background and motivation",
        "Explain why the research problem matters",
    ),
    ("S03", "03_rq.png", "03_rq.md", "Problem gap and research questions", "State the gap and RQs"),
    ("S04", "04_formulation.png", "04_formulation.md", "Problem formulation", "Show the formal setup"),
    ("S05", "05_key_insight.png", "05_key_insight.md", "Key insight", "Communicate the central idea"),
    ("S06", "06_method_overview.png", "06_method_overview.md", "Method overview", "Show the method pipeline"),
    ("S07", "07_system_design.png", "07_system_design.md", "Method details / system design", "Detail modules"),
    (
        "S08",
        "08_reproduction.png",
        "08_reproduction.md",
        "Benchmark and reproduction plan",
        "Explain baseline reproduction",
    ),
    ("S09", "09_experiments.png", "09_experiments.md", "Experiment design", "Describe evaluation protocol"),
    ("S10", "10_contributions.png", "10_contributions.md", "Expected contributions", "Summarize planned contributions"),
    ("S11", "11_risks.png", "11_risks.md", "Risks / challenges", "Show technical and evidence risks"),
    ("S12", "12_summary.png", "12_summary.md", "Summary and next steps", "Close with execution plan"),
]


def today_string() -> str:
    return dt.date.today().isoformat()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def write_text(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_yaml(path: Path, payload: dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(read_text(path))
    return payload if isinstance(payload, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "research-run"


def minimal_pdf_bytes(title: str) -> bytes:
    safe_title = title.encode("ascii", "ignore").decode("ascii") or "Research Artifact"
    content = f"BT /F1 18 Tf 72 720 Td ({safe_title}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(content)} >> stream\n{content}\nendstream endobj",
    ]
    offsets: list[int] = []
    body = b"%PDF-1.4\n"
    for obj in objects:
        offsets.append(len(body))
        body += obj.encode("ascii") + b"\n"
    xref_offset = len(body)
    xref = ["xref", f"0 {len(objects) + 1}", "0000000000 65535 f "]
    xref.extend(f"{offset:010d} 00000 n " for offset in offsets)
    trailer = f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    return body + ("\n".join(xref) + "\n" + trailer).encode("ascii")


def write_pdf(path: Path, title: str, force: bool = False) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(minimal_pdf_bytes(title))


def prd_markdown(title: str, purpose: str) -> str:
    return f"""# Research PRD

## 1. Executive Summary
- One-sentence project summary: {title}.
- Core research problem: TODO.
- Expected contribution: TODO.
- Minimum viable research goal: {purpose}.
- Current project status: scaffold.

## 2. Background Tutorial
- Domain background: TODO.
- Fundamental concepts: TODO.
- Required math / systems / ML / security background, as applicable: TODO.
- Common beginner misunderstandings: TODO.
- Why this project is worth doing: TODO.

## 3. Related Work Map
- Research lineage: TODO.
- Representative methods: TODO.
- What each method solves: TODO.
- What each method does not solve: TODO.
- Closest baselines: TODO.
- Differences between our work and prior work: TODO.

## 4. Benchmark and Reproduction Plan
- Benchmark selection criteria: TODO.
- Candidate benchmark paper matrix: TODO.
- Selected reproduction targets: TODO.
- Official-code reuse / official-code adaptation / paper-based reimplementation classification: TODO.
- Reproduction protocol: TODO.
- Reproduction risks: TODO.
- Scaffold reuse plan: TODO.

## 5. Problem Statement
- Informal problem description: TODO.
- Formal problem definition: TODO.
- Scope: TODO.
- Non-goals: TODO.
- Threat model / assumptions if applicable: TODO.

## 6. Research Questions and Hypotheses
- RQ table: TODO.
- Hypothesis table: TODO.
- Expected claim for each RQ: TODO.
- Falsification conditions: TODO.

## 7. Formalization
- Notation: TODO.
- Objective: TODO.
- Constraints: TODO.
- Optimization target / system target: TODO.
- Theoretical rationale: TODO.
- Expected properties: TODO.

## 8. Proposed Method
- Method overview: TODO.
- Key idea: TODO.
- Module breakdown: TODO.
- Algorithm / workflow: TODO.
- Complexity: TODO.
- Failure modes: TODO.

## 9. System and Implementation Design
- Code architecture: TODO.
- Data flow: TODO.
- Config design: TODO.
- Module interfaces: TODO.
- Inputs and outputs: TODO.
- Reproducibility design: TODO.

## 10. Experiment Design
- Dataset plan: TODO.
- Baseline plan: TODO.
- Metric definitions: TODO.
- Main experiments: TODO.
- Ablation studies: TODO.
- Sensitivity analysis: TODO.
- Failure-case analysis: TODO.
- Statistical protocol: TODO.

## 11. Task Graph and Student Work Plan
- Phase breakdown: TODO.
- Task list: TODO.
- Task dependencies: TODO.
- Task inputs / outputs / acceptance criteria: TODO.
- Weekly milestones: TODO.
- Go / No-Go checkpoints: TODO.

## 12. Harness and Acceptance Criteria
- Unit harness: TODO.
- Integration harness: TODO.
- Experiment harness: TODO.
- Reproduction harness: TODO.
- Evidence requirements: TODO.
- Anti-mock policy: TODO.

## 13. Evidence Ledger
- Claim-to-evidence mapping: TODO.
- Experiment-to-claim mapping: TODO.
- Current evidence status: TODO.
- Missing evidence: TODO.
- Which results may enter paper: TODO.

## 14. Paper Plan
- Planned title: {title}.
- Planned abstract logic: TODO.
- Planned contributions: TODO.
- Planned figures and tables: TODO.
- Planned experiment-to-section mapping: TODO.
- What can be written before experiments: TODO.
- What must wait for evidence: TODO.

## 15. Risks, Limitations, and Ethics
- Technical risks: TODO.
- Experiment risks: TODO.
- Theory risks: TODO.
- Academic integrity risks: TODO.
- Data / ethics / reproducibility risks: TODO.
- Limitation plan: TODO.
"""


def latex_from_markdown(markdown: str) -> str:
    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{hyperref}",
        r"\title{Research PRD}",
        r"\date{\today}",
        r"\begin{document}",
        r"\maketitle",
    ]
    for line in markdown.splitlines():
        if line.startswith("# "):
            lines.append(r"\section*{" + line[2:].replace("&", r"\&") + "}")
        elif line.startswith("## "):
            lines.append(r"\subsection*{" + line[3:].replace("&", r"\&") + "}")
        elif line.startswith("- "):
            lines.append(line.replace("&", r"\&") + r"\\")
        elif line.strip():
            lines.append(line.replace("&", r"\&") + r"\\")
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def init_spec_scaffold(research_dir: Path, force: bool = False) -> None:
    spec = research_dir / "spec"
    write_text(
        spec / "README.md",
        "# Research Spec\n\nThis directory is the global machine-readable execution contract compiled from the Research PRD.\n",
        force,
    )
    write_yaml(
        spec / "global_spec.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "status": "scaffold",
            "source": {"prd": "docs/research/prd/research_prd.md"},
            "authority": "compile_from_prd_not_paper",
            "rq_chain": [],
            "blockers": ["Compile RQ -> Hypothesis -> Claim -> Experiment -> Harness -> Evidence from PRD."],
        },
        force,
    )
    shared_payloads = {
        "dataset_manifest.yaml": {"schema_version": SCHEMA_VERSION, "datasets": []},
        "metric_manifest.yaml": {"schema_version": SCHEMA_VERSION, "metrics": []},
        "model_manifest.yaml": {"schema_version": SCHEMA_VERSION, "models": []},
        "environment_spec.yaml": {"schema_version": SCHEMA_VERSION, "environments": []},
        "seed_protocol.yaml": {"schema_version": SCHEMA_VERSION, "seed_protocols": []},
        "artifact_schema.yaml": {"schema_version": SCHEMA_VERSION, "artifact_schemas": []},
        "anti_mock_policy.yaml": {
            "schema_version": SCHEMA_VERSION,
            "allowed_for": ["unit_test", "smoke_test", "harness_plumbing"],
            "forbidden_for": [
                "research_claim",
                "benchmark_result",
                "baseline_comparison",
                "ablation_result",
                "final_task_completion",
                "paper_table",
                "paper_figure",
                "go_no_go_decision",
            ],
        },
        "evidence_contract.yaml": {
            "schema_version": SCHEMA_VERSION,
            "claims": [],
            "evidence_rules": {
                "forbidden_as_claim_evidence": [
                    "mock_result",
                    "toy_result",
                    "smoke_test_only",
                    "cached_metric_without_raw_runs",
                ]
            },
        },
    }
    for filename, payload in shared_payloads.items():
        write_yaml(spec / "shared" / filename, payload, force)

    write_yaml(
        spec / "reproduction" / "benchmark_candidate_matrix.yaml",
        {"schema_version": SCHEMA_VERSION, "candidate_papers": []},
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_manifest.yaml",
        {"schema_version": SCHEMA_VERSION, "reproduction_targets": []},
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "reproduction" / "reproduction_harness.yaml",
        {"schema_version": SCHEMA_VERSION, "harnesses": []},
        force,
    )
    write_text(
        spec / "reproduction" / "reproduction_gap_report.md",
        "# Reproduction Gap Report\n\n- [BLOCKED] Fill benchmark targets, reproduction modes, commands, and artifacts from the PRD.\n",
        force,
    )
    write_yaml(spec / "implementation" / "module_contracts.yaml", {"schema_version": SCHEMA_VERSION, "modules": []}, force)
    write_yaml(
        spec / "implementation" / "implementation_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "implementation" / "implementation_harness.yaml",
        {"schema_version": SCHEMA_VERSION, "harnesses": []},
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_manifest.yaml",
        {"schema_version": SCHEMA_VERSION, "experiments": [], "claims": []},
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_task_graph.yaml",
        {"schema_version": SCHEMA_VERSION, "tasks": [], "gates": []},
        force,
    )
    write_yaml(
        spec / "experiments" / "experiment_harness.yaml",
        {"schema_version": SCHEMA_VERSION, "harnesses": []},
        force,
    )
    write_yaml(spec / "paper" / "placeholder_map.yaml", {"placeholders": []}, force)
    write_yaml(spec / "paper" / "result_binding.yaml", {"schema_version": SCHEMA_VERSION, "bindings": []}, force)


def init_research_workspace(repo: Path, title: str, purpose: str, force: bool = False) -> Path:
    research_dir = repo / DEFAULT_RESEARCH_DIR
    for dirname in ["prd", "paper", "spec", "plans", "ppt", "audits"]:
        (research_dir / dirname).mkdir(parents=True, exist_ok=True)

    prd = prd_markdown(title, purpose)
    write_text(research_dir / "prd" / "research_prd.md", prd, force)
    write_text(research_dir / "prd" / "research_prd.tex", latex_from_markdown(prd), force)
    write_pdf(research_dir / "prd" / "research_prd.pdf", title, force)

    paper_md = "\n".join(
        [
            f"# {title}",
            "",
            "## Abstract",
            "We propose a research program derived from the Research PRD. Empirical claims remain experiment-bound placeholders until execution.",
            "",
            "## Introduction",
            "TODO: compile motivation, gap, and contributions from the PRD.",
            "",
            "## Method",
            "TODO: formulate and describe the proposed method from PRD sections 7 and 8.",
            "",
            "## Evaluation Plan",
            "Experiment placeholders must be registered in placeholder_map.yaml before use.",
            "",
        ]
    )
    write_text(research_dir / "paper" / "planned_paper.md", paper_md, force)
    write_text(research_dir / "paper" / "planned_paper.tex", latex_from_markdown(paper_md), force)
    write_pdf(research_dir / "paper" / "planned_paper.pdf", title, force)
    write_yaml(research_dir / "paper" / "placeholder_map.yaml", {"placeholders": []}, force)
    write_text(
        research_dir / "paper" / "paper_gap_report.md",
        "# Paper Gap Report\n\n- [BLOCKED] Register missing claims, experiments, datasets, baselines, metrics, formulas, and tables here instead of inventing them.\n",
        force,
    )
    init_spec_scaffold(research_dir, force)
    for path in [
        research_dir / "plans" / ".gitkeep",
        research_dir / "ppt" / ".gitkeep",
        research_dir / "audits" / ".gitkeep",
    ]:
        write_text(path, "", force)
    return research_dir


def hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return "missing"
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def git_commit(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return "UNKNOWN"
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "UNKNOWN"


def collect_spec_ids(research_dir: Path) -> dict[str, set[str]]:
    ids = {"experiments": set(), "harnesses": set(), "tasks": set(), "gates": set()}
    exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    for experiment in as_list(exp_manifest.get("experiments")):
        if isinstance(experiment, dict) and experiment.get("experiment_id"):
            ids["experiments"].add(str(experiment["experiment_id"]))
    for graph_path in [
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_task_graph.yaml",
        research_dir / "spec" / "implementation" / "implementation_task_graph.yaml",
    ]:
        graph = load_yaml(graph_path)
        for task in as_list(graph.get("tasks")):
            if isinstance(task, dict) and task.get("task_id"):
                ids["tasks"].add(str(task["task_id"]))
        for gate in as_list(graph.get("gates")):
            if isinstance(gate, dict) and gate.get("gate_id"):
                ids["gates"].add(str(gate["gate_id"]))
    for harness_path in [
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_harness.yaml",
        research_dir / "spec" / "implementation" / "implementation_harness.yaml",
    ]:
        harness_doc = load_yaml(harness_path)
        for harness in as_list(harness_doc.get("harnesses")):
            if isinstance(harness, dict) and harness.get("harness_id"):
                ids["harnesses"].add(str(harness["harness_id"]))
    return ids


def latest_child(parent: Path) -> Path | None:
    children = sorted([path for path in parent.iterdir() if path.is_dir()]) if parent.exists() else []
    return children[-1] if children else None


def generate_plan(
    research_dir: Path,
    date: str,
    purpose: str,
    track: str,
    gate: str | None = None,
    target: str = "codex",
    force: bool = False,
) -> Path:
    plan_id = f"{date}-{slugify(purpose)}"
    plan_dir = research_dir / "plans" / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    ids = collect_spec_ids(research_dir)
    selected_gates = [gate] if gate else sorted(ids["gates"])
    harnesses = sorted(ids["harnesses"])
    repo = research_dir.parents[1] if research_dir.name == "research" and research_dir.parent.name == "docs" else research_dir.parent
    payload = {
        "plan_id": plan_id,
        "created_at": date,
        "purpose": purpose,
        "source_versions": {
            "prd_hash": hash_path(research_dir / "prd"),
            "paper_hash": hash_path(research_dir / "paper"),
            "spec_hash": hash_path(research_dir / "spec"),
            "git_commit": git_commit(repo),
        },
        "track": track,
        "target": target,
        "source_spec": [
            "docs/research/spec/reproduction/reproduction_manifest.yaml",
            "docs/research/spec/reproduction/reproduction_harness.yaml",
            "docs/research/spec/experiments/experiment_manifest.yaml",
            "docs/research/spec/experiments/experiment_harness.yaml",
        ],
        "allowed_scope": [
            f"docs/research/plans/{plan_id}/**",
            "artifacts/**",
            "scripts/reproduction/**" if track == "reproduction" else "src/**",
        ],
        "forbidden_actions": [
            "infer experiments from paper",
            "mock missing datasets, baselines, metrics, or results",
            "change core baseline algorithms silently",
            "write unvalidated empirical claims into paper",
        ],
        "gates": selected_gates,
        "harnesses": harnesses,
        "artifacts": ["artifacts/**"],
        "completion_condition": [
            "all selected gates pass or blockers are documented",
            "declared harness stdout/stderr is saved",
            "current_state.md, blocker_log.md, decision_log.md, run_log.md, and final_summary.md are updated",
        ],
    }
    write_yaml(plan_dir / "plan.yaml", payload, force)
    write_text(
        plan_dir / "plan.md",
        f"# {plan_id}\n\nPurpose: {purpose}\n\nTrack: {track}\n\nExecute the earliest incomplete gate from `docs/research/spec/`.\n",
        force,
    )
    write_text(
        plan_dir / "ai_loop_prompt.md",
        "\n".join(
            [
                f"# AI Loop Prompt: {plan_id}",
                "",
                "Executable source of truth is `docs/research/spec/`.",
                "PRD is the human research source of truth.",
                "Paper is the narrative target and placeholder map only.",
                "Do not infer experiments from paper.",
                "Always execute the earliest incomplete gate.",
                "Run declared harnesses and save stdout/stderr.",
                "Update current_state.md, blocker_log.md, decision_log.md, run_log.md, and final_summary.md.",
                "Do not mock missing datasets, baselines, metrics, or results.",
                "Stop and log a blocker when required information is missing.",
            ]
        )
        + "\n",
        force,
    )
    for name in ["current_state.md", "blocker_log.md", "decision_log.md", "run_log.md", "final_summary.md"]:
        write_text(plan_dir / name, f"# {name.removesuffix('.md').replace('_', ' ').title()}\n\n", force)
    return plan_dir


def generate_ppt(research_dir: Path, mode: str = "standard", force: bool = False) -> Path:
    deck_dir = research_dir / "ppt" / "main_deck"
    prompt_dir = deck_dir / "slide_prompts"
    (deck_dir / "pages").mkdir(parents=True, exist_ok=True)
    (deck_dir / "exports").mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    slides = STANDARD_SLIDES
    if mode == "short":
        slides = STANDARD_SLIDES[:6]
    elif mode == "long":
        slides = STANDARD_SLIDES + [
            ("S13", "13_ablation.png", "13_ablation.md", "Ablation plan", "Show planned ablations"),
            ("S14", "14_statistics.png", "14_statistics.md", "Statistical protocol", "Show seed and test protocol"),
            ("S15", "15_timeline.png", "15_timeline.md", "Execution timeline", "Show dated execution plan"),
        ]
    write_yaml(
        deck_dir / "deck_spec.yaml",
        {
            "deck_id": "main_deck",
            "mode": mode,
            "page_count_target": len(slides),
            "aspect_ratio": "16:9",
            "style": {
                "tone": "top-tier academic conference talk",
                "visual_style": "clean, modern, minimal, professional",
                "density": "medium",
                "figure_priority": "high",
            },
            "constraints": {
                "no_fake_results": True,
                "no_unbound_claims": True,
                "no_unregistered_experiments": True,
                "each_slide_one_takeaway": True,
                "no_pptx": True,
            },
        },
        force,
    )
    manifest = {
        "slides": [
            {
                "slide_id": slide_id,
                "filename": filename,
                "prompt": prompt,
                "title": title,
                "purpose": purpose,
                "source_sections": [{"prd": "Research PRD"}, {"paper": "planned paper"}],
                "required_elements": ["title", "figure_or_structure", "takeaway"],
                "takeaway": purpose,
            }
            for slide_id, filename, prompt, title, purpose in slides
        ]
    }
    write_yaml(deck_dir / "slide_manifest.yaml", manifest, force)
    for _, filename, prompt_name, title, purpose in slides:
        write_text(
            prompt_dir / prompt_name,
            "\n".join(
                [
                    "Generate a single 16:9 academic presentation slide as a polished PNG.",
                    "",
                    f"Slide title: \"{title}\"",
                    "",
                    "This slide should look like a top-tier conference talk slide: clean, professional, visually balanced, not crowded, white background, modern academic design, strong typography, and one clear takeaway.",
                    "",
                    "Content requirements:",
                    f"- Purpose: {purpose}.",
                    "- Use only content grounded in the Research PRD, planned paper, and spec.",
                    f"- Save the rendered page as `pages/{filename}`.",
                    "",
                    "Important constraints:",
                    "- Do not invent experiments or results.",
                    "- Do not create a .pptx file.",
                    "- Maintain the same visual language as the deck.",
                ]
            )
            + "\n",
            force,
        )
    write_text(deck_dir / "slide_notes.md", "# Slide Notes\n\n", force)
    write_text(deck_dir / "deck_gap_report.md", "# Deck Gap Report\n\n- No empirical result may appear without evidence or placeholder binding.\n", force)
    write_text(
        deck_dir / "render_plan.md",
        "\n".join(
            [
                "# Render Plan",
                "",
                "1. Read `deck_spec.yaml`.",
                "2. Read `slide_manifest.yaml`.",
                "3. For each slide, read prompt under `slide_prompts/`.",
                "4. Generate a PNG page at 16:9.",
                "5. Save into `pages/`.",
                "6. Verify all pages exist.",
                "7. Combine PNG pages into `exports/main_deck.pdf`.",
                "8. Do not invent content or empirical results.",
                "9. Do not create `.pptx` output.",
            ]
        )
        + "\n",
        force,
    )
    return deck_dir


def generate_audit(research_dir: Path, date: str, force: bool = False) -> Path:
    audit_dir = research_dir / "audits" / f"{date}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    matrix = {
        "schema_version": SCHEMA_VERSION,
        "dimensions": {
            key: {"status": "unchecked", "findings": []}
            for key in AUDIT_MATRIX_KEYS
        },
    }
    write_yaml(audit_dir / "alignment_matrix.yaml", matrix, force)
    write_yaml(audit_dir / "drift_findings.yaml", {"schema_version": SCHEMA_VERSION, "findings": []}, force)
    write_text(
        audit_dir / "audit_report.md",
        "# Research Audit Report\n\nThis audit checks PRD, Paper, Spec, Plans, PPT, and artifacts for alignment drift.\n",
        force,
    )
    write_text(
        audit_dir / "repair_plan.md",
        "# Repair Plan\n\n## Must fix before execution\n\n- Review alignment findings.\n\n## Recommended next research-plan target\n\n- TBD.\n",
        force,
    )
    return audit_dir


def generate_paper(research_dir: Path, force: bool = False) -> Path:
    exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    experiments = [item for item in as_list(exp_manifest.get("experiments")) if isinstance(item, dict)]
    placeholders = []
    lines = [
        "# Planned Research Paper",
        "",
        "## Abstract",
        "We propose the method and define an execution-bound evaluation protocol. Unobserved empirical values remain placeholders.",
        "",
        "## Introduction",
        "We formulate the problem and motivate the declared research questions.",
        "",
        "## Method",
        "We design the method described in the Research PRD.",
        "",
        "## Evaluation",
    ]
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id", "")).strip()
        if not experiment_id:
            continue
        placeholder = f"{{{{{experiment_id}.OURS.primary_metric}}}}"
        lines.append(f"Experiment {experiment_id} tests the declared hypothesis. Table 1 reports {placeholder} after execution.")
        placeholders.append(
            {
                "placeholder": placeholder,
                "experiment_id": experiment_id,
                "method_id": "OURS",
                "metric": "primary_metric",
                "source_after_execution": f"artifacts/experiments/{experiment_id}/aggregate/summary.json",
                "paper_location": "Table 1 / Main Results",
            }
        )
    if not placeholders:
        lines.append("No experiment-bound result placeholders are available yet.")
    paper = "\n".join(lines) + "\n"
    write_text(research_dir / "paper" / "planned_paper.md", paper, force)
    write_text(research_dir / "paper" / "planned_paper.tex", latex_from_markdown(paper), force)
    write_yaml(research_dir / "paper" / "placeholder_map.yaml", {"placeholders": placeholders}, force)
    write_text(research_dir / "paper" / "paper_gap_report.md", "# Paper Gap Report\n\n- Record missing claims or experiments here.\n", force)
    write_pdf(research_dir / "paper" / "planned_paper.pdf", "Planned Research Paper", force)
    return research_dir / "paper"


class Validation:
    def __init__(self) -> None:
        self.issues: list[str] = []

    @property
    def ok(self) -> bool:
        return not self.issues

    def error(self, message: str) -> None:
        self.issues.append(message)

    def require_file(self, path: Path, label: str) -> bool:
        if not path.exists():
            self.error(f"missing {label}: {path.as_posix()}")
            return False
        return True


def validate_prd(research_dir: Path) -> Validation:
    validation = Validation()
    prd = research_dir / "prd" / "research_prd.md"
    if not validation.require_file(prd, "Research PRD"):
        return validation
    text = read_text(prd)
    for section in PRD_SECTIONS:
        if section not in text:
            validation.error(f"missing PRD section: {section}")
    if "Reader Model and Usage" in text:
        validation.error("PRD must not expose a Reader Model and Usage section")
    return validation


def collect_placeholders(text: str) -> set[str]:
    return {match.group(0) for match in re.finditer(r"\{\{[^{}]+\}\}", text)}


def placeholder_experiment_id(placeholder: str) -> str:
    return placeholder.strip("{} ").split(".", 1)[0]


def spec_experiment_ids(research_dir: Path) -> set[str]:
    manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    ids = set()
    for experiment in as_list(manifest.get("experiments")):
        if isinstance(experiment, dict) and experiment.get("experiment_id"):
            ids.add(str(experiment["experiment_id"]))
    return ids


def validate_paper(research_dir: Path) -> Validation:
    validation = Validation()
    paper_paths = [research_dir / "paper" / "planned_paper.md", research_dir / "paper" / "planned_paper.tex"]
    if not validation.require_file(paper_paths[0], "planned paper markdown"):
        return validation
    text = "\n".join(read_text(path) for path in paper_paths if path.exists())
    lower_text = text.lower()
    for phrase in FORBIDDEN_RESULT_PHRASES:
        if phrase in lower_text:
            validation.error(f"unvalidated empirical result language: `{phrase}`")
    map_path = research_dir / "paper" / "placeholder_map.yaml"
    if not validation.require_file(map_path, "placeholder_map.yaml"):
        return validation
    mapping = load_yaml(map_path)
    entries = [item for item in as_list(mapping.get("placeholders")) if isinstance(item, dict)]
    registered = {str(item.get("placeholder", "")).strip() for item in entries if item.get("placeholder")}
    for placeholder in collect_placeholders(text):
        if placeholder not in registered:
            validation.error(f"unregistered placeholder: {placeholder}")
    experiment_ids = spec_experiment_ids(research_dir)
    for entry in entries:
        placeholder = str(entry.get("placeholder", "")).strip()
        experiment_id = str(entry.get("experiment_id", "")).strip() or placeholder_experiment_id(placeholder)
        if placeholder and placeholder not in collect_placeholders(text):
            validation.error(f"placeholder registered but unused in paper: {placeholder}")
        if experiment_ids and experiment_id not in experiment_ids:
            validation.error(f"placeholder maps to unknown spec experiment: {placeholder} -> {experiment_id}")
    return validation


def has_command_or_blocker(harness: dict[str, Any]) -> bool:
    command = harness.get("command")
    blocker = harness.get("blocker") or harness.get("explicit_blocker")
    if isinstance(command, str) and command.strip():
        return True
    if isinstance(command, list) and any(str(item).strip() for item in command):
        return True
    if isinstance(blocker, str) and blocker.strip():
        return True
    if isinstance(blocker, dict) and blocker:
        return True
    return False


def validate_task_graph(
    research_dir: Path,
    graph_path: Path,
    harness_path: Path,
    validation: Validation,
    required: bool = True,
) -> None:
    if required:
        validation.require_file(graph_path, "task graph")
        validation.require_file(harness_path, "harness manifest")
    graph = load_yaml(graph_path)
    harness_doc = load_yaml(harness_path)
    tasks = [item for item in as_list(graph.get("tasks")) if isinstance(item, dict)]
    gates = [item for item in as_list(graph.get("gates")) if isinstance(item, dict)]
    harnesses = [item for item in as_list(harness_doc.get("harnesses")) if isinstance(item, dict)]
    harness_ids = {str(item.get("harness_id")) for item in harnesses if item.get("harness_id")}
    task_ids = {str(item.get("task_id")) for item in tasks if item.get("task_id")}
    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        for harness_id in [str(item).strip() for item in as_list(task.get("harnesses")) if str(item).strip()]:
            if harness_id not in harness_ids:
                validation.error(f"task {task_id} references missing harness {harness_id}")
        if not as_list(task.get("harnesses")):
            validation.error(f"task {task_id} has no harness")
    for gate in gates:
        gate_id = str(gate.get("gate_id", "")).strip()
        for task_id in [str(item).strip() for item in as_list(gate.get("tasks")) if str(item).strip()]:
            if task_id not in task_ids:
                validation.error(f"gate {gate_id} references missing task {task_id}")
    for harness in harnesses:
        harness_id = str(harness.get("harness_id", "")).strip()
        if not has_command_or_blocker(harness):
            validation.error(f"harness {harness_id} has no command or explicit blocker")
        if harness.get("type") == "full_experiment":
            if harness.get("independent_rerun_required") is not True:
                validation.error(f"full experiment harness {harness_id} must require independent rerun")
            pass_criteria = {str(item) for item in as_list(harness.get("pass_criteria"))}
            required_criteria = {
                "all_declared_seeds_completed",
                "all_declared_baselines_completed",
                "no_mock_data_used",
                "no_missing_metric",
                "no_test_tuning",
                "artifact_hashes_recorded",
            }
            missing = sorted(required_criteria - pass_criteria)
            if missing:
                validation.error(f"full experiment harness {harness_id} missing pass criteria: {', '.join(missing)}")
            if harness.get("may_support_research_claim") and "no_mock_data_used" not in pass_criteria:
                validation.error(f"full experiment harness {harness_id} allows mock evidence for research claim")


def validate_spec(research_dir: Path) -> Validation:
    validation = Validation()
    for relative_path in SPEC_FILES:
        validation.require_file(research_dir / "spec" / relative_path, f"spec/{relative_path}")
    global_spec = load_yaml(research_dir / "spec" / "global_spec.yaml")
    if not as_list(global_spec.get("rq_chain")):
        validation.error("global_spec.yaml has no RQ -> Hypothesis -> Claim -> Experiment chain")

    exp_manifest = load_yaml(research_dir / "spec" / "experiments" / "experiment_manifest.yaml")
    experiments = [item for item in as_list(exp_manifest.get("experiments")) if isinstance(item, dict)]
    if not experiments:
        validation.error("experiment_manifest.yaml has no experiments")
    required_exp_fields = [
        "experiment_id",
        "title",
        "linked_rq",
        "hypothesis",
        "claim",
        "purpose",
        "status",
        "dataset",
        "split_file",
        "preprocessing_config",
        "models",
        "proposed_method_config",
        "baselines",
        "seeds",
        "metrics",
        "statistical_protocol",
        "commands",
        "required_artifacts",
        "harnesses",
        "support_condition",
        "falsification_condition",
        "mock_policy",
    ]
    experiment_harnesses = {
        str(item.get("harness_id"))
        for item in as_list(load_yaml(research_dir / "spec" / "experiments" / "experiment_harness.yaml").get("harnesses"))
        if isinstance(item, dict) and item.get("harness_id")
    }
    for experiment in experiments:
        experiment_id = str(experiment.get("experiment_id", "")).strip() or "<missing>"
        for field in required_exp_fields:
            if not experiment.get(field):
                validation.error(f"experiment {experiment_id} missing {field}")
        for harness_id in [str(item).strip() for item in as_list(experiment.get("harnesses")) if str(item).strip()]:
            if harness_id not in experiment_harnesses:
                validation.error(f"experiment {experiment_id} references missing harness {harness_id}")

    validate_task_graph(
        research_dir,
        research_dir / "spec" / "experiments" / "experiment_task_graph.yaml",
        research_dir / "spec" / "experiments" / "experiment_harness.yaml",
        validation,
    )
    validate_task_graph(
        research_dir,
        research_dir / "spec" / "reproduction" / "reproduction_task_graph.yaml",
        research_dir / "spec" / "reproduction" / "reproduction_harness.yaml",
        validation,
        required=False,
    )
    validate_task_graph(
        research_dir,
        research_dir / "spec" / "implementation" / "implementation_task_graph.yaml",
        research_dir / "spec" / "implementation" / "implementation_harness.yaml",
        validation,
        required=False,
    )

    reproduction_manifest = load_yaml(research_dir / "spec" / "reproduction" / "reproduction_manifest.yaml")
    for target in as_list(reproduction_manifest.get("reproduction_targets")):
        if not isinstance(target, dict):
            continue
        reproduction_id = str(target.get("reproduction_id", "")).strip() or "<missing>"
        mode = str(target.get("reproduction_mode", "")).strip()
        if mode not in REPRODUCTION_MODES:
            validation.error(f"reproduction target {reproduction_id} has invalid reproduction_mode {mode}")
        if mode == "paper_based_reimplementation" and "paper_based_reimplementation" not in target:
            validation.error(f"paper-based reproduction {reproduction_id} missing paper_based_reimplementation detail")

    evidence_contract = load_yaml(research_dir / "spec" / "shared" / "evidence_contract.yaml")
    if not evidence_contract.get("claims") and not evidence_contract.get("evidence_rules"):
        validation.error("evidence_contract.yaml has no claim contract or evidence rules")
    return validation


def validate_plan(research_dir: Path) -> Validation:
    validation = Validation()
    plans_dir = research_dir / "plans"
    plan_dirs = sorted(path for path in plans_dir.iterdir() if path.is_dir()) if plans_dir.exists() else []
    if not plan_dirs:
        validation.error("no dated research plan exists")
        return validation
    ids = collect_spec_ids(research_dir)
    current_spec_hash = hash_path(research_dir / "spec")
    for plan_dir in plan_dirs:
        plan_yaml = plan_dir / "plan.yaml"
        if not validation.require_file(plan_yaml, "plan.yaml"):
            continue
        payload = load_yaml(plan_yaml)
        versions = payload.get("source_versions", {}) if isinstance(payload.get("source_versions"), dict) else {}
        if not versions.get("spec_hash"):
            validation.error(f"plan {plan_dir.name} missing source_versions.spec_hash")
        elif versions.get("spec_hash") != current_spec_hash:
            validation.error(f"plan {plan_dir.name} has stale spec hash")
        if not versions.get("prd_hash") or not versions.get("paper_hash") or not versions.get("git_commit"):
            validation.error(f"plan {plan_dir.name} missing PRD/paper/git source hash")
        for key in ["allowed_scope", "forbidden_actions", "gates", "harnesses", "artifacts", "completion_condition"]:
            if not as_list(payload.get(key)):
                validation.error(f"plan {plan_dir.name} missing {key}")
        for gate_id in [str(item).strip() for item in as_list(payload.get("gates")) if str(item).strip()]:
            if gate_id not in ids["gates"]:
                validation.error(f"plan {plan_dir.name} references missing spec gate {gate_id}")
        for harness_id in [str(item).strip() for item in as_list(payload.get("harnesses")) if str(item).strip()]:
            if harness_id not in ids["harnesses"]:
                validation.error(f"plan {plan_dir.name} references missing spec harness {harness_id}")
        for name in ["ai_loop_prompt.md", "current_state.md", "blocker_log.md", "decision_log.md", "run_log.md", "final_summary.md"]:
            validation.require_file(plan_dir / name, f"plan {plan_dir.name}/{name}")
    return validation


def validate_ppt(research_dir: Path) -> Validation:
    validation = Validation()
    deck_dir = research_dir / "ppt" / "main_deck"
    for name in ["deck_spec.yaml", "slide_manifest.yaml", "render_plan.md", "slide_notes.md", "deck_gap_report.md"]:
        validation.require_file(deck_dir / name, name)
    if list(deck_dir.rglob("*.pptx")):
        validation.error("ppt-ready forbids .pptx output")
    manifest = load_yaml(deck_dir / "slide_manifest.yaml")
    experiment_ids = spec_experiment_ids(research_dir)
    for slide in as_list(manifest.get("slides")):
        if not isinstance(slide, dict):
            continue
        prompt_name = str(slide.get("prompt") or "").strip()
        slide_id = str(slide.get("slide_id") or "").strip()
        if not prompt_name:
            validation.error(f"slide {slide_id} missing prompt field")
            continue
        prompt_path = deck_dir / "slide_prompts" / prompt_name
        if not prompt_path.exists():
            validation.error(f"missing slide prompt: {prompt_name}")
            continue
        prompt_text = read_text(prompt_path)
        for phrase in FORBIDDEN_RESULT_PHRASES:
            if phrase in prompt_text.lower():
                validation.error(f"slide prompt {prompt_name} has fake empirical result phrase: {phrase}")
        for experiment_id in re.findall(r"\bE\d+\b", prompt_text):
            if experiment_ids and experiment_id not in experiment_ids:
                validation.error(f"slide prompt {prompt_name} references unregistered experiment {experiment_id}")
    return validation


def validate_audit(research_dir: Path) -> Validation:
    validation = Validation()
    audit_dir = latest_child(research_dir / "audits")
    if audit_dir is None:
        validation.error("no dated research audit exists")
        return validation
    for name in ["audit_report.md", "alignment_matrix.yaml", "drift_findings.yaml", "repair_plan.md"]:
        validation.require_file(audit_dir / name, name)
    matrix = load_yaml(audit_dir / "alignment_matrix.yaml")
    dimensions = matrix.get("dimensions", {}) if isinstance(matrix.get("dimensions"), dict) else {}
    for key in AUDIT_MATRIX_KEYS:
        if key not in dimensions:
            validation.error(f"alignment matrix missing dimension: {key}")
    return validation


def validate_alignment(research_dir: Path) -> Validation:
    validation = Validation()
    for child_validation in [validate_prd(research_dir), validate_paper(research_dir), validate_spec(research_dir), validate_ppt(research_dir)]:
        validation.issues.extend(child_validation.issues)
    return validation


def validate_research(research_dir: Path, mode: str) -> Validation:
    validators = {
        "prd-ready": validate_prd,
        "paper-ready": validate_paper,
        "spec-ready": validate_spec,
        "plan-ready": validate_plan,
        "ppt-ready": validate_ppt,
        "audit-ready": validate_audit,
        "alignment-check": validate_alignment,
    }
    if mode not in validators:
        raise ValueError(f"unknown validation mode: {mode}")
    return validators[mode](research_dir)


def print_validation(validation: Validation, mode: str, research_dir: Path) -> int:
    if validation.ok:
        print(f"[OK] {mode}: {research_dir}")
        return 0
    for issue in validation.issues:
        print(f"[ERROR] {issue}")
    print(f"[BLOCKED] {mode}: {research_dir}")
    return 1


def resolve_research_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "research_dir", ""):
        return Path(args.research_dir).resolve()
    repo = Path(getattr(args, "repo", ".")).resolve()
    return (repo / DEFAULT_RESEARCH_DIR).resolve()
