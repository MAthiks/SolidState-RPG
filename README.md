# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 329 VERIFIED

- Checkpoint: `329`
- ID: `OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`
- Status: `VERIFIED_OFFLINE_PLAYABLE_RUNTIME_PACKAGE`
- Parent: `328 — STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`
- Record: `patches/checkpoint329/CHECKPOINT_329.json`
- Record Git blob SHA-1: `deb884f6a0506a887f12e421eef1fcd628c7524b`
- Certified ZIP SHA-256: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`
- Package matrix: `284/284 PASS`
- Checkpoint 328 regression: `207/207 PASS`
- Checkpoint 315/native core: `5/5 PASS`

## Offline playable runtime

Checkpoint 329 packages the certified runtime for practical offline execution. The package is loopback-only, requires no Internet connection and no external Python package, supports 1–4 players, Player Interface V1, local roll ledger, Checkpoint 327 authenticated save/resume and Checkpoint 328 Strict Replay continuity.

The extracted package verifies `173/173` immutable files against its package manifest and passes its self-test. ZIP CRC is clean. The release identity is the ZIP SHA-256 above plus the versioned checkpoint record and package manifest identity.

Commercial scenario PDFs/text are **not** embedded in GitHub or in the ZIP. Exact user-owned private sources are imported locally into `sources/` and verified before a commercial scenario becomes `SOURCE_READY`; missing or mismatched sources fail closed.

This is a **Keeper-assisted** offline runtime. It does not claim autonomous local-AI narration, and free-form user-entered stats are not certified as CoC7 character creation.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Next phase

`ANDROID_APK_WRAPPER_AND_PRIVATE_SOURCE_IMPORT_V1`

The next milestone wraps this exact Checkpoint 329 runtime for Android while preserving the ZIP/runtime identity, private-source boundary, save/resume and Strict Replay guarantees.

Automatic downgrade is forbidden.
