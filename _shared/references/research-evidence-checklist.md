# Research Evidence Checklist

Use this checklist for research-style reports. Its purpose is to keep Kaiming He style review pressure concrete: every important claim must have visible evidence, limits, and reproducibility hooks.

## Required Evidence Ledger

Every central claim should be recorded in a table with this schema:

| Claim | Evidence | Source | Limitation | Confidence |
| --- | --- | --- | --- | --- |
| What the report claims | Result, derivation, citation, or repo artifact | Paper, dataset, run, commit, or script | Where the claim may fail | high / medium / low |

The canonical shorthand is:

`claim -> evidence -> source -> limitation -> confidence`

## Required Research Tables

For experimental reports, include these structures unless the report explicitly explains why they do not apply:

- baseline matrix: method, metric, dataset split, hyperparameter fairness, result, conclusion.
- ablation matrix: component changed, single variable changed, expected effect, observed effect, interpretation.
- reproducibility table: random seed, data split, training or evaluation config, hardware, command, artifact path.
- failure-case table: failure condition, observed behavior, likely cause, impact on the claim, next verification.

## Audit Questions

- Is the research problem stated in one precise sentence?
- Is the contribution boundary clear enough that a reviewer can say what is new?
- Are baselines representative and comparable?
- Does each ablation isolate one factor?
- Are negative results or failure cases visible?
- Do figures and tables report sample size, metric direction, and uncertainty when relevant?
- Does the conclusion stay within the evidence ledger?
