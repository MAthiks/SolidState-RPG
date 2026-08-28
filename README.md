# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 328 VERIFIED

- Checkpoint: `328`
- ID: `STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`
- Parent: `327 — SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`
- Record: `patches/checkpoint328/CHECKPOINT_328.json`
- Record Git blob SHA-1: `7d88dd5c481948d593644c98db93ca6cc9a2c9d5`
- Chunk 328 tests: `207/207 PASS`
- Strict Replay historical regressions: `2/2 + 4/4 + 2/2 PASS`
- Checkpoint 315/native core: `5/5 PASS`

## Strict Replay save/resume continuity

Checkpoint 328 proves that an uninterrupted session and the same session interrupted after four strict events, saved through Checkpoint 327, restored into a fresh engine and continued produce the same canonical digest, strict-state digest, strict journal hash chain, deterministic roll tape, action order and semantic commit trace.

The matrix covers all five currently certified scenario keys and player counts `1`, `2`, `3`, `4`. Strict Replay does not reroll on resume: supplied roll values are part of the strict event payload. Reordered or duplicated replay events, or a final strict state inconsistent with the journal, fail closed even when the save bundle is re-authenticated.

## Scenario status

- scenario3: `PASS_REAL`
- scenario4 — Les Registres de Brume: `PASS_REAL`
- scenario5 — L'Antre de l'abomination: `PASS_REAL`
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`
- scenario7 — L'Explorateur assassiné: `PASS_REAL`

## Next phase

`OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`

The next milestone packages the certified runtime for practical offline play without changing the Checkpoint 328 authority or publishing commercial scenario source text.

Automatic downgrade is forbidden.
