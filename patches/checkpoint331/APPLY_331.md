# Apply Checkpoint 331

Parent authority: **Checkpoint 330 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2**.

1. Start from a runtime with Checkpoint 330 patches applied.
2. Copy `solidstate_runtime/save_resume_multiplayer_v2.py` into the runtime package.
3. Apply `INIT_AND_SAVE_EXPORT_331.patch` with `patch -p1`.
4. Apply `OFFLINE_ATOMIC_RESTORE_331.patch` with `patch -p1`.
5. Run `run_tests_chunk331.py` with the exact private scenario sources available only locally. Expected: `987/987 PASS`.
6. Re-run Checkpoint 330 regression: `522/522 PASS`; adapted Checkpoint 329 package regression: `198/198 PASS`; Checkpoint 315/core: `5/5 PASS` each.

Security invariant: an invalid/tampered/unavailable-source save is restored only into a temporary staging SQLite database. The live slot must not be deleted or replaced until authentication, semantic consistency, player-interface projection, inherited Strict Replay gate and private-source gate all pass.

Checkpoint 331 does **not** certify multiplayer Strict Replay V2; that remains the next phase.
