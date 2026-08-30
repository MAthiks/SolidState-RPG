from __future__ import annotations

import copy
import re

MODULE_ID = "LSNT_V1_7_PRECOMPILE_GATE_R1_C4B2_V1"
SCENARIO_ID = "LSNT-V1.7-STANDALONE-1942"
KEEPER_ID = "LSNT-GARDIEN-V1.7-STANDALONE-1942"
PLAYER_ID = "LSNT-JOUEUR-V1.7-STANDALONE-1942"
SUPERSEDED = ("LSNT-V1.5-MULTI-1942", "LSNT-V1.6-HM-1942")
V15_HASHES = {
    "9c1e609d50250599a30fdb3ec899cf8b62cc9638944891900d0a982d958760f6",
    "9838b2f3e816e1ce08c29fa148eef765d2d1934a334ce8a78f8313fe6dc1b889",
}

# Structure-only draft. It is deliberately non-executable until exact PDF byte hashes are bound.
PRECOMPILE = {
    "schema": "SOLIDSTATE_LSNT_V1_7_PRECOMPILE_DRAFT_V1",
    "scenario_id": SCENARIO_ID,
    "pair_id": SCENARIO_ID,
    "edition": "1.7-STANDALONE",
    "runtime_dependency_on_v1_5": False,
    "status": "DRAFT_NON_EXECUTABLE_SOURCE_HASHES_PENDING",
    "source_identity": {
        "keeper": {"source_id": KEEPER_ID, "sha256": None, "bytes_verified": False},
        "player": {"source_id": PLAYER_ID, "sha256": None, "bytes_verified": False},
    },
    "launch": {
        "era": "1942-06",
        "player_count_min": 1,
        "player_count_max": 4,
        "start_node": "BIR_HALIM",
        "bcra_npc": "ROMAIN_PERSY",
        "bcra_autonomous": True,
    },
    "structure": {
        "world_clock": [
            "J1_0800", "J1_1700", "J1_2340", "J2_0600", "J2_1400",
            "J2_2340", "J3_0900", "J3_1600", "J3_2340", "J4_0510", "J4_1200",
        ],
        "front_checks": ["0600", "1800"],
        "ending_family_count": 10,
        "single_clue_indispensable": False,
        "minimum_independent_nonhuman_routes": 3,
        "knowledge_partition_required": True,
        "timeline_sync_if_split": True,
        "individual_exposure_thresholds": [2, 4, 6],
        "individual_sanity": True,
    },
    "travel": {
        "BIR_HALIM__CONVOY": {"distance_km": 35, "minutes": [50, 70]},
        "CONVOY__SIDI_MARUT": {"distance_km": 28, "minutes": [45, 60]},
        "SIDI_MARUT__FORTS": {"distance_km": 22, "minutes": [35, 50]},
        "FORTS__WADIS": {"distance_km": 30, "minutes": [60, 90]},
        "WADIS__RUINS": {"distance_km": 18, "minutes": [45, 75]},
        "INTERIOR__COASTAL_ROAD": {"distance_km": 55, "minutes": [90, 150]},
        "COASTAL_ROAD__TMIMI": {"distance_km": 40, "minutes": [50, 80]},
    },
    "shared_resources": {
        "water_liters_by_player_count": {1: 32, 2: 48, 3: 64, 4: 80},
        "team_radio_batteries": 2,
        "fuel_state": "FULL_TANK_PLUS_TWO_20L_JERRICANS",
        "vehicle_id": "FORD_C11ADF",
        "vehicle_status": "OPERATIONAL",
        "fuel_tank_capacity_liters": None,
        "fuel_consumption_l_per_100km": None,
    },
    "state_contract": [
        "WORLD_TIME", "PARTY_SPLIT", "POSITION", "ROMAIN_PERSY",
        "HP_SAN_MP_LUCK", "EXPOSURE", "INVENTORY", "SHARED_RESOURCES",
        "VEHICLE", "WATER", "FUEL", "AMMO", "RADIO", "FRONT", "FACTIONS",
        "KNOWLEDGE", "SHARED_KNOWLEDGE", "EVENTS", "CONSEQUENCES_PENDING",
    ],
    "player_projection_contract": {
        "mission_visible": True,
        "bcra_visible": True,
        "vehicle_and_shared_resources_visible": True,
        "individual_inventory_visible": True,
        "known_information_only": True,
        "guardian_truth_visible": False,
        "hidden_future_events_visible": False,
        "source_hashes_visible": False,
        "canonical_graph_visible": False,
    },
    "activation_policy": {
        "requires_two_exact_pdf_hashes": True,
        "requires_hashes_computed_from_bytes": True,
        "reuse_v1_5_hashes": False,
        "fallback_to_superseded_pair": False,
        "compile_private_guardian_graph_before_identity": False,
    },
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def public_precompile_status() -> dict:
    out = copy.deepcopy(PRECOMPILE)
    out["source_identity"]["keeper"].pop("sha256", None)
    out["source_identity"]["player"].pop("sha256", None)
    return out


def bind_exact_source_identities(*, keeper_sha256: str | None, player_sha256: str | None,
                                 keeper_bytes_verified: bool = False,
                                 player_bytes_verified: bool = False) -> dict:
    before = copy.deepcopy(PRECOMPILE["source_identity"])
    hashes = (("keeper", keeper_sha256, keeper_bytes_verified), ("player", player_sha256, player_bytes_verified))
    for role, value, verified in hashes:
        if not value:
            return {"status": "BLOCKED", "code": "EXACT_SOURCE_HASH_MISSING", "role": role, "before": before}
        value = str(value).lower()
        if not HEX64.fullmatch(value):
            return {"status": "BLOCKED", "code": "SOURCE_HASH_FORMAT_INVALID", "role": role, "before": before}
        if value in V15_HASHES:
            return {"status": "BLOCKED", "code": "SUPERSEDED_HASH_REUSE_FORBIDDEN", "role": role, "before": before}
        if not verified:
            return {"status": "BLOCKED", "code": "SOURCE_BYTES_NOT_VERIFIED", "role": role, "before": before}
    if keeper_sha256.lower() == player_sha256.lower():
        return {"status": "BLOCKED", "code": "KEEPER_PLAYER_HASH_COLLISION", "before": before}
    bound = copy.deepcopy(PRECOMPILE)
    bound["source_identity"]["keeper"].update({"sha256": keeper_sha256.lower(), "bytes_verified": True})
    bound["source_identity"]["player"].update({"sha256": player_sha256.lower(), "bytes_verified": True})
    bound["status"] = "SOURCE_IDENTITY_2_OF_2_READY_FOR_PRIVATE_COMPILATION"
    return {"status": "READY", "module_id": MODULE_ID, "manifest": bound}


def player_projection_template(player_count: int) -> dict:
    if not isinstance(player_count, int) or isinstance(player_count, bool) or not 1 <= player_count <= 4:
        return {"status": "BLOCKED", "code": "PLAYER_COUNT_OUT_OF_RANGE"}
    water = PRECOMPILE["shared_resources"]["water_liters_by_player_count"][player_count]
    return {
        "status": "PLAYER_PROJECTION_TEMPLATE_READY",
        "scenario_id": SCENARIO_ID,
        "era": PRECOMPILE["launch"]["era"],
        "player_count": player_count,
        "bcra_npc": "Romain Persy",
        "bcra_autonomous": True,
        "vehicle": {"id": "FORD_C11ADF", "status": "OPERATIONAL"},
        "shared_resources": {
            "water_liters": water,
            "team_radio_batteries": 2,
            "fuel": "FULL_TANK_PLUS_TWO_20L_JERRICANS",
        },
        "state_fields": ["HP", "SAN", "MP", "LUCK", "CONDITIONS", "INVENTORY", "KNOWN_INFORMATION"],
        "source_hashes_exposed": False,
        "canonical_graph_exposed": False,
        "guardian_truth_exposed": False,
    }
