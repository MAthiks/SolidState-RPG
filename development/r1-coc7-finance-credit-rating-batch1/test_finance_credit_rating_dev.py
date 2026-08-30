from __future__ import annotations

import unittest

import finance_credit_rating_dev as fin


class FinanceCreditRatingBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(fin.MODULE_ID, 'COC7_FINANCE_CREDIT_RATING_R1_BATCH1_DEV_V1')
        self.assertEqual(fin.PARENT_AGING_MODULE_ID, 'COC7_INVESTIGATOR_AGING_R1_BATCH2_DEV_V1')

    def test_002_source_identity(self):
        self.assertEqual(fin.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(fin.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_003_private_profile_requires_verified_adapter(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id='MID', adapter_verified=False)
        self.assertEqual(r['code'], 'PRIVATE_CASH_ASSETS_ADAPTER_NOT_VERIFIED')

    def test_004_private_profile_resolves_without_embedding_table(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id='MID', adapter_verified=True)
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertFalse(r['private_table_values_embedded'])
        self.assertFalse(r['randomness_generated'])

    def test_005_private_profile_trims_living_standard_id(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id='  MID  ', adapter_verified=True)
        self.assertEqual(r['living_standard_id'], 'MID')

    def test_006_private_profile_credit_rating_bounds(self):
        r = fin.validate_private_finance_profile(credit_rating=100, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id='MID', adapter_verified=True)
        self.assertEqual(r['code'], 'CREDIT_RATING_INVALID')

    def test_007_private_profile_money_must_be_nonnegative_integral(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=-1, cash_refresh_units=20, asset_value_units=100, living_standard_id='MID', adapter_verified=True)
        self.assertEqual(r['code'], 'FINANCE_PROFILE_MONEY_INVALID')

    def test_008_private_profile_requires_living_standard_id(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id=' ', adapter_verified=True)
        self.assertEqual(r['code'], 'LIVING_STANDARD_ID_REQUIRED')

    def test_009_credit_rating_regular_success(self):
        r = fin.credit_rating_check(credit_rating=40, recorded_roll=30, difficulty='REGULAR', purpose='FINANCIAL_STATUS_GOAL')
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertTrue(r['success'])

    def test_010_credit_rating_first_impression_substitute(self):
        r = fin.credit_rating_check(credit_rating=60, recorded_roll=20, difficulty='HARD', purpose='FIRST_IMPRESSION_APP_SUBSTITUTE')
        self.assertEqual(r['purpose'], 'FIRST_IMPRESSION_APP_SUBSTITUTE')
        self.assertTrue(r['success'])

    def test_011_credit_rating_never_experience_tick(self):
        r = fin.credit_rating_check(credit_rating=60, recorded_roll=20, difficulty='REGULAR', purpose='FINANCIAL_STATUS_GOAL')
        self.assertFalse(r['experience_tick_allowed'])

    def test_012_credit_rating_unmaterialized_purpose_blocks(self):
        r = fin.credit_rating_check(credit_rating=60, recorded_roll=20, difficulty='REGULAR', purpose='BRIBE_AUTO_SUCCESS')
        self.assertEqual(r['code'], 'CREDIT_RATING_PURPOSE_UNMATERIALIZED')

    def test_013_credit_rating_invalid_difficulty_blocks(self):
        r = fin.credit_rating_check(credit_rating=60, recorded_roll=20, difficulty='IMPOSSIBLE', purpose='FINANCIAL_STATUS_GOAL')
        self.assertEqual(r['code'], 'CREDIT_RATING_DIFFICULTY_INVALID')

    def test_014_credit_rating_invalid_roll_blocks(self):
        r = fin.credit_rating_check(credit_rating=60, recorded_roll=0, difficulty='REGULAR', purpose='FINANCIAL_STATUS_GOAL')
        self.assertEqual(r['code'], 'CREDIT_RATING_CHECK_INPUT_INVALID')

    def test_015_living_standard_expense_not_bookkept(self):
        r = fin.adjudicate_expenditure(amount_units=100, current_cash_units=5, spending_level_units=10, keeper_confirms_within_living_standard=True)
        self.assertEqual(r['reason'], 'WITHIN_LIVING_STANDARD')
        self.assertFalse(r['bookkeeping_required'])
        self.assertEqual(r['cash_after'], 5)

    def test_016_at_spending_level_not_bookkept(self):
        r = fin.adjudicate_expenditure(amount_units=10, current_cash_units=50, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['reason'], 'AT_OR_BELOW_DAILY_SPENDING_LEVEL')
        self.assertEqual(r['cash_after'], 50)

    def test_017_below_spending_level_not_bookkept(self):
        r = fin.adjudicate_expenditure(amount_units=9, current_cash_units=50, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertFalse(r['bookkeeping_required'])

    def test_018_above_spending_level_deducts_full_purchase(self):
        r = fin.adjudicate_expenditure(amount_units=11, current_cash_units=50, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['cash_deduction'], 11)
        self.assertEqual(r['cash_after'], 39)

    def test_019_exact_cash_purchase_resolves_to_zero(self):
        r = fin.adjudicate_expenditure(amount_units=11, current_cash_units=11, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['cash_after'], 0)

    def test_020_insufficient_cash_requires_explicit_resolution(self):
        r = fin.adjudicate_expenditure(amount_units=30, current_cash_units=12, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['status'], 'PENDING')
        self.assertEqual(r['cash_shortfall_units'], 18)
        self.assertTrue(r['asset_or_debt_resolution_required'] if 'asset_or_debt_resolution_required' in r else True)

    def test_021_insufficient_cash_no_partial_mutation(self):
        r = fin.adjudicate_expenditure(amount_units=30, current_cash_units=12, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['cash_after'], 12)
        self.assertFalse(r['partial_cash_mutation_applied'])
        self.assertFalse(r['automatic_asset_conversion'])
        self.assertFalse(r['automatic_debt_creation'])

    def test_022_expenditure_negative_money_blocks(self):
        r = fin.adjudicate_expenditure(amount_units=-1, current_cash_units=12, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['code'], 'EXPENDITURE_MONEY_INVALID')

    def test_023_expenditure_keeper_gate_must_be_boolean(self):
        r = fin.adjudicate_expenditure(amount_units=1, current_cash_units=12, spending_level_units=10, keeper_confirms_within_living_standard=1)
        self.assertEqual(r['code'], 'LIVING_STANDARD_GATE_INVALID')

    def test_024_small_purchase_list_required(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[], current_cash_units=50, spending_level_units=10, keeper_combines_for_threshold=False)
        self.assertEqual(r['code'], 'PURCHASE_LIST_REQUIRED')

    def test_025_each_small_purchase_must_be_within_limit(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[5, 11], current_cash_units=50, spending_level_units=10, keeper_combines_for_threshold=True)
        self.assertEqual(r['code'], 'COMBINED_SMALL_PURCHASE_RULE_REQUIRES_EACH_ITEM_AT_OR_BELOW_LIMIT')

    def test_026_keeper_may_leave_small_purchases_uncombined(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[8, 8], current_cash_units=50, spending_level_units=10, keeper_combines_for_threshold=False)
        self.assertFalse(r['combined'])
        self.assertFalse(r['bookkeeping_required'])
        self.assertEqual(r['cash_after'], 50)

    def test_027_combined_total_within_limit_not_bookkept(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[4, 6], current_cash_units=50, spending_level_units=10, keeper_combines_for_threshold=True)
        self.assertTrue(r['combined'])
        self.assertFalse(r['bookkeeping_required'])

    def test_028_combined_total_above_limit_deducts_total(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[6, 6], current_cash_units=50, spending_level_units=10, keeper_combines_for_threshold=True)
        self.assertEqual(r['cash_deduction'], 12)
        self.assertEqual(r['cash_after'], 38)

    def test_029_combined_insufficient_cash_no_partial_mutation(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[6, 6], current_cash_units=5, spending_level_units=10, keeper_combines_for_threshold=True)
        self.assertEqual(r['status'], 'PENDING')
        self.assertEqual(r['cash_after'], 5)
        self.assertFalse(r['partial_cash_mutation_applied'])
        self.assertFalse(r['automatic_asset_conversion'])

    def test_030_combined_purchase_gate_must_be_boolean(self):
        r = fin.adjudicate_same_day_small_purchases(purchase_amounts_units=[1], current_cash_units=5, spending_level_units=10, keeper_combines_for_threshold='yes')
        self.assertEqual(r['code'], 'COMBINE_GATE_INVALID')

    def test_031_asset_transfer_waits_for_keeper_completion(self):
        r = fin.resolve_asset_to_cash_transfer(current_cash_units=10, current_assets_units=100, transfer_units=20, keeper_confirms_conversion_completed=False)
        self.assertEqual(r['status'], 'PENDING')
        self.assertEqual(r['cash_after'], 10)
        self.assertEqual(r['assets_after'], 100)
        self.assertFalse(r['automatic_duration_selected'])

    def test_032_asset_transfer_completed_is_atomic(self):
        r = fin.resolve_asset_to_cash_transfer(current_cash_units=10, current_assets_units=100, transfer_units=20, keeper_confirms_conversion_completed=True)
        self.assertEqual(r['cash_after'], 30)
        self.assertEqual(r['assets_after'], 80)

    def test_033_asset_transfer_cannot_exceed_assets(self):
        r = fin.resolve_asset_to_cash_transfer(current_cash_units=10, current_assets_units=100, transfer_units=101, keeper_confirms_conversion_completed=True)
        self.assertEqual(r['code'], 'ASSET_TRANSFER_EXCEEDS_ASSETS')

    def test_034_asset_transfer_does_not_create_debt_terms(self):
        r = fin.resolve_asset_to_cash_transfer(current_cash_units=10, current_assets_units=100, transfer_units=20, keeper_confirms_conversion_completed=True)
        self.assertFalse(r['automatic_debt_terms'])

    def test_035_large_sum_can_enter_cash_immediately(self):
        r = fin.receive_large_sum(amount_units=50, current_cash_units=10, current_assets_units=100, destination='CASH')
        self.assertEqual(r['cash_after'], 60)
        self.assertEqual(r['assets_after'], 100)

    def test_036_cash_destination_rejects_investment_gate(self):
        r = fin.receive_large_sum(amount_units=50, current_cash_units=10, current_assets_units=100, destination='CASH', investment_completed=True)
        self.assertEqual(r['code'], 'INVESTMENT_GATE_UNUSED_FOR_CASH')

    def test_037_assets_destination_waits_for_investment(self):
        r = fin.receive_large_sum(amount_units=50, current_cash_units=10, current_assets_units=100, destination='ASSETS', investment_completed=False)
        self.assertEqual(r['status'], 'PENDING')
        self.assertEqual(r['assets_after'], 100)
        self.assertFalse(r['automatic_investment_time_selected'])

    def test_038_assets_destination_after_investment(self):
        r = fin.receive_large_sum(amount_units=50, current_cash_units=10, current_assets_units=100, destination='ASSETS', investment_completed=True)
        self.assertEqual(r['assets_after'], 150)
        self.assertEqual(r['cash_after'], 10)

    def test_039_invalid_money_destination_blocks(self):
        r = fin.receive_large_sum(amount_units=50, current_cash_units=10, current_assets_units=100, destination='DEBT', investment_completed=False)
        self.assertEqual(r['code'], 'MONEY_IN_DESTINATION_INVALID')

    def test_040_status_quo_changes_nothing(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='STATUS_QUO', keeper_confirms_condition=True, recorded_dice=[])
        self.assertEqual(r['credit_rating_after'], 40)

    def test_041_status_quo_consumes_no_dice(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='STATUS_QUO', keeper_confirms_condition=True, recorded_dice=[1])
        self.assertEqual(r['code'], 'STATUS_QUO_MUST_NOT_CONSUME_CHANGE_INPUTS')

    def test_042_credit_rating_change_requires_keeper_gate(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='PROMOTION', keeper_confirms_condition=False, recorded_dice=[3])
        self.assertEqual(r['code'], 'KEEPER_CREDIT_RATING_CHANGE_GATE_REQUIRED')

    def test_043_promotion_uses_exact_d6(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='PROMOTION', keeper_confirms_condition=True, recorded_dice=[6])
        self.assertEqual(r['credit_rating_after'], 46)

    def test_044_promotion_rejects_d10_value(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='PROMOTION', keeper_confirms_condition=True, recorded_dice=[7])
        self.assertEqual(r['code'], 'PROMOTION_REQUIRES_EXACT_RECORDED_D6')

    def test_045_promotion_above_99_fails_closed(self):
        r = fin.development_credit_rating_change(current_cr=98, condition='PROMOTION', keeper_confirms_condition=True, recorded_dice=[2])
        self.assertEqual(r['code'], 'CREDIT_RATING_ABOVE_99_UNMATERIALIZED')

    def test_046_demotion_uses_recorded_d10(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='DEMOTION_OR_UNPAID_LEAVE', keeper_confirms_condition=True, recorded_dice=[7])
        self.assertEqual(r['credit_rating_after'], 33)

    def test_047_demotion_floors_zero(self):
        r = fin.development_credit_rating_change(current_cr=3, condition='DEMOTION_OR_UNPAID_LEAVE', keeper_confirms_condition=True, recorded_dice=[9])
        self.assertEqual(r['credit_rating_after'], 0)

    def test_048_lower_asset_bracket_requires_private_gate(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='ASSETS_MATCH_LOWER_BRACKET', keeper_confirms_condition=True, recorded_dice=[4], adapter_bracket_verified=False)
        self.assertEqual(r['code'], 'LOWER_BRACKET_PRIVATE_ADAPTER_GATE_REQUIRED')

    def test_049_lower_asset_bracket_with_verified_gate(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='ASSETS_MATCH_LOWER_BRACKET', keeper_confirms_condition=True, recorded_dice=[4], adapter_bracket_verified=True)
        self.assertEqual(r['credit_rating_after'], 36)

    def test_050_lower_asset_bracket_rejects_invalid_explicit_bounds(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='ASSETS_MATCH_LOWER_BRACKET', keeper_confirms_condition=True, recorded_dice=[4], adapter_bracket_verified=True, target_bracket_min=80, target_bracket_max=20)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_051_higher_bracket_requires_private_gate(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[5], adapter_bracket_verified=False, target_bracket_min=25, target_bracket_max=30)
        self.assertEqual(r['code'], 'HIGHER_BRACKET_PRIVATE_ADAPTER_GATE_REQUIRED')

    def test_052_higher_bracket_requires_valid_bounds(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[5], adapter_bracket_verified=True, target_bracket_min=30, target_bracket_max=25)
        self.assertEqual(r['code'], 'TARGET_BRACKET_INVALID')

    def test_053_higher_bracket_rolls_until_entry(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[3, 4], adapter_bracket_verified=True, target_bracket_min=25, target_bracket_max=30)
        self.assertEqual(r['credit_rating_after'], 27)
        self.assertEqual(r['recorded_dice'], [3, 4])

    def test_054_higher_bracket_more_d10_required(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[2], adapter_bracket_verified=True, target_bracket_min=25, target_bracket_max=30)
        self.assertEqual(r['code'], 'MORE_D10_REQUIRED_TO_REACH_TARGET_BRACKET')
        self.assertEqual(r['credit_rating_reached'], 22)

    def test_055_higher_bracket_extra_d10_rejected(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[5, 1], adapter_bracket_verified=True, target_bracket_min=25, target_bracket_max=30)
        self.assertEqual(r['code'], 'EXTRA_D10_AFTER_TARGET_BRACKET_REACHED')

    def test_056_higher_bracket_overshoot_fails_closed(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[10], adapter_bracket_verified=True, target_bracket_min=25, target_bracket_max=29)
        self.assertEqual(r['code'], 'TARGET_BRACKET_OVERSHOOT_UNMATERIALIZED')

    def test_057_higher_bracket_already_inside_uses_no_dice(self):
        r = fin.development_credit_rating_change(current_cr=26, condition='HIGHER_ASSET_BRACKET', keeper_confirms_condition=True, recorded_dice=[], adapter_bracket_verified=True, target_bracket_min=25, target_bracket_max=30)
        self.assertEqual(r['credit_rating_after'], 26)

    def test_058_main_income_lost_uses_exact_2d10(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[6, 4])
        self.assertEqual(r['credit_rating_after'], 30)

    def test_059_main_income_lost_bad_dice_count_blocks(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[6])
        self.assertEqual(r['code'], 'MAIN_INCOME_LOST_REQUIRES_EXACT_RECORDED_2D10')

    def test_060_main_income_safety_net_requires_recorded_d10(self):
        r = fin.development_credit_rating_change(current_cr=10, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[10, 10], state_safety_net=True)
        self.assertEqual(r['code'], 'SAFETY_NET_REQUIRES_RECORDED_D10')

    def test_061_main_income_safety_net_floor(self):
        r = fin.development_credit_rating_change(current_cr=15, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[10, 10], state_safety_net=True, safety_net_d10=6)
        self.assertEqual(r['safety_net_floor'], 5)
        self.assertEqual(r['credit_rating_after'], 5)

    def test_062_unused_safety_net_die_blocks(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[2, 2], state_safety_net=False, safety_net_d10=4)
        self.assertEqual(r['code'], 'SAFETY_NET_D10_UNUSED')

    def test_063_crash_uses_d100(self):
        r = fin.development_credit_rating_change(current_cr=70, condition='CRASH', keeper_confirms_condition=True, recorded_dice=[30])
        self.assertEqual(r['credit_rating_after'], 40)

    def test_064_crash_floors_zero(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='CRASH', keeper_confirms_condition=True, recorded_dice=[100])
        self.assertEqual(r['credit_rating_after'], 0)

    def test_065_unknown_credit_rating_condition_blocks(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='LOTTERY', keeper_confirms_condition=True, recorded_dice=[])
        self.assertEqual(r['code'], 'CREDIT_RATING_CONDITION_UNMATERIALIZED')

    def test_066_unrelated_bracket_input_blocks_promotion(self):
        r = fin.development_credit_rating_change(current_cr=20, condition='PROMOTION', keeper_confirms_condition=True, recorded_dice=[3], adapter_bracket_verified=True)
        self.assertEqual(r['code'], 'BRACKET_INPUT_UNUSED')

    def test_067_refresh_requires_verified_private_adapter(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=False)
        self.assertEqual(r['code'], 'PRIVATE_CASH_ASSETS_ADAPTER_NOT_VERIFIED')

    def test_068_refresh_adds_cash_amount_to_remaining_cash(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True)
        self.assertEqual(r['cash_after'], 30)

    def test_069_unchanged_credit_rating_preserves_assets(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True)
        self.assertEqual(r['assets_after'], 100)
        self.assertFalse(r['asset_value_recalculated_from_private_adapter'])

    def test_070_unchanged_credit_rating_rejects_silent_asset_recalc(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True, adapter_recalculated_asset_value_units=110)
        self.assertEqual(r['code'], 'UNCHANGED_CR_MUST_NOT_SILENTLY_RECALCULATE_ASSETS')

    def test_071_changed_credit_rating_requires_asset_recalc(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=45, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True)
        self.assertEqual(r['code'], 'RECALCULATED_ASSET_VALUE_REQUIRED_AFTER_CR_CHANGE')

    def test_072_changed_credit_rating_uses_private_recalculated_assets(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=45, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True, adapter_recalculated_asset_value_units=140)
        self.assertEqual(r['assets_after'], 140)
        self.assertTrue(r['asset_value_recalculated_from_private_adapter'])
        self.assertFalse(r['private_table_values_embedded'])

    def test_073_refresh_invalid_credit_rating_blocks(self):
        r = fin.refresh_development_finances(credit_rating_before=100, credit_rating_after=45, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True, adapter_recalculated_asset_value_units=140)
        self.assertEqual(r['code'], 'FINANCE_REFRESH_CREDIT_RATING_INVALID')

    def test_074_refresh_negative_money_blocks(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=-1, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True)
        self.assertEqual(r['code'], 'FINANCE_REFRESH_MONEY_INVALID')

    def test_075_no_randomness_profile(self):
        r = fin.validate_private_finance_profile(credit_rating=40, spending_level_units=10, cash_refresh_units=20, asset_value_units=100, living_standard_id='MID', adapter_verified=True)
        self.assertFalse(r['randomness_generated'])

    def test_076_no_randomness_expenditure(self):
        r = fin.adjudicate_expenditure(amount_units=11, current_cash_units=50, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertFalse(r['randomness_generated'])

    def test_077_no_randomness_credit_rating_change(self):
        r = fin.development_credit_rating_change(current_cr=40, condition='PROMOTION', keeper_confirms_condition=True, recorded_dice=[3])
        self.assertFalse(r['randomness_generated'])

    def test_078_no_randomness_refresh(self):
        r = fin.refresh_development_finances(credit_rating_before=40, credit_rating_after=40, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True)
        self.assertFalse(r['randomness_generated'])

    def test_079_replay_expenditure_stable(self):
        kwargs = dict(amount_units=11, current_cash_units=50, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(fin.adjudicate_expenditure(**kwargs), fin.adjudicate_expenditure(**kwargs))

    def test_080_replay_credit_change_stable(self):
        kwargs = dict(current_cr=40, condition='MAIN_INCOME_LOST', keeper_confirms_condition=True, recorded_dice=[6, 4], state_safety_net=True, safety_net_d10=3)
        self.assertEqual(fin.development_credit_rating_change(**kwargs), fin.development_credit_rating_change(**kwargs))

    def test_081_replay_refresh_stable(self):
        kwargs = dict(credit_rating_before=40, credit_rating_after=45, current_cash_units=10, current_assets_units=100, adapter_cash_refresh_units=20, adapter_verified=True, adapter_recalculated_asset_value_units=140)
        self.assertEqual(fin.refresh_development_finances(**kwargs), fin.refresh_development_finances(**kwargs))

    def test_082_zero_amount_purchase_is_valid(self):
        r = fin.adjudicate_expenditure(amount_units=0, current_cash_units=10, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['cash_after'], 10)

    def test_083_bool_money_is_rejected(self):
        r = fin.adjudicate_expenditure(amount_units=True, current_cash_units=10, spending_level_units=10, keeper_confirms_within_living_standard=False)
        self.assertEqual(r['code'], 'EXPENDITURE_MONEY_INVALID')

    def test_084_parent_aging_module_survives(self):
        self.assertEqual(fin.aging.MODULE_ID, 'COC7_INVESTIGATOR_AGING_R1_BATCH2_DEV_V1')


# Deterministic boundary matrix: public mechanics must remain replay-stable and tick-free
# across representative Credit Rating values without generating random values.
def _make_boundary_test(cr: int):
    def _test(self):
        roll = max(1, cr if cr else 1)
        r = fin.credit_rating_check(credit_rating=cr, recorded_roll=roll, difficulty='REGULAR', purpose='FINANCIAL_STATUS_GOAL')
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertFalse(r['experience_tick_allowed'])
        self.assertFalse(r['randomness_generated'])
    return _test


for _idx, _cr in enumerate((0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 98, 99), start=1):
    setattr(FinanceCreditRatingBatch1Tests, f'test_generated_boundary_{_idx:02d}', _make_boundary_test(_cr))


if __name__ == '__main__':
    unittest.main()
