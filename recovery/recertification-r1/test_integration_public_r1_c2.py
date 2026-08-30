import json
import os
import tempfile
from pathlib import Path

from integrated_adjudication_r1_c2 import RULES_ZIP_SHA256, SourceBackedRuntimeR1C2

checks = []


def ck(name, condition, detail=None):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError((name, detail))


def run():
    rules_zip = Path(os.environ["R1_C1_RULES_ZIP"])
    temp = Path(tempfile.mkdtemp(prefix="r1c2_public_"))
    sources = {
        "COC7_KEEPER": temp / "missing-keeper.pdf",
        "COC7_INVESTIGATOR": temp / "missing-investigator.pdf",
    }
    runtime = SourceBackedRuntimeR1C2(temp / "runtime.sqlite", rules_zip, sources, b"public-ci")
    ready = runtime.new_session([{"name": "P1", "stats": {"HP": 12, "SAN": 60}}], "PUBLIC-CI")
    ck("session_ready", ready["status"] == "SESSION_READY")

    rules = runtime._rules_identity()
    ck("rules_identity_verified", rules["status"] == "VERIFIED", rules)
    ck("rules_sha_exact", rules.get("zip_sha256") == RULES_ZIP_SHA256, rules)

    before = runtime.state_digest()
    bad_actor = runtime.adjudicate_skill(
        player_id="P1",
        character_id="WRONG",
        skill_value=50,
        recorded_roll=20,
        replay=True,
        event_id="WRONG-ACTOR",
    )
    ck("actor_mismatch_blocked", bad_actor["code"] == "ACTOR_CONTROL_MISMATCH", bad_actor)
    ck("actor_mismatch_zero_mutation", runtime.state_digest() == before)

    source_block = runtime.adjudicate_skill(
        player_id="P1",
        character_id="C1",
        skill_value=50,
        recorded_roll=20,
        replay=True,
        event_id="MISSING-SOURCE",
    )
    ck("missing_private_source_blocked", source_block["code"] == "SOURCE_PREFLIGHT_FAILED", source_block)
    ck("missing_private_source_zero_mutation", runtime.state_digest() == before)

    unknown = runtime._preflight("UNMATERIALIZED_MECHANIC")
    ck("unmaterialized_mechanic_blocked", unknown["code"] == "MECHANIC_UNMATERIALIZED", unknown)

    fake_rules = temp / "fake-rules.zip"
    fake_rules.write_bytes(rules_zip.read_bytes() + b"tamper")
    tampered = SourceBackedRuntimeR1C2(temp / "tampered.sqlite", fake_rules, sources, b"public-ci")
    tampered.new_session([{"name": "P1", "stats": {"HP": 12, "SAN": 60}}], "TAMPER")
    tampered_before = tampered.state_digest()
    result = tampered.adjudicate_skill(
        player_id="P1",
        character_id="C1",
        skill_value=50,
        recorded_roll=20,
        replay=True,
    )
    ck("tampered_rules_blocked", result["code"] == "RULES_PACKAGE_HASH_MISMATCH", result)
    ck("tampered_rules_zero_mutation", tampered.state_digest() == tampered_before)

    san = runtime.adjudicate_sanity_loss(
        player_id="P1",
        character_id="C1",
        loss=5,
        sanity_start_of_day=60,
        commit=True,
    )
    ck("san_never_bypasses_source_gate", san["code"] == "SOURCE_PREFLIGHT_FAILED", san)

    runtime.close()
    tampered.close()
    report = {
        "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_PUBLIC_TEST_V1",
        "result": "PASS",
        "passed": len(checks),
        "total": len(checks),
        "scope": "public fail-closed and cryptographic integration checks; private happy path is separate",
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
