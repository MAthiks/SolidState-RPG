# Android Runtime Integration V1 — candidate

Authority floor: **Checkpoint 333 — MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2**.

This directory starts the Android integration phase without promoting an APK or a new Solid State checkpoint.

## Implemented in this slice

`RuntimeAuthorityV1.kt` is a fail-closed attachment gate for an Android wrapper. It requires the exact Checkpoint 333 authority identity and the exact certified Checkpoint 329 package identity used to reconstruct the 330→331→332 runtime chain.

The gate rejects:

- any authority below Checkpoint 333;
- an unverified future checkpoint accepted by number alone;
- a mismatched Checkpoint 333 ID or record Git blob;
- a mismatched Checkpoint 329 runtime ZIP or package manifest;
- an incomplete 329→330→331→332 reconstruction;
- commercial/private sources embedded in the application;
- a local source pack that is not ready;
- unverified multiplayer player-state partitioning;
- unverified atomic save/resume;
- unverified actor-bound Strict Replay.

## Verified now

The Kotlin gate and its standalone JVM test were compiled with `kotlinc` and executed locally.

Result: **13/13 PASS**.

Source SHA-256:

- `RuntimeAuthorityV1.kt`: `35d866dec0ef847bdeb481dcd03c9b579c7d3d2fe6a5301626a7aea087964d51`
- `RuntimeAuthorityV1Test.kt`: `5863e01985c3eecd8c9583fa72a52a34b94993b2ec4b30e613009a336f6c1827`

## Current hard blocker

The certified base artifact required by Checkpoint 333 reconstruction is not present in the currently accessible File Library or repository artifact directory:

`SolidState_Offline_Runtime_v1_Checkpoint329.zip`

Expected SHA-256:

`75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`

Package manifest SHA-256:

`aba613f506e92248ee7e8ffd4a190c0d293b9e638be116659ad06a4e9a703dc9`

The runtime is **not reconstructed from source memory**. Android runtime attachment therefore remains fail-closed until that exact artifact can be verified and layers 330, 331 and 332 can be applied and checked.

## Next safe step

1. Recover the exact Checkpoint 329 ZIP and verify its SHA-256, CRC, 173-file manifest and offline self-test.
2. Apply and verify Checkpoints 330→331→332.
3. Feed verified runtime evidence into `RuntimeAuthorityV1`.
4. Only then add the Android lifecycle/serialization bridge and exercise offline launch, 1–4 player isolation, save/resume and actor-bound Strict Replay.
5. No APK promotion before integration tests, signing, signature verification and final APK SHA-256 recording.

Commercial/private scenario PDFs remain outside GitHub and outside the APK.
