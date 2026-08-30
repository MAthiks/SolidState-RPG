from __future__ import annotations

import copy
import hashlib
import hmac
import json
from typing import Iterable

from lsnt_v1_7_router_dev import (
    LSNT_V1_7_CANONICAL_GRAPH_DEV,
    PAIR_ID,
    SOURCE_IDS,
    STATE_BINDING,
    public_descriptor,
    resolve_route_dev,
)

SAVE_SCHEMA = "SOLIDSTATE_LSNT_V1_7_DEV_SAVE_V1"
SYNTHETIC_IDENTITY_MODE = "SYNTHETIC_TEST_ONLY_NOT_CANONICAL"
WATER_BY_PLAYER_COUNT = {1: 32, 2: 48, 3: 64, 4: 80}


def canon(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


def canonical_graph_sha256() -> str:
    return digest(LSNT_V1_7_CANONICAL_GRAPH_DEV)


def _validate_players(players: Iterable[dict]) -> list[dict]:
    rows = [copy.deepcopy(p) for p in players]
    if not 1 <= len(rows) <= 4:
        raise ValueError("PLAYER_COUNT_OUT_OF_RANGE")
    seen_players: set[str] = set()
    seen_characters: set[str] = set()
    for row in rows:
        player_id = str(row.get("player_id", ""))
        character_id = str(row.get("character_id", ""))
        if not player_id or not character_id:
            raise ValueError("PLAYER_OR_CHARACTER_ID_MISSING")
        if player_id in seen_players or character_id in seen_characters:
            raise ValueError("DUPLICATE_PLAYER_OR_CHARACTER_ID")
        seen_players.add(player_id)
        seen_characters.add(character_id)
    return rows


def _base_party(players: list[dict]) -> tuple[dict, dict]:
    party = {}
    control_map = {}
    for row in players:
        player_id = row["player_id"]
        character_id = row["character_id"]
        control_map[player_id] = character_id
        party[player_id] = {
            "character_id": character_id,
            "stats": {"HP": None, "SAN": None, "MP": None, "LUCK": None},
            "conditions": [],
            "inventory": [],
            "knowledge": [],
            "position": "LSNT_START_BIR_HALIM",
        }
    return party, control_map


def _shared_resources(player_count: int) -> dict:
    return {
        "water_liters": WATER_BY_PLAYER_COUNT[player_count],
        "fuel": {
            "tank_state": "FULL",
            "jerrycans_liters": [20, 20],
            "exact_tank_capacity_liters": None,
            "exact_consumption": None,
        },
        "vehicle": {
            "model": "Ford Fordor C11ADF",
            "condition": "OPERATIONAL",
            "damage": 0,
            "position": "LSNT_START_BIR_HALIM",
        },
        "radio": {"team_radio": True, "batteries": 2},
        "medical_kit": 1,
        "maps": True,
        "lamp": True,
        "navigation_gear": True,
    }


def _scenario_binding(source_hashes: dict[str, str], identity_mode: str) -> dict:
    return {
        "scenario_key": "SOLEIL_NOIR",
        "scenario_id": PAIR_ID,
        "pair_id": PAIR_ID,
        "source_ids": list(SOURCE_IDS),
        "source_hashes": copy.deepcopy(source_hashes),
        "source_identity_mode": identity_mode,
        "canonical_graph_sha256": canonical_graph_sha256(),
        "state_contract": list(STATE_BINDING),
        "legacy_runtime_allowed": False,
    }


def create_production_session(players: Iterable[dict], *, source_hashes: dict[str, str] | None = None) -> dict:
    """Production-shaped path. It must stay blocked until real v1.7 hashes are materialized."""
    before = None
    routed = resolve_route_dev("SOLEIL_NOIR", requested_pair_id=PAIR_ID, source_hashes=source_hashes)
    if routed.get("status") != "ROUTE_READY":
        return {
            "status": "FAIL_CLOSED",
            "code": routed.get("code", "SCENARIO_ROUTE_NOT_READY"),
            "route": routed,
            "before": before,
            "after": before,
        }
    return {"status": "UNREACHABLE_UNTIL_REAL_HASHES_MATERIALIZED"}


def create_synthetic_test_session(players: Iterable[dict], *, source_hashes: dict[str, str]) -> dict:
    """DEV-only harness. Synthetic hashes test state plumbing, never source authenticity."""
    rows = _validate_players(players)
    if set(source_hashes) != set(SOURCE_IDS):
        raise ValueError("SYNTHETIC_SOURCE_SET_INVALID")
    for value in source_hashes.values():
        if len(str(value)) != 64 or any(ch not in "0123456789abcdef" for ch in str(value).lower()):
            raise ValueError("SYNTHETIC_HASH_FORMAT_INVALID")
    party, control_map = _base_party(rows)
    state = {
        "dev_only": True,
        "authority_promoted": False,
        "world_time": "J1 08:00",
        "party_split": False,
        "party": party,
        "control_map": control_map,
        "romain_persy": {
            "name": "Romain Persy",
            "age": 33,
            "npc_autonomous": True,
            "replacement_pc": False,
            "position": "LSNT_START_BIR_HALIM",
            "status": "ACTIVE",
        },
        "shared_resources": _shared_resources(len(rows)),
        "front": {"state": "RELATIVELY_STABLE", "last_check": None},
        "factions": {},
        "shared_knowledge": [],
        "events": {"potential": [], "triggered": [], "obsolete": [], "resolved": []},
        "consequences_pending": [],
        "scenario_runtime": _scenario_binding(source_hashes, SYNTHETIC_IDENTITY_MODE),
    }
    return {
        "status": "SYNTHETIC_TEST_SESSION_READY",
        "identity_mode": SYNTHETIC_IDENTITY_MODE,
        "state": state,
        "public": public_descriptor(),
    }


def player_view(state: dict, player_id: str) -> dict:
    if player_id not in state.get("party", {}):
        return {"status": "BLOCKED", "code": "PLAYER_NOT_IN_SESSION"}
    own = copy.deepcopy(state["party"][player_id])
    return {
        "status": "READY",
        "scenario": public_descriptor(),
        "player_id": player_id,
        "character": own,
        "shared_resources": copy.deepcopy(state["shared_resources"]),
        "world_time": state["world_time"],
        "party_split": state["party_split"],
        "shared_knowledge": copy.deepcopy(state["shared_knowledge"]),
    }


def add_private_knowledge(state: dict, *, actor_player_id: str, character_id: str, fact_id: str) -> dict:
    before = digest(state)
    controlled = state.get("control_map", {}).get(actor_player_id)
    if controlled != character_id:
        return {"status": "BLOCKED", "code": "ACTOR_CHARACTER_MISMATCH", "before": before, "after": before}
    target = state["party"][actor_player_id]["knowledge"]
    if fact_id not in target:
        target.append(fact_id)
    return {"status": "COMMITTED", "before": before, "after": digest(state)}


def share_knowledge(state: dict, *, actor_player_id: str, fact_id: str) -> dict:
    before = digest(state)
    row = state.get("party", {}).get(actor_player_id)
    if row is None:
        return {"status": "BLOCKED", "code": "PLAYER_NOT_IN_SESSION", "before": before, "after": before}
    if fact_id not in row["knowledge"]:
        return {"status": "BLOCKED", "code": "FACT_NOT_KNOWN_BY_ACTOR", "before": before, "after": before}
    if fact_id not in state["shared_knowledge"]:
        state["shared_knowledge"].append(fact_id)
    return {"status": "COMMITTED", "before": before, "after": digest(state)}


def save_bundle(state: dict, secret: bytes) -> dict:
    payload = {"schema": SAVE_SCHEMA, "state": copy.deepcopy(state)}
    raw = canon(payload).encode("utf-8")
    return {
        "payload": payload,
        "auth": {
            "algorithm": "HMAC-SHA256",
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "hmac_sha256": hmac.new(secret, raw, hashlib.sha256).hexdigest(),
        },
    }


def restore_synthetic_test_bundle(bundle: dict, secret: bytes, expected_source_hashes: dict[str, str]) -> dict:
    try:
        if set(bundle) != {"payload", "auth"}:
            raise ValueError("BUNDLE_SHAPE_INVALID")
        payload = bundle["payload"]
        auth = bundle["auth"]
        if payload.get("schema") != SAVE_SCHEMA:
            raise ValueError("SAVE_SCHEMA_INVALID")
        raw = canon(payload).encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != auth.get("payload_sha256"):
            raise ValueError("PAYLOAD_HASH_MISMATCH")
        expected_hmac = hmac.new(secret, raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_hmac, str(auth.get("hmac_sha256", ""))):
            raise ValueError("SAVE_AUTHENTICATION_FAILED")
        state = copy.deepcopy(payload["state"])
        scenario = state.get("scenario_runtime") or {}
        expected_binding = _scenario_binding(expected_source_hashes, SYNTHETIC_IDENTITY_MODE)
        for key in (
            "scenario_key",
            "scenario_id",
            "pair_id",
            "source_ids",
            "source_hashes",
            "source_identity_mode",
            "canonical_graph_sha256",
            "legacy_runtime_allowed",
        ):
            if scenario.get(key) != expected_binding.get(key):
                raise ValueError("SCENARIO_BINDING_MISMATCH")
        if state.get("authority_promoted") is not False or state.get("dev_only") is not True:
            raise ValueError("DEV_AUTHORITY_FLAG_INVALID")
        return {"status": "RESTORED_STRICT_DEV", "state": state}
    except Exception as error:
        return {"status": "FAIL_CLOSED", "code": str(error)}
