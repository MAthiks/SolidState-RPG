# Apply Checkpoint 321 — Scenario 5 PASS_REAL release audit

Parent authority: `Checkpoint 320 — SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`.

1. Reconstruct and verify Checkpoint 320 first.
2. Copy `solidstate_runtime/scenario5_release_gate.py` into the runtime package.
3. Replace `solidstate_runtime/multi_scenario_status_resolver.py` with the Checkpoint 321 version.
4. Copy `scenario_candidates/scenario5/ANTRE_PASS_REAL_RELEASE_321.json` into scenario 5.
5. Append `INIT_APPEND_321.txt` to `solidstate_runtime/__init__.py` if the export is not already present.
6. Provide the original `antre.pdf` outside the public repository and set `ANTRE_SOURCE_PDF=/path/to/antre.pdf`.
7. Run `run_tests_chunk321.py` and require `27/27 PASS`.
8. Do not accept `PASS_REAL` if the release certificate is missing, malformed, tampered, or reports any Keeper→Player leak.

The scenario source PDF is not republished in this public repository. The release certificate records its SHA-256 only.
