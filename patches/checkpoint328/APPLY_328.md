# Apply Checkpoint 328

1. Start from verified Checkpoint 327.
2. Copy `solidstate_runtime/strict_replay_save_resume_v1.py` into the runtime package.
3. Append `INIT_APPEND_328.txt` to `solidstate_runtime/__init__.py` if package export is desired.
4. Keep the Checkpoint 327 `save_resume_v1.py` implementation unchanged; its Git blob SHA-1 must remain `85f3232ca2b3b855dd5ae05a4630324551dc9a82` for this certification.
5. Run `run_tests_chunk328.py` and require `207/207 PASS`.
6. Re-run historical Strict Replay tests 259, 263 and 270, Checkpoint 315 and native core.

Checkpoint 328 adds no commercial scenario text. Strict Replay stores supplied deterministic roll values in strict events; replay never silently rerolls them.
