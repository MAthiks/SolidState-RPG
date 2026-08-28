import json,re
from pathlib import Path
_HEX64=re.compile(r"[0-9a-f]{64}")
_HEX40=re.compile(r"[0-9a-f]{40}")
class Scenario6ReleaseGateV1:
    PARENT_CHECKPOINT_GIT_BLOB_SHA1="9107299fad5183862a22513c208014b8dc4b1f5d"
    PATH_ARTIFACT_GIT_BLOB_SHA1="04adb29032bd77d7bdbb5b9e0036d98539505aab"
    SOURCE_PDF_SHA256="31e864a4603cba6fdacfebb6fc1e9239509507b369a3c54441f55b977ddf8143"
    SOURCE_LAYOUT_SHA256="82c27f32a4244d0964fbb94ef4bb34c81b3f81775ca3561ecf3c4f8bda2f498a"
    EXPECTED_SOURCE_EVIDENCE={
        "start_slice_sha256":"62786aceb2ebd05ba3d9eb7106dc5f59a873701b6eb6fd8adf4755782e704cbf",
        "act_i_to_ii_slice_sha256":"0f07117218dbebe0004783de1c43b1b242a95064dc94d6e401ed5c6d02a52143",
        "act_ii_to_iii_slice_sha256":"0bf262513a2814d75bef38be98519b38fb7d08c88bf08a7b403107db7f0a606b",
        "terminal_slice_sha256":"46b893cb20158cd3d60b4ebd17a5f49e1c9240eb9cc90cc076d140fd19877aa0"
    }
    REQUIRED_CHECKS=(
        "source_identity","source_preflight","historical_release_readiness_support",
        "source_backed_path_proof","generic_path_execution","conditional_path_preserved",
        "alternative_endings_preserved","knowledge_isolation","player_safe_projection",
        "resolver_promotion","scenario_selection_selectable","tamper_fail_closed","status_regression"
    )
    @classmethod
    def validate_certificate(cls,cert):
        if cert.get("schema")!="SOLIDSTATE_SCENARIO6_PASS_REAL_RELEASE_323_V1":return {"status":"BLOCKED","code":"RELEASE_SCHEMA_INVALID"}
        if cert.get("scenario_key")!="scenario6":return {"status":"BLOCKED","code":"RELEASE_SCENARIO_MISMATCH"}
        if cert.get("parent_checkpoint")!=322:return {"status":"BLOCKED","code":"RELEASE_PARENT_CHECKPOINT_INVALID"}
        if cert.get("parent_checkpoint_git_blob_sha1")!=cls.PARENT_CHECKPOINT_GIT_BLOB_SHA1:return {"status":"BLOCKED","code":"PARENT_CHECKPOINT_IDENTITY_MISMATCH"}
        if cert.get("checkpoint322_path_artifact_git_blob_sha1")!=cls.PATH_ARTIFACT_GIT_BLOB_SHA1:return {"status":"BLOCKED","code":"PATH_ARTIFACT_IDENTITY_MISMATCH"}
        if cert.get("source_pdf_sha256")!=cls.SOURCE_PDF_SHA256:return {"status":"BLOCKED","code":"SOURCE_PDF_HASH_MISMATCH"}
        if cert.get("source_layout_sha256")!=cls.SOURCE_LAYOUT_SHA256:return {"status":"BLOCKED","code":"SOURCE_LAYOUT_HASH_MISMATCH"}
        if cert.get("path_status")!="PASS_REAL_CANDIDATE" or cert.get("path_length")!=6:return {"status":"BLOCKED","code":"PATH_NOT_CERTIFICATION_READY"}
        if cert.get("terminal")!="MUSE_TERMINAL_ENMOUTEF_BODY_FUTURE":return {"status":"BLOCKED","code":"TERMINAL_AUTHORITY_MISMATCH"}
        if cert.get("conditional_path_preserved") is not True:return {"status":"BLOCKED","code":"CONDITIONAL_PATH_COLLAPSED"}
        if cert.get("alternative_endings_preserved") is not True:return {"status":"BLOCKED","code":"ALTERNATIVE_ENDINGS_COLLAPSED"}
        if cert.get("open_conclusion_not_collapsed") is not True:return {"status":"BLOCKED","code":"OPEN_CONCLUSION_COLLAPSED"}
        if cert.get("historical_freeze_reactivated") is not False:return {"status":"BLOCKED","code":"HISTORICAL_FREEZE_REACTIVATION_FORBIDDEN"}
        if cert.get("source_text_republished") is not False:return {"status":"BLOCKED","code":"SOURCE_TEXT_REPUBLICATION_FORBIDDEN"}
        if cert.get("release_class")!="PASS_REAL" or cert.get("pass_real") is not True:return {"status":"BLOCKED","code":"PASS_REAL_NOT_AUTHORIZED"}
        if cert.get("player_keeper_leaks")!=0:return {"status":"BLOCKED","code":"KNOWLEDGE_LEAK_PRESENT"}
        failed=[k for k in cls.REQUIRED_CHECKS if cert.get("checks",{}).get(k)!="PASS"]
        if failed:return {"status":"BLOCKED","code":"RELEASE_CHECKS_INCOMPLETE","failed":failed}
        ev=cert.get("source_evidence",{})
        for k,expected in cls.EXPECTED_SOURCE_EVIDENCE.items():
            if not _HEX64.fullmatch(str(ev.get(k,""))):return {"status":"BLOCKED","code":"SOURCE_EVIDENCE_HASH_INVALID","field":k}
            if ev.get(k)!=expected:return {"status":"BLOCKED","code":"SOURCE_EVIDENCE_HASH_MISMATCH","field":k}
        for k in ("parent_checkpoint_git_blob_sha1","checkpoint322_path_artifact_git_blob_sha1"):
            if not _HEX40.fullmatch(str(cert.get(k,""))):return {"status":"BLOCKED","code":"REPOSITORY_IDENTITY_INVALID","field":k}
        if cert.get("promotion_source")!="SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1":return {"status":"BLOCKED","code":"PROMOTION_AUTHORITY_INVALID"}
        return {"status":"PASS","code":"SCENARIO6_PASS_REAL_RELEASE_AUTHORIZED"}
    @classmethod
    def load_and_validate(cls,scenario_dir):
        p=Path(scenario_dir)/"MUSE_PASS_REAL_RELEASE_323.json"
        if not p.exists():return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_MISSING"}
        try:cert=json.loads(p.read_text(encoding="utf-8"))
        except Exception:return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_INVALID_JSON"}
        g=cls.validate_certificate(cert)
        return {**g,"certificate":cert} if g["status"]=="PASS" else g
