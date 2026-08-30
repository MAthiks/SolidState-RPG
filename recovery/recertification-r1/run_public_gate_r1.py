#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = "5936b9e67af65b5a4d7d9c2d18ae6c44a7829db7"
LOST_ZIP = "SolidState_Offline_Runtime_v1_Checkpoint329.zip"
EXPECTED_BLOBS = {
    "CHECKPOINT.md": "024a925076ca1759b08dd0a166479460e5cb3f3d",
    "manifest/authority_floor.json": "f2263080e0cf97b42eb19293348a5958c3cebe7b",
    "patches/checkpoint333/CHECKPOINT_333.json": "965695bdc3ebe13f7337bb491796f6a193bd8fa6",
    "patches/checkpoint333/APPLY_333.md": "18854cf56aa5b9456237a48463769aee1f7e483f",
    "patches/checkpoint333/run_tests_chunk333.py": "cf0f3093e33a140551a3443ce3fa72c9dc8c6f7c",
    "patches/checkpoint333/NATIVE_RUNTIME_CHUNK333_REPORT.json": "ae6df132726e2745a63eb810fc017a4af2703585",
    "patches/checkpoint330/solidstate_runtime/multiplayer_certification_v2.py": "7dd495abe9eb0e44d3653334d39ca99d879debaa",
    "patches/checkpoint331/solidstate_runtime/save_resume_multiplayer_v2.py": "fe8caded08ec30f50a6f4c80a23de8fc5e35b510",
    "patches/checkpoint332/solidstate_runtime/strict_replay_multiplayer_v2.py": "fbcab13c95317907039a961d4af4f5592bb2ffc8",
}

checks = []

def run(*args, check=True):
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr}")
    return p

def record(name, ok, detail=None):
    checks.append({"name": name, "pass": bool(ok), "detail": detail})
    if not ok:
        raise AssertionError(f"{name}: {detail}")

# Exact ancestry: R1 starts from the Checkpoint333 main commit and may add only recovery work.
ancestor = run("git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD", check=False)
record("checkpoint333_base_is_ancestor", ancestor.returncode == 0, BASE_COMMIT)

# Immutable public identities recorded by the certified stack.
for path, expected in EXPECTED_BLOBS.items():
    p = ROOT / path
    record(f"exists:{path}", p.is_file(), str(p))
    actual = run("git", "hash-object", path).stdout.strip()
    record(f"blob:{path}", actual == expected, {"expected": expected, "actual": actual})

cp333 = json.loads((ROOT / "patches/checkpoint333/CHECKPOINT_333.json").read_text(encoding="utf-8"))
record("checkpoint333_number", cp333.get("checkpoint") == 333, cp333.get("checkpoint"))
record("checkpoint333_id", cp333.get("checkpoint_id") == "MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2", cp333.get("checkpoint_id"))
record("checkpoint333_verified_status", cp333.get("status") == "VERIFIED_MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2", cp333.get("status"))
cert = cp333.get("certification", {})
record("checkpoint333_2300_pass", cert.get("chunk333") == "2300/2300 PASS", cert.get("chunk333"))
record("checkpoint333_source_backed", cert.get("source_backed") is True, cert.get("source_backed"))
record("checkpoint333_zero_keeper_player_leaks", cert.get("keeper_to_player_leaks") == 0, cert.get("keeper_to_player_leaks"))
anti = cp333.get("anti_rollback", {})
record("automatic_downgrade_forbidden", anti.get("automatic_downgrade_forbidden") is True, anti)
record("android_runtime_floor_333", anti.get("android_runtime_floor") == 333, anti.get("android_runtime_floor"))

# Public checkpoint records 330-332 must remain present and verified, but their historical tests are not rerun here.
for n in (330, 331, 332):
    data = json.loads((ROOT / f"patches/checkpoint{n}/CHECKPOINT_{n}.json").read_text(encoding="utf-8"))
    record(f"checkpoint{n}_number", data.get("checkpoint") == n, data.get("checkpoint"))
    record(f"checkpoint{n}_verified_record", str(data.get("status", "")).startswith("VERIFIED"), data.get("status"))

tracked = [x for x in run("git", "ls-files").stdout.splitlines() if x]
record("lost_checkpoint329_zip_not_tracked", all(Path(x).name != LOST_ZIP for x in tracked), LOST_ZIP)
tracked_pdfs = [x for x in tracked if x.lower().endswith(".pdf")]
record("no_private_pdf_tracked", len(tracked_pdfs) == 0, tracked_pdfs)

manifest = json.loads((ROOT / "recovery/recertification-r1/RECOVERY_MANIFEST_R1.json").read_text(encoding="utf-8"))
record("r1_not_authority", manifest.get("status") == "CANDIDATE_NOT_AUTHORITY", manifest.get("status"))
record("r1_no_checkpoint334", manifest.get("promotion", {}).get("checkpoint334_created") is False, manifest.get("promotion"))
record("r1_no_android_promotion", manifest.get("promotion", {}).get("android_apk_promoted") is False, manifest.get("promotion"))
record("r1_historical_bytes_declared_missing", manifest.get("historical_gap", {}).get("bytes_available") is False, manifest.get("historical_gap"))

report = {
    "schema": "SOLIDSTATE_RECOVERY_RECERTIFICATION_R1_A_GATE_REPORT_V1",
    "generation": "RECOVERY_RECERTIFICATION_R1",
    "stage": "R1-A_PUBLIC_PROVENANCE",
    "result": "PASS",
    "head": run("git", "rev-parse", "HEAD").stdout.strip(),
    "base_commit": BASE_COMMIT,
    "checks_passed": len(checks),
    "checks_total": len(checks),
    "checks": checks,
    "scope_boundary": {
        "playable_runtime_certified": False,
        "private_source_backed_recertified": False,
        "checkpoint334_created": False,
        "android_apk_promoted": False,
        "next_gate": "R1-B_NEW_RUNTIME_MATERIALIZATION"
    }
}
out = ROOT / "recovery/recertification-r1/R1_A_GATE_REPORT.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("generation", "stage", "result", "head", "checks_passed", "checks_total")}, indent=2))
