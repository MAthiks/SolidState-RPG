import re
from collections import deque
from copy import deepcopy
from .generic_state_transitions import GenericStateTransition

_HEX64=re.compile(r"[0-9a-f]{64}")

class InvestigationStartEvidenceGateV4:
    REQUIRED={"scene_id","source_refs","source_hashes","partition","availability","explicit_source_language","source_language_audit","derived_from_clue_anchor"}
    @classmethod
    def validate(cls,r):
        missing=cls.REQUIRED-set(r)
        if missing:return {"status":"BLOCKED","code":"START_EVIDENCE_INCOMPLETE","missing":sorted(missing)}
        if r.get("partition")!="PLAYER_SAFE":return {"status":"BLOCKED","code":"START_NOT_PLAYER_SAFE"}
        if r.get("availability")!="AT_SCENARIO_START":return {"status":"BLOCKED","code":"START_AVAILABILITY_UNSUPPORTED"}
        if not r.get("explicit_source_language"):return {"status":"BLOCKED","code":"START_NOT_EXPLICIT"}
        if r.get("source_language_audit")!="MANUALLY_VERIFIED_EXPLICIT":return {"status":"BLOCKED","code":"START_LANGUAGE_AUDIT_MISSING"}
        if r.get("derived_from_clue_anchor"):return {"status":"BLOCKED","code":"CLUE_ANCHOR_IS_NOT_START_CAUSALITY"}
        refs,hs=r.get("source_refs"),r.get("source_hashes")
        if not isinstance(refs,list) or not refs or not isinstance(hs,list) or len(refs)!=len(hs):return {"status":"BLOCKED","code":"START_SOURCE_EVIDENCE_INVALID"}
        if not all(_HEX64.fullmatch(str(x)) for x in hs):return {"status":"BLOCKED","code":"START_SOURCE_HASH_INVALID"}
        return {"status":"RESOLVED","code":"INVESTIGATION_START_RESOLVED"}

class ExplicitInvestigationProgressionGateV4:
    REQUIRED={"transition_id","from_scene","to_scene","predicate","effects","relation","authority","source_refs","source_hashes","partition","target_binding_count","explicit_source_language","source_language_audit","derived_from_clue_anchor","requires_specific_clue_anchor"}
    ALLOWED={
      ("SCENARIO_SETUP","EXPLICIT_INVITATION_AND_TRAVEL"),
      ("WORLD_EVENT_HANDOFF","EXPLICIT_WORLD_EVENT_HANDOFF"),
      ("INVESTIGATION_START","EXPLICIT_INVESTIGATION_START"),
      ("INVESTIGATION_PROGRESS","EXPLICIT_INVESTIGATION_PROGRESS_MARKER"),
      ("SOLUTION_OPPORTUNITY","EXPLICIT_SOLUTION_OPPORTUNITY"),
      ("CONDITIONAL_CONFESSION","EXPLICIT_CONDITIONAL_CONFESSION"),
      ("TARGET_HANDOFF","EXPLICIT_SECOND_TARGET_HANDOFF"),
      ("CONDITIONAL_POLICE_CONVICTION","EXPLICIT_POLICE_CONVICTION"),
      ("ARREST_OUTCOME","EXPLICIT_ARREST_OUTCOME"),
      ("TERMINAL_CONSEQUENCE","EXPLICIT_CONCLUSION_CONDITION"),
    }
    @classmethod
    def validate(cls,r):
        missing=cls.REQUIRED-set(r)
        if missing:return {"status":"BLOCKED","code":"PROGRESSION_EVIDENCE_INCOMPLETE","missing":sorted(missing)}
        if r.get("derived_from_clue_anchor"):return {"status":"BLOCKED","code":"CLUE_ANCHOR_NOT_CAUSAL_EDGE"}
        if r.get("requires_specific_clue_anchor"):return {"status":"BLOCKED","code":"SPECIFIC_CLUE_ANCHOR_CANNOT_GATE_PATH"}
        if not r.get("explicit_source_language"):return {"status":"BLOCKED","code":"PROGRESSION_SOURCE_NOT_EXPLICIT"}
        if r.get("source_language_audit")!="MANUALLY_VERIFIED_EXPLICIT":return {"status":"BLOCKED","code":"PROGRESSION_LANGUAGE_AUDIT_MISSING"}
        if (r.get("relation"),r.get("authority")) not in cls.ALLOWED:return {"status":"BLOCKED","code":"PROGRESSION_AUTHORITY_INSUFFICIENT"}
        if r.get("target_binding_count")!=1:return {"status":"BLOCKED","code":"PROGRESSION_TARGET_NOT_UNIQUE"}
        if r.get("from_scene")==r.get("to_scene"):return {"status":"BLOCKED","code":"PROGRESSION_SELF_TRANSITION"}
        refs,hs=r.get("source_refs"),r.get("source_hashes")
        if not isinstance(refs,list) or not refs or not isinstance(hs,list) or len(refs)!=len(hs):return {"status":"BLOCKED","code":"PROGRESSION_SOURCE_EVIDENCE_INVALID"}
        if not all(_HEX64.fullmatch(str(x)) for x in hs):return {"status":"BLOCKED","code":"PROGRESSION_SOURCE_HASH_INVALID"}
        if r.get("partition") not in {"PLAYER_SAFE","KEEPER","SYSTEM"}:return {"status":"BLOCKED","code":"PROGRESSION_PARTITION_INVALID"}
        if r.get("editorial_reference_only"):return {"status":"BLOCKED","code":"EDITORIAL_REFERENCE_IS_NOT_PROGRESSION"}
        return {"status":"RESOLVED","code":"EXPLICIT_INVESTIGATION_PROGRESSION"}
    @classmethod
    def materialize(cls,r):
        g=cls.validate(r)
        if g["status"]!="RESOLVED":return g
        t={"transition_id":r["transition_id"],"from_scene":r["from_scene"],"to_scene":r["to_scene"],"predicate":deepcopy(r["predicate"]),"effects":deepcopy(r["effects"]),"authority":r["authority"],"executable":True,"provenance":{"source_refs":list(r["source_refs"]),"source_hashes":list(r["source_hashes"]),"partition":r["partition"],"relation":r["relation"],"derived_from_clue_anchor":False}}
        v=GenericStateTransition.validate(t)
        if not v["ok"]:return {"status":"BLOCKED","code":"GENERIC_PROGRESSION_REJECTED","validation":v}
        return {"status":"MATERIALIZED","code":"INVESTIGATION_PROGRESSION_MATERIALIZED","transition":t}

class SourceBackedInvestigationPathV4:
    @staticmethod
    def _path(start,terminal,ts):
        by={}
        for t in ts:by.setdefault(t["from_scene"],[]).append(t)
        q=deque([(start,[start],[])]);seen={start}
        while q:
            n,nodes,tids=q.popleft()
            if n==terminal:return nodes,tids
            for t in by.get(n,[]):
                nxt=t["to_scene"]
                if nxt in seen:continue
                seen.add(nxt);q.append((nxt,nodes+[nxt],tids+[t["transition_id"]]))
        return None,None
    @classmethod
    def prove(cls,start,records,terminal):
        sg=InvestigationStartEvidenceGateV4.validate(start)
        if sg["status"]!="RESOLVED":return {"status":"BLOCKED","code":sg["code"],"pass_real_candidate":False,"promotion_applied":False}
        mats=[]
        for r in records:
            m=ExplicitInvestigationProgressionGateV4.materialize(r)
            if m["status"]!="MATERIALIZED":return {"status":"BLOCKED","code":m.get("code"),"transition_id":r.get("transition_id"),"pass_real_candidate":False,"promotion_applied":False}
            mats.append(m["transition"])
        nodes,tids=cls._path(start["scene_id"],terminal,mats)
        if not nodes:return {"status":"BLOCKED","code":"NO_SOURCE_BACKED_INVESTIGATION_PATH","pass_real_candidate":False,"promotion_applied":False}
        state={"available_scenes":[start["scene_id"]],"transition_ledger":[]}
        byid={t["transition_id"]:t for t in mats}
        for tid in tids:
            a=GenericStateTransition.apply(byid[tid],state)
            if a["status"]!="COMMITTED":return {"status":"BLOCKED","code":"INVESTIGATION_PATH_EXECUTION_FAILED","transition_id":tid,"pass_real_candidate":False,"promotion_applied":False}
            state=a["state"]
        return {"status":"PROVED","code":"SOURCE_BACKED_INVESTIGATION_PATH_PROVED","pass_real_candidate":True,"promotion_applied":False,"path_nodes":nodes,"transition_ids":tids,"executed_state":state,"clue_anchor_edges_used":0}
    @staticmethod
    def player_safe_summary(p):
        if p.get("status")!="PROVED":return {"status":p.get("status"),"pass_real_candidate":False}
        return {"status":"CERTIFICATION_READY","pass_real_candidate":True,"path_length":len(p.get("transition_ids",[])),"promotion_applied":False,"clue_anchor_edges_used":0}
