---
name: report
description: "Use when a user explicitly invokes the legacy report skill name or asks how old report-* skills map to the research execution skill family."
---

# Legacy Report Router

## Overview

This repository has migrated from the old `report-*` PRD framing to the focused `research-*` execution skill family.

Use the new skills:

- `research` (default unified controller)
- `research-init`
- `research-prd`
- `research-paper`
- `research-spec`
- `research-plan`
- `research-audit`
- `research-ppt`

Legacy mapping:

- `report-init` -> `research-init`
- `report-update` or `report-prd` -> `research-prd`
- `report-paper` -> `research-paper`
- `report-spec` -> `research-spec`
- `report-goal` -> `research-plan`
- `report-audit` -> `research-audit`
- autonomous `report-goal` style loops -> `research`

Do not continue old `docs/report` semantics unless the user explicitly asks to inspect or migrate an older workspace.
