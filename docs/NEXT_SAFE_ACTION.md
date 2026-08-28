# Next safe action

## Recovery complete

Checkpoint 315 is now verified from the original archive.

- Checkpoint: `315`
- ID: `SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`
- Archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`
- Manifest verification: `1205 / 1205 PASS`
- Checkpoint test: `5/5 PASS`

## Current development branch

Use:

`dev315-safe-transition-recovery`

Do not use the old RC1 `develop` branch as the source of current runtime authority.

## Next compiler/runtime phase

Resume exactly from the Checkpoint 315 declared next phase:

`SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`

The objective is to recover only transitions that are explicitly supported by source language and can be bound to runtime entities without inference that would create false causal paths.

## Invariants to preserve

- scenario3 remains `PASS_REAL`.
- scenario4 remains `COMPILED_PROTECTED_NOT_PASS_REAL` until a source-backed executable start/causal path is proven.
- scenario5 remains `COMPILED_CANDIDATE_NOT_PATH_PROVEN` until the explicit start entity and path are proven.
- scenario6 remains `COMPILED_CANDIDATE_NOT_PATH_PROVEN` until safe typed transitions are proven.
- scenario7 remains `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN` until causal investigation transitions are proven.
- Endpoint/source-role recovery alone never promotes a scenario to `PASS_REAL`.

## Work order

1. Build a Safe Transition Recovery detector/gate using explicit source language only.
2. Apply it independently to scenarios 4–7.
3. Materialize typed transitions only when both endpoints and source authority are explicit.
4. Run regression preserving historical statuses by default.
5. Promote a scenario only after a complete source-backed executable path is demonstrated.
6. Produce the next checkpoint only after the new transition layer passes regression.
