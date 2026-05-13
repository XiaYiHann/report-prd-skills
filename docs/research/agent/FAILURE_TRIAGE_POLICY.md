# Failure Triage Policy

A failed task must be classified before any research conclusion is made.

## Classes

### 1. Environment Failure

- dependency missing
- CUDA/device unavailable
- file path invalid
- permission or local toolchain unavailable

### 2. Execution Failure

- script crash
- exception
- timeout
- OOM
- process exits before producing declared outputs

### 3. Harness Failure

- test predicate failed
- output missing
- artifact schema invalid
- success predicate cannot be evaluated

### 4. Spec Gap

- command undefined
- dataset unspecified
- metric not operationalized
- baseline source unclear
- allowed files or artifact paths missing

### 5. PRD Ambiguity

- research question unclear
- hypothesis is not falsifiable
- pass, block, or falsification condition missing
- Gate schedule or Harness table is underspecified

### 6. Research Falsification Candidate

Allowed only if:

- harness ran successfully;
- outputs are valid;
- artifacts and hashes are recorded;
- the result contradicts a predefined falsification condition;
- no execution, harness, environment, spec, or PRD ambiguity is still unresolved.

### 7. Confirmed Research Falsification

Allowed only after adversarial audit.

The audit must rule out code defects, data leakage, metric bugs, harness bugs, environment failures, and PRD/SPEC ambiguity before the gate can be marked `falsified`.

## State Mapping

`failed_execution` maps to environment or execution repair.  
`failed_harness` maps to harness repair or task-level failure.  
`research_falsification_candidate` maps to audit required.  
`confirmed_research_falsification` maps to gate `falsified` only after audit.

Never interpret `failed_execution` or `failed_harness` as confirmed research falsification.
