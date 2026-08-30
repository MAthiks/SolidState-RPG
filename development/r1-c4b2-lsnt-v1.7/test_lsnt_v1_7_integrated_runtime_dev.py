from __future__ import annotations

import copy
import unittest

import lsnt_v1_7_integrated_runtime_dev as rt

HASHES = {"LSNT_V1_7_KEEPER": "a" * 64, "LSNT_V1_7_PLAYER": "b" * 64}
SECRET = b"lsnt-v17-integrated-dev"


def event(event_id, actor_id, action, **payload):
    return {"event_id": event_id, "actor_id": actor_id, "action": action, "payload": payload}


def script(player_count: int):
    rows = [
        event("E01", "SYSTEM", "TRAVEL", route_id="BIR_HALIM_TO_CONVOY", actual_minutes=60),
        event("E02", "P1", "PRIVATE_KNOWLEDGE", character_id="C1", fact_id="CONVOY_SHADOW_ANOMALY"),
        event("E03", "P1", "EXPOSURE", character_id="C1", exposure_kind="BRIEF_ANOMALY", threshold_outcomes={}),
        event("E04", "P1", "SAN", character_id="C1", experience_id="SHADOW_MOVES_AFTER_STOP", san_check_success=True),
        event("E05", "SYSTEM", "TRAVEL", route_id="CONVOY_TO_SIDI_MARUT", actual_minutes=45),
        event("E06", "P1", "SHARE_KNOWLEDGE", fact_id="CONVOY_SHADOW_ANOMALY"),
        event("E07", "SYSTEM", "ADVANCE_TIME", target="J1 18:00", facts={"TRACES_LEFT": True}),
        event("E08", "SYSTEM", "FRONT_CHECK", check_time="J1 18:00", recorded_roll=5, causal_modifiers=[]),
        event("E09", "P1", "EXPOSURE", character_id="C1", exposure_kind="PROLONGED", threshold_outcomes={2: False}),
        event("E10", "P1", "SAN", character_id="C1", experience_id="DISCOVER_SHADOW_GATE", san_check_success=False, recorded_loss=4),
        event("E11", "SYSTEM", "ADVANCE_TIME", target="J2 06:10", facts={}),
        event("E12", "SYSTEM", "FRONT_CHECK", check_time="J2 06:00", recorded_roll=2, causal_modifiers=[]),
        event("E13", "SYSTEM", "ADVANCE_TIME", target="J2 15:00", facts={}),
    ]
    if player_count >= 2:
        rows.insert(9, event("E09B", "P2", "EXPOSURE", character_id="C2", exposure_kind="DIRECT_CONTACT", threshold_outcomes={2: True}))
        rows.insert(10, event("E09C", "P2", "SAN", character_id="C2", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=False, recorded_loss=2))
    return rows


def apply_all(state, events):
    for e in events:
        r = rt.apply_event(state, e)
        if r["status"] != "COMMITTED":
            raise AssertionError((e, r))
    return state


class LSNTV17IntegratedRuntimeDevTests(unittest.TestCase):
    def test_01_full_script_replay_matches_one_to_four_players(self):
        for count in range(1, 5):
            with self.subTest(count=count):
                state = rt.create_runtime(count, source_hashes=HASHES)
                apply_all(state, script(count))
                replay = rt.verify_journal(state)
                self.assertEqual(replay["status"], "REPLAY_MATCH")
                self.assertEqual(replay["events"], len(script(count)))

    def test_02_continuous_vs_resumed_equal_one_to_four_players(self):
        for count in range(1, 5):
            with self.subTest(count=count):
                events = script(count)
                cut = len(events) // 2
                continuous = rt.create_runtime(count, source_hashes=HASHES)
                apply_all(continuous, events)
                resumed = rt.create_runtime(count, source_hashes=HASHES)
                apply_all(resumed, events[:cut])
                bundle = rt.save_bundle(resumed, SECRET)
                restored = rt.restore_bundle(bundle, SECRET, HASHES)
                self.assertEqual(restored["status"], "RESTORED_STRICT_REPLAY_DEV")
                resumed = restored["state"]
                apply_all(resumed, events[cut:])
                self.assertEqual(rt.semantic_digest(resumed), rt.semantic_digest(continuous))
                self.assertEqual(rt.verify_journal(resumed)["status"], "REPLAY_MATCH")

    def test_03_world_time_survives_resume(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:8])
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, HASHES)
        self.assertEqual(restored["state"]["world_time"], state["world_time"])

    def test_04_front_history_survives_resume(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:8])
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, HASHES)["state"]
        self.assertEqual(restored["front"]["history"], state["front"]["history"])

    def test_05_san_survives_resume(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:10])
        self.assertEqual(state["party"]["P1"]["stats"]["SAN"], 56)
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, HASHES)["state"]
        self.assertEqual(restored["party"]["P1"]["stats"]["SAN"], 56)

    def test_06_exposure_survives_resume(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:10])
        self.assertEqual(state["party"]["P1"]["exposure_state"]["exposure"], 3)
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, HASHES)["state"]
        self.assertEqual(restored["party"]["P1"]["exposure_state"], state["party"]["P1"]["exposure_state"])

    def test_07_private_then_shared_knowledge_survives_resume(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        apply_all(state, script(2)[:6])
        self.assertIn("CONVOY_SHADOW_ANOMALY", state["party"]["P1"]["knowledge"])
        self.assertEqual(state["party"]["P2"]["knowledge"], [])
        self.assertIn("CONVOY_SHADOW_ANOMALY", state["shared_knowledge"])
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, HASHES)["state"]
        self.assertEqual(restored["shared_knowledge"], state["shared_knowledge"])

    def test_08_player_two_exposure_does_not_change_player_one(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        p2 = event("P2-X", "P2", "EXPOSURE", character_id="C2", exposure_kind="DIRECT_CONTACT", threshold_outcomes={2: True})
        rt.apply_event(state, p2)
        self.assertNotIn("exposure_state", state["party"]["P1"])
        self.assertEqual(state["party"]["P2"]["exposure_state"]["exposure"], 3)

    def test_09_wrong_actor_event_is_zero_mutation_and_not_journaled(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        before = rt.semantic_digest(state)
        r = rt.apply_event(state, event("BAD", "P1", "SAN", character_id="C2", experience_id="SHADOW_PRECEDES_GESTURE", san_check_success=True))
        self.assertEqual(r["status"], "BLOCKED")
        self.assertEqual(before, rt.semantic_digest(state))
        self.assertEqual(state["action_journal"], [])

    def test_10_duplicate_event_id_rejected(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        e = event("DUP", "P1", "PRIVATE_KNOWLEDGE", character_id="C1", fact_id="A")
        self.assertEqual(rt.apply_event(state, e)["status"], "COMMITTED")
        before = rt.semantic_digest(state)
        self.assertEqual(rt.apply_event(state, e)["code"], "DUPLICATE_EVENT_ID")
        self.assertEqual(before, rt.semantic_digest(state))

    def test_11_journal_previous_hash_chain_is_contiguous(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1))
        previous = rt.GENESIS
        for row in state["action_journal"]:
            self.assertEqual(row["previous_hash"], previous)
            previous = row["event_hash"]

    def test_12_event_hash_tamper_detected(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:3])
        tampered = copy.deepcopy(state)
        tampered["action_journal"][1]["payload"]["fact_id"] = "ALTERED"
        self.assertEqual(rt.verify_journal(tampered)["code"], "EVENT_HASH_MISMATCH")

    def test_13_reordered_journal_detected(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:3])
        tampered = copy.deepcopy(state)
        tampered["action_journal"][1], tampered["action_journal"][2] = tampered["action_journal"][2], tampered["action_journal"][1]
        self.assertEqual(rt.verify_journal(tampered)["code"], "HASH_CHAIN_PREVIOUS_MISMATCH")

    def test_14_omitted_middle_event_detected(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:4])
        tampered = copy.deepcopy(state)
        del tampered["action_journal"][1]
        self.assertEqual(rt.verify_journal(tampered)["code"], "HASH_CHAIN_PREVIOUS_MISMATCH")

    def test_15_duplicate_journal_event_detected(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:2])
        tampered = copy.deepcopy(state)
        tampered["action_journal"].append(copy.deepcopy(tampered["action_journal"][1]))
        self.assertEqual(rt.verify_journal(tampered)["code"], "DUPLICATE_EVENT_ID")

    def test_16_state_tamper_reauthenticated_still_fails_replay(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:10])
        tampered = copy.deepcopy(state)
        tampered["party"]["P1"]["stats"]["SAN"] = 60
        bundle = rt.save_bundle(tampered, SECRET)
        restored = rt.restore_bundle(bundle, SECRET, HASHES)
        self.assertEqual(restored["status"], "FAIL_CLOSED")
        self.assertEqual(restored["code"], "REPLAY_FINAL_STATE_MISMATCH")

    def test_17_recorded_san_loss_tamper_detected_even_if_event_rehashed(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:10])
        tampered = copy.deepcopy(state)
        row = next(x for x in tampered["action_journal"] if x["action"] == "SAN" and x["payload"].get("recorded_loss") is not None)
        row["payload"]["recorded_loss"] = 2
        row["event_hash"] = rt.event_hash(row)
        # Following previous-hash links are now stale; this must fail before any reroll could occur.
        verify = rt.verify_journal(tampered)
        self.assertNotEqual(verify["status"], "REPLAY_MATCH")

    def test_18_replay_front_uses_recorded_roll_not_new_randomness(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:8])
        front_event = next(x for x in state["action_journal"] if x["action"] == "FRONT_CHECK")
        self.assertEqual(front_event["payload"]["recorded_roll"], 5)
        self.assertEqual(rt.verify_journal(state)["status"], "REPLAY_MATCH")

    def test_19_replay_san_uses_recorded_loss_not_new_randomness(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:10])
        san_event = [x for x in state["action_journal"] if x["action"] == "SAN"][-1]
        self.assertEqual(san_event["payload"]["recorded_loss"], 4)
        self.assertEqual(rt.verify_journal(state)["status"], "REPLAY_MATCH")

    def test_20_oasis_possible_event_remains_potential_after_full_script(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1))
        self.assertIn("OASIS_MAY_CHANGE_BY_FRONT", [x["event_id"] for x in state["events"]["potential"]])
        self.assertNotIn("OASIS_MAY_CHANGE_BY_FRONT", [x["event_id"] for x in state["events"]["triggered"]])

    def test_21_voss_interest_triggers_from_explicit_fact(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:7])
        self.assertIn("VOSS_INTEREST_IF_TRACES", [x["event_id"] for x in state["events"]["triggered"]])

    def test_22_front_changes_only_from_recorded_check(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:8])
        self.assertEqual(state["front"]["state"], "ALLIES")
        self.assertEqual(state["front"]["history"][0]["roll"], 5)

    def test_23_second_front_check_replays_to_axis(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:12])
        self.assertEqual(state["front"]["state"], "AXIS")
        self.assertEqual([x["roll"] for x in state["front"]["history"]], [5, 2])

    def test_24_no_automatic_ending_after_integrated_script(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1))
        ev = rt.evaluate_endings(state, {})
        self.assertEqual(ev["eligible_endings"], [])
        self.assertIsNone(ev["automatic_selection"])

    def test_25_one_pc_death_in_two_player_session_is_not_game_over(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        rt.apply_event(state, event("DEATH1", "SYSTEM", "PC_STATUS", player_id="P1", field="dead", value=True))
        self.assertNotIn("GAME_OVER", [x["ending_id"] for x in rt.evaluate_endings(state, {})["eligible_endings"]])

    def test_26_all_pc_death_is_game_over_but_romain_not_replacement(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        rt.apply_event(state, event("D1", "SYSTEM", "PC_STATUS", player_id="P1", field="dead", value=True))
        rt.apply_event(state, event("D2", "SYSTEM", "PC_STATUS", player_id="P2", field="dead", value=True))
        self.assertFalse(state["romain_persy"]["replacement_pc"])
        self.assertIn("GAME_OVER", [x["ending_id"] for x in rt.evaluate_endings(state, {})["eligible_endings"]])

    def test_27_withdrawal_ending_requires_all_active_pcs(self):
        state = rt.create_runtime(2, source_hashes=HASHES)
        rt.apply_event(state, event("W1", "SYSTEM", "PC_STATUS", player_id="P1", field="withdrawn", value=True))
        self.assertNotIn("ENQUETE_ABANDONNEE", [x["ending_id"] for x in rt.evaluate_endings(state, {})["eligible_endings"]])
        rt.apply_event(state, event("W2", "SYSTEM", "PC_STATUS", player_id="P2", field="withdrawn", value=True))
        self.assertIn("ENQUETE_ABANDONNEE", [x["ending_id"] for x in rt.evaluate_endings(state, {})["eligible_endings"]])

    def test_28_world_fact_can_make_multiple_endings_eligible_without_auto_selection(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        ev = rt.evaluate_endings(state, {"ALLIES_RECOVERED_FRAGMENT": True, "TEMPORARY_COOPERATION": True})
        found = {x["ending_id"] for x in ev["eligible_endings"]}
        self.assertEqual(found, {"FRAGMENT_ALLIE", "ALLIANCE_AMERE"})
        self.assertIsNone(ev["automatic_selection"])

    def test_29_save_rejects_wrong_expected_source_identity(self):
        state = rt.create_runtime(1, source_hashes=HASHES)
        apply_all(state, script(1)[:3])
        wrong = {"LSNT_V1_7_KEEPER": "c" * 64, "LSNT_V1_7_PLAYER": "b" * 64}
        restored = rt.restore_bundle(rt.save_bundle(state, SECRET), SECRET, wrong)
        self.assertEqual(restored["status"], "FAIL_CLOSED")
        self.assertEqual(restored["code"], "SCENARIO_BINDING_MISMATCH")

    def test_30_integrated_runtime_stays_dev_only(self):
        state = rt.create_runtime(4, source_hashes=HASHES)
        self.assertTrue(state["dev_only"])
        self.assertFalse(state["authority_promoted"])
        self.assertEqual(state["scenario_runtime"]["source_identity_mode"], "SYNTHETIC_TEST_ONLY_NOT_CANONICAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
