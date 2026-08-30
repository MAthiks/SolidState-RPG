from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    sha256: str
    role: str
    private: bool = True


SOURCE_SPECS = {
    "COC7_KEEPER": SourceSpec(
        "COC7_KEEPER",
        "691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779",
        "RULEBOOK",
    ),
    "COC7_INVESTIGATOR": SourceSpec(
        "COC7_INVESTIGATOR",
        "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17",
        "RULEBOOK",
    ),
    "AE_COLLECTION": SourceSpec(
        "AE_COLLECTION",
        "31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143",
        "SCENARIO_COLLECTION",
    ),
    "BRUME_KEEPER": SourceSpec(
        "BRUME_KEEPER",
        "76dc387ef0d24e2f03d5c2e906c89ac5709552a698a9c8d93a3df5fa8282a0fa",
        "KEEPER_SCENARIO",
    ),
    "BRUME_PLAYER": SourceSpec(
        "BRUME_PLAYER",
        "86c414eb4d28d7bb907799b5b0e9fea2de4c600fd4d2792e304381e0688fb20b",
        "PLAYER_SCENARIO",
    ),
    "ANTRE_SOURCE": SourceSpec(
        "ANTRE_SOURCE",
        "4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb",
        "SCENARIO_SOURCE",
    ),
    "SOLEIL_NOIR_KEEPER": SourceSpec(
        "SOLEIL_NOIR_KEEPER",
        "9c1e609d50250599a30fdb3ec899cf8b62cc9638944891900d0a982d958760f6",
        "KEEPER_SCENARIO",
    ),
    "SOLEIL_NOIR_PLAYER": SourceSpec(
        "SOLEIL_NOIR_PLAYER",
        "9838b2f3e816e1ce08c29fa148eef765d2d1934a334ce8a78f8313fe6dc1b889",
        "PLAYER_SCENARIO",
    ),
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(source_id: str, path: str | Path) -> dict:
    spec = SOURCE_SPECS.get(source_id)
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


def verify_required(mapping: dict[str, str | Path], required: list[str]) -> dict:
    results = []
    for source_id in required:
        result = verify_source(source_id, mapping.get(source_id, ""))
        results.append(result)
        if result["status"] != "VERIFIED":
            return {
                "status": "BLOCKED",
                "code": "PRIVATE_SOURCE_PREFLIGHT_FAILED",
                "failed_source": source_id,
                "results": results,
            }
    return {
        "status": "VERIFIED",
        "code": "PRIVATE_SOURCE_PREFLIGHT_PASS",
        "results": results,
    }
