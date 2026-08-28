# Recovery checkpoint and authority floor

## Current authority floor

Authority lock: `SOLIDSTATE-AUTHORITY-LOCK-D5-304`

Status: **AUTHORITY FLOOR VERIFIED / CORRECTION 018 PAYLOAD NOT PRESENT**

- Solid State: `v7.8.1 candidate`
- Correction: `018`
- Scenario pair: `LSNT-V1.7-STANDALONE-1942`
- Ironman Commit: `6`
- Expected payload SHA-256: `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`
- Install generation floor: `4`
- Minimum pack version: `1.1.4`

Because the exact Correction 018 payload is not currently stored in this repository, its implementation remains **VERSION NON CONFIRMEE**. The authority floor is nevertheless retained: an older version must not silently replace it.

## Last verified restorable baseline

Checkpoint ID: `SS-7.7_COC7-4.7_BASELINE`

Status: **WORKING BACKUP VERIFIED / RECOVERY BASELINE**

- Solid State: `7.7`
- CoC7 Rules Core: `4.7`
- Working Backup: `Solid_State_v7.7_CoC7_v4.7_Working_Backup.zip`
- Verified SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

GitHub contains a verified extracted mirror under:

`artifacts/checkpoints/Solid_State_v7.7_CoC7_v4.7_Working_Backup/`

The v7.7/v4.7 baseline is the safe restoration point if newer payloads are unavailable. Restoration to it does **not** authorize lowering the authority floor or calling v7.7 the current engine.

## CoC7 documentary sources

Official Keeper Rulebook / Investigator Handbook may be used to materialize exact missing mechanical records when a newer runtime package references them but does not contain them. Such records must remain source-attributed and fail closed where the source does not support a value.

## Anti-rollback invariant

1. Newer validated authority artifacts outrank older recovery backups.
2. Missing newer payload => retain authority floor and report **VERSION NON CONFIRMEE**.
3. Never reconstruct the missing Correction 018 runtime from conversation memory.
4. A deliberate downgrade requires explicit user authorization naming the lower target.
5. Any future newer authority lock or checkpoint must be verified before replacing this floor.

See `manifest/authority_floor.json`.
