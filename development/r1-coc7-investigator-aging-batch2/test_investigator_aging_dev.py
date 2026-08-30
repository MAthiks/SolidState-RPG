from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import investigator_aging_dev as a


class InvestigatorAgingBatch2Tests(unittest.TestCase):
    def _chars(self, **kw):
        base = {'STR': 80, 'CON': 80, 'DEX': 80, 'SIZ': 70, 'APP': 70, 'EDU': 60}
        base.update(kw)
        return base

    def _apply(self, **kw):
        base = dict(
            old_age=39, new_age=40, mode='NATURAL_OR_TIME_SKIP',
            current_characteristics=self._chars(), current_mov=8,
            allocations={40: {'STR': 5}},
            edu_checks={40: {'percentile': 50}},
            keeper_confirms_magical=False,
        )
        base.update(kw)
        return a.apply_aging(**base)

    def test_001_identity(self):
        self.assertEqual(a.MODULE_ID, 'COC7_INVESTIGATOR_AGING_R1_BATCH2_DEV_V1')
        self.assertEqual(a.PARENT_DEVELOPMENT_MODULE_ID, 'COC7_INVESTIGATOR_DEVELOPMENT_R1_BATCH1_DEV_V1')

    def test_002_source_identity(self):
        self.assertEqual(a.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(a.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_003_turning20_milestone(self):
        r = a.crossed_aging_milestones(old_age=19, new_age=20)
        self.assertEqual(r['milestones'], [20]); self.assertEqual(r['edu_milestones'], [20])

    def test_004_no_milestone_in_thirties(self):
        r = a.crossed_aging_milestones(old_age=21, new_age=39)
        self.assertEqual(r['milestones'], [])

    def test_005_turning40_milestone(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=39, new_age=40)['milestones'], [40])

    def test_006_two_decades_cumulative(self):
        r = a.crossed_aging_milestones(old_age=35, new_age=55)
        self.assertEqual(r['milestones'], [40, 50]); self.assertEqual(r['edu_milestones'], [40, 50])

    def test_007_through80_cumulative(self):
        r = a.crossed_aging_milestones(old_age=35, new_age=85)
        self.assertEqual(r['milestones'], [40, 50, 60, 70, 80])
        self.assertEqual(r['edu_milestones'], [40, 50, 60])

    def test_008_after80_decades_materialized(self):
        r = a.crossed_aging_milestones(old_age=75, new_age=105)
        self.assertEqual(r['milestones'], [80, 90, 100])

    def test_009_old95_to105_only100(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=95, new_age=105)['milestones'], [100])

    def test_010_age_not_advancing_blocks(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=40, new_age=40)['status'], 'BLOCKED')

    def test_011_reverse_age_blocks(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=50, new_age=40)['status'], 'BLOCKED')

    def test_012_invalid_mode_blocks(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=39, new_age=40, mode='TIME_TRAVEL')['status'], 'BLOCKED')

    def test_013_magical_requires_keeper(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=39, new_age=50, mode='SUDDEN_MAGICAL')['status'], 'BLOCKED')

    def test_014_magical_suppresses_turning20_positive(self):
        r = a.crossed_aging_milestones(old_age=19, new_age=50, mode='SUDDEN_MAGICAL', keeper_confirms_magical=True)
        self.assertEqual(r['milestones'], [40, 50]); self.assertEqual(r['edu_milestones'], [])

    def test_015_natural_rejects_magical_gate(self):
        self.assertEqual(a.crossed_aging_milestones(old_age=39, new_age=40, keeper_confirms_magical=True)['status'], 'BLOCKED')

    def test_016_edu_roll_above_improves(self):
        r = a.edu_age_improvement(current_edu=60, recorded_percentile=61, recorded_gain_d10=7)
        self.assertTrue(r['improved']); self.assertEqual(r['EDU_after'], 67)

    def test_017_edu_equal_does_not_improve(self):
        r = a.edu_age_improvement(current_edu=60, recorded_percentile=60)
        self.assertFalse(r['improved']); self.assertEqual(r['EDU_after'], 60)

    def test_018_edu_lower_does_not_improve(self):
        self.assertFalse(a.edu_age_improvement(current_edu=60, recorded_percentile=20)['improved'])

    def test_019_edu_96_not_special_at99(self):
        r = a.edu_age_improvement(current_edu=99, recorded_percentile=96)
        self.assertFalse(r['improved']); self.assertFalse(r['ordinary_skill_over_95_rule_imported'])

    def test_020_edu_100_above99_uses_d10_but_caps(self):
        r = a.edu_age_improvement(current_edu=99, recorded_percentile=100, recorded_gain_d10=10)
        self.assertTrue(r['improved']); self.assertEqual(r['uncapped_EDU_after'], 109); self.assertEqual(r['EDU_after'], 99)

    def test_021_edu_success_requires_d10(self):
        self.assertEqual(a.edu_age_improvement(current_edu=60, recorded_percentile=80)['status'], 'BLOCKED')

    def test_022_edu_failure_rejects_d10(self):
        self.assertEqual(a.edu_age_improvement(current_edu=60, recorded_percentile=40, recorded_gain_d10=5)['status'], 'BLOCKED')

    def test_023_edu_cap_input(self):
        self.assertEqual(a.edu_age_improvement(current_edu=100, recorded_percentile=100)['status'], 'BLOCKED')

    def test_024_turning20_applies_explicit_gain_and_edu(self):
        r = self._apply(
            old_age=19, new_age=20,
            allocations={20: {'STR': 3, 'SIZ': 2}},
            edu_checks={20: {'percentile': 70, 'gain_d10': 5}},
        )
        self.assertEqual(r['characteristics_after']['STR'], 83)
        self.assertEqual(r['characteristics_after']['SIZ'], 72)
        self.assertEqual(r['characteristics_after']['EDU'], 65)
        self.assertEqual(r['MOV_after'], 8)

    def test_025_turning20_requires_exact_five(self):
        r = self._apply(old_age=19, new_age=20, allocations={20: {'STR': 4}}, edu_checks={20: {'percentile': 50}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_026_turning20_rejects_wrong_stat(self):
        r = self._apply(old_age=19, new_age=20, allocations={20: {'CON': 5}}, edu_checks={20: {'percentile': 50}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_027_turning40_applies_losses(self):
        r = self._apply()
        self.assertEqual(r['characteristics_after']['STR'], 75)
        self.assertEqual(r['characteristics_after']['APP'], 65)
        self.assertEqual(r['MOV_after'], 7)

    def test_028_turning40_split_physical_loss(self):
        r = self._apply(allocations={40: {'STR': 2, 'CON': 2, 'DEX': 1}})
        self.assertEqual(r['characteristics_after']['STR'], 78)
        self.assertEqual(r['characteristics_after']['CON'], 78)
        self.assertEqual(r['characteristics_after']['DEX'], 79)

    def test_029_turning50_is_five_more(self):
        r = self._apply(
            old_age=49, new_age=50,
            allocations={50: {'DEX': 5}},
            edu_checks={50: {'percentile': 50}},
        )
        self.assertEqual(r['characteristics_after']['DEX'], 75); self.assertEqual(r['APP_after'] if 'APP_after' in r else r['characteristics_after']['APP'], 65)

    def test_030_turning60_is_ten(self):
        r = self._apply(
            old_age=59, new_age=60,
            allocations={60: {'CON': 10}},
            edu_checks={60: {'percentile': 50}},
        )
        self.assertEqual(r['characteristics_after']['CON'], 70); self.assertEqual(r['MOV_after'], 7)

    def test_031_turning70_no_edu(self):
        r = self._apply(
            old_age=69, new_age=70,
            allocations={70: {'STR': 20}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['STR'], 60); self.assertEqual(r['characteristics_after']['EDU'], 60)

    def test_032_turning80_forty(self):
        r = self._apply(
            old_age=79, new_age=80,
            allocations={80: {'DEX': 40}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['DEX'], 40); self.assertEqual(r['characteristics_after']['APP'], 65)

    def test_033_turning90_eighty_no_app_loss(self):
        chars = self._chars(STR=200)
        r = self._apply(
            old_age=89, new_age=90, current_characteristics=chars,
            allocations={90: {'STR': 80}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['STR'], 120)
        self.assertEqual(r['characteristics_after']['APP'], 70)
        self.assertEqual(r['MOV_after'], 7)

    def test_034_turning100_eighty_again(self):
        chars = self._chars(STR=300)
        r = self._apply(
            old_age=89, new_age=100, current_characteristics=chars, current_mov=8,
            allocations={90: {'STR': 80}, 100: {'STR': 80}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['STR'], 140); self.assertEqual(r['MOV_after'], 6)

    def test_035_two_decades_apply_both(self):
        r = self._apply(
            old_age=35, new_age=55,
            allocations={40: {'STR': 5}, 50: {'DEX': 5}},
            edu_checks={40: {'percentile': 61, 'gain_d10': 5}, 50: {'percentile': 66, 'gain_d10': 4}},
        )
        self.assertEqual(r['applied_milestones'], [40, 50])
        self.assertEqual(r['characteristics_after']['EDU'], 69)
        self.assertEqual(r['APP_after'] if 'APP_after' in r else r['characteristics_after']['APP'], 60)
        self.assertEqual(r['MOV_after'], 6)

    def test_036_second_edu_check_uses_updated_edu(self):
        r = self._apply(
            old_age=35, new_age=55,
            allocations={40: {'STR': 5}, 50: {'DEX': 5}},
            edu_checks={40: {'percentile': 61, 'gain_d10': 10}, 50: {'percentile': 69}},
        )
        self.assertEqual(r['characteristics_after']['EDU'], 70)
        self.assertFalse(r['events'][1]['EDU_check']['improved'])

    def test_037_three_edu_milestones_sequence(self):
        r = self._apply(
            old_age=35, new_age=65, current_characteristics=self._chars(STR=100, CON=100, DEX=100),
            allocations={40: {'STR': 5}, 50: {'DEX': 5}, 60: {'CON': 10}},
            edu_checks={40: {'percentile': 61, 'gain_d10': 5}, 50: {'percentile': 66, 'gain_d10': 5}, 60: {'percentile': 71, 'gain_d10': 5}},
        )
        self.assertEqual(r['characteristics_after']['EDU'], 75)

    def test_038_magical_aging_suppresses_edu(self):
        r = self._apply(
            old_age=39, new_age=50, mode='SUDDEN_MAGICAL', keeper_confirms_magical=True,
            allocations={40: {'STR': 5}, 50: {'DEX': 5}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['EDU'], 60)
        self.assertTrue(r['education_gain_suppressed_for_magical_aging'])

    def test_039_magical_aging_still_applies_app_mov(self):
        r = self._apply(
            old_age=39, new_age=50, mode='SUDDEN_MAGICAL', keeper_confirms_magical=True,
            allocations={40: {'STR': 5}, 50: {'DEX': 5}}, edu_checks={},
        )
        self.assertEqual(r['characteristics_after']['APP'], 60); self.assertEqual(r['MOV_after'], 6)

    def test_040_missing_allocation_blocks(self):
        r = self._apply(old_age=35, new_age=55, allocations={40: {'STR': 5}}, edu_checks={40: {'percentile': 50}, 50: {'percentile': 50}})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'MISSING_OR_EXTRA_MILESTONE_ALLOCATION')

    def test_041_extra_allocation_blocks(self):
        r = self._apply(allocations={40: {'STR': 5}, 50: {'STR': 5}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_042_missing_edu_record_blocks(self):
        r = self._apply(edu_checks={})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'MISSING_OR_EXTRA_EDU_CHECK_RECORD')

    def test_043_extra_edu_record_blocks(self):
        r = self._apply(edu_checks={40: {'percentile': 50}, 50: {'percentile': 50}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_044_allocation_total_mismatch_blocks(self):
        r = self._apply(allocations={40: {'STR': 4}})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'ALLOCATION_TOTAL_MISMATCH')

    def test_045_invalid_allocation_key_blocks(self):
        r = self._apply(allocations={40: {'SIZ': 5}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_046_negative_characteristic_blocks(self):
        r = self._apply(current_characteristics=self._chars(STR=3), allocations={40: {'STR': 5}})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'NEGATIVE_CHARACTERISTIC_WOULD_RESULT')

    def test_047_app_below_zero_fails_closed(self):
        r = self._apply(current_characteristics=self._chars(APP=3))
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'APP_REDUCTION_BELOW_ZERO_UNMATERIALIZED')

    def test_048_mov_below_zero_fails_closed(self):
        r = self._apply(current_mov=0)
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'MOV_REDUCTION_BELOW_ZERO_UNMATERIALIZED')

    def test_049_string_milestone_keys_accepted(self):
        r = self._apply(allocations={'40': {'STR': 5}}, edu_checks={'40': {'percentile': 50}})
        self.assertEqual(r['status'], 'RESOLVED')

    def test_050_duplicate_normalized_key_blocks(self):
        r = self._apply(allocations={40: {'STR': 5}, '40': {'STR': 5}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_051_bad_edu_record_extra_field_blocks(self):
        r = self._apply(edu_checks={40: {'percentile': 50, 'foo': 1}})
        self.assertEqual(r['status'], 'BLOCKED')

    def test_052_edu_gain_missing_propagates_block(self):
        r = self._apply(edu_checks={40: {'percentile': 80}})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'UNRECORDED_EDU_GAIN_D10')

    def test_053_edu_unused_gain_propagates_block(self):
        r = self._apply(edu_checks={40: {'percentile': 50, 'gain_d10': 3}})
        self.assertEqual(r['status'], 'BLOCKED'); self.assertEqual(r['code'], 'UNUSED_EDU_GAIN_D10')

    def test_054_hp_recalculation_when_con_changes(self):
        r = self._apply(allocations={40: {'CON': 5}})
        self.assertTrue(r['HP_recalculation_required']); self.assertEqual(r['derived_HP_after'], (75 + 70) // 10)

    def test_055_hp_recalculation_when_siz_changes_turn20(self):
        r = self._apply(old_age=19, new_age=20, allocations={20: {'SIZ': 5}}, edu_checks={20: {'percentile': 50}})
        self.assertTrue(r['HP_recalculation_required']); self.assertEqual(r['derived_HP_after'], (80 + 75) // 10)

    def test_056_hp_no_recalc_when_only_str_changes(self):
        r = self._apply(allocations={40: {'STR': 5}})
        self.assertFalse(r['HP_recalculation_required'])

    def test_057_db_build_recalc_when_str_changes(self):
        self.assertTrue(self._apply(allocations={40: {'STR': 5}})['damage_bonus_build_recalculation_required'])

    def test_058_db_build_recalc_when_siz_changes(self):
        r = self._apply(old_age=19, new_age=20, allocations={20: {'SIZ': 5}}, edu_checks={20: {'percentile': 50}})
        self.assertTrue(r['damage_bonus_build_recalculation_required'])

    def test_059_no_auto_current_hp_reconciliation(self):
        self.assertTrue(self._apply(allocations={40: {'CON': 5}})['current_HP_reconciliation_not_automated'])

    def test_060_no_auto_stat_selection(self):
        self.assertFalse(self._apply()['automatic_stat_selection'])

    def test_061_no_randomness_milestones(self):
        self.assertFalse(a.crossed_aging_milestones(old_age=39, new_age=40)['randomness_generated'])

    def test_062_no_randomness_edu(self):
        self.assertFalse(a.edu_age_improvement(current_edu=60, recorded_percentile=50)['randomness_generated'])

    def test_063_no_randomness_apply(self):
        self.assertFalse(self._apply()['randomness_generated'])

    def test_064_apply_replay_stable(self):
        args = dict(
            old_age=35, new_age=55, mode='NATURAL_OR_TIME_SKIP', current_characteristics=self._chars(), current_mov=8,
            allocations={40: {'STR': 5}, 50: {'DEX': 5}},
            edu_checks={40: {'percentile': 50}, 50: {'percentile': 50}}, keeper_confirms_magical=False,
        )
        self.assertEqual(a.apply_aging(**args), a.apply_aging(**args))

    def test_065_no_milestone_apply_is_noop(self):
        r = self._apply(old_age=21, new_age=39, allocations={}, edu_checks={})
        self.assertEqual(r['applied_milestones'], []); self.assertEqual(r['MOV_after'], 8); self.assertEqual(r['characteristics_after'], self._chars())

    def test_066_very_old_age_requires_each_decade(self):
        r = a.crossed_aging_milestones(old_age=89, new_age=121)
        self.assertEqual(r['milestones'], [90, 100, 110, 120])


def _safe_alloc(age):
    if age == 20:
        return {'STR': 5}
    points = {40: 5, 50: 5, 60: 10, 70: 20, 80: 40}.get(age, 80)
    return {'STR': points}


def _edu_records(milestones, start=60):
    # All fail intentionally so no D10 is required, keeping generated cases deterministic.
    return {age: {'percentile': 1} for age in milestones if age in {20, 40, 50, 60}}


def _add_generated_tests():
    cases = []
    for old, new, expected in [
        (19, 20, [20]), (20, 39, []), (39, 40, [40]), (40, 49, []),
        (49, 50, [50]), (59, 60, [60]), (69, 70, [70]), (79, 80, [80]),
        (89, 90, [90]), (90, 99, []), (99, 100, [100]), (85, 115, [90, 100, 110]),
    ]:
        cases.append(('milestones', old, new, expected))
    for edu, roll, improves in [
        (20, 20, False), (20, 21, True), (50, 50, False), (50, 51, True),
        (95, 95, False), (95, 96, True), (98, 99, True), (99, 99, False), (99, 100, True),
    ]:
        cases.append(('edu', edu, roll, improves))
    for old, new in [(39, 40), (49, 50), (59, 60), (69, 70), (79, 80), (89, 90), (99, 100)]:
        cases.append(('apply', old, new))

    for i, case in enumerate(cases, 1):
        def make_test(case):
            def test(self):
                if case[0] == 'milestones':
                    _, old, new, expected = case
                    self.assertEqual(a.crossed_aging_milestones(old_age=old, new_age=new)['milestones'], expected)
                elif case[0] == 'edu':
                    _, edu, roll, expected = case
                    gain = 1 if expected else None
                    r = a.edu_age_improvement(current_edu=edu, recorded_percentile=roll, recorded_gain_d10=gain)
                    self.assertEqual(r['improved'], expected)
                else:
                    _, old, new = case
                    plan = a.crossed_aging_milestones(old_age=old, new_age=new)
                    alloc = {m: _safe_alloc(m) for m in plan['allocation_milestones']}
                    edu = _edu_records(plan['edu_milestones'])
                    r = a.apply_aging(
                        old_age=old, new_age=new, mode='NATURAL_OR_TIME_SKIP',
                        current_characteristics={'STR': 500, 'CON': 500, 'DEX': 500, 'SIZ': 100, 'APP': 100, 'EDU': 60},
                        current_mov=20, allocations=alloc, edu_checks=edu,
                    )
                    self.assertEqual(r['status'], 'RESOLVED')
                    self.assertEqual(r['applied_milestones'], plan['milestones'])
            return test
        setattr(InvestigatorAgingBatch2Tests, f'test_generated_{i:02d}', make_test(case))


_add_generated_tests()

if __name__ == '__main__':
    unittest.main()
