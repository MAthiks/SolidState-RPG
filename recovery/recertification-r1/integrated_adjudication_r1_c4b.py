from __future__ import annotations

import copy
import hashlib
import hmac

from integrated_adjudication_r1_c4 import SourceBackedRuntimeR1C4
from scenario_router_r1_c4 import player_projection
from scenario_router_r1_c4b import ROUTER_ID, resolve_route_c4b
from runtime_r1.core import CHECKPOINT_FLOOR, canon

INTEGRATION_ID = "SOLIDSTATE_RECOVERY_RUNTIME_R1_C4B_V1"
SAVE_SCHEMA = "SOLIDSTATE_RECOVERY_SAVE_R1_C4B_V1"
AUTHORITY_ID = "RECOVERY_RECERTIFICATION_R1_C4B"


class SourceBackedRuntimeR1C4B(SourceBackedRuntimeR1C4):
    def scenario_preflight(self, scenario_key: str):
        return resolve_route_c4b(scenario_key, self.source_paths)

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
            routed = resolve_route_c4b(scenario.get("scenario_key", ""), self.source_paths)
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
            return {
                "status": "RESTORED_STRICT",
                "commit_sequence": state["commit_sequence"],
                "scenario_id": state["scenario_runtime"]["scenario_id"],
            }
        except Exception as error:
            return {"status": "FAIL_CLOSED", "code": str(error), "before": before, "after": self.state_digest()}
