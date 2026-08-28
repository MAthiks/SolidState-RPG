# APPLY 329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1

Parent authority: Checkpoint 328 (`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`).

1. Reconstruct the verified Checkpoint 328 runtime from the versioned checkpoint chain.
2. Overlay the public package-specific files under `offline_package/`.
3. Keep commercial/private source PDFs outside the repository and outside the public ZIP source tree; users place their own exact files in `sources/`.
4. Verify `PACKAGE_MANIFEST.json` with `verify_package.py`.
5. Execute `run_tests_chunk329.py` with `OFFLINE_PACKAGE_ROOT`, `AE_SOURCE_PDF`, `BRUME_KEEPER_PDF`, `BRUME_PLAYER_PDF`, and `ANTRE_SOURCE_PDF` pointing to exact user-owned sources.
6. Require `284/284 PASS`, Checkpoint 328 `207/207 PASS`, Checkpoint 315 `5/5 PASS`, native core `5/5 PASS`, ZIP CRC PASS, and extracted-package self-test PASS.

This checkpoint certifies a **Keeper-assisted offline runtime package**. It does not claim autonomous offline AI narration and does not change any scenario `PASS_REAL` status.
