# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 319 VERIFIED

- Checkpoint: `319`
- ID: `SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`
- Status: `VERIFIED_SCENARIO4_PASS_REAL_RELEASE`
- Parent: `318 — SCENARIO4_SOURCE_BACKED_PATH_CLOSURE_V1`
- Checkpoint record: `patches/checkpoint319/CHECKPOINT_319.json`
- Checkpoint record SHA-256: `12d341468385d63e092f31c12de2b0715e27b3f305823cf6fcee5e750b9afc0d`
- Chunk 319 release audit: `18/18 PASS`
- Checkpoint 315 regression: `PASS`
- Native core regression: `PASS`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

Scenario 4 is promoted only through the separate release certificate `BRUME_PASS_REAL_RELEASE_319.json`. The historical `BRUME_FINAL_CLASSIFICATION.json` is preserved unchanged as provenance.

The release audit verified dual-source preflight, zero Keeper→Player leaks, protected release readiness, executable start-to-terminal path, resolver behavior, certification eligibility, fail-closed tamper handling and player interface selection.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316, 317 and 318 in order.
3. Apply `patches/checkpoint319/` and require `run_tests_chunk319.py` to pass `18/18`.

## Next phase

`SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`

Automatic downgrade is forbidden. Keeper/source text is not republished in the public repository; release evidence stores source references and hashes only.
