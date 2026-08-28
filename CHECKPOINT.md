# Official development checkpoint

## Checkpoint 321 — VERIFIED SCENARIO 5 RELEASE

- Checkpoint: `321`
- ID: `SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`
- Parent: `320 — SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`
- Record: `patches/checkpoint321/CHECKPOINT_321.json`
- Record SHA-256: `d3edb5ebc7ae751b51ad1a2fd9ad417e549862f961c30580e8b9fa1168dea65a`

## Certified scope

Checkpoint 321 performs the separate release audit that Checkpoint 320 deliberately required before scenario5 could become selectable. It promotes only L'Antre de l'abomination to `PASS_REAL` after the current path proof, source identity, source coverage, knowledge firewall, resolver and interface-selection boundaries all pass.

The old `ANTRE_PASS_REAL_CERTIFICATE.json` is not reactivated. It remains historical provenance only.

## Verification

- `run_tests_chunk321.py`: `27/27 PASS`
- independent historical Antre audit: `15/15 PASS`
- original `antre.pdf` SHA-256: `4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb` — `PASS`
- source coverage: `0` open domains
- Checkpoint 320 ten-transition route reproof: `PASS`
- Keeper→Player leaks: `0`
- resolver fails closed without the 321 certificate: `PASS`
- resolver promotes only with the 321 certificate: `PASS`
- Scenario Selection Interface marks scenario5 selectable only after release: `PASS`
- tampered parent hash / knowledge leak / historical-cert reactivation: all fail closed
- Checkpoint 315 and native-core regressions: `PASS`

## Scenario status after Checkpoint 321

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next phase

`SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`

## Anti-rollback invariant

1. Checkpoint 321 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 321 in order.
3. Scenario5 `PASS_REAL` requires the Checkpoint 321 release certificate; the historical certificate alone is insufficient.
4. The original scenario PDF remains external/non-public and is identified by SHA-256.
5. Conversation memory never outranks verified artifacts and hashes.
