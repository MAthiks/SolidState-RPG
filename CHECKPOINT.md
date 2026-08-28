# Official checkpoint

Checkpoint ID: `SS-7.7_COC7-4.7_BASELINE`

Status: **DECLARED / PAYLOAD NOT YET VERIFIED**

## Versions

- Solid State: `7.7`
- CoC7 Rules Core: `4.7`

## Anti-rollback invariant

Versioned checkpoint artifacts take precedence over conversational memory whenever they conflict.

Never downgrade automatically to an older version. If the current payload cannot be verified against a stored artifact/hash, report exactly: **version non confirmée**.

## Verification state

The library contains official CoC7 source PDFs and older/newer Solid State project artifacts, but an exact recoverable v7.7 + v4.7 packaged payload was not located during repository bootstrap. Therefore this checkpoint records the declared version identity without inventing engine/rules content.

## Next promotion rule

This checkpoint becomes `VERIFIED` only after exact v7.7 and v4.7 artifacts are imported, hashed, and referenced from `manifest/checkpoint.json`.
