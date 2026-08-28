# Apply Checkpoint 320

Parent authority: Checkpoint 319.

1. Reconstruct the verified Checkpoint 319 runtime chain.
2. Verify the scenario source layout SHA-256 is `adb1e8c0c9e525e32f6f5f4dde4e9c9d87a651e7f830b1c14ef8b23f5c6c5467`.
3. When the original `antre.pdf` is available, verify SHA-256 `4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb`.
4. Copy `solidstate_runtime/source_backed_route_v2.py` into the runtime package.
5. Replace `solidstate_runtime/interface_v1.py` with the included verified Checkpoint 316 full module. This is a packaging/export repair only; no Interface V1 behavior is changed.
6. Ensure `solidstate_runtime/__init__.py` exports `ScenarioSelectionInterfaceV1, PlayerInterfaceV1, LaunchChainV1` and append the line in `INIT_APPEND_320.txt`.
7. Copy `ANTRE_PATH_CLOSURE_320.json` alongside the checkpoint audit artifacts.
8. Run `run_tests_chunk320.py` and require `22/22 PASS`.

Checkpoint 320 proves one complete source-backed executable route from the player-facing invitation start to the source-authorized open epilogue resolution.

It does **not** promote scenario5 to PASS_REAL. The historical `ANTRE_PASS_REAL_CERTIFICATE.json` remains provenance only. Promotion requires a separate `SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1`.

No source text from `antre.pdf` is republished in this patch; public evidence stores source refs and SHA-256 values only.
