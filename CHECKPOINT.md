# Official development checkpoint

## Checkpoint 325 — VERIFIED SCENARIO 7 RELEASE

- Checkpoint: `325`
- ID: `SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`
- Parent: `324 — SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`
- Record: `patches/checkpoint325/CHECKPOINT_325.json`
- Record Git blob SHA-1: `9cd353b6ba666d5bd44c7b8e81adf47c7fc7c6e4`

## Certified scope

Checkpoint 325 performs the release audit required by Checkpoint 324 and promotes only scenario7 — L’Explorateur assassiné — to `PASS_REAL`.

The audit independently re-proves the ten-transition source-backed investigation path, verifies the original source PDF and source-layout identities, preserves the historical investigation topology, requires `0 / 107` clue-to-scene anchors as causal edges, verifies zero Keeper→Player leakage, tests resolver/interface promotion, and rejects tampered release evidence fail-closed.

## Verification

- `run_tests_chunk325.py`: `31/31 PASS`
- Checkpoint 324 isolated regression: `25/25 PASS`
- Checkpoint 323 isolated regression: `31/31 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native runtime regression: `5/5 PASS`
- original source PDF SHA-256: `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143` — `PASS`
- source-layout SHA-256: `7b00a96cb2ab83e40b576bd0cb2e96d369393f6ce714c1d59a4a4b2f6a3265e3` — `PASS`
- aggregate source-evidence digest: `PASS`
- Keeper→Player leaks: `0`
- clue-anchor causal edges used: `0`
- Scenario Selection Interface: scenario7 selectable only with valid 325 certificate

## Scenario status after Checkpoint 325

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

`MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`

## Anti-rollback invariant

1. Checkpoint 325 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 325 in order.
3. Scenario7 `PASS_REAL` requires the Checkpoint 325 release certificate.
4. The 107 clue-to-scene anchors remain non-causal; release does not convert them into an ordered clue path.
5. Commercial source text remains external/non-public; public evidence stores source refs and hashes only.
6. Conversation memory never outranks verified artifacts and hashes.
