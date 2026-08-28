# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 325 VERIFIED

- Checkpoint: `325`
- ID: `SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`
- Status: `VERIFIED_SCENARIO7_PASS_REAL_RELEASE`
- Parent: `324 — SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`
- Checkpoint record: `patches/checkpoint325/CHECKPOINT_325.json`
- Checkpoint record Git blob SHA-1: `9cd353b6ba666d5bd44c7b8e81adf47c7fc7c6e4`
- Release audit: `31/31 PASS`
- Checkpoint 324 isolated regression: `25/25 PASS`
- Checkpoint 323 isolated regression: `31/31 PASS`
- Checkpoint 315/native core regressions: `5/5 PASS`
- Keeper→Player leaks: `0`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

Checkpoint 325 promotes scenario7 only through `EXPLORATEUR_PASS_REAL_RELEASE_325.json`. The release gate re-proves the ten-transition Checkpoint 324 path, requires the original PDF/source-layout identities, preserves all `107` clue-to-scene anchors as non-causal, uses `0` clue anchors as path edges, verifies zero Keeper→Player leakage, and fails closed on tampered release evidence.

The source collection PDF remains external to the public repository and is identified by SHA-256 `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 324 in order.
3. Apply `patches/checkpoint325/` according to `APPLY_325.md`.
4. Provide the original Aventures Effroyables PDF outside the repository via `EXPLORATEUR_SOURCE_PDF`.
5. Require `run_tests_chunk325.py` to pass `31/31`.
6. Re-run Checkpoints 324 and 323 in their frozen pre-release environments and require `25/25` and `31/31`.
7. Require Checkpoint 315 and native-core regressions to remain `5/5 PASS`.

## Next phase

`MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`

The next milestone validates 1–4 independent players, control mappings and knowledge partitions before save/resume and Strict Replay integration.

Automatic downgrade is forbidden.
