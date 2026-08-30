from __future__ import annotations

import copy
import unittest

import lsnt_v1_7_state_binding_dev as binding

SECRET = b"solidstate-r1-c4b2-dev-secret"
SYNTHETIC_HASHES = {
    "LSNT_V1_7_KEEPER": "a" * 64,
    "LSNT_V1_7_PLAYER": "b" * 64,
}


def players(count: int) -> list[dict]:
    return [
        {"player_id": f"P{i}", "character_id": f"C{i}"}
        for i in range(1, count + 1)
    ]


class LSNTV17StateBindingDevTests(unittest.TestCase):
    def test_01_production_path_stays_blocked_without_real_hashes(self):
        r = binding.create_production_session(players(1))
        self.assertEqual(r["status"], "FAIL_CLOSED")
        self.assertEqual(r["code"], "SOURCE_HASH_PENDING")

    def test_02_synthetic_harness_is_explicitly_noncanonical(self):
        r = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)
        self.assertEqual(r["status"], "SYNTHETIC_TEST_SESSION_READY")
        self.assertEqual(r["identity_mode"], binding.SYNTHETIC_IDENTITY_MODE)
        self.assertTrue(r["state"]["dev_only"])
        self.assertFalse(r["state"]["authority_promoted"])

    def test_03_one_player_water(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["shared_resources"]["water_liters"], 32)

    def test_04_two_player_water(self):
        state = binding.create_synthetic_test_session(players(2), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["shared_resources"]["water_liters"], 48)

    def test_05_three_player_water(self):
        state = binding.create_synthetic_test_session(players(3), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["shared_resources"]["water_liters"], 64)

    def test_06_four_player_water(self):
        state = binding.create_synthetic_test_session(players(4), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["shared_resources"]["water_liters"], 80)

    def test_07_zero_players_rejected(self):
        with self.assertRaisesRegex(ValueError, "PLAYER_COUNT_OUT_OF_RANGE"):
            binding.create_synthetic_test_session([], source_hashes=SYNTHETIC_HASHES)

    def test_08_five_players_rejected(self):
        with self.assertRaisesRegex(ValueError, "PLAYER_COUNT_OUT_OF_RANGE"):
            binding.create_synthetic_test_session(players(5), source_hashes=SYNTHETIC_HASHES)

    def test_09_duplicate_player_rejected(self):
        rows = [{"player_id": "P1", "character_id": "C1"}, {"player_id": "P1", "character_id": "C2"}]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PLAYER_OR_CHARACTER_ID"):
            binding.create_synthetic_test_session(rows, source_hashes=SYNTHETIC_HASHES)

    def test_10_duplicate_character_rejected(self):
        rows = [{"player_id": "P1", "character_id": "C1"}, {"player_id": "P2", "character_id": "C1"}]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PLAYER_OR_CHARACTER_ID"):
            binding.create_synthetic_test_session(rows, source_hashes=SYNTHETIC_HASHES)

    def test_11_control_map_is_one_actor_one_character(self):
        state = binding.create_synthetic_test_session(players(4), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["control_map"], {"P1": "C1", "P2": "C2", "P3": "C3", "P4": "C4"})

    def test_12_private_knowledge_is_actor_bound(self):
        state = binding.create_synthetic_test_session(players(2), source_hashes=SYNTHETIC_HASHES)["state"]
        r = binding.add_private_knowledge(state, actor_player_id="P1", character_id="C1", fact_id="FACT_A")
        self.assertEqual(r["status"], "COMMITTED")
        self.assertEqual(state["party"]["P1"]["knowledge"], ["FACT_A"])
        self.assertEqual(state["party"]["P2"]["knowledge"], [])
        self.assertEqual(state["shared_knowledge"], [])

    def test_13_wrong_actor_knowledge_write_is_zero_mutation(self):
        state = binding.create_synthetic_test_session(players(2), source_hashes=SYNTHETIC_HASHES)["state"]
        before = binding.digest(state)
        r = binding.add_private_knowledge(state, actor_player_id="P1", character_id="C2", fact_id="FACT_X")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["code"], "ACTOR_CHARACTER_MISMATCH")
        self.assertEqual(before, binding.digest(state))

    def test_14_unknown_fact_cannot_be_shared(self):
        state = binding.create_synthetic_test_session(players(2), source_hashes=SYNTHETIC_HASHES)["state"]
        before = binding.digest(state)
        r = binding.share_knowledge(state, actor_player_id="P1", fact_id="UNKNOWN")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(before, binding.digest(state))

    def test_15_known_fact_shares_only_explicitly(self):
        state = binding.create_synthetic_test_session(players(2), source_hashes=SYNTHETIC_HASHES)["state"]
        binding.add_private_knowledge(state, actor_player_id="P1", character_id="C1", fact_id="FACT_A")
        self.assertEqual(state["shared_knowledge"], [])
        r = binding.share_knowledge(state, actor_player_id="P1", fact_id="FACT_A")
        self.assertEqual(r["status"], "COMMITTED")
        self.assertEqual(state["shared_knowledge"], ["FACT_A"])

    def test_16_player_view_contains_only_own_character(self):
        state = binding.create_synthetic_test_session(players(3), source_hashes=SYNTHETIC_HASHES)["state"]
        view = binding.player_view(state, "P2")
        self.assertEqual(view["status"], "READY")
        self.assertEqual(view["character"]["character_id"], "C2")
        serialized = str(view)
        self.assertNotIn("'C1'", serialized)
        self.assertNotIn("'C3'", serialized)
        self.assertNotIn("scenario_runtime", serialized)

    def test_17_player_view_has_no_keeper_graph(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        view = binding.player_view(state, "P1")
        serialized = str(view)
        self.assertNotIn("investigation_links", serialized)
        self.assertNotIn("sanity_loss_records", serialized)
        self.assertNotIn("canonical_graph_sha256", serialized)

    def test_18_initial_vehicle_and_fuel_contract(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        shared = state["shared_resources"]
        self.assertEqual(shared["vehicle"]["model"], "Ford Fordor C11ADF")
        self.assertEqual(shared["vehicle"]["condition"], "OPERATIONAL")
        self.assertEqual(shared["fuel"]["tank_state"], "FULL")
        self.assertEqual(shared["fuel"]["jerrycans_liters"], [20, 20])
        self.assertIsNone(shared["fuel"]["exact_tank_capacity_liters"])
        self.assertIsNone(shared["fuel"]["exact_consumption"])

    def test_19_initial_radio_batteries(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        self.assertEqual(state["shared_resources"]["radio"]["batteries"], 2)

    def test_20_romain_is_autonomous_not_replacement_pc(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        r = state["romain_persy"]
        self.assertEqual(r["name"], "Romain Persy")
        self.assertTrue(r["npc_autonomous"])
        self.assertFalse(r["replacement_pc"])

    def test_21_scenario_binding_uses_v17_only(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        s = state["scenario_runtime"]
        self.assertEqual(s["pair_id"], "LSNT-V1.7-STANDALONE-1942")
        self.assertFalse(s["legacy_runtime_allowed"])
        self.assertEqual(s["source_hashes"], SYNTHETIC_HASHES)

    def test_22_graph_binding_is_deterministic(self):
        self.assertEqual(binding.canonical_graph_sha256(), binding.canonical_graph_sha256())
        self.assertEqual(len(binding.canonical_graph_sha256()), 64)

    def test_23_save_restore_roundtrip_one_to_four_players(self):
        for count in range(1, 5):
            with self.subTest(count=count):
                state = binding.create_synthetic_test_session(players(count), source_hashes=SYNTHETIC_HASHES)["state"]
                binding.add_private_knowledge(state, actor_player_id="P1", character_id="C1", fact_id=f"FACT_{count}")
                bundle = binding.save_bundle(state, SECRET)
                restored = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
                self.assertEqual(restored["status"], "RESTORED_STRICT_DEV")
                self.assertEqual(binding.digest(restored["state"]), binding.digest(state))

    def test_24_bad_hmac_rejected(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        bundle = binding.save_bundle(state, SECRET)
        bundle["auth"]["hmac_sha256"] = "0" * 64
        r = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
        self.assertEqual(r["status"], "FAIL_CLOSED")
        self.assertEqual(r["code"], "SAVE_AUTHENTICATION_FAILED")

    def test_25_reauthenticated_pair_tamper_rejected(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        tampered = copy.deepcopy(state)
        tampered["scenario_runtime"]["pair_id"] = "LSNT-V1.5-MULTI-1942"
        bundle = binding.save_bundle(tampered, SECRET)
        r = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
        self.assertEqual(r["status"], "FAIL_CLOSED")
        self.assertEqual(r["code"], "SCENARIO_BINDING_MISMATCH")

    def test_26_reauthenticated_source_hash_tamper_rejected(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        tampered = copy.deepcopy(state)
        tampered["scenario_runtime"]["source_hashes"]["LSNT_V1_7_KEEPER"] = "c" * 64
        bundle = binding.save_bundle(tampered, SECRET)
        r = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
        self.assertEqual(r["code"], "SCENARIO_BINDING_MISMATCH")

    def test_27_reauthenticated_graph_binding_tamper_rejected(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        tampered = copy.deepcopy(state)
        tampered["scenario_runtime"]["canonical_graph_sha256"] = "d" * 64
        bundle = binding.save_bundle(tampered, SECRET)
        r = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
        self.assertEqual(r["code"], "SCENARIO_BINDING_MISMATCH")

    def test_28_reauthenticated_authority_flag_tamper_rejected(self):
        state = binding.create_synthetic_test_session(players(1), source_hashes=SYNTHETIC_HASHES)["state"]
        tampered = copy.deepcopy(state)
        tampered["authority_promoted"] = True
        bundle = binding.save_bundle(tampered, SECRET)
        r = binding.restore_synthetic_test_bundle(bundle, SECRET, SYNTHETIC_HASHES)
        self.assertEqual(r["code"], "DEV_AUTHORITY_FLAG_INVALID")

    def test_29_synthetic_source_set_must_be_exact(self):
        with self.assertRaisesRegex(ValueError, "SYNTHETIC_SOURCE_SET_INVALID"):
            binding.create_synthetic_test_session(players(1), source_hashes={"LSNT_V1_7_KEEPER": "a" * 64})

    def test_30_synthetic_hash_format_is_validated(self):
        bad = {"LSNT_V1_7_KEEPER": "x" * 64, "LSNT_V1_7_PLAYER": "b" * 64}
        with self.assertRaisesRegex(ValueError, "SYNTHETIC_HASH_FORMAT_INVALID"):
            binding.create_synthetic_test_session(players(1), source_hashes=bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
