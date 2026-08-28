# Next safe action

## Checkpoint 329 complete

Current authority:

`Checkpoint 329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`

Verification:

- full offline package matrix: `284/284 PASS`
- portable package matrix: `199/199 PASS`
- player counts: `1, 2, 3, 4`
- all five scenario statuses: `PASS_REAL`
- Checkpoint 327 save/resume: `PASS`
- Checkpoint 328 Strict Replay continuity: `207/207 PASS`
- ZIP CRC: `PASS`
- immutable extracted manifest: `173/173 PASS`
- extracted self-test: `PASS`
- certified ZIP SHA-256: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`
- external Internet dependency: `false`
- commercial source text embedded: `false`
- missing/mismatched private source: fail closed
- autonomous offline AI narration: not claimed

## Next phase

Proceed with:

`ANDROID_APK_WRAPPER_AND_PRIVATE_SOURCE_IMPORT_V1`

Work order:

1. Wrap the exact Checkpoint 329 offline runtime in an Android application without changing certified runtime semantics.
2. Preserve the private `sources/` boundary and implement user-controlled local PDF/source import into app-private storage.
3. Verify imported sources against the exact SHA-256 requirements before enabling the corresponding scenario.
4. Preserve 1–4 player controls, Player Interface V1, local rolls, authenticated save/resume and Strict Replay.
5. Keep all HTTP/runtime traffic loopback-only or remove the HTTP bridge entirely if the Android wrapper can call the runtime directly.
6. Ensure the APK contains no commercial scenario source material and no hard-coded private save authentication secret.
7. Run install/start/restart/save/resume/replay tests on Android before certifying a new checkpoint.
8. Keep autonomous local-AI narration outside the certified APK milestone unless separately audited.

Automatic downgrade is forbidden.
