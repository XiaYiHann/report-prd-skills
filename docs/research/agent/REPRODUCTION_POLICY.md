# Reproduction Policy

Every epoch must run a reproduction gate before proposed-method experiments, unless the PRD explicitly marks reproduction as not applicable and a human approval record waives the gate.

## Reproduction Types

- `official_code`: official implementation is available and can be run as the primary target.
- `forked_official_code`: official implementation needs a local fork or patch, with patch diff recorded.
- `third_party_code`: non-author implementation is used and must be labeled as lower evidence than official code.
- `faithful_reimplementation`: implementation is reconstructed from paper details, with all deviations recorded.
- `analytical_baseline`: baseline is a closed-form or simple control method with no external code dependency.
- `literature_only_not_executable`: baseline is relevant for discussion but cannot support paper claims.

## Status Values

- `pending`
- `search_done`
- `planned`
- `environment_ready`
- `smoke_passed`
- `small_scale_passed`
- `full_passed`
- `blocked_missing_code`
- `blocked_missing_data`
- `blocked_stale_dependency`
- `blocked_ambiguous_algorithm`
- `failed_metric_mismatch`
- `failed_unexplained`
- `excluded_by_human`

## Evidence Levels

- `official_full_reproduction`
- `official_small_scale_reproduction`
- `official_smoke_only`
- `third_party_reproduction`
- `faithful_reimplementation`
- `analytical_baseline`
- `literature_only`
- `failed_but_informative`

Environment failure, dependency failure, timeout, OOM, missing data, or harness failure must not be treated as method failure. Failed reproduction is useful evidence only after classification and audit; it cannot silently disappear from the baseline landscape.

Mock data must not be used as real reproduction evidence. Literature-only and smoke-only reproduction evidence can support motivation, sanity checks, or limitations, but not allowed paper claims.
