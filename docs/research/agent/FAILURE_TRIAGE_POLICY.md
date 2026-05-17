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

---

## 7. Method Scope Contraction (method paper only)

### Trigger
An experiment fails, but the failure is scene-specific rather than method-contradicting, and the epoch's `PAPER_TYPE.yaml` declares `paper_type: method`.

### Required triage questions
1. Does the failure persist after environment/execution/harness repair? (if no → not scope contraction; repair and rerun)
2. Does the same method configuration succeed on other tasks/scenes with `method_validity: maintained`? (if no → may be method flaw)
3. Can the failure be explained by a known limitation of the method (e.g., requires symbolic parser, requires step structure, requires formalizable task)? (if yes → scope contraction)

### Action (mandatory; Agent may not bypass)
- **Do NOT** mark the method claim as `falsified`.
- **Do NOT** stop method-level experiments.
- **Do NOT** downgrade a `method` claim into a `finding` claim.
- **Do NOT** let the failing agent self-assess `method_validity`. The triage must be performed by an **independent review subagent**.
- Update `APPLICABILITY_MAP.yaml` with the new boundary (after subagent review confirms scope contraction).
- Continue method validation on remaining applicable scenes (if subagent review concludes `method_validity: maintained`).
- Report scope contraction as a **CONTRIBUTION** in `runs/TASK_XXX_scope_contraction.md`, not as a limitation or failure.
- If no `APPLICABILITY_MAP.yaml` exists, create it under `docs/research/{CURRENT}/APPLICABILITY_MAP.yaml`.

### Hard rule: Subagent Review Trigger (method paper only)
For `paper_type: method`, every experiment failure **must** trigger a subagent review before any state change:

1. **The failing agent halts**. It may NOT mark the task `completed`, `blocked`, or `failed_harness`.
2. **The failing agent produces a review package** at `runs/TASK_XXX_review_package/`:
   - `failure_log.md`: stdout/stderr tail, exception traceback, exit code
   - `code_diff.txt`: git diff of all modified files since last successful run
   - `test_manifest.yaml`: L0-L2 results (if any were run)
   - `context.yaml`: current `PAPER_TYPE.yaml`, `APPLICABILITY_MAP.yaml`, task contract
3. **Controller spawns `research-audit` subagent** with explicit instruction:  
   "You are an independent reviewer. The main agent has failed an experiment. Your job is to assess whether this failure weakens the **core method** or only narrows the **applicable scope**. You must not take the main agent's self-assessment at face value."
4. **Subagent outputs** `runs/TASK_XXX_subagent_review.md` containing:
   - `failure_classification`: environment | execution | harness | scene_specific | method_contradicting
   - `method_validity_assessment`: maintained | weakened | falsified
   - `scope_contraction_recommended`: true | false
   - `excluded_scenes`: [] (if scope contraction)
   - `continued_scenes`: [] (where method should still be validated)
   - `falsification_risk`: none | low | high
   - `review_confidence`: low | medium | high
   - `dissent_note`: "" (if subagent disagrees with main agent's preliminary classification)
5. **Main agent may only proceed after subagent review is present**. The main agent must:
   - Copy subagent conclusions into `METHOD_DEFENSE.yaml`
   - If it disagrees with the subagent, it must escalate to human review (write `HUMAN_REVIEW_REQUESTS.yaml`) rather than override.

### Hard rule for method paper stop conditions
For `paper_type: method`, the stop condition is **"all applicable scenes exhausted or method falsified by subagent-audited review"**, not "same failure twice".
- Two failures on the **same scene** do NOT stop the method pipeline.
- Two failures on **different scenes** with different root causes do NOT stop the method pipeline.
- Method pipeline stops only when:
  1. The subagent review concludes `method_validity: falsified`; OR
  2. Every scene in `APPLICABILITY_MAP.yaml` has been tried and failed (each with subagent review); OR
  3. A human explicitly requests stop.

### Output artifact sequence
After any method-paper experiment failure, the following artifacts must exist **in order** before the task can advance:

1. `runs/TASK_XXX_review_package/failure_log.md` (by failing agent)
2. `runs/TASK_XXX_subagent_review.md` (by review subagent)
3. `docs/research/{CURRENT}/METHOD_DEFENSE.yaml` (by main agent, copying subagent conclusions)

```yaml
# METHOD_DEFENSE.yaml schema
method_validity: maintained | weakened | falsified
reviewed_by: subagent  # must be "subagent", not "self"
subagent_review_ref: runs/TASK_XXX_subagent_review.md
scope_contraction:
  excluded_scenes: []
  reason: ""
  contribution_note: ""  # why this contraction is scientifically valuable
next_applicable_scenes: []
falsification_risk: none | low | high
```
No task may be marked `completed` after a method-paper experiment failure until **all three artifacts** are present.
