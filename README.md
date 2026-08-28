# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Highest current work-checkpoint evidence

An official project TODO identifies the working baseline as:

- Checkpoint: `315`
- ID: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`

The exact Checkpoint 315 payload, manifest and SHA-256 have **not** yet been located in the repository or available recovery files. Therefore Checkpoint 315 is an **attested work checkpoint / authority ceiling**, not a verified executable runtime. Status: **VERSION NON CONFIRMEE**.

No older payload may be promoted over this evidence, and Checkpoint 315 must not be reconstructed from conversation memory.

## Last fully described authority lock

`SOLIDSTATE-AUTHORITY-LOCK-D5-304` records:

- Engine: `Solid State v7.8.1 candidate`
- Correction: `018`
- Scenario pair: `LSNT-V1.7-STANDALONE-1942`
- Ironman Commit: `6`
- Expected payload SHA-256: `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`
- Authority-lock SHA-256: `5d82126e8e28d64c57f0ecb427766ac70a4b1746a228b60cff9e8ddec3ea893e`

The Correction 018 payload is not present in this repository, so its implementation also remains **VERSION NON CONFIRMEE**.

## Last verified restorable baseline

- Solid State engine: `v7.7`
- CoC7 Rules Core: `v4.7`
- Working Backup SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

This is the last physically verified restoration baseline. It must not be mislabeled as the current development state.

## Authority order

1. Exact Checkpoint 315 artifact, if recovered and hash-verified
2. D5-304 authority lock / Correction 018 floor
3. Verified v7.7 + CoC7 v4.7 recovery baseline
4. Validated documentary sources for missing records
5. Conversation memory only as non-authoritative context

Missing higher payloads retain their authority position but are reported **VERSION NON CONFIRMEE**. Automatic downgrade is forbidden.

See `manifest/authority_floor.json`, `CHECKPOINT.md`, and `docs/ANTI_ROLLBACK.md`.
