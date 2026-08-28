# Next safe action

## Checkpoint 317 complete

Current authority:

`Checkpoint 317 — SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

Verification:

- Chunk 317: `12/12 PASS`
- Checkpoint 316 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- Native core regression: `PASS`
- `PASS_REAL` promotions: `0`

Recovered safe transitions: scenario4=`8`, scenario5=`1`, scenario6=`1`, scenario7=`0`.

## Next phase

Proceed with:

`SAFE_TRANSITION_PATH_CLOSURE_AND_SCENARIO_SPECIFIC_PROOFS_V1`

Work scenario by scenario. Use only Checkpoint 317-admitted transitions plus additional transitions that independently pass the same explicit-source gate.

Priority order:

1. scenario4 — attempt to connect an explicit start to a source-backed terminal/issue path while preserving Keeper partitioning.
2. scenario5 — resolve the explicit start entity and determine whether the existing safe transition can participate in a complete path.
3. scenario6 — continue Act II → Act III → Conclusion only where explicit handoffs can be bound safely.
4. scenario7 — recover investigation causality without turning clue proximity or headings into causal edges.

A scenario remains non-`PASS_REAL` unless a complete executable start-to-terminal path is proven and all regression/firewall checks pass.
