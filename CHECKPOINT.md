# Official development checkpoint

## Checkpoint 326 — VERIFIED MULTIPLAYER 1–4 CERTIFICATION

- Checkpoint: `326`
- ID: `MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`
- Parent: `325 — SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`
- Record: `patches/checkpoint326/CHECKPOINT_326.json`
- Record Git blob SHA-1: `64302d18fb12cfb2a6fba4968b10c8423211bc73`

## Certified scope

Checkpoint 326 certifies the native runtime for 1–4 independent players. The certified contract requires exactly one owned investigator per player, unique control, separate player-visible knowledge, no Keeper-knowledge projection, fail-closed cross-player control, and per-character transaction isolation.

Player Interface V1 is verified independently for every supported player count. Each player receives only their own PV/SAN/PM/Chance/conditions/inventory projection; Normal/Libre remains an open prompt; assisted mode remains exactly `3 choices + 1 free action`; and a suggestion that requires another player's knowledge is blocked.

The launch chain is also certified for 1, 2, 3 and 4 players through `SESSION_READY` with the exact player→character control map.

## Runtime correction discovered by the audit

The pre-326 native `SolidStateEngine.attach_character()` accepted a character even when `characters.owner_id` belonged to another player. Checkpoint 326 adds an engine-level ownership gate and foreign-control guard. Invalid attachment now returns a rollback result without changing canonical state, SQL party mapping or commit sequence.

## Verification

- `run_tests_chunk326.py`: `334/334 PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native runtime regression: `5/5 PASS`
- historical multiplayer Chunk 147: `3/3 PASS`
- historical multiplayer Chunk 148: `2/2 PASS`
- historical multiplayer Chunk 168: `3/3 PASS`
- supported player counts: `1, 2, 3, 4`
- Keeper knowledge exposed: `0`
- cross-player character control: blocked
- wrong-owner attachment: blocked before commit
- all five certified scenarios remain `PASS_REAL`

## Scenario status after Checkpoint 326

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

`SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`

## Anti-rollback invariant

1. Checkpoint 326 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 through 326 in order.
3. One player may control only their own investigator in the certified multiplayer path.
4. Player knowledge partitions remain independent unless a separately authorized transfer occurs.
5. A failed player/character transaction must not corrupt another investigator state.
6. Conversation memory never outranks verified artifacts and hashes.
