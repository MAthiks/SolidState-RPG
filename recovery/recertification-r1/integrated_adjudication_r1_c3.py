from __future__ import annotations

import copy
import hashlib
import hmac

from integrated_adjudication_r1_c2 import (
    SourceBackedRuntimeR1C2,
    INTEGRATION_ID as C2_ID,
    MECHANIC_SOURCE,
    verify_source,
)
from runtime_r1.core import CHECKPOINT_FLOOR, canon, sha
from rules_r1.core_rules import sanity_transition

INTEGRATION_ID = "SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_V1"
SAVE_SCHEMA = "SOLIDSTATE_RECOVERY_SAVE_R1_C3_V1"
AUTHORITY_ID = "RECOVERY_RECERTIFICATION_R1_C3"
ALLOWED_STATS = {"HP", "SAN", "MP", "Luck"}
_GLOBAL_SOURCE_CACHE = {}
_GLOBAL_RULES_CACHE = {}


class SourceBackedRuntimeR1C3(SourceBackedRuntimeR1C2):
    """C3 adds generic, actor-bound, replayable mechanical stat deltas."""

    def __init__(self, db_path, rules_zip, source_paths, secret=b"recovery-r1-test-secret"):
        super().__init__(db_path, rules_zip, source_paths, secret)
        self._source_identity_cache = _GLOBAL_SOURCE_CACHE
        self._rules_identity_cache = _GLOBAL_RULES_CACHE

    @staticmethod
    def _file_fingerprint(path):
        from pathlib import Path
        p = Path(path)
        if not p.is_file():
            return None
        st = p.stat()
        return (str(p.resolve()), st.st_size, st.st_mtime_ns)

    def _rules_identity(self):
        fp = self._file_fingerprint(self.rules_zip)
        cached = self._rules_identity_cache.get(fp) if fp is not None else None
        if cached:
            return copy.deepcopy(cached)
        result = super()._rules_identity()
        if result.get("status") == "VERIFIED":
            self._rules_identity_cache[fp] = copy.deepcopy(result)
        return result

    def _verified_source(self, source_id):
        path = self.source_paths.get(source_id, "")
        fp = self._file_fingerprint(path)
        key = (source_id, fp)
        cached = self._source_identity_cache.get(key)
        if cached:
            return copy.deepcopy(cached)
        result = verify_source(source_id, path)
        if result.get("status") == "VERIFIED":
            self._source_identity_cache[key] = copy.deepcopy(result)
        return result

    def _preflight(self, mechanic, scenario_sources=()):
        rules = self._rules_identity()
        if rules["status"] != "VERIFIED":
            return {"status": "BLOCKED", "code": rules["code"], "rules": rules}
        rule_source = MECHANIC_SOURCE.get(mechanic)
        if rule_source is None:
            return {"status": "BLOCKED", "code": "MECHANIC_UNMATERIALIZED", "mechanic": mechanic}
        required = [rule_source] + list(scenario_sources)
        verified = []
        for source_id in required:
            result = self._verified_source(source_id)
            if result["status"] != "VERIFIED":
                return {
                    "status": "BLOCKED",
                    "code": "SOURCE_PREFLIGHT_FAILED",
                    "failed_source": source_id,
                    "source_result": result,
                    "rules": rules,
                }
            verified.append({"source_id": source_id, "sha256": result["sha256"], "role": result["role"]})
        return {"status": "VERIFIED", "rules": rules, "sources": verified}

    @staticmethod
    def _stat_bounds(state, character_id, stat):
        initial = state["initial_characters"][character_id].get("stats", {}).get(stat)
        if stat == "HP":
            return 0, initial if isinstance(initial, (int, float)) else None
        if stat == "SAN":
            return 0, 99
        if stat == "MP":
            return 0, initial if isinstance(initial, (int, float)) else None
        if stat == "Luck":
            return 0, 99
        return None, None

    @classmethod
    def _validate_and_apply_deltas(cls, state, character_id, deltas, *, mutate):
        if not isinstance(deltas, list):
            return {"status": "BLOCKED", "code": "MECHANICAL_DELTAS_LIST_REQUIRED"}
        target = state["characters"].get(character_id)
        if not isinstance(target, dict):
            return {"status": "BLOCKED", "code": "CHARACTER_NOT_FOUND"}
        stats = target.setdefault("stats", {})
        normalized = []
        for index, item in enumerate(deltas):
            if not isinstance(item, dict):
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_INVALID", "index": index}
            if set(item) - {"stat", "op", "value", "before", "after"}:
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_SHAPE_INVALID", "index": index}
            stat = item.get("stat")
            op = item.get("op", "ADD")
            value = item.get("value")
            if stat not in ALLOWED_STATS:
                return {"status": "BLOCKED", "code": "MECHANICAL_STAT_UNMATERIALIZED", "stat": stat}
            if op != "ADD":
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_OP_UNSUPPORTED", "op": op}
            if not isinstance(value, int) or isinstance(value, bool):
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_VALUE_INVALID", "stat": stat}
            current = stats.get(stat)
            if not isinstance(current, (int, float)) or isinstance(current, bool):
                return {"status": "BLOCKED", "code": "MECHANICAL_STAT_MISSING", "stat": stat}
            after = current + value
            minimum, maximum = cls._stat_bounds(state, character_id, stat)
            if minimum is not None and after < minimum:
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_BELOW_MINIMUM", "stat": stat, "after": after}
            if maximum is not None and after > maximum:
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_ABOVE_MAXIMUM", "stat": stat, "after": after}
            if "before" in item and item["before"] != current:
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_BEFORE_MISMATCH", "stat": stat}
            if "after" in item and item["after"] != after:
                return {"status": "BLOCKED", "code": "MECHANICAL_DELTA_AFTER_MISMATCH", "stat": stat}
            normalized.append({"stat": stat, "op": "ADD", "value": value, "before": current, "after": after})
            if mutate:
                stats[stat] = after
        return {"status": "PASS", "deltas": normalized}

    def append_mechanical_event(self, *, player_id, character_id, action_id, roll, deltas, mechanic, event_id=None, provenance=None):
        state = self._get_state()
        before = sha(state)
        if state is None:
            return {"status": "FAIL_CLOSED", "code": "SESSION_NOT_READY", "before": before, "after": before}
        if state["interface_session"]["control_map"].get(player_id) != character_id:
            return {"status": "FAIL_CLOSED", "code": "ACTOR_CONTROL_MISMATCH", "before": before, "after": before}
        if not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
            return {"status": "FAIL_CLOSED", "code": "ROLL_INVALID", "before": before, "after": before}
        eid = event_id or f"{state['session_id']}:{state['commit_sequence'] + 1}:{player_id}"
        if any(row["event"].get("event_id") == eid for row in state["journal"]):
            return {"status": "FAIL_CLOSED", "code": "DUPLICATE_EVENT_ID", "before": before, "after": before}
        candidate = copy.deepcopy(state)
        checked = self._validate_and_apply_deltas(candidate, character_id, deltas, mutate=True)
        if checked["status"] != "PASS":
            return {"status": "FAIL_CLOSED", "code": checked["code"], "detail": checked, "before": before, "after": before}
        event = {
            "event_id": eid,
            "action_id": str(action_id),
            "payload": {
                "player_id": player_id,
                "character_id": character_id,
                "roll": roll,
                "delta": 0,
                "mechanic": str(mechanic),
                "mechanical_deltas": checked["deltas"],
                "provenance": copy.deepcopy(provenance or {}),
            },
        }
        previous_hash = candidate["journal"][-1]["event_hash"] if candidate["journal"] else "GENESIS"
        row = {"event": event, "previous_hash": previous_hash, "event_hash": self._event_hash(previous_hash, event)}
        candidate["journal"].append(row)
        candidate["commit_sequence"] += 1
        self._commit_state(candidate)
        return {"status": "COMMIT", "event_id": eid, "commit_sequence": candidate["commit_sequence"], "event_hash": row["event_hash"], "state_delta": checked["deltas"]}

    @classmethod
    def verify_journal(cls, state, expected_actor_trace=None):
        previous_hash = "GENESIS"
        seen = set()
        trace = []
        replay_state = copy.deepcopy(state)
        replay_state["characters"] = copy.deepcopy(state["initial_characters"])
        control_map = state["interface_session"]["control_map"]
        for index, row in enumerate(state.get("journal", [])):
            event = row.get("event", {})
            event_id = event.get("event_id")
            payload = event.get("payload", {})
            if not event_id or event_id in seen:
                return {"status": "REPLAY_DIVERGENCE", "reason": "DUPLICATE_OR_MISSING_EVENT_ID", "index": index}
            seen.add(event_id)
            if row.get("previous_hash") != previous_hash or row.get("event_hash") != cls._event_hash(previous_hash, event):
                return {"status": "REPLAY_DIVERGENCE", "reason": "HASH_CHAIN_INVALID", "index": index}
            player_id = payload.get("player_id")
            character_id = payload.get("character_id")
            roll = payload.get("roll")
            if control_map.get(player_id) != character_id:
                return {"status": "REPLAY_DIVERGENCE", "reason": "ACTOR_CONTROL_MISMATCH", "index": index}
            if not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
                return {"status": "REPLAY_DIVERGENCE", "reason": "ROLL_INVALID", "index": index}
            mechanical = payload.get("mechanical_deltas")
            if mechanical is not None:
                checked = cls._validate_and_apply_deltas(replay_state, character_id, mechanical, mutate=True)
                if checked["status"] != "PASS":
                    return {"status": "REPLAY_DIVERGENCE", "reason": checked["code"], "index": index, "detail": checked}
            else:
                delta = payload.get("delta", 0)
                if not isinstance(delta, int) or isinstance(delta, bool):
                    return {"status": "REPLAY_DIVERGENCE", "reason": "DELTA_INVALID", "index": index}
                if delta:
                    checked = cls._validate_and_apply_deltas(replay_state, character_id, [{"stat": "HP", "op": "ADD", "value": delta}], mutate=True)
                    if checked["status"] != "PASS":
                        return {"status": "REPLAY_DIVERGENCE", "reason": checked["code"], "index": index, "detail": checked}
            trace.append({"event_id": event_id, "action_id": event.get("action_id"), "player_id": player_id, "character_id": character_id, "roll": roll, "event_hash": row.get("event_hash")})
            previous_hash = row["event_hash"]
        if replay_state["characters"] != state["characters"]:
            return {"status": "REPLAY_DIVERGENCE", "reason": "CANONICAL_STATE_MISMATCH"}
        if expected_actor_trace is not None and trace != expected_actor_trace:
            return {"status": "REPLAY_DIVERGENCE", "reason": "ACTOR_TRACE_MISMATCH", "actual": trace, "expected": expected_actor_trace}
        return {"status": "REPLAY_MATCH", "events": len(trace), "actor_trace": trace}

    def _bundle_payload_c3(self):
        return {"schema": SAVE_SCHEMA, "checkpoint_floor": CHECKPOINT_FLOOR, "authority_id": AUTHORITY_ID, "integration_id": INTEGRATION_ID, "state": self._get_state()}

    def save_bundle(self):
        payload = self._bundle_payload_c3()
        raw = canon(payload).encode("utf-8")
        return {"payload": payload, "auth": {"algorithm": "HMAC-SHA256", "payload_sha256": hashlib.sha256(raw).hexdigest(), "hmac_sha256": hmac.new(self.secret, raw, hashlib.sha256).hexdigest()}}

    def restore_bundle(self, bundle):
        before = self.state_digest()
        try:
            if set(bundle) != {"payload", "auth"}:
                raise ValueError("BUNDLE_SHAPE_INVALID")
            payload = bundle["payload"]
            auth = bundle["auth"]
            raw = canon(payload).encode("utf-8")
            if payload.get("schema") != SAVE_SCHEMA or payload.get("checkpoint_floor") != CHECKPOINT_FLOOR or payload.get("authority_id") != AUTHORITY_ID or payload.get("integration_id") != INTEGRATION_ID:
                raise ValueError("AUTHORITY_FLOOR_INVALID")
            if hashlib.sha256(raw).hexdigest() != auth.get("payload_sha256"):
                raise ValueError("PAYLOAD_HASH_MISMATCH")
            expected = hmac.new(self.secret, raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, str(auth.get("hmac_sha256", ""))):
                raise ValueError("SAVE_AUTHENTICATION_FAILED")
            state = copy.deepcopy(payload["state"])
            if state.get("authority_floor") != CHECKPOINT_FLOOR:
                raise ValueError("STATE_AUTHORITY_FLOOR_INVALID")
            if self.verify_journal(state).get("status") != "REPLAY_MATCH":
                raise ValueError("STRICT_REPLAY_INVALID")
            self._commit_state(state)
            return {"status": "RESTORED_STRICT", "commit_sequence": state["commit_sequence"]}
        except Exception as error:
            return {"status": "FAIL_CLOSED", "code": str(error), "before": before, "after": self.state_digest()}

    def adjudicate_sanity_loss(self, *, player_id, character_id, loss, sanity_start_of_day, daily_loss_before=0, scenario_sources=(), san_roll, event_id=None, loss_provenance="recorded scenario/rule loss"):
        before = self.state_digest()
        if not self._actor_ok(player_id, character_id):
            return {"status": "FAIL_CLOSED", "code": "ACTOR_CONTROL_MISMATCH", "before": before, "after": before}
        preflight = self._preflight("SANITY_LOSS", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {"status": "FAIL_CLOSED", "code": preflight["code"], "preflight": preflight, "before": before, "after": before}
        if not isinstance(san_roll, int) or isinstance(san_roll, bool) or not 1 <= san_roll <= 100:
            return {"status": "FAIL_CLOSED", "code": "ROLL_INVALID", "before": before, "after": before}
        state = self.state()
        current_san = state["characters"][character_id].get("stats", {}).get("SAN")
        if not isinstance(current_san, int) or isinstance(current_san, bool):
            return {"status": "FAIL_CLOSED", "code": "MECHANICAL_SAN_MISSING", "before": before, "after": before}
        outcome = sanity_transition(current_san=current_san, sanity_start_of_day=sanity_start_of_day, loss=loss, daily_loss_before=daily_loss_before)
        delta = int(outcome["SAN"] - current_san)
        commit = self.append_mechanical_event(
            player_id=player_id,
            character_id=character_id,
            action_id="SANITY:LOSS",
            roll=san_roll,
            deltas=[{"stat": "SAN", "op": "ADD", "value": delta}],
            mechanic="SANITY_LOSS",
            event_id=event_id,
            provenance={"loss": loss, "loss_provenance": loss_provenance, "sanity_start_of_day": sanity_start_of_day, "daily_loss_before": daily_loss_before, "rules_integration_parent": C2_ID},
        )
        if commit["status"] != "COMMIT":
            return {"status": "FAIL_CLOSED", "code": commit.get("code", "COMMIT_FAILED"), "before": before, "after": self.state_digest()}
        return {
            "status": "COMMIT",
            "integration_id": INTEGRATION_ID,
            "actor": {"player_id": player_id, "character_id": character_id},
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "dice": {"expression": "1d100", "result": san_roll, "provenance": "recorded SAN check / no reroll on replay"},
            "outcome": outcome,
            "state_delta": {f"characters.{character_id}.stats.SAN": {"op": "add", "value": delta}},
            "commit_sequence": commit["commit_sequence"],
            "event_hash": commit["event_hash"],
        }
