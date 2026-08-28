import json,re
from pathlib import Path
_HEX64=re.compile(r"[0-9a-f]{64}")
class Scenario5ReleaseGateV1:
    PARENT_RECORD_SHA256="d4f1ee742c546f7a8b28c3853393e7e292c0184600c99d3d1cdfe0dcba035697"
    PATH_ARTIFACT_SHA256="fc35640258ed28a56de6aa055e228223b91fbf0e39595475e8d502f03f517b28"
    SOURCE_PDF_SHA256="4df3dfa3f1bfb8ecaabaf135cd3f0ac481326d72f334fb2155614553bac20ffb"
    SOURCE_LAYOUT_SHA256="adb1e8c0c9e525e32f6f5f4dde4e9c9d87a651e7f830b1c14ef8b23f5c6c5467"
    REQUIRED_CHECKS=("source_identity","source_validation","coverage_zero_open","source_backed_path_proof","generic_route_execution","source_authorized_open_epilogue","knowledge_isolation","player_safe_projection","resolver_promotion","scenario_selection_selectable","tamper_fail_closed","status_regression","historical_certificate_not_authority")
    @classmethod
    def validate_certificate(cls,cert):
        if cert.get("schema")!="SOLIDSTATE_SCENARIO5_PASS_REAL_RELEASE_321_V1":return {"status":"BLOCKED","code":"RELEASE_SCHEMA_INVALID"}
        if cert.get("scenario_key")!="scenario5":return {"status":"BLOCKED","code":"RELEASE_SCENARIO_MISMATCH"}
        if cert.get("parent_checkpoint")!=320:return {"status":"BLOCKED","code":"RELEASE_PARENT_CHECKPOINT_INVALID"}
        if cert.get("parent_checkpoint_record_sha256")!=cls.PARENT_RECORD_SHA256:return {"status":"BLOCKED","code":"PARENT_CHECKPOINT_HASH_MISMATCH"}
        if cert.get("checkpoint320_path_artifact_sha256")!=cls.PATH_ARTIFACT_SHA256:return {"status":"BLOCKED","code":"PATH_ARTIFACT_HASH_MISMATCH"}
        if cert.get("source_pdf_sha256")!=cls.SOURCE_PDF_SHA256:return {"status":"BLOCKED","code":"SOURCE_PDF_HASH_MISMATCH"}
        if cert.get("source_layout_sha256")!=cls.SOURCE_LAYOUT_SHA256:return {"status":"BLOCKED","code":"SOURCE_LAYOUT_HASH_MISMATCH"}
        if cert.get("path_status")!="PASS_REAL_CANDIDATE" or cert.get("path_length")!=10:return {"status":"BLOCKED","code":"PATH_NOT_CERTIFICATION_READY"}
        if cert.get("terminal")!="ANTRE_EPILOGUE_OPEN_KEEPER_RESOLUTION":return {"status":"BLOCKED","code":"TERMINAL_AUTHORITY_MISMATCH"}
        if cert.get("release_class")!="PASS_REAL" or cert.get("pass_real") is not True:return {"status":"BLOCKED","code":"PASS_REAL_NOT_AUTHORIZED"}
        if cert.get("player_keeper_leaks")!=0:return {"status":"BLOCKED","code":"KNOWLEDGE_LEAK_PRESENT"}
        if cert.get("historical_pass_real_certificate_reactivated") is not False:return {"status":"BLOCKED","code":"HISTORICAL_CERTIFICATE_REACTIVATION_FORBIDDEN"}
        failed=[k for k in cls.REQUIRED_CHECKS if cert.get("checks",{}).get(k)!="PASS"]
        if failed:return {"status":"BLOCKED","code":"RELEASE_CHECKS_INCOMPLETE","failed":failed}
        for k in ("coverage_ledger_sha256","historical_certificate_sha256","historical_build_sha256","source_first_pass_zip_sha256"):
            if not _HEX64.fullmatch(str(cert.get("provenance",{}).get(k,""))):return {"status":"BLOCKED","code":"PROVENANCE_HASH_INVALID","field":k}
        if cert.get("promotion_source")!="SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1":return {"status":"BLOCKED","code":"PROMOTION_AUTHORITY_INVALID"}
        return {"status":"PASS","code":"SCENARIO5_PASS_REAL_RELEASE_AUTHORIZED"}
    @classmethod
    def load_and_validate(cls,scenario_dir):
        p=Path(scenario_dir)/"ANTRE_PASS_REAL_RELEASE_321.json"
        if not p.exists():return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_MISSING"}
        try:cert=json.loads(p.read_text(encoding="utf-8"))
        except Exception:return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_INVALID_JSON"}
        g=cls.validate_certificate(cert)
        return {**g,"certificate":cert} if g["status"]=="PASS" else g
