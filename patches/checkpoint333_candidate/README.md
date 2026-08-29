# Checkpoint 333 candidate — MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2

Status: **PARTIAL_PASS_SOURCE_INDEPENDENT — NOT PROMOTED**.

Parent verified authority: **Checkpoint 332 — MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2**.

## What was actually executed

The exact certified Checkpoint 329 runtime ZIP was recovered and verified before reconstruction:

- SHA-256: `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`
- ZIP CRC: `PASS`
- `verify_package.py`: `PASS`, 173 files
- offline self-test: `PASS`

Checkpoints 330, 331 and 332 were then reconstructed in order. The three added runtime modules matched their repository Git blob SHA-1 identities exactly:

- 330 `multiplayer_certification_v2.py`: `7dd495abe9eb0e44d3653334d39ca99d879debaa`
- 331 `save_resume_multiplayer_v2.py`: `fe8caded08ec30f50a6f4c80a23de8fc5e35b510`
- 332 `strict_replay_multiplayer_v2.py`: `fbcab13c95317907039a961d4af4f5592bb2ffc8`

The combined source-independent audit completed **2300/2300 PASS** with **0 Keeper→Player leaks**.

Coverage included:

- all five registered scenarios mechanically exercised;
- 1, 2, 3 and 4-player sessions;
- 12-event interleaved actor-bound sequences per core case;
- Player and Keeper knowledge changes;
- targeted wrong-actor, invalid-roll and impossible-mechanical failures with zero mutation;
- multiple save/resume cuts at events 1, 6 and 11 for scenario3 across 1–4 players;
- cross-scenario 4-player save/resume checks for scenario4–scenario7;
- Strict Replay verification immediately after restore and after resumed segments;
- canonical-state, semantic SQL-table and player-view equality between continuous and resumed paths;
- tampered HMAC, checkpoint floor, control map, ownership and knowledge rejection;
- actor reattribution detection even after rebuilding a valid journal hash chain.

## Why this is not Checkpoint 333

The exact private scenario PDFs were located in the user's Library, but raw materialization into the execution environment returned HTTP 403. Therefore the source-backed `PASS_REAL` gates were **not rerun**.

This candidate must not update `CHECKPOINT.md`, README authority claims, or the anti-rollback floor. **Checkpoint 332 remains the current verified authority.**

## Promotion gate

Promote only after the same combined audit is rerun with the exact private source pack locally available and all five scenarios retain `PASS_REAL`, with zero Keeper→Player leaks and no regression in the 330→331→332 contract.
