# Official development checkpoint

## Checkpoint 315 — VERIFIED

- Checkpoint: `315`
- ID/version: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Classification: `SOURCE_ROLE_RECOVERY_VALIDATED_NO_FALSE_PATH_PROMOTION`
- Source archive: `SolidState_NATIVE_RUNTIME_BIG_CHUNK_315_SOURCE_ROLE_ENDPOINT_RECOVERY_CHECKPOINT.zip`
- Source archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Archive size: `3015801` bytes
- `CHECKPOINT_315.json` SHA-256: `593fb299c62fdb1a4b4daab6abe4b397c59d9dd931537c8c929c6e8efe05bfaa`
- Embedded `MANIFEST_SHA256.json` SHA-256: `3e2c82e0628424844217ee0773ac2c65caf6e72d84f9d33f70281432ff30ebef`
- Embedded manifest verification: `1205 / 1205 PASS`
- ZIP CRC: `PASS`

## Executed verification

- `run_tests_chunk313.py`: `3/3 PASS`
- `run_tests_chunk314.py`: `1/1 PASS`
- `run_tests_chunk315.py`: `5/5 PASS`
- base native runtime `run_tests.py`: `5/5 PASS`

Checkpoint 315 is therefore the current verified development authority. It is no longer an evidence-only checkpoint.

## Checkpoint 315 invariants

- scenario3: `PASS_REAL`
- scenario4: `COMPILED_PROTECTED_NOT_PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`
- runtime scenario-name leaks: none
- promotions to `PASS_REAL`: `0`

Role/endpoint recovery must not by itself manufacture causal transitions or promote scenario status.

## Next phase

`SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

Development must resume from Checkpoint 315 and preserve the historical scenario-status invariants until source-backed executable transitions are proven.

## GitHub preservation boundary

Project-owned checkpoint evidence is mirrored under branch:

`checkpoint/315-verified-original`

The complete binary ZIP is not republished in the public repository because the archive contains source-text material that must remain non-public. GitHub records the original archive hash and verified checkpoint evidence instead.

## Earlier authority history

### D5-304

- Solid State `v7.8.1 candidate`
- Correction `018`
- Ironman Commit `6`
- expected payload SHA-256 `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`

This is historical provenance below Checkpoint 315.

### Legacy recovery fallback

- Solid State `7.7`
- CoC7 Rules Core `4.7`
- Working Backup SHA-256 `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

This remains a legacy recovery fallback, not the current engine state.

## Anti-rollback invariant

1. Checkpoint 315 is the current verified development authority.
2. Never silently replace it with RC1, Correction 018, or v7.7/v4.7.
3. Scenario 4–7 status may only be promoted after source-backed executable path proof.
4. Conversation memory never outranks verified artifacts and hashes.
5. Any later checkpoint must be independently verified before replacing 315.

See `manifest/authority_floor.json` and `manifest/recovery_gap_checkpoint315.json`.
