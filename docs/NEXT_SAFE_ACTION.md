# Next safe action

## Checkpoint 322 complete

Current authority:

`Checkpoint 322 — SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`

Verification:

- Chunk 322: `29/29 PASS`
- six-transition conditional Act I → Conclusion path: `PASS`
- original source PDF SHA-256: `PASS`
- exact source-slice hashes: `PASS`
- manual directional-language audit: `PASS`
- Keeper/Player knowledge firewall: `PASS`
- Checkpoint 321 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- native core regression: `PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL_CANDIDATE_NOT_RELEASED`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next phase

Proceed with:

`SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`

Target scenario: Muse équivoque aux yeux de sel gemme.

Required audit points:

1. Reverify the exact Checkpoint 322 path and source PDF identity.
2. Recheck scenario6 preflight and historical release-readiness evidence without treating old status files as current promotion authority.
3. Add a new scenario6 release certificate gate; path proof must not be sufficient by itself.
4. Require zero Keeper→Player leaks and preserve independent knowledge partitions.
5. Update the status resolver only if the new release certificate passes.
6. Verify Scenario Selection Interface keeps scenario6 blocked without the certificate and makes it selectable only after successful audit.
7. Verify tampered source hashes, missing manual-language audit, ambiguous route targets and incomplete release evidence all fail closed.
8. Re-run current/core regressions before producing a new checkpoint.

The release audit must preserve the scenario's alternative conclusions. `PASS_REAL` means executable/source-faithful, not that one ending is made canonical.

Automatic downgrade is forbidden.
