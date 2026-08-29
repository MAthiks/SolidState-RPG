# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 330 VERIFIED

- Checkpoint: `330`
- ID: `MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2`
- Parent: `329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`
- Record: `patches/checkpoint330/CHECKPOINT_330.json`
- Record Git blob SHA-1: `62166f32edfc10e3a32553cfeb889019996dfd13`
- Multiplayer matrix: `522/522 PASS`
- Clean rebuild from Checkpoint 329 + patch: `522/522 PASS`
- Checkpoint 329 portable regression: `199/199 PASS`
- Checkpoint 315/native core: `5/5 PASS`

## Multiplayer V2

Checkpoint 330 recertifies the runtime for `1`, `2`, `3` and `4` players. Every player controls exactly one owned investigator; character controls are unique; canonical party state, SQL party bindings and the active interface control map must agree. Player knowledge partitions and Player Interface V1 surfaces remain isolated, with `0` Keeper-to-player knowledge leaks.

The recertification also closes three real parent-runtime defects: a late P2/P3/P4 setup failure could leave earlier players partially committed; character ownership could be silently reassigned after attachment; and Player Interface V1 trusted only the party row when checking ownership. Multiplayer setup is now staged atomically, character ownership is immutable, silent player-character rebinding is blocked, and split-brain/tampered ownership or control mappings fail closed.

A failed action or transaction for one investigator does not advance the commit or corrupt sibling states. Normal/Libre remains exactly `Que fais-tu ?`; Facile/Assisté remains exactly three player-safe suggestions plus one free action.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Scope boundary

Checkpoint 329 save/resume and Checkpoint 328 Strict Replay still pass as regressions, but Checkpoint 330 does **not** claim their multiplayer V2 recertification.

## Next phase

`MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`

After that: `MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`.

The Android APK candidate work is paused and is not part of the current authority.

Automatic downgrade is forbidden.
