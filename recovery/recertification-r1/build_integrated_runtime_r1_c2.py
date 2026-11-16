#!/usr/bin/env python3

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUTDIR = Path(os.environ.get("R1_C2_OUTDIR", HERE / "c2_dist")).resolve()
STAGE = OUTDIR / "SolidState_Recovery_Runtime_R1_C2"
ZIP_PATH = OUTDIR / "SolidState_Recovery_Runtime_R1_C2.zip"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
FROZEN_RULES_SOURCE_COMMIT = "af1d1a0113e2181c9e827f0d111273be180ca670"
EXPECTED_RULES_SHA256 = "c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2"
HISTORICAL_329 = "75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if OUTDIR.exists():
    shutil.rmtree(OUTDIR)
STAGE.mkdir(parents=True)

rules_build_dir = Path(tempfile.mkdtemp(prefix="r1c2_rules_"))
env = os.environ.copy()
env["R1_C1_OUTDIR"] = str(rules_build_dir)
env["RECOVERY_SOURCE_COMMIT"] = FROZEN_RULES_SOURCE_COMMIT
subprocess.run(
    [sys.executable, str(HERE / "build_rules_package_r1.py")],
    cwd=REPO,
    env=env,
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
rules_zip = rules_build_dir / "CoC7_Recovery_Rules_R1_Core.zip"
actual_rules_sha = sha256_file(rules_zip)
if actual_rules_sha != EXPECTED_RULES_SHA256:
    raise SystemExit(
        f"Frozen R1-C1 Rules Package identity mismatch: {actual_rules_sha} != {EXPECTED_RULES_SHA256}"
    )

sources = [
    "runtime_r1/__init__.py",
    "runtime_r1/core.py",
    "rules_r1/__init__.py",
    "rules_r1/core_rules.py",
    "rules_r1/RULES_PROVENANCE_R1.json",
    "source_adapter_r1.py",
    "integrated_adjudication_r1_c2.py",
    "RECOVERY_RUNTIME_IDENTITY_R1_C2.json",
    "verify_package.py",
    "test_integration_public_r1_c2.py",
]
for relative in sources:
    source = HERE / relative
    destination = STAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)

rules_destination = STAGE / "rules" / rules_zip.name
rules_destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(rules_zip, rules_destination)

source_commit = os.environ.get("RECOVERY_SOURCE_COMMIT_C2")
if not source_commit:
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()

rows = []
for path in sorted(STAGE.rglob("*")):
    if path.is_file():
        rows.append(
            {
                "path": path.relative_to(STAGE).as_posix(),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )

manifest = {
    "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_PACKAGE_MANIFEST_V1",
    "generation": "RECOVERY_RECERTIFICATION_R1",
    "stage": "R1-C2_RUNTIME_RULES_INTEGRATION",
    "integration_id": "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_V1",
    "status": "CANDIDATE_NOT_AUTHORITY",
    "source_commit": source_commit,
    "documentary_authority_floor": 333,
    "embedded_rules_package": {
        "package_id": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1",
        "sha256": actual_rules_sha,
        "frozen_source_commit": FROZEN_RULES_SOURCE_COMMIT,
    },
    "historical_checkpoint329_sha256": HISTORICAL_329,
    "claims_historical_329_byte_identity": False,
    "private_sources_embedded": False,
    "immutable_files": rows,
}
(STAGE / "PACKAGE_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(STAGE.rglob("*")):
        if not path.is_file():
            continue
        relative = (Path(STAGE.name) / path.relative_to(STAGE)).as_posix()
        info = zipfile.ZipInfo(relative, FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o644 & 0xFFFF) << 16
        archive.writestr(info, path.read_bytes())

with zipfile.ZipFile(ZIP_PATH) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit(f"ZIP CRC failure: {bad}")

zip_sha = sha256_file(ZIP_PATH)
report = {
    "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_BUILD_REPORT_V1",
    "result": "PASS",
    "integration_id": "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_V1",
    "package": ZIP_PATH.name,
    "source_commit": source_commit,
    "zip_sha256": zip_sha,
    "zip_size": ZIP_PATH.stat().st_size,
    "zip_crc": "PASS",
    "manifest_sha256": sha256_file(STAGE / "PACKAGE_MANIFEST.json"),
    "immutable_files": len(rows),
    "embedded_rules_sha256": actual_rules_sha,
    "private_sources_embedded": False,
    "historical_checkpoint329_sha256": HISTORICAL_329,
    "byte_identical_to_historical_329": zip_sha == HISTORICAL_329,
    "authority_promoted": False,
    "next_gate": "R1-C3_COMPLETE_RULES_STATE_DELTA_AND_SCENARIO_RECERTIFICATION",
}
(OUTDIR / "R1_C2_BUILD_REPORT.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))
