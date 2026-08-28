# Next safe action

## Checkpoint 323 complete

Current authority:

`Checkpoint 323 — SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1`

Verification:

- release audit: `31/31 PASS`
- Checkpoint 322 isolated regression: `29/29 PASS`
- Checkpoint 321 isolated regression: `27/27 PASS`
- original source PDF SHA-256: `PASS`
- exact source-evidence hashes: `PASS`
- Keeper→Player leaks: `0`
- resolver / scenario selection / tamper gates: `PASS`
- alternative endings and open conclusion preserved

Scenario status now:

- scenario3: `PASS_REAL`
- scenario4: `PASS_REAL`
- scenario5: `PASS_REAL`
- scenario6: `PASS_REAL`
- scenario7: `COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN`

## Next phase

Proceed with:

`SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1`

Target scenario: L'Explorateur assassiné.

Work order:

1. Recover a defensible player-safe start from source evidence.
2. Reuse the existing investigation topology only as provenance; graph order or clue adjacency alone cannot create causal edges.
3. Recover explicit clue/action/condition transitions toward a supported terminal or conclusion state.
4. Execute any complete path through the generic transition layer.
5. Preserve Keeper/Player partitioning and keep hidden evidence off the player surface.
6. Produce a `PASS_REAL_CANDIDATE` milestone first. Any release promotion must remain a separate audit.

Automatic downgrade is forbidden.
