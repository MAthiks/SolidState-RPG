# Anti-rollback policy

This repository is the authoritative version ledger for Solid State RPG.

## Rules

1. Never infer a newer payload from an older artifact.
2. Never silently substitute conversation memory for a missing versioned artifact.
3. Never lower the active version because a chat, PDF, ZIP, or prompt contains an older version number.
4. Compare incoming artifacts against `manifest/checkpoint.json` before adopting them.
5. A downgrade is allowed only when the user explicitly names the target lower version and explicitly requests the downgrade.
6. Distinguish checkpoint identity verification from implementation-payload verification.
7. A checkpoint recovery archive may be `VERIFIED_METADATA_ARTIFACT` while engine/rules payloads remain `VERSION_NON_CONFIRMEE`.
8. A component is `VERIFIED` only when the exact payload is present and its cryptographic hash matches the recorded authority.
9. If verification is impossible, retain the current authority floor and report `version non confirmée`.
10. Never overwrite an accepted checkpoint artifact; create a new checkpoint for validated upgrades.

## Development workflow

- `checkpoint/ss-7.7-coc7-4.7`: immutable baseline identity / recovery branch.
- `develop`: normal future development.
- `main`: accepted project state.

Future releases should receive an immutable version tag or dedicated checkpoint branch and a manifest with hashes.

## Current baseline

- Declared restoration target: Solid State `v7.7` + CoC7 Rules Core `v4.7`.
- Recovery backup stored in GitHub and hash-verified.
- Full v7.7 engine payload: `VERSION_NON_CONFIRMEE`.
- Full v4.7 Rules Core payload: `VERSION_NON_CONFIRMEE`.
