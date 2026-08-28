# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 323 VERIFIED

- Checkpoint: `323`
- ID: `SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`
- Status: `VERIFIED_SCENARIO6_PASS_REAL_RELEASE`
- Parent: `322 — SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`
- Checkpoint record: `patches/checkpoint323/CHECKPOINT_323.json`
- Checkpoint record Git blob SHA-1: `c7c16db278e1d80d910376d2c9fa2360cb945a83`
- Release audit: `31/31 PASS`
- Checkpoint 322 isolated regression: `29/29 PASS`
- Checkpoint 321 isolated regression: `27/27 PASS`
- Checkpoint 315/native core regressions: `PASS`
- Keeper→Player leaks: `0`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

Scenario6 is promoted only through `MUSE_PASS_REAL_RELEASE_323.json`. The release gate requires the verified Checkpoint 322 path, exact repository identities, original PDF/source-layout hashes, exact source-evidence hashes, zero knowledge leaks, fail-closed tamper handling and preserved alternative/open conclusions.

`PASS_REAL` does not make one Muse ending canonical. The conditional path and alternative conclusions remain preserved.

The source collection PDF remains external to the public repository and is identified by SHA-256 `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 322 in order.
3. Apply `patches/checkpoint323/` according to `APPLY_323.md`.
4. Provide the original Aventures Effroyables PDF outside the repository via `MUSE_SOURCE_PDF`.
5. Execute Checkpoint 321/322 regressions in their frozen pre-promotion environment.
6. Require `run_tests_chunk323.py` to pass `31/31`.

## Next phase

`SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`

Automatic downgrade is forbidden.
