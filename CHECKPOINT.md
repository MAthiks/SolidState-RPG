# Official development checkpoint

## Checkpoint 319 — VERIFIED SCENARIO 4 RELEASE

- Checkpoint: `319`
- ID: `SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`
- Parent: `318 — SCENARIO4_SOURCE_BACKED_PATH_CLOSURE_V1`
- Record: `patches/checkpoint319/CHECKPOINT_319.json`
- Record SHA-256: `12d341468385d63e092f31c12de2b0715e27b3f305823cf6fcee5e750b9afc0d`

## Certified scope

Checkpoint 319 performs the release audit that Checkpoint 318 deliberately kept separate from path proof. It promotes only scenario 4 — Les Registres de Brume — to `PASS_REAL` after all release gates pass.

Verified gates:

- dual-source preflight and pair identity: `PASS`
- knowledge firewall: `PASS`, Keeper→Player leaks = `0`
- protected release readiness: `PASS`
- source-backed path reproof: `PASS`
- generic transition execution ledger: `PASS`
- release certificate gate: `PASS`
- tamper/failure cases fail closed: `PASS`
- resolver returns scenario4 `PASS_REAL`: `PASS`
- certification eligibility: `CERTIFY`
- Scenario Selection Interface marks scenario4 selectable: `PASS`
- player selection surface exposes no Keeper evidence: `PASS`
- scenario status regression: `PASS`

## Verification

- `run_tests_chunk319.py`: `18/18 PASS`
- Checkpoint 315 regression: `PASS`
- native runtime regression: `PASS`

## Scenario status after Checkpoint 319

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

The historical scenario4 classification file remains unchanged. The newer release certificate is the explicit promotion authority.

## Next phase

`SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`

## Anti-rollback invariant

1. Checkpoint 319 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 + 317 + 318 + 319 in order.
3. Do not silently downgrade scenario4 from `PASS_REAL` to its historical pre-release classification.
4. Source text remains non-public; evidence uses source refs and hashes.
5. Conversation memory never outranks verified artifacts.
