# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 322 VERIFIED

- Checkpoint: `322`
- ID: `SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1`
- Status: `VERIFIED_PATH_PROOF_MILESTONE_NOT_RELEASE`
- Parent: `321 — SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`
- Checkpoint record: `patches/checkpoint322/CHECKPOINT_322.json`
- Checkpoint record Git blob SHA-1: `9107299fad5183862a22513c208014b8dc4b1f5d`
- Chunk 322 tests: `29/29 PASS`
- Checkpoint 321 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- Native core regression: `PASS`
- Knowledge firewall: `PASS`

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL_CANDIDATE_NOT_RELEASED`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

Checkpoint 322 proves one complete conditional source-backed path for scenario6 using six explicitly audited narrative transitions from an Act I player-safe start to an explicit conditional conclusion consequence. The path executes through the generic transition layer. Alternative branches and the open conclusion remain preserved; the path proof does not select or invent an ideal ending.

The source collection PDF is external to the public repository and is identified by SHA-256 `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`. Public checkpoint artifacts contain only project code, source references, hashes and certification metadata.

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 321 in order.
3. Apply `patches/checkpoint322/` according to `APPLY_322.md`.
4. Provide the original Aventures Effroyables PDF outside the repository via `MUSE_SOURCE_PDF`.
5. Require `run_tests_chunk322.py` to pass `29/29`.

## Next phase

`SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`

Automatic downgrade is forbidden. Scenario6 remains blocked in the certified player scenario-selection interface until the separate release audit succeeds.
