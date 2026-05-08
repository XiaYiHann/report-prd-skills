---
name: report
description: "Use when the user wants a durable PRD-based single-source report under docs/report. Routes to initialization, brainstorming, update, audit, goal, or paper workflows. The report family supports research-prd and engineering-prd sources, rendered to both report.pdf and report.md."
---

# Report

## Overview

Use this skill as the routing entry for the `report` family.

The family maintains one durable LaTeX source workspace under `docs/report/<slug>/` and two rendered artifacts: `docs/report/report.pdf` and `docs/report/report.md`. Both artifacts are generated from the LaTeX source; neither artifact is the editable source of truth.

The workspace also owns execution manifests: `report.manifest.yaml`, `tasks/task_graph.yaml`, `harness/harness.yaml`, `evidence/evidence_manifest.yaml`, and for `research-prd`, `experiments/experiment_manifest.yaml`. These manifests are the machine contract for `report-goal`.

The report family is now PRD-first. All new reports must be one of:

- `research-prd`: top-tier research program PRD with falsifiable hypotheses, evidence ledger, baselines, ablations, reproducibility, failure cases, risks, ethics, and Go / No-Go gates.
- `engineering-prd`: top-tier engineering PRD with Goals & Non-Goals, modular requirements, Acceptance Criteria, interfaces, NFRs, testing, release gates, roadmap, and operational readiness.

Legacy structures such as `research`, `project`, `hybrid`, `teaching`, and `executor-handbook` are no longer valid initialization targets.

## Routing Rules

Route to the narrowest matching skill:

- `report-init`: create a fixed semi-empty `research-prd` or `engineering-prd` LaTeX workspace and render `report.pdf` plus `report.md`.
- `report-brainstorming`: discuss, compare, clarify, and structure a PRD before write-back.
- `report-update`: write confirmed conclusions into the PRD, re-render `report.pdf` plus `report.md`, and run consistency checks. Use deep-spec mode for execution manifest write-back.
- `report-audit`: review PRD structure, evidence boundaries, acceptance gates, readability, dual-artifact freshness, release readiness, and execution-readiness.
- `report-goal`: generate a manifest-gated execution prompt; missing or invalid manifests produce a repair goal, not an implementation goal.
- `report-paper`: derive a top-tier computer-science conference paper from the report, manifests, and evidence ledger. This is the only paper-specific report skill.

Stay in this routing skill only when the user's intent is still ambiguous.

## Shared Contract

- Maintain LaTeX as the single source of truth.
- Treat `report.pdf` and `report.md` as sibling rendered artifacts derived by `render_report.py`.
- Keep brainstorming and write-back separate.
- Keep prose report and execution manifests synchronized when deep-spec mode is active.
- New initialization must choose `research-prd` or `engineering-prd`.
- Current implementation state, milestones, blockers, and run status belong in `项目进度`.
- Keep `source claim`, `design intent`, `repo-observed fact`, and `report synthesis` distinct.
- Use formal Chinese written language: rigorous, clear, beginner-aware, and information-dense.
- Every chapter should begin with a conclusion sentence.
- Every major chapter should include at least one figure or table.
- Use `总览图 -> 细节图` as the default visual progression.
- Use TikZ / PGFPlots for final figures unless the workspace has a verified Mermaid render path.
- If a change is high-disagreement or under-argued, use `report-audit` with multi-agent audit mode before write-back.
- After every meaningful render, inspect XeLaTeX warnings, self-check output, and Markdown export freshness before release.

## PRD Hard Gates

For `research-prd`, the report must visibly include:

- Research Questions and falsifiable hypotheses.
- Evidence Ledger: `claim -> evidence -> source -> limitation -> confidence`.
- Baseline Matrix, Ablation Matrix, Reproducibility Table, and Failure-case Table.
- Risks, ethics, and Go / No-Go gates.
- Clear separation between planned evidence and observed evidence.

For `engineering-prd`, the report must visibly include:

- Goals & Non-Goals.
- Modular functional requirements with Acceptance Criteria.
- Priorities and dependencies.
- NFR matrix.
- Interface/data contracts and error semantics.
- Testing / acceptance / release plan.
- Operational Readiness Matrix.
- Phased MVP roadmap.

## Interaction Contract

Use defaults only for mechanical setup. Ask before deciding:

- whether the target is `research-prd` or `engineering-prd` when the prompt is ambiguous.
- primary audience and explanation depth.
- major chapter restructuring.
- whether a statement is design intent or repo-observed fact.
- whether repo status may appear outside `项目进度`.
- whether a disputed claim needs multi-agent audit before write-back.
- how to change layout/content if needed to clear compile warnings.

Read `report/_shared/references/decision-gates.md` when a branch choice may affect report direction.

## Family Layout

Shared resources live under the main report skill:

- `report/_shared/scripts/init_report.py`
- `report/_shared/scripts/render_report.py`
- `report/_shared/scripts/self_check_report.py`
- `report/_shared/scripts/scan_repo.py`
- `report/_shared/scripts/accept_edits.py`
- `report/_shared/references/report-structures.md`
- `report/_shared/references/research-prd-template.md`
- `report/_shared/references/engineering-prd-template.md`
- `report/_shared/references/research-evidence-checklist.md`
- `report/_shared/references/operational-readiness-checklist.md`
- `report/_shared/references/reuse-websearch-playbook.md`
- `report/_shared/references/diagram-guide.md`
- `report/_shared/references/anti-patterns.md`
- `report/_shared/references/progress-chapter-policy.md`

Read shared references only when needed.

## Quick Decision Tree

- “科研 PRD / 研究计划 / grant / 论文方法计划” -> `report-init --type research-prd`
- “工程 PRD / 产品需求 / 系统设计 / vibe-coding / Agent 可执行项目文档” -> `report-init --type engineering-prd`
- “先讨论方向，不写回” -> `report-brainstorming`
- “把确认内容写回 report” -> `report-update`
- “审计是否可交付” -> `report-audit`
- “生成执行 goal / Claude 或 Codex 自动执行 / harness / evidence ledger” -> `report-goal`
- “生成论文 / 顶会论文 / NeurIPS / ICLR / AAAI / paper draft” -> `report-paper`
- “某个 claim / 设计路线需要正反裁决 / 多视角审查” -> `report-audit`

## When Not To Stay Here

Do not keep working in this routing skill when a narrower skill clearly fits.

Only edit this `report` skill family itself when the user explicitly asks to improve the skills.
