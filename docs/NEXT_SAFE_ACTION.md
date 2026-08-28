# Next safe action

## Checkpoint 320 complete

Current authority:

`Checkpoint 320 — SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`

Verification:

- Chunk 320: `22/22 PASS`
- Checkpoint 319 current-overlay regression: `PASS`
- Checkpoint 315 core regression: `PASS`
- Native core regression: `PASS`
- Checkpoint 318 isolated reconstruction: `15/15 PASS`
- original `antre.pdf` SHA-256 verification: `PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL_CANDIDATE_NOT_RELEASED`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next phase

Proceed with:

`SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`

Target scenario: L'Antre de l'abomination.

Required audit points:

1. Reverify the exact Checkpoint 320 path proof and source hashes.
2. Verify the source validation and any protected/player-facing boundary available for scenario5.
3. Add a separate scenario5 release certificate gate; do not reuse the historical PASS_REAL certificate as authority.
4. Update the status resolver only if the new release certificate passes.
5. Verify Scenario Selection Interface V1 keeps scenario5 blocked before the certificate and selectable only after it.
6. Verify no Keeper/source graph or hidden evidence is exposed on the player surface.
7. Verify tampered or incomplete release evidence fails closed.
8. Re-run current and core regressions before producing the next checkpoint.

Automatic downgrade is forbidden.
