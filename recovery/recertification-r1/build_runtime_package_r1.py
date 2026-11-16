#!/usr/bin/env python3

import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUTDIR = Path(os.environ.get("R1_B_OUTDIR", HERE / "dist")).resolve()
STAGE = OUTDIR / "SolidState_Recovery_Runtime_R1_B"
ZIP_PATH = OUTDIR / "SolidState_Recovery_Runtime_R1_B.zip"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
HISTORICAL_329 = "75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if OUTDIR.exists():
    shutil.rmtree(OUTDIR)
STAGE.mkdir(parents=True)
(STAGE / "runtime_r1").mkdir()

sources = [
    (HERE / "runtime_r1/__init__.py", STAGE / "runtime_r1/__init__.py"),
    (HERE / "runtime_r1/core.py", STAGE / "runtime_r1/core.py"),
    (HERE / "runtime_r1/self_test.py", STAGE / "runtime_r1/self_test.py"),
    (HERE / "verify_package.py", STAGE / "verify_package.py"),
    (HERE / "RECOVERY_RUNTIME_IDENTITY_R1_B.json", STAGE / "RECOVERY_RUNTIME_IDENTITY_R1_B.json"),
]
for source, destination in sources:
    shutil.copy2(source, destination)

head = os.environ.get("RECOVERY_SOURCE_COMMIT")
if not head:
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        head = "LOCAL_PROTOTYPE_NOT_GIT"

rows = []
for path in sorted(STAGE.rglob("*")):
    if path.is_file():
        relative = path.relative_to(STAGE).as_posix()
        data = path.read_bytes()
        rows.append({"path": relative, "sha256": sha256_bytes(data), "size": len(data)})

manifest = {
    "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_B_PACKAGE_MANIFEST_V1",
    "generation": "RECOVERY_RECERTIFICATION_R1",
    "stage": "R1-B_NEW_RUNTIME_MATERIALIZATION",
    "status": "CANDIDATE_NOT_AUTHORITY",
    "source_commit": head,
    "documentary_authority_floor": 333,
    "historical_checkpoint329_sha256": HISTORICAL_329,
    "claims_historical_329_byte_identity": False,
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
    "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_B_BUILD_REPORT_V1",
    "result": "PASS",
    "package": ZIP_PATH.name,
    "source_commit": head,
    "zip_sha256": zip_sha,
    "zip_size": ZIP_PATH.stat().st_size,
    "zip_crc": "PASS",
    "manifest_sha256": sha256_file(STAGE / "PACKAGE_MANIFEST.json"),
    "immutable_files": len(rows),
    "historical_checkpoint329_sha256": HISTORICAL_329,
    "byte_identical_to_historical_329": zip_sha == HISTORICAL_329,
    "status": "CANDIDATE_NOT_AUTHORITY",
    "next_gate": "R1-C_PRIVATE_SOURCE_BACKED_FULL_RECERTIFICATION",
}
(OUTDIR / "R1_B_BUILD_REPORT.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))
