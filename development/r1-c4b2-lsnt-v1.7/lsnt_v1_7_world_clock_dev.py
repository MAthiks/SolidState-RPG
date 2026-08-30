from __future__ import annotations

import copy
import re
from dataclasses import dataclass

CLOCK_ORIGIN_DAY = 1
CLOCK_START = "J1 08:00"
FRONT_STATES = {"AXIS", "STATUS_QUO", "ALLIES"}


@dataclass(frozen=True)
class WorldEvent:
    event_id: str
    at: str
    condition_fact: str | None = None
    possible_only: bool = False


WORLD_EVENTS = (
    WorldEvent("MISSION_START", "J1 08:00"),
    WorldEvent("VOSS_INTEREST_IF_TRACES", "J1 17:00", "TRACES_LEFT"),
    WorldEvent("FIRST_NOTABLE_EXPANSION", "J1 23:40"),
    WorldEvent("AXIS_PATROL_TO_CONVOY", "J2 06:00"),
    WorldEvent("OASIS_MAY_CHANGE_BY_FRONT", "J2 14:00", possible_only=True),
    WorldEvent("SHADOW_GATE_ACTIVITY_INCREASES", "J2 23:40"),
    WorldEvent("VOSS_PREPARES_TRANSFER", "J3 09:00"),
    WorldEvent("POSSIBLE_BOMBARDMENT", "J3 16:00", possible_only=True),
    WorldEvent("EFFECT_ZONE_EXPANDS", "J3 23:40"),
    WorldEvent("TRANSFER_DEPARTS_IF_VOSS_CONTROLS", "J4 05:10", "VOSS_CONTROLS_FRAGMENT"),
    WorldEvent("CRITICAL_ZENITH_IF_DEVICE_OPEN", "J4 12:00", "DEVICE_OPEN"),
)

TRAVEL = {
    "BIR_HALIM_TO_CONVOY": {"from": "LSNT_START_BIR_HALIM", "to": "LSNT_NODE_CONVOY", "km": 35, "normal_min": 50, "normal_max": 70},
    "CONVOY_TO_SIDI_MARUT": {"from": "LSNT_NODE_CONVOY", "to": "LSNT_NODE_SIDI_MARUT", "km": 28, "normal_min": 45, "normal_max": 60},
    "SIDI_MARUT_TO_FORTS": {"from": "LSNT_NODE_SIDI_MARUT", "to": "LSNT_NODE_FORT_17B", "km": 22, "normal_min": 35, "normal_max": 50},
    "FORTS_TO_WADIS": {"from": "LSNT_NODE_FORT_17B", "to": "LSNT_NODE_WADI", "km": 30, "normal_min": 60, "normal_max": 90},
    "WADIS_TO_RUINS": {"from": "LSNT_NODE_WADI", "to": "LSNT_NODE_QASR_IREM", "km": 18, "normal_min": 45, "normal_max": 75},
    "INTERIOR_TO_COASTAL_ROAD": {"from": "LSNT_TAG_INTERIOR", "to": "LSNT_NODE_ROUTE_COTIERE", "km": 55, "normal_min": 90, "normal_max": 150},
    "COASTAL_ROAD_TO_TMIMI": {"from": "LSNT_NODE_ROUTE_COTIERE", "to": "LSNT_NODE_AERODROME_TMIMI", "km": 40, "normal_min": 50, "normal_max": 80},
}

CAUSAL_TRAVEL_REASONS = {"TERRAIN", "BREAKDOWN", "COMBAT", "STORM", "DETOUR", "MILITARY_CONTROL"}


def parse_time(value: str) -> int:
    m = re.fullmatch(r"J([1-9][0-9]*) ([0-2][0-9]):([0-5][0-9])", str(value))
    if not m:
        raise ValueError("WORLD_TIME_FORMAT_INVALID")
    day, hour, minute = map(int, m.groups())
    if hour > 23:
        raise ValueError("WORLD_TIME_FORMAT_INVALID")
    return (day - CLOCK_ORIGIN_DAY) * 1440 + hour * 60 + minute


def format_time(total_minutes: int) -> str:
    if not isinstance(total_minutes, int) or total_minutes < 0:
        raise ValueError("WORLD_TIME_VALUE_INVALID")
    day_offset, minute_of_day = divmod(total_minutes, 1440)
    hour, minute = divmod(minute_of_day, 60)
    return f"J{day_offset + CLOCK_ORIGIN_DAY} {hour:02d}:{minute:02d}"


def ensure_event_state(state: dict) -> dict:
    events = state.setdefault("events", {})
    for key in ("potential", "triggered", "obsolete", "resolved"):
        events.setdefault(key, [])
    return events


def _record_once(events: dict, bucket: str, event_id: str, at: str, reason: str) -> None:
    for rows in events.values():
        if any(row.get("event_id") == event_id for row in rows):
            return
    events[bucket].append({"event_id": event_id, "at": at, "reason": reason})


def due_front_checks(start_minutes: int, end_minutes: int) -> list[str]:
    if end_minutes < start_minutes:
        raise ValueError("WORLD_TIME_REWIND_FORBIDDEN")
    out = []
    start_day = start_minutes // 1440 + 1
    end_day = end_minutes // 1440 + 1
    for day in range(start_day, end_day + 1):
        for hh in (6, 18):
            stamp = f"J{day} {hh:02d}:00"
            t = parse_time(stamp)
            if start_minutes < t <= end_minutes:
                out.append(stamp)
    return out


def advance_world_time(state: dict, target: str, *, facts: dict[str, bool | None] | None = None) -> dict:
    facts = facts or {}
    current = parse_time(state.get("world_time", CLOCK_START))
    end = parse_time(target)
    if end < current:
        return {"status": "BLOCKED", "code": "WORLD_TIME_REWIND_FORBIDDEN", "world_time": state.get("world_time")}
    events = ensure_event_state(state)
    for definition in WORLD_EVENTS:
        t = parse_time(definition.at)
        if not current < t <= end:
            continue
        if definition.possible_only:
            _record_once(events, "potential", definition.event_id, definition.at, "SOURCE_SAYS_POSSIBLE_CAUSAL_RESOLUTION_REQUIRED")
            continue
        if definition.condition_fact:
            value = facts.get(definition.condition_fact)
            if value is True:
                _record_once(events, "triggered", definition.event_id, definition.at, f"CONDITION_TRUE:{definition.condition_fact}")
            elif value is False:
                _record_once(events, "obsolete", definition.event_id, definition.at, f"CONDITION_FALSE:{definition.condition_fact}")
            else:
                _record_once(events, "potential", definition.event_id, definition.at, f"CONDITION_UNRESOLVED:{definition.condition_fact}")
            continue
        _record_once(events, "triggered", definition.event_id, definition.at, "UNCONDITIONAL_SOURCE_CLOCK")
    checks = due_front_checks(current, end)
    state["world_time"] = target
    return {"status": "ADVANCED", "from": format_time(current), "to": target, "front_checks_due": checks}


def resolve_front_check(
    state: dict,
    *,
    check_time: str,
    facts_result: str | None = None,
    recorded_roll: int | None = None,
    causal_modifiers: list[int] | None = None,
    replay: bool = False,
) -> dict:
    check_minutes = parse_time(check_time)
    if check_time.split(" ")[1] not in {"06:00", "18:00"}:
        return {"status": "BLOCKED", "code": "FRONT_CHECK_TIME_INVALID"}
    if check_minutes > parse_time(state.get("world_time", CLOCK_START)):
        return {"status": "BLOCKED", "code": "FRONT_CHECK_NOT_DUE"}
    front = state.setdefault("front", {"state": "RELATIVELY_STABLE", "last_check": None, "history": []})
    front.setdefault("history", [])
    if any(row.get("check_time") == check_time for row in front["history"]):
        return {"status": "BLOCKED", "code": "FRONT_CHECK_ALREADY_RESOLVED"}

    if facts_result is not None:
        if facts_result not in FRONT_STATES:
            return {"status": "BLOCKED", "code": "FRONT_FACT_RESULT_INVALID"}
        if recorded_roll is not None:
            return {"status": "BLOCKED", "code": "FRONT_ROLL_FORBIDDEN_WHEN_FACTS_DECIDE"}
        result = facts_result
        record = {"check_time": check_time, "mode": "FACTS", "result": result, "roll": None, "modifiers": []}
    else:
        if not isinstance(recorded_roll, int) or not 1 <= recorded_roll <= 6:
            return {"status": "BLOCKED", "code": "FRONT_RECORDED_1D6_REQUIRED"}
        modifiers = list(causal_modifiers or [])
        if any((not isinstance(v, int)) or v not in {-1, 0, 1} for v in modifiers):
            return {"status": "BLOCKED", "code": "FRONT_CAUSAL_MODIFIER_INVALID"}
        adjusted = recorded_roll + sum(modifiers)
        result = "AXIS" if adjusted <= 2 else "STATUS_QUO" if adjusted <= 4 else "ALLIES"
        record = {
            "check_time": check_time,
            "mode": "RECORDED_REPLAY" if replay else "RECORDED_LIVE_INPUT",
            "result": result,
            "roll": recorded_roll,
            "modifiers": modifiers,
            "adjusted": adjusted,
        }
    front["state"] = result
    front["last_check"] = check_time
    front["history"].append(record)
    return {"status": "RESOLVED", **copy.deepcopy(record)}


def apply_travel(
    state: dict,
    *,
    route_id: str,
    actual_minutes: int,
    causal_reason: str | None = None,
) -> dict:
    route = TRAVEL.get(route_id)
    if route is None:
        return {"status": "BLOCKED", "code": "TRAVEL_ROUTE_UNKNOWN"}
    if not isinstance(actual_minutes, int) or actual_minutes <= 0:
        return {"status": "BLOCKED", "code": "TRAVEL_DURATION_INVALID"}
    normal = route["normal_min"] <= actual_minutes <= route["normal_max"]
    if not normal:
        if causal_reason not in CAUSAL_TRAVEL_REASONS:
            return {"status": "BLOCKED", "code": "OUT_OF_RANGE_TRAVEL_REQUIRES_SOURCE_CAUSAL_REASON"}
    current = parse_time(state.get("world_time", CLOCK_START))
    target = format_time(current + actual_minutes)
    advanced = advance_world_time(state, target)
    if advanced["status"] != "ADVANCED":
        return advanced
    state.setdefault("travel_history", []).append({
        "route_id": route_id,
        "from": route["from"],
        "to": route["to"],
        "km": route["km"],
        "minutes": actual_minutes,
        "normal_range": [route["normal_min"], route["normal_max"]],
        "causal_reason": causal_reason,
    })
    return {"status": "TRAVEL_COMMITTED", "world_time": target, "front_checks_due": advanced["front_checks_due"]}
