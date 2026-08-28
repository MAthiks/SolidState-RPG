import re
from copy import deepcopy
from .generic_state_transitions import GenericStateTransition

class SafeTransitionEvidenceGate:
    REQUIRED = {
        "transition_id","from_scene","to_scene","predicate","effects",
        "authority","relation","source_ref","source_sha256","partition",
        "target_binding_count","explicit_source_language"
    }
    ALLOWED = {
        ("LEADS_TO", "EXPLICIT_SOURCE_TABLE_RELATION"),
        ("CONDITIONAL_REDIRECT", "EXPLICIT_CONDITION_PLUS_UNIQUE_TARGET"),
        ("SECTION_HANDOFF", "EXPLICIT_SECTION_HANDOFF"),
        ("ACCESS_PATH", "EXPLICIT_DIRECTIONAL_LITERAL"),
    }

    @classmethod
    def validate(cls, record):
        missing = cls.REQUIRED - set(record)
        if missing:
            return {"status":"BLOCKED","code":"TRANSITION_EVIDENCE_INCOMPLETE","missing":sorted(missing)}
        if not record.get("explicit_source_language"):
            return {"status":"BLOCKED","code":"SOURCE_LANGUAGE_NOT_EXPLICIT"}
        if (record.get("relation"), record.get("authority")) not in cls.ALLOWED:
            return {"status":"BLOCKED","code":"TRANSITION_AUTHORITY_INSUFFICIENT"}
        if record.get("target_binding_count") != 1:
            return {"status":"BLOCKED","code":"TARGET_BINDING_NOT_UNIQUE"}
        if not record.get("from_scene") or not record.get("to_scene"):
            return {"status":"BLOCKED","code":"TRANSITION_ENDPOINT_MISSING"}
        if record["from_scene"] == record["to_scene"]:
            return {"status":"BLOCKED","code":"SELF_TRANSITION"}
        if not re.fullmatch(r"[0-9a-f]{64}", str(record.get("source_sha256",""))):
            return {"status":"BLOCKED","code":"SOURCE_HASH_INVALID"}
        if record.get("partition") not in {"KEEPER","PLAYER_SAFE","SYSTEM"}:
            return {"status":"BLOCKED","code":"SOURCE_PARTITION_INVALID"}
        if record.get("editorial_reference_only"):
            return {"status":"BLOCKED","code":"EDITORIAL_REFERENCE_IS_NOT_CAUSALITY"}
        return {"status":"RESOLVED","code":"SAFE_SOURCE_BACKED_TRANSITION"}

    @classmethod
    def materialize(cls, record):
        gate = cls.validate(record)
        if gate["status"] != "RESOLVED":
            return gate
        transition = {
            "transition_id": record["transition_id"],
            "from_scene": record["from_scene"],
            "to_scene": record["to_scene"],
            "predicate": deepcopy(record["predicate"]),
            "effects": deepcopy(record["effects"]),
            "authority": record["authority"],
            "executable": True,
            "provenance": {
                "source_ref": record["source_ref"],
                "source_sha256": record["source_sha256"],
                "partition": record["partition"],
                "relation": record["relation"],
            },
        }
        v = GenericStateTransition.validate(transition)
        if not v["ok"]:
            return {"status":"BLOCKED","code":"GENERIC_TRANSITION_REJECTED","validation":v}
        return {"status":"MATERIALIZED","code":"SAFE_TRANSITION_MATERIALIZED","transition":transition}

class SafeTransitionRecoveryV1:
    """Fail-closed recovery of source-backed transitions. Never promotes scenario status."""
    @staticmethod
    def recover(records):
        admitted, blocked = [], []
        for rec in records:
            out = SafeTransitionEvidenceGate.materialize(rec)
            if out["status"] == "MATERIALIZED":
                admitted.append(out["transition"])
            else:
                blocked.append({"transition_id":rec.get("transition_id"),"code":out.get("code")})
        return {
            "status":"RECOVERED" if admitted else "NO_SAFE_TRANSITIONS",
            "safe_transition_count":len(admitted),
            "blocked_count":len(blocked),
            "transitions":admitted,
            "blocked":blocked,
            "pass_real_promotion":False,
        }

    @staticmethod
    def player_safe_provenance(result):
        """Strip Keeper-only text by construction; expose hashes/refs only."""
        rows=[]
        for t in result.get("transitions",[]):
            p=t["provenance"]
            rows.append({
                "transition_id":t["transition_id"],
                "source_ref":p["source_ref"],
                "source_sha256":p["source_sha256"],
                "relation":p["relation"],
            })
        return {"safe_transition_count":len(rows),"provenance":rows}
