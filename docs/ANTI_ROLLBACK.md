# Anti-rollback policy

This repository is the authoritative version ledger for Solid State RPG.

## Rules

1. Never infer a newer payload from an older artifact.
2. Never silently substitute conversation memory for a missing versioned artifact.
3. Never lower the active version because a chat, PDF, ZIP, or prompt contains an older version number.
4. Compare incoming artifacts against `manifest/checkpoint.json` before adopting them.
5. A downgrade is allowed only when the user explicitly names the target lower version and explicitly requests the downgrade.
6. A version is `VERIFIED` only when the exact artifact is present and its cryptographic hash is recorded.
7. If verification is impossible, retain the current authority floor and mark the relevant component `VERSION_NON_CONFIRMEE`.

## Development workflow

- `checkpoint/ss-7.7-coc7-4.7`: immutable baseline identity / recovery branch.
- `develop`: normal future development.
- `main`: accepted project state.

Future releases should receive an immutable version tag or dedicated checkpoint branch and a manifest with hashes.
