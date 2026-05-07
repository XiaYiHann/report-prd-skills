# Repository Scan Playbook

Use this playbook when the report must explain a local repository.

## Step 1: Deterministic First Pass

Run:

```bash
python3 scripts/scan_repo.py /absolute/path/to/repo
```

Use that output to identify high-value paths before opening files in detail.

## Step 2: Prioritize by Signal

Read these paths first when they exist:

- `README*`
- `docs/`
- `specs/`, `plans/`, `architecture/`
- core source directories such as `src/`, `app/`, `simulation/`, `packages/`
- `tests/`
- paper or report sources such as `.tex`, `.bib`, figure directories
- dependency manifests and runtime configs

## Step 3: Split the Work

If subagents are available, split the scan by responsibility:

- architecture and code paths
- docs and specifications
- tests and behavior guarantees
- paper sources, figures, and datasets

Do not send the whole repo to one subagent unless the repository is tiny.

## Step 4: Extract Report Material

Translate the scan into report-ready material:

- problem statement
- module boundaries
- algorithm steps
- configuration or parameter entry points
- tests that define hard constraints
- outputs, figures, and evidence artifacts

## Step 5: Ignore Noise

Common noise paths:

- `.git/`
- virtual environments
- build outputs
- caches
- generated PDFs, logs, and archives

Only include them if the user explicitly asks for build artifacts or release packaging.
