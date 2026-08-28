# Apply Checkpoint 327

Parent authority: Checkpoint 326.

1. Reconstruct verified Checkpoint 326.
2. Copy `solidstate_runtime/save_resume_v1.py` into the runtime package.
3. Append the line from `INIT_APPEND_327.txt` to `solidstate_runtime/__init__.py`.
4. Keep the save authentication secret outside the save bundle and outside the public repository; minimum 32 bytes.
5. Run `run_tests_chunk327.py` and require `71/71 PASS`.
6. Re-run Checkpoint 326 and require `334/334 PASS`.
7. Re-run Checkpoint 325 with the original Aventures Effroyables PDF and require `31/31 PASS`.
8. Re-run Checkpoint 315 and the native core tests and require `5/5 PASS` each.

Restore is fail-closed and only targets a pristine database. A save revalidates the selected scenario as `PASS_REAL`, preserves the exact commit sequence, control map, interface session, mechanics, inventory and knowledge partitions, and authenticates the canonical payload with HMAC-SHA256.
