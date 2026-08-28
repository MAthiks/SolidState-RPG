# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 324 VERIFIED

- Checkpoint: `324`
- ID: `SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`
- Status: `VERIFIED_PATH_PROOF_MILESTONE_NOT_RELEASE`
- Parent: `323 — SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`
- Checkpoint record: `patches/checkpoint324/CHECKPOINT_324.json`
- Checkpoint record Git blob SHA-1: `7aa9fdef7297bfc14e33897a4659c4671a8732ab`
- Chunk 324 tests: `25/25 PASS`
- Checkpoint 323 regression: `PASS`
- Checkpoint 315 regression: `5/5 PASS`
- Native core regression: `5/5 PASS`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL_CANDIDATE_NOT_RELEASED`

Checkpoint 324 proves one complete source-backed investigation progression path for scenario7 using ten explicit narrative/conditional transitions. It deliberately uses `0` of the `107` clue-to-scene anchors as causal edges. Clues remain evidence available to investigation, not an automatically ordered route.

The source collection PDF remains external to the public repository and is identified by SHA-256 `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 323 in order.
3. Apply `patches/checkpoint324/` according to `APPLY_324.md`.
4. Provide the original Aventures Effroyables PDF outside the repository via `EXPLORATEUR_SOURCE_PDF`.
5. Require `run_tests_chunk324.py` to pass `25/25`.
6. Re-run Checkpoint 323, Checkpoint 315 and native-core regressions.

## Next phase

`SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`

Automatic downgrade is forbidden. Scenario7 remains blocked in the certified player scenario-selection interface until the separate release audit succeeds.
