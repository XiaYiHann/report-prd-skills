---
name: research-update
description: "Use when the user wants to update, reinstall, verify, or clean the research-loop skill family itself, including installer version drift, retired skill cleanup, ~/.agents/skills canonical layout, ~/.claude/skills symlink state, or visible skill manifest checks."
---

# Research Update

## Purpose

Update the installed research-loop skill family and verify the runtime skill
surface. This is a maintenance skill for the framework installation, not a
research execution skill.

Use it for requests such as:

- update research-loop skills to the latest version;
- reinstall from this checkout or from `main`;
- clean retired skills such as `research-prd` or `research-ppt`;
- verify that `~/.claude/skills` points to `~/.agents/skills`;
- check whether the visible research skill list matches the current manifest.

## Contract

- `~/.agents/skills` is the canonical skill store.
- `~/.claude/skills` must be a symlink to `~/.agents/skills`.
- Visible research-loop skills are exactly:
  - `research`
  - `research-explore`
  - `research-insight`
  - `research-status`
  - `research-update`
  - `research-init`
  - `research-goal`
  - `research-audit`
- Internal compiler modules may exist, but must not contain `SKILL.md`:
  - `research-spec`
  - `research-plan`
  - `research-paper`
- Retired user-facing skills must not exist:
  - `research-prd`
  - `research-ppt`
  - `research-evidence`
  - `research-writing`
  - `research-brainstorming`

## Workflow

1. Identify the update source:
   - local checkout: use `RESEARCH_EXECUTION_SKILLS_SOURCE_DIR=/absolute/repo`;
   - remote main: use the raw `install.sh` one-line command.
2. Before changing anything, inspect:
   - `ls -ld ~/.agents/skills ~/.claude/skills`;
   - `readlink ~/.claude/skills`;
   - visible research skills under `~/.agents/skills/*/SKILL.md`.
3. Run the installer with `--force`.
4. Run the verification script.
5. Report:
   - source used;
   - visible manifest after update;
   - retired entries removed or still present;
   - symlink state;
   - whether the remote `main` command already contains the fix.

## Commands

Update from a local checkout:

```bash
RESEARCH_EXECUTION_SKILLS_SOURCE_DIR=/absolute/path/to/research-loop \
  bash /absolute/path/to/research-loop/install.sh --force --no-agents
```

Update from remote `main`:

```bash
curl -fsSL https://raw.githubusercontent.com/XiaYiHann/research-loop/main/install.sh | bash -s -- --force
```

Verify installed surface:

```bash
python3 ~/.agents/skills/research-update/scripts/verify_research_update.py
```

Machine-readable verification:

```bash
python3 ~/.agents/skills/research-update/scripts/verify_research_update.py --json
```

## Boundaries

- Do not modify `docs/research/`.
- Do not advance `TASK_QUEUE.yaml`.
- Do not create, close, or bind any research epoch.
- Do not push to `main` unless the user explicitly authorizes it.
- If local fixes are not merged to `main`, say that the remote `curl` command
  cannot see them yet.
