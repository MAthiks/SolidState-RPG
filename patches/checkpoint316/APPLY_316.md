# Apply Checkpoint 316

Parent authority: Checkpoint `315 — SOURCE_ROLE_AND_ENDPOINT_RECOVERY_V1`.

Required parent archive SHA-256:

`5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`

## Patch application

1. Verify the parent Checkpoint 315 archive SHA-256 before modifying it.
2. Copy `solidstate_runtime/interface_v1.py` into the parent runtime at `solidstate_runtime/interface_v1.py`.
3. Append this export to `solidstate_runtime/__init__.py`:

`from .interface_v1 import ScenarioSelectionInterfaceV1, PlayerInterfaceV1, LaunchChainV1`

4. Copy `run_tests_chunk316.py` and `NATIVE_RUNTIME_CHUNK316_REPORT.json` to the runtime root.
5. Verify the SHA-256 values recorded in `CHECKPOINT_316.json`.
6. Run `run_tests_chunk316.py` and require `10/10 PASS`.
7. Re-run `run_tests_chunk315.py` and require `5/5 PASS`.
8. Re-run `run_tests.py` and require `5/5 PASS`.

## Certified scope

Checkpoint 316 certifies the TODO 315 tasks 1–5 only:

- Scenario Selection Interface V1.
- Player Interface V1.
- Normal/Libre open prompt plus Facile/Assisté `3 choices + 1 free action`.
- Launch chain scenario → validation → players → characters → session readiness.
- Player-surface Keeper-data leakage prevention.

It is an interface milestone, not a full release.

## Status invariants

No scenario status is promoted by this checkpoint. Scenario 3 remains `PASS_REAL`; scenarios 4–7 retain their Checkpoint 315 non-`PASS_REAL` classifications.

## Next phase

`SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1`
