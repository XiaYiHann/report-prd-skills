# CLAUDE.md

This repository is the `research-loop` meta-framework. It must not be treated as
a concrete downstream research project.

- Read `docs/research/RESEARCH_DIRECTION.md` when it exists, but treat it as the framework charter.
- Do not resolve a repo-local active epoch from `docs/research/CURRENT`; this repo must not require `docs/research/Vn/`.
- Read the relevant `skills/research*/SKILL.md`, shared schema, scripts, and tests for the framework task.
- Keep all changes inside the framework scope: skills, schemas, tests, installer, documentation, and tracked agent policies.
- Never bind this repository to a concrete dataset, baseline, metric, benchmark, method, paper claim, or paper-binding decision.
- Never fabricate execution, artifact, benchmark, or paper result.
- Never create repo-local Vn+1 or paper-binding artifacts.
- Never modify `RESEARCH_DIRECTION.md` without explicit user instruction.
- Git allowed: `git status`, `git diff`, `git log`, `git add` allowed files, `git commit` current framework task, `git tag` framework release.
- Git forbidden unless explicitly authorized: `git push`, `git reset --hard`, `git clean -fd`, `git rebase`, checkout that overwrites user changes, history rewrite, force push, deleting files outside task scope.

## Research Agent Behavior Contract

1. RQ before action. In this repo, RQ means the framework-level protocol question the system must support; it is not a repo-local project claim.
2. Reproduce before propose. Framework behavior, schema changes, validators, and scripts need regression tests before new abstractions are accepted.
3. Evidence before writing. Do not write framework claims unless the corresponding test, log, audit sample, or command output exists.
4. Surgical edits. Modify only declared framework files. Do not silently rewrite unrelated artifacts.
5. Conflict surfacing. If docs, schemas, scripts, tests, or agent policies disagree, stop and report the conflict instead of averaging them.
6. Checkpoint long loops. After each major stage, write what changed, what evidence was produced, and what remains blocked.
7. Fail visibly. Missing schema coverage, failed validator behavior, skipped tests, or unverifiable framework claims must be explicitly marked.
8. Deterministic work belongs to scripts. Formatting checks, table generation, metric computation, and file routing should be scripted, not decided by LLM judgment.
9. Tests are evidence, not decoration. Passing tests only count if they verify the intended framework behavior.
10. Convention beats novelty. Follow the project's existing folder structure, naming, template, and artifact format unless explicitly asked to migrate.
