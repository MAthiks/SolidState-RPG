# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 331 VERIFIED

- Checkpoint: `331`
- ID: `MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`
- Parent: `330 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2`
- Record: `patches/checkpoint331/CHECKPOINT_331.json`
- Record Git blob SHA-1: `642e94456b0084954f8cd5f4362be19c4a237c7b`
- Save/resume matrix: `987/987 PASS`
- Clean rebuild from Checkpoint 330 + patch: `987/987 PASS`
- Checkpoint 330 regression: `522/522 PASS`
- Checkpoint 329 adapted portable regression: `198/198 PASS`
- Checkpoint 315/native core: `5/5 PASS`

## Multiplayer save/resume V2

Checkpoint 331 recertifies save/resume for all five `PASS_REAL` scenarios and for `1`, `2`, `3` and `4` players. The selected scenario, SESSION_READY interface record, exact player-character control map, PV/SAN/PM/Chance, wounds/conditions, inventory and independent player knowledge partitions are preserved exactly across same-runtime and fresh-runtime restoration. Keeper knowledge remains absent from every player projection.

Checkpoint 331 also closes a destructive restore defect: the former offline restore path deleted the live SQLite slot before the untrusted save had passed authentication and semantic validation. Restore is now performed in an isolated staging database and the live slot is replaced atomically only after HMAC/schema/authority, semantic consistency, player-interface, inherited Strict Replay gate and private-source checks all pass. Rejected or malformed saves therefore leave the active session unchanged.

The save authority floor is advanced from the historical Checkpoint 326 binding to Checkpoint 330 multiplayer V2. Re-authenticated but semantically inconsistent saves involving ownership/control, mechanics, wounds, inventory, knowledge, character state or commit history fail closed.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Scope boundary

Checkpoint 331 certifies multiplayer save/resume V2. It uses the existing Strict Replay restoration gate as a regression, but does **not** yet certify full multiplayer Strict Replay V2 continuity.

## Next phase

`MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`

The Android APK candidate remains paused and unpromoted.

Automatic downgrade is forbidden.
