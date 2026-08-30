import unittest

import source_identity_proof_v2 as m


def att(role, token, pages, created):
    return {
        "provider": m.PROVIDER,
        "role": role,
        "document_id": m.KEEPER_ID if role == "KEEPER" else m.PLAYER_ID,
        "pair_id": m.SCENARIO_ID,
        "page_count": pages,
        "provider_created_at": created,
        "provider_object_token_sha256": token,
        "full_document_retrieved": True,
        "identity_markers_verified": True,
    }


K = att("KEEPER", "a"*64, 3, "2026-08-25T05:10:49Z")
P = att("PLAYER", "b"*64, 1, "2026-08-25T05:10:50Z")


class SourceIdentityProofV2Tests(unittest.TestCase):
    def test_001_provider_pair_ready(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(proof["status"], "SOURCE_IDENTITY_PROVIDER_ATTESTED")

    def test_002_provider_is_dev_only(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="DEV_RUNTIME")["status"], "ALLOWED_DEV_ONLY")

    def test_003_provider_allows_dev_matrix(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="DEV_MATRIX")["status"], "ALLOWED_DEV_ONLY")

    def test_004_provider_blocks_module_ready(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="MODULE_READY")["code"],
                         "BYTE_EXACT_IDENTITY_REQUIRED_FOR_FREEZE_OR_PROMOTION")

    def test_005_provider_blocks_frozen_candidate(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="FROZEN_CANDIDATE")["status"], "BLOCKED")

    def test_006_provider_blocks_promotion(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="PROMOTION")["status"], "BLOCKED")

    def test_007_wrong_keeper_id_blocked(self):
        bad = dict(K); bad["document_id"] = m.PLAYER_ID
        self.assertEqual(m.build_provider_pair_proof(keeper=bad, player=P)["status"], "BLOCKED")

    def test_008_wrong_pair_blocked(self):
        bad = dict(P); bad["pair_id"] = "LSNT-V1.5-MULTI-1942"
        self.assertEqual(m.build_provider_pair_proof(keeper=K, player=bad)["status"], "BLOCKED")

    def test_009_partial_document_blocked(self):
        bad = dict(K); bad["full_document_retrieved"] = False
        self.assertEqual(m.build_provider_pair_proof(keeper=bad, player=P)["status"], "BLOCKED")

    def test_010_marker_failure_blocked(self):
        bad = dict(P); bad["identity_markers_verified"] = False
        self.assertEqual(m.build_provider_pair_proof(keeper=K, player=bad)["status"], "BLOCKED")

    def test_011_page_count_fail_closed(self):
        bad = dict(K); bad["page_count"] = 1
        self.assertEqual(m.build_provider_pair_proof(keeper=bad, player=P)["status"], "BLOCKED")

    def test_012_provider_collision_blocked(self):
        bad = dict(P); bad["provider_object_token_sha256"] = "a"*64
        self.assertEqual(m.build_provider_pair_proof(keeper=K, player=bad)["code"],
                         "KEEPER_PLAYER_PROVIDER_OBJECT_COLLISION")

    def test_013_legacy_pdf_hash_not_provider_token(self):
        bad = dict(K); bad["provider_object_token_sha256"] = next(iter(m.LEGACY_V15_PDF_HASHES))
        self.assertEqual(m.build_provider_pair_proof(keeper=bad, player=P)["status"], "BLOCKED")

    def test_014_byte_exact_ready(self):
        proof = m.build_byte_exact_pair_proof(
            keeper_sha256="c"*64, player_sha256="d"*64,
            keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(proof["status"], "SOURCE_IDENTITY_BYTE_EXACT")

    def test_015_byte_exact_allows_promotion_gate(self):
        proof = m.build_byte_exact_pair_proof(
            keeper_sha256="c"*64, player_sha256="d"*64,
            keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(m.permission_for(proof, target="PROMOTION")["status"], "ALLOWED")

    def test_016_old_v15_hash_rejected_as_pdf(self):
        proof = m.build_byte_exact_pair_proof(
            keeper_sha256=next(iter(m.LEGACY_V15_PDF_HASHES)),
            player_sha256="d"*64, keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(proof["status"], "BLOCKED")

    def test_017_unverified_pdf_bytes_blocked(self):
        proof = m.build_byte_exact_pair_proof(
            keeper_sha256="c"*64, player_sha256="d"*64,
            keeper_bytes_verified=False, player_bytes_verified=True)
        self.assertEqual(proof["status"], "BLOCKED")

    def test_018_public_projection_strips_secrets(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        pub = m.public_proof_projection(proof)
        raw = repr(pub)
        self.assertNotIn("provider_object_token_sha256", raw)
        self.assertNotIn("keeper_sha256", raw)
        self.assertNotIn("player_sha256", raw)

    def test_019_unknown_target_blocked(self):
        proof = m.build_provider_pair_proof(keeper=K, player=P)
        self.assertEqual(m.permission_for(proof, target="ANDROID")["status"], "BLOCKED")

    def test_020_pair_digest_stable(self):
        p1 = m.build_provider_pair_proof(keeper=K, player=P)
        p2 = m.build_provider_pair_proof(keeper=dict(K), player=dict(P))
        self.assertEqual(p1["pair_digest"], p2["pair_digest"])


if __name__ == "__main__":
    unittest.main()
