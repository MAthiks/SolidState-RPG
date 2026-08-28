# APPLY 329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1

Parent authority: Checkpoint 328 (`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`).

1. Reconstruct the verified Checkpoint 328 runtime from the versioned checkpoint chain.
2. Decode `build_offline_package_v1.py.zlib.b64` with Base64, then zlib, to recover `build_offline_package_v1.py`. Its SHA-256 must be `7c5048f3b61b708a21faf466aa7367ccc8b6c1c4624e3620a14d34a698033ae6`.
3. Run the builder against that exact Checkpoint 328 runtime. The deterministic output ZIP must have SHA-256 `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`.
4. Keep commercial/private source PDFs outside the repository and outside the public ZIP; users place their own exact files in the generated `sources/` directory.
5. Verify generated `PACKAGE_MANIFEST.json` with `verify_package.py`. The package manifest SHA-256 is `aba613f506e92248ee7e8ffd4a190c0d293b9e638be116659ad06a4e9a703dc9` and covers 173 immutable files.
6. Execute public `run_tests_chunk329.py` with `OFFLINE_PACKAGE_ROOT`, `AE_SOURCE_PDF`, `BRUME_KEEPER_PDF`, `BRUME_PLAYER_PDF`, and `ANTRE_SOURCE_PDF` pointing to exact user-owned sources; require `199/199 PASS`.
7. The archived certification report records the full package matrix `284/284 PASS`, Checkpoint 328 `207/207 PASS`, Checkpoint 315 `5/5 PASS`, native core `5/5 PASS`, ZIP CRC PASS and extracted-package self-test PASS.

Compressed recovery artifacts use the suffix `.zlib.b64`; decode Base64 first, then zlib. This checkpoint certifies a **Keeper-assisted offline runtime package**. It does not claim autonomous offline AI narration and does not change any scenario `PASS_REAL` status.
