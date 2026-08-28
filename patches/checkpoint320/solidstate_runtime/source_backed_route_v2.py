import re
from collections import deque
from copy import deepcopy
from .generic_state_transitions import GenericStateTransition

_HEX64 = re.compile(r"[0-9a-f]{64}")

class SourceStartEvidenceGateV2:
    REQUIRED = {"scene_id","source_refs","source_hashes","partition","availability","explicit_source_language"}
    ALLOWED_AVAILABILITY = {"AT_SCENARIO_START","AT_ARRIVAL"}

    @classmethod
    def validate(cls, record):
        missing = cls.REQUIRED - set(record)
        if missing:
            return {"status":"BLOCKED","code":"START_EVIDENCE_INCOMPLETE","missing":sorted(missing)}
        if record.get("partition") != "PLAYER_SAFE":
            return {"status":"BLOCKED","code":"START_NOT_PLAYER_SAFE"}
        if record.get("availability") not in cls.ALLOWED_AVAILABILITY:
            return {"status":"BLOCKED","code":"START_AVAILABILITY_UNSUPPORTED"}
        if not record.get("explicit_source_language"):
            return {"status":"BLOCKED","code":"START_NOT_EXPLICIT"}
        refs, hashes = record.get("source_refs"), record.get("source_hashes")
        if not isinstance(refs,list) or not refs or not isinstance(hashes,list) or len(refs)!=len(hashes):
            return {"status":"BLOCKED","code":"START_SOURCE_EVIDENCE_INVALID"}
        if not all(_HEX64.fullmatch(str(h)) for h in hashes):
            return {"status":"BLOCKED","code":"START_SOURCE_HASH_INVALID"}
        if not record.get("scene_id"):
            return {"status":"BLOCKED","code":"START_SCENE_MISSING"}
        return {"status":"RESOLVED","code":"SOURCE_START_RESOLVED"}

class ExplicitRouteTransitionGateV2:
    REQUIRED = {
        "transition_id","from_scene","to_scene","predicate","effects","relation","authority",
        "source_refs","source_hashes","partition","target_binding_count","explicit_source_language"
    }
    ALLOWED = {
        ("REQUIRED_TRAVEL","EXPLICIT_REQUIRED_TRAVEL"),
        ("SCHEDULED_TRANSFER","EXPLICIT_SCHEDULED_EVENT"),
        ("TIMED_EVENT","EXPLICIT_TIMED_EVENT"),
        ("PLAYER_OPTION","EXPLICIT_PLAYER_OPTION"),
        ("CONDITIONAL_CAPTURE","EXPLICIT_CONDITIONAL_CONSEQUENCE"),
        ("CONDITIONAL_REVIVAL","EXPLICIT_CONDITIONAL_SEQUENCE"),
        ("TERMINAL_HANDOFF","EXPLICIT_EPILOGUE_DEPENDENCY"),
    }

    @classmethod
    def validate(cls, record):
        missing = cls.REQUIRED - set(record)
        if missing:
            return {"status":"BLOCKED","code":"ROUTE_EVIDENCE_INCOMPLETE","missing":sorted(missing)}
        if not record.get("explicit_source_language"):
            return {"status":"BLOCKED","code":"ROUTE_SOURCE_NOT_EXPLICIT"}
        if (record.get("relation"),record.get("authority")) not in cls.ALLOWED:
            return {"status":"BLOCKED","code":"ROUTE_AUTHORITY_INSUFFICIENT"}
        if record.get("target_binding_count") != 1:
            return {"status":"BLOCKED","code":"ROUTE_TARGET_NOT_UNIQUE"}
        if record.get("from_scene") == record.get("to_scene"):
            return {"status":"BLOCKED","code":"ROUTE_SELF_TRANSITION"}
        refs, hashes = record.get("source_refs"), record.get("source_hashes")
        if not isinstance(refs,list) or not refs or not isinstance(hashes,list) or len(refs)!=len(hashes):
            return {"status":"BLOCKED","code":"ROUTE_SOURCE_EVIDENCE_INVALID"}
        if not all(_HEX64.fullmatch(str(h)) for h in hashes):
            return {"status":"BLOCKED","code":"ROUTE_SOURCE_HASH_INVALID"}
        if record.get("partition") not in {"KEEPER","PLAYER_SAFE","SYSTEM"}:
            return {"status":"BLOCKED","code":"ROUTE_PARTITION_INVALID"}
        if record.get("editorial_reference_only"):
            return {"status":"BLOCKED","code":"EDITORIAL_REFERENCE_IS_NOT_ROUTE"}
        return {"status":"RESOLVED","code":"EXPLICIT_ROUTE_RELATION"}

    @classmethod
    def materialize(cls, record):
        gate = cls.validate(record)
        if gate["status"] != "RESOLVED":
            return gate
        t = {
            "transition_id":record["transition_id"],
            "from_scene":record["from_scene"],
            "to_scene":record["to_scene"],
            "predicate":deepcopy(record["predicate"]),
            "effects":deepcopy(record["effects"]),
            "authority":record["authority"],
            "executable":True,
            "provenance":{
                "source_refs":list(record["source_refs"]),
                "source_hashes":list(record["source_hashes"]),
                "partition":record["partition"],
                "relation":record["relation"],
            },
        }
        v = GenericStateTransition.validate(t)
        if not v["ok"]:
            return {"status":"BLOCKED","code":"GENERIC_ROUTE_TRANSITION_REJECTED","validation":v}
        return {"status":"MATERIALIZED","code":"ROUTE_TRANSITION_MATERIALIZED","transition":t}

class SourceBackedRouteProofV2:
    @staticmethod
    def _path(start, terminal, transitions):
        by_from={}
        for t in transitions: by_from.setdefault(t["from_scene"],[]).append(t)
        q=deque([(start,[start],[])])
        seen={start}
        while q:
            node,nodes,tids=q.popleft()
            if node==terminal: return nodes,tids
            for t in by_from.get(node,[]):
                nxt=t["to_scene"]
                if nxt in seen: continue
                seen.add(nxt); q.append((nxt,nodes+[nxt],tids+[t["transition_id"]]))
        return None,None

    @classmethod
    def prove(cls, start_record, transition_records, terminal_scene):
        sg=SourceStartEvidenceGateV2.validate(start_record)
        if sg["status"]!="RESOLVED":
            return {"status":"BLOCKED","code":sg["code"],"pass_real_candidate":False,"promotion_applied":False}
        materialized=[]
        for rec in transition_records:
            out=ExplicitRouteTransitionGateV2.materialize(rec)
            if out["status"]!="MATERIALIZED":
                return {"status":"BLOCKED","code":out.get("code"),"transition_id":rec.get("transition_id"),"pass_real_candidate":False,"promotion_applied":False}
            materialized.append(out["transition"])
        nodes,tids=cls._path(start_record["scene_id"],terminal_scene,materialized)
        if not nodes:
            return {"status":"BLOCKED","code":"NO_SOURCE_BACKED_ROUTE","pass_real_candidate":False,"promotion_applied":False}
        state={"available_scenes":[start_record["scene_id"]],"transition_ledger":[]}
        by_id={t["transition_id"]:t for t in materialized}
        for tid in tids:
            applied=GenericStateTransition.apply(by_id[tid],state)
            if applied["status"]!="COMMITTED":
                return {"status":"BLOCKED","code":"ROUTE_EXECUTION_FAILED","transition_id":tid,"pass_real_candidate":False,"promotion_applied":False}
            state=applied["state"]
        return {
            "status":"PROVED","code":"SOURCE_BACKED_ROUTE_PROVED","pass_real_candidate":True,"promotion_applied":False,
            "path_nodes":nodes,"transition_ids":tids,"executed_state":state,
            "start_evidence":{"source_refs":start_record["source_refs"],"source_hashes":start_record["source_hashes"],"partition":start_record["partition"]},
        }

    @staticmethod
    def player_safe_summary(proof):
        if proof.get("status")!="PROVED":
            return {"status":proof.get("status"),"pass_real_candidate":False}
        return {"status":"CERTIFICATION_READY","pass_real_candidate":True,"path_length":len(proof.get("transition_ids",[])),"promotion_applied":False}
