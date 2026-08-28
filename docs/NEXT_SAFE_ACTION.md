# Next safe action

## Checkpoint 325 complete

Current authority:

`Checkpoint 325 — SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`

Verification:

- release audit: `31/31 PASS`
- Checkpoint 324 isolated regression: `25/25 PASS`
- Checkpoint 323 isolated regression: `31/31 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- native core regression: `5/5 PASS`
- original source PDF / layout / source-evidence digest: `PASS`
- clue-to-scene anchors used as causal edges: `0 / 107`
- Keeper→Player leaks: `0`
- resolver / scenario selection / tamper gates: `PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

Proceed with:

`MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`

Work order:

1. Test launch/session preparation with 1, 2, 3 and 4 distinct players.
2. Verify one independent character/control binding per player and reject duplicate or cross-owned bindings.
3. Verify independent knowledge partitions: information learned by one character must not appear to another without an explicit authorized transfer.
4. Recheck Player Interface V1 status panels and 3+1 assisted choices independently for every player.
5. Verify scenario certification status remains identical across multiplayer counts and Keeper data never enters a player surface.
6. Stress atomic player/character transactions so one player failure cannot corrupt other character states.
7. Produce a new checkpoint only after the full 1–4 player matrix passes.

After that, continue with save/resume and deterministic Strict Replay integration.

Automatic downgrade is forbidden.
