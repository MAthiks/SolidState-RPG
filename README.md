# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 321 VERIFIED

- Checkpoint: `321`
- ID: `SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`
- Status: `VERIFIED_SCENARIO5_PASS_REAL_RELEASE`
- Parent: `320 — SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`
- Checkpoint record: `patches/checkpoint321/CHECKPOINT_321.json`
- Checkpoint record SHA-256: `d3edb5ebc7ae751b51ad1a2fd9ad417e549862f961c30580e8b9fa1168dea65a`
- Release audit: `27/27 PASS`
- Independent Antre audit: `15/15 PASS`
- Keeper→Player leaks: `0`
- Original `antre.pdf` SHA-256: `4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

Scenario5 is promoted only through the new release certificate `ANTRE_PASS_REAL_RELEASE_321.json`. The older `ANTRE_PASS_REAL_CERTIFICATE.json` remains immutable historical provenance and is explicitly forbidden as current promotion authority.

The audit re-proves the Checkpoint 320 ten-transition route from source hashes, verifies zero open source-coverage domains, confirms knowledge isolation/player-safe projection, verifies fail-closed tamper behavior, and checks that Scenario Selection Interface V1 keeps scenario5 blocked without the 321 certificate and selectable only with it.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 320 in order.
3. Apply `patches/checkpoint321/` according to `APPLY_321.md`.
4. Provide the original `antre.pdf` outside the public repository via `ANTRE_SOURCE_PDF`.
5. Require `run_tests_chunk321.py` to pass `27/27`.

## Next phase

`SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`

Automatic downgrade is forbidden. Source text is not republished in the public repository; certification evidence stores hashes and references only.
