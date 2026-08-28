# Apply Checkpoint 323

Parent authority: Checkpoint 322.

1. Reconstruct and verify Checkpoint 322 first.
2. Apply `solidstate_runtime/scenario6_release_gate.py`.
3. Replace `solidstate_runtime/multi_scenario_status_resolver.py` with the 323 resolver overlay.
4. Append the Scenario6ReleaseGateV1 export from `INIT_APPEND_323.txt`.
5. Copy `scenario_candidates/scenario6/MUSE_PASS_REAL_RELEASE_323.json`.
6. Provide the original Aventures Effroyables PDF externally via `MUSE_SOURCE_PDF`; do not publish it in the repository.
7. Run `run_tests_chunk323.py` and require all tests to pass.

Checkpoint 322 and 321 regressions are executed in their frozen pre-promotion environment because their historical assertions require scenario6 to remain blocked.
