# Apply Checkpoint 319

Parent authority: Checkpoint 318.

1. Reconstruct the verified Checkpoint 318 runtime chain (315 -> 316 -> 317 -> 318).
2. Copy `solidstate_runtime/scenario4_release_gate.py` into the runtime package.
3. Replace `solidstate_runtime/multi_scenario_status_resolver.py` with the Checkpoint 319 version.
4. Append the exact line in `INIT_APPEND_319.txt` to `solidstate_runtime/__init__.py` if not already present.
5. Copy `scenario_candidates/scenario4/BRUME_PASS_REAL_RELEASE_319.json` into the scenario4 candidate directory.
6. Run `run_tests_chunk319.py`.
7. Require `18/18 PASS`; any failure blocks the promotion.

Checkpoint 319 promotes only scenario4 (Les Registres de Brume) to `PASS_REAL`.
It does not alter scenario5–7 status.

The historical `BRUME_FINAL_CLASSIFICATION.json` remains unchanged as provenance. The newer release certificate is an overlay produced by the separate release audit.

No Keeper/source text is republished in this patch; evidence is represented by source refs and SHA-256 values.
