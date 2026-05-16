# Reproduction Audit Policy

This policy is a framework template for downstream research epochs. In this
meta-framework repository, reproduction audit logic may be tested with fixtures,
but the repository itself must not be treated as having project-level prior-work
evidence or paper-eligible claims.

Reproduction audit is the gatekeeper between prior-work evidence and paper claim eligibility.

For each reproduction item, answer:

1. Was web search performed and logged?
2. Was local repo search performed and logged?
3. Does `BASELINE_LOCK.yaml` reference `baselines/INDEX.yaml`?
4. Do selected baselines, datasets, and borrowed experiment designs resolve to dossier cards?
5. Was the reproduction type correctly classified?
6. If official code exists, was the upstream URL and commit recorded?
7. If no official code exists, was absence evidence recorded?
8. Are dataset, model, metric, and preprocessing aligned with the paper?
9. Are deviations explicitly recorded?
10. Can this reproduction support a paper claim, a sanity check, discussion only, or no claim?

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
