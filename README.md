# report-prd-skills

A [Claude Code](https://code.claude.com) skill family for generating **PRD-based reports** from LaTeX source. Supports two PRD types — `research-prd` (academic research programs) and `engineering-prd` (software engineering specs) — rendered to both PDF and Markdown artifacts.

## Skills

| Skill | Purpose |
|-------|---------|
| [`report`](skills/report/SKILL.md) | Router skill. Directs to the correct sub-skill based on user intent. |
| [`report-init`](skills/report-init/SKILL.md) | Scaffold a fixed semi-empty PRD LaTeX workspace. Renders `report.pdf` + `report.md`. |
| [`report-brainstorming`](skills/report-brainstorming/SKILL.md) | Discuss, compare, and structure a PRD before write-back. |
| [`report-update`](skills/report-update/SKILL.md) | Write confirmed conclusions into the PRD, re-render, and run consistency checks. |
| [`report-audit`](skills/report-audit/SKILL.md) | Review PRD structure, evidence, readability, and release readiness. |
| [`report-debate`](skills/report-debate/SKILL.md) | Run structured pro/con reasoning on a disputed PRD claim or design choice. |
| [`report-goal`](skills/report-goal/SKILL.md) | Generate an autonomous agent execution prompt from a PRD report. |

## Architecture

```
User intent
    │
    ▼
┌─────────────────────────┐
│   report (router)       │  Routes to narrowest matching skill
└────┬────────┬────────┬──┘
     │        │        │
     ▼        ▼        ▼
 init    brainstorm  update    audit    debate    goal
     │        │        │
     └────────┴────────┘
              │
              ▼
    ┌──────────────────┐
    │   _shared/       │  Python scripts, reference docs,
    │                  │  LaTeX templates, checklists
    └──────────────────┘
```

## Installation

### Clone to skills directory

```bash
git clone https://github.com/xyh/report-prd-skills.git ~/.claude/skills/report-skills
```

Then use each skill directly via `/report`, `/report-init`, `/report-update`, etc.

### As a Claude Code plugin marketplace

```bash
/plugin marketplace add xyh/report-prd-skills
/plugin install report-skills
```

## PRD Types

### `research-prd`

For academic research programs. Requires:

- Research Questions and falsifiable hypotheses
- Evidence Ledger: `claim → evidence → source → limitation → confidence`
- Baseline Matrix, Ablation Matrix, Reproducibility Table, Failure-case Table
- Risks, ethics, and Go / No-Go gates

### `engineering-prd`

For software engineering specifications. Requires:

- Goals & Non-Goals
- Modular functional requirements with Acceptance Criteria
- NFR matrix, interface/data contracts
- Testing / acceptance / release plan
- Operational Readiness Matrix, phased MVP roadmap

## Shared Resources

`_shared/` contains resources used across all skills:

- **`_shared/scripts/`** — Python tools for initialization, rendering, repo scanning, self-check
- **`_shared/references/`** — PRD templates, style guides, checklists, writing guidelines
- **`_shared/assets/templates/`** — LaTeX templates, metadata schemas, outline files

## Contributing

Issues, PRs, and suggestions welcome. Before submitting a skill change:

1. Ensure `SKILL.md` has valid YAML frontmatter (`name` + `description`)
2. Keep `SKILL.md` body under 500 lines
3. Run `_shared/scripts/tests/` to verify shared scripts
4. Grep for personal paths/PII before committing

## License

Apache 2.0
