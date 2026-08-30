import json

from .core_rules import (
    classify_damage,
    derived_stats,
    firearm_difficulty,
    meets_difficulty,
    occupation_points,
    opposed,
    percentile_from_digits,
    personal_interest_points,
    pushed_roll_allowed,
    resolve_temporary_insanity,
    sanity_transition,
    success_level,
)

checks = []


def ck(name, condition):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError(name)


def run():
    ck("critical", success_level(50, 1) == "CRITICAL")
    ck("extreme", success_level(50, 10) == "EXTREME")
    ck("hard", success_level(50, 25) == "HARD")
    ck("regular", success_level(50, 50) == "REGULAR")
    ck("failure", success_level(50, 95) == "FAILURE")
    ck("fumble_low_skill", success_level(40, 96) == "FUMBLE")
    ck("not_fumble_50", success_level(50, 96) == "FAILURE")
    ck("fumble_100", success_level(90, 100) == "FUMBLE")
    ck("hard_gate", meets_difficulty(60, 30, "HARD")["success"])
    ck("extreme_gate_fail", not meets_difficulty(60, 20, "EXTREME")["success"])
    ck("opposed_level", opposed(60, 25, 80, 70)["winner"] == "A")
    ck("opposed_tie_skill", opposed(70, 60, 50, 45)["winner"] == "A")
    ck("bonus_die", percentile_from_digits(4, [4, 2], 1) == 24)
    ck("penalty_die", percentile_from_digits(4, [4, 2], -1) == 44)
    ck("00_is_100", percentile_from_digits(0, [0], 0) == 100)

    harvey = derived_stats(STR=20, CON=70, SIZ=80, DEX=55, POW=45, age=42)
    ck("harvey_hp", harvey["HP"] == 15)
    ck("harvey_san", harvey["SAN"] == 45)
    ck("harvey_mp", harvey["MP"] == 9)
    ck("harvey_mov", harvey["MOV"] == 6)
    ck("harvey_db", harvey["damage_bonus"] == "0" and harvey["build"] == 0)
    ck("personal_interest", personal_interest_points(85) == 170)
    ck("journalist_points", occupation_points("EDU_X4", {"EDU": 84}) == 336)
    ck("push_skill", pushed_roll_allowed("SKILL"))
    ck("push_combat_blocked", not pushed_roll_allowed("COMBAT"))

    ck("regular_damage", classify_damage(15, 15, 7)["major_wound"] is False)
    major = classify_damage(15, 15, 8)
    ck("major_wound", major["major_wound"] and major["current_hp"] == 7 and major["requires_con_for_major_wound"])
    dying = classify_damage(15, 4, 5, True)
    ck("dying", dying["dying"] and dying["current_hp"] == 0)
    ck("over_max_death", classify_damage(15, 15, 16)["status"] == "DEAD")

    ck("san_stable", sanity_transition(current_san=60, sanity_start_of_day=60, loss=4)["state"] == "STABLE")
    ck("temp_check", sanity_transition(current_san=60, sanity_start_of_day=60, loss=5)["state"] == "TEMPORARY_INSANITY_INT_CHECK_REQUIRED")
    ck("temp_int_success", resolve_temporary_insanity(70, 45))
    ck("temp_int_failure", not resolve_temporary_insanity(40, 80))
    ck("indefinite", sanity_transition(current_san=60, sanity_start_of_day=60, loss=12)["state"] == "INDEFINITE_INSANITY")
    ck("permanent", sanity_transition(current_san=2, sanity_start_of_day=60, loss=2)["state"] == "PERMANENT_INSANITY")

    ck("firearm_regular", firearm_difficulty(15, 15) == "REGULAR")
    ck("firearm_hard", firearm_difficulty(30, 15) == "HARD")
    ck("firearm_extreme", firearm_difficulty(60, 15) == "EXTREME")

    result = {"schema": "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_TEST_V1", "result": "PASS", "passed": len(checks), "total": len(checks)}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
