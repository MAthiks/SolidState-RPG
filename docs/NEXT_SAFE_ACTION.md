# Next safe action

## Checkpoint 331 complete

Current authority:

`Checkpoint 331 — MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`

Verification:

- multiplayer save/resume V2 matrix: `987/987 PASS`
- clean rebuild from Checkpoint 330 + patch: `987/987 PASS`
- scenarios: `scenario3` through `scenario7`
- player counts: `1, 2, 3, 4`
- selected scenario and SESSION_READY interface: exact after restore
- control map and one-character-per-player ownership: exact after restore
- PV/SAN/PM/Chance, wounds/conditions and inventory: exact after restore
- player knowledge partitions: exact after restore
- Keeper→Player leaks: `0`
- same-runtime and fresh-runtime restore: `PASS`
- next commit after resume: `saved_commit + 1`
- malformed/tampered save: fail closed
- rejected save changes active session: `false`
- restore validation: isolated staging DB, atomic live replacement only after PASS
- Checkpoint 330 regression: `522/522 PASS`
- Checkpoint 329 adapted portable regression: `198/198 PASS`
- Checkpoint 315/native core: `5/5 PASS`
- all five scenario statuses: `PASS_REAL`

Closed defects: destructive restore before validation; stale save authority floor at Checkpoint 326; incomplete semantic split-brain validation.

## Next phase

Proceed with:

`MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`

Work order:

1. For all five scenarios and 1–4 players, compare uninterrupted execution against save→fresh-runtime→resume execution.
2. Require exact equality of Strict Replay event order, event identities, deterministic roll tape, hash chain, semantic commit trace and final canonical digest.
3. Exercise independent actions from every player, including interleaved P1–P4 actions, while preserving player ownership/knowledge/interface isolation.
4. Prove that a failed action for one player creates no replay event, no commit and no sibling-state mutation.
5. Reject reordered, duplicated, omitted or cross-player-attributed replay events even if the enclosing save is re-authenticated.
6. Prove resume never rerolls a recorded random value and never duplicates/omits a committed action.
7. Re-run Checkpoint 331, 330, package/core regressions and keep all five scenarios `PASS_REAL`.

Android APK work remains paused and unpromoted.

Automatic downgrade is forbidden.
