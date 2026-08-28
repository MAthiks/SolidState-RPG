# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current authority floor

- Engine authority floor: `Solid State v7.8.1 candidate`
- Correction: `018`
- Scenario pair: `LSNT-V1.7-STANDALONE-1942`
- Ironman Commit: `6`
- Expected payload SHA-256: `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`
- Payload presence in repository: **NO — VERSION NON CONFIRMEE**

This authority floor is recorded from the active external authority lock `SOLIDSTATE-AUTHORITY-LOCK-D5-304`. It prevents an older state from being silently treated as current.

## Last verified restorable baseline

- Solid State engine: `v7.7`
- CoC7 Rules Core: `v4.7`
- Working Backup SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

The v7.7/v4.7 checkpoint remains the verified recovery baseline. It is **not** allowed to overwrite or lower the v7.8.1/Correction 018 authority floor unless an explicit downgrade is requested.

## Authority order

1. Newest separately validated authority-lock/checkpoint artifact
2. Verified release/working backup and cryptographic hashes
3. Git history and versioned manifests
4. Validated documentary sources for missing mechanical records
5. Conversation memory only as non-authoritative context

If the current payload cannot be physically verified, report **VERSION NON CONFIRMEE** while retaining the highest verified authority floor.

See `manifest/authority_floor.json`, `CHECKPOINT.md`, and `docs/ANTI_ROLLBACK.md`.
