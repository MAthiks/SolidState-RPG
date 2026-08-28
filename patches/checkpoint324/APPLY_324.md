# Apply Checkpoint 324

Parent authority: Checkpoint 323.

1. Copy `solidstate_runtime/source_backed_investigation_v4.py` into the runtime package.
2. Append `INIT_APPEND_324.txt` to `solidstate_runtime/__init__.py`.
3. Copy `scenario_candidates/scenario7/EXPLORATEUR_PATH_CLOSURE_324.json` into scenario7.
4. Copy `run_tests_chunk324.py` to the runtime root.
5. Keep the commercial source PDF external to the public repository.
6. Set `EXPLORATEUR_SOURCE_PDF` to the original `L'Appel de Cthulhu 7 - Aventures Effroyables.pdf`.
7. Require SHA-256 `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.
8. Run `run_tests_chunk324.py` and require `25/25 PASS`.
9. Run parent/core regressions separately: Checkpoint 323 PASS, Checkpoint 315 `5/5`, native runtime `5/5`.

Checkpoint 324 proves only a source-backed investigation progression path. Scenario7 remains non-`PASS_REAL` until a separate release audit succeeds. The 107 clue-to-scene anchors remain non-causal.
