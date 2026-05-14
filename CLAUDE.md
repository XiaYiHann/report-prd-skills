# CLAUDE.md

- Always read `docs/research/RESEARCH_DIRECTION.md`.
- Resolve current epoch from `docs/research/CURRENT`.
- Read `docs/research/{CURRENT}/RESEARCH_SPINE.yaml` to understand the evidence-bound research spine (RQ -> Claim -> Experiment -> Evidence -> Figure/Table -> Paper Section).
- Execute only the active task from `docs/research/{CURRENT}/TASK_QUEUE.yaml` unless user explicitly overrides.
- Keep all exploration inside Research Corridor.
- Never fabricate execution, artifact, benchmark, or paper result.
- Never create Vn+1 before Vn closeout.
- Never modify `RESEARCH_DIRECTION.md` without explicit user instruction.
- After each loop, update `LOOP_LOG.md` and `TASK_QUEUE.yaml`.
- Git allowed: `git status`, `git diff`, `git log`, `git add` allowed files, `git commit` current task, `git tag` closeout/paper binding.
- Git forbidden unless explicitly authorized: `git push`, `git reset --hard`, `git clean -fd`, `git rebase`, checkout that overwrites user changes, history rewrite, force push, deleting files outside task scope.

## Research Agent Behavior Contract

1. RQ before action. Every task must map to a Research Question, Claim, Experiment, Evidence, Figure/Table, or Paper Section.
2. Reproduce before propose. Before claiming novelty or designing experiments, search prior work and inspect the current repo.
3. Evidence before writing. Do not write paper claims unless the corresponding data, log, table, or citation exists.
4. Surgical edits. Modify only the current version folder or declared target files. Do not silently rewrite unrelated artifacts.
5. Conflict surfacing. If PRD, spec, task, paper, or code disagree, stop and report the conflict instead of averaging them.
6. Checkpoint long loops. After each major stage, write what changed, what evidence was produced, and what remains blocked.
7. Fail visibly. Missing data, failed reproduction, skipped experiment, or unverifiable claim must be explicitly marked.
8. Deterministic work belongs to scripts. Formatting checks, table generation, metric computation, and file routing should be scripted, not decided by LLM judgment.
9. Tests are evidence, not decoration. Passing tests only count if they verify the intended scientific or system behavior.
10. Convention beats novelty. Follow the project's existing folder structure, naming, template, and artifact format unless explicitly asked to migrate.
