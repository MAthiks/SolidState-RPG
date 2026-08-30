from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lsnt_v17_precompile_gate as gate

KEEPER_ROLE_MARKERS = ("DOCUMENT GARDIEN", "Version 1.7", "STANDALONE")
PLAYER_ROLE_MARKERS = ("DOSSIER JOUEUR", "Version 1.7", "STANDALONE")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("PYPDF_REQUIRED_FOR_DOCUMENT_IDENTITY_CHECK") from exc
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _verify_document(path: Path, *, source_id: str, pair_id: str, role_markers: tuple[str, ...]) -> dict:
    if not path.exists() or not path.is_file():
        return {"status": "BLOCKED", "code": "SOURCE_FILE_MISSING", "path": str(path)}
    with path.open("rb") as f:
        header = f.read(5)
    if header != b"%PDF-":
        return {"status": "BLOCKED", "code": "SOURCE_NOT_PDF", "path": str(path)}
    try:
        text = _extract_pdf_text(path)
    except Exception as exc:
        return {"status": "BLOCKED", "code": "PDF_TEXT_EXTRACTION_FAILED", "detail": str(exc)}
    required = (source_id, pair_id, *role_markers)
    missing = [marker for marker in required if marker not in text]
    if missing:
        return {"status": "BLOCKED", "code": "DOCUMENT_IDENTITY_MARKER_MISSING", "missing": missing}
    return {
        "status": "VERIFIED_FROM_BYTES",
        "source_id": source_id,
        "pair_id": pair_id,
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def materialize_pair(keeper_path: str | Path, player_path: str | Path) -> dict:
    keeper = _verify_document(Path(keeper_path), source_id=gate.KEEPER_ID, pair_id=gate.SCENARIO_ID, role_markers=KEEPER_ROLE_MARKERS)
    if keeper.get("status") != "VERIFIED_FROM_BYTES":
        return {"status": "BLOCKED", "code": "KEEPER_IDENTITY_FAILED", "keeper": keeper}
    player = _verify_document(Path(player_path), source_id=gate.PLAYER_ID, pair_id=gate.SCENARIO_ID, role_markers=PLAYER_ROLE_MARKERS)
    if player.get("status") != "VERIFIED_FROM_BYTES":
        return {"status": "BLOCKED", "code": "PLAYER_IDENTITY_FAILED", "keeper": keeper, "player": player}
    bound = gate.bind_exact_source_identities(
        keeper_sha256=keeper["sha256"],
        player_sha256=player["sha256"],
        keeper_bytes_verified=True,
        player_bytes_verified=True,
    )
    if bound.get("status") != "READY":
        return {"status": "BLOCKED", "code": "CRYPTOGRAPHIC_BINDING_FAILED", "binding": bound}
    return {
        "status": "SOURCE_IDENTITY_2_OF_2_VERIFIED",
        "scenario_id": gate.SCENARIO_ID,
        "keeper": keeper,
        "player": player,
        "manifest_status": bound["manifest"]["status"],
        "runtime_dependency_on_v1_5": False,
        "authority_promoted": False,
        "checkpoint_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("keeper_pdf")
    parser.add_argument("player_pdf")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = materialize_pair(args.keeper_pdf, args.player_pdf)
    raw = json.dumps(result, indent=2, sort_keys=True)
    print(raw)
    if args.output:
        Path(args.output).write_text(raw + "\n", encoding="utf-8")
    return 0 if result.get("status") == "SOURCE_IDENTITY_2_OF_2_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
