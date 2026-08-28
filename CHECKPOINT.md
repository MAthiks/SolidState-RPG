# Official checkpoint

Checkpoint ID: `SS-7.7_COC7-4.7_BASELINE`

Status: **CHECKPOINT ARTIFACT VERIFIED / IMPLEMENTATION PAYLOAD NOT YET VERIFIED**

## Versions

- Solid State: `7.7`
- CoC7 Rules Core: `4.7`

## Verified recovery artifact

GitHub stores the verified recovery backup:

`artifacts/checkpoints/SolidState_v7.7_CoC7_4.7_SoleilNoir_v1.5_Backup.zip`

SHA-256:

`70e34301ac5e322978d2c70e99f301e28ddd5b0dc2a0d96f0c5cee66b71f3cfc`

The embedded checkpoint ZIP has SHA-256:

`7d5949930affda5a2dc64c0bf555827f131b9826c33f474411d133c81157f304`

Its internal manifest hashes were independently rechecked and match the archived checkpoint metadata.

## Anti-rollback invariant

Versioned checkpoint artifacts take precedence over conversational memory whenever they conflict.

Never downgrade automatically to an older version. If the current implementation payload cannot be verified against a stored artifact/hash, report exactly: **version non confirmée**.

## Verification boundary

The archived checkpoint proves the declared restoration baseline and its metadata, including Solid State `7.7`, CoC7 Rules Core `4.7`, sentinels `SSR-MP-018` through `SSR-MP-029`, and the expected canonical rules-package hash.

It does **not** embed the full historical Solid State v7.7 implementation payload or the canonical CoC7 Rules Core v4.7 package. Those two payloads therefore remain `VERSION_NON_CONFIRMEE`.

Expected CoC7 Rules Core package:
- ID: `COC7_COMPILED_RULE_PACKAGE_4_7`
- SHA-256: `6c179ffeb3f7d78e19fddc7c1246e2357e0411d6491334761ca0a069d6a35dd7`

Referenced companion working backup:
- `Solid_State_v7.7_CoC7_v4.7_Working_Backup.zip`
- expected SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

## Promotion rule

The implementation status becomes `VERIFIED` only after the exact v7.7 engine payload and v4.7 Rules Core artifact are imported and their hashes match authoritative recorded values.
