from __future__ import annotations

import copy

from scenario_router_r1_c4 import ScenarioRoute
from scenario_router_r1_c4b import ROUTES as ROUTES_C4B
from source_adapter_r1_c4b import verify_source_c4b

ROUTER_ID = "SOLIDSTATE_CANONICAL_SCENARIO_ROUTER_R1_C4B2_LSNT_V1"

LSNT_PATH = {
    "graph_version": "LSNT_V1_5_CANONICAL_GRAPH_R1_C4B2_V1",
    "start": "LSNT_START_BIR_HALIM_BRIEFING",
    "nodes": [
        "LSNT_START_BIR_HALIM_BRIEFING",
        "LSNT_NODE_ABANDONED_CONVOY",
        "LSNT_NODE_SIDI_MARUT",
        "LSNT_NODE_FORT_17B",
        "LSNT_NODE_WADI_MIRRORS",
        "LSNT_NODE_CAMP_SALVI",
        "LSNT_NODE_QASR_IREM",
        "LSNT_NODE_CROISSANT_CREUX",
        "LSNT_NODE_CHAMBER_ZENITH",
        "LSNT_NODE_TMIMI_AIRFIELD",
        "LSNT_NODE_COASTAL_ROAD",
        "LSNT_HUB_GROUP_RESOLUTION",
        "LSNT_TERMINAL_GROUP_CONCLUSION",
    ],
    "travel_edges": [
        ["LSNT_START_BIR_HALIM_BRIEFING", "LSNT_NODE_ABANDONED_CONVOY"],
        ["LSNT_NODE_ABANDONED_CONVOY", "LSNT_NODE_SIDI_MARUT"],
        ["LSNT_NODE_SIDI_MARUT", "LSNT_NODE_FORT_17B"],
        ["LSNT_NODE_FORT_17B", "LSNT_NODE_WADI_MIRRORS"],
        ["LSNT_NODE_WADI_MIRRORS", "LSNT_NODE_QASR_IREM"],
        ["LSNT_NODE_QASR_IREM", "LSNT_NODE_CHAMBER_ZENITH"],
        ["LSNT_NODE_CAMP_SALVI", "LSNT_NODE_CHAMBER_ZENITH"],
        ["LSNT_NODE_CROISSANT_CREUX", "LSNT_NODE_CHAMBER_ZENITH"],
        ["LSNT_NODE_QASR_IREM", "LSNT_HUB_GROUP_RESOLUTION"],
        ["LSNT_NODE_CHAMBER_ZENITH", "LSNT_HUB_GROUP_RESOLUTION"],
        ["LSNT_NODE_TMIMI_AIRFIELD", "LSNT_HUB_GROUP_RESOLUTION"],
        ["LSNT_NODE_COASTAL_ROAD", "LSNT_HUB_GROUP_RESOLUTION"],
        ["LSNT_HUB_GROUP_RESOLUTION", "LSNT_TERMINAL_GROUP_CONCLUSION"],
    ],
    "clue_network": {
        "LSNT_NODE_ABANDONED_CONVOY": ["PROGETTO_NERO", "QASR_IREM", "ANOMALY"],
        "LSNT_NODE_FORT_17B": ["CAMP_SALVI", "TRANSFER_TIMELINE"],
        "LSNT_NODE_SIDI_MARUT": ["CROISSANT_CREUX", "SECONDARY_ACCESS"],
        "LSNT_NODE_CAMP_SALVI": ["CHAMBER_ZENITH", "DANGER"],
        "LSNT_NODE_WADI_MIRRORS": ["NON_MILITARY_NATURE"],
        "LSNT_NODE_QASR_IREM": ["ORIGIN", "CLOSURE"],
        "LSNT_NODE_CROISSANT_CREUX": ["CONTAINMENT"],
        "AXIS_RADIO": ["MILITARY_TIMELINE"],
    },
    "world_timeline": [
        "J1_0800_MISSION",
        "J1_1700_AXIS_INTEREST_IF_TRACES",
        "J1_2340_FIRST_NOTABLE_EXPANSION",
        "J2_0600_AXIS_PATROL_CONVOY",
        "J2_1400_OASIS_FRONT_DEPENDENT",
        "J2_2340_SHADOW_DOOR_INCREASE",
        "J3_0900_TRANSFER_PREPARATION",
        "J3_1600_POSSIBLE_BOMBARDMENT",
        "J3_2340_EFFECT_ZONE_GROWS",
        "J4_0510_TRANSFER_DEPARTURE_IF_AXIS_CONTROL",
        "J4_1200_CRITICAL_ZENITH_IF_OPEN",
    ],
    "front_track_checks": ["0600", "1800"],
    "exposure_thresholds": [2, 4, 6],
    "ending_families": [
        "LE_MIDI_REFERME",
        "VICTOIRE_MILITAIRE",
        "VICTOIRE_INCOMPLETE",
        "CONVOI_DE_LOMBRE",
        "FRAGMENT_ALLIE",
        "QASR_IREM_DETRUITE",
        "ZENITH_NOIR",
        "ALLIANCE_AMERE",
        "ENQUETE_ABANDONNEE",
        "GAME_OVER",
    ],
    "resolution_methods": [
        "CLOSE_BY_INSCRIPTIONS",
        "REBURY_CHAMBER",
        "DESTROY_FRAGMENT_UNPREDICTABLE",
        "EXTRACT_FRAGMENT_WORSENS_CARRIER_AREA",
        "SABOTAGE_PROGETTO_NERO",
        "EVACUATE_AND_REPORT",
    ],
    "single_clue_indispensable": False,
    "non_human_nature_routes_minimum": 3,
    "alternative_investigation_routes_preserved": True,
    "clue_order_forced": False,
    "world_clock_j1_j4_preserved": True,
    "front_track_preserved": True,
    "knowledge_partition_required": True,
    "timeline_synchronizer_required_if_split": True,
    "individual_exposure_required": True,
    "individual_sanity_required": True,
    "party_resolution_required": True,
    "ten_ending_families_preserved": True,
    "bcr_ally_autonomous": True,
}

ROUTES = dict(ROUTES_C4B)
ROUTES["SOLEIL_NOIR"] = ScenarioRoute(
    "SOLEIL_NOIR",
    "LSNT-V1.5-MULTI-1942",
    "Le Soleil Noir de Tobrouk",
    ("SOLEIL_NOIR_KEEPER", "SOLEIL_NOIR_PLAYER"),
    "DUAL_PROTECTED",
    None,
    "RECOVERY_SOURCE_COMPILED_C4B2",
    True,
    "PLAYER_DOCUMENT_PLUS_ENGINE_FIREWALL",
    LSNT_PATH,
    "LSNT-V1.5-MULTI-1942",
    "C4B2 compiles the exact v1.5 protected source pair into a non-linear multiplayer route while preserving C4B and earlier routes.",
)


def _public_route(route: ScenarioRoute) -> dict:
    data = dict(route.__dict__)
    data.pop("canonical_path", None)
    data.pop("note", None)
    return data


def resolve_route_c4b2(scenario_key: str, source_paths: dict) -> dict:
    key = str(scenario_key).upper()
    route = ROUTES.get(key)
    if route is None:
        return {"status": "BLOCKED", "code": "SCENARIO_NOT_REGISTERED", "scenario_key": scenario_key}
    verified = []
    for source_id in route.source_ids:
        result = verify_source_c4b(source_id, source_paths.get(source_id, ""))
        if result.get("status") != "VERIFIED":
            return {
                "status": "BLOCKED",
                "code": "SCENARIO_SOURCE_PREFLIGHT_FAILED",
                "router_id": ROUTER_ID,
                "scenario_key": key,
                "failed_source": source_id,
                "source_result": result,
            }
        verified.append({"source_id": source_id, "sha256": result["sha256"], "role": result["role"]})
    if not route.canonical_path_ready:
        return {
            "status": "SOURCE_READY_PATH_BLOCKED",
            "code": "CANONICAL_PATH_UNCOMPILED",
            "router_id": ROUTER_ID,
            "route": _public_route(route),
            "sources": verified,
        }
    return {
        "status": "ROUTE_READY",
        "router_id": ROUTER_ID,
        "route": copy.deepcopy(dict(route.__dict__)),
        "sources": verified,
    }
