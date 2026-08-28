import json, re
from pathlib import Path

_HEX64 = re.compile(r"[0-9a-f]{64}")

class Scenario4ReleaseGateV1:
    REQUIRED_CHECKS = (
        "dual_source_preflight",
        "knowledge_firewall",
        "protected_release_readiness",
        "source_backed_path_proof",
        "generic_path_execution",
        "player_safe_projection",
        "status_regression",
    )

    @classmethod
    def validate_certificate(cls, cert):
        if cert.get("schema") != "SOLIDSTATE_SCENARIO4_PASS_REAL_RELEASE_319_V1":
            return {"status":"BLOCKED","code":"RELEASE_SCHEMA_INVALID"}
        if cert.get("scenario_key") != "scenario4":
            return {"status":"BLOCKED","code":"RELEASE_SCENARIO_MISMATCH"}
        if cert.get("parent_checkpoint") != 318:
            return {"status":"BLOCKED","code":"RELEASE_PARENT_CHECKPOINT_INVALID"}
        if cert.get("path_status") != "PASS_REAL_CANDIDATE":
            return {"status":"BLOCKED","code":"PATH_NOT_CERTIFICATION_READY"}
        if cert.get("pass_real") is not True or cert.get("release_class") != "PASS_REAL":
            return {"status":"BLOCKED","code":"PASS_REAL_NOT_AUTHORIZED"}
        checks=cert.get("checks",{})
        failed=[k for k in cls.REQUIRED_CHECKS if checks.get(k)!="PASS"]
        if failed:
            return {"status":"BLOCKED","code":"RELEASE_CHECKS_INCOMPLETE","failed":failed}
        if cert.get("player_keeper_leaks") != 0:
            return {"status":"BLOCKED","code":"KNOWLEDGE_LEAK_PRESENT"}
        ev=cert.get("source_evidence",{})
        required_hashes=("player_start_sha256","keeper_leads_to_sha256","keeper_action_sha256","keeper_outcome_sha256")
        bad=[k for k in required_hashes if not _HEX64.fullmatch(str(ev.get(k,"")))]
        if bad:
            return {"status":"BLOCKED","code":"SOURCE_EVIDENCE_HASH_INVALID","fields":bad}
        if cert.get("promotion_source") != "SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1":
            return {"status":"BLOCKED","code":"PROMOTION_AUTHORITY_INVALID"}
        return {"status":"PASS","code":"SCENARIO4_PASS_REAL_RELEASE_AUTHORIZED"}

    @classmethod
    def load_and_validate(cls, scenario_dir):
        p=Path(scenario_dir)/"BRUME_PASS_REAL_RELEASE_319.json"
        if not p.exists():
            return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_MISSING"}
        try:
            cert=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"status":"BLOCKED","code":"RELEASE_CERTIFICATE_INVALID_JSON"}
        gate=cls.validate_certificate(cert)
        if gate["status"]!="PASS":
            return gate
        return {"status":"PASS","code":gate["code"],"certificate":cert}
