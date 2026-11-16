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
OUTDIR = Path(os.environ.get("R1_C1_OUTDIR", HERE / "rules_dist")).resolve()
STAGE = OUTDIR / "CoC7_Recovery_Rules_R1_Core"
ZIP_PATH = OUTDIR / "CoC7_Recovery_Rules_R1_Core.zip"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
HISTORICAL_47 = "6c179ffeb3f7d78e19fddc7c1246e2357e0411d6491334761ca0a069d6a35dd7"


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if OUTDIR.exists():
    shutil.rmtree(OUTDIR)
(STAGE / "rules_r1").mkdir(parents=True)

for relative in (
    "rules_r1/__init__.py",
    "rules_r1/core_rules.py",
    "rules_r1/RULES_PROVENANCE_R1.json",
    "rules_r1/test_core_rules.py",
):
    source = HERE / relative
    destination = STAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)

source_commit = os.environ.get("RECOVERY_SOURCE_COMMIT")
if not source_commit:
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()

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
    "schema": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_MANIFEST_V1",
    "package_id": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1",
    "status": "MIGRATION_CANDIDATE_NOT_CANONICAL_4_7",
    "source_commit": source_commit,
    "documentary_authority_floor": 333,
    "historical_compiled_rules_4_7_sha256": HISTORICAL_47,
    "claims_historical_4_7_identity": False,
    "immutable_files": rows,
}
(STAGE / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

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
    "schema": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_BUILD_REPORT_V1",
    "result": "PASS",
    "package_id": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1",
    "package": ZIP_PATH.name,
    "source_commit": source_commit,
    "zip_sha256": zip_sha,
    "zip_size": ZIP_PATH.stat().st_size,
    "zip_crc": "PASS",
    "manifest_sha256": sha256_file(STAGE / "PACKAGE_MANIFEST.json"),
    "immutable_files": len(rows),
    "historical_compiled_rules_4_7_sha256": HISTORICAL_47,
    "byte_identical_to_historical_4_7": zip_sha == HISTORICAL_47,
    "authority_promoted": False,
    "next_gate": "R1-C2_RUNTIME_RULES_INTEGRATION",
}
(OUTDIR / "R1_C1_RULES_BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
