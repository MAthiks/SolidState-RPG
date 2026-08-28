# Apply Checkpoint 322

Parent authority: Checkpoint 321.

1. Reconstruct and verify Checkpoint 321 first.
2. Require the original `L'Appel de Cthulhu 7 - Aventures Effroyables.pdf` to be available outside the public repository.
3. Verify its SHA-256 is `31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143`.
4. Copy `solidstate_runtime/source_backed_route_v3.py` into the runtime package.
5. Append `INIT_APPEND_322.txt` to `solidstate_runtime/__init__.py` if the export line is not already present.
6. Copy `scenario_candidates/scenario6/MUSE_PATH_CLOSURE_322.json` into scenario6.
7. Run `MUSE_SOURCE_PDF=/path/to/original.pdf python run_tests_chunk322.py`.
8. Require `29/29 PASS` before accepting Checkpoint 322.

Checkpoint 322 proves only one conditional source-backed path. It does not promote scenario6 to `PASS_REAL`.
Commercial source text/PDF must not be copied into the public repository.
