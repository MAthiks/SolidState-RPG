from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

MODULE_ID = "LSNT_V1_7_SOURCE_IDENTITY_PROOF_V2"
SCENARIO_ID = "LSNT-V1.7-STANDALONE-1942"
KEEPER_ID = "LSNT-GARDIEN-V1.7-STANDALONE-1942"
PLAYER_ID = "LSNT-JOUEUR-V1.7-STANDALONE-1942"
PROVIDER = "CHATGPT_FILE_LIBRARY"

HEX64 = re.compile(r"^[0-9a-f]{64}$")
LEGACY_V15_PDF_HASHES = {
    "9c1e609d50250599a30fdb3ec899cf8b62cc9638944891900d0a982d958760f6",
    "9838b2f3e816e1ce08c29fa148eef765d2d1934a334ce8a78f8313fe6dc1b889",
}

DEV_TARGETS = {"DEV_RUNTIME", "DEV_MATRIX"}
BYTE_EXACT_TARGETS = {"MODULE_READY", "FROZEN_CANDIDATE", "PROMOTION"}


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _blocked(code: str, **extra: Any) -> dict:
    out = {"status": "BLOCKED", "code": code, "module_id": MODULE_ID}
    out.update(extra)
    return out


def validate_provider_document(attestation: dict, *, role: str) -> dict:
    if not isinstance(attestation, dict):
        return _blocked("ATTESTATION_NOT_OBJECT", role=role)

    expected_id = KEEPER_ID if role == "KEEPER" else PLAYER_ID
    expected_pages_min = 3 if role == "KEEPER" else 1

    required = {
        "provider": PROVIDER,
        "role": role,
        "document_id": expected_id,
        "pair_id": SCENARIO_ID,
        "full_document_retrieved": True,
        "identity_markers_verified": True,
    }
    for key, expected in required.items():
        if attestation.get(key) != expected:
            return _blocked("ATTESTATION_FIELD_MISMATCH", role=role, field=key)

    pages = attestation.get("page_count")
    if not isinstance(pages, int) or isinstance(pages, bool) or pages < expected_pages_min:
        return _blocked("ATTESTATION_PAGE_COUNT_INVALID", role=role)

    token_hash = str(attestation.get("provider_object_token_sha256", "")).lower()
    if not HEX64.fullmatch(token_hash):
        return _blocked("PROVIDER_OBJECT_TOKEN_HASH_INVALID", role=role)

    # A provider-object token hash is not a PDF-byte hash. It must never be
    # accepted in a slot that historically held v1.5 PDF byte hashes.
    if token_hash in LEGACY_V15_PDF_HASHES:
        return _blocked("LEGACY_PDF_HASH_MISUSED_AS_PROVIDER_TOKEN", role=role)

    created_at = attestation.get("provider_created_at")
    if not isinstance(created_at, str) or not created_at.endswith("Z"):
        return _blocked("PROVIDER_CREATED_AT_INVALID", role=role)

    normalized = {
        "provider": PROVIDER,
        "role": role,
        "document_id": expected_id,
        "pair_id": SCENARIO_ID,
        "page_count": pages,
        "provider_created_at": created_at,
        "provider_object_token_sha256": token_hash,
        "full_document_retrieved": True,
        "identity_markers_verified": True,
    }
    return {
        "status": "PROVIDER_DOCUMENT_ATTESTED",
        "module_id": MODULE_ID,
        "role": role,
        "attestation_digest": _canonical_hash(normalized),
        "normalized": normalized,
    }


def build_provider_pair_proof(*, keeper: dict, player: dict) -> dict:
    k = validate_provider_document(keeper, role="KEEPER")
    if k.get("status") != "PROVIDER_DOCUMENT_ATTESTED":
        return _blocked("KEEPER_PROVIDER_ATTESTATION_FAILED", detail=k)

    p = validate_provider_document(player, role="PLAYER")
    if p.get("status") != "PROVIDER_DOCUMENT_ATTESTED":
        return _blocked("PLAYER_PROVIDER_ATTESTATION_FAILED", detail=p)

    if k["normalized"]["provider_object_token_sha256"] == p["normalized"]["provider_object_token_sha256"]:
        return _blocked("KEEPER_PLAYER_PROVIDER_OBJECT_COLLISION")

    pair_payload = {
        "scenario_id": SCENARIO_ID,
        "keeper_attestation_digest": k["attestation_digest"],
        "player_attestation_digest": p["attestation_digest"],
        "verification_level": "PROVIDER_ATTESTED",
        "raw_pdf_sha256_materialized": False,
        "runtime_dependency_on_v1_5": False,
    }
    return {
        "status": "SOURCE_IDENTITY_PROVIDER_ATTESTED",
        "module_id": MODULE_ID,
        "verification_level": "PROVIDER_ATTESTED",
        "pair_digest": _canonical_hash(pair_payload),
        "keeper": k,
        "player": p,
        "raw_pdf_sha256_materialized": False,
        "authority_promoted": False,
        "checkpoint_created": False,
    }


def build_byte_exact_pair_proof(
    *,
    keeper_sha256: str,
    player_sha256: str,
    keeper_bytes_verified: bool,
    player_bytes_verified: bool,
) -> dict:
    keeper_sha256 = str(keeper_sha256).lower()
    player_sha256 = str(player_sha256).lower()
    for role, value, verified in (
        ("KEEPER", keeper_sha256, keeper_bytes_verified),
        ("PLAYER", player_sha256, player_bytes_verified),
    ):
        if not HEX64.fullmatch(value):
            return _blocked("PDF_SHA256_INVALID", role=role)
        if value in LEGACY_V15_PDF_HASHES:
            return _blocked("SUPERSEDED_V1_5_PDF_HASH_REUSE_FORBIDDEN", role=role)
        if verified is not True:
            return _blocked("PDF_BYTES_NOT_VERIFIED", role=role)

    if keeper_sha256 == player_sha256:
        return _blocked("KEEPER_PLAYER_PDF_HASH_COLLISION")

    payload = {
        "scenario_id": SCENARIO_ID,
        "keeper_sha256": keeper_sha256,
        "player_sha256": player_sha256,
        "verification_level": "BYTE_EXACT",
        "runtime_dependency_on_v1_5": False,
    }
    return {
        "status": "SOURCE_IDENTITY_BYTE_EXACT",
        "module_id": MODULE_ID,
        "verification_level": "BYTE_EXACT",
        "pair_digest": _canonical_hash(payload),
        "keeper_sha256": keeper_sha256,
        "player_sha256": player_sha256,
        "raw_pdf_sha256_materialized": True,
        "authority_promoted": False,
        "checkpoint_created": False,
    }


def permission_for(proof: dict, *, target: str) -> dict:
    if target not in DEV_TARGETS | BYTE_EXACT_TARGETS:
        return _blocked("UNKNOWN_PERMISSION_TARGET", target=target)
    level = proof.get("verification_level") if isinstance(proof, dict) else None
    status = proof.get("status") if isinstance(proof, dict) else None

    if level == "BYTE_EXACT" and status == "SOURCE_IDENTITY_BYTE_EXACT":
        return {
            "status": "ALLOWED",
            "target": target,
            "verification_level": "BYTE_EXACT",
            "portable_byte_identity": True,
        }

    if level == "PROVIDER_ATTESTED" and status == "SOURCE_IDENTITY_PROVIDER_ATTESTED":
        if target in DEV_TARGETS:
            return {
                "status": "ALLOWED_DEV_ONLY",
                "target": target,
                "verification_level": "PROVIDER_ATTESTED",
                "portable_byte_identity": False,
                "promotion_allowed": False,
            }
        return _blocked(
            "BYTE_EXACT_IDENTITY_REQUIRED_FOR_FREEZE_OR_PROMOTION",
            target=target,
            verification_level="PROVIDER_ATTESTED",
        )

    return _blocked("SOURCE_IDENTITY_PROOF_INVALID", target=target)


def public_proof_projection(proof: dict) -> dict:
    if not isinstance(proof, dict):
        return _blocked("SOURCE_IDENTITY_PROOF_INVALID")
    out = {
        "status": proof.get("status"),
        "module_id": MODULE_ID,
        "scenario_id": SCENARIO_ID,
        "verification_level": proof.get("verification_level"),
        "raw_pdf_sha256_materialized": bool(proof.get("raw_pdf_sha256_materialized")),
        "runtime_dependency_on_v1_5": False,
        "authority_promoted": False,
        "checkpoint_created": False,
    }
    # Provider object tokens, raw PDF hashes and private document content are
    # intentionally absent from the public projection.
    return copy.deepcopy(out)
