import json
import tempfile
from pathlib import Path

from source_adapter_r1 import verify_source

checks = []


def ck(name, condition):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError(name)


def run():
    ck("unknown_id_blocked", verify_source("UNKNOWN", "/tmp/nope")["code"] == "SOURCE_ID_UNKNOWN")
    ck("missing_file_blocked", verify_source("COC7_KEEPER", "/tmp/nope")["code"] == "SOURCE_FILE_MISSING")
    path = Path(tempfile.mkdtemp()) / "fake.pdf"
    path.write_bytes(b"not the private source")
    result = verify_source("COC7_KEEPER", path)
    ck("hash_mismatch_blocked", result["code"] == "SOURCE_HASH_MISMATCH")
    ck("hash_mismatch_never_verified", result["status"] != "VERIFIED")
    report = {
        "schema": "SOLIDSTATE_RECOVERY_SOURCE_ADAPTER_R1_TEST_V1",
        "result": "PASS",
        "passed": len(checks),
        "total": len(checks),
        "scope": "fail-closed public CI; exact private source identity is verified only in local R1-C precheck",
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
