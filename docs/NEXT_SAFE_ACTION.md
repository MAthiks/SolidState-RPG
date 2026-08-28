# Next safe action

## Checkpoint 324 complete

Current authority:

`Checkpoint 324 — SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`

Verification:

- Chunk 324: `25/25 PASS`
- ten-transition source-backed investigation progression: `PASS`
- clue-to-scene anchors used as causal edges: `0 / 107`
- original source PDF SHA-256: `PASS`
- exact source-layout / source-slice hashes: `PASS`
- anti-false-causality gates: `PASS`
- Checkpoint 323 regression: `PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native core regression: `5/5 PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL_CANDIDATE_NOT_RELEASED`

## Next phase

Proceed with:

`SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`

Target scenario: L'Explorateur assassiné.

Required audit points:

1. Reverify the exact Checkpoint 324 path, original PDF identity and source-slice hashes.
2. Preserve all 107 clue-to-scene anchors as non-causal; none may become a release prerequisite merely because it is adjacent in the compiled topology.
3. Add a separate scenario7 release certificate gate; path proof alone is insufficient.
4. Require zero Keeper→Player leaks and player-safe scenario-selection output.
5. Update the status resolver only if the new certificate passes.
6. Verify scenario7 remains blocked without the release certificate and becomes selectable only with a valid certificate.
7. Tampered hashes, missing manual-language audits, clue-anchor promotion, ambiguous targets and incomplete release evidence must all fail closed.
8. Re-run current/core regressions before producing a new checkpoint.

Automatic downgrade is forbidden.
