# Official development checkpoint

## Checkpoint 316 — VERIFIED INTERFACE MILESTONE

- Checkpoint: `316`
- ID: `PLAYER_AND_SCENARIO_INTERFACE_V1`
- Status: `CERTIFIED_INTERFACE_MILESTONE_NOT_RELEASE`
- Parent: `315 — SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Parent archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Checkpoint record: `patches/checkpoint316/CHECKPOINT_316.json`
- Checkpoint record SHA-256: `21b4c03215f00ce6d3ab20a2ede36012359bd82f4defce49c062cccc5ff8d345`

## Certified scope

The Checkpoint 315 TODO tasks 1–5 are now materialized and tested:

1. Scenario Selection Interface V1 — certified-status registry view; non-certified scenarios fail closed.
2. Player Interface V1 — PV, SAN, PM, Chance, wound/condition state and actual owned inventory.
3. Player decision interface — Normal/Libre uses an open `Que fais-tu ?` prompt; Facile/Assisté uses exactly 3 player-safe contextual choices + 1 free action.
4. Launch chain — scenario → validation → players → characters → `SESSION_READY`.
5. Keeper leakage prevention — explicit player-safe projection plus knowledge visibility gate.

## Verification

- `run_tests_chunk316.py`: `10/10 PASS`
- `run_tests_chunk315.py`: `5/5 PASS`
- native runtime `run_tests.py`: `5/5 PASS`
- historical scenario promotions: `0`

Patch SHA-256 values:

- `solidstate_runtime/interface_v1.py`: `a06629a976a71f339b64b90411eb33478a2b7379e38474efc2b1725d9f8dc21f`
- `run_tests_chunk316.py`: `606a1e8a9a57a273c7556bf28fbedf7f5c4df8249d31463df8728dca291cf4f9`
- `NATIVE_RUNTIME_CHUNK316_REPORT.json`: `2c626fc3710bea40d9d36d24206c29497f664ceda8a41f63e7ba52a02b39ab67`

## Scenario invariants

Checkpoint 316 does not promote scenario certification:

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Parent Checkpoint 315

The original Checkpoint 315 remains the required runtime parent and has independently verified integrity:

- archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- manifest: `1205 / 1205 PASS`
- ZIP CRC: `PASS`
- checkpoint test: `5/5 PASS`

## Next phase

`SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

Future transition recovery must use explicit source language only and must not create a causal edge or a `PASS_REAL` promotion by inference.

## Anti-rollback invariant

1. Checkpoint 316 is the current verified development authority.
2. Reconstruction requires the exact verified Checkpoint 315 parent archive plus the Checkpoint 316 patch.
3. Never silently replace 316 with 315, RC1, Correction 018, or v7.7/v4.7.
4. Scenario 4–7 status may only be promoted after source-backed executable path proof.
5. Conversation memory never outranks verified artifacts and hashes.

See `manifest/authority_floor.json` and `patches/checkpoint316/APPLY_316.md`.
