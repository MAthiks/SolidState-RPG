from __future__ import annotations

import copy

EXPOSURE_INCREMENTS = {
    "BRIEF_ANOMALY": 1,
    "PROLONGED": 2,
    "DIRECT_CONTACT": 3,
}
EXPOSURE_THRESHOLDS = (2, 4, 6)
SANITY_LOSSES = {
    "SHADOW_MOVES_AFTER_STOP": {"success": "0", "failure": "1D3"},
    "SHADOW_PRECEDES_GESTURE": {"success": "1", "failure": "1D4"},
    "DISCOVER_SHADOW_GATE": {"success": "1", "failure": "1D6"},
    "SEE_CONSTRAINED_HUMAN": {"success": "1D2", "failure": "1D8"},
    "OBSERVE_ACTIVE_CHAMBER": {"success": "1D3", "failure": "1D10"},
    "UNDERSTAND_PROPAGATION_POTENTIAL": {"success": "1D4", "failure": "1D10"},
}
DIE_MAX = {"1D2": 2, "1D3": 3, "1D4": 4, "1D6": 6, "1D8": 8, "1D10": 10}


def _owned_row(state: dict, actor_player_id: str, character_id: str) -> tuple[dict | None, dict | None]:
    controlled = state.get("control_map", {}).get(actor_player_id)
    if controlled != character_id:
        return None, {"status": "BLOCKED", "code": "ACTOR_CHARACTER_MISMATCH"}
    row = state.get("party", {}).get(actor_player_id)
    if not row or row.get("character_id") != character_id:
        return None, {"status": "BLOCKED", "code": "CHARACTER_STATE_NOT_FOUND"}
    return row, None


def _exposure_state(row: dict) -> dict:
    return row.setdefault("exposure_state", {
        "exposure": 0,
        "manifestation_failures": 0,
        "delayed_thresholds": [],
        "resolved_thresholds": [],
    })


def crossed_thresholds(old: int, new: int) -> list[int]:
    return [threshold for threshold in EXPOSURE_THRESHOLDS if old < threshold <= new]


def apply_exposure(
    state: dict,
    *,
    actor_player_id: str,
    character_id: str,
    exposure_kind: str,
    threshold_outcomes: dict[int, bool] | None = None,
) -> dict:
    row, error = _owned_row(state, actor_player_id, character_id)
    if error:
        return error
    increment = EXPOSURE_INCREMENTS.get(exposure_kind)
    if increment is None:
        return {"status": "BLOCKED", "code": "EXPOSURE_KIND_UNKNOWN"}
    current = _exposure_state(row)
    old = int(current["exposure"])
    new = min(6, old + increment)
    thresholds = crossed_thresholds(old, new)
    outcomes = threshold_outcomes or {}
    if thresholds and set(outcomes) != set(thresholds):
        return {
            "status": "BLOCKED",
            "code": "POW_THRESHOLD_OUTCOME_REQUIRED",
            "thresholds": thresholds,
        }
    snapshot = copy.deepcopy(current)
    current["exposure"] = new
    for threshold in thresholds:
        success = outcomes[threshold]
        if not isinstance(success, bool):
            current.clear(); current.update(snapshot)
            return {"status": "BLOCKED", "code": "POW_THRESHOLD_OUTCOME_INVALID", "threshold": threshold}
        current["resolved_thresholds"].append({"threshold": threshold, "success": success})
        if success:
            current["delayed_thresholds"].append(threshold)
        else:
            current["manifestation_failures"] += 1
    return {
        "status": "COMMITTED",
        "character_id": character_id,
        "old_exposure": old,
        "new_exposure": new,
        "thresholds_crossed": thresholds,
        "manifestation_failures": current["manifestation_failures"],
        "suspense_triggered_stage": False,
    }


def _loss_value(expr: str, recorded_loss: int | None) -> tuple[int | None, str | None]:
    if expr == "0":
        if recorded_loss is not None:
            return None, "SAN_RANDOM_LOSS_FORBIDDEN_FOR_FIXED_VALUE"
        return 0, None
    if expr == "1":
        if recorded_loss is not None:
            return None, "SAN_RANDOM_LOSS_FORBIDDEN_FOR_FIXED_VALUE"
        return 1, None
    maximum = DIE_MAX.get(expr)
    if maximum is None:
        return None, "SAN_EXPRESSION_UNKNOWN"
    if not isinstance(recorded_loss, int) or not 1 <= recorded_loss <= maximum:
        return None, "SAN_RECORDED_LOSS_REQUIRED"
    return recorded_loss, None


def apply_sanity_experience(
    state: dict,
    *,
    actor_player_id: str,
    character_id: str,
    experience_id: str,
    san_check_success: bool,
    recorded_loss: int | None = None,
    replay: bool = False,
    directly_exposed: bool = True,
) -> dict:
    row, error = _owned_row(state, actor_player_id, character_id)
    if error:
        return error
    record = SANITY_LOSSES.get(experience_id)
    if record is None:
        return {"status": "BLOCKED", "code": "SAN_EXPERIENCE_UNKNOWN"}
    if not directly_exposed:
        return {"status": "BLOCKED", "code": "SAN_DIRECT_EXPOSURE_REQUIRED", "zero_mutation": True}
    if not isinstance(san_check_success, bool):
        return {"status": "BLOCKED", "code": "SAN_CHECK_OUTCOME_REQUIRED"}
    current_san = row.setdefault("stats", {}).get("SAN")
    if not isinstance(current_san, int) or current_san < 0:
        return {"status": "BLOCKED", "code": "SAN_CURRENT_VALUE_REQUIRED"}
    expr = record["success" if san_check_success else "failure"]
    loss, loss_error = _loss_value(expr, recorded_loss)
    if loss_error:
        return {"status": "BLOCKED", "code": loss_error, "expression": expr}
    new_san = max(0, current_san - int(loss))
    row["stats"]["SAN"] = new_san
    journal = state.setdefault("scenario_san_journal", [])
    # Persisted provenance is canonical and replay-stable. Whether the reducer is
    # currently verifying replay is returned separately and never changes saved state.
    journal.append({
        "player_id": actor_player_id,
        "character_id": character_id,
        "experience_id": experience_id,
        "directly_exposed": True,
        "san_check_success": san_check_success,
        "loss_expression": expr,
        "recorded_loss": recorded_loss,
        "loss": loss,
        "old_san": current_san,
        "new_san": new_san,
        "provenance": "RECORDED_INPUT",
    })
    return {
        "status": "COMMITTED",
        "old_san": current_san,
        "new_san": new_san,
        "loss": loss,
        "loss_expression": expr,
        "provenance": "RECORDED_INPUT",
        "execution_mode": "REPLAY_VERIFICATION" if replay else "LIVE_COMMIT",
    }
