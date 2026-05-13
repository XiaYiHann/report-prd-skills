# Reproduction Audit Policy

Reproduction audit is the gatekeeper between prior-work evidence and paper claim eligibility.

For each reproduction item, answer:

1. Was web search performed and logged?
2. Was local repo search performed and logged?
3. Was the reproduction type correctly classified?
4. If official code exists, was the upstream URL and commit recorded?
5. If no official code exists, was absence evidence recorded?
6. Are dataset, model, metric, and preprocessing aligned with the paper?
7. Are deviations explicitly recorded?
8. Can this reproduction support a paper claim, a sanity check, discussion only, or no claim?

Audit output must be machine-readable:

```yaml
audit_result:
  repro_id: ""
  status: pass | repair_required | evidence_limited | reject
  claim_support_level: full | partial | sanity_only | none
  required_repairs: []
```

Allowed claim support requires:

- valid reproduction evidence level;
- audit status passed;
- artifact hashes when artifacts exist;
- no unresolved data, metric, model, or harness defect.

`literature_only`, `official_smoke_only`, and `failed_but_informative` evidence cannot support allowed paper claims. They may support related work, motivation, limitations, or diagnostic discussion when labeled.
