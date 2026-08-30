import tempfile
import unittest
from pathlib import Path
from unittest import mock

import materialize_v17_source_identity as m
import lsnt_v17_precompile_gate as gate


class MaterializeV17Tests(unittest.TestCase):
    def make_pdf(self, root: Path, name: str, payload: bytes) -> Path:
        p = root / name
        p.write_bytes(b"%PDF-" + payload)
        return p

    def test_missing_keeper(self):
        with tempfile.TemporaryDirectory() as td:
            r = m.materialize_pair(Path(td) / "missing.pdf", Path(td) / "player.pdf")
            self.assertEqual(r["code"], "KEEPER_IDENTITY_FAILED")

    def test_non_pdf_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            k = Path(td) / "k.pdf"
            k.write_text("not pdf")
            r = m._verify_document(k, source_id=gate.KEEPER_ID, pair_id=gate.SCENARIO_ID, role_markers=m.KEEPER_ROLE_MARKERS)
            self.assertEqual(r["code"], "SOURCE_NOT_PDF")

    def test_missing_marker_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.make_pdf(Path(td), "k.pdf", b"abc")
            with mock.patch.object(m, "_extract_pdf_text", return_value="Version 1.7 STANDALONE DOCUMENT GARDIEN"):
                r = m._verify_document(p, source_id=gate.KEEPER_ID, pair_id=gate.SCENARIO_ID, role_markers=m.KEEPER_ROLE_MARKERS)
            self.assertEqual(r["code"], "DOCUMENT_IDENTITY_MARKER_MISSING")
            self.assertIn(gate.KEEPER_ID, r["missing"])

    def test_keeper_role_marker_required(self):
        with tempfile.TemporaryDirectory() as td:
            p = self.make_pdf(Path(td), "k.pdf", b"abc")
            text = f"{gate.KEEPER_ID} {gate.SCENARIO_ID} Version 1.7 STANDALONE"
            with mock.patch.object(m, "_extract_pdf_text", return_value=text):
                r = m._verify_document(p, source_id=gate.KEEPER_ID, pair_id=gate.SCENARIO_ID, role_markers=m.KEEPER_ROLE_MARKERS)
            self.assertEqual(r["code"], "DOCUMENT_IDENTITY_MARKER_MISSING")
            self.assertIn("DOCUMENT GARDIEN", r["missing"])

    def test_pair_materializes_from_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            k = self.make_pdf(root, "keeper.pdf", b"keeper unique bytes")
            p = self.make_pdf(root, "player.pdf", b"player unique bytes")
            ktext = f"{gate.KEEPER_ID} {gate.SCENARIO_ID} Version 1.7 STANDALONE DOCUMENT GARDIEN"
            ptext = f"{gate.PLAYER_ID} {gate.SCENARIO_ID} Version 1.7 STANDALONE DOSSIER JOUEUR"
            def extract(path):
                return ktext if Path(path) == k else ptext
            with mock.patch.object(m, "_extract_pdf_text", side_effect=extract):
                r = m.materialize_pair(k, p)
            self.assertEqual(r["status"], "SOURCE_IDENTITY_2_OF_2_VERIFIED")
            self.assertEqual(len(r["keeper"]["sha256"]), 64)
            self.assertEqual(len(r["player"]["sha256"]), 64)
            self.assertNotEqual(r["keeper"]["sha256"], r["player"]["sha256"])
            self.assertFalse(r["runtime_dependency_on_v1_5"])
            self.assertFalse(r["authority_promoted"])

    def test_old_hash_reuse_remains_blocked(self):
        with mock.patch.object(m, "_verify_document") as verify:
            old = next(iter(gate.V15_HASHES))
            verify.side_effect = [
                {"status": "VERIFIED_FROM_BYTES", "sha256": old, "source_id": gate.KEEPER_ID, "pair_id": gate.SCENARIO_ID, "byte_size": 1},
                {"status": "VERIFIED_FROM_BYTES", "sha256": "b" * 64, "source_id": gate.PLAYER_ID, "pair_id": gate.SCENARIO_ID, "byte_size": 1},
            ]
            r = m.materialize_pair("k", "p")
        self.assertEqual(r["code"], "CRYPTOGRAPHIC_BINDING_FAILED")
        self.assertEqual(r["binding"]["code"], "SUPERSEDED_HASH_REUSE_FORBIDDEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
