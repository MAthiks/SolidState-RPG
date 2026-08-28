# Next safe action

## Recovery first

The next safe project action is to recover the exact artifact behind:

`Checkpoint 315 — SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`

Do not resume runtime implementation from RC1, Correction 018, or the v7.7 recovery baseline while this higher checkpoint is attested but unavailable.

## What to look for

Prefer files created/exported immediately before the official `SolidState_TODO_Checkpoint315.pdf` (2026-08-28), especially ZIP/JSON artifacts containing any of:

- `315`
- `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- `SOURCE_ROLE`
- `ENDPOINT_RECOVERY`
- `CHECKPOINT_STATE`
- `INSTALL_MANIFEST`
- `ScenarioRegistry`
- source-role mappings or endpoint recovery reports

If the exact original is recovered, verify its archive integrity and SHA-256 first, then import it on a new branch descended from `recovery/checkpoint-315-evidence`.

## Work allowed before recovery

Only non-destructive recovery/audit work is allowed: locating artifacts, hashing originals, documenting provenance and inspecting source documents. New runtime functionality must not be labeled as implementation of Checkpoint 315 until the runtime base is recovered.
