# Official development checkpoint

## Checkpoint 323 — VERIFIED SCENARIO 6 RELEASE

- Checkpoint: `323`
- ID: `SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`
- Parent: `322 — SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`
- Record: `patches/checkpoint323/CHECKPOINT_323.json`
- Record Git blob SHA-1: `c7c16db278e1d80d910376d2c9fa2360cb945a83`

## Certified scope

Checkpoint 323 performs the separate release audit required by Checkpoint 322 and promotes only scenario6 — Muse équivoque aux yeux de sel gemme — to `PASS_REAL`.

The promotion re-proves the six-transition conditional path against exact source hashes, verifies the original PDF identity, preserves alternative endings and the open conclusion, validates independent knowledge partitioning, confirms zero Keeper→Player evidence leakage, tests resolver/interface behavior and rejects tampered release evidence.

## Verification

- `run_tests_chunk323.py`: `31/31 PASS`
- Checkpoint 322 isolated regression: `29/29 PASS`
- Checkpoint 321 isolated regression: `27/27 PASS`
- Checkpoint 315 regression: `PASS`
- native runtime regression: `PASS`
- source PDF SHA-256: `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143` — `PASS`
- exact source-evidence hashes: `PASS`
- Keeper→Player leaks: `0`
- release tamper cases: fail closed
- Scenario Selection Interface: scenario6 selectable only with valid 323 certificate

## Scenario status after Checkpoint 323

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next phase

`SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`

## Anti-rollback invariant

1. Checkpoint 323 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 323 in order.
3. Scenario6 `PASS_REAL` requires the Checkpoint 323 release certificate.
4. `PASS_REAL` does not collapse Muse's alternative/open endings into a single canonical ending.
5. Commercial source text remains external/non-public; public evidence stores source refs and hashes only.
6. Conversation memory never outranks verified artifacts and hashes.
