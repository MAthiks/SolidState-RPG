from __future__ import annotations

import copy
from dataclasses import dataclass

from source_adapter_r1 import verify_source

ROUTER_ID = "SOLIDSTATE_CANONICAL_SCENARIO_ROUTER_R1_C4_V1"


@dataclass(frozen=True)
class ScenarioRoute:
    scenario_key: str
    scenario_id: str
    title: str
    source_ids: tuple[str, ...]
    source_mode: str
    release_checkpoint: int | None
    release_class: str
    canonical_path_ready: bool
    player_projection_mode: str
    canonical_path: dict | None = None
    source_pair_id: str | None = None
    note: str | None = None


ROUTES = {
    "MAISON_PENDU": ScenarioRoute(
        "MAISON_PENDU",
        "SCENARIO3_MAISON_DU_PENDU_SOURCE_UNVERIFIED_C4",
        "La Maison du Pendu",
        ("MAISON_PENDU_SOURCE",),
        "SINGLE_SOURCE_UNVERIFIED",
        None,
        "BLOCKED_SOURCE_IDENTITY_UNVERIFIED",
        False,
        "ENGINE_FILTER_REQUIRED",
        None,
        None,
        "C3 incorrectly mapped this scenario to AE_COLLECTION. C4 refuses that substitution.",
    ),
    "BRUME": ScenarioRoute(
        "BRUME",
        "SCENARIO4_REGISTRES_DE_BRUME_V1_1",
        "Les Registres de Brume",
        ("BRUME_KEEPER", "BRUME_PLAYER"),
        "DUAL_PROTECTED",
        319,
        "PASS_REAL",
        True,
        "PLAYER_DOCUMENT_PLUS_ENGINE_FIREWALL",
        {"start": "BRUME_NODE_MAIRIE", "via": ["BRUME_NODE_GALERIE_WARD"], "terminal": "BRUME_TERMINAL_MAREE_REFERMEE", "path_length": 2},
    ),
    "ANTRE": ScenarioRoute(
        "ANTRE",
        "ANTRE-ABOMINATION-SOURCE",
        "L'Antre de l'abomination",
        ("ANTRE_SOURCE",),
        "SINGLE_SOURCE",
        321,
        "PASS_REAL",
        True,
        "ENGINE_FILTER_REQUIRED",
        {"terminal": "ANTRE_EPILOGUE_OPEN_KEEPER_RESOLUTION", "path_length": 10, "open_epilogue": True},
    ),
    "MUSE": ScenarioRoute(
        "MUSE",
        "SCENARIO6_MUSE_EQUIVOQUE_V1",
        "Muse équivoque aux yeux de sel gemme",
        ("AE_COLLECTION",),
        "COLLECTION_SLICE",
        323,
        "PASS_REAL",
        True,
        "ENGINE_FILTER_REQUIRED",
        {"start": "MUSE_ACT_I_WITNESS_SUICIDE", "terminal": "MUSE_TERMINAL_ENMOUTEF_BODY_FUTURE", "path_length": 6, "alternative_endings_preserved": True},
    ),
    "EXPLORATEUR": ScenarioRoute(
        "EXPLORATEUR",
        "SCENARIO7_EXPLORATEUR_ASSASSINE",
        "L’Explorateur assassiné",
        ("AE_COLLECTION",),
        "COLLECTION_SLICE",
        325,
        "PASS_REAL",
        True,
        "ENGINE_FILTER_REQUIRED",
        {"terminal": "EXPLORATEUR_TERMINAL_JUDICIAL_CONCLUSION", "path_length": 10, "clue_anchor_edges_used": 0, "alternative_investigation_routes_preserved": True},
    ),
    "SOLEIL_NOIR": ScenarioRoute(
        "SOLEIL_NOIR",
        "LSNT-V1.5-MULTI-1942",
        "Le Soleil Noir de Tobrouk",
        ("SOLEIL_NOIR_KEEPER", "SOLEIL_NOIR_PLAYER"),
        "DUAL_PROTECTED",
        None,
        "SOURCE_PAIR_VERIFIED_PATH_UNCOMPILED_C4",
        False,
        "PLAYER_DOCUMENT_PLUS_ENGINE_FIREWALL",
        None,
        "LSNT-V1.5-MULTI-1942",
        "C4 preserves the v1.5 pair used by frozen C3; later scenario editions require an explicit migration.",
    ),
}


def _public_route(route: ScenarioRoute) -> dict:
    data = dict(route.__dict__)
    # canonical path IDs are keeper-side routing metadata; not part of player projection.
    data.pop("canonical_path", None)
    data.pop("note", None)
    return data


def resolve_route(scenario_key: str, source_paths: dict) -> dict:
    key = str(scenario_key).upper()
    route = ROUTES.get(key)
    if route is None:
        return {"status": "BLOCKED", "code": "SCENARIO_NOT_REGISTERED", "scenario_key": scenario_key}
    if key == "MAISON_PENDU":
        return {
            "status": "BLOCKED",
            "code": "SCENARIO_SOURCE_IDENTITY_UNVERIFIED",
            "router_id": ROUTER_ID,
            "route": _public_route(route),
            "correction": "AE_COLLECTION_SUBSTITUTION_FORBIDDEN",
        }
    verified = []
    for source_id in route.source_ids:
        result = verify_source(source_id, source_paths.get(source_id, ""))
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


def player_projection(route_result: dict) -> dict:
    if route_result.get("status") not in {"ROUTE_READY", "SOURCE_READY_PATH_BLOCKED"}:
        return {"status": "BLOCKED", "code": route_result.get("code", "ROUTE_NOT_READY")}
    route = dict(route_result["route"])
    route.pop("canonical_path", None)
    route.pop("note", None)
    return {
        "status": "READY",
        "scenario": {
            "scenario_key": route["scenario_key"],
            "scenario_id": route["scenario_id"],
            "title": route["title"],
            "source_mode": route["source_mode"],
            "source_pair_id": route.get("source_pair_id"),
        },
    }
