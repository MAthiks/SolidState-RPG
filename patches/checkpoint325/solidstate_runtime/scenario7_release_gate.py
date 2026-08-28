import json,re
from pathlib import Path
_HEX64=re.compile(r"[0-9a-f]{64}")
_HEX40=re.compile(r"[0-9a-f]{40}")
class Scenario7ReleaseGateV1:
    PARENT_CHECKPOINT_GIT_BLOB_SHA1="7aa9fdef7297bfc14e33897a4659c4671a8732ab"
    PATH_ARTIFACT_GIT_BLOB_SHA1="285d05fc1ef90f1925334b179e659c90362e8e51"
    SOURCE_PDF_SHA256="31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143"
    SOURCE_LAYOUT_SHA256="7b00a96cb2ab83e40b576bd0cb2e96d369393f6ce714c1d59a4a4b2f6a3265e3"
    SOURCE_EVIDENCE_DIGEST_SHA256="2f15ee7f3b5caf8a85863afe4742aa6b803d75eb9fd848cfdbb8a57d36c5ad94"
    REQUIRED_CHECKS=(
        "source_identity","source_preflight","source_backed_path_proof","generic_path_execution",
        "historical_noncausal_topology_preserved","zero_clue_anchor_edges_used",
        "alternative_investigation_routes_preserved","knowledge_isolation","player_safe_projection",
        "resolver_promotion","scenario_selection_selectable","tamper_fail_closed","status_regression"
    )
    @classmethod
    def validate_certificate(cls,cert):
        if cert.get("schema")!="SOLIDSTATE_SCENARIO7_PASS_REAL_RELEASE_325_V1":return {"status":"BLOCKED","code":"RELEASE_SCHEMA_INVALID"}
        if cert.get("scenario_key")!="scenario7":return {"status":"BLOCKED","code":"RELEASE_SCENARIO_MISMATCH"}
        if cert.get("parent_checkpoint")!=324:return {"status":"BLOCKED","code":"RELEASE_PARENT_CHECKPOINT_INVALID"}
        if cert.get("parent_checkpoint_git_blob_sha1")!=cls.PARENT_CHECKPOINT_GIT_BLOB_SHA1:return {"status":"BLOCKED","code":"PARENT_CHECKPOINT_IDENTITY_MISMATCH"}
        if cert.get("checkpoint324_path_artifact_git_blob_sha1")!=cls.PATH_ARTIFACT_GIT_BLOB_SHA1:return {"status":"BLOCKED","code":"PATH_ARTIFACT_IDENTITY_MISMATCH"}
        if cert.get("source_pdf_sha256")!=cls.SOURCE_PDF_SHA256:return {"status":"BLOCKED","code":"SOURCE_PDF_HASH_MISMATCH"}
        if cert.get("source_layout_sha256")!=cls.SOURCE_LAYOUT_SHA256:return {"status":"BLOCKED","code":"SOURCE_LAYOUT_HASH_MISMATCH"}
        if cert.get("source_evidence_digest_sha256")!=cls.SOURCE_EVIDENCE_DIGEST_SHA256:return {"status":"BLOCKED","code":"SOURCE_EVIDENCE_DIGEST_MISMATCH"}
        if cert.get("path_status")!="PASS_REAL_CANDIDATE" or cert.get("path_length")!=10:return {"status":"BLOCKED","code":"PATH_NOT_CERTIFICATION_READY"}
        if cert.get("terminal")!="EXPLORATEUR_TERMINAL_JUDICIAL_CONCLUSION":return {"status":"BLOCKED","code":"TERMINAL_AUTHORITY_MISMATCH"}
        if cert.get("clue_scene_anchor_count")!=107:return {"status":"BLOCKED","code":"CLUE_ANCHOR_COUNT_MISMATCH"}
        if cert.get("clue_anchor_edges_used")!=0:return {"status":"BLOCKED","code":"CLUE_ANCHOR_CAUSALITY_FORBIDDEN"}
        if cert.get("historical_causal_transition_count")!=0:return {"status":"BLOCKED","code":"HISTORICAL_CAUSALITY_REWRITE_FORBIDDEN"}
        if cert.get("alternative_investigation_routes_preserved") is not True:return {"status":"BLOCKED","code":"ALTERNATIVE_INVESTIGATION_ROUTES_COLLAPSED"}
        if cert.get("specific_clue_anchor_required") is not False:return {"status":"BLOCKED","code":"SPECIFIC_CLUE_ANCHOR_REQUIREMENT_FORBIDDEN"}
        if cert.get("source_text_republished") is not False:return {"status":"BLOCKED","code":"SOURCE_TEXT_REPUBLICATION_FORBIDDEN"}
        if cert.get("release_class")!="PASS_REAL" or cert.get("pass_real") is not True:return {"status":"BLOCKED","code":"PASS_REAL_NOT_AUTHORIZED"}
        if cert.get("player_keeper_leaks")!=0:return {"status":"BLOCKED","code":"KNOWLEDGE_LEAK_PRESENT"}
        failed=[k for k in cls.REQUIRED_CHECKS if cert.get("checks",{}).get(k)!="PASS"]
        if failed:return {"status":"BLOCKED","code":"RELEASE_CHECKS_INCOMPLETE","failed":failed}
        if not _HEX64.fullmatch(str(cert.get("source_evidence_digest_sha256",""))):return {"status":"BLOCKED","code":"SOURCE_EVIDENCE_DIGEST_INVALID"}
        for k in ("parent_checkpoint_git_blob_sha1","checkpoint324_path_artifact_git_blob_sha1"):
            if not _HEX40.fullmatch(str(cert.get(k,""))):return {"status":"BLOCKED","code":"REPOSITORY_IDENTITY_INVALID","field":k}
        if cert.get("promotion_source")!="SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1":return {"status":"BLOCKED","code":"PROMOTION_AUTHORITY_INVALID"}
        return {"status":"PASS","code":"SCENARIO7_PASS_REAL_RELEASE_AUTHORIZED"}
    @classmethod
    def load_and_validate(cls,scenario_dir):
        p=Path(scenario_dir)/"EXPLORATEUR_PASS_REAL_RELEASE_325.json"
        if not p.exists():return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_MISSING"}
        try:cert=json.loads(p.read_text(encoding="utf-8"))
        except Exception:return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_INVALID_JSON"}
        g=cls.validate_certificate(cert)
        return {**g,"certificate":cert} if g["status"]=="PASS" else g
