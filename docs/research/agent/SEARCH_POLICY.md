# Search Policy

This policy is part of the research-loop framework contract for generated
downstream research workspaces. It is not a repo-local mandate to bind this
meta-framework repository to a concrete project, dataset, baseline, metric, or
paper claim.

Search is mandatory before tasks that can change the research evidence base:

1. project start;
2. version start;
3. baseline selection;
4. reproduction;
5. dataset, model, or metric selection;
6. unexpected positive or negative result interpretation;
7. pivot proposal;
8. paper binding.

Search must cover both external and local evidence:

- web literature;
- official code;
- third-party implementations;
- datasets;
- model checkpoints;
- known issues, forks, and reproduction notes;
- current local repository state.

Search is not required for:

1. pure formatting;
2. local bug fix under locked `SPEC.yaml`;
3. rerunning the same harness;
4. artifact path repair;
5. writing reports from existing logs.

If web access is unavailable, create `search/search_blocker.md`, mark the task as blocked unless the task is explicitly search-optional, and do not invent papers, repositories, datasets, metrics, or model capabilities.

Absence evidence is required when official code, data, or model checkpoints cannot be found. Record the query, checked sources, timestamp, and confidence level.

The system should prefer sufficient logged search to under-searching for reproduction, dataset, model, metric, and baseline decisions. Search must still be bounded and decision-oriented:

- default query minimum: 6;
- default query maximum: 20;
- stop when official code status, dataset availability, metric definition, and at least three candidate baselines or justified scarcity are resolved.

Baseline search has three artifact layers:

1. `search/` records raw discovery and absence evidence.
2. `baselines/INDEX.yaml` records curated baseline, paper, dataset, experiment-design, and reuse-decision cards under `baselines/Bxxx/`.
3. `BASELINE_LOCK.yaml` records the final version-level decision and must reference the selected dossier cards.
