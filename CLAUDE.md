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
