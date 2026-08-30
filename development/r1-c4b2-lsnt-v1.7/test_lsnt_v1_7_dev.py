from __future__ import annotations

import json
import unittest
from pathlib import Path

import lsnt_v1_7_router_dev as lsnt

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "LSNT_V1_7_SCENARIO_MANIFEST_DEV.json").read_text(encoding="utf-8"))


class LSNTV17DevTests(unittest.TestCase):
    def test_01_pair_identity_is_v17(self):
        self.assertEqual(lsnt.PAIR_ID, "LSNT-V1.7-STANDALONE-1942")
        self.assertEqual(MANIFEST["scenario"]["pair_id"], lsnt.PAIR_ID)

    def test_02_document_ids_are_v17(self):
        self.assertEqual(lsnt.KEEPER_DOCUMENT_ID, "LSNT-GARDIEN-V1.7-STANDALONE-1942")
        self.assertEqual(lsnt.PLAYER_DOCUMENT_ID, "LSNT-JOUEUR-V1.7-STANDALONE-1942")

    def test_03_v15_and_v16_are_provenance_only(self):
        self.assertFalse(MANIFEST["scenario"]["runtime_dependency_on_v1_5"])
        self.assertFalse(MANIFEST["scenario"]["runtime_dependency_on_v1_6"])
        self.assertEqual(MANIFEST["scenario"]["legacy_runtime_status"], "PROVENANCE_ONLY")

    def test_04_legacy_v15_pair_is_rejected(self):
        r = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id="LSNT-V1.5-MULTI-1942")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["code"], "LEGACY_SCENARIO_PAIR_FORBIDDEN")

    def test_05_legacy_v16_pair_is_rejected(self):
        r = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id="LSNT-V1.6-HM-1942")
        self.assertEqual(r["code"], "LEGACY_SCENARIO_PAIR_FORBIDDEN")

    def test_06_unknown_pair_is_rejected(self):
        r = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id="LSNT-V9")
        self.assertEqual(r["code"], "SCENARIO_PAIR_MISMATCH")

    def test_07_source_hashes_are_not_invented(self):
        self.assertIsNone(lsnt.EXPECTED_SOURCE_HASHES["LSNT_V1_7_KEEPER"])
        self.assertIsNone(lsnt.EXPECTED_SOURCE_HASHES["LSNT_V1_7_PLAYER"])
        self.assertIsNone(MANIFEST["source_gate"]["keeper"]["expected_sha256"])
        self.assertIsNone(MANIFEST["source_gate"]["player"]["expected_sha256"])

    def test_08_source_hash_pending_blocks_startup(self):
        r = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id=lsnt.PAIR_ID)
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(r["code"], "SOURCE_HASH_PENDING")

    def test_09_fake_hashes_cannot_bypass_pending_identity(self):
        fake = {sid: "0" * 64 for sid in lsnt.SOURCE_IDS}
        r = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id=lsnt.PAIR_ID, source_hashes=fake)
        self.assertEqual(r["code"], "SOURCE_HASH_PENDING")

    def test_10_structure_is_compiled_but_not_route_ready(self):
        self.assertEqual(MANIFEST["status"], "STRUCTURE_COMPILED_SOURCE_HASH_PENDING_NOT_ROUTE_READY")
        self.assertFalse(MANIFEST["promotion"]["frozen_candidate"])

    def test_11_supported_players_are_one_to_four(self):
        self.assertEqual(MANIFEST["scenario"]["supported_player_counts"], [1, 2, 3, 4])
        self.assertEqual(lsnt.public_descriptor()["supported_player_counts"], [1, 2, 3, 4])

    def test_12_romain_persy_identity(self):
        npc = MANIFEST["scenario_contract"]["romain_persy"]
        self.assertEqual(npc["name"], "Romain Persy")
        self.assertEqual(npc["age"], 33)
        self.assertTrue(npc["npc_autonomous"])
        self.assertTrue(npc["never_replacement_pc"])

    def test_13_graph_has_core_locations(self):
        nodes = set(lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["nodes"])
        expected = {
            "LSNT_START_BIR_HALIM", "LSNT_NODE_CONVOY", "LSNT_NODE_SIDI_MARUT",
            "LSNT_NODE_FORT_17B", "LSNT_NODE_OASIS", "LSNT_NODE_WADI",
            "LSNT_NODE_CAMP_SALVI", "LSNT_NODE_QASR_IREM",
            "LSNT_NODE_CROISSANT_CREUX", "LSNT_NODE_RADIO_AXE",
            "LSNT_NODE_CHAMBRE_ZENITH", "LSNT_NODE_ROUTE_COTIERE",
            "LSNT_NODE_AERODROME_TMIMI",
        }
        self.assertTrue(expected.issubset(nodes))

    def test_14_clue_network_is_non_linear(self):
        graph = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV
        self.assertFalse(graph["single_clue_required"])
        self.assertFalse(graph["clue_order_forced"])
        self.assertTrue(graph["alternative_routes_preserved"])
        self.assertEqual(graph["distinct_non_human_proof_routes"], 3)
        self.assertGreaterEqual(len(graph["investigation_links"]["LSNT_NODE_CONVOY"]), 3)

    def test_15_world_clock_has_eleven_source_events(self):
        clock = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["world_clock"]
        self.assertEqual(len(clock), 11)
        self.assertEqual(clock[0], ["J1 08:00", "MISSION_START"])
        self.assertEqual(clock[-1], ["J4 12:00", "CRITICAL_ZENITH_IF_DEVICE_OPEN"])

    def test_16_front_track_preserves_causality(self):
        front = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["front_track"]
        self.assertEqual(front["check_times"], ["06:00", "18:00"])
        self.assertTrue(front["facts_override_roll"])
        self.assertEqual(front["fallback_die"], "1D6")
        self.assertTrue(front["unit_teleportation_forbidden"])

    def test_17_travel_table_is_source_sized_and_not_pacing_driven(self):
        travel = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["travel_records"]
        self.assertEqual(len(travel), 7)
        self.assertEqual(travel[0][2:], [35, [50, 70]])
        self.assertEqual(travel[-1][2:], [40, [50, 80]])
        self.assertTrue(lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["world_time_authoritative"])

    def test_18_exposure_contract(self):
        exp = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["exposure"]
        self.assertEqual(exp["range"], [0, 6])
        self.assertEqual(exp["pow_check_thresholds"], [2, 4, 6])
        self.assertEqual(exp["increments"], {"BRIEF_ANOMALY": 1, "PROLONGED": 2, "DIRECT_CONTACT": 3})
        self.assertTrue(exp["trigger_for_suspense_forbidden"])

    def test_19_sanity_loss_table_is_materialized(self):
        san = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV["sanity_loss_records"]
        self.assertEqual(len(san), 6)
        self.assertEqual(san[0], ["SHADOW_MOVES_AFTER_STOP", "0", "1D3"])
        self.assertEqual(san[-1], ["UNDERSTAND_PROPAGATION_POTENTIAL", "1D4", "1D10"])

    def test_20_ten_ending_families_without_forced_single_ending(self):
        graph = lsnt.LSNT_V1_7_CANONICAL_GRAPH_DEV
        self.assertEqual(graph["ending_count"], 10)
        self.assertEqual(len(graph["ending_family_ids"]), 10)
        self.assertTrue(graph["causality_over_convergence"])

    def test_21_state_binding_has_persistent_multiplayer_fields(self):
        required = {
            "WORLD_TIME", "PARTY_SPLIT", "POSITION[CharacterID]", "HP", "SAN", "MP", "LUCK",
            "EXPOSURE", "INVENTORY", "SHARED_RESOURCES", "VEHICLE", "WATER", "FUEL", "AMMO",
            "RADIO", "FRONT", "FACTIONS", "KNOWLEDGE", "SHARED_KNOWLEDGE", "EVENTS",
            "CONSEQUENCES_PENDING",
        }
        self.assertTrue(required.issubset(set(lsnt.STATE_BINDING)))

    def test_22_player_projection_has_no_keeper_graph(self):
        blocked = lsnt.resolve_route_dev("SOLEIL_NOIR", requested_pair_id=lsnt.PAIR_ID)
        p = lsnt.player_projection_dev(blocked)
        serialized = json.dumps(p, sort_keys=True)
        self.assertNotIn("canonical_path", serialized)
        self.assertNotIn("investigation_links", serialized)
        self.assertNotIn("sanity_loss_records", serialized)
        self.assertFalse(p["scenario"]["keeper_truth_exposed"])

    def test_23_split_party_never_auto_shares_clues(self):
        self.assertFalse(MANIFEST["player_projection"]["split_party_auto_shares_clues"])
        self.assertTrue(MANIFEST["player_projection"]["per_character_knowledge"])

    def test_24_ford_exact_fuel_values_stay_fail_closed(self):
        f = MANIFEST["historical_technical_fail_closed"]
        self.assertEqual(f["ford_c11adf_exact_tank_capacity"], "UNKNOWN_UNTIL_VALIDATED")
        self.assertEqual(f["ford_c11adf_exact_consumption"], "UNKNOWN_UNTIL_VALIDATED")
        self.assertFalse(f["automatic_range_estimate_for_pacing"])

    def test_25_frozen_c4b_parent_is_not_mutated(self):
        self.assertIn("MAISON_PENDU", lsnt.ROUTES)
        self.assertEqual(lsnt.ROUTES["MAISON_PENDU"].source_ids, ("MAISON_PENDU_SOURCE",))
        self.assertEqual(lsnt.ROUTES["SOLEIL_NOIR"].source_pair_id, lsnt.PAIR_ID)

    def test_26_non_lsnt_routes_delegate_to_parent(self):
        r = lsnt.resolve_route_dev("BRUME")
        self.assertEqual(r["status"], "DELEGATED_TO_FROZEN_PARENT")
        self.assertEqual(r["route"]["scenario_key"], "BRUME")

    def test_27_no_promotion_side_effects(self):
        self.assertFalse(MANIFEST["authority_promoted"])
        self.assertFalse(MANIFEST["promotion"]["checkpoint334_created"])
        self.assertFalse(MANIFEST["promotion"]["android_promoted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
