# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Active checkpoint

- Solid State engine: `v7.7`
- CoC7 Rules Core: `v4.7`
- Checkpoint policy: anti-rollback
- Repository authority: GitHub history + checkpoint manifest

The version identifiers above are the declared baseline. The exact historical v7.7 / v4.7 payload has not yet been recovered from a verifiable artifact, so implementation payloads remain **VERSION NON CONFIRMEE** until imported and hashed.

## Authority order

1. Verified checkpoint artifact + hash stored in this repository
2. Git commit history / protected checkpoint branch
3. Current documented project state
4. Conversation memory only as non-authoritative context

A lower or older version MUST NOT silently replace a verified newer checkpoint.

See `CHECKPOINT.md` and `docs/ANTI_ROLLBACK.md`.
