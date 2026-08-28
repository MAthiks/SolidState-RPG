# Official development checkpoint

## Checkpoint 328 — VERIFIED STRICT REPLAY CONTINUITY

- Checkpoint: `328`
- ID: `STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`
- Parent: `327 — SAVE_RESUME_SELECTED_SCENARIO_AND_FULL_INTERFACE_V1`
- Record: `patches/checkpoint328/CHECKPOINT_328.json`
- Record Git blob SHA-1: `7d88dd5c481948d593644c98db93ca6cc9a2c9d5`

## Certified scope

Checkpoint 328 certifies deterministic Strict Replay continuity across a real save/resume boundary. Continuous execution and interrupted execution resume to the same canonical state, strict journal hash chain, deterministic roll sequence, action order and semantic commit trace.

The certification matrix covers scenario3 through scenario7 and 1–4 players, with eight strict events per session and a save after event four. Resume uses the Checkpoint 327 authenticated save implementation identified by Git blob SHA-1 `85f3232ca2b3b855dd5ae05a4630324551dc9a82`.

Strict Replay never silently rerolls. Reordered, duplicated or state-inconsistent strict journals fail closed before resumed play is accepted.

## Verification

- `run_tests_chunk328.py`: `207/207 PASS`
- Strict Replay Chunk 259: `2/2 PASS`
- Strict Replay Chunk 263: `4/4 PASS`
- Strict release gate Chunk 270: `2/2 PASS`
- Checkpoint 315: `5/5 PASS`
- native core: `5/5 PASS`
- all five scenario statuses remain `PASS_REAL`

## Next phase

`OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`

## Anti-rollback invariant

1. Checkpoint 328 is the current verified authority.
2. Reconstruction requires verified 327 plus Checkpoint 328.
3. Resume requires an authenticated Checkpoint 327 save and a valid strict replay journal.
4. Replay uses recorded deterministic roll values; it never rerolls them silently.
5. Conversation memory never outranks verified artifacts and hashes.
