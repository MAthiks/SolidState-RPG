# Official development checkpoint

## Checkpoint 331 — VERIFIED MULTIPLAYER SAVE/RESUME RECERTIFICATION V2

- Checkpoint: `331`
- ID: `MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`
- Parent: `330 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2`
- Record: `patches/checkpoint331/CHECKPOINT_331.json`
- Record Git blob SHA-1: `642e94456b0084954f8cd5f4362be19c4a237c7b`

## Certified scope

Checkpoint 331 certifies save/resume for 1–4 player sessions across all five `PASS_REAL` scenarios. It preserves selected scenario, SESSION_READY player list/control map, PV/SAN/PM/Chance, wounds/conditions, actual inventory, canonical state, persisted SQL projections and independent player knowledge partitions exactly. Keeper knowledge remains absent from player surfaces.

Restore is fail-closed and non-destructive: untrusted bundles are authenticated and semantically validated in a separate staging SQLite database. The live slot is atomically replaced only after all required gates pass. Invalid HMAC/hash/schema/authority, control/ownership split-brain, mechanical/wound/inventory/knowledge/character inconsistencies, commit gaps, malformed JSON and missing private sources are rejected without changing the active session.

## Verification

- Checkpoint 331 matrix: `987/987 PASS`
- clean reconstruction from Checkpoint 330 plus patch: `987/987 PASS`
- Checkpoint 330 regression: `522/522 PASS`
- Checkpoint 329 adapted portable regression: `198/198 PASS`
- Checkpoint 315: `5/5 PASS`
- native core: `5/5 PASS`
- scenarios: `scenario3` through `scenario7`
- player counts: `1, 2, 3, 4`
- Keeper→Player leaks after restore: `0`
- same-runtime restore: `PASS`
- fresh-runtime restore: `PASS`
- next commit after resume: `saved_commit + 1`
- rejected save mutates live slot: `false`

## Defects closed

1. `DESTRUCTIVE_RESTORE_BEFORE_VALIDATION`
2. `SAVE_AUTHORITY_FLOOR_STALE_AT_CHECKPOINT326`
3. `SAVE_SEMANTIC_SPLIT_BRAIN_GAPS`

## Scope boundary

The existing Strict Replay restore gate remains a regression dependency only. Full multiplayer Strict Replay V2 is not certified by Checkpoint 331.

## Next phase

`MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`

## Anti-rollback invariant

1. Checkpoint 331 is the current verified authority.
2. Save authority floor is Checkpoint 330 multiplayer V2.
3. An untrusted save may never destroy or replace the live slot before complete validation.
4. Player ownership, controls, knowledge partitions and player-interface isolation remain mandatory after resume.
5. Commercial source material remains private/non-public.
6. Android APK work remains paused and unpromoted.
7. Conversation memory never outranks verified artifacts and hashes.
