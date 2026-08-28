# Official development checkpoint

## Checkpoint 317 — VERIFIED SAFE TRANSITION MILESTONE

- Checkpoint: `317`
- ID: `SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`
- Parent: `316 — PLAYER_AND_SCENARIO_INTERFACE_V1`
- Root runtime parent: verified Checkpoint 315 archive SHA-256 `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Checkpoint record: `patches/checkpoint317/CHECKPOINT_317.json`

## Certified scope

Checkpoint 317 adds a fail-closed `SafeTransitionEvidenceGate` and `SafeTransitionRecoveryV1` layer. A transition is executable only when source language is explicit, both endpoints are bound, the target is unique, the source reference/hash is present and the authority class is accepted.

Recovered safe transitions:

- scenario4: `8`
- scenario5: `1`
- scenario6: `1`
- scenario7: `0`

No scenario status was promoted.

## Verification

- `run_tests_chunk317.py`: `12/12 PASS`
- Checkpoint 316 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- native runtime regression: `PASS`
- historical scenario promotions: `0`

## Scenario invariants

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Source-protection invariant

Keeper/source text is not republished in the public repository. Checkpoint evidence contains source references and hashes only. Editorial references, ambiguous targets and inferred causal links fail closed.

## Next phase

`SAFE_TRANSITION_PATH_CLOSURE_AND_SCENARIO_SPECIFIC_PROOFS_V1`

Attempt path closure independently for scenarios 4–7. Promotion is allowed only after a complete source-backed executable path is proven with the Keeper/Player firewall intact.

## Anti-rollback invariant

1. Checkpoint 317 is the current verified development authority.
2. Reconstruction requires verified Checkpoint 315 + Checkpoint 316 + Checkpoint 317 patches in order.
3. Never silently substitute 316, 315, RC1, Correction 018, or v7.7/v4.7 as current.
4. Conversation memory never outranks verified artifacts.
