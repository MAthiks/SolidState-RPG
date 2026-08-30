from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import investigator_development_dev as d


class InvestigatorDevelopmentBatch1Tests(unittest.TestCase):
    def _tick(self, **kw):
        base = dict(
            skill_id='LIBRARY_USE', roll_success=True, used_bonus_die=False,
            luck_spent_on_roll=False, opposed_roll=False, opposed_winner=None,
            already_checked=False,
        )
        base.update(kw)
        return d.experience_tick(**base)

    def test_001_identity(self):
        self.assertEqual(d.MODULE_ID, 'COC7_INVESTIGATOR_DEVELOPMENT_R1_BATCH1_DEV_V1')
        self.assertEqual(d.PARENT_MAGIC_MODULE_ID, 'COC7_MAGIC_CORE_R1_BATCH2_DEV_V1')

    def test_002_source_identity(self):
        self.assertEqual(d.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(d.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_003_successful_use_grants_tick(self):
        r = self._tick()
        self.assertTrue(r['new_tick_granted']); self.assertTrue(r['pending_check_after'])

    def test_004_failed_use_no_tick(self):
        r = self._tick(roll_success=False)
        self.assertFalse(r['new_tick_granted']); self.assertEqual(r['reason'], 'SKILL_USE_NOT_SUCCESSFUL')

    def test_005_bonus_die_blocks_tick(self):
        r = self._tick(used_bonus_die=True)
        self.assertFalse(r['new_tick_granted']); self.assertEqual(r['reason'], 'BONUS_DIE_BLOCKS_TICK')

    def test_006_luck_spend_blocks_tick(self):
        r = self._tick(luck_spent_on_roll=True)
        self.assertFalse(r['new_tick_granted']); self.assertEqual(r['reason'], 'LUCK_SPEND_BLOCKS_TICK')

    def test_007_opposed_winner_ticks(self):
        r = self._tick(opposed_roll=True, opposed_winner=True)
        self.assertTrue(r['new_tick_granted'])

    def test_008_opposed_nonwinner_no_tick(self):
        r = self._tick(opposed_roll=True, opposed_winner=False)
        self.assertFalse(r['new_tick_granted']); self.assertEqual(r['reason'], 'OPPOSED_ROLL_NONWINNER')

    def test_009_opposed_requires_winner(self):
        self.assertEqual(self._tick(opposed_roll=True, opposed_winner=None)['status'], 'BLOCKED')

    def test_010_nonopposed_rejects_winner_flag(self):
        self.assertEqual(self._tick(opposed_roll=False, opposed_winner=True)['status'], 'BLOCKED')

    def test_011_duplicate_tick_not_added(self):
        r = self._tick(already_checked=True)
        self.assertFalse(r['new_tick_granted']); self.assertTrue(r['pending_check_after'])

    def test_012_mythos_never_ticks(self):
        r = self._tick(skill_id='Cthulhu Mythos')
        self.assertFalse(r['new_tick_granted']); self.assertEqual(r['reason'], 'SKILL_NEVER_RECEIVES_IMPROVEMENT_CHECK')

    def test_013_credit_rating_never_ticks(self):
        r = self._tick(skill_id='Credit Rating')
        self.assertFalse(r['new_tick_granted'])

    def test_014_invalid_tick_flag_blocks(self):
        self.assertEqual(self._tick(roll_success=1)['status'], 'BLOCKED')

    def test_015_no_pending_no_dice_is_noop(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=False, recorded_percentile=None)
        self.assertFalse(r['improvement_checked']); self.assertEqual(r['skill_after'], 20)

    def test_016_no_pending_rejects_dice(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=False, recorded_percentile=80)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_017_improvement_roll_above_skill(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=21, recorded_gain_d10=3)
        self.assertTrue(r['improved']); self.assertEqual(r['skill_after'], 23)

    def test_018_equal_roll_does_not_improve(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=20)
        self.assertFalse(r['improved']); self.assertEqual(r['skill_after'], 20)

    def test_019_lower_roll_does_not_improve(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=8)
        self.assertFalse(r['improved'])

    def test_020_over_95_improves_high_skill(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=99, pending_check=True, recorded_percentile=96, recorded_gain_d10=2)
        self.assertTrue(r['improved']); self.assertEqual(r['skill_after'], 101)

    def test_021_over_95_improves_skill_over_100(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=120, pending_check=True, recorded_percentile=96, recorded_gain_d10=1)
        self.assertTrue(r['improved']); self.assertEqual(r['skill_after'], 121)

    def test_022_roll_95_not_special(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=99, pending_check=True, recorded_percentile=95)
        self.assertFalse(r['improved'])

    def test_023_success_requires_d10(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=80)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_024_failure_rejects_d10(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=10, recorded_gain_d10=5)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_025_cross_90_requires_2d6(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=85, pending_check=True, recorded_percentile=97, recorded_gain_d10=8)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_026_cross_90_reward(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=85, pending_check=True, recorded_percentile=97, recorded_gain_d10=8, recorded_sanity_2d6=[4, 5])
        self.assertTrue(r['crossed_90_threshold']); self.assertEqual(r['sanity_reward_pending_application'], 9)

    def test_027_exactly_reaches_90(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=85, pending_check=True, recorded_percentile=97, recorded_gain_d10=5, recorded_sanity_2d6=[1, 1])
        self.assertEqual(r['skill_after'], 90); self.assertTrue(r['crossed_90_threshold'])

    def test_028_already_90_does_not_repeat_reward(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=90, pending_check=True, recorded_percentile=96, recorded_gain_d10=4)
        self.assertFalse(r['crossed_90_threshold']); self.assertEqual(r['sanity_reward_pending_application'], 0)

    def test_029_unused_2d6_rejected(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=80, recorded_gain_d10=3, recorded_sanity_2d6=[1, 1])
        self.assertEqual(r['status'], 'BLOCKED')

    def test_030_bad_2d6_rejected(self):
        r = d.resolve_skill_improvement(skill_id='SWORD', current_skill=85, pending_check=True, recorded_percentile=97, recorded_gain_d10=8, recorded_sanity_2d6=[0, 7])
        self.assertEqual(r['status'], 'BLOCKED')

    def test_031_pending_check_consumed(self):
        r = d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=10)
        self.assertFalse(r['pending_check_after'])

    def test_032_mythos_improvement_blocks(self):
        r = d.resolve_skill_improvement(skill_id='CTHULHU_MYTHOS', current_skill=10, pending_check=True, recorded_percentile=80, recorded_gain_d10=3)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_033_credit_improvement_blocks(self):
        r = d.resolve_skill_improvement(skill_id='CREDIT_RATING', current_skill=40, pending_check=True, recorded_percentile=80, recorded_gain_d10=3)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_034_improvement_replay_stable(self):
        args = dict(skill_id='LIBRARY_USE', current_skill=55, pending_check=True, recorded_percentile=68, recorded_gain_d10=3)
        self.assertEqual(d.resolve_skill_improvement(**args), d.resolve_skill_improvement(**args))

    def test_035_training_four_months_grants_check(self):
        r = d.training_segment(campaign_context=True, segment_months=4, keeper_confirms_completed=True, keeper_confirms_valid=True)
        self.assertTrue(r['experience_check_granted'])

    def test_036_training_incomplete_no_check(self):
        r = d.training_segment(campaign_context=True, segment_months=4, keeper_confirms_completed=False, keeper_confirms_valid=True)
        self.assertFalse(r['experience_check_granted'])

    def test_037_training_invalidated_no_check(self):
        r = d.training_segment(campaign_context=True, segment_months=4, keeper_confirms_completed=True, keeper_confirms_valid=False)
        self.assertFalse(r['experience_check_granted'])

    def test_038_training_requires_campaign_context(self):
        r = d.training_segment(campaign_context=False, segment_months=4, keeper_confirms_completed=True, keeper_confirms_valid=True)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_039_training_short_default_blocks(self):
        r = d.training_segment(campaign_context=True, segment_months=3, keeper_confirms_completed=True, keeper_confirms_valid=True)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_040_training_short_keeper_override(self):
        r = d.training_segment(campaign_context=True, segment_months=3, keeper_confirms_completed=True, keeper_confirms_valid=True, renowned_teacher_shortening_authorized=True)
        self.assertTrue(r['experience_check_granted'])

    def test_041_self_study_four_months(self):
        r = d.self_study_plan(academic_skill_id='HISTORY', study_months=4, keeper_agrees_academic_subject=True)
        self.assertTrue(r['improvement_check_required_after_study'])

    def test_042_self_study_short_blocks(self):
        r = d.self_study_plan(academic_skill_id='HISTORY', study_months=3, keeper_agrees_academic_subject=True)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_043_self_study_short_override(self):
        r = d.self_study_plan(academic_skill_id='HISTORY', study_months=2, keeper_agrees_academic_subject=True, renowned_teacher_shortening_authorized=True)
        self.assertEqual(r['status'], 'RESOLVED')

    def test_044_self_study_keeper_gate(self):
        r = d.self_study_plan(academic_skill_id='HISTORY', study_months=4, keeper_agrees_academic_subject=False)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_045_self_study_mythos_blocks(self):
        r = d.self_study_plan(academic_skill_id='CTHULHU_MYTHOS', study_months=4, keeper_agrees_academic_subject=True)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_046_luck_option_gate(self):
        r = d.recover_luck(optional_rule_enabled=False, session_complete=True, current_luck=40, recorded_percentile=80, recorded_gain_d10=5)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_047_luck_session_end_gate(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=False, current_luck=40, recorded_percentile=80, recorded_gain_d10=5)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_048_luck_above_score_recovers(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=41, recorded_gain_d10=7)
        self.assertTrue(r['recovery_success']); self.assertEqual(r['luck_after'], 47)

    def test_049_luck_equal_score_no_recovery(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=40)
        self.assertFalse(r['recovery_success']); self.assertEqual(r['luck_after'], 40)

    def test_050_luck_lower_score_no_recovery(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=20)
        self.assertFalse(r['recovery_success'])

    def test_051_luck_success_requires_d10(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=80)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_052_luck_failure_rejects_d10(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=20, recorded_gain_d10=2)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_053_luck_caps_99(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=95, recorded_percentile=100, recorded_gain_d10=10)
        self.assertEqual(r['luck_after'], 99); self.assertEqual(r['actual_luck_gain'], 4)

    def test_054_luck_99_roll_100_has_zero_actual_gain(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=99, recorded_percentile=100, recorded_gain_d10=10)
        self.assertTrue(r['recovery_success']); self.assertEqual(r['luck_after'], 99); self.assertEqual(r['actual_luck_gain'], 0)

    def test_055_luck_never_resets_to_starting_value(self):
        r = d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=15, recorded_percentile=20, recorded_gain_d10=6)
        self.assertFalse(r['starting_luck_reset_applied']); self.assertEqual(r['luck_after'], 21)

    def test_056_luck_replay_stable(self):
        args = dict(optional_rule_enabled=True, session_complete=True, current_luck=15, recorded_percentile=37, recorded_gain_d10=6)
        self.assertEqual(d.recover_luck(**args), d.recover_luck(**args))

    def test_057_no_randomness_tick(self): self.assertFalse(self._tick()['randomness_generated'])
    def test_058_no_randomness_improvement(self):
        self.assertFalse(d.resolve_skill_improvement(skill_id='STEALTH', current_skill=20, pending_check=True, recorded_percentile=10)['randomness_generated'])
    def test_059_no_randomness_training(self):
        self.assertFalse(d.training_segment(campaign_context=True, segment_months=4, keeper_confirms_completed=True, keeper_confirms_valid=True)['randomness_generated'])
    def test_060_no_randomness_luck(self):
        self.assertFalse(d.recover_luck(optional_rule_enabled=True, session_complete=True, current_luck=40, recorded_percentile=20)['randomness_generated'])


def _add_generated_tests():
    cases = []
    for skill, roll, improves in [
        (0, 1, True), (20, 20, False), (20, 21, True), (50, 50, False),
        (50, 51, True), (95, 95, False), (95, 96, True), (99, 96, True),
        (100, 96, True), (120, 96, True), (120, 95, False),
    ]:
        cases.append(('skill', skill, roll, improves))
    for luck, roll, success in [
        (0, 1, True), (10, 10, False), (10, 11, True), (50, 50, False),
        (50, 51, True), (98, 99, True), (99, 99, False), (99, 100, True),
    ]:
        cases.append(('luck', luck, roll, success))
    for months, override, resolved in [
        (1, False, False), (2, False, False), (3, False, False), (4, False, True),
        (5, False, True), (1, True, True), (2, True, True), (3, True, True),
    ]:
        cases.append(('training', months, override, resolved))
    for a, b in [(1,1),(1,6),(2,5),(3,4),(6,6)]:
        cases.append(('sanity2d6', a, b, a+b))

    for i, case in enumerate(cases, 1):
        def make_test(case):
            def test(self):
                if case[0] == 'skill':
                    _, skill, roll, expected = case
                    gain = 1 if expected else None
                    reward = [1, 1] if skill < 90 <= skill + (gain or 0) else None
                    r = d.resolve_skill_improvement(
                        skill_id='GENERATED_SKILL', current_skill=skill, pending_check=True,
                        recorded_percentile=roll, recorded_gain_d10=gain, recorded_sanity_2d6=reward,
                    )
                    self.assertEqual(r['improved'], expected)
                elif case[0] == 'luck':
                    _, luck, roll, expected = case
                    gain = 1 if expected else None
                    r = d.recover_luck(
                        optional_rule_enabled=True, session_complete=True, current_luck=luck,
                        recorded_percentile=roll, recorded_gain_d10=gain,
                    )
                    self.assertEqual(r['recovery_success'], expected)
                elif case[0] == 'training':
                    _, months, override, expected = case
                    r = d.training_segment(
                        campaign_context=True, segment_months=months,
                        keeper_confirms_completed=True, keeper_confirms_valid=True,
                        renowned_teacher_shortening_authorized=override,
                    )
                    self.assertEqual(r['status'] == 'RESOLVED', expected)
                else:
                    _, a, b, expected = case
                    r = d.resolve_skill_improvement(
                        skill_id='SWORD', current_skill=89, pending_check=True,
                        recorded_percentile=96, recorded_gain_d10=1,
                        recorded_sanity_2d6=[a, b],
                    )
                    self.assertEqual(r['sanity_reward_pending_application'], expected)
            return test
        setattr(InvestigatorDevelopmentBatch1Tests, f'test_generated_{i:02d}', make_test(case))


_add_generated_tests()

if __name__ == '__main__':
    unittest.main()
