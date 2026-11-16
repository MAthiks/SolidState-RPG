from __future__ import annotations

PACKAGE_ID = "COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1"
CHECKPOINT_FLOOR = 333

LEVEL_RANK = {
    "FUMBLE": 0,
    "FAILURE": 1,
    "REGULAR": 2,
    "HARD": 3,
    "EXTREME": 4,
    "CRITICAL": 5,
}


def _valid_percent(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100


def success_level(value: int, roll: int) -> str:
    if not _valid_percent(value) or not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
        raise ValueError("PERCENTILE_INPUT_INVALID")
    if roll == 1:
        return "CRITICAL"
    if roll == 100 or (value < 50 and roll >= 96):
        return "FUMBLE"
    if roll <= value // 5:
        return "EXTREME"
    if roll <= value // 2:
        return "HARD"
    if roll <= value:
        return "REGULAR"
    return "FAILURE"


def meets_difficulty(value: int, roll: int, difficulty: str = "REGULAR") -> dict:
    level = success_level(value, roll)
    need = {"REGULAR": 2, "HARD": 3, "EXTREME": 4}.get(difficulty)
    if need is None:
        raise ValueError("DIFFICULTY_INVALID")
    return {"level": level, "success": LEVEL_RANK[level] >= need, "difficulty": difficulty}


def opposed(value_a: int, roll_a: int, value_b: int, roll_b: int) -> dict:
    level_a = success_level(value_a, roll_a)
    level_b = success_level(value_b, roll_b)
    rank_a = LEVEL_RANK[level_a]
    rank_b = LEVEL_RANK[level_b]
    if rank_a > rank_b:
        winner = "A"
    elif rank_b > rank_a:
        winner = "B"
    elif value_a > value_b:
        winner = "A"
    elif value_b > value_a:
        winner = "B"
    else:
        winner = "TIE_REROLL_OR_IMPASSE"
    return {"a": level_a, "b": level_b, "winner": winner}


def percentile_from_digits(units: int, tens: list[int], net_bonus: int = 0) -> int:
    if not (
        isinstance(units, int)
        and 0 <= units <= 9
        and tens
        and all(isinstance(t, int) and 0 <= t <= 9 for t in tens)
    ):
        raise ValueError("PERCENTILE_DIGITS_INVALID")
    count = 1 + abs(net_bonus)
    if len(tens) != count:
        raise ValueError("TENS_DICE_COUNT_INVALID")
    values = []
    for tens_digit in tens:
        value = tens_digit * 10 + units
        values.append(100 if value == 0 else value)
    if net_bonus > 0:
        return min(values)
    if net_bonus < 0:
        return max(values)
    return values[0]


def derived_stats(*, STR: int, CON: int, SIZ: int, DEX: int, POW: int, age: int) -> dict:
    for value in (STR, CON, SIZ, DEX, POW):
        if not _valid_percent(value):
            raise ValueError("CHARACTERISTIC_INVALID")
    if not isinstance(age, int) or not 15 <= age <= 90:
        raise ValueError("AGE_INVALID")

    hp = (CON + SIZ) // 10
    san = POW
    mp = POW // 5

    if STR < SIZ and DEX < SIZ:
        mov = 7
    elif STR > SIZ and DEX > SIZ:
        mov = 9
    else:
        mov = 8

    if age >= 80:
        mov -= 5
    elif age >= 70:
        mov -= 4
    elif age >= 60:
        mov -= 3
    elif age >= 50:
        mov -= 2
    elif age >= 40:
        mov -= 1

    total = STR + SIZ
    if total <= 64:
        damage_bonus, build = "-2", -2
    elif total <= 84:
        damage_bonus, build = "-1", -1
    elif total <= 124:
        damage_bonus, build = "0", 0
    elif total <= 164:
        damage_bonus, build = "+1D4", 1
    elif total <= 204:
        damage_bonus, build = "+1D6", 2
    else:
        extra = (total - 205) // 80
        dice = 2 + extra
        damage_bonus, build = f"+{dice}D6", 3 + extra

    return {
        "HP": hp,
        "SAN": san,
        "MP": mp,
        "MOV": mov,
        "damage_bonus": damage_bonus,
        "build": build,
    }


def occupation_points(formula: str, characteristics: dict) -> int:
    if formula == "EDU_X4":
        return characteristics["EDU"] * 4
    if formula == "EDU_X2_APP_X2":
        return characteristics["EDU"] * 2 + characteristics["APP"] * 2
    if formula == "EDU_X2_DEX_X2":
        return characteristics["EDU"] * 2 + characteristics["DEX"] * 2
    if formula == "EDU_X2_STR_OR_DEX_X2":
        return characteristics["EDU"] * 2 + max(characteristics["STR"], characteristics["DEX"]) * 2
    raise ValueError("OCCUPATION_FORMULA_UNMATERIALIZED")


def personal_interest_points(INT: int) -> int:
    if not _valid_percent(INT):
        raise ValueError("INT_INVALID")
    return INT * 2


def pushed_roll_allowed(category: str) -> bool:
    return category not in {"COMBAT", "CHASE", "SANITY", "LUCK"}


def classify_damage(max_hp: int, current_hp: int, damage: int, had_major_wound: bool = False) -> dict:
    if (
        not all(isinstance(x, int) and not isinstance(x, bool) for x in (max_hp, current_hp, damage))
        or max_hp <= 0
        or current_hp < 0
        or damage < 0
    ):
        raise ValueError("DAMAGE_INPUT_INVALID")

    if damage > max_hp:
        return {
            "status": "DEAD",
            "current_hp": 0,
            "major_wound": True,
            "dying": False,
            "unconscious": True,
        }

    major = had_major_wound or damage * 2 >= max_hp
    new_hp = max(0, current_hp - damage)
    dying = major and new_hp == 0
    return {
        "status": "DYING" if dying else ("UNCONSCIOUS" if new_hp == 0 else "INJURED"),
        "current_hp": new_hp,
        "major_wound": major,
        "dying": dying,
        "unconscious": new_hp == 0,
        "requires_con_for_major_wound": damage * 2 >= max_hp and new_hp > 0,
    }


def sanity_transition(*, current_san: int, sanity_start_of_day: int, loss: int, daily_loss_before: int = 0) -> dict:
    for value in (current_san, sanity_start_of_day, loss, daily_loss_before):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("SANITY_INPUT_INVALID")

    new_san = max(0, current_san - loss)
    if new_san == 0:
        return {"SAN": 0, "state": "PERMANENT_INSANITY"}

    daily_loss = daily_loss_before + loss
    if daily_loss * 5 >= sanity_start_of_day:
        return {"SAN": new_san, "state": "INDEFINITE_INSANITY", "daily_loss": daily_loss}

    if loss >= 5:
        return {
            "SAN": new_san,
            "state": "TEMPORARY_INSANITY_INT_CHECK_REQUIRED",
            "daily_loss": daily_loss,
        }

    return {"SAN": new_san, "state": "STABLE", "daily_loss": daily_loss}


def resolve_temporary_insanity(INT: int, int_roll: int) -> bool:
    return success_level(INT, int_roll) in {"REGULAR", "HARD", "EXTREME", "CRITICAL"}


def firearm_difficulty(distance: float, base_range: float) -> str:
    if base_range <= 0 or distance < 0:
        raise ValueError("RANGE_INVALID")
    if distance <= base_range:
        return "REGULAR"
    if distance <= 2 * base_range:
        return "HARD"
    if distance <= 4 * base_range:
        return "EXTREME"
    return "BEYOND_STANDARD_VERY_LONG_RANGE"
