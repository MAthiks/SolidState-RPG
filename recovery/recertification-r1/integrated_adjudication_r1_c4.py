from __future__ import annotations

import copy
import hashlib
import hmac

from integrated_adjudication_r1_c3 import SourceBackedRuntimeR1C3
from registry_r1_c4 import (
    REGISTRY_ID,
    resolve_equipment,
    resolve_occupation,
    resolve_skill,
    resolve_weapon,
)
from scenario_router_r1_c4 import ROUTER_ID, player_projection, resolve_route
from source_adapter_r1 import verify_source
from runtime_r1.core import CHECKPOINT_FLOOR, canon

INTEGRATION_ID = "SOLIDSTATE_RECOVERY_RUNTIME_R1_C4_V1"
SAVE_SCHEMA = "SOLIDSTATE_RECOVERY_SAVE_R1_C4_V1"
AUTHORITY_ID = "RECOVERY_RECERTIFICATION_R1_C4"


class SourceBackedRuntimeR1C4(SourceBackedRuntimeR1C3):
    def registry_resolve(self, registry: str, record_id: str, **kwargs):
        registry = str(registry).upper()
        if registry == "OCCUPATION":
            return resolve_occupation(record_id, characteristics=kwargs.get("characteristics"))
        if registry == "SKILL":
            return resolve_skill(record_id, dex=kwargs.get("dex"))
        if registry == "EQUIPMENT":
            return resolve_equipment(record_id)
        if registry == "WEAPON":
            return resolve_weapon(record_id)
        return {"status": "BLOCKED", "code": "REGISTRY_UNKNOWN", "registry": registry}

    def scenario_preflight(self, scenario_key: str):
        return resolve_route(scenario_key, self.source_paths)

    def new_canonical_session(self, scenario_key, players, session_id="R1-C4-SESSION"):
        before = self.state_digest()
        rules = self._rules_identity()
        if rules.get("status") != "VERIFIED":
            return {"status": "FAIL_CLOSED", "code": rules.get("code", "RULES_PACKAGE_INVALID"), "before": before, "after": before}
        for source_id in ("COC7_KEEPER", "COC7_INVESTIGATOR"):
            source = verify_source(source_id, self.source_paths.get(source_id, ""))
            if source.get("status") != "VERIFIED":
                return {"status": "FAIL_CLOSED", "code": "RULEBOOK_SOURCE_PREFLIGHT_FAILED", "failed_source": source_id, "source_result": source, "before": before, "after": before}
        routed = self.scenario_preflight(scenario_key)
        if routed.get("status") != "ROUTE_READY":
            return {
                "status": "FAIL_CLOSED",
                "code": routed.get("code", "SCENARIO_ROUTE_NOT_READY"),
                "route": routed,
                "before": before,
                "after": before,
            }
        ready = self.new_session(players, session_id)
        if ready.get("status") != "SESSION_READY":
            return {"status": "FAIL_CLOSED", "code": ready.get("code", "SESSION_INIT_FAILED")}
        state = self._get_state()
        state["scenario_runtime"] = {
            "router_id": ROUTER_ID,
            "registry_id": REGISTRY_ID,
            "scenario_key": routed["route"]["scenario_key"],
            "scenario_id": routed["route"]["scenario_id"],
            "title": routed["route"]["title"],
            "source_ids": list(routed["route"]["source_ids"]),
            "source_hashes": {row["source_id"]: row["sha256"] for row in routed["sources"]},
            "release_checkpoint": routed["route"]["release_checkpoint"],
            "release_class": routed["route"]["release_class"],
            "canonical_path": copy.deepcopy(routed["route"].get("canonical_path")),
        }
        self._commit_state(state)
        return {
            "status": "SCENARIO_SESSION_READY",
            "integration_id": INTEGRATION_ID,
            "scenario": player_projection(routed)["scenario"],
            "players": ready["players"],
            "control_map": ready["control_map"],
        }

    def player_scenario_projection(self, player_id):
        state = self._get_state()
        if state is None:
            return {"status": "BLOCKED", "code": "SESSION_NOT_READY"}
        if player_id not in state.get("party", {}):
            return {"status": "BLOCKED", "code": "PLAYER_NOT_IN_SESSION"}
        scenario = state.get("scenario_runtime")
        if not scenario:
            return {"status": "BLOCKED", "code": "SCENARIO_NOT_BOUND"}
        return {
            "status": "READY",
            "scenario": {
                "scenario_key": scenario["scenario_key"],
                "scenario_id": scenario["scenario_id"],
                "title": scenario["title"],
            },
        }

    def save_bundle(self):
        payload = {
            "schema": SAVE_SCHEMA,
            "checkpoint_floor": CHECKPOINT_FLOOR,
            "authority_id": AUTHORITY_ID,
            "integration_id": INTEGRATION_ID,
            "state": self._get_state(),
        }
        raw = canon(payload).encode("utf-8")
        return {
            "payload": payload,
            "auth": {
                "algorithm": "HMAC-SHA256",
                "payload_sha256": hashlib.sha256(raw).hexdigest(),
                "hmac_sha256": hmac.new(self.secret, raw, hashlib.sha256).hexdigest(),
            },
        }

    def restore_bundle(self, bundle):
        before = self.state_digest()
        try:
            if set(bundle) != {"payload", "auth"}:
                raise ValueError("BUNDLE_SHAPE_INVALID")
            payload = bundle["payload"]
            auth = bundle["auth"]
            raw = canon(payload).encode("utf-8")
            if (
                payload.get("schema") != SAVE_SCHEMA
                or payload.get("checkpoint_floor") != CHECKPOINT_FLOOR
                or payload.get("authority_id") != AUTHORITY_ID
                or payload.get("integration_id") != INTEGRATION_ID
            ):
                raise ValueError("AUTHORITY_FLOOR_INVALID")
            if hashlib.sha256(raw).hexdigest() != auth.get("payload_sha256"):
                raise ValueError("PAYLOAD_HASH_MISMATCH")
            expected = hmac.new(self.secret, raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, str(auth.get("hmac_sha256", ""))):
                raise ValueError("SAVE_AUTHENTICATION_FAILED")
            state = copy.deepcopy(payload["state"])
            if state.get("authority_floor") != CHECKPOINT_FLOOR:
                raise ValueError("STATE_AUTHORITY_FLOOR_INVALID")
            scenario = state.get("scenario_runtime")
            if not scenario:
                raise ValueError("SCENARIO_BINDING_MISSING")
            routed = resolve_route(scenario.get("scenario_key", ""), self.source_paths)
            if routed.get("status") != "ROUTE_READY":
                raise ValueError("SCENARIO_ROUTE_REVALIDATION_FAILED")
            canonical = routed["route"]
            expected_hashes = {row["source_id"]: row["sha256"] for row in routed["sources"]}
            if (
                scenario.get("scenario_id") != canonical.get("scenario_id")
                or scenario.get("source_ids") != list(canonical.get("source_ids", ()))
                or scenario.get("source_hashes") != expected_hashes
                or scenario.get("canonical_path") != canonical.get("canonical_path")
            ):
                raise ValueError("SCENARIO_BINDING_MISMATCH")
            if self.verify_journal(state).get("status") != "REPLAY_MATCH":
                raise ValueError("STRICT_REPLAY_INVALID")
            self._commit_state(state)
            return {"status": "RESTORED_STRICT", "commit_sequence": state["commit_sequence"], "scenario_id": state["scenario_runtime"]["scenario_id"]}
        except Exception as error:
            return {"status": "FAIL_CLOSED", "code": str(error), "before": before, "after": self.state_digest()}
