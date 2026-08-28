# Official development checkpoint

## Checkpoint 329 — VERIFIED OFFLINE PLAYABLE RUNTIME PACKAGE

- Checkpoint: `329`
- ID: `OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`
- Parent: `328 — STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`
- Record: `patches/checkpoint329/CHECKPOINT_329.json`
- Record Git blob SHA-1: `deb884f6a0506a887f12e421eef1fcd628c7524b`
- Certified ZIP SHA-256: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`

## Certified scope

Checkpoint 329 certifies the offline package built from the Checkpoint 328 runtime. It preserves 1–4 player support, Player Interface V1, local roll ledger, Checkpoint 327 save/resume and Checkpoint 328 Strict Replay continuity while removing any Internet dependency from the native execution path.

The distributed ZIP contains no commercial scenario PDF or text. User-owned source files are imported locally and validated before commercial scenarios become `SOURCE_READY`. Missing or mismatched private sources fail closed and are never exposed on player surfaces.

The package is intentionally Keeper-assisted. It does not claim autonomous offline AI narration and does not certify free-form user-entered stats as faithful CoC7 character creation.

## Verification

- full package matrix: `284/284 PASS`
- portable package matrix: `199/199 PASS`
- Checkpoint 328 regression: `207/207 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native core: `5/5 PASS`
- ZIP CRC: `PASS`
- extracted package manifest: `173/173 PASS`
- extracted self-test: `PASS`
- package manifest SHA-256: `aba613f506e92248ee7e8ffd4a190c0d293b9e638be116659ad06a4e9a703dc9`
- external network dependency: `false`
- commercial source text embedded: `false`
- all five scenario statuses remain `PASS_REAL`

## Next phase

`ANDROID_APK_WRAPPER_AND_PRIVATE_SOURCE_IMPORT_V1`

## Anti-rollback invariant

1. Checkpoint 329 is the current verified authority.
2. The offline release identity requires ZIP SHA-256 `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`.
3. Checkpoint 328 remains the certified runtime parent.
4. Commercial source material remains private/non-public and is validated locally.
5. Save/resume and Strict Replay guarantees may not be weakened by Android packaging.
6. Conversation memory never outranks verified artifacts and hashes.
