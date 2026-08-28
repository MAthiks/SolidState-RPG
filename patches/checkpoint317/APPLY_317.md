# Apply Checkpoint 317

Parent authority: Checkpoint 316, itself applied to the verified Checkpoint 315 archive.

## Preconditions

1. Verify the original Checkpoint 315 archive SHA-256: `5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`.
2. Apply Checkpoint 316 Interface V1 exactly as documented in `patches/checkpoint316/`.
3. Confirm the Checkpoint 316 regression suite passes before applying this patch.

## Apply

1. Copy `solidstate_runtime/safe_transition_recovery.py` into the runtime package.
2. Append the exact line from `INIT_APPEND_317.txt` to `solidstate_runtime/__init__.py` if it is not already present.
3. Copy `run_tests_chunk317.py` to the runtime root.
4. Keep `SAFE_TRANSITION_RECOVERY_317.json` and `NATIVE_RUNTIME_CHUNK317_REPORT.json` as checkpoint evidence.
5. Run `python run_tests_chunk317.py`.

Expected result: `12/12 PASS` with zero `PASS_REAL` promotions.

## Source protection

No source text is republished by this patch. Transition evidence contains source references and SHA-256 hashes only. Keeper-only evidence remains Keeper-only.
