# Official development checkpoint

## Checkpoint 330 — VERIFIED MULTIPLAYER 1–4 RECERTIFICATION V2

- Checkpoint: `330`
- ID: `MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2`
- Parent: `329 — OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`
- Record: `patches/checkpoint330/CHECKPOINT_330.json`
- Record Git blob SHA-1: `62166f32edfc10e3a32553cfeb889019996dfd13`
- Parent runtime ZIP SHA-256: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`

## Certified scope

Checkpoint 330 certifies multiplayer state/control/knowledge isolation for 1–4 players. Each player has exactly one owned investigator, controls are unique, canonical and SQL party mappings are consistent, interface control mappings match, player knowledge partitions are independent, and Keeper knowledge remains absent from player projections.

Three defects discovered in the Checkpoint 329 runtime are closed: partial live-state contamination after a later player's setup failure, silent character-owner reassignment, and a Player Interface ownership gate which trusted only the party row. Multiplayer session construction is now atomic, character ownership is immutable, and inconsistent/tampered control or ownership mappings fail closed.

## Verification

- Checkpoint 330 matrix: `522/522 PASS`
- clean reconstruction from exact Checkpoint 329 ZIP plus patch: `522/522 PASS`
- Checkpoint 329 portable regression: `199/199 PASS`
- Checkpoint 315: `5/5 PASS`
- native core: `5/5 PASS`
- player counts: `1, 2, 3, 4`
- Keeper→Player leaks: `0`
- failed player action corrupts siblings: `false`
- cross-player control: blocked
- Normal/Libre prompt: `Que fais-tu ?`
- Facile/Assisté: exactly `3 choices + 1 free action`
- all five scenario statuses remain `PASS_REAL`

## Scope boundary

Save/resume and Strict Replay remain green as Checkpoint 329 regressions only. Their multiplayer V2 recertification is deliberately deferred.

## Next phase

`MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`

Then: `MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`.

## Anti-rollback invariant

1. Checkpoint 330 is the current verified authority.
2. Reconstruction requires the exact Checkpoint 329 runtime ZIP plus the versioned 330 patch set.
3. Character ownership and player control may not be silently reassigned.
4. Multiplayer bootstrap must be all-or-nothing.
5. Player/knowledge partition isolation is mandatory.
6. Android APK work is paused and is not promoted into this checkpoint.
7. Conversation memory never outranks verified artifacts and hashes.
