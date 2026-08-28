# Next safe action

## Checkpoint 327 complete

Current authority:

`Checkpoint 327 — SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`

Verification:

- save/resume matrix: `71/71 PASS`
- player counts restored: `1, 2, 3, 4`
- all five `PASS_REAL` scenarios roundtrip: `PASS`
- exact selected scenario revalidation: `PASS`
- exact commit sequence restore: `PASS`
- next commit = saved commit + 1: `PASS`
- control map / ownership roundtrip: `PASS`
- Player Interface V1 roundtrip: `PASS`
- PV/SAN/PM/Chance/conditions/inventory roundtrip: `PASS`
- independent knowledge partitions roundtrip: `PASS`
- Keeper→Player leaks: `0`
- HMAC-SHA256 save authentication: `PASS`
- tampered / wrong-key / semantic-invalid saves: fail closed
- dirty restore target: blocked
- Checkpoint 326 regression: `334/334 PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315/native core regressions: `5/5 PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

Proceed with:

`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`

Work order:

1. Record a deterministic committed action/journal sequence before a save boundary.
2. Save through Checkpoint 327 and restore into a fresh engine.
3. Continue the sequence after resume and prove commit/event ordering is identical to an uninterrupted control run.
4. Verify roll-ledger identities, event hashes and canonical state digest before and after the save boundary.
5. Detect duplicated, skipped, reordered or modified replay events fail closed.
6. Verify replay continuity independently for 1–4 players without merging knowledge partitions.
7. Keep all five scenario certification statuses unchanged and keep Keeper data off player replay surfaces.
8. Produce a separate checkpoint before packaging the certified offline runtime / APK path.

Automatic downgrade is forbidden.
