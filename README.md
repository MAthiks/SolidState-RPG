# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 317 VERIFIED

- Checkpoint: `317`
- ID: `SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`
- Status: `VERIFIED_MILESTONE_NOT_RELEASE`
- Parent: `316 — PLAYER_AND_SCENARIO_INTERFACE_V1`
- Root runtime parent: verified Checkpoint 315 archive SHA-256 `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Chunk 317 tests: `12/12 PASS`
- Checkpoint 316 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- Native core regression: `PASS`
- `PASS_REAL` promotions: `0`

Recovered source-backed transitions:

- scenario4: `8`
- scenario5: `1`
- scenario6: `1`
- scenario7: `0`

Checkpoint 317 materializes only transitions supported by explicit source language with uniquely bound endpoints. Editorial references, ambiguous targets, semantic proximity and inferred causality fail closed. Keeper source text is not republished; public evidence uses source refs and hashes only.

## Historical scenario status invariant

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Reconstruction chain

1. Verify Checkpoint 315 original archive SHA-256.
2. Apply `patches/checkpoint316/` and require its regressions to pass.
3. Apply `patches/checkpoint317/` and run `run_tests_chunk317.py`.

## Next phase

`SAFE_TRANSITION_PATH_CLOSURE_AND_SCENARIO_SPECIFIC_PROOFS_V1`

The next work must attempt complete source-backed executable paths scenario by scenario without changing certification status until a full path is proven.

Automatic downgrade is forbidden.

See `manifest/authority_floor.json`, `patches/checkpoint317/CHECKPOINT_317.json`, `CHECKPOINT.md`, and `docs/NEXT_SAFE_ACTION.md`.
