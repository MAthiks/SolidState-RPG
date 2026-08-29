# APPLY 333 — MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2

Parent authority: **Checkpoint 332 — MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2**.

Checkpoint 333 is a certification-only checkpoint. It adds no runtime behavior beyond the exact 330→331→332 contract; it certifies those layers together as one release stack.

## Reconstruction and source prerequisites

1. Start from the exact certified Checkpoint 329 runtime ZIP with SHA-256 `75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`.
2. Require ZIP CRC `PASS`, `verify_package.py` `PASS` over 173 immutable package files, and offline self-test `PASS` before applying later layers.
3. Reconstruct Checkpoints 330, 331 and 332 in order according to their `APPLY_*.md` instructions.
4. Verify the reconstructed added-module Git blob identities:
   - 330 `multiplayer_certification_v2.py`: `7dd495abe9eb0e44d3653334d39ca99d879debaa`
   - 331 `save_resume_multiplayer_v2.py`: `fe8caded08ec30f50a6f4c80a23de8fc5e35b510`
   - 332 `strict_replay_multiplayer_v2.py`: `fbcab13c95317907039a961d4af4f5592bb2ffc8`
5. Keep all commercial/private PDFs outside GitHub. Place the exact local source files into the runtime `sources/` directory so `SourcePackValidatorV1` reports all five scenarios source-ready.

## Audit

Copy `run_tests_chunk333.py` to the reconstructed runtime root and execute it there with the exact private source pack present.

Promotion requires:

- `2300/2300 PASS` on the combined source-backed full-stack matrix;
- 5 scenarios × 1–4 players;
- 12 interleaved actor-bound events per core case;
- targeted failed wrong-actor, invalid-roll and impossible-mechanical actions with zero mutation;
- Player/Keeper knowledge changes with Keeper→Player leaks fixed at `0`;
- multiple save/resume cuts at events 1, 6 and 11 for scenario3 across 1–4 players;
- cross-scenario 4-player save/resume at event 6 for scenario4–scenario7;
- actor-bound Strict Replay equality after restore and resumed segments;
- continuous/resumed canonical state, semantic SQL state and player views identical;
- bad HMAC, downgrade floor, control-map, ownership and knowledge tampering rejected without mutating live state;
- actor reattribution detected after rebuilding a valid hash chain;
- all five scenario statuses remain `PASS_REAL` and source-ready.

Also rerun the exact Checkpoint 332 matrix and require `558/558 PASS`, including duplicate, omission, reorder and actor-reattribution replay negatives.

## Result

Certified execution: `2300/2300 PASS`.
Checkpoint 332 rerun: `558/558 PASS`.
Keeper→Player leaks: `0`.
All five scenarios: `PASS_REAL`, source-ready.

Checkpoint 333 may therefore become the anti-rollback authority. Android APK work may resume only from this certified stack; no older runtime may replace it.
