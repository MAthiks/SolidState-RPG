# Checkpoint 315 recovery status

## Target

- Checkpoint: `315`
- ID: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Evidence: `SolidState_TODO_Checkpoint315.pdf` identifies this checkpoint as the official working baseline.

## Current result

**BLOCKED — VERSION NON CONFIRMEE**

The exact Checkpoint 315 runtime/package, checkpoint manifest and authoritative SHA-256 have not been located in:

- the active uploaded recovery ZIP set,
- the File Library searches by checkpoint ID/module names,
- the GitHub repository.

## Proven lower chain

### Last fully described authority lock

- `SOLIDSTATE-AUTHORITY-LOCK-D5-304`
- Solid State `v7.8.1 candidate`
- Correction `018`
- Scenario pair `LSNT-V1.7-STANDALONE-1942`
- Ironman Commit `6`
- expected payload SHA-256 `18490fbad2ceaeda10d1ad43295474e6c6c0103014c93e004323ec0405df079e`
- authority-lock SHA-256 `5d82126e8e28d64c57f0ecb427766ac70a4b1746a228b60cff9e8ddec3ea893e`

The Correction 018 payload itself is also not currently present.

### Last physically verified recovery backup

- Solid State `7.7`
- CoC7 Rules Core `4.7`
- Working Backup SHA-256 `2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe`

## Later native-runtime evidence

A recovered README titled `Solid State Native Runtime — Big Chunk 1` proves that a later executable OOP runtime slice existed with:

- SQLite persistence,
- atomic transactions,
- canonical state,
- Ironman commits,
- hash-chained roll ledger,
- characters,
- party attachment.

The same README explicitly states that complete CoC7 rules, native equipment resolver, temporal registry, external verified RNG and full canonical scenario execution were not yet implemented in that slice.

No verified artifact chain currently proves that Big Chunk 1 equals, contains, or is a parent of Checkpoint 315.

## Checkpoint 315 documented work state

The official TODO records these priorities/statuses:

1. Scenario Selection Interface V1 — TODO.
2. Player Interface V1 — TODO.
3. 3 contextual choices + 1 free action — finalize/test.
4. Launch chain scenario → validation → players → PJ → session — TODO.
5. Certify no Keeper-data leakage in player interface — TODO.
6. Safe Transition Recovery V1 — next compiler phase.
7. Les Registres de Brume — blocked source/compilation.
8. L’Antre de l’abomination — partial.
9. Muse équivoque aux yeux de sel gemme — endpoints recovered.
10. L’Explorateur assassiné — endpoints recovered.
11. 1–4 player independent state/knowledge test — TODO.
12. Save/resume with selected scenario and full interface — TODO.
13. Strict Replay integration — TODO.
14. UI + scenario + Rules Core + anti-rollback regression battery — TODO.
15. Produce a new certified checkpoint after interface integration — TODO.

Scenario-status invariant: scenario 3 remains `PASS_REAL`; scenarios 4–7 must not be promoted to `PASS_REAL` until a source-backed executable path is proven.

## Recovery gate

Development from Checkpoint 315 resumes only after all required identity evidence is available:

- exact Checkpoint 315 package/runtime artifact,
- manifest/checkpoint state,
- authoritative SHA-256 or an original artifact from which it can be calculated,
- parent/provenance chain,
- integrity verification.

Until then:

- do not reconstruct 315 from memory,
- do not promote RC1, Correction 018 or v7.7 as the current runtime,
- do not claim TODO functions are implemented,
- do not alter scenario `PASS_REAL` statuses.
