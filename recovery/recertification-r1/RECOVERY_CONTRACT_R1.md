# Recovery Recertification R1 — Contract

## Identity

- Generation: `RECOVERY_RECERTIFICATION_R1`
- Stage: `R1-A_PUBLIC_PROVENANCE`
- Base commit: `5936b9e67af65b5a4d7d9c2d18ae6c44a7829db7`
- Documentary authority floor: `Checkpoint 333 — MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2`
- Status: `CANDIDATE_NOT_AUTHORITY`

This generation is **not** Checkpoint 329, 330, 331, 332, 333 or 334. It is a new recovery lineage created because the exact certified Checkpoint 329 runtime bytes are no longer available.

## Historical gap

The missing historical artifact remains:

`SolidState_Offline_Runtime_v1_Checkpoint329.zip`

Certified historical SHA-256:

`75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add`

R1 MUST NOT generate a file and claim that historical identity unless the produced bytes independently hash to that exact value. A different byte sequence receives a new recovery identity and a new SHA-256.

## R1-A — public provenance gate

R1-A may pass only if all of the following are true:

1. The branch descends from the exact Checkpoint 333 `main` commit above.
2. `CHECKPOINT.md` and `CHECKPOINT_333.json` retain their certified Git blob identities.
3. The materialized Checkpoint 330, 331 and 332 modules retain the exact Git blob identities recorded by Checkpoint 333.
4. Checkpoint 333 still records `2300/2300 PASS`, source-backed certification, Android floor 333 and automatic downgrade forbidden.
5. The lost Checkpoint 329 ZIP is not silently recreated or tracked as if original.
6. No commercial/private PDF is added to the public repository.
7. Python source in the repository remains syntactically compilable.

Passing R1-A proves only public provenance and contract continuity. It does **not** prove a reconstructed playable runtime.

## R1-B — new runtime materialization

R1-B will assemble a new runtime from actually materialized versioned code/evidence. The resulting package must:

- use a new recovery package name;
- have a newly calculated SHA-256;
- contain an immutable package manifest;
- include a package verifier and offline self-test;
- never claim byte identity with the lost Checkpoint 329 ZIP unless the SHA-256 is exactly identical;
- preserve the Checkpoint 333 behavioral contracts as minimum requirements.

## R1-C — private source-backed recertification

Commercial/private source PDFs remain local and outside GitHub. With the exact private source pack present, promotion requires a full source-backed regression at least equivalent to the certified stack, including:

- multiplayer 1–4 ownership/control/knowledge isolation;
- atomic save/resume and non-destructive tamper rejection;
- actor-bound Strict Replay with no reroll;
- duplicate/omit/reorder/actor-reattribution negatives;
- Keeper→Player leaks = `0`;
- all five currently certified scenarios remaining source-ready and `PASS_REAL` only if the new runtime actually proves those gates;
- a combined full-stack matrix at least equivalent to Checkpoint 333 (`2300/2300` historical reference) plus the exact Checkpoint 332 replay matrix (`558/558` historical reference), or a documented stricter successor matrix.

## Promotion rule

R1 does not alter `CHECKPOINT.md`, `manifest/authority_floor.json`, or `main` merely by passing R1-A. A new authority may be created only after R1-B and R1-C produce fresh cryptographic identities and complete passing evidence. Automatic downgrade remains forbidden.
