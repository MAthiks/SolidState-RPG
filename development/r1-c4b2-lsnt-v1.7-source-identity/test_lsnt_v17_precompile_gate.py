import json
import unittest
import lsnt_v17_precompile_gate as m


class V17PrecompileGateTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.SCENARIO_ID, "LSNT-V1.7-STANDALONE-1942")
        self.assertEqual(m.KEEPER_ID, "LSNT-GARDIEN-V1.7-STANDALONE-1942")
        self.assertEqual(m.PLAYER_ID, "LSNT-JOUEUR-V1.7-STANDALONE-1942")
        self.assertFalse(m.PRECOMPILE["runtime_dependency_on_v1_5"])

    def test_initial_state_fail_closed(self):
        self.assertEqual(m.PRECOMPILE["status"], "DRAFT_NON_EXECUTABLE_SOURCE_HASHES_PENDING")
        self.assertIsNone(m.PRECOMPILE["source_identity"]["keeper"]["sha256"])
        self.assertIsNone(m.PRECOMPILE["source_identity"]["player"]["sha256"])

    def test_structure(self):
        s = m.PRECOMPILE["structure"]
        self.assertEqual(len(s["world_clock"]), 11)
        self.assertEqual(s["front_checks"], ["0600", "1800"])
        self.assertEqual(s["ending_family_count"], 10)
        self.assertFalse(s["single_clue_indispensable"])
        self.assertEqual(s["minimum_independent_nonhuman_routes"], 3)
        self.assertEqual(s["individual_exposure_thresholds"], [2, 4, 6])
        self.assertTrue(s["knowledge_partition_required"])

    def test_travel(self):
        self.assertEqual(len(m.PRECOMPILE["travel"]), 7)
        for edge, row in m.PRECOMPILE["travel"].items():
            self.assertGreater(row["distance_km"], 0, edge)
            self.assertEqual(len(row["minutes"]), 2)
            self.assertLessEqual(row["minutes"][0], row["minutes"][1])

    def test_resources(self):
        r = m.PRECOMPILE["shared_resources"]
        self.assertEqual(r["water_liters_by_player_count"], {1: 32, 2: 48, 3: 64, 4: 80})
        self.assertEqual(r["team_radio_batteries"], 2)
        self.assertIsNone(r["fuel_tank_capacity_liters"])
        self.assertIsNone(r["fuel_consumption_l_per_100km"])

    def test_state_contract(self):
        required = {"WORLD_TIME", "PARTY_SPLIT", "POSITION", "KNOWLEDGE", "SHARED_KNOWLEDGE", "EVENTS", "CONSEQUENCES_PENDING", "WATER", "FUEL", "AMMO", "RADIO", "FRONT"}
        self.assertTrue(required.issubset(set(m.PRECOMPILE["state_contract"])))

    def test_hash_missing(self):
        r = m.bind_exact_source_identities(keeper_sha256=None, player_sha256=None)
        self.assertEqual(r["code"], "EXACT_SOURCE_HASH_MISSING")

    def test_hash_format(self):
        r = m.bind_exact_source_identities(keeper_sha256="x" * 64, player_sha256="b" * 64, keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(r["code"], "SOURCE_HASH_FORMAT_INVALID")

    def test_v15_hash_reuse_blocked(self):
        old = next(iter(m.V15_HASHES))
        r = m.bind_exact_source_identities(keeper_sha256=old, player_sha256="b" * 64, keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(r["code"], "SUPERSEDED_HASH_REUSE_FORBIDDEN")

    def test_unverified_bytes_blocked(self):
        r = m.bind_exact_source_identities(keeper_sha256="a" * 64, player_sha256="b" * 64)
        self.assertEqual(r["code"], "SOURCE_BYTES_NOT_VERIFIED")

    def test_collision_blocked(self):
        r = m.bind_exact_source_identities(keeper_sha256="a" * 64, player_sha256="a" * 64, keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(r["code"], "KEEPER_PLAYER_HASH_COLLISION")

    def test_verified_hashes_can_only_unlock_private_compilation(self):
        r = m.bind_exact_source_identities(keeper_sha256="a" * 64, player_sha256="b" * 64, keeper_bytes_verified=True, player_bytes_verified=True)
        self.assertEqual(r["status"], "READY")
        self.assertEqual(r["manifest"]["status"], "SOURCE_IDENTITY_2_OF_2_READY_FOR_PRIVATE_COMPILATION")

    def test_public_status_strips_hash_slots(self):
        p = m.public_precompile_status()
        self.assertNotIn("sha256", p["source_identity"]["keeper"])
        self.assertNotIn("sha256", p["source_identity"]["player"])

    def test_player_counts(self):
        for n in range(1, 5):
            p = m.player_projection_template(n)
            self.assertEqual(p["status"], "PLAYER_PROJECTION_TEMPLATE_READY")
            self.assertEqual(p["shared_resources"]["water_liters"], {1: 32, 2: 48, 3: 64, 4: 80}[n])
        self.assertEqual(m.player_projection_template(0)["status"], "BLOCKED")
        self.assertEqual(m.player_projection_template(5)["status"], "BLOCKED")

    def test_player_projection_no_guardian_values(self):
        forbidden = ("fragment", "chambre du zenith", "croissant creux", "voss", "salvi", "le_midi_referme", "qasr_irem")
        for n in range(1, 5):
            raw = json.dumps(m.player_projection_template(n), ensure_ascii=False).lower()
            for marker in forbidden:
                self.assertNotIn(marker, raw)
            p = m.player_projection_template(n)
            self.assertFalse(p["source_hashes_exposed"])
            self.assertFalse(p["canonical_graph_exposed"])
            self.assertFalse(p["guardian_truth_exposed"])

    def test_persy_spelling(self):
        raw = json.dumps(m.PRECOMPILE, ensure_ascii=False)
        self.assertIn("PERSY", raw)
        self.assertNotIn("PERCY", raw)

    def test_activation_policy(self):
        a = m.PRECOMPILE["activation_policy"]
        self.assertTrue(a["requires_two_exact_pdf_hashes"])
        self.assertTrue(a["requires_hashes_computed_from_bytes"])
        self.assertFalse(a["reuse_v1_5_hashes"])
        self.assertFalse(a["fallback_to_superseded_pair"])
        self.assertFalse(a["compile_private_guardian_graph_before_identity"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
