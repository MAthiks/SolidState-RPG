# Apply Checkpoint 318

Checkpoint 318 is a project-owned patch over the verified Checkpoint 317 chain. It does not republish scenario source text.

## Parent requirement

Reconstruct the verified Checkpoint 317 state first. That chain ultimately requires the original Checkpoint 315 archive with SHA-256:

`5d6a05baf68dc10fae9a9bae933a9c7edddf155ae13eade29c14dfe1119b195b`

Then apply Checkpoint 316 and Checkpoint 317 exactly as recorded before applying this patch.

## Files

Copy:

- `solidstate_runtime/source_backed_path_closure.py` -> runtime package
- `run_tests_chunk318.py` -> runtime root
- `BRUME_PATH_CLOSURE_318.json` -> runtime root or certification artifact directory
- `NATIVE_RUNTIME_CHUNK318_REPORT.json` -> certification artifact directory

Append the single import line from `INIT_APPEND_318.txt` to `solidstate_runtime/__init__.py` if it is not already present.

## Integrity

Verify the SHA-256 values recorded in `CHECKPOINT_318.json` before execution.

## Certification

Run:

`python run_tests_chunk318.py`

Required result:

- Chunk 318: `15/15 PASS`
- Checkpoint 317 regression: `PASS`
- Checkpoint 316 regression: `PASS`
- Checkpoint 315 regression: `PASS`
- Native core regression: `PASS`

## Status boundary

Checkpoint 318 proves one complete source-backed executable path for scenario 4 and therefore establishes `PASS_REAL_CANDIDATE` only.

It MUST NOT change scenario 4 to `PASS_REAL` by itself. The next gate is:

`SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`

No Keeper source text may be exposed through player-facing certification summaries.
