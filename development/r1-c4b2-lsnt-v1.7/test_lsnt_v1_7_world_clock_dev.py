from __future__ import annotations

import unittest

import lsnt_v1_7_world_clock_dev as world


def base_state(time="J1 08:00"):
    return {"world_time": time, "events": {"potential": [], "triggered": [], "obsolete": [], "resolved": []}, "front": {"state": "RELATIVELY_STABLE", "last_check": None, "history": []}}


class LSNTV17WorldClockDevTests(unittest.TestCase):
    def test_01_parse_and_format_roundtrip(self):
        for stamp in ("J1 08:00", "J1 23:40", "J2 06:00", "J4 12:00"):
            self.assertEqual(world.format_time(world.parse_time(stamp)), stamp)

    def test_02_invalid_time_rejected(self):
        with self.assertRaisesRegex(ValueError, "WORLD_TIME_FORMAT_INVALID"):
            world.parse_time("J1 25:00")

    def test_03_rewind_is_blocked(self):
        state = base_state("J2 06:00")
        r = world.advance_world_time(state, "J1 18:00")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(state["world_time"], "J2 06:00")

    def test_04_unconditional_clock_event_triggers_once(self):
        state = base_state()
        world.advance_world_time(state, "J1 23:50")
        ids = [x["event_id"] for x in state["events"]["triggered"]]
        self.assertIn("FIRST_NOTABLE_EXPANSION", ids)
        world.advance_world_time(state, "J2 00:10")
        ids2 = [x["event_id"] for x in state["events"]["triggered"]]
        self.assertEqual(ids2.count("FIRST_NOTABLE_EXPANSION"), 1)

    def test_05_true_conditional_event_triggers(self):
        state = base_state()
        world.advance_world_time(state, "J1 18:00", facts={"TRACES_LEFT": True})
        self.assertIn("VOSS_INTEREST_IF_TRACES", [x["event_id"] for x in state["events"]["triggered"]])

    def test_06_false_conditional_event_obsoletes(self):
        state = base_state()
        world.advance_world_time(state, "J1 18:00", facts={"TRACES_LEFT": False})
        self.assertIn("VOSS_INTEREST_IF_TRACES", [x["event_id"] for x in state["events"]["obsolete"]])

    def test_07_unknown_conditional_event_remains_potential(self):
        state = base_state()
        world.advance_world_time(state, "J1 18:00")
        self.assertIn("VOSS_INTEREST_IF_TRACES", [x["event_id"] for x in state["events"]["potential"]])

    def test_08_possible_oasis_event_is_not_auto_triggered(self):
        state = base_state("J2 12:00")
        world.advance_world_time(state, "J2 15:00")
        self.assertIn("OASIS_MAY_CHANGE_BY_FRONT", [x["event_id"] for x in state["events"]["potential"]])
        self.assertNotIn("OASIS_MAY_CHANGE_BY_FRONT", [x["event_id"] for x in state["events"]["triggered"]])

    def test_09_possible_bombardment_is_not_auto_triggered(self):
        state = base_state("J3 15:00")
        world.advance_world_time(state, "J3 17:00")
        self.assertIn("POSSIBLE_BOMBARDMENT", [x["event_id"] for x in state["events"]["potential"]])

    def test_10_transfer_condition_true(self):
        state = base_state("J4 04:00")
        world.advance_world_time(state, "J4 06:00", facts={"VOSS_CONTROLS_FRAGMENT": True})
        self.assertIn("TRANSFER_DEPARTS_IF_VOSS_CONTROLS", [x["event_id"] for x in state["events"]["triggered"]])

    def test_11_zenith_condition_false(self):
        state = base_state("J4 11:00")
        world.advance_world_time(state, "J4 13:00", facts={"DEVICE_OPEN": False})
        self.assertIn("CRITICAL_ZENITH_IF_DEVICE_OPEN", [x["event_id"] for x in state["events"]["obsolete"]])

    def test_12_front_checks_due_at_06_and_18_only(self):
        due = world.due_front_checks(world.parse_time("J1 08:00"), world.parse_time("J2 19:00"))
        self.assertEqual(due, ["J1 18:00", "J2 06:00", "J2 18:00"])

    def test_13_facts_decide_front_without_roll(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", facts_result="ALLIES")
        self.assertEqual(r["status"], "RESOLVED")
        self.assertEqual(r["mode"], "FACTS")
        self.assertIsNone(r["roll"])
        self.assertEqual(state["front"]["state"], "ALLIES")

    def test_14_roll_forbidden_when_facts_decide(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", facts_result="AXIS", recorded_roll=6)
        self.assertEqual(r["code"], "FRONT_ROLL_FORBIDDEN_WHEN_FACTS_DECIDE")

    def test_15_unresolved_front_requires_recorded_roll(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00")
        self.assertEqual(r["code"], "FRONT_RECORDED_1D6_REQUIRED")

    def test_16_front_roll_mapping_axis(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=2)
        self.assertEqual(r["result"], "AXIS")

    def test_17_front_roll_mapping_status_quo(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=4)
        self.assertEqual(r["result"], "STATUS_QUO")

    def test_18_front_roll_mapping_allies(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=5)
        self.assertEqual(r["result"], "ALLIES")

    def test_19_causal_modifier_is_applied(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=4, causal_modifiers=[1])
        self.assertEqual(r["adjusted"], 5)
        self.assertEqual(r["result"], "ALLIES")

    def test_20_each_causal_modifier_is_limited_to_one(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=4, causal_modifiers=[2])
        self.assertEqual(r["code"], "FRONT_CAUSAL_MODIFIER_INVALID")

    def test_21_duplicate_front_check_is_rejected(self):
        state = base_state("J1 18:00")
        world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=3)
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=6)
        self.assertEqual(r["code"], "FRONT_CHECK_ALREADY_RESOLVED")
        self.assertEqual(len(state["front"]["history"]), 1)

    def test_22_replay_uses_recorded_roll(self):
        state = base_state("J1 18:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=6, replay=True)
        self.assertEqual(r["mode"], "RECORDED_REPLAY")
        self.assertEqual(r["roll"], 6)

    def test_23_front_check_wrong_time_blocked(self):
        state = base_state("J1 12:00")
        r = world.resolve_front_check(state, check_time="J1 12:00", recorded_roll=4)
        self.assertEqual(r["code"], "FRONT_CHECK_TIME_INVALID")

    def test_24_front_future_check_blocked(self):
        state = base_state("J1 08:00")
        r = world.resolve_front_check(state, check_time="J1 18:00", recorded_roll=4)
        self.assertEqual(r["code"], "FRONT_CHECK_NOT_DUE")

    def test_25_all_seven_travel_records_materialized(self):
        self.assertEqual(len(world.TRAVEL), 7)
        self.assertEqual(world.TRAVEL["BIR_HALIM_TO_CONVOY"]["km"], 35)
        self.assertEqual(world.TRAVEL["COASTAL_ROAD_TO_TMIMI"]["normal_max"], 80)

    def test_26_normal_travel_advances_exact_given_time(self):
        state = base_state("J1 08:00")
        r = world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=60)
        self.assertEqual(r["status"], "TRAVEL_COMMITTED")
        self.assertEqual(state["world_time"], "J1 09:00")
        self.assertEqual(state["travel_history"][0]["minutes"], 60)

    def test_27_engine_does_not_choose_a_travel_duration(self):
        state = base_state()
        r = world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=0)
        self.assertEqual(r["code"], "TRAVEL_DURATION_INVALID")

    def test_28_out_of_range_without_cause_is_blocked(self):
        state = base_state()
        r = world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=100)
        self.assertEqual(r["code"], "OUT_OF_RANGE_TRAVEL_REQUIRES_SOURCE_CAUSAL_REASON")
        self.assertEqual(state["world_time"], "J1 08:00")

    def test_29_out_of_range_with_source_cause_is_allowed(self):
        state = base_state()
        r = world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=100, causal_reason="STORM")
        self.assertEqual(r["status"], "TRAVEL_COMMITTED")
        self.assertEqual(state["world_time"], "J1 09:40")

    def test_30_unknown_causal_reason_is_blocked(self):
        state = base_state()
        r = world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=100, causal_reason="PACING")
        self.assertEqual(r["code"], "OUT_OF_RANGE_TRAVEL_REQUIRES_SOURCE_CAUSAL_REASON")

    def test_31_travel_crossing_front_check_reports_due_check(self):
        state = base_state("J1 17:30")
        r = world.apply_travel(state, route_id="CONVOY_TO_SIDI_MARUT", actual_minutes=45)
        self.assertEqual(r["front_checks_due"], ["J1 18:00"])
        self.assertEqual(state["world_time"], "J1 18:15")

    def test_32_time_is_monotonic_across_multiple_travel_actions(self):
        state = base_state("J1 08:00")
        world.apply_travel(state, route_id="BIR_HALIM_TO_CONVOY", actual_minutes=50)
        first = world.parse_time(state["world_time"])
        world.apply_travel(state, route_id="CONVOY_TO_SIDI_MARUT", actual_minutes=45)
        second = world.parse_time(state["world_time"])
        self.assertGreater(second, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
