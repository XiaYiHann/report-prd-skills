---
name: research-insight
description: "Use when completed runs, blockers, anomalies, negative results, or saved exploration sessions need evidence-grounded interpretation into the current epoch wiki or legacy insight logs. Also use when the user requests interpretation, analysis, or summary of any executed task evidence."
---

# Research Insight

## Purpose

`research-insight` is the explicit interpretation layer for the research loop. It turns executed task evidence, blockers, negative results, and saved exploration sessions into bounded, evidence-grounded insight records.

It is not an execution skill (neither experiment execution nor document expression), PRD authority, Spec authority, Audit authority, or Paper Binding authority.

## Skill Invocation Contract

Conceptual command forms:

```text
/research insight
/research insight --promote <explore_session_id>
/research insight --gate <gate_id>
```

`/research insight` is invoked through the `research` controller. It does not run as a top-level skill outside the research loop.

## Use When

- An active task has completed and the run report asks whether wiki should be updated.
- A gate passed, failed, or became `gate_blocked`.
- A negative result, anomaly, failed path, or surprising simplification appears.
- A saved `/research explore` session should be promoted into wiki candidates.
- Closeout preparation needs consolidated `positive_signals`, `negative_results`, `failed_paths`, `evidence_map`, or `next_version_seed`.

Do not use it for code execution, broad replanning, PRD rewriting, Paper Binding, or literature search that has not been explicitly requested.

## Read Order

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/PRD.md`
5. `docs/research/{CURRENT}/SPEC.yaml`
6. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
7. `docs/research/{CURRENT}/LOOP_LOG.md`
8. `docs/research/{CURRENT}/runs/`
9. `docs/research/{CURRENT}/artifacts/`
10. `docs/research/{CURRENT}/wiki/*`
11. `docs/research/explore/sessions/` only when promoting saved exploration

Old versions are context only. Read old `closeout.md`, `wiki/epoch_summary.md`, `wiki/evidence_map.md`, and `wiki/next_version_seed.md`; do not let old PRDs override the current epoch.

## Primary Outputs

Epoch wiki is the current source for durable insight:

- `docs/research/{CURRENT}/wiki/epoch_summary.md`
- `docs/research/{CURRENT}/wiki/evidence_map.md`
- `docs/research/{CURRENT}/wiki/positive_signals.md`
- `docs/research/{CURRENT}/wiki/negative_results.md`
- `docs/research/{CURRENT}/wiki/failed_paths.md`
- `docs/research/{CURRENT}/wiki/baseline_landscape.md`
- `docs/research/{CURRENT}/wiki/literature_notes.md`
- `docs/research/{CURRENT}/wiki/open_questions.md`
- `docs/research/{CURRENT}/wiki/next_version_seed.md`

Legacy `docs/research/insights/insight_log.md` is compatibility storage only. Write it only when `CURRENT` is absent, the user explicitly requests legacy mode, or migration requires preserving old material.

## Interpretation Contract

Every insight entry must separate:

- `fact`: what command, run, artifact, blocker, or source actually exists.
- `artifact`: concrete paths, metrics, logs, stdout/stderr, or saved explore sessions.
- `interpretation`: what the evidence suggests inside the current PRD/SPEC boundary.
- `speculation`: plausible but unverified explanation.

Every promoted insight must include:

- source task or explore session
- source run or blocker
- source artifact path, or explicit `none`
- evidence level: `exploratory`, `diagnostic`, `confirmatory`, `reproduced`, or `paper_admissible`
- effect on current epoch: `no_change`, `update_wiki`, `add_task_candidate`, `closeout_consideration`, `next_version_seed_candidate`, or `out_of_scope_escalation`
- recommended next action

## Promotion Rules

- Positive signal → `positive_signals.md` and usually `evidence_map.md`.
- Negative result → `negative_results.md`, `evidence_map.md`, and possibly `open_questions.md`.
- Repeated failed path → `failed_paths.md`.
- Baseline or novelty implication → `baseline_landscape.md` and `literature_notes.md`.
- Future framing implication → `next_version_seed.md`.
- Out-of-scope implication → write an escalation recommendation; do not update PRD or create a new version.

## Hard Boundaries

- Do not modify `RESEARCH_DIRECTION.md`.
- Do not modify PRD core claims.
- Do not create `Vn+1`.
- Do not enter Paper Binding.
- Do not claim an exploratory observation is stable.
- Do not invent experiments, artifacts, stdout/stderr, citations, benchmark values, hashes, or Git commits.
- Do not use prompt-only scaffold as result evidence.
- Do not promote legacy insight to current claim evidence unless current `PRD.md` or `SPEC.yaml` explicitly carries it forward.

Insight explains evidence. It does not create evidence.
