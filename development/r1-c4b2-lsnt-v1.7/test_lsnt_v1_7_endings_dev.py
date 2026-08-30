from __future__ import annotations

import unittest

import lsnt_v1_7_endings_dev as endings


def state(count=2):
    return {
        "party": {
            f"P{i}": {"character_id": f"C{i}", "dead": False, "incapacitated": False, "withdrawn": False}
            for i in range(1, count + 1)
        },
        "romain_persy": {"npc_autonomous": True, "replacement_pc": False, "dead": False},
    }


def ids(result):
    return [row["ending_id"] for row in result["eligible_endings"]]


class LSNTV17EndingDevTests(unittest.TestCase):
    def test_01_exactly_ten_families_materialized(self):
        self.assertEqual(len(endings.ENDING_FAMILIES), 10)

    def test_02_no_facts_no_ending(self):
        r = endings.evaluate_endings(state(), world_facts={})
        self.assertEqual(r["eligible_endings"], [])
        self.assertIsNone(r["automatic_selection"])

    def test_03_midi_referme_requires_both_facts(self):
        s = state()
        self.assertNotIn("LE_MIDI_REFERME", ids(endings.evaluate_endings(s, world_facts={"DEVICE_CLOSED": True})))
        r = endings.evaluate_endings(s, world_facts={"DEVICE_CLOSED": True, "LOCAL_THREAT_CONTAINED": True})
        self.assertIn("LE_MIDI_REFERME", ids(r))

    def test_04_victoire_militaire_requires_unresolved_phenomenon(self):
        r = endings.evaluate_endings(state(), world_facts={"PROGETTO_NERO_DESTROYED": True, "PHENOMENON_UNRESOLVED": True})
        self.assertIn("VICTOIRE_MILITAIRE", ids(r))

    def test_05_victoire_incomplete(self):
        r = endings.evaluate_endings(state(), world_facts={"FRAGMENT_REBURIED": True, "FUTURE_AWAKENING_POSSIBLE": True})
        self.assertIn("VICTOIRE_INCOMPLETE", ids(r))

    def test_06_convoi_de_lombre(self):
        r = endings.evaluate_endings(state(), world_facts={"VOSS_TRANSFERRED_FRAGMENT": True})
        self.assertIn("CONVOI_DE_LOMBRE", ids(r))

    def test_07_fragment_allie(self):
        r = endings.evaluate_endings(state(), world_facts={"ALLIES_RECOVERED_FRAGMENT": True})
        self.assertIn("FRAGMENT_ALLIE", ids(r))

    def test_08_qasr_irem_detruite(self):
        r = endings.evaluate_endings(state(), world_facts={"QASR_IREM_COLLAPSED": True})
        self.assertIn("QASR_IREM_DETRUITE", ids(r))

    def test_09_zenith_noir(self):
        r = endings.evaluate_endings(state(), world_facts={"MAJOR_EXPANSION_DAY4": True})
        self.assertIn("ZENITH_NOIR", ids(r))

    def test_10_alliance_amere(self):
        r = endings.evaluate_endings(state(), world_facts={"TEMPORARY_COOPERATION": True})
        self.assertIn("ALLIANCE_AMERE", ids(r))

    def test_11_enquete_abandonnee_all_active_pcs_withdraw(self):
        s = state(2)
        s["party"]["P1"]["withdrawn"] = True
        s["party"]["P2"]["withdrawn"] = True
        r = endings.evaluate_endings(s, world_facts={})
        self.assertIn("ENQUETE_ABANDONNEE", ids(r))

    def test_12_one_active_pc_not_withdrawn_blocks_abandon(self):
        s = state(2)
        s["party"]["P1"]["withdrawn"] = True
        r = endings.evaluate_endings(s, world_facts={})
        self.assertNotIn("ENQUETE_ABANDONNEE", ids(r))

    def test_13_one_pc_death_does_not_end_group(self):
        s = state(2)
        s["party"]["P1"]["dead"] = True
        r = endings.evaluate_endings(s, world_facts={})
        self.assertNotIn("GAME_OVER", ids(r))

    def test_14_all_controllable_pcs_dead_is_game_over(self):
        s = state(2)
        for row in s["party"].values():
            row["dead"] = True
        r = endings.evaluate_endings(s, world_facts={})
        self.assertIn("GAME_OVER", ids(r))

    def test_15_dead_and_incapacitated_mix_is_game_over(self):
        s = state(2)
        s["party"]["P1"]["dead"] = True
        s["party"]["P2"]["incapacitated"] = True
        r = endings.evaluate_endings(s, world_facts={})
        self.assertIn("GAME_OVER", ids(r))

    def test_16_no_causal_pursuit_is_game_over(self):
        r = endings.evaluate_endings(state(), world_facts={"NO_CAUSAL_PLAYABLE_PURSUIT": True})
        self.assertIn("GAME_OVER", ids(r))

    def test_17_romain_survival_does_not_prevent_game_over(self):
        s = state(1)
        s["party"]["P1"]["dead"] = True
        s["romain_persy"]["dead"] = False
        r = endings.evaluate_endings(s, world_facts={})
        self.assertIn("GAME_OVER", ids(r))

    def test_18_romain_never_becomes_replacement_pc(self):
        s = state(1)
        s["party"]["P1"]["dead"] = True
        self.assertFalse(s["romain_persy"]["replacement_pc"])
        self.assertIn("GAME_OVER", ids(endings.evaluate_endings(s, world_facts={})))

    def test_19_multiple_causally_valid_endings_are_preserved(self):
        facts = {"ALLIES_RECOVERED_FRAGMENT": True, "TEMPORARY_COOPERATION": True}
        r = endings.evaluate_endings(state(), world_facts=facts)
        self.assertIn("FRAGMENT_ALLIE", ids(r))
        self.assertIn("ALLIANCE_AMERE", ids(r))
        self.assertIsNone(r["automatic_selection"])

    def test_20_engine_never_declares_single_correct_ending(self):
        r = endings.evaluate_endings(state(), world_facts={"VOSS_TRANSFERRED_FRAGMENT": True})
        self.assertFalse(r["single_forced_correct_ending"])

    def test_21_finalize_requires_verified_conditions(self):
        ev = endings.evaluate_endings(state(), world_facts={})
        r = endings.finalize_ending(ev, ending_id="FRAGMENT_ALLIE")
        self.assertEqual(r["code"], "ENDING_CONDITIONS_NOT_VERIFIED")

    def test_22_finalize_eligible_ending(self):
        ev = endings.evaluate_endings(state(), world_facts={"ALLIES_RECOVERED_FRAGMENT": True})
        r = endings.finalize_ending(ev, ending_id="FRAGMENT_ALLIE")
        self.assertEqual(r["status"], "FINALIZED")
        self.assertEqual(r["ending"]["ending_id"], "FRAGMENT_ALLIE")

    def test_23_unknown_ending_id_blocked(self):
        ev = endings.evaluate_endings(state(), world_facts={})
        r = endings.finalize_ending(ev, ending_id="HAPPY_ENDING")
        self.assertEqual(r["code"], "ENDING_ID_UNKNOWN")

    def test_24_abandoned_investigation_keeps_clock_semantics_in_evidence(self):
        s = state(1)
        s["party"]["P1"]["withdrawn"] = True
        ev = endings.evaluate_endings(s, world_facts={})
        row = next(x for x in ev["eligible_endings"] if x["ending_id"] == "ENQUETE_ABANDONNEE")
        self.assertIn("WORLD_CLOCK_CONTINUES", row["evidence"])

    def test_25_party_and_world_verification_flags_are_explicit(self):
        r = endings.evaluate_endings(state(), world_facts={})
        self.assertTrue(r["party_state_verified"])
        self.assertTrue(r["world_state_input_present"])

    def test_26_absent_world_facts_are_not_silently_invented(self):
        r = endings.evaluate_endings(state(), world_facts=None)
        self.assertFalse(r["world_state_input_present"])
        self.assertEqual(r["eligible_endings"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
