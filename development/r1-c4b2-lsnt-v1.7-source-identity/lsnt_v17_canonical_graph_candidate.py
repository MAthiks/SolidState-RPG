from __future__ import annotations

import copy

MODULE_ID = "LSNT_V1_7_CANONICAL_GRAPH_CANDIDATE_R1_C4B2_V1"
SCENARIO_ID = "LSNT-V1.7-STANDALONE-1942"
KEEPER_ID = "LSNT-GARDIEN-V1.7-STANDALONE-1942"
PLAYER_ID = "LSNT-JOUEUR-V1.7-STANDALONE-1942"
STATUS = "GRAPH_STRUCTURALLY_COMPILED_SOURCE_IDENTITY_PENDING"

# Deliberately empty until the exact v1.7 PDF bytes are materialized.
CANONICAL_KEEPER_SHA256 = None
CANONICAL_PLAYER_SHA256 = None

V15_HASHES = {
    "9c1e609d50250599a30fdb3ec899cf8b62cc9638944891900d0a982d958760f6",
    "9838b2f3e816e1ce08c29fa148eef765d2d1934a334ce8a78f8313fe6dc1b889",
}

GRAPH = {
    "schema": "SOLIDSTATE_LSNT_V1_7_CANONICAL_GRAPH_CANDIDATE_V1",
    "scenario_id": SCENARIO_ID,
    "source_pair": SCENARIO_ID,
    "source_ids": {"keeper": KEEPER_ID, "player": PLAYER_ID},
    "status": STATUS,
    "runtime_dependency_on_v1_5": False,
    "launch": {
        "era": "1942-06",
        "zone": "CYRENAICA_TOBRUK_QASR_IREM",
        "duration_hours": [10, 15],
        "player_count": [1, 4],
        "start_node": "BIR_HALIM",
        "bcra_npc": "ROMAIN_PERSY",
        "bcra_autonomous": True,
        "ending_family_count": 10,
    },
    "locations": {
        "BIR_HALIM": {"function": "ALLIED_START", "initial": "RADIO_AND_6_SUPPORT_MEN"},
        "ABANDONED_CONVOY": {"function": "FIRST_MYSTERY", "initial": "7_VEHICLES_INTERNAL_IMPACTS_TRACKS_SOUTH"},
        "SIDI_MARUT": {"function": "SUPPLY_RUMORS", "initial": "NEUTRAL_CONTROL_VARIABLE"},
        "FORT_17B": {"function": "PRISONERS_AND_MAPS", "initial": "11_ITALIANS"},
        "WADI_MIRRORS": {"function": "ANOMALIES", "initial": "REFRACTIONS_VITRIFIED_ROCKS"},
        "SALVI_CAMP": {"function": "FORWARD_LAB", "initial": "DISMANTLABLE"},
        "QASR_IREM": {"function": "MAIN_RUINS", "initial": "MULTIPLE_ENTRANCES"},
        "ZENITH_CHAMBER": {"function": "COSMIC_NODE", "initial": "FRAGMENT_AND_DEVICE"},
        "TMIMI_AIRFIELD": {"function": "POSSIBLE_EXTRACTION", "initial": "DEPENDS_ON_FRONT"},
        "COASTAL_ROAD": {"function": "STRATEGIC_MOBILITY", "initial": "BOMBARDMENTS_CONTROLS"},
    },
    "clue_network": {
        "CONVOY": {"clues": ["FALSE_COMPASSES", "TRACKS", "FILM", "JOURNAL"], "connections": ["SALVI", "QASR_IREM", "ANOMALY"]},
        "FORT_17B": {"clues": ["CODED_ORDERS", "PRISONER"], "connections": ["SALVI_CAMP", "TRANSFER"]},
        "OASIS": {"clues": ["CITY_WHERE_NOON_DOES_NOT_ENTER"], "connections": ["CROISSANT_CREUX", "SECONDARY_ENTRANCE"]},
        "SALVI_CAMP": {"clues": ["PLATES", "NOTES", "MAP"], "connections": ["CHAMBER", "DANGER"]},
        "WADI": {"clues": ["SHIFTED_SHADOWS", "BLACK_GLASS"], "connections": ["NON_MILITARY_NATURE"]},
        "QASR_IREM": {"clues": ["INSCRIPTIONS", "CARTRIDGES", "BODY"], "connections": ["ORIGIN", "CLOSURE"]},
        "CROISSANT_CREUX": {"clues": ["INCOMPLETE_RITUAL", "DEVICE"], "connections": ["CONFINEMENT"]},
        "AXIS_RADIO": {"clues": ["TRANSFER_ORDER"], "connections": ["MILITARY_CLOCK"]},
    },
    "clue_policy": {
        "single_clue_indispensable": False,
        "independent_nonhuman_routes": 3,
        "knowledge_store": "KNOWLEDGE[CharacterID]",
    },
    "world_clock": [
        ("J1_0800", "MISSION_ASSIGNED_FRONT_RELATIVELY_STABLE"),
        ("J1_1700", "VOSS_LEARNS_ALLIED_INTEREST_IF_TRACES_LEFT"),
        ("J1_2340", "FIRST_NOTABLE_EXPANSION"),
        ("J2_0600", "AXIS_PATROL_TO_CONVOY"),
        ("J2_1400", "OASIS_MAY_CHANGE_BY_FRONT_TRACK"),
        ("J2_2340", "SHADOW_BEARERS_MORE_ACTIVE"),
        ("J3_0900", "VOSS_PREPARES_TRANSFER"),
        ("J3_1600", "BOMBARDMENT_POSSIBLE"),
        ("J3_2340", "EFFECT_ZONE_EXPANDS"),
        ("J4_0510", "TRANSFER_DEPARTS_IF_VOSS_CONTROLS"),
        ("J4_1200", "CRITICAL_ZENITH_IF_DEVICE_OPEN"),
    ],
    "front_track": {
        "checks": ["0600", "1800"],
        "deterministic_if_facts_decide": True,
        "otherwise_roll": "1D6",
        "outcomes": {"1-2": "AXIS", "3-4": "STATUS_QUO", "5-6": "ALLIES"},
        "causal_modifier_max_abs": 1,
        "unit_teleportation": False,
    },
    "travel": {
        "BIR_HALIM__ABANDONED_CONVOY": {"distance_km": 35, "minutes": [50, 70]},
        "ABANDONED_CONVOY__SIDI_MARUT": {"distance_km": 28, "minutes": [45, 60]},
        "SIDI_MARUT__FORTS": {"distance_km": 22, "minutes": [35, 50]},
        "FORTS__WADIS": {"distance_km": 30, "minutes": [60, 90]},
        "WADIS__RUINS": {"distance_km": 18, "minutes": [45, 75]},
        "INTERIOR__COASTAL_ROAD": {"distance_km": 55, "minutes": [90, 150]},
        "COASTAL_ROAD__TMIMI_AIRFIELD": {"distance_km": 40, "minutes": [50, 80]},
    },
    "exposure": {
        "range": [0, 6],
        "increments": {"BRIEF_ANOMALY": 1, "PROLONGED": 2, "DIRECT_CONTACT": 3},
        "pow_thresholds": [2, 4, 6],
        "success": "DELAY_MANIFESTATION_KEEP_COUNTER",
        "failure": "ADVANCE_ONE_STAGE",
        "suspense_trigger_forbidden": True,
    },
    "sanity": {
        "SHADOW_MOVES_AFTER_STOP": ["0", "1D3"],
        "SHADOW_PRECEDES_GESTURE": ["1", "1D4"],
        "DISCOVER_SHADOW_BEARER": ["1", "1D6"],
        "SEE_CONSTRAINED_HUMAN": ["1D2", "1D8"],
        "OBSERVE_ACTIVE_CHAMBER": ["1D3", "1D10"],
        "UNDERSTAND_PROPAGATION_POTENTIAL": ["1D4", "1D10"],
    },
    "shared_resources": {
        "water_liters_by_player_count": {1: 32, 2: 48, 3: 64, 4: 80},
        "vehicle": "FORD_FORDOR_C11ADF_DESERT",
        "vehicle_status": "OPERATIONAL_AT_BIR_HALIM",
        "fuel": "FULL_TANK_PLUS_TWO_20L_JERRICANS",
        "fuel_capacity_numeric": None,
        "fuel_consumption_numeric": None,
        "team_radio_batteries": 2,
        "persistent": ["WATER", "FUEL", "AMMO", "VEHICLE", "COMMUNICATIONS", "CARE", "WOUNDS"],
    },
    "resolution_methods": {
        "CLOSE_BY_INSCRIPTIONS": ["DURABLE_CONFINEMENT", "UNDERSTANDING_AND_ACCESS"],
        "REBURY_CHAMBER": ["STRONG_REDUCTION", "LONG_EXPLOSIVES_COLLAPSE"],
        "DESTROY_FRAGMENT": ["UNPREDICTABLE", "FRAGMENTATION_MULTIPLICATION"],
        "EXTRACT_FRAGMENT": ["TRANSPORT", "WORSENS_AROUND_CARRIER"],
        "SABOTAGE_PROGETTO_NERO": ["PREVENTS_EXPLOITATION", "PHENOMENON_ACTIVE"],
        "EVACUATE_REPORT": ["SAVES_LIVES", "PROBLEM_UNRESOLVED"],
    },
    "endings": [
        "LE_MIDI_REFERME", "VICTOIRE_MILITAIRE", "VICTOIRE_INCOMPLETE", "CONVOI_DE_LOMBRE",
        "FRAGMENT_ALLIE", "QASR_IREM_DETRUITE", "ZENITH_NOIR", "ALLIANCE_AMERE",
        "ENQUETE_ABANDONNEE", "GAME_OVER",
    ],
    "ending_policy": {
        "check_party_state": True,
        "check_world_state": True,
        "single_pc_death_ends_game": False,
        "romain_replacement_pc": False,
    },
    "state_contract": [
        "WORLD_TIME", "PARTY_SPLIT", "POSITION[CharacterID]", "ROMAIN_PERSY", "HP/SAN/MP/LUCK",
        "EXPOSURE", "INVENTORY", "SHARED_RESOURCES", "VEHICLE", "WATER", "FUEL", "AMMO",
        "RADIO", "FRONT", "FACTIONS", "KNOWLEDGE", "SHARED_KNOWLEDGE",
        "EVENTS_POTENTIAL/TRIGGERED/OBSOLETE/RESOLVED", "CONSEQUENCES_PENDING",
    ],
}

PLAYER_SAFE = {
    "mission": "RECONNOITER_CONVOY_DETERMINE_PROGETTO_NERO_PREVENT_TRANSFER_IF_POSSIBLE",
    "bcra": {
        "name": "Romain Persy", "age": 33, "autonomous": True,
        "consequence_scope": ["WOUNDS", "SAN", "CAPTURE", "SEPARATION", "DEATH"],
        "visible_kit": ["ENFIELD_NO2_MKI_38", "24_ROUNDS", "KNIFE", "2L_CANTEEN", "2_DAY_RATIONS", "SMALL_KIT", "NOTEBOOK", "COMPASS", "BINOCULARS"],
        "radio_only_if_assigned": True,
    },
    "vehicle": {"id": "FORD_FORDOR_C11ADF_DESERT", "status": "OPERATIONAL", "fuel": "FULL_TANK_PLUS_TWO_20L_JERRICANS"},
    "shared": {"water_liters_by_player_count": {1: 32, 2: 48, 3: 64, 4: 80}, "team_radio_batteries": 2},
    "arming_policy": "NO_AUTOMATIC_CIVIL_ARMING_ROLE_AND_SKILL_REQUIRED",
    "captured_weapon_policy": "MUST_BE_OBTAINED_IN_PLAY",
    "knowledge_policy": "INDIVIDUAL_UNLESS_OBSERVED_TOGETHER_TRANSMITTED_OR_LEGITIMATELY_DEDUCED",
    "interface_fields": ["HP", "SAN", "MP", "LUCK", "WOUNDS_CONDITIONS", "OWNED_INVENTORY", "KNOWN_INFORMATION"],
    "time_policy": "NO_RHYTHM_ACCELERATION_OR_SLOWDOWN",
}


def graph_candidate_status() -> dict:
    return {
        "status": STATUS,
        "module_id": MODULE_ID,
        "scenario_id": SCENARIO_ID,
        "exact_keeper_sha256": CANONICAL_KEEPER_SHA256,
        "exact_player_sha256": CANONICAL_PLAYER_SHA256,
        "executable": False,
        "authority_promoted": False,
    }


def structural_graph() -> dict:
    return copy.deepcopy(GRAPH)


def player_projection_template(player_count: int) -> dict:
    if not isinstance(player_count, int) or isinstance(player_count, bool) or not 1 <= player_count <= 4:
        return {"status": "BLOCKED", "code": "PLAYER_COUNT_OUT_OF_RANGE"}
    out = copy.deepcopy(PLAYER_SAFE)
    out.update({
        "status": "PLAYER_PROJECTION_TEMPLATE_READY",
        "scenario_id": SCENARIO_ID,
        "player_count": player_count,
        "water_liters": GRAPH["shared_resources"]["water_liters_by_player_count"][player_count],
        "guardian_truth_exposed": False,
        "future_events_exposed": False,
        "source_hashes_exposed": False,
        "canonical_graph_exposed": False,
    })
    return out


def initial_state_candidate(player_count: int) -> dict:
    proj = player_projection_template(player_count)
    if proj.get("status") == "BLOCKED":
        return proj
    characters = {}
    for index in range(1, player_count + 1):
        cid = f"PC{index}"
        characters[cid] = {
            "position": "BIR_HALIM",
            "exposure": 0,
            "inventory": [],
            "knowledge": [],
        }
    return {
        "status": "INITIAL_STATE_CANDIDATE_READY_NON_EXECUTABLE",
        "scenario_id": SCENARIO_ID,
        "world_time": "J1_0800",
        "party_split": False,
        "characters": characters,
        "romain_persy": {"position": "BIR_HALIM", "autonomous": True},
        "shared_resources": {
            "water_liters": proj["water_liters"],
            "fuel": GRAPH["shared_resources"]["fuel"],
            "team_radio_batteries": 2,
            "vehicle": GRAPH["shared_resources"]["vehicle"],
        },
        "shared_knowledge": [],
        "front": "RELATIVELY_STABLE",
        "events": {},
        "consequences_pending": [],
        "executable": False,
    }


def activate_canonical_graph() -> dict:
    if CANONICAL_KEEPER_SHA256 is None or CANONICAL_PLAYER_SHA256 is None:
        return {
            "status": "BLOCKED",
            "code": "EXACT_CANONICAL_HASH_ALLOWLIST_UNMATERIALIZED",
            "scenario_id": SCENARIO_ID,
            "zero_mutation": True,
        }
    if CANONICAL_KEEPER_SHA256 in V15_HASHES or CANONICAL_PLAYER_SHA256 in V15_HASHES:
        return {"status": "BLOCKED", "code": "SUPERSEDED_HASH_REUSE_FORBIDDEN", "zero_mutation": True}
    return {"status": "BLOCKED", "code": "ACTIVATION_NOT_IMPLEMENTED_BEFORE_PRIVATE_IDENTITY_GATE", "zero_mutation": True}
