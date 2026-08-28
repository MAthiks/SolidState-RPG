# Official development checkpoint

## Checkpoint 324 — VERIFIED SCENARIO 7 PATH PROOF

- Checkpoint: `324`
- ID: `SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`
- Parent: `323 — SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`
- Record: `patches/checkpoint324/CHECKPOINT_324.json`
- Record Git blob SHA-1: `7aa9fdef7297bfc14e33897a4659c4671a8732ab`

## Certified scope

Checkpoint 324 resolves the Checkpoint 315 task for L’Explorateur assassiné at path-proof level. It proves one complete executable investigation progression using ten transitions backed by manually audited explicit source language.

The historical investigation topology is preserved exactly as non-causal provenance: all `107` clue-to-scene anchors remain `causal_edge = false`, and Checkpoint 324 uses `0` clue anchors as causal transitions. Investigation progress is modeled as explicit world/state/condition progression rather than as a fixed sequence of clues.

Path proof status: `PASS_REAL_CANDIDATE`.

Release status: `pass_real = false`.

## Verification

- `run_tests_chunk324.py`: `25/25 PASS`
- Checkpoint 323 regression: `PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native runtime regression: `5/5 PASS`
- original source PDF SHA-256: `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143` — `PASS`
- source-layout SHA-256: `7b00a96cb2ab83e40b576bd0cb2e96d369393f6ce714c1d59a4a4b2f6a3265e3` — `PASS`
- inferred/ambiguous/editorial-only transitions: fail closed
- specific clue anchors cannot gate the certified path
- player-safe summary contains no Keeper evidence
- Scenario Selection Interface still blocks scenario7 before release

## Scenario status after Checkpoint 324

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL_CANDIDATE_NOT_RELEASED`

## Next gate

`SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`

## Anti-rollback invariant

1. Checkpoint 324 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 324 in order.
3. Path proof never self-promotes scenario7.
4. The 107 clue-to-scene anchors remain non-causal unless separately proven; Checkpoint 324 does not promote any of them.
5. Commercial source text remains external/non-public; public evidence stores source refs and hashes only.
6. Conversation memory never outranks verified artifacts and hashes.
