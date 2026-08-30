from __future__ import annotations

import copy
import unittest

import lsnt_v1_7_exposure_san_dev as es
import lsnt_v1_7_state_binding_dev as binding

HASHES = {"LSNT_V1_7_KEEPER": "a" * 64, "LSNT_V1_7_PLAYER": "b" * 64}


def state(count=1):
    s = binding.create_synthetic_test_session(
        [{"player_id": f"P{i}", "character_id": f"C{i}"} for i in range(1, count + 1)],
        source_hashes=HASHES,
    )["state"]
    for row in s["party"].values():
        row["stats"].update({"HP": 10, "SAN": 60, "MP": 12, "LUCK": 50})
    return s


class LSNTV17ExposureSanDevTests(unittest.TestCase):
    def test_01_exposure_table_exact(self):
        self.assertEqual(es.EXPOSURE_INCREMENTS, {"BRIEF_ANOMALY": 1, "PROLONGED": 2, "DIRECT_CONTACT": 3})
        self.assertEqual(es.EXPOSURE_THRESHOLDS, (2, 4, 6))

    def test_02_brief_exposure_plus_one(self):
        s = state()
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        self.assertEqual(r["new_exposure"], 1)

    def test_03_threshold_two_requires_pow_outcome(self):
        s = state()
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        before = copy.deepcopy(s)
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        self.assertEqual(r["code"], "POW_THRESHOLD_OUTCOME_REQUIRED")
        self.assertEqual(s, before)

    def test_04_pow_success_delays_manifestation_and_keeps_counter(self):
        s = state()
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY", threshold_outcomes={2: True})
        self.assertEqual(r["new_exposure"], 2)
        x = s["party"]["P1"]["exposure_state"]
        self.assertEqual(x["delayed_thresholds"], [2])
        self.assertEqual(x["manifestation_failures"], 0)

    def test_05_pow_failure_advances_failure_counter(self):
        s = state()
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="PROLONGED", threshold_outcomes={2: False})
        self.assertEqual(r["new_exposure"], 3)
        self.assertEqual(r["manifestation_failures"], 1)
        self.assertFalse(r["suspense_triggered_stage"])

    def test_06_direct_contact_can_cross_two_thresholds(self):
        s = state()
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="DIRECT_CONTACT", threshold_outcomes={2: True, 4: False})
        self.assertEqual(r["thresholds_crossed"], [2, 4])
        self.assertEqual(r["new_exposure"], 4)
        self.assertEqual(r["manifestation_failures"], 1)

    def test_07_exposure_caps_at_six(self):
        s = state()
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="DIRECT_CONTACT", threshold_outcomes={2: True})
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="DIRECT_CONTACT", threshold_outcomes={4: True, 6: True})
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="DIRECT_CONTACT")
        self.assertEqual(r["new_exposure"], 6)

    def test_08_wrong_actor_exposure_blocked(self):
        s = state(2)
        before = copy.deepcopy(s)
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C2", exposure_kind="BRIEF_ANOMALY")
        self.assertEqual(r["code"], "ACTOR_CHARACTER_MISMATCH")
        self.assertEqual(s, before)

    def test_09_unknown_exposure_kind_blocked(self):
        s = state()
        r = es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="SUSPENSE")
        self.assertEqual(r["code"], "EXPOSURE_KIND_UNKNOWN")

    def test_10_exposure_is_individual(self):
        s = state(2)
        es.apply_exposure(s, actor_player_id="P1", character_id="C1", exposure_kind="BRIEF_ANOMALY")
        self.assertEqual(s["party"]["P1"]["exposure_state"]["exposure"], 1)
        self.assertNotIn("exposure_state", s["party"]["P2"])

    def test_11_sanity_table_has_six_source_records(self):
        self.assertEqual(len(es.SANITY_LOSSES), 6)
        self.assertEqual(es.SANITY_LOSSES["SHADOW_MOVES_AFTER_STOP"], {"success": "0", "failure": "1D3"})
        self.assertEqual(es.SANITY_LOSSES["UNDERSTAND_PROPAGATION_POTENTIAL"], {"success": "1D4", "failure": "1D10"})

    def test_12_fixed_zero_success_needs_no_loss_roll(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=True)
        self.assertEqual(r["loss"], 0)
        self.assertEqual(r["new_san"], 60)

    def test_13_fixed_one_success_needs_no_loss_roll(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True)
        self.assertEqual(r["loss"], 1)
        self.assertEqual(r["new_san"], 59)

    def test_14_random_failure_requires_recorded_loss(self):
        s = state()
        before = copy.deepcopy(s)
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=False)
        self.assertEqual(r["code"], "SAN_RECORDED_LOSS_REQUIRED")
        self.assertEqual(s, before)

    def test_15_recorded_d3_failure_commits_exact_value(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=False, recorded_loss=3)
        self.assertEqual(r["loss"], 3)
        self.assertEqual(r["new_san"], 57)

    def test_16_out_of_range_d3_loss_blocked(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=False, recorded_loss=4)
        self.assertEqual(r["code"], "SAN_RECORDED_LOSS_REQUIRED")

    def test_17_success_d2_requires_recorded_loss(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SEE_CONSTRAINED_HUMAN", san_check_success=True, recorded_loss=2)
        self.assertEqual(r["loss"], 2)
        self.assertEqual(r["new_san"], 58)

    def test_18_failure_d10_accepts_ten(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="OBSERVE_ACTIVE_CHAMBER", san_check_success=False, recorded_loss=10)
        self.assertEqual(r["loss"], 10)
        self.assertEqual(r["new_san"], 50)

    def test_19_no_random_value_allowed_for_fixed_loss(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True, recorded_loss=1)
        self.assertEqual(r["code"], "SAN_RANDOM_LOSS_FORBIDDEN_FOR_FIXED_VALUE")

    def test_20_indirect_report_does_not_equal_direct_exposure(self):
        s = state()
        before = copy.deepcopy(s)
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="OBSERVE_ACTIVE_CHAMBER", san_check_success=False, recorded_loss=4, directly_exposed=False)
        self.assertEqual(r["code"], "SAN_DIRECT_EXPOSURE_REQUIRED")
        self.assertEqual(s, before)

    def test_21_wrong_actor_san_blocked_zero_mutation(self):
        s = state(2)
        before = copy.deepcopy(s)
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C2", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True)
        self.assertEqual(r["code"], "ACTOR_CHARACTER_MISMATCH")
        self.assertEqual(s, before)

    def test_22_unknown_experience_blocked(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="FAKE", san_check_success=True)
        self.assertEqual(r["code"], "SAN_EXPERIENCE_UNKNOWN")

    def test_23_current_san_required(self):
        s = state()
        s["party"]["P1"]["stats"]["SAN"] = None
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True)
        self.assertEqual(r["code"], "SAN_CURRENT_VALUE_REQUIRED")

    def test_24_san_never_drops_below_zero(self):
        s = state()
        s["party"]["P1"]["stats"]["SAN"] = 3
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="OBSERVE_ACTIVE_CHAMBER", san_check_success=False, recorded_loss=10)
        self.assertEqual(r["new_san"], 0)

    def test_25_replay_marks_recorded_provenance(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="DISCOVER_SHADOW_GATE", san_check_success=False, recorded_loss=5, replay=True)
        self.assertEqual(r["provenance"], "RECORDED_REPLAY")
        self.assertEqual(s["scenario_san_journal"][-1]["recorded_loss"], 5)

    def test_26_live_input_is_recorded_not_generated_here(self):
        s = state()
        r = es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="DISCOVER_SHADOW_GATE", san_check_success=False, recorded_loss=4)
        self.assertEqual(r["provenance"], "RECORDED_LIVE_INPUT")
        self.assertEqual(s["scenario_san_journal"][-1]["loss"], 4)

    def test_27_each_player_san_is_isolated(self):
        s = state(2)
        es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True)
        self.assertEqual(s["party"]["P1"]["stats"]["SAN"], 59)
        self.assertEqual(s["party"]["P2"]["stats"]["SAN"], 60)

    def test_28_multiple_experiences_accumulate_exactly(self):
        s = state()
        es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True)
        es.apply_sanity_experience(s, actor_player_id="P1", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=False, recorded_loss=2)
        self.assertEqual(s["party"]["P1"]["stats"]["SAN"], 57)
        self.assertEqual(len(s["scenario_san_journal"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
