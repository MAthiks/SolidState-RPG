# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — VERIFIED

- Checkpoint: `315`
- ID: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Classification: `SOURCE_ROLE_RECOVERY_VALIDATED_NO_FALSE_PATH_PROMOTION`
- Original archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Original archive size: `3015801` bytes
- Embedded manifest: `1205 / 1205` entries verified
- ZIP CRC: `PASS`
- Runtime checkpoint test: `5/5 PASS`
- Native runtime core test: `5/5 PASS`
- Next phase: `SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

The original Checkpoint 315 archive has been recovered and independently verified. Project-owned checkpoint evidence is mirrored on branch `checkpoint/315-verified-original`. Proprietary/source-text material from the archive is intentionally not republished in this public repository.

## Historical scenario status invariant at Checkpoint 315

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`
- promotions_to_pass_real: `0`

Endpoint/source-role recovery alone must not create causal graph edges or promote scenarios to `PASS_REAL`.

## Earlier authority history

D5-304 / Solid State v7.8.1 candidate / Correction 018 remains historical provenance below Checkpoint 315.

## Last verified legacy recovery baseline

- Solid State engine: `v7.7`
- CoC7 Rules Core: `v4.7`
- Working Backup SHA-256: `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

This remains a legacy recovery fallback only. It must never silently replace Checkpoint 315.

## Authority order

1. Verified Checkpoint 315 original artifact
2. D5-304 authority lock / Correction 018 history
3. Verified v7.7 + CoC7 v4.7 legacy recovery baseline
4. Validated documentary sources for missing records
5. Conversation memory only as non-authoritative context

Automatic downgrade is forbidden.

See `manifest/authority_floor.json`, `manifest/recovery_gap_checkpoint315.json`, `CHECKPOINT.md`, and `docs/ANTI_ROLLBACK.md`.
