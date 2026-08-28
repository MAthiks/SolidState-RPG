# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 327 VERIFIED

- Checkpoint: `327`
- ID: `SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`
- Status: `VERIFIED_SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE`
- Parent: `326 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`
- Checkpoint record: `patches/checkpoint327/CHECKPOINT_327.json`
- Checkpoint record Git blob SHA-1: `aa49bea4e0a3a4b6a77a7de7afd1db623f46c1bb`
- Chunk 327 tests: `71/71 PASS`
- Checkpoint 326 regression: `334/334 PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315/native core regressions: `5/5 PASS`

## Save / resume certification

Checkpoint 327 certifies save and resume for `1`, `2`, `3` and `4` players. A saved session preserves the exact selected `PASS_REAL` scenario, `SESSION_READY` interface record, player list and control map, canonical commit sequence, character records, PV/SAN/PM/Chance, wounds/conditions, mechanical registry and inventory, independent knowledge partitions, scenario/session state, roll ledger, playloop/action history and world facts.

Restore occurs into a pristine runtime database and does not invent a new commit. The next valid transaction resumes at exactly `saved_commit + 1`. All five certified scenarios survive a save → fresh engine → resume roundtrip.

Save bundles are authenticated with `HMAC-SHA256`. The authentication secret is external to the bundle and public repository. Modified payloads, wrong keys, inconsistent control maps, invalid commit ledgers, uncertified scenario identities and dirty restore targets all fail closed before player narration resumes.

Keeper knowledge is restored internally but remains absent from player projections; certified Keeper→Player leakage remains `0`.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 326 in order.
3. Apply `patches/checkpoint327/` according to `APPLY_327.md`.
4. Keep the save authentication secret external and at least 32 bytes.
5. Require `run_tests_chunk327.py` to pass `71/71`.
6. Re-run Checkpoint 326, Checkpoint 325 with its original source PDF, Checkpoint 315 and native-core regressions.

## Next phase

`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`

The next milestone must prove deterministic replay continuity across a save/resume boundary without duplicating, skipping or reordering committed events.

Automatic downgrade is forbidden.
