# Research Loop Fixtures

The unified `/research` tests build temporary workspaces for the main controller transitions:

- empty workspace initialization
- PRD missing or not human-approved
- PRD-approved workspace with missing spec
- spec-ready workspace with no active plan
- active plan incomplete, complete, blocked, or stale
- PRD ambiguity requiring human review
- open pivot or negative-result blockers

The fixtures are generated in temporary directories so tests can mutate state, queues, plans, audits, and insight files independently.
