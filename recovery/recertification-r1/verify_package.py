#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
failures = []

for row in manifest["immutable_files"]:
    path = ROOT / row["path"]
    if not path.is_file():
        failures.append({"path": row["path"], "reason": "MISSING"})
        continue
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != row["sha256"] or len(data) != row["size"]:
        failures.append(
            {
                "path": row["path"],
                "reason": "IDENTITY_MISMATCH",
                "expected_sha256": row["sha256"],
                "actual_sha256": actual,
                "expected_size": row["size"],
                "actual_size": len(data),
            }
        )

result = {
    "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_B_VERIFY_V1",
    "result": "PASS" if not failures else "FAIL",
    "verified_files": len(manifest["immutable_files"]) - len(failures),
    "total_files": len(manifest["immutable_files"]),
    "failures": failures,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not failures else 1)
