import copy
import json
import tempfile
from pathlib import Path

from .core import RecoveryRuntimeR1

checks = []


def ck(name, condition, detail=None):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError((name, detail))


def players(n):
    return [
        {
            "name": f"I{i}",
            "stats": {"HP": 10 + i, "SAN": 60 + i, "MP": 8 + i, "Luck": 40 + i},
            "inventory": [],
        }
        for i in range(1, n + 1)
    ]


def run():
    cases = 0
    for n in (1, 2, 3, 4):
        cases += 1
        td = Path(tempfile.mkdtemp(prefix="r1b_"))
        continuous = RecoveryRuntimeR1(td / "continuous.sqlite", b"k")
        resumed = RecoveryRuntimeR1(td / "resumed.sqlite", b"k")
        a = continuous.new_session(players(n), f"S{n}")
        b = resumed.new_session(players(n), f"S{n}")
        ck(f"n{n}_setup_continuous", a["status"] == "SESSION_READY")
        ck(f"n{n}_setup_resumed", b["status"] == "SESSION_READY")
        cmap = a["control_map"]
        ids = list(cmap)
        cid = cmap[ids[0]]

        for runtime in (continuous, resumed):
            runtime.add_knowledge(cid, "PUB", "PLAYER", {"v": "seen"})
            runtime.add_knowledge(cid, "SECRET", "KEEPER", {"v": "hidden"})
        view = continuous.player_view(ids[0])
        ck(f"n{n}_public_visible", any(x["knowledge_id"] == "PUB" for x in view["knowledge"]))
        ck(f"n{n}_keeper_hidden", all(x["knowledge_id"] != "SECRET" for x in view["knowledge"]))

        tape = []
        for i in range(8):
            pid = ids[i % n]
            tape.append((pid, cmap[pid], f"A{i + 1}", ((n * 17 + i * 13) % 100) + 1, 0, f"E{n}_{i + 1}"))

        for row in tape[:4]:
            ck(f"n{n}_cont_pre_{row[5]}", continuous.append_player_action(*row[:5], event_id=row[5])["status"] == "COMMIT")
            ck(f"n{n}_resume_pre_{row[5]}", resumed.append_player_action(*row[:5], event_id=row[5])["status"] == "COMMIT")

        save = resumed.save_bundle()
        before = resumed.state_digest()
        tampered = copy.deepcopy(save)
        tampered["payload"]["state"]["session_id"] = "TAMPERED"
        bad = resumed.restore_bundle(tampered)
        ck(f"n{n}_tamper_blocked", bad["status"] == "FAIL_CLOSED")
        ck(f"n{n}_tamper_zero_mutation", before == resumed.state_digest())
        ck(f"n{n}_restore_valid", resumed.restore_bundle(save)["status"] == "RESTORED_STRICT")

        for row in tape[4:]:
            ck(f"n{n}_cont_post_{row[5]}", continuous.append_player_action(*row[:5], event_id=row[5])["status"] == "COMMIT")
            ck(f"n{n}_resume_post_{row[5]}", resumed.append_player_action(*row[:5], event_id=row[5])["status"] == "COMMIT")

        ck(f"n{n}_replay_continuous", continuous.verify_journal(continuous.state())["status"] == "REPLAY_MATCH")
        ck(f"n{n}_replay_resumed", resumed.verify_journal(resumed.state())["status"] == "REPLAY_MATCH")
        ck(f"n{n}_fingerprint_equal", continuous.continuity_fingerprint() == resumed.continuity_fingerprint())

        before = continuous.state_digest()
        wrong_cid = cmap[ids[-1]] if n > 1 else "WRONG"
        bad = continuous.append_player_action(ids[0], wrong_cid, "BAD", 50, event_id=f"BAD{n}")
        ck(f"n{n}_wrong_actor_blocked", bad["status"] == "FAIL_CLOSED")
        ck(f"n{n}_wrong_actor_zero_mutation", before == continuous.state_digest())

        before = continuous.state_digest()
        bad = continuous.append_player_action(ids[0], cmap[ids[0]], "BADROLL", 101, event_id=f"BADR{n}")
        ck(f"n{n}_bad_roll_blocked", bad["status"] == "FAIL_CLOSED")
        ck(f"n{n}_bad_roll_zero_mutation", before == continuous.state_digest())

        state = continuous.state()
        duplicate = copy.deepcopy(state)
        duplicate["journal"].insert(2, copy.deepcopy(duplicate["journal"][1]))
        ck(f"n{n}_duplicate_rejected", continuous.verify_journal(duplicate)["status"] == "REPLAY_DIVERGENCE")

        omitted = copy.deepcopy(state)
        omitted["journal"].pop(1)
        ck(f"n{n}_omit_rejected", continuous.verify_journal(omitted)["status"] == "REPLAY_DIVERGENCE")

        reordered = copy.deepcopy(state)
        reordered["journal"][1], reordered["journal"][2] = reordered["journal"][2], reordered["journal"][1]
        ck(f"n{n}_reorder_rejected", continuous.verify_journal(reordered)["status"] == "REPLAY_DIVERGENCE")

        if n > 1:
            reattributed = copy.deepcopy(state)
            new_pid = ids[0] if reattributed["journal"][1]["event"]["payload"]["player_id"] != ids[0] else ids[1]
            reattributed["journal"][1]["event"]["payload"]["player_id"] = new_pid
            reattributed["journal"][1]["event"]["payload"]["character_id"] = cmap[new_pid]
            previous_hash = "GENESIS"
            for row in reattributed["journal"]:
                row["previous_hash"] = previous_hash
                row["event_hash"] = RecoveryRuntimeR1._event_hash(previous_hash, row["event"])
                previous_hash = row["event_hash"]
            expected = continuous.verify_journal(state)["actor_trace"]
            ck(f"n{n}_reattribution_detected", continuous.verify_journal(reattributed, expected)["status"] == "REPLAY_DIVERGENCE")

        rng = continuous.roll_d100()
        ck(f"n{n}_rng_range", 1 <= rng["result"] <= 100)
        ck(f"n{n}_rng_provenance", "OS CSPRNG" in rng["provenance"])

        continuous.close()
        resumed.close()

    result = {
        "schema": "SOLIDSTATE_RECOVERY_RUNTIME_R1_B_SELF_TEST_V1",
        "result": "PASS",
        "cases": cases,
        "passed": len(checks),
        "total": len(checks),
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
