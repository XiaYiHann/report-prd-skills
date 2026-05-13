---
name: research
description: "Use when a research workspace under docs/research needs the default autonomous controller across PRD, Spec, Plan, execution, audit, insight feedback, or paper stages."
---

# research

## Purpose

`research` is the unified epoch contract controller for Codex / Claude Code agent executors.

It inspects `docs/research/`, resolves the current epoch from `CURRENT`, and reports the bounded research contract through Direction, PRD, Spec, Plan, Task Queue, Next Action, execution, gate, insight interpretation, wiki, closeout, and paper binding. It does not provide an independent resident backend; Codex / Claude Code execute `NEXT_ACTION.md` as the agent executor and must submit structured evidence with `update_state.py`.

新版系统是 **Charter-bounded + Git-backed + Explore-enabled Epoch Research Loop**：

> 自动科研不是自动写论文，而是一个按研究版本推进的闭环：每个版本都在顶层研究方向约束下，完整提出问题、签订实验合同、执行或被门禁阻断、把证据与洞察沉淀进 wiki，然后生成下一版更清晰的研究问题，直到某个版本 closed_stable 后进入 Paper Binding。

> Auto research is not automatic paper writing. It is a charter-bounded, epoch-based loop where each research version fully frames, contracts, executes, gates, distills evidence into a wiki, and either seeds the next sharper version or enters paper binding.

## Core hierarchy

`RESEARCH_DIRECTION.md` constrains exploration.  
`CURRENT` resolves the active epoch.  
`Vn/PRD.md` defines the current research truth.  
`Vn/SPEC.yaml` constrains execution.  
`Vn/PLAN.md` schedules execution.  
`Vn/TASK_QUEUE.yaml` defines available work.  
`Vn/NEXT_ACTION.md` defines the only task for the current loop.  
`Vn/GIT_STATE.yaml` records Git checkpoints.  
`docs/research/explore/` records pure exploration sessions.  
Runs and artifacts provide evidence.  
Wiki records durable insight.  
Closeout controls next version or Paper Binding.

Authority chain:

```text
RESEARCH_DIRECTION.md
  -> CURRENT
  -> Vn/PRD.md
  -> Vn/SPEC.yaml
  -> Vn/PLAN.md
  -> Vn/TASK_QUEUE.yaml
  -> Vn/NEXT_ACTION.md
  -> Vn/runs + Vn/artifacts
  -> Vn/audits
  -> research-insight
  -> Vn/wiki
  -> Vn/closeout.md
  -> Vn+1/PRD.md 或 paper binding
```

Every `/research` run must first read:

1. `docs/research/RESEARCH_DIRECTION.md`
2. `docs/research/CURRENT`
3. `docs/research/{CURRENT}/STATUS.yaml`
4. `docs/research/{CURRENT}/NEXT_ACTION.md`
5. `docs/research/{CURRENT}/TASK_QUEUE.yaml`
6. `docs/research/{CURRENT}/PRD.md`
7. `docs/research/{CURRENT}/SPEC.yaml`
8. `docs/research/{CURRENT}/PLAN.md`

旧版本只读 `closeout.md` 和轻量 wiki。禁止让旧版本 PRD 覆盖当前版本 PRD。

### Ralph-loop readiness check

读完上述 8 个文件后，检查是否满足自动循环执行条件。若以下条件**全部满足**，且当前**不在** ralph-loop 中（`.claude/.ralph-loop.local.md` 不存在），则**仅输出启动建议，不执行任何任务**：

- `STATUS.yaml.status` 为 `prd_locked`、`spec_ready`、`plan_ready` 或 `running`
- `TASK_QUEUE.yaml` 中有 `status: active` 或 `status: pending` 的任务
- `NEXT_ACTION.md` 中有具体的、非占位符的 Active Task

满足条件时输出：

```
[research] 检测到可执行任务，建议启动自动循环：

  /ralph-loop "/research" --max-iterations 50 --completion-promise "RESEARCH_COMPLETE"

启动后每个迭代会自动执行 NEXT_ACTION.md 中的一个原子任务。
受阻时循环自动停止。用 /cancel-ralph 可随时取消。
```

用户执行上述命令后，系统进入全自动 Gate-by-Gate 执行。

若当前**已在** ralph-loop 中（`.claude/.ralph-loop.local.md` 存在），则跳过此提示，正常进入执行流程。

## Execution policy

- Always execute the earliest incomplete gate, or write the precise next execution prompt when the controller cannot safely run harnesses itself.
- Default to the current `Vn`; do not advance legacy folders when `CURRENT` exists.
- `research_loop.py` defaults to epoch contract mode when `CURRENT` and `Vn/` exist; the legacy deterministic controller requires explicit `--legacy-controller`.
- Execute only `Vn/NEXT_ACTION.md`; do not skip `TASK_QUEUE.yaml`.
- Treat `TASK_QUEUE.yaml` as gate-aware state: Task statuses are `pending`, `active`, `completed`, `blocked`, `failed_execution`, `failed_harness`, and `skipped`; Gate statuses are `pending`, `active`, `audit_required`, `audit_failed`, `passed`, `blocked`, and `falsified`.
- Treat `docs/research/agent/SEARCH_POLICY.md` and `docs/research/agent/REPRODUCTION_POLICY.md` as hard execution policies.
- Default epochs start with `G0_SEARCH_LOCK` and `G1_REPRODUCTION_LOCK`; do not activate proposed-method experiment tasks until these gates are passed, explicitly human-waived, or blocked with recorded evidence.
- Stay inside the Research Corridor.
- Do not create `Vn+1` before current `Vn/closeout.md` is complete and status is `closed_*`.
- If the user invokes `/research explore`, switch to `research-explore`; do not execute a task or modify PRD.
- If the user invokes `/research insight`, switch to `research-insight`; interpret existing evidence only and update the current epoch wiki.
- If the user invokes `/research audit`, honor audit modes: format, migration, epoch, git, evidence, paper-binding, full.
- Before executing `NEXT_ACTION`, record `git status --short` when Git is available.
- After task completion, record `git diff --stat`, write a task run report, and commit only when task policy allows.
- Never infer experiments from paper.
- Never fabricate data, metrics, baselines, or results.
- Never use mock/toy/smoke outputs as claim evidence.
- Never treat prompt-only scaffold as experiment evidence or Paper Binding evidence.
- If execution fails, retry within the current plan's allowed scope.
- Do not treat `failed_execution` or `failed_harness` as research falsification. Classify failures using `docs/research/agent/FAILURE_TRIAGE_POLICY.md`.
- If spec is incomplete but PRD is clear, repair spec and regenerate the plan.
- If PRD is ambiguous or a research hypothesis is challenged, stop and request human review.

## Ralph Loop Integration

`/research` is designed to run as a stateless-per-iteration worker inside Claude Code's ralph-loop plugin. Each iteration reads persisted state from files, executes one atomic task, updates state, and exits. The next iteration picks up where the previous left off.

### Starting the loop

After the PRD is filled and approved:

```
/ralph-loop "/research" --max-iterations 50 --completion-promise "RESEARCH_COMPLETE"
```

This feeds `/research` to Claude Code repeatedly. Each iteration:

1. Read `RESEARCH_DIRECTION.md` and `CURRENT`
2. Read `Vn/STATUS.yaml` — if `status` is `closed_*` or `paper_binding_ready`, **stop and output completion signal**
3. Read `Vn/NEXT_ACTION.md` — this is the only task for this iteration
4. Read `Vn/TASK_QUEUE.yaml` for task details (success criteria, test commands, evidence requirements)
5. Execute the atomic task described in NEXT_ACTION.md
6. Record Git state before and after
7. Write `Vn/runs/TASK_XXX_report.md` with commands, evidence, diff summary, and commit hash
8. Update state files:
   - `LOOP_LOG.md` — append loop entry
   - `TASK_QUEUE.yaml` — mark current task done, activate next
   - `NEXT_ACTION.md` — write the next atomic task
   - `STATUS.yaml` — update status if gate completed or blocked
   - `GIT_STATE.yaml` — record commit hash
9. If the completed task crosses a gate boundary, call `research-insight` to update `Vn/wiki/*`

### Completion signal

When `STATUS.yaml.status` is any of `closed_success`, `closed_negative`, `closed_blocked`, `closed_falsified`, `closed_pivot_required`, `closed_stable`, or `paper_binding_ready`, output:

```
<promise>RESEARCH_COMPLETE</promise>
```

This tells ralph-loop to stop. The state file `.claude/.ralph-loop.local.md` is automatically cleaned up.

### Block signal

When `STATUS.yaml.status` is `gate_blocked` and a blocker is documented in `Vn/runs/TASK_XXX_blocker.md`, output:

```
<promise>RESEARCH_BLOCKED</promise>
```

The user can inspect the blocker, resolve it, and restart with `/ralph-loop "/research" --max-iterations N`.

### Cancelling

```
/cancel-ralph
```

Stops the loop immediately. State files are preserved — restarting the loop resumes from the last persisted state.

### Loop safety rules

- Never rely on previous chat memory as evidence — only persisted files are authoritative.
- If `NEXT_ACTION.md` is ambiguous, write a concrete blocker instead of guessing.
- If the same task fails twice with the same cause, escalate to `gate_blocked`.
- If `NEXT_ACTION.md` references a subagent (e.g., `research-coding`), delegate to that subagent via the Agent tool.
- Do not expand scope beyond `NEXT_ACTION.md` in a single iteration.

## Insight policy

The goal is not to mechanically prove the initial idea.

The PRD is treated as the current best research hypothesis. The agent must record failures, anomalies, negative results, and surprising observations. It may propose diagnostic experiments or 15-degree pivots. It must not modify core PRD claims without human approval.

`research-insight` is the explicit interpretation layer. In epoch workspaces, durable insight belongs in `docs/research/{CURRENT}/wiki/*`. Legacy `docs/research/insights/insight_log.md` remains readable for compatibility and migration, but it is not the default current-epoch insight truth when `CURRENT` exists.

## Version transition policy

工程问题留在当前版本；研究问题改变才开下一版本。

Create `Vn+1` only when current status is closed and `closeout.md` says `create_next_version: true`, or when closeout shows that the main research question, core hypothesis, baseline landscape, metric/dataset/model choice, or phase has changed. Do not create a new version for code bugs, missing paths, reruns, minor spec field fixes, paper placeholder fixes, or stale-plan regeneration.

## Paper Binding policy

Paper Binding is allowed only when current status is `closed_stable` or `paper_binding_ready`, `PAPER_BINDING_DECISION.md` says `paper_binding_ready: true`, and every allowed claim is backed by experiment, run, artifact, metric, baseline, seed protocol, and audit status. Exploratory insight can support motivation or discussion only.

## Outputs

- `docs/research/RESEARCH_DIRECTION.md`
- `docs/research/CURRENT`
- `docs/research/Vn/STATUS.yaml`
- `docs/research/Vn/TASK_QUEUE.yaml`
- `docs/research/Vn/NEXT_ACTION.md`
- `docs/research/Vn/LOOP_LOG.md`
- `docs/research/Vn/GIT_STATE.yaml`
- `docs/research/Vn/git_log.md`
- `docs/research/Vn/runs/TASK_XXX_report.md`
- `docs/research/Vn/wiki/*`
- `docs/research/Vn/closeout.md`
- `docs/research/Vn/PAPER_BINDING_DECISION.md`
- `docs/research/state.yaml`
- `docs/research/plans/plan_queue.yaml`
- dated plans under `docs/research/plans/YYYY-MM-DD-purpose/`
- audit reports under `docs/research/audits/YYYY-MM-DD-audit/`
- legacy insight logs under `docs/research/insights/`
- spec feedback under `docs/research/spec/feedback/`
- human review requests under `docs/research/audits/YYYY-MM-DD-prd-review/`
- ralph-loop state file `.claude/.ralph-loop.local.md` (managed by ralph-loop plugin)

## Command

### Controller (epoch contract summary)

```bash
python3 ~/.claude/skills/research/scripts/research_loop.py --repo /absolute/path/to/repo --once
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --max-steps 1
python3 ~/.claude/skills/research/scripts/research_loop.py --workspace docs/research --dry-run --json
```

When `CURRENT` and `Vn/` exist, the default implementation reports the epoch contract for Codex / Claude Code. Legacy deterministic controller behavior requires explicit `--legacy-controller`.

### Autonomous loop (ralph-loop)

```bash
# Start autonomous execution (50 iterations max)
/ralph-loop "/research" --max-iterations 50 --completion-promise "RESEARCH_COMPLETE"

# Resume after blocker resolution
/ralph-loop "/research" --max-iterations 30

# Cancel running loop
/cancel-ralph
```

## Agent Executor Boundary

Codex / Claude Code are the supported agent executors. They read `Vn/NEXT_ACTION.md`, perform the task in their own runtime, and call `update_state.py` with commands, stdout/stderr paths, exit code, artifact hashes, tests, git state, and blockers.

`--executor prompt-only` remains only as a legacy-controller compatibility slot. The epoch controller does not run an independent backend and must not claim that it ran harnesses or generated experimental evidence.

## Git Safety

Allowed Git operations: `git status`, `git diff`, `git log`, `git add` allowed files, `git commit` current task, and `git tag` closeout / paper binding.

Forbidden unless explicitly authorized: `git push`, `git reset --hard`, `git clean -fd`, `git rebase`, checkout that overwrites user changes, rewrite history, force push, and deleting files outside task scope.

## Explore and Audit

`/research explore` is pure discussion and optional saved EXP sessions. It can propose wiki, task, baseline, literature, next-version, or paper-shape updates, but cannot execute them.

`/research insight` promotes existing evidence, blockers, negative results, failed paths, or saved EXP sessions into the current `Vn/wiki/*`. It must separate fact, artifact, interpretation, and speculation.

`/research audit` is the gatekeeper for format, migration, git, evidence, and paper binding. It can detect legacy workspace layout and generate a migration plan; it must not silently rewrite research claims.

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
