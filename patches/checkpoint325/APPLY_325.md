# Apply Checkpoint 325

Parent authority: Checkpoint 324.

1. Reconstruct the verified Checkpoint 324 runtime.
2. Copy `scenario7_release_gate.py` and `multi_scenario_status_resolver.py` into `solidstate_runtime/`.
3. Append `INIT_APPEND_325.txt` to `solidstate_runtime/__init__.py` if the export is not already present.
4. Copy `EXPLORATEUR_PASS_REAL_RELEASE_325.json` into `scenario_candidates/scenario7/`.
5. Keep the commercial source PDF outside the public repository.
6. Set `EXPLORATEUR_SOURCE_PDF` to the exact external PDF whose SHA-256 is `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.
7. Run `run_tests_chunk325.py` and require `31/31 PASS`.
8. Re-run Checkpoint 324 in its frozen pre-release environment and require `25/25 PASS`.
9. Re-run Checkpoint 323 in its frozen environment and require `31/31 PASS`.
10. Require Checkpoint 315 and native-core regressions to remain `5/5 PASS`.

The 325 certificate is the only current promotion authority for scenario7. The 107 clue-to-scene anchors remain non-causal; none may be converted into an automatic transition.
