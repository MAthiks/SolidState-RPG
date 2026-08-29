# APPLY 330 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2

Parent authority: Checkpoint 329 (`OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`).
Parent runtime ZIP identity: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`.

1. Extract the exact Checkpoint 329 offline runtime.
2. Apply `ENGINE_MULTIPLAYER_HARDENING_330.patch` with `patch -p1`.
3. Apply `PLAYER_INTERFACE_MULTIPLAYER_HARDENING_330.patch` with `patch -p1`.
4. Apply `OFFLINE_MULTIPLAYER_ATOMIC_BOOTSTRAP_330.patch` with `patch -p1`.
5. Copy `solidstate_runtime/multiplayer_certification_v2.py` into the runtime and append `INIT_APPEND_330.txt` to `solidstate_runtime/__init__.py` when a package-level export is desired.
6. Copy and run `run_tests_chunk330.py` from the runtime root. Require `522/522 PASS`.
7. Re-run the Checkpoint 329 portable matrix with exact user-owned sources. Require `199/199 PASS`.
8. Re-run Checkpoint 315 and native core regressions. Require `5/5 PASS` for each.

Checkpoint 330 certifies multiplayer state/control/knowledge isolation only. Checkpoint 329 save/resume and Strict Replay are regression-tested but are **not** recertified by this checkpoint. The next phase is `MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`, followed by `MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`.

No commercial scenario source text or PDF is part of this patch.
