# Next safe action

## Checkpoint 316 complete

The Checkpoint 315 interface priorities 1–5 have been materialized and verified as:

`Checkpoint 316 — PLAYER_AND_SCENARIO_INTERFACE_V1`

Verification:

- Interface tests: `10/10 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- Native runtime core: `5/5 PASS`
- Scenario status promotions: `0`

## Current development authority

Use Checkpoint 316 as the current development state.

Parent reconstruction chain:

1. Verify the Checkpoint 315 source archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`.
2. Apply the exact patch under `patches/checkpoint316/` according to `APPLY_316.md`.
3. Require all Checkpoint 316 and parent regression tests to pass.

## Next compiler/runtime phase

Proceed with:

`SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

The transition layer must only materialize a transition when source language explicitly supports the relationship and both endpoints can be bound to runtime entities. Endpoint proximity, document order, headings or semantic similarity are insufficient by themselves.

## Scenario order

Apply transition recovery independently to scenarios 4–7 while preserving their current classifications by default:

- scenario4 — `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5 — `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6 — `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7 — `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

scenario3 remains `PASS_REAL` and is the regression anchor.

## Promotion gate

A scenario may be promoted only when a complete source-backed executable path is demonstrated and the player/keeper knowledge firewall remains intact.

The next checkpoint must be produced only after the Safe Transition Recovery layer passes regression without false causal-path promotion.
