# CLAUDE.md

- Always read `docs/research/RESEARCH_DIRECTION.md`.
- Resolve current epoch from `docs/research/CURRENT`.
- Execute only `docs/research/{CURRENT}/NEXT_ACTION.md` unless user explicitly overrides.
- Keep all exploration inside Research Corridor.
- Never fabricate execution, artifact, benchmark, or paper result.
- Never create Vn+1 before Vn closeout.
- Never modify `RESEARCH_DIRECTION.md` without explicit user instruction.
- After each loop, update `LOOP_LOG.md`, `TASK_QUEUE.yaml`, and `NEXT_ACTION.md`.
