# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 320 VERIFIED

- Checkpoint: `320`
- ID: `SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`
- Status: `VERIFIED_PATH_PROOF_MILESTONE_NOT_RELEASE`
- Parent: `319 — SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`
- Checkpoint record: `patches/checkpoint320/CHECKPOINT_320.json`
- Checkpoint record SHA-256: `d4f1ee742c546f7a8b28c3853393e7e292c0184600c99d3d1cdfe0dcba035697`
- Chunk 320 tests: `22/22 PASS`
- Checkpoint 319 current-overlay regression: `PASS`
- Checkpoint 315 core regression: `PASS`
- Native core regression: `PASS`
- Checkpoint 318 isolated reconstruction: `15/15 PASS`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL_CANDIDATE_NOT_RELEASED`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

Checkpoint 320 proves one complete, source-backed executable route for scenario5 from a player-safe invitation start to a source-authorized open epilogue resolution. Conditional branches remain conditional. No release promotion is applied by path proof.

The historical `ANTRE_PASS_REAL_CERTIFICATE.json` is retained as provenance only and is not current release authority. Scenario5 requires a separate release audit before the resolver or player scenario-selection interface may expose it as `PASS_REAL`.

Checkpoint 320 also restores the full verified Checkpoint 316 Interface V1 package exports (`ScenarioSelectionInterfaceV1`, `PlayerInterfaceV1`, `LaunchChainV1`). This is a packaging/export repair, not a behavior change.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316, 317, 318 and 319 in order.
3. Apply `patches/checkpoint320/` and require `run_tests_chunk320.py` to pass `22/22`.
4. Verify `antre.pdf` SHA-256 `4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb` when the source PDF is available.

## Next phase

`SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`

Automatic downgrade is forbidden. Keeper/source text is not republished in the public repository; checkpoint evidence stores source references and hashes only.
