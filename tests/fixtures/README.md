# Research Workflow Fixtures

The regression tests build temporary fixtures for:

- valid scaffold
- valid paper placeholders
- invalid fake paper results
- spec missing harness
- stale plan spec hash

They are generated in temporary directories so each test can mutate the workspace without sharing state.
