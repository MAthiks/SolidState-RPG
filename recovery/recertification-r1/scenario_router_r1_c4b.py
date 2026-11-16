from __future__ import annotations

import copy

from scenario_router_r1_c4 import ROUTES as ROUTES_C4, ScenarioRoute, player_projection
from source_adapter_r1_c4b import verify_source_c4b

ROUTER_ID = "SOLIDSTATE_CANONICAL_SCENARIO_ROUTER_R1_C4B_V1"

MAISON_PATH = {
    "graph_version": "MAISON_PENDU_CANONICAL_GRAPH_R1_C4B_V1",
    "start": "MP_START_PARIS_CASE",
    "nodes": [
        "MP_START_PARIS_CASE",
        "MP_HUB_PARIS_INVESTIGATION",
        "MP_NODE_APARTMENT_MARAIS",
        "MP_NODE_MINISTRY_WAR",
        "MP_NODE_POLICE",
        "MP_NODE_GERNEC",
        "MP_NODE_LANNION",
        "MP_HUB_RESOLUTION",
        "MP_TERMINAL_DOSSIER_GOV_PRESS",
        "MP_TERMINAL_BASE_DIRECT_OPEN",
    ],
    "edges": [
        ["MP_START_PARIS_CASE", "MP_HUB_PARIS_INVESTIGATION"],
        ["MP_HUB_PARIS_INVESTIGATION", "MP_NODE_APARTMENT_MARAIS"],
        ["MP_HUB_PARIS_INVESTIGATION", "MP_NODE_MINISTRY_WAR"],
        ["MP_HUB_PARIS_INVESTIGATION", "MP_NODE_POLICE"],
        ["MP_NODE_APARTMENT_MARAIS", "MP_NODE_GERNEC"],
        ["MP_NODE_GERNEC", "MP_NODE_LANNION"],
        ["MP_NODE_LANNION", "MP_HUB_RESOLUTION"],
        ["MP_HUB_RESOLUTION", "MP_TERMINAL_DOSSIER_GOV_PRESS"],
        ["MP_HUB_RESOLUTION", "MP_TERMINAL_BASE_DIRECT_OPEN"],
    ],
    "optional_side_nodes": ["MP_NODE_MINISTRY_WAR", "MP_NODE_POLICE"],
    "alternative_routes_preserved": True,
    "clue_order_forced": False,
    "open_resolution_preserved": True,
    "source_page_text_sha256": {
        "1": "0555b72cfe022b7a52dce32f0a675ec8e8a84f41da2948cbbfde7a1d36dbdf07",
        "2": "0b89b5419f1a5bc9fc9360f0f6b45ed837028ae4482dcf9cba0f8d6ee4e6bee2",
        "3": "0991f15f70b24926c2f50494d723d742e62e030df63bb4cc4e9c8cbcda4aba36",
        "4": "ffc8b9c8d716dead231cf921a573280b5d29cca669afbd7acad6e44da5aca4af",
    },
}

ROUTES = dict(ROUTES_C4)
ROUTES["MAISON_PENDU"] = ScenarioRoute(
    "MAISON_PENDU",
    "SCENARIO3_MAISON_DU_PENDU_R1_C4B",
    "La Maison du Pendu",
    ("MAISON_PENDU_SOURCE",),
    "SINGLE_SOURCE",
    None,
    "RECOVERY_SOURCE_COMPILED_C4B",
    True,
    "ENGINE_FILTER_REQUIRED",
    MAISON_PATH,
    None,
    "C4B replaces C3's invalid AE_COLLECTION substitution with an exact private-source identity and a source-backed non-linear investigation graph.",
)


def _public_route(route: ScenarioRoute) -> dict:
    data = dict(route.__dict__)
    data.pop("canonical_path", None)
    data.pop("note", None)
    return data


def resolve_route_c4b(scenario_key: str, source_paths: dict) -> dict:
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
