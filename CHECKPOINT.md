# Official development checkpoint

## Checkpoint 327 — VERIFIED SAVE / RESUME

- Checkpoint: `327`
- ID: `SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`
- Parent: `326 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`
- Record: `patches/checkpoint327/CHECKPOINT_327.json`
- Record Git blob SHA-1: `aa49bea4e0a3a4b6a77a7de7afd1db623f46c1bb`

## Certified scope

Checkpoint 327 certifies persistent save/resume of the selected scenario and full Player Interface V1 state for 1–4 players. It preserves the exact `SESSION_READY` record and control map, canonical commit sequence, character ownership, PV/SAN/PM/Chance, conditions, inventory, knowledge partitions and the runtime ledgers needed for later replay continuity.

All five scenarios currently released as `PASS_REAL` complete a save → fresh engine → restore roundtrip without silent reselection or downgrade. The selected scenario is revalidated against the current certified scenario registry before restore is allowed.

Save integrity is authenticated with HMAC-SHA256 using a secret that is never embedded in the save bundle or public repository. Restore is allowed only into a pristine database. Tampering, wrong authentication secret, inconsistent player→character ownership, invalid commit ledger and uncertified scenario identity fail closed.

## Verification

- `run_tests_chunk327.py`: `71/71 PASS`
- supported player counts: `1, 2, 3, 4`
- five `PASS_REAL` scenario roundtrips: `PASS`
- exact saved commit restored: `PASS`
- next transaction = saved commit + 1: `PASS`
- Player Interface V1 roundtrip: `PASS`
- mechanics / inventory / conditions roundtrip: `PASS`
- independent knowledge partitions roundtrip: `PASS`
- Keeper→Player leaks after resume: `0`
- tamper and wrong-key cases: fail closed
- authenticated semantic inconsistency cases: fail closed
- Checkpoint 326 regression: `334/334 PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native core regression: `5/5 PASS`

## Scenario status after Checkpoint 327

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`

## Anti-rollback invariant

1. Checkpoint 327 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 327 in order.
3. Resume requires an authenticated save and a currently `PASS_REAL` selected scenario.
4. Restore must not create, skip or renumber the saved canonical commit.
5. The save authentication secret remains external to the bundle and repository.
6. Player knowledge partitions remain independent and Keeper knowledge stays off player surfaces.
7. Conversation memory never outranks verified artifacts and hashes.
