---
name: research-explore
description: "Use when discussing research ideas, literature, baselines, novelty, failure analysis, paper shape, or next-version framing without executing tasks."
---

# Research Explore

## Purpose

`research-explore` is the pure exploration layer for the Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop.

It supports research-direction discussion, literature exploration, hypothesis critique, baseline challenge, novelty screening, failure interpretation, paper-shape discussion, and next-version seed generation.

It is not an execution skill, PRD authority, Spec authority, Plan authority, or Paper Binding authority.

## Read Order

Every `/research explore` run first reads:

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/PRD.md`
5. `docs/research/{CURRENT}/SPEC.yaml`
6. `docs/research/{CURRENT}/wiki/epoch_summary.md`
7. `docs/research/{CURRENT}/wiki/evidence_map.md`
8. `docs/research/{CURRENT}/wiki/positive_signals.md`
9. `docs/research/{CURRENT}/wiki/negative_results.md`
10. `docs/research/{CURRENT}/wiki/open_questions.md`
11. `docs/research/{CURRENT}/wiki/next_version_seed.md`
12. `docs/research/{CURRENT}/closeout.md`

Old versions are context only. Read only `closeout.md`, `wiki/epoch_summary.md`, `wiki/evidence_map.md`, and `wiki/next_version_seed.md`.

## Commands

Conceptual command forms:

```text
/research explore
/research explore --save
/research explore --mode idea
/research explore --mode literature
/research explore --mode baseline
/research explore --mode next-version
/research explore --mode paper-shape
/research explore --mode failure-analysis
```

## Modes

`mode=idea` outputs:
- idea risks
- minimal falsifiable question
- possible V0 framing
- required literature search
- possible baseline
- stop conditions

`mode=literature` outputs:
- literature findings
- related work map
- novelty risk
- must-compare baselines
- literature blocker when web access is unavailable

`mode=baseline` outputs:
- missing baseline
- unfair baseline
- strongest baseline
- appendix baseline
- reviewer objection

`mode=next-version` outputs:
- keep
- drop
- new core question
- minimal next experiments
- next stop conditions
- out-of-scope risk

`mode=paper-shape` outputs:
- method paper
- mechanism paper
- diagnostic paper
- negative result paper
- benchmark/tooling paper

`mode=failure-analysis` outputs:
- execution bug
- spec gap
- metric mismatch
- research falsification
- pivot needed

## Save Targets

Saved exploration goes under:

```text
docs/research/explore/sessions/EXP_0001.md
docs/research/explore/syntheses/EXP_SYNTHESIS.md
docs/research/explore/proposals/DIRECTION_UPDATE_PROPOSAL.md
docs/research/explore/proposals/NEXT_VERSION_PROPOSAL.md
docs/research/explore/proposals/BASELINE_UPDATE_PROPOSAL.md
docs/research/explore/proposals/LITERATURE_BLOCKER.md
```

Explore can propose save targets such as:

- `Vn/wiki/literature_notes.md`
- `Vn/wiki/baseline_landscape.md`
- `Vn/wiki/open_questions.md`
- `Vn/wiki/next_version_seed.md`

It must not write them directly unless the user explicitly asks for a save/update action.

## Web Search Policy

Use web search when the task involves:

- new direction / new idea
- literature review
- baseline lock
- novelty claim
- related work
- before paper binding
- user explicitly asks whether similar work exists
- uncertain new term, paper, repo, author, model, or method

Do not web search for:

- code bug fixes
- task queue writing
- next action updates
- format migration audit
- pure wiki cleanup

If web access is unavailable, write `docs/research/explore/proposals/LITERATURE_BLOCKER.md`. Do not fabricate citations, benchmark facts, or related work.

## Hard Boundaries

Explore can suggest; it cannot execute. "Execute" here means experiment execution (running code, generating data, modifying `STATUS.yaml` or `RESEARCH_DIRECTION.md`). Document expression (writing proposals, saving EXP sessions) is not execution and is allowed.

It must not:

- modify `RESEARCH_DIRECTION.md`
- modify `Vn/PRD.md`, `Vn/SPEC.yaml`, or `Vn/PLAN.md`
- create `Vn+1`
- enter Paper Binding
- claim a result is stable
- turn exploratory insight into paper result
- fabricate literature, experiments, artifacts, stdout/stderr, benchmark numbers, or hashes

## Active Recommendation Rule

If exploration produces a finding with `update_wiki` or `add_task_candidate` level value for the current epoch, the agent must end the response with an explicit save proposal naming the target wiki file (e.g., `Vn/wiki/open_questions.md`) and wait for user confirmation. Do not remain silent and do not write without approval.

Explore 不执行，Git 不解释，Wiki 不证明，Audit 不发明，Paper 不反推。
