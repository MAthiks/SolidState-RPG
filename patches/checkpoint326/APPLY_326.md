# Apply Checkpoint 326

Parent authority: Checkpoint 325.

1. Apply `ENGINE_ATTACH_326.patch` to `solidstate_runtime/engine.py`.
2. Add `solidstate_runtime/multiplayer_certification_v1.py`.
3. Add `solidstate_runtime/player_interface_v1.py` (restored Interface V1 player/launch surface).
4. Append `INIT_APPEND_326.txt` to `solidstate_runtime/__init__.py` if those exports are not already present.
5. Add `run_tests_chunk326.py`.
6. Run `run_tests_chunk326.py` and require `334/334 PASS`.
7. Re-run Checkpoint 325, Checkpoint 315 and native-core regressions.
8. Re-run historical multiplayer Chunks 147, 148 and 168.

Checkpoint 326 certifies 1–4 players with exactly one owned investigator per player, unique control, separate player knowledge, Player Interface V1 isolation, Normal/Libre open prompt, assisted 3 choices + 1 free action, launch-to-session readiness, cross-player control fail-closed, and per-character transaction isolation.

Automatic downgrade is forbidden.
