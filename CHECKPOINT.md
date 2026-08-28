# Official checkpoint

Checkpoint ID: `SS-7.7_COC7-4.7_BASELINE`

Status: **WORKING BACKUP VERIFIED / IMPLEMENTATION PAYLOAD NOT YET FULLY VERIFIED**

## Versions

- Solid State: `7.7`
- CoC7 Rules Core: `4.7`

## Verified recovery artifacts

### Recovery checkpoint backup

`artifacts/checkpoints/SolidState_v7.7_CoC7_4.7_SoleilNoir_v1.5_Backup.zip`

SHA-256:

`70e34301ac5e322978d2c70e99f301e28ddd5b0dc2a0d96f0c5cee66b71f3cfc`

Embedded checkpoint ZIP SHA-256:

`7d5949930affda5a2dc64c0bf555827f131b9826c33f474411d133c81157f304`

### Working Backup

Source archive:

`Solid_State_v7.7_CoC7_v4.7_Working_Backup.zip`

Verified SHA-256:

`2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

The source archive has been independently verified. GitHub contains a verified extracted mirror under:

`artifacts/checkpoints/Solid_State_v7.7_CoC7_v4.7_Working_Backup/`

The binary ZIP itself is not committed because the connector refused the binary write. `ARCHIVE_VERIFICATION.json` records the exact source-archive hash and the hashes of the extracted files. One extracted test-procedure file could not be mirrored by the connector; its verified hash is preserved in the verification manifest.

## Anti-rollback invariant

Versioned checkpoint artifacts take precedence over conversational memory whenever they conflict.

Never downgrade automatically to an older version. If the current implementation payload cannot be verified against a stored artifact/hash, report exactly: **version non confirmée**.

## Verification boundary

The recovery artifacts verify the declared baseline identity Solid State `7.7` + CoC7 Rules Core `4.7`, the continuity snapshot, sentinels `SSR-MP-018` through `SSR-MP-029`, and the expected canonical rules-package hash.

They do **not** contain the complete canonical CoC7 Rules Core v4.7 package. The exact implementation payload therefore remains `VERSION_NON_CONFIRMEE` until the canonical package itself is present and hash-verified.

Expected CoC7 Rules Core package:
- ID: `COC7_COMPILED_RULE_PACKAGE_4_7`
- SHA-256: `6c179ffeb3f7d78e19fddc7c1246e2357e0411d6491334761ca0a069d6a35dd7`

## Promotion rule

The implementation status becomes `VERIFIED` only after the exact v7.7 engine payload and v4.7 Rules Core artifact are imported and their hashes match authoritative recorded values.
