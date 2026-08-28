# Official development checkpoint

## Checkpoint 320 — VERIFIED SCENARIO 5 PATH PROOF

- Checkpoint: `320`
- ID: `SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1`
- Parent: `319 — SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1`
- Record: `patches/checkpoint320/CHECKPOINT_320.json`
- Record SHA-256: `d4f1ee742c546f7a8b28c3853393e7e292c0184600c99d3d1cdfe0dcba035697`

## Certified scope

Checkpoint 320 resolves the Checkpoint 315 task for L'Antre de l'abomination at the path-proof level only. It establishes a defensible player-safe start from the scenario invitation and proves one complete executable route through ten explicitly source-backed transitions to an open Keeper epilogue resolution.

The route proof uses fail-closed gates. Inferred transitions, ambiguous targets and editorial references alone are rejected. Conditional source branches remain conditional rather than being rewritten as mandatory canon.

Path proof status: `PASS_REAL_CANDIDATE`.

Release status: `pass_real = false`.

The historical `ANTRE_PASS_REAL_CERTIFICATE.json` is provenance only and is not reactivated as current release authority.

## Verification

- `run_tests_chunk320.py`: `22/22 PASS`
- Checkpoint 319 current-overlay regression: `PASS`
- Checkpoint 315 core regression: `PASS`
- native runtime regression: `PASS`
- isolated Checkpoint 318 reconstruction: `15/15 PASS`
- original `antre.pdf` SHA-256: `4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb` — `PASS`

## Packaging repair

Checkpoint 320 restores the complete verified Checkpoint 316 Interface V1 exports:

- `ScenarioSelectionInterfaceV1`
- `PlayerInterfaceV1`
- `LaunchChainV1`

The underlying Interface V1 module is the previously verified Checkpoint 316 module. This is a package/export reconstruction repair only; no interface behavior is changed.

## Scenario status after Checkpoint 320

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL_CANDIDATE_NOT_RELEASED`
- scenario6: `COMPILED_CANDIDATE_NOT_PATH_PROVEN`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next gate

`SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`

Scenario5 must remain blocked in the certified player scenario-selection interface until the separate release audit verifies the path proof, source integrity, status resolver boundary, Keeper/Player firewall and fail-closed tamper handling.

## Anti-rollback invariant

1. Checkpoint 320 is the current verified development authority.
2. Reconstruction requires verified 315 + patches 316 + 317 + 318 + 319 + 320 in order.
3. Path proof does not self-promote scenario5.
4. The older Antre PASS_REAL certificate remains historical provenance only.
5. Source text remains non-public; evidence uses source refs and hashes.
6. Conversation memory never outranks verified artifacts.
