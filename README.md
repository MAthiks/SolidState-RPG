# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 318 VERIFIED

- Checkpoint: `318`
- ID: `SCENARIO4_SOURCE_BACKED_PATH_CLOSURE_V1`
- Status: `VERIFIED_PATH_PROOF_MILESTONE_NOT_RELEASE`
- Parent: `317 — SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`
- Checkpoint record: `patches/checkpoint318/CHECKPOINT_318.json`
- Checkpoint record SHA-256: `2e7ca4f410475695828847eb019a21a271bdb357616343c7c1af7d9ca8e8af71`
- Chunk 318 tests: `15/15 PASS`
- Checkpoint 317/316/315 regressions: `PASS`
- Native core regression: `PASS`

Scenario 4 now has one proved source-backed executable start-to-terminal path and is therefore `PASS_REAL_CANDIDATE` only. No release promotion has been applied.

## Scenario status boundary

- scenario3: `PASS_REAL`
- scenario4: historical release status unchanged; path proof status `PASS_REAL_CANDIDATE`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 and 317 in order.
3. Apply `patches/checkpoint318/` and require `run_tests_chunk318.py` to pass.

## Next phase

`SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`

A path proof does not self-promote a scenario. The release audit must separately verify the certification prerequisites, status resolver behavior, interface selection behavior and Keeper/Player firewall before changing scenario 4 to `PASS_REAL`.

Automatic downgrade is forbidden.
