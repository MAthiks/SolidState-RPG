import re
from collections import deque
from copy import deepcopy
from .generic_state_transitions import GenericStateTransition

_HEX64 = re.compile(r"[0-9a-f]{64}")

class StartCandidateEvidenceGate:
    REQUIRED = {
        "scene_id", "source_ref", "source_sha256", "partition",
        "availability", "explicit_source_language"
    }

    @classmethod
    def validate(cls, record):
        missing = cls.REQUIRED - set(record)
        if missing:
            return {"status": "BLOCKED", "code": "START_EVIDENCE_INCOMPLETE", "missing": sorted(missing)}
        if not record.get("explicit_source_language"):
            return {"status": "BLOCKED", "code": "START_NOT_EXPLICIT"}
        if record.get("partition") != "PLAYER_SAFE":
            return {"status": "BLOCKED", "code": "START_NOT_PLAYER_SAFE"}
        if record.get("availability") != "AT_ARRIVAL":
            return {"status": "BLOCKED", "code": "START_NOT_INITIAL_AVAILABLE"}
        if not _HEX64.fullmatch(str(record.get("source_sha256", ""))):
            return {"status": "BLOCKED", "code": "START_HASH_INVALID"}
        if not record.get("scene_id"):
            return {"status": "BLOCKED", "code": "START_SCENE_MISSING"}
        return {"status": "RESOLVED", "code": "DEFENSIBLE_START_CANDIDATE"}

class TerminalOutcomeEvidenceGate:
    REQUIRED = {
        "terminal_scene", "from_scene", "predicate", "effects",
        "action_source_ref", "action_source_sha256",
        "outcome_source_ref", "outcome_source_sha256",
        "partition", "explicit_source_language", "target_binding_count"
    }

    @classmethod
    def validate(cls, record):
        missing = cls.REQUIRED - set(record)
        if missing:
            return {"status": "BLOCKED", "code": "TERMINAL_EVIDENCE_INCOMPLETE", "missing": sorted(missing)}
        if not record.get("explicit_source_language"):
            return {"status": "BLOCKED", "code": "TERMINAL_NOT_EXPLICIT"}
        if record.get("partition") != "KEEPER":
            return {"status": "BLOCKED", "code": "TERMINAL_PARTITION_INVALID"}
        if record.get("target_binding_count") != 1:
            return {"status": "BLOCKED", "code": "TERMINAL_TARGET_NOT_UNIQUE"}
        for key in ("action_source_sha256", "outcome_source_sha256"):
            if not _HEX64.fullmatch(str(record.get(key, ""))):
                return {"status": "BLOCKED", "code": "TERMINAL_HASH_INVALID", "field": key}
        if record.get("from_scene") == record.get("terminal_scene"):
            return {"status": "BLOCKED", "code": "TERMINAL_SELF_TRANSITION"}
        if not record.get("action_source_ref") or not record.get("outcome_source_ref"):
            return {"status": "BLOCKED", "code": "TERMINAL_SOURCE_REF_MISSING"}
        return {"status": "RESOLVED", "code": "EXPLICIT_ACTION_TO_TERMINAL_OUTCOME"}

    @classmethod
    def materialize(cls, record):
        gate = cls.validate(record)
        if gate["status"] != "RESOLVED":
            return gate
        transition = {
            "transition_id": record.get("transition_id", "TERMINAL_TRANSITION"),
            "from_scene": record["from_scene"],
            "to_scene": record["terminal_scene"],
            "predicate": deepcopy(record["predicate"]),
            "effects": deepcopy(record["effects"]),
            "authority": "EXPLICIT_ACTION_PLUS_TERMINAL_CONDITION",
            "executable": True,
            "provenance": {
                "action_source_ref": record["action_source_ref"],
                "action_source_sha256": record["action_source_sha256"],
                "outcome_source_ref": record["outcome_source_ref"],
                "outcome_source_sha256": record["outcome_source_sha256"],
                "partition": record["partition"],
            },
        }
        v = GenericStateTransition.validate(transition)
        if not v["ok"]:
            return {"status": "BLOCKED", "code": "TERMINAL_GENERIC_TRANSITION_REJECTED", "validation": v}
        return {"status": "MATERIALIZED", "code": "TERMINAL_TRANSITION_MATERIALIZED", "transition": transition}

class SourceBackedPathClosureV1:
    """Proves one executable source-backed path. Does not itself promote scenario release status."""

    @staticmethod
    def _find_path(start_scene, terminal_scene, transitions):
        by_from = {}
        for t in transitions:
            by_from.setdefault(t["from_scene"], []).append(t)
        q = deque([(start_scene, [start_scene], [])])
        seen = {start_scene}
        while q:
            node, nodes, tids = q.popleft()
            if node == terminal_scene:
                return nodes, tids
            for t in by_from.get(node, []):
                nxt = t["to_scene"]
                if nxt in seen:
                    continue
                seen.add(nxt)
                q.append((nxt, nodes + [nxt], tids + [t["transition_id"]]))
        return None, None

    @classmethod
    def prove(cls, start_record, safe_transitions, terminal_record):
        sg = StartCandidateEvidenceGate.validate(start_record)
        if sg["status"] != "RESOLVED":
            return {"status": "BLOCKED", "code": sg["code"], "pass_real_candidate": False}
        tm = TerminalOutcomeEvidenceGate.materialize(terminal_record)
        if tm["status"] != "MATERIALIZED":
            return {"status": "BLOCKED", "code": tm["code"], "pass_real_candidate": False}
        transitions = []
        for t in safe_transitions:
            v = GenericStateTransition.validate(t)
            if not v["ok"]:
                return {"status": "BLOCKED", "code": "UNSAFE_PARENT_TRANSITION", "validation": v, "pass_real_candidate": False}
            transitions.append(deepcopy(t))
        transitions.append(tm["transition"])
        nodes, tids = cls._find_path(start_record["scene_id"], terminal_record["terminal_scene"], transitions)
        if not nodes:
            return {"status": "BLOCKED", "code": "NO_START_TO_TERMINAL_PATH", "pass_real_candidate": False}
        state = {"available_scenes": [start_record["scene_id"]], "transition_ledger": []}
        by_id = {t["transition_id"]: t for t in transitions}
        for tid in tids:
            applied = GenericStateTransition.apply(by_id[tid], state)
            if applied["status"] != "COMMITTED":
                return {"status": "BLOCKED", "code": "PATH_EXECUTION_FAILED", "transition_id": tid, "pass_real_candidate": False}
            state = applied["state"]
        return {
            "status": "PROVED",
            "code": "SOURCE_BACKED_START_TO_TERMINAL_PATH",
            "pass_real_candidate": True,
            "promotion_applied": False,
            "path_nodes": nodes,
            "transition_ids": tids,
            "executed_state": state,
            "start_evidence": {
                "source_ref": start_record["source_ref"],
                "source_sha256": start_record["source_sha256"],
                "partition": start_record["partition"],
            },
            "terminal_evidence": tm["transition"]["provenance"],
        }

    @staticmethod
    def player_safe_summary(proof):
        if proof.get("status") != "PROVED":
            return {"status": proof.get("status"), "pass_real_candidate": False}
        return {
            "status": "CERTIFICATION_READY",
            "pass_real_candidate": bool(proof.get("pass_real_candidate")),
            "path_length": len(proof.get("transition_ids", [])),
            "promotion_applied": False,
        }
