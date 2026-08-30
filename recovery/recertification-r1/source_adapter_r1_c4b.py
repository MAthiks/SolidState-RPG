from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from source_adapter_r1 import SourceSpec, SOURCE_SPECS, sha256_file

SOURCE_SPECS_C4B = dict(SOURCE_SPECS)
SOURCE_SPECS_C4B["MAISON_PENDU_SOURCE"] = SourceSpec(
    "MAISON_PENDU_SOURCE",
    "03867cec90056dfb2777bdc6ff38013dd44acad9d8b08ecd571e795518ba1ee0",
    "SCENARIO_SOURCE",
)


def verify_source_c4b(source_id: str, path: str | Path) -> dict:
    spec = SOURCE_SPECS_C4B.get(source_id)
    if spec is None:
        return {"status": "BLOCKED", "code": "SOURCE_ID_UNKNOWN", "source_id": source_id}
    candidate = Path(path)
    if not candidate.is_file():
        return {"status": "BLOCKED", "code": "SOURCE_FILE_MISSING", "source_id": source_id}
    actual = sha256_file(candidate)
    if actual != spec.sha256:
        return {
            "status": "BLOCKED",
            "code": "SOURCE_HASH_MISMATCH",
            "source_id": source_id,
            "expected_sha256": spec.sha256,
            "actual_sha256": actual,
        }
    return {
        "status": "VERIFIED",
        "code": "SOURCE_IDENTITY_PASS",
        "source_id": source_id,
        "sha256": actual,
        "role": spec.role,
        "private": spec.private,
    }


def verify_required_c4b(mapping: dict[str, str | Path], required: list[str]) -> dict:
    results = []
    for source_id in required:
        result = verify_source_c4b(source_id, mapping.get(source_id, ""))
        results.append(result)
        if result["status"] != "VERIFIED":
            return {
                "status": "BLOCKED",
                "code": "PRIVATE_SOURCE_PREFLIGHT_FAILED",
                "failed_source": source_id,
                "results": results,
            }
    return {"status": "VERIFIED", "code": "PRIVATE_SOURCE_PREFLIGHT_PASS", "results": results}
