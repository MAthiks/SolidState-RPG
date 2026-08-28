# Recovery / Application
1. Verify this package ZIP hash.
2. Verify the v7.7/4.7 Working Backup exact SHA-256.
3. If mismatch: STOP and declare VERSION NON CONFIRMÉE.
4. Apply INTEGRATION_PLAN_003.md in order.
5. Run REGRESSION_MATRIX.json tests.
6. Never overwrite the protected baseline.
7. Only after all tests pass, create a new v7.8-RC1 Working Backup and hash it.
