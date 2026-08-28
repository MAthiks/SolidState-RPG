# Next safe action

## Checkpoint 326 complete

Current authority:

`Checkpoint 326 — MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`

Verification:

- multiplayer matrix: `334/334 PASS`
- player counts certified: `1, 2, 3, 4`
- exactly one owned investigator per player: `PASS`
- unique control map: `PASS`
- independent player knowledge partitions: `PASS`
- Keeper knowledge exposed: `0`
- Player Interface V1 isolated per player: `PASS`
- Normal/Libre open prompt: `PASS`
- assisted 3 choices + 1 free action: `PASS`
- foreign-player knowledge cannot authorize a suggestion: `PASS`
- launch chain through `SESSION_READY`: `PASS`
- failed character transaction leaves other character states unchanged: `PASS`
- wrong-owner attachment fails without commit advance: `PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315/native core regressions: `5/5 PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

Proceed with:

`SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`

Work order:

1. Save and restore the selected scenario identity and certification authority without reselecting or silently downgrading the scenario.
2. Persist and restore the full `SESSION_READY` interface record, player list and exact control map for 1–4 players.
3. Persist and restore each player's PV, SAN, PM, Chance, injuries/conditions and actual inventory.
4. Persist and restore independent player knowledge partitions; Keeper knowledge must never enter a resumed player projection.
5. Verify resume does not duplicate, skip or reorder committed scenario/session state and does not invent a new commit history.
6. Detect missing, corrupted or tampered save state fail-closed before player narration resumes.
7. Re-run the complete 1–4 player matrix after resume and keep all five scenarios `PASS_REAL`.
8. Produce a new checkpoint before beginning deterministic Strict Replay integration.

After this milestone, continue with `STRICT_REPLAY_INTERFACE_SCENARIO_INTEGRATION_V1`.

Automatic downgrade is forbidden.
