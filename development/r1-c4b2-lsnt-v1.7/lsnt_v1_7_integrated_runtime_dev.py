from __future__ import annotations

import copy
import hashlib

import lsnt_v1_7_endings_dev as endings
import lsnt_v1_7_exposure_san_dev as exposure
import lsnt_v1_7_state_binding_dev as binding
import lsnt_v1_7_world_clock_dev as world

GENESIS = "0" * 64
SUPPORTED_ACTIONS = {
    "TRAVEL",
    "ADVANCE_TIME",
    "FRONT_CHECK",
    "PRIVATE_KNOWLEDGE",
    "SHARE_KNOWLEDGE",
    "EXPOSURE",
    "SAN",
    "PC_STATUS",
}


def semantic_state(state: dict) -> dict:
    out = copy.deepcopy(state)
    out.pop("action_journal", None)
    out.pop("dev_bootstrap", None)
    return out


def semantic_digest(state: dict) -> str:
    return binding.digest(semantic_state(state))


def _event_material(row: dict) -> dict:
    return {
        "event_id": row["event_id"],
        "actor_id": row["actor_id"],
        "action": row["action"],
        "payload": row["payload"],
        "previous_hash": row["previous_hash"],
        "semantic_before": row["semantic_before"],
        "semantic_after": row["semantic_after"],
    }


def event_hash(row: dict) -> str:
    return hashlib.sha256(binding.canon(_event_material(row)).encode("utf-8")).hexdigest()


def create_runtime(player_count: int, *, source_hashes: dict[str, str]) -> dict:
    players = [{"player_id": f"P{i}", "character_id": f"C{i}"} for i in range(1, player_count + 1)]
    ready = binding.create_synthetic_test_session(players, source_hashes=source_hashes)
    state = ready["state"]
    for row in state["party"].values():
        row["stats"].update({"HP": 10, "SAN": 60, "MP": 12, "LUCK": 50})
        row.update({"dead": False, "incapacitated": False, "withdrawn": False})
    state["action_journal"] = []
    state["dev_bootstrap"] = {
        "players": players,
        "source_hashes": copy.deepcopy(source_hashes),
        "initial_stats": {"HP": 10, "SAN": 60, "MP": 12, "LUCK": 50},
    }
    return state


def _apply_payload(state: dict, event: dict, *, replay: bool) -> dict:
    action = event["action"]
    actor = event["actor_id"]
    p = event["payload"]
    if action == "TRAVEL":
        if actor != "SYSTEM":
            return {"status": "BLOCKED", "code": "SYSTEM_ACTION_REQUIRED"}
        return world.apply_travel(state, route_id=p["route_id"], actual_minutes=p["actual_minutes"], causal_reason=p.get("causal_reason"))
    if action == "ADVANCE_TIME":
        if actor != "SYSTEM":
            return {"status": "BLOCKED", "code": "SYSTEM_ACTION_REQUIRED"}
        return world.advance_world_time(state, p["target"], facts=p.get("facts"))
    if action == "FRONT_CHECK":
        if actor != "SYSTEM":
            return {"status": "BLOCKED", "code": "SYSTEM_ACTION_REQUIRED"}
        return world.resolve_front_check(
            state,
            check_time=p["check_time"],
            facts_result=p.get("facts_result"),
            recorded_roll=p.get("recorded_roll"),
            causal_modifiers=p.get("causal_modifiers"),
            replay=replay,
        )
    if action == "PRIVATE_KNOWLEDGE":
        return binding.add_private_knowledge(state, actor_player_id=actor, character_id=p["character_id"], fact_id=p["fact_id"])
    if action == "SHARE_KNOWLEDGE":
        return binding.share_knowledge(state, actor_player_id=actor, fact_id=p["fact_id"])
    if action == "EXPOSURE":
        outcomes = {int(k): v for k, v in (p.get("threshold_outcomes") or {}).items()}
        return exposure.apply_exposure(
            state,
            actor_player_id=actor,
            character_id=p["character_id"],
            exposure_kind=p["exposure_kind"],
            threshold_outcomes=outcomes,
        )
    if action == "SAN":
        return exposure.apply_sanity_experience(
            state,
            actor_player_id=actor,
            character_id=p["character_id"],
            experience_id=p["experience_id"],
            san_check_success=p["san_check_success"],
            recorded_loss=p.get("recorded_loss"),
            replay=replay,
            directly_exposed=p.get("directly_exposed", True),
        )
    if action == "PC_STATUS":
        if actor != "SYSTEM":
            return {"status": "BLOCKED", "code": "SYSTEM_ACTION_REQUIRED"}
        player_id = p["player_id"]
        row = state.get("party", {}).get(player_id)
        if row is None:
            return {"status": "BLOCKED", "code": "PLAYER_NOT_IN_SESSION"}
        field = p["field"]
        if field not in {"dead", "incapacitated", "withdrawn"} or not isinstance(p["value"], bool):
            return {"status": "BLOCKED", "code": "PC_STATUS_UPDATE_INVALID"}
        row[field] = p["value"]
        return {"status": "COMMITTED", "player_id": player_id, "field": field, "value": p["value"]}
    return {"status": "BLOCKED", "code": "ACTION_UNKNOWN"}


def apply_event(state: dict, event: dict, *, replay: bool = False, record: bool = True) -> dict:
    if set(event) != {"event_id", "actor_id", "action", "payload"}:
        return {"status": "BLOCKED", "code": "EVENT_SHAPE_INVALID"}
    if event["action"] not in SUPPORTED_ACTIONS:
        return {"status": "BLOCKED", "code": "ACTION_UNKNOWN"}
    journal = state.setdefault("action_journal", [])
    if record and any(row["event_id"] == event["event_id"] for row in journal):
        return {"status": "BLOCKED", "code": "DUPLICATE_EVENT_ID"}
    before_snapshot = copy.deepcopy(state)
    before = semantic_digest(state)
    result = _apply_payload(state, event, replay=replay)
    if result.get("status") in {"BLOCKED", "FAIL_CLOSED"}:
        state.clear(); state.update(before_snapshot)
        return result
    after = semantic_digest(state)
    if record:
        row = {
            "event_id": event["event_id"],
            "actor_id": event["actor_id"],
            "action": event["action"],
            "payload": copy.deepcopy(event["payload"]),
            "previous_hash": journal[-1]["event_hash"] if journal else GENESIS,
            "semantic_before": before,
            "semantic_after": after,
        }
        row["event_hash"] = event_hash(row)
        journal.append(row)
    return {"status": "COMMITTED", "action_result": result, "semantic_before": before, "semantic_after": after}


def _rebuild_from_bootstrap(bootstrap: dict) -> dict:
    ready = binding.create_synthetic_test_session(bootstrap["players"], source_hashes=bootstrap["source_hashes"])
    state = ready["state"]
    for row in state["party"].values():
        row["stats"].update(copy.deepcopy(bootstrap["initial_stats"]))
        row.update({"dead": False, "incapacitated": False, "withdrawn": False})
    state["action_journal"] = []
    state["dev_bootstrap"] = copy.deepcopy(bootstrap)
    return state


def verify_journal(state: dict) -> dict:
    journal = state.get("action_journal")
    bootstrap = state.get("dev_bootstrap")
    if not isinstance(journal, list) or not isinstance(bootstrap, dict):
        return {"status": "FAIL", "code": "REPLAY_METADATA_MISSING"}
    previous = GENESIS
    seen = set()
    replay_state = _rebuild_from_bootstrap(bootstrap)
    for index, row in enumerate(journal):
        if row.get("event_id") in seen:
            return {"status": "FAIL", "code": "DUPLICATE_EVENT_ID", "index": index}
        seen.add(row.get("event_id"))
        if row.get("previous_hash") != previous:
            return {"status": "FAIL", "code": "HASH_CHAIN_PREVIOUS_MISMATCH", "index": index}
        if row.get("event_hash") != event_hash(row):
            return {"status": "FAIL", "code": "EVENT_HASH_MISMATCH", "index": index}
        if semantic_digest(replay_state) != row.get("semantic_before"):
            return {"status": "FAIL", "code": "REPLAY_BEFORE_MISMATCH", "index": index}
        event = {"event_id": row["event_id"], "actor_id": row["actor_id"], "action": row["action"], "payload": copy.deepcopy(row["payload"])}
        result = apply_event(replay_state, event, replay=True, record=False)
        if result.get("status") != "COMMITTED":
            return {"status": "FAIL", "code": "REPLAY_ACTION_BLOCKED", "index": index, "detail": result}
        if semantic_digest(replay_state) != row.get("semantic_after"):
            return {"status": "FAIL", "code": "REPLAY_AFTER_MISMATCH", "index": index}
        previous = row["event_hash"]
    if semantic_digest(replay_state) != semantic_digest(state):
        return {"status": "FAIL", "code": "REPLAY_FINAL_STATE_MISMATCH"}
    return {"status": "REPLAY_MATCH", "events": len(journal), "final_digest": semantic_digest(state)}


def save_bundle(state: dict, secret: bytes) -> dict:
    return binding.save_bundle(state, secret)


def restore_bundle(bundle: dict, secret: bytes, expected_source_hashes: dict[str, str]) -> dict:
    restored = binding.restore_synthetic_test_bundle(bundle, secret, expected_source_hashes)
    if restored.get("status") != "RESTORED_STRICT_DEV":
        return restored
    replay = verify_journal(restored["state"])
    if replay.get("status") != "REPLAY_MATCH":
        return {"status": "FAIL_CLOSED", "code": replay.get("code"), "replay": replay}
    return {"status": "RESTORED_STRICT_REPLAY_DEV", "state": restored["state"], "replay": replay}


def evaluate_endings(state: dict, world_facts: dict[str, bool] | None = None) -> dict:
    return endings.evaluate_endings(state, world_facts=world_facts)
