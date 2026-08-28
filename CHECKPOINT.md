# Recovery checkpoint and authority audit

## Highest attested work checkpoint

An official project TODO dated 2026-08-28 identifies:

- Checkpoint: `315`
- ID: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Role: working baseline for the next interface/compiler phase

Status: **ATTESTED WORK CHECKPOINT / PAYLOAD, MANIFEST AND HASH NOT LOCATED — VERSION NON CONFIRMEE**

The TODO states that implementation status must only be granted to functions materialized in the runtime and validated by tests. It also records that scenario 3 remains `PASS_REAL`, while scenarios 4–7 must retain non-`PASS_REAL` status until a source-backed executable path is proven.

Checkpoint 315 therefore outranks older development context as a work-state marker, but it must not be represented as a verified executable checkpoint until its exact artifact, manifest and hash are recovered.

## Last fully described authority lock

Authority lock: `SOLIDSTATE-AUTHORITY-LOCK-D5-304`

Status: **AUTHORITY LOCK VERIFIED / CORRECTION 018 PAYLOAD NOT PRESENT**

- Solid State: `v7.8.1 candidate`
- Correction: `018`
- Scenario pair: `LSNT-V1.7-STANDALONE-1942`
- Ironman Commit: `6`
- Expected payload SHA-256: `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`
- Authority-lock SHA-256: `5d82126e8e28d64c57f0ecb427766ac70a4b1746a228b60cff9e8ddec3ea893e`

The Correction 018 runtime is not present in this repository, so its executable implementation remains **VERSION NON CONFIRMEE**.

## Last verified restorable baseline

Checkpoint ID: `SS-7.7_COC7-4.7_BASELINE`

Status: **WORKING BACKUP VERIFIED / RECOVERY BASELINE**

- Solid State: `7.7`
- CoC7 Rules Core: `4.7`
- Working Backup: `Solid_State_v7.7_CoC7_v4.7_Working_Backup.zip`
- Verified SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

GitHub contains a verified extracted mirror under:

`artifacts/checkpoints/Solid_State_v7.7_CoC7_v4.7_Working_Backup/`

This is a safe restoration payload, not the current development state.

## Later runtime evidence

A separately recovered `Solid State Native Runtime — Big Chunk 1` README demonstrates that an executable OOP runtime slice existed after the older specification-only phase, with SQLite persistence, atomic transactions, canonical state, Ironman commits, hash-chained roll ledger, characters and party attachment. The README also explicitly lists incomplete CoC7 rules, native equipment resolver, temporal registry, external verified RNG and full canonical scenario execution as not yet implemented. No proven artifact chain currently links this runtime slice to Checkpoint 315, so it is preserved as provenance evidence only.

## CoC7 documentary sources

Official Keeper Rulebook / Investigator Handbook may be used to resolve exact missing mechanical records. Such records must be source-attributed and fail closed where the source does not support a value. Documentary recovery cannot be used to fabricate a missing engine/checkpoint payload.

## Anti-rollback invariant

1. Exact verified Checkpoint 315 artifact, if recovered, has priority over the older states below.
2. Until then, retain 315 as the highest attested work-state marker and D5-304 as the last fully described authority lock.
3. Missing higher payload => report **VERSION NON CONFIRMEE**; never silently substitute v7.7, RC1 or Correction 018 as the current runtime.
4. v7.7/v4.7 remains the last physically verified recovery baseline.
5. Never reconstruct Checkpoint 315 or Correction 018 from conversation memory.
6. A deliberate downgrade requires explicit user authorization naming the lower target.

See `manifest/authority_floor.json` and `manifest/recovery_gap_checkpoint315.json`.
