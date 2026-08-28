# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 326 VERIFIED

- Checkpoint: `326`
- ID: `MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION_V1`
- Status: `VERIFIED_MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_CERTIFICATION`
- Parent: `325 — SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1`
- Checkpoint record: `patches/checkpoint326/CHECKPOINT_326.json`
- Checkpoint record Git blob SHA-1: `64302d18fb12cfb2a6fba4968b10c8423211bc73`
- Chunk 326 tests: `334/334 PASS`
- Checkpoint 325 regression: `31/31 PASS`
- Checkpoint 315 regression: `5/5 PASS`
- Native core regression: `5/5 PASS`

## Multiplayer certification

Checkpoint 326 certifies the native runtime for `1`, `2`, `3` and `4` players. Each player controls exactly one investigator owned by that player; character control is unique; player knowledge partitions remain independent; Keeper knowledge is never projected; cross-player control fails closed; and a failed character transaction cannot corrupt another character state.

The audit also verifies Player Interface V1 independently for every player: PV, SAN, PM, Chance, conditions and owned inventory; Normal/Libre remains an open `Que fais-tu ?` prompt; assisted mode remains exactly 3 contextual player-safe choices + 1 free action; foreign-player knowledge cannot authorize a suggestion; and the scenario → players → characters → `SESSION_READY` launch chain passes for all supported player counts.

During certification, the native engine exposed a real ownership flaw: `attach_character()` could previously attach a character owned by another player. Checkpoint 326 fixes this at engine level. Owner mismatch now fails closed without advancing the canonical commit or altering the party mapping.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Reconstruction chain

1. Verify the Checkpoint 315 original archive.
2. Apply Checkpoints 316 through 325 in order.
3. Apply `patches/checkpoint326/` according to `APPLY_326.md`.
4. Require `run_tests_chunk326.py` to pass `334/334`.
5. Re-run Checkpoint 325, Checkpoint 315, native-core and historical multiplayer 147/148/168 regressions.

## Next phase

`SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`

The next milestone must preserve selected scenario identity, full player-interface state, multiplayer control maps and independent knowledge across save/resume before deterministic Strict Replay integration.

Automatic downgrade is forbidden.
