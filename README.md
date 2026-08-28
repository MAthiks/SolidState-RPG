# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 316 VERIFIED

- Checkpoint: `316`
- ID: `PLAYER_AND_SCENARIO_INTERFACE_V1`
- Status: `CERTIFIED_INTERFACE_MILESTONE_NOT_RELEASE`
- Parent checkpoint: `315 — SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Parent archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Checkpoint 316 record SHA-256: `21b4c03215f00ce6d3ab20a2ede36012359bd82f4defce49c062cccc5ff8d345`
- Interface tests: `10/10 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- Native runtime core regression: `5/5 PASS`
- Next phase: `SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

Checkpoint 316 materializes and certifies the Checkpoint 315 TODO tasks 1–5: scenario selection, player status interface, 3 choices + 1 free action in assisted mode, the scenario → validation → players → characters → session-ready launch chain, and Keeper-data leakage prevention.

The patch is stored under `patches/checkpoint316/` and is reproducible only on the verified Checkpoint 315 parent archive. The old RC1 `develop` branch is not runtime authority.

## Historical scenario status invariant

Checkpoint 316 does not promote any scenario status:

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`
- promotions_to_pass_real: `0`

## Parent Checkpoint 315

The original Checkpoint 315 archive remains the verified parent runtime:

- archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- manifest verification: `1205 / 1205 PASS`
- ZIP CRC: `PASS`
- Checkpoint 315 test: `5/5 PASS`

Project-owned evidence is mirrored on `checkpoint/315-verified-original`. Proprietary/source-text material from the archive is intentionally not republished in this public repository.

## Legacy recovery baseline

- Solid State engine: `v7.7`
- CoC7 Rules Core: `v4.7`
- Working Backup SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

This remains a legacy recovery fallback only.

## Authority order

1. Verified Checkpoint 316 interface milestone
2. Verified Checkpoint 315 original runtime artifact
3. D5-304 / Correction 018 history
4. Verified v7.7 + CoC7 v4.7 legacy recovery baseline
5. Conversation memory only as non-authoritative context

Automatic downgrade is forbidden.

See `manifest/authority_floor.json`, `patches/checkpoint316/CHECKPOINT_316.json`, `CHECKPOINT.md`, and `docs/ANTI_ROLLBACK.md`.
