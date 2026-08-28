# Apply Checkpoint 326

Parent authority: Checkpoint 325.

1. Apply `ENGINE_ATTACH_326.patch` to `solidstate_runtime/engine.py`.
2. Add `solidstate_runtime/multiplayer_certification_v1.py`.
3. Append `INIT_APPEND_326.txt` to `solidstate_runtime/__init__.py` if that export is not already present.
4. Add `run_tests_chunk326.py`.
5. Run `run_tests_chunk326.py` and require `228/228 PASS`.
6. Re-run Checkpoint 325, Checkpoint 315 and native-core regressions.
7. Re-run historical multiplayer Chunks 147, 148 and 168.

Checkpoint 326 certifies 1–4 players with exactly one owned investigator per player, unique control, separate player knowledge, no Keeper knowledge projection, cross-player control fail-closed, and per-character transaction isolation.

Automatic downgrade is forbidden.
