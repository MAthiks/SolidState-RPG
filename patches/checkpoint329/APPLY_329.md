# APPLY 329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1

Parent authority: Checkpoint 328 (`STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`).

1. Verify the Checkpoint 328 authority chain before using this release.
2. Obtain the certified artifact `SolidState_Offline_Runtime_v1_Checkpoint329.zip` and require SHA-256 `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`.
3. Require ZIP CRC PASS, then extract it and execute `verify_package.py`; the package manifest SHA-256 is `aba613f506e92248ee7e8ffd4a190c0d293b9e638be116659ad06a4e9a703dc9` and covers 173 immutable files.
4. Keep all commercial/private source PDFs outside GitHub and outside the ZIP. Users place their own exact files in the generated `sources/` directory. Missing or mismatched sources fail closed.
5. `PACKAGE_SOURCE_INDEX_329.json` records the SHA-256 identities of the package-specific public files without republishing scenario text.
6. Execute `run_tests_chunk329.py` with `OFFLINE_PACKAGE_ROOT`, `AE_SOURCE_PDF`, `BRUME_KEEPER_PDF`, `BRUME_PLAYER_PDF`, and `ANTRE_SOURCE_PDF` pointing to exact user-owned sources; require the portable package matrix to pass.
7. Certification evidence for this checkpoint records the full package matrix `284/284 PASS`, Checkpoint 328 `207/207 PASS`, Checkpoint 315 `5/5 PASS`, native core `5/5 PASS`, ZIP CRC PASS, and extracted-package self-test PASS.
8. A deterministic bit-for-bit rebuild was verified during certification. Because a large builder transfer showed integrity risk, that builder is deliberately **not** part of the GitHub authority set. The release identity is the certified ZIP SHA-256 plus the package manifest and repository records above.

This checkpoint certifies a **Keeper-assisted offline runtime package**. It does not claim autonomous offline AI narration, does not certify CoC7 character creation from free-form user stats, and does not change any scenario `PASS_REAL` status.
