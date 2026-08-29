# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 332 VERIFIED

- Checkpoint: `332`
- ID: `MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`
- Parent: `331 — MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2`
- Record: `patches/checkpoint332/CHECKPOINT_332.json`
- Record Git blob SHA-1: `a1a8159b12404c0174cfe55d01607a2a1b9a04a8`
- Strict Replay V2 matrix: `558/558 PASS`
- Matrix: 5 `PASS_REAL` scenarios × 1–4 players = 20 cases

## Multiplayer V2 chain

Checkpoint 330 certifies independent player state/control/knowledge. Checkpoint 331 certifies authenticated, atomic multiplayer save/resume. Checkpoint 332 now certifies actor-bound multiplayer Strict Replay across uninterrupted and save→resume execution.

Each strict event records the deterministic roll together with `player_id` and the investigator `character_id`, and validates that pair against the Multiplayer V2 control map. Continuous and resumed execution produce identical commit sequence, canonical digest, strict-state digest, journal hash chain, roll tape, action order and actor trace. Replay never rerolls a recorded value.

Duplicate, omitted and reordered events are rejected by revision/digest/hash-chain contracts. Wrong-character actions fail before commit. A deliberately re-attributed event whose hash chain is rebuilt is still detected when compared with the expected actor tape.

The complete parent certifications remain authoritative: Checkpoint 331 `987/987 PASS`, Checkpoint 330 `522/522 PASS`. The focused 332 parent regression is `30/30 PASS`; the parent matrices are not falsely reported as rerun by this checkpoint.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Next phase

`MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2`

The Android APK candidate remains paused and unpromoted.

Automatic downgrade is forbidden.
