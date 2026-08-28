# Next safe action

## Checkpoint 328 complete

Current authority:

`Checkpoint 328 — STRICT_REPLAY_SAVE_RESUME_CONTINUITY_V1`

Verification:

- strict continuity matrix: `207/207 PASS`
- scenario keys: `scenario3` through `scenario7`
- player counts: `1, 2, 3, 4`
- uninterrupted vs save/resume: `REPLAY_MATCH`
- canonical digest: identical
- strict journal hash chain: identical
- deterministic roll tape: identical
- semantic commit trace: identical
- reordered / duplicated / state-inconsistent strict journals: fail closed
- historical Strict Replay regressions: PASS
- Checkpoint 315/native core: `5/5 PASS`

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `PASS_REAL`

## Next phase

Proceed with:

`OFFLINE_PLAYABLE_RUNTIME_PACKAGE_V1`

Work order:

1. Package the certified runtime without altering Checkpoint 328 authority.
2. Keep commercial scenario source PDFs/text external to the public package.
3. Provide an offline launcher and local persistent storage.
4. Wire scenario selection, 1–4 player setup, Player Interface V1, Checkpoint 327 save/resume and Checkpoint 328 Strict Replay continuity.
5. Ensure no network dependency is required for the native rules/state/runtime path.
6. Keep any optional local-AI narration clearly separate from the deterministic certified core.
7. Produce a testable offline archive before APK packaging.

Automatic downgrade is forbidden.
