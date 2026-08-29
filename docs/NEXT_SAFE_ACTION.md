# Next safe action

## Checkpoint 330 complete

Current authority:

`Checkpoint 330 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2`

Verification:

- multiplayer V2 matrix: `522/522 PASS`
- clean rebuild from exact Checkpoint 329 runtime + patch: `522/522 PASS`
- player counts: `1, 2, 3, 4`
- exactly one owned investigator per player: `PASS`
- unique controls: `PASS`
- canonical SQL party consistency: `PASS`
- interface control-map consistency: `PASS`
- independent player knowledge partitions: `PASS`
- Keeper→Player leaks: `0`
- isolated player interfaces: `PASS`
- failed player action corrupts siblings: `false`
- silent character-owner transfer: blocked
- silent player-character rebind: blocked
- multiplayer bootstrap: atomic
- Checkpoint 329 portable regression: `199/199 PASS`
- Checkpoint 315/native core: `5/5 PASS`
- all five scenario statuses: `PASS_REAL`

Three parent-runtime defects were closed: partial live-party state after a later player's setup failure; character owner reassignment split-brain; and the Player Interface party-only ownership gate.

## Next phase

Proceed with:

`MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`

Work order:

1. For 1, 2, 3 and 4 players, save a fully independent multiplayer session and restore it into a fresh runtime.
2. Require exact preservation of player list, one-character-per-player ownership and the V2 control map.
3. Preserve each player's PV/SAN/PM/Chance, wounds/conditions and actual inventory independently.
4. Preserve each player's knowledge partition independently; Keeper knowledge must remain absent from every resumed player projection.
5. Verify that a save captured after a failed action contains no partial mutation from that failed player.
6. Reject tampered saves which alter ownership, party/control maps, player sets, character identities or knowledge partitions.
7. Require restore to fail closed before any player surface is exposed if the multiplayer V2 contract does not validate.
8. Keep all five scenarios `PASS_REAL` and re-run Checkpoint 330 plus Checkpoint 329/core regressions.

After successful save/resume recertification, proceed with `MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`.

Android APK work remains paused and unpromoted.

Automatic downgrade is forbidden.
