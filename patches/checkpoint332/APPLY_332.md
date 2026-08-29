# Apply Checkpoint 332

Parent authority: Checkpoint 331 `MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`.

1. Start from the exact Checkpoint 331 reconstructed runtime.
2. Copy `solidstate_runtime/strict_replay_multiplayer_v2.py` into `solidstate_runtime/`.
3. Append `INIT_APPEND_332.txt` to `solidstate_runtime/__init__.py` once.
4. Run `run_tests_chunk332.py` with the private source PDFs supplied only through the local source pack/environment.
5. Certification requires every Checkpoint 332 assertion to pass and all five scenario statuses to remain `PASS_REAL`.

No commercial scenario text or PDF is part of this patch. No reroll is performed during replay; the supplied deterministic roll tape is preserved in strict events.
