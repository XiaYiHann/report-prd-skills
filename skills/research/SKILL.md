---
name: research
description: "Use when a research workspace under docs/research needs the default autonomous controller across PRD, Spec, Plan, execution, audit, insight feedback, or paper stages, and no sub-mode (explore, insight, or audit) is explicitly invoked."
---

# research

## Purpose

`research` is the unified epoch contract controller for Codex / Claude Code agent executors.

It inspects `docs/research/`, resolves the current epoch from `CURRENT`, and owns the bounded research lifecycle through Direction, PRD, internal Spec compilation, internal Plan compilation, Task Queue, Next Action, execution, gate, insight interpretation, wiki, closeout, paper draft, and paper binding. It does not provide an independent resident backend; Codex / Claude Code execute `TASK_QUEUE.yaml` active task as the agent executor and must submit structured evidence with `update_state.py`.

新版系统是 **Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop**：

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

## Core hierarchy

`RESEARCH_DIRECTION.md` constrains exploration.  
`CURRENT` resolves the active epoch.  
`Vn/goal.md` and `Vn/GOAL_LOCK.yaml` define the current long-running execution objective and its source hashes.
`Vn/PRD.tex` defines the current research truth; `Vn/PRD.pdf` is the review artifact and `Vn/PRD_SUMMARY.md` is agent context only.
`Vn/RESEARCH_SPINE.yaml` binds the evidence chain (RQ -> Claim -> Experiment -> Evidence -> Figure/Table -> Paper Section).  
`Vn/rqs/RQxx/SPEC.yaml` constrains RQ-local execution.
`Vn/rqs/RQxx/PLAN.md` schedules RQ-local evidence generation.
`Vn/rqs/RQxx/INSIGHT_REVIEW.yaml` records the AI draft and the human verdict; only human-reviewed insights can become durable wiki knowledge.
`Vn/reproduction/REPRODUCTION_LEDGER.yaml` records reusable reproduction assets, compatibility audits, delta checks, and borrowed experiment designs across RQs.
`Vn/TASK_QUEUE.yaml` defines available work.  
The active task from `Vn/TASK_QUEUE.yaml` defines the current loop task.  
`Vn/GIT_STATE.yaml` records Git checkpoints.  
`docs/research/explore/` records pure exploration sessions.  
Runs and artifacts provide evidence.  
Wiki records only human-reviewed durable insight, with `Vn/wiki/frontier_map.yaml` as the version-to-version synthesis source for next RQ proposals.  
Closeout controls next version or Paper Binding.

Authority chain:

```text
RESEARCH_DIRECTION.md (研究走廊边界，所有 RQ 必须落在其范围内)
  -> CURRENT
  -> Vn/goal.md
  -> Vn/GOAL_LOCK.yaml
  -> Vn/PRD.tex
    -> Vn/RESEARCH_SPINE.yaml (RQ 必须绑定 direction_ref 到 RESEARCH_DIRECTION.md)
      -> Vn/rqs/RQxx/SPEC.yaml
      -> Vn/rqs/RQxx/PLAN.md
      -> Vn/rqs/RQxx/TASKS.yaml
      -> Vn/TASK_QUEUE.yaml
      -> Vn/runs + Vn/artifacts
      -> Vn/audits
      -> research-insight
      -> Vn/wiki
  -> Vn/closeout.md
  -> Vn+1/PRD.tex 或 paper binding
```

Every `/research` run must first read:

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/goal.md`
5. `docs/research/{CURRENT}/GOAL_LOCK.yaml`
6. `docs/research/{CURRENT}/RESEARCH_SPINE.yaml`
7. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
8. `docs/research/{CURRENT}/PRD.tex`
9. `docs/research/{CURRENT}/PRD_SUMMARY.md`
10. `docs/research/{CURRENT}/BASELINE_LOCK.yaml`
11. `docs/research/{CURRENT}/EVIDENCE_GATE.yaml`
12. `docs/research/{CURRENT}/rqs/RQxx/SPEC.yaml`
13. `docs/research/{CURRENT}/rqs/RQxx/PLAN.md`
14. `docs/research/{CURRENT}/rqs/RQxx/TASKS.yaml`
15. `docs/research/{CURRENT}/rqs/RQxx/INSIGHT_REVIEW.yaml`
16. `docs/research/{CURRENT}/reproduction/REPRODUCTION_LEDGER.yaml`
17. `docs/research/{CURRENT}/wiki/frontier_map.yaml`

**File-level distinction**:
- `goal.md` is the **version-level** anchor. It defines the overall mission, global constraints, and success criteria for the entire `Vn`. It changes only when the version's core question or scope shifts.
- `GOAL_LOCK.yaml` records the source hashes behind `goal.md`; refresh the goal when `goal-ready` reports a stale lock.
- `PRD.tex` is the research hypothesis source of truth.
- `PRD_SUMMARY.md` is not a source of truth and cannot define experiments.
- `rqs/RQxx/PLAN.md` is the concrete RQ schedule derived from `rqs/RQxx/SPEC.yaml`; `PLAN.md` is the epoch orchestration summary.
- `rqs/RQxx/INSIGHT_REVIEW.yaml` is the human insight gate: AI may draft, but the human verdict controls wiki binding and paper eligibility.
- `reproduction/REPRODUCTION_LEDGER.yaml` is the reuse ledger for prior-work reproductions; each RQ must pass a coverage check, but compatible reproduction assets may be reused.
- `wiki/frontier_map.yaml` is the next-version basis: it summarizes human-reviewed knowledge, reusable reproductions, open frontier questions, and human direction decisions.

Old versions are read-only; consult only `closeout.md` and `wiki/epoch_summary.md` from legacy epochs. Never let an old-version PRD override the current epoch PRD.（旧版本只读 `closeout.md` 和轻量 wiki；禁止让旧版本 PRD 覆盖当前版本 PRD。）

### Goal-mode readiness check

读完上述文件后，检查是否满足目标模式执行条件。若以下条件**全部满足**，且当前不是由 Codex / Claude Code 目标模式驱动的一次执行迭代，则**仅输出目标模式启动建议，不执行任何任务**：

- `STATUS.yaml.status` 为 `prd_locked`、`spec_ready`、`plan_ready` 或 `running`
- `TASK_QUEUE.yaml` 中有 `status: active` 或 `status: pending` 的任务
- `TASK_QUEUE.yaml` 中有具体的、非占位符的 Active Task
- `goal-ready` 通过，或 `GOAL_LOCK.yaml` 明确指出 stale source 需要先刷新

满足条件时输出：

```
[research] 检测到可执行任务，建议进入 Codex / Claude Code 目标模式：

  使用 docs/research/{CURRENT}/goal.md 作为目标输入。

目标模式每轮只能执行 `TASK_QUEUE.yaml` 中的唯一 active task。
遇到 blocker、stale lock、human review、gate_blocked 或 closed_* 时停止。
```

若当前已处于目标模式迭代中，则跳过此提示，直接进入执行流程。

## Execution policy

- Always execute the earliest incomplete gate, or write the precise next execution prompt when the controller cannot safely run harnesses itself.
- Default to the current `Vn`; do not advance legacy folders when `CURRENT` exists.
- `research_loop.py` defaults to epoch contract mode when `CURRENT` and `Vn/` exist; the legacy deterministic controller requires explicit `--legacy-controller`.
- PRD, Spec, Plan, and paper draft generation are internal compiler passes owned by `/research`. Users should not need to invoke retired compiler skills directly during the normal lifecycle.
- Internal Spec/Plan/Paper passes may run automatically, but their gates cannot auto-pass: `spec-ready`, `loop-ready`/plan gate, `paper-ready`, and `paper-binding-ready` remain hard validation boundaries.
- Paper is semi-internal: placeholder-complete draft generation is automatic, but Paper Binding remains blocked until `PAPER_BINDING_DECISION.md` explicitly records `paper_binding_ready: true` and audit passes.
- Execute only the active task from `Vn/TASK_QUEUE.yaml`; do not skip `TASK_QUEUE.yaml`.
- Do not execute a task that lacks `research_binding`. Every active task must declare whether it is `direction_bootstrap`, `spine_bound`, `maintenance`, or `paper_binding`.
- For `spine_bound` work, `research_binding` must trace the task to `RESEARCH_SPINE.yaml` through `rq_id`, `claim_ids`, `experiment_ids`, and `evidence_ids`; experiment, analysis, and result-binding tasks must bind concrete experiment and evidence ids before execution.
- Treat `TASK_QUEUE.yaml` as gate-aware state: Task statuses are `pending`, `active`, `completed`, `blocked`, `failed_execution`, `failed_harness`, and `skipped`; Gate statuses are `pending`, `active`, `audit_required`, `audit_failed`, `passed`, `blocked`, and `falsified`.
- Treat `docs/research/agent/SEARCH_POLICY.md` and `docs/research/agent/REPRODUCTION_POLICY.md` as hard execution policies.
- Default epochs start with `G0_SEARCH_LOCK`, which must produce `search/` logs, curated `baselines/INDEX.yaml` dossier entries, and version-level `BASELINE_LOCK.yaml`, and then `G1_REPRODUCTION_LOCK`; do not activate reproduction, proposed-method implementation, or experiment tasks until baseline lock is `locked`, selected baseline/dataset/design refs resolve to dossier cards, and the relevant gate is `passed`, explicitly human-waived, or explicitly marked as `failed_harness` with recorded evidence and human waiver. A gate in `blocked` or `falsified` status is not an exemption; it stops activation.
- Every approved RQ must run reproduction coverage before innovation or experiment work. Coverage may resolve to `reuse_allowed`, `delta_check_required`, `new_reproduction_required`, or `reuse_blocked`; it must be recorded in `REPRODUCTION_LEDGER.yaml`.
- Insight is not self-approved by the executor. The agent writes an AI draft in `INSIGHT_REVIEW.yaml`; wiki binding and paper eligibility require a human verdict.
- Stay inside the Research Corridor.
- Do not create `Vn+1` before current `Vn/closeout.md` is complete and status is `closed_*`.
- If the user invokes `/research explore`, switch to `research-explore`; do not execute a task or modify PRD.
- If the user invokes `/research insight`, switch to `research-insight`; interpret existing evidence only and update the current epoch wiki.
- If the user invokes `/research audit`, honor audit modes: format, migration, epoch, git, evidence, paper-binding, full.
- Before executing the active task, record `git status --short` when Git is available.
- After task completion, record `git diff --stat`, write a task run report, and commit only when task policy allows.
- Never infer experiments from paper.
- Never fabricate data, metrics, baselines, or results.
- Never use mock/toy/smoke outputs as claim evidence.
- Never treat prompt-only scaffold as experiment evidence or Paper Binding evidence.
- If execution fails, retry within the current plan's allowed scope.
- Do not treat `failed_execution` or `failed_harness` as research falsification. Classify failures using `docs/research/agent/FAILURE_TRIAGE_POLICY.md`.
- If spec is incomplete but PRD is clear, repair spec and regenerate the plan.
- If PRD is ambiguous or a research hypothesis is challenged, stop and request human review.
- **Document-writing vs Execution autonomy boundary**:
  - When writing, editing, or compiling research documents (PRD, SPEC, PLAN, RESEARCH_SPINE, ai_loop_prompt.md, goal.md, CODEX_GOAL_TEMPLATE.md), if user intent is unclear, contradictory, or a decision would change the research direction, core hypothesis, baseline selection, metric choice, or evidence boundary: **stop and ask the user before proceeding**. Do not choose the most convenient interpretation.
  - When executing the active task (running experiments, writing implementation code, running harnesses, collecting artifacts, running tests, reproducing baselines): **do not stop to ask for preference clarification**. Proceed autonomously. Record blockers only for missing required information (dataset paths, commands, seeds, artifacts), not for ambiguous design choices.

## Internal Compiler Pipeline

`/research` is the only normal lifecycle entry. The following former user-facing skills are now internal passes:

```text
initialized --prd-ready--> prd_locked
prd_locked --compile SPEC + spec-ready--> spec_ready
spec_ready --compile PLAN/TASK_QUEUE + loop-ready--> plan_ready
plan_ready/running --agent executor--> gate / closeout
closed_stable --paper draft + paper-ready--> waiting_human_binding_decision
closed_stable + PAPER_BINDING_DECISION.md:true --paper-binding-ready--> paper_binding_ready
paper_binding_ready --binding manuscript generated--> paper_bound
```

Internal pass ownership:

- **Spec compiler**: uses `skills/research-spec/scripts/` and shared code, but `/research` calls it automatically after PRD lock.
- **Plan compiler**: uses `skills/research-plan/scripts/` and shared code, but `/research` calls it automatically after Spec readiness.
- **Paper draft compiler**: uses `skills/research-paper/scripts/`, but `/research` calls it automatically after stable closeout.
- **Paper Binding**: never auto-approved; the human decision file remains the explicit signature.

Spec/Plan/Paper can be implicit, but their gates cannot be implicit. Every failed internal pass writes a machine-readable blocker under `Vn/audits/*-gate/` and stops progression.

## Goal Mode Integration

`/research` is designed to run as a stateless-per-iteration worker under Codex or Claude Code goal mode. Each iteration reads persisted state from files, executes one atomic task, updates state, and exits. The next iteration picks up where the previous left off through `goal.md`, `GOAL_LOCK.yaml`, and `TASK_QUEUE.yaml`.

### Starting goal mode

After the PRD is filled and approved:

```
Use docs/research/{CURRENT}/goal.md as the Codex or Claude Code goal-mode input.
```

Each iteration:

1. Read `RESEARCH_DIRECTION.md` and `CURRENT`
2. Read `Vn/STATUS.yaml` — if `status` is `closed_*` or `paper_bound`, **stop and output completion signal**
3. Read the active task from `Vn/TASK_QUEUE.yaml`.
4. Read `Vn/TASK_QUEUE.yaml` for task details (success criteria, test commands, evidence requirements)
5. Execute the atomic task described in the active task entry.
6. Record Git state before and after
7. Write `Vn/runs/TASK_XXX_report.md` with commands, evidence, diff summary, and commit hash
8. Update state files:
   - `LOOP_LOG.md` — append loop entry
   - `TASK_QUEUE.yaml` — mark current task done, activate next
   - Update `TASK_QUEUE.yaml` to reflect the next atomic task.
   - `STATUS.yaml` — update status if gate completed or blocked
   - `GIT_STATE.yaml` — record commit hash
9. If the completed task crosses a gate boundary, call `research-insight` to update `Vn/wiki/*`

### Completion signal

When `STATUS.yaml.status` is any of `closed_success`, `closed_negative`, `closed_blocked`, `closed_falsified`, `closed_pivot_required`, `closed_stable`, or `paper_bound`, output:

```
<promise>RESEARCH_COMPLETE</promise>
```

This tells the goal-mode executor to stop. No plugin-local state file is required.

### Block signal

When `STATUS.yaml.status` is `gate_blocked` and a blocker is documented in `Vn/runs/TASK_XXX_blocker.md`, output:

```
<promise>RESEARCH_BLOCKED</promise>
```

The user can inspect the blocker, resolve it, refresh the stale contract if needed, and restart goal mode from the same `goal.md`.

### Loop safety rules

- Never rely on previous chat memory as evidence — only persisted files are authoritative.
- If the active task is ambiguous, write a concrete blocker instead of guessing.
- If the same task fails twice with the same cause, escalate to `gate_blocked`.
- If the active task references a subagent (e.g., `research-coding`), delegate to that subagent via the Agent tool.
- Do not expand scope beyond the active task in a single iteration.

## Insight policy

The goal is not to mechanically prove the initial idea.

The PRD is treated as the current best research hypothesis. The agent must record failures, anomalies, negative results, and surprising observations. It may propose diagnostic experiments or 15-degree pivots. It must not modify core PRD claims without human approval.

`research-insight` is the explicit interpretation layer. In epoch workspaces, durable insight belongs in `docs/research/{CURRENT}/wiki/*`. Legacy `docs/research/insights/insight_log.md` remains readable for compatibility and migration, but it is not the default current-epoch insight truth when `CURRENT` exists.

## Version transition policy

Create `Vn+1` only when current status is closed and `closeout.md` says `create_next_version: true`, or when closeout shows that the main research question, core hypothesis, baseline landscape, metric/dataset/model choice, or phase has changed. Do not create a new version for code bugs, missing paths, reruns, minor spec field fixes, paper placeholder fixes, or stale-plan regeneration.（工程问题留在当前版本；研究问题改变才开下一版本。）

## Paper Binding policy

Paper draft generation is an internal `/research` expression stage after closeout. Paper Binding is allowed only when current status is `closed_stable` or `paper_binding_ready`, `PAPER_BINDING_DECISION.md` says `paper_binding_ready: true`, and every allowed claim is backed by experiment, run, artifact, metric, baseline, seed protocol, and audit status. Successful binding advances the epoch to `paper_bound`; exploratory insight can support motivation or discussion only.

Conflict resolution: If `STATUS.yaml` and `PAPER_BINDING_DECISION.md` disagree, trust `PAPER_BINDING_DECISION.md` and pause for human review. The human decision file overrides the machine status when they conflict.

## Outputs

- `docs/research/RESEARCH_DIRECTION.md`
- `docs/research/CURRENT`
- `docs/research/Vn/STATUS.yaml`
- `docs/research/Vn/TASK_QUEUE.yaml`
- `docs/research/Vn/LOOP_LOG.md`
- `docs/research/Vn/GIT_STATE.yaml`
- `docs/research/Vn/git_log.md`
- `docs/research/Vn/runs/TASK_XXX_report.md`
- `docs/research/Vn/wiki/*`
- `docs/research/Vn/closeout.md`
- `docs/research/Vn/PAPER_BINDING_DECISION.md`
- `docs/research/Vn/STATUS.yaml` (per-epoch state; legacy `state.yaml` is fallback only)
- `docs/research/Vn/TASK_QUEUE.yaml`
- `docs/research/plans/plan_queue.yaml` (legacy)
- dated plans under `docs/research/plans/YYYY-MM-DD-purpose/`
- audit reports under `docs/research/audits/YYYY-MM-DD-audit/`
- legacy insight logs under `docs/research/insights/`
- spec feedback under `docs/research/spec/feedback/`
- human review requests under `docs/research/audits/YYYY-MM-DD-prd-review/`

## Command

### Controller (epoch contract summary)

```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo /absolute/path/to/repo --once
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --max-steps 1
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --dry-run --json
```

When `CURRENT` and `Vn/` exist, the default implementation reports the epoch contract and may advance internal compiler passes (`prd_locked -> spec_ready -> plan_ready`, and `closed_stable -> paper draft / binding gate`) without running experiment harnesses. Legacy deterministic controller behavior requires explicit `--legacy-controller`.

### Autonomous loop (goal mode)

```bash
# Start or resume autonomous execution
Use docs/research/{CURRENT}/goal.md as the Codex or Claude Code goal-mode input.
```

## Agent Executor Boundary

Codex / Claude Code are the supported agent executors. They read the active task from `Vn/TASK_QUEUE.yaml`, perform the task in their own runtime, and call `update_state.py` with commands, stdout/stderr paths, exit code, artifact hashes, tests, git state, and blockers.

`--executor prompt-only` remains only as a legacy-controller compatibility slot. The epoch controller does not run an independent backend and must not claim that it ran harnesses or generated experimental evidence.

## Glossary

Terms used across the research skill family with precise operational definitions:

- **Research Corridor** — The scope declared in `RESEARCH_DIRECTION.md` plus the current epoch's `Vn/PRD.tex` and `Vn/RESEARCH_SPINE.yaml`. If those files are absent, the agent must stop and request human clarification rather than guessing the boundary.
- **backend** — An independent resident execution environment (e.g., a daemon, server, or persistent compute layer) that runs experiments, harnesses, or generates empirical evidence. The `research` skill does not provide such a backend; Codex / Claude Code are the agent executors.
- **Charter-bounded** — The epoch loop is constrained by a human-approved research charter (`RESEARCH_DIRECTION.md`). Agents may not modify the charter or explore outside its scope without explicit human instruction.
- **工程问题 (engineering issue)** — Bug fixes, path corrections, reruns, minor spec field fixes, paper placeholder fixes, or stale-plan regeneration. These stay in the current version.
- **研究问题改变 (research issue change)** — Changes to the main research question, core hypothesis, baseline landscape, metric/dataset/model choice, or phase. These justify creating `Vn+1`.

## Global Language Contract

All human-facing research artifacts under `docs/research/` must be **Chinese by default**.

This includes:
- PRD prose, plans, prompts, gap reports, blockers, and acceptance criteria
- Audit reports, drift findings, repair plans, and wiki entries
- EXP sessions, explore syntheses, and insight interpretations
- Task run reports, decision logs, and loop logs

Machine-facing layers remain **English** for parser compatibility:
- YAML keys, stable IDs, schema fields, and filenames
- LaTeX structural commands and TikZ code
- Git commit messages and branch names

The only explicit exception is the internal paper draft/binding stage: the manuscript body (Abstract, Introduction, Method, Experiments, Results) may be English for top-conference submission style. All associated metadata, blockers, gap reports, placeholder maps, and binding decisions remain Chinese.

Internal compiler modules that define language clauses through scripts or generated templates must not contradict this contract.

## Git Safety

Allowed Git operations: `git status`, `git diff`, `git log`, `git add` allowed files, `git commit` current task, and `git tag` closeout / paper binding.

Forbidden unless explicitly authorized: `git push`, `git reset --hard`, `git clean -fd`, `git rebase`, checkout that overwrites user changes, rewrite history, force push, and deleting files outside task scope.

## Explore and Audit

`/research explore` is pure discussion and optional saved EXP sessions. It can propose wiki, task, baseline, literature, next-version, or paper-shape updates, but cannot execute them. When the user explicitly invokes `/research explore`, delegate immediately to the `research-explore` skill.

`/research insight` promotes existing evidence, blockers, negative results, failed paths, or saved EXP sessions into the current `Vn/wiki/*`. It must separate fact, artifact, interpretation, and speculation. When the user explicitly invokes `/research insight`, delegate immediately to the `research-insight` skill.

`/research audit` is the gatekeeper for format, migration, git, evidence, and paper binding. It can detect legacy workspace layout and generate a migration plan; it must not silently rewrite research claims. When the user explicitly invokes `/research audit`, delegate immediately to the `research-audit` skill.

## Claude Code Subagents

When project-level subagents are installed under `.claude/agents/`, `/research` remains the controller and the subagents are specialized workers:

- `research-math` for formulation and notation checks.
- `research-literature` for related work, benchmark, and baseline analysis.
- `research-reproduce` for baseline reproduction.
- `research-coding` for implementation under the current plan.
- `research-experiment` for declared experiment execution.
- `research-analysis` for anomalies, negative results, and pivot proposals.
- `research-paper` for placeholder-safe manuscript updates.
- `research-audit` for cross-file drift and evidence checks.

Do not use a custom registry as the primary subagent format. Claude Code project agents are Markdown files with YAML frontmatter in `.claude/agents/`.
