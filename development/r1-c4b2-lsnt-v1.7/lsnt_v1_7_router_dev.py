from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECOVERY = ROOT / "recovery" / "recertification-r1"
if str(RECOVERY) not in sys.path:
    sys.path.insert(0, str(RECOVERY))

from scenario_router_r1_c4 import ScenarioRoute  # noqa: E402
from scenario_router_r1_c4b import ROUTES as ROUTES_C4B  # noqa: E402

ROUTER_ID = "SOLIDSTATE_LSNT_V1_7_ROUTER_R1_C4B2_DEV_V1"
PAIR_ID = "LSNT-V1.7-STANDALONE-1942"
KEEPER_DOCUMENT_ID = "LSNT-GARDIEN-V1.7-STANDALONE-1942"
PLAYER_DOCUMENT_ID = "LSNT-JOUEUR-V1.7-STANDALONE-1942"
SOURCE_IDS = ("LSNT_V1_7_KEEPER", "LSNT_V1_7_PLAYER")
LEGACY_PAIR_IDS = {
    "LSNT-V1.5-MULTI-1942",
    "LSNT-V1.6-HM-1942",
}

# Exact PDF hashes are intentionally absent until the v1.7 bytes are mounted.
EXPECTED_SOURCE_HASHES = {
    "LSNT_V1_7_KEEPER": None,
    "LSNT_V1_7_PLAYER": None,
}

LSNT_V1_7_CANONICAL_GRAPH_DEV = {
    "graph_version": "LSNT_V1_7_CANONICAL_GRAPH_R1_C4B2_DEV_V1",
    "start": "LSNT_START_BIR_HALIM",
    "nodes": [
        "LSNT_START_BIR_HALIM",
        "LSNT_NODE_CONVOY",
        "LSNT_NODE_SIDI_MARUT",
        "LSNT_NODE_FORT_17B",
        "LSNT_NODE_OASIS",
        "LSNT_NODE_WADI",
        "LSNT_NODE_CAMP_SALVI",
        "LSNT_NODE_QASR_IREM",
        "LSNT_NODE_CROISSANT_CREUX",
        "LSNT_NODE_RADIO_AXE",
        "LSNT_NODE_CHAMBRE_ZENITH",
        "LSNT_NODE_ROUTE_COTIERE",
        "LSNT_NODE_AERODROME_TMIMI",
    ],
    "investigation_links": {
        "LSNT_NODE_CONVOY": ["LSNT_NODE_CAMP_SALVI", "LSNT_NODE_QASR_IREM", "LSNT_TAG_ANOMALY"],
        "LSNT_NODE_FORT_17B": ["LSNT_NODE_CAMP_SALVI", "LSNT_TAG_TRANSFER"],
        "LSNT_NODE_OASIS": ["LSNT_NODE_CROISSANT_CREUX", "LSNT_TAG_SECONDARY_ENTRANCE"],
        "LSNT_NODE_CAMP_SALVI": ["LSNT_NODE_CHAMBRE_ZENITH", "LSNT_TAG_DANGER"],
        "LSNT_NODE_WADI": ["LSNT_TAG_NON_MILITARY_NATURE"],
        "LSNT_NODE_QASR_IREM": ["LSNT_TAG_ORIGIN", "LSNT_TAG_CLOSURE"],
        "LSNT_NODE_CROISSANT_CREUX": ["LSNT_TAG_CONTAINMENT"],
        "LSNT_NODE_RADIO_AXE": ["LSNT_TAG_MILITARY_CLOCK"],
    },
    "travel_records": [
        ["LSNT_START_BIR_HALIM", "LSNT_NODE_CONVOY", 35, [50, 70]],
        ["LSNT_NODE_CONVOY", "LSNT_NODE_SIDI_MARUT", 28, [45, 60]],
        ["LSNT_NODE_SIDI_MARUT", "LSNT_NODE_FORT_17B", 22, [35, 50]],
        ["LSNT_NODE_FORT_17B", "LSNT_NODE_WADI", 30, [60, 90]],
        ["LSNT_NODE_WADI", "LSNT_NODE_QASR_IREM", 18, [45, 75]],
        ["LSNT_TAG_INTERIOR", "LSNT_NODE_ROUTE_COTIERE", 55, [90, 150]],
        ["LSNT_NODE_ROUTE_COTIERE", "LSNT_NODE_AERODROME_TMIMI", 40, [50, 80]],
    ],
    "world_clock": [
        ["J1 08:00", "MISSION_START"],
        ["J1 17:00", "VOSS_INTEREST_IF_TRACES"],
        ["J1 23:40", "FIRST_NOTABLE_EXPANSION"],
        ["J2 06:00", "AXIS_PATROL_TO_CONVOY"],
        ["J2 14:00", "OASIS_MAY_CHANGE_BY_FRONT"],
        ["J2 23:40", "SHADOW_GATE_ACTIVITY_INCREASES"],
        ["J3 09:00", "VOSS_PREPARES_TRANSFER"],
        ["J3 16:00", "POSSIBLE_BOMBARDMENT"],
        ["J3 23:40", "EFFECT_ZONE_EXPANDS"],
        ["J4 05:10", "TRANSFER_DEPARTS_IF_VOSS_CONTROLS"],
        ["J4 12:00", "CRITICAL_ZENITH_IF_DEVICE_OPEN"],
    ],
    "front_track": {
        "check_times": ["06:00", "18:00"],
        "facts_override_roll": True,
        "fallback_die": "1D6",
        "fallback_ranges": {"1-2": "AXIS", "3-4": "STATUS_QUO", "5-6": "ALLIES"},
        "causal_modifier_max_per_significant_event": 1,
        "unit_teleportation_forbidden": True,
    },
    "exposure": {
        "range": [0, 6],
        "increments": {"BRIEF_ANOMALY": 1, "PROLONGED": 2, "DIRECT_CONTACT": 3},
        "pow_check_thresholds": [2, 4, 6],
        "trigger_for_suspense_forbidden": True,
    },
    "sanity_loss_records": [
        ["SHADOW_MOVES_AFTER_STOP", "0", "1D3"],
        ["SHADOW_PRECEDES_GESTURE", "1", "1D4"],
        ["DISCOVER_SHADOW_GATE", "1", "1D6"],
        ["SEE_CONSTRAINED_HUMAN", "1D2", "1D8"],
        ["OBSERVE_ACTIVE_CHAMBER", "1D3", "1D10"],
        ["UNDERSTAND_PROPAGATION_POTENTIAL", "1D4", "1D10"],
    ],
    "ending_family_ids": [f"LSNT_ENDING_{i:02d}" for i in range(1, 11)],
    "ending_count": 10,
    "single_clue_required": False,
    "distinct_non_human_proof_routes": 3,
    "clue_order_forced": False,
    "alternative_routes_preserved": True,
    "causality_over_convergence": True,
    "world_time_authoritative": True,
}

STATE_BINDING = (
    "WORLD_TIME",
    "PARTY_SPLIT",
    "POSITION[CharacterID]",
    "ROMAIN_PERSY",
    "HP",
    "SAN",
    "MP",
    "LUCK",
    "EXPOSURE",
    "INVENTORY",
    "SHARED_RESOURCES",
    "VEHICLE",
    "WATER",
    "FUEL",
    "AMMO",
    "RADIO",
    "FRONT",
    "FACTIONS",
    "KNOWLEDGE",
    "SHARED_KNOWLEDGE",
    "EVENTS",
    "CONSEQUENCES_PENDING",
)

ROUTES = dict(ROUTES_C4B)
ROUTES["SOLEIL_NOIR"] = ScenarioRoute(
    "SOLEIL_NOIR",
    PAIR_ID,
    "Le Soleil Noir de Tobrouk",
    SOURCE_IDS,
    "DUAL_PROTECTED",
    None,
    "STRUCTURE_COMPILED_SOURCE_HASH_PENDING_DEV",
    True,
    "PLAYER_DOCUMENT_PLUS_ENGINE_FIREWALL",
    LSNT_V1_7_CANONICAL_GRAPH_DEV,
    PAIR_ID,
    "v1.7 standalone is the only runtime target for C4B2; v1.5/v1.6 are provenance only.",
)


def public_descriptor() -> dict:
    return {
        "scenario_key": "SOLEIL_NOIR",
        "scenario_id": PAIR_ID,
        "title": "Le Soleil Noir de Tobrouk",
        "pair_id": PAIR_ID,
        "era": "JUIN_1942",
        "supported_player_counts": [1, 2, 3, 4],
        "romain_persy": {"name": "Romain Persy", "age": 33, "npc_autonomous": True},
        "knowledge_partition": "Knowledge[CharacterID]",
        "keeper_truth_exposed": False,
    }


def _source_gate(provided_hashes: dict[str, str] | None) -> dict:
    provided_hashes = provided_hashes or {}
    for source_id in SOURCE_IDS:
        expected = EXPECTED_SOURCE_HASHES[source_id]
        if expected is None:
            return {
                "status": "BLOCKED",
                "code": "SOURCE_HASH_PENDING",
                "source_id": source_id,
            }
        provided = provided_hashes.get(source_id)
        if not provided:
            return {"status": "BLOCKED", "code": "SOURCE_HASH_MISSING", "source_id": source_id}
        if provided != expected:
            return {
                "status": "BLOCKED",
                "code": "SOURCE_HASH_MISMATCH",
                "source_id": source_id,
                "expected_sha256": expected,
                "actual_sha256": provided,
            }
    return {"status": "VERIFIED", "code": "SOURCE_PAIR_IDENTITY_PASS"}


def resolve_route_dev(
    scenario_key: str,
    *,
    requested_pair_id: str | None = None,
    source_hashes: dict[str, str] | None = None,
) -> dict:
    key = str(scenario_key).upper()
    if key != "SOLEIL_NOIR":
        route = ROUTES.get(key)
        if route is None:
            return {"status": "BLOCKED", "code": "SCENARIO_NOT_REGISTERED", "scenario_key": scenario_key}
        return {"status": "DELEGATED_TO_FROZEN_PARENT", "route": copy.deepcopy(dict(route.__dict__))}

    if requested_pair_id in LEGACY_PAIR_IDS:
        return {
            "status": "BLOCKED",
            "code": "LEGACY_SCENARIO_PAIR_FORBIDDEN",
            "requested_pair_id": requested_pair_id,
            "required_pair_id": PAIR_ID,
        }
    if requested_pair_id not in {None, PAIR_ID}:
        return {
            "status": "BLOCKED",
            "code": "SCENARIO_PAIR_MISMATCH",
            "requested_pair_id": requested_pair_id,
            "required_pair_id": PAIR_ID,
        }

    gate = _source_gate(source_hashes)
    if gate["status"] != "VERIFIED":
        return {
            "status": "BLOCKED",
            "code": gate["code"],
            "router_id": ROUTER_ID,
            "scenario_key": key,
            "required_pair_id": PAIR_ID,
            "source_gate": gate,
            "public": public_descriptor(),
        }

    return {
        "status": "ROUTE_READY",
        "router_id": ROUTER_ID,
        "route": copy.deepcopy(dict(ROUTES[key].__dict__)),
        "state_binding": list(STATE_BINDING),
        "public": public_descriptor(),
    }


def player_projection_dev(route_result: dict) -> dict:
    public = copy.deepcopy(route_result.get("public") or public_descriptor())
    return {
        "status": "READY" if route_result.get("status") == "ROUTE_READY" else "PREFLIGHT_BLOCKED",
        "scenario": public,
        "code": None if route_result.get("status") == "ROUTE_READY" else route_result.get("code"),
    }
