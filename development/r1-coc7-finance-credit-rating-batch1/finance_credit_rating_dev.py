from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
PARENT_DIR = ROOT / 'development' / 'r1-coc7-investigator-aging-batch2'
for path in (RULES_DIR, PARENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import investigator_aging_dev as aging  # noqa: E402

MODULE_ID = 'COC7_FINANCE_CREDIT_RATING_R1_BATCH1_DEV_V1'
PARENT_AGING_MODULE_ID = aging.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _valid_bool(value):
    return isinstance(value, bool)


def _valid_money(value):
    # Runtime uses caller-normalized integral money units to avoid float/replay drift.
    return _valid_int(value, 0)


def _valid_die(value, sides):
    return _valid_int(value, 1, sides)


def _blocked(code, **extra):
    return {'status': 'BLOCKED', 'code': code, **extra}


def validate_private_finance_profile(
    *,
    credit_rating: int,
    spending_level_units: int,
    cash_refresh_units: int,
    asset_value_units: int,
    living_standard_id: str,
    adapter_verified: bool,
) -> dict:
    if not _valid_int(credit_rating, 0, 99):
        return _blocked('CREDIT_RATING_INVALID')
    if not all(_valid_money(v) for v in (spending_level_units, cash_refresh_units, asset_value_units)):
        return _blocked('FINANCE_PROFILE_MONEY_INVALID')
    if not isinstance(living_standard_id, str) or not living_standard_id.strip():
        return _blocked('LIVING_STANDARD_ID_REQUIRED')
    if not _valid_bool(adapter_verified) or not adapter_verified:
        return _blocked('PRIVATE_CASH_ASSETS_ADAPTER_NOT_VERIFIED')
    return {
        'status': 'RESOLVED',
        'credit_rating': credit_rating,
        'spending_level_units': spending_level_units,
        'cash_refresh_units': cash_refresh_units,
        'asset_value_units': asset_value_units,
        'living_standard_id': living_standard_id.strip(),
        'private_table_values_embedded': False,
        'adapter_verified': True,
        'randomness_generated': False,
    }


def credit_rating_check(
    *,
    credit_rating: int,
    recorded_roll: int,
    difficulty: str,
    purpose: str,
) -> dict:
    if not _valid_int(credit_rating, 0, 99) or not _valid_die(recorded_roll, 100):
        return _blocked('CREDIT_RATING_CHECK_INPUT_INVALID')
    if purpose not in {'FINANCIAL_STATUS_GOAL', 'FIRST_IMPRESSION_APP_SUBSTITUTE'}:
        return _blocked('CREDIT_RATING_PURPOSE_UNMATERIALIZED')
    if difficulty not in {'REGULAR', 'HARD', 'EXTREME'}:
        return _blocked('CREDIT_RATING_DIFFICULTY_INVALID')
    result = core_rules.meets_difficulty(credit_rating, recorded_roll, difficulty)
    return {
        'status': 'RESOLVED',
        'purpose': purpose,
        'difficulty': difficulty,
        'credit_rating': credit_rating,
        'recorded_roll': recorded_roll,
        'level': result['level'],
        'success': result['success'],
        'experience_tick_allowed': False,
        'randomness_generated': False,
    }


def adjudicate_expenditure(
    *,
    amount_units: int,
    current_cash_units: int,
    spending_level_units: int,
    keeper_confirms_within_living_standard: bool,
) -> dict:
    if not all(_valid_money(v) for v in (amount_units, current_cash_units, spending_level_units)):
        return _blocked('EXPENDITURE_MONEY_INVALID')
    if not _valid_bool(keeper_confirms_within_living_standard):
        return _blocked('LIVING_STANDARD_GATE_INVALID')

    if keeper_confirms_within_living_standard:
        return {
            'status': 'RESOLVED',
            'bookkeeping_required': False,
            'reason': 'WITHIN_LIVING_STANDARD',
            'cash_before': current_cash_units,
            'cash_after': current_cash_units,
            'asset_or_debt_resolution_required': False,
            'randomness_generated': False,
        }
    if amount_units <= spending_level_units:
        return {
            'status': 'RESOLVED',
            'bookkeeping_required': False,
            'reason': 'AT_OR_BELOW_DAILY_SPENDING_LEVEL',
            'cash_before': current_cash_units,
            'cash_after': current_cash_units,
            'asset_or_debt_resolution_required': False,
            'randomness_generated': False,
        }
    if current_cash_units >= amount_units:
        return {
            'status': 'RESOLVED',
            'bookkeeping_required': True,
            'reason': 'ABOVE_SPENDING_LEVEL_CASH_DEDUCTION',
            'cash_before': current_cash_units,
            'cash_after': current_cash_units - amount_units,
            'cash_deduction': amount_units,
            'asset_or_debt_resolution_required': False,
            'randomness_generated': False,
        }
    return {
        'status': 'PENDING',
        'code': 'INSUFFICIENT_CASH_ASSET_OR_DEBT_RESOLUTION_REQUIRED',
        'bookkeeping_required': True,
        'cash_before': current_cash_units,
        'cash_after': current_cash_units,
        'required_total_units': amount_units,
        'cash_shortfall_units': amount_units - current_cash_units,
        'partial_cash_mutation_applied': False,
        'automatic_asset_conversion': False,
        'automatic_debt_creation': False,
        'randomness_generated': False,
    }


def adjudicate_same_day_small_purchases(
    *,
    purchase_amounts_units: list[int],
    current_cash_units: int,
    spending_level_units: int,
    keeper_combines_for_threshold: bool,
) -> dict:
    if not isinstance(purchase_amounts_units, list) or not purchase_amounts_units:
        return _blocked('PURCHASE_LIST_REQUIRED')
    if not all(_valid_money(v) for v in purchase_amounts_units):
        return _blocked('PURCHASE_AMOUNT_INVALID')
    if not _valid_money(current_cash_units) or not _valid_money(spending_level_units):
        return _blocked('PURCHASE_MONEY_INPUT_INVALID')
    if not _valid_bool(keeper_combines_for_threshold):
        return _blocked('COMBINE_GATE_INVALID')
    if any(v > spending_level_units for v in purchase_amounts_units):
        return _blocked('COMBINED_SMALL_PURCHASE_RULE_REQUIRES_EACH_ITEM_AT_OR_BELOW_LIMIT')

    total = sum(purchase_amounts_units)
    if not keeper_combines_for_threshold or total <= spending_level_units:
        return {
            'status': 'RESOLVED',
            'combined': keeper_combines_for_threshold,
            'combined_total_units': total,
            'bookkeeping_required': False,
            'cash_before': current_cash_units,
            'cash_after': current_cash_units,
            'randomness_generated': False,
        }
    if current_cash_units >= total:
        return {
            'status': 'RESOLVED',
            'combined': True,
            'combined_total_units': total,
            'bookkeeping_required': True,
            'cash_before': current_cash_units,
            'cash_after': current_cash_units - total,
            'cash_deduction': total,
            'randomness_generated': False,
        }
    return {
        'status': 'PENDING',
        'code': 'COMBINED_PURCHASES_EXCEED_CASH_ASSET_OR_DEBT_RESOLUTION_REQUIRED',
        'combined': True,
        'combined_total_units': total,
        'cash_before': current_cash_units,
        'cash_after': current_cash_units,
        'cash_shortfall_units': total - current_cash_units,
        'partial_cash_mutation_applied': False,
        'automatic_asset_conversion': False,
        'randomness_generated': False,
    }


def resolve_asset_to_cash_transfer(
    *,
    current_cash_units: int,
    current_assets_units: int,
    transfer_units: int,
    keeper_confirms_conversion_completed: bool,
) -> dict:
    if not all(_valid_money(v) for v in (current_cash_units, current_assets_units, transfer_units)):
        return _blocked('ASSET_TRANSFER_MONEY_INVALID')
    if not _valid_bool(keeper_confirms_conversion_completed):
        return _blocked('ASSET_TRANSFER_KEEPER_GATE_INVALID')
    if transfer_units > current_assets_units:
        return _blocked('ASSET_TRANSFER_EXCEEDS_ASSETS')
    if not keeper_confirms_conversion_completed:
        return {
            'status': 'PENDING',
            'code': 'ASSET_CONVERSION_TIME_KEEPER_DETERMINED',
            'cash_after': current_cash_units,
            'assets_after': current_assets_units,
            'automatic_duration_selected': False,
            'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED',
        'cash_before': current_cash_units,
        'assets_before': current_assets_units,
        'transfer_units': transfer_units,
        'cash_after': current_cash_units + transfer_units,
        'assets_after': current_assets_units - transfer_units,
        'automatic_debt_terms': False,
        'randomness_generated': False,
    }


def receive_large_sum(
    *,
    amount_units: int,
    current_cash_units: int,
    current_assets_units: int,
    destination: str,
    investment_completed: bool = False,
) -> dict:
    if not all(_valid_money(v) for v in (amount_units, current_cash_units, current_assets_units)):
        return _blocked('MONEY_IN_INPUT_INVALID')
    if not _valid_bool(investment_completed):
        return _blocked('INVESTMENT_GATE_INVALID')
    if destination == 'CASH':
        if investment_completed:
            return _blocked('INVESTMENT_GATE_UNUSED_FOR_CASH')
        return {
            'status': 'RESOLVED',
            'cash_after': current_cash_units + amount_units,
            'assets_after': current_assets_units,
            'randomness_generated': False,
        }
    if destination == 'ASSETS':
        if not investment_completed:
            return {
                'status': 'PENDING',
                'code': 'INVESTMENT_INTO_ASSETS_NOT_COMPLETED',
                'cash_after': current_cash_units,
                'assets_after': current_assets_units,
                'automatic_investment_time_selected': False,
                'randomness_generated': False,
            }
        return {
            'status': 'RESOLVED',
            'cash_after': current_cash_units,
            'assets_after': current_assets_units + amount_units,
            'randomness_generated': False,
        }
    return _blocked('MONEY_IN_DESTINATION_INVALID')


def _apply_cr_delta(current_cr: int, delta: int) -> int | None:
    after = max(0, current_cr + delta)
    if after > 99:
        return None
    return after


def development_credit_rating_change(
    *,
    current_cr: int,
    condition: str,
    keeper_confirms_condition: bool,
    recorded_dice: list[int],
    adapter_bracket_verified: bool = False,
    target_bracket_min: int | None = None,
    target_bracket_max: int | None = None,
    state_safety_net: bool = False,
    safety_net_d10: int | None = None,
) -> dict:
    if not _valid_int(current_cr, 0, 99) or not _valid_bool(keeper_confirms_condition):
        return _blocked('CREDIT_RATING_CHANGE_INPUT_INVALID')
    if not isinstance(recorded_dice, list) or not _valid_bool(adapter_bracket_verified) or not _valid_bool(state_safety_net):
        return _blocked('CREDIT_RATING_CHANGE_GATE_INVALID')
    if condition not in {
        'HIGHER_ASSET_BRACKET', 'PROMOTION', 'STATUS_QUO', 'DEMOTION_OR_UNPAID_LEAVE',
        'ASSETS_MATCH_LOWER_BRACKET', 'MAIN_INCOME_LOST', 'CRASH'
    }:
        return _blocked('CREDIT_RATING_CONDITION_UNMATERIALIZED')

    if condition == 'STATUS_QUO':
        if keeper_confirms_condition is not True or recorded_dice or adapter_bracket_verified or target_bracket_min is not None or target_bracket_max is not None or state_safety_net or safety_net_d10 is not None:
            return _blocked('STATUS_QUO_MUST_NOT_CONSUME_CHANGE_INPUTS')
        return {
            'status': 'RESOLVED', 'condition': condition,
            'credit_rating_before': current_cr, 'credit_rating_after': current_cr,
            'randomness_generated': False,
        }
    if not keeper_confirms_condition:
        return _blocked('KEEPER_CREDIT_RATING_CHANGE_GATE_REQUIRED')

    if condition == 'HIGHER_ASSET_BRACKET':
        if not adapter_bracket_verified:
            return _blocked('HIGHER_BRACKET_PRIVATE_ADAPTER_GATE_REQUIRED')
        if not _valid_int(target_bracket_min, 0, 99) or not _valid_int(target_bracket_max, 0, 99) or target_bracket_min > target_bracket_max:
            return _blocked('TARGET_BRACKET_INVALID')
        if state_safety_net or safety_net_d10 is not None:
            return _blocked('SAFETY_NET_INPUT_UNUSED')
        if target_bracket_min <= current_cr <= target_bracket_max:
            if recorded_dice:
                return _blocked('ALREADY_IN_TARGET_BRACKET_MUST_NOT_CONSUME_DICE')
            return {
                'status': 'RESOLVED', 'condition': condition,
                'credit_rating_before': current_cr, 'credit_rating_after': current_cr,
                'recorded_dice': [], 'target_bracket': [target_bracket_min, target_bracket_max],
                'randomness_generated': False,
            }
        if current_cr > target_bracket_max:
            return _blocked('HIGHER_BRACKET_NOT_ABOVE_CURRENT_CREDIT_RATING')
        cr = current_cr
        used = []
        for idx, die in enumerate(recorded_dice):
            if not _valid_die(die, 10):
                return _blocked('RECORDED_D10_INVALID', index=idx)
            cr += die
            used.append(die)
            if cr > 99:
                return _blocked('CREDIT_RATING_ABOVE_99_UNMATERIALIZED')
            if cr > target_bracket_max:
                return _blocked('TARGET_BRACKET_OVERSHOOT_UNMATERIALIZED')
            if target_bracket_min <= cr <= target_bracket_max:
                if idx != len(recorded_dice) - 1:
                    return _blocked('EXTRA_D10_AFTER_TARGET_BRACKET_REACHED')
                return {
                    'status': 'RESOLVED', 'condition': condition,
                    'credit_rating_before': current_cr, 'credit_rating_after': cr,
                    'recorded_dice': used, 'target_bracket': [target_bracket_min, target_bracket_max],
                    'randomness_generated': False,
                }
        return _blocked('MORE_D10_REQUIRED_TO_REACH_TARGET_BRACKET', credit_rating_reached=cr)

    if adapter_bracket_verified or target_bracket_min is not None or target_bracket_max is not None:
        if condition != 'ASSETS_MATCH_LOWER_BRACKET':
            return _blocked('BRACKET_INPUT_UNUSED')

    if condition == 'PROMOTION':
        if len(recorded_dice) != 1 or not _valid_die(recorded_dice[0], 6):
            return _blocked('PROMOTION_REQUIRES_EXACT_RECORDED_D6')
        if state_safety_net or safety_net_d10 is not None:
            return _blocked('SAFETY_NET_INPUT_UNUSED')
        after = _apply_cr_delta(current_cr, recorded_dice[0])
        if after is None:
            return _blocked('CREDIT_RATING_ABOVE_99_UNMATERIALIZED')

    elif condition in {'DEMOTION_OR_UNPAID_LEAVE', 'ASSETS_MATCH_LOWER_BRACKET'}:
        if len(recorded_dice) != 1 or not _valid_die(recorded_dice[0], 10):
            return _blocked('DECREASE_REQUIRES_EXACT_RECORDED_D10')
        if condition == 'ASSETS_MATCH_LOWER_BRACKET' and not adapter_bracket_verified:
            return _blocked('LOWER_BRACKET_PRIVATE_ADAPTER_GATE_REQUIRED')
        if state_safety_net or safety_net_d10 is not None:
            return _blocked('SAFETY_NET_INPUT_UNUSED')
        after = max(0, current_cr - recorded_dice[0])

    elif condition == 'MAIN_INCOME_LOST':
        if len(recorded_dice) != 2 or not all(_valid_die(v, 10) for v in recorded_dice):
            return _blocked('MAIN_INCOME_LOST_REQUIRES_EXACT_RECORDED_2D10')
        raw_after = max(0, current_cr - sum(recorded_dice))
        if state_safety_net:
            if not _valid_die(safety_net_d10, 10):
                return _blocked('SAFETY_NET_REQUIRES_RECORDED_D10')
            floor = safety_net_d10 - 1
            after = max(raw_after, floor)
        else:
            if safety_net_d10 is not None:
                return _blocked('SAFETY_NET_D10_UNUSED')
            floor = None
            after = raw_after

    else:  # CRASH
        if len(recorded_dice) != 1 or not _valid_die(recorded_dice[0], 100):
            return _blocked('CRASH_REQUIRES_EXACT_RECORDED_D100')
        if state_safety_net or safety_net_d10 is not None:
            return _blocked('SAFETY_NET_INPUT_UNUSED')
        after = max(0, current_cr - recorded_dice[0])

    return {
        'status': 'RESOLVED',
        'condition': condition,
        'credit_rating_before': current_cr,
        'credit_rating_after': after,
        'recorded_dice': list(recorded_dice),
        'state_safety_net': state_safety_net,
        'safety_net_floor': floor if condition == 'MAIN_INCOME_LOST' else None,
        'minimum_credit_rating_zero': True,
        'randomness_generated': False,
    }


def refresh_development_finances(
    *,
    credit_rating_before: int,
    credit_rating_after: int,
    current_cash_units: int,
    current_assets_units: int,
    adapter_cash_refresh_units: int,
    adapter_verified: bool,
    adapter_recalculated_asset_value_units: int | None = None,
) -> dict:
    if not _valid_int(credit_rating_before, 0, 99) or not _valid_int(credit_rating_after, 0, 99):
        return _blocked('FINANCE_REFRESH_CREDIT_RATING_INVALID')
    if not all(_valid_money(v) for v in (current_cash_units, current_assets_units, adapter_cash_refresh_units)):
        return _blocked('FINANCE_REFRESH_MONEY_INVALID')
    if not _valid_bool(adapter_verified) or not adapter_verified:
        return _blocked('PRIVATE_CASH_ASSETS_ADAPTER_NOT_VERIFIED')

    cr_changed = credit_rating_before != credit_rating_after
    if cr_changed:
        if not _valid_money(adapter_recalculated_asset_value_units):
            return _blocked('RECALCULATED_ASSET_VALUE_REQUIRED_AFTER_CR_CHANGE')
        assets_after = adapter_recalculated_asset_value_units
    else:
        if adapter_recalculated_asset_value_units is not None:
            return _blocked('UNCHANGED_CR_MUST_NOT_SILENTLY_RECALCULATE_ASSETS')
        assets_after = current_assets_units

    return {
        'status': 'RESOLVED',
        'credit_rating_before': credit_rating_before,
        'credit_rating_after': credit_rating_after,
        'cash_before': current_cash_units,
        'cash_refresh_added_units': adapter_cash_refresh_units,
        'cash_after': current_cash_units + adapter_cash_refresh_units,
        'assets_before': current_assets_units,
        'assets_after': assets_after,
        'asset_value_recalculated_from_private_adapter': cr_changed,
        'private_table_values_embedded': False,
        'randomness_generated': False,
    }
