from __future__ import annotations

import unittest

import general_skill_resolution_dev as g


class GeneralSkillResolutionBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(g.MODULE_ID, 'COC7_GENERAL_SKILL_RESOLUTION_R1_BATCH1_DEV_V1')
        self.assertEqual(g.PARENT_FINANCE_MODULE_ID, 'COC7_FINANCE_CREDIT_RATING_R1_BATCH1_DEV_V1')

    def test_002_source_identity(self):
        self.assertEqual(g.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(g.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_003_parent_finance_survives(self):
        self.assertEqual(g.finance.MODULE_ID, 'COC7_FINANCE_CREDIT_RATING_R1_BATCH1_DEV_V1')

    def test_004_opponent_49_regular(self):
        self.assertEqual(g.living_opponent_difficulty(49)['difficulty'], 'REGULAR')

    def test_005_opponent_50_hard(self):
        self.assertEqual(g.living_opponent_difficulty(50)['difficulty'], 'HARD')

    def test_006_opponent_89_hard(self):
        self.assertEqual(g.living_opponent_difficulty(89)['difficulty'], 'HARD')

    def test_007_opponent_90_extreme(self):
        self.assertEqual(g.living_opponent_difficulty(90)['difficulty'], 'EXTREME')

    def test_008_opponent_above100_still_extreme(self):
        self.assertEqual(g.living_opponent_difficulty(150)['difficulty'], 'EXTREME')

    def test_009_opponent_negative_blocks(self):
        self.assertEqual(g.living_opponent_difficulty(-1)['code'], 'OPPONENT_VALUE_INVALID')

    def test_010_push_skill_failure_plan(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='take more time', already_pushed=False)
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertTrue(r['second_and_final_attempt'])

    def test_011_push_characteristic_failure_plan(self):
        r=g.plan_pushed_roll(category='CHARACTERISTIC', original_level='FAILURE', same_goal_confirmed=True, justification='greater effort', already_pushed=False)
        self.assertEqual(r['status'], 'RESOLVED')

    def test_012_push_requires_failure(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='REGULAR', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'PUSH_REQUIRES_FAILED_OR_FUMBLED_ORIGINAL_ROLL')

    def test_013_push_requires_same_goal(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=False, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'PUSH_REQUIRES_SAME_GOAL')

    def test_014_push_requires_justification(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification=' ', already_pushed=False)
        self.assertEqual(r['code'], 'PUSH_JUSTIFICATION_REQUIRED')

    def test_015_push_cannot_be_third_attempt(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=True)
        self.assertEqual(r['code'], 'PUSH_IS_SECOND_AND_FINAL_ATTEMPT')

    def test_016_luck_not_pushable(self):
        r=g.plan_pushed_roll(category='LUCK', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_NOT_PUSHABLE')

    def test_017_sanity_not_pushable(self):
        r=g.plan_pushed_roll(category='SANITY', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_NOT_PUSHABLE')

    def test_018_combat_not_pushable(self):
        r=g.plan_pushed_roll(category='COMBAT', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_NOT_PUSHABLE')

    def test_019_chase_not_pushable(self):
        r=g.plan_pushed_roll(category='CHASE', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_NOT_PUSHABLE')

    def test_020_opposed_not_pushable(self):
        r=g.plan_pushed_roll(category='OPPOSED', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_NOT_PUSHABLE')

    def test_021_unknown_push_category_blocks(self):
        r=g.plan_pushed_roll(category='MAGIC_CUSTOM', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False)
        self.assertEqual(r['code'], 'ROLL_CATEGORY_UNMATERIALIZED')

    def test_022_fumble_must_apply_original_consequence(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FUMBLE', same_goal_confirmed=True, justification='again', already_pushed=False, original_fumble_consequence_applied=False)
        self.assertEqual(r['code'], 'ORIGINAL_FUMBLE_CONSEQUENCE_MUST_ALREADY_APPLY')

    def test_023_fumble_can_be_planned_without_erasing_consequence(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FUMBLE', same_goal_confirmed=True, justification='again', already_pushed=False, original_fumble_consequence_applied=True)
        self.assertTrue(r['original_fumble_consequence_preserved'])

    def test_024_failure_must_not_fake_fumble_consequence(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False, original_fumble_consequence_applied=True)
        self.assertEqual(r['code'], 'FUMBLE_CONSEQUENCE_GATE_UNUSED')

    def test_025_unchanged_push_keeps_difficulty(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False, original_difficulty='HARD')
        self.assertEqual(r['difficulty'], 'HARD')

    def test_026_changed_situation_requires_keeper_difficulty(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False, situation_changed=True)
        self.assertEqual(r['code'], 'CHANGED_SITUATION_REQUIRES_KEEPER_DIFFICULTY')

    def test_027_changed_situation_can_change_difficulty(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False, situation_changed=True, original_difficulty='REGULAR', keeper_new_difficulty='HARD')
        self.assertEqual(r['difficulty'], 'HARD')

    def test_028_unchanged_situation_rejects_new_difficulty(self):
        r=g.plan_pushed_roll(category='SKILL', original_level='FAILURE', same_goal_confirmed=True, justification='again', already_pushed=False, keeper_new_difficulty='HARD')
        self.assertEqual(r['code'], 'UNCHANGED_SITUATION_MUST_KEEP_DIFFICULTY')

    def test_029_pushed_success_achieves_goal(self):
        r=g.resolve_pushed_roll(value=60, recorded_roll=40, difficulty='REGULAR')
        self.assertTrue(r['success'])
        self.assertTrue(r['goal_achieved'])

    def test_030_pushed_failure_requires_keeper_consequence(self):
        r=g.resolve_pushed_roll(value=40, recorded_roll=80, difficulty='REGULAR')
        self.assertEqual(r['code'], 'FAILED_PUSH_REQUIRES_KEEPER_DEFINED_CONSEQUENCE')

    def test_031_pushed_failure_resolves_with_keeper_consequence(self):
        r=g.resolve_pushed_roll(value=40, recorded_roll=80, difficulty='REGULAR', keeper_failure_consequence_id='LOSS_OF_EQUIPMENT')
        self.assertFalse(r['success'])
        self.assertEqual(r['keeper_failure_consequence_id'], 'LOSS_OF_EQUIPMENT')

    def test_032_pushed_fumble_resolves_with_keeper_consequence(self):
        r=g.resolve_pushed_roll(value=40, recorded_roll=100, difficulty='REGULAR', keeper_failure_consequence_id='CAPTURE')
        self.assertEqual(r['level'], 'FUMBLE')

    def test_033_pushed_success_rejects_failure_consequence(self):
        r=g.resolve_pushed_roll(value=60, recorded_roll=40, difficulty='REGULAR', keeper_failure_consequence_id='SHOULD_NOT_APPLY')
        self.assertEqual(r['code'], 'SUCCESS_MUST_NOT_APPLY_PUSH_FAILURE_CONSEQUENCE')

    def test_034_pushed_hard_difficulty(self):
        r=g.resolve_pushed_roll(value=60, recorded_roll=30, difficulty='HARD')
        self.assertTrue(r['success'])

    def test_035_pushed_invalid_roll_blocks(self):
        self.assertEqual(g.resolve_pushed_roll(value=60, recorded_roll=0, difficulty='REGULAR')['code'], 'PUSHED_ROLL_INPUT_INVALID')

    def test_036_group_any_success(self):
        p=[{'actor_id':'A','value':50,'recorded_roll':20},{'actor_id':'B','value':20,'recorded_roll':90}]
        r=g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ANY_SUCCESS')
        self.assertTrue(r['group_success'])
        self.assertEqual(r['successful_participants'],1)

    def test_037_group_any_all_fail(self):
        p=[{'actor_id':'A','value':20,'recorded_roll':80},{'actor_id':'B','value':20,'recorded_roll':90}]
        self.assertFalse(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ANY_SUCCESS')['group_success'])

    def test_038_group_all_success(self):
        p=[{'actor_id':'A','value':60,'recorded_roll':20},{'actor_id':'B','value':70,'recorded_roll':30}]
        self.assertTrue(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ALL_SUCCESS')['group_success'])

    def test_039_group_all_one_fail(self):
        p=[{'actor_id':'A','value':60,'recorded_roll':20},{'actor_id':'B','value':20,'recorded_roll':90}]
        self.assertFalse(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ALL_SUCCESS')['group_success'])

    def test_040_group_hard_difficulty(self):
        p=[{'actor_id':'A','value':60,'recorded_roll':30}]
        self.assertTrue(g.resolve_group_skill_roll(participants=p,difficulty='HARD',success_mode='ANY_SUCCESS')['group_success'])

    def test_041_group_duplicate_actor_blocks(self):
        p=[{'actor_id':'A','value':60,'recorded_roll':20},{'actor_id':'A','value':60,'recorded_roll':20}]
        self.assertEqual(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ANY_SUCCESS')['code'],'GROUP_PARTICIPANT_ID_INVALID_OR_DUPLICATE')

    def test_042_group_empty_blocks(self):
        self.assertEqual(g.resolve_group_skill_roll(participants=[],difficulty='REGULAR',success_mode='ANY_SUCCESS')['code'],'GROUP_PARTICIPANTS_REQUIRED')

    def test_043_group_bad_record_blocks(self):
        p=[{'actor_id':'A','value':60}]
        self.assertEqual(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ANY_SUCCESS')['code'],'GROUP_PARTICIPANT_RECORD_INVALID')

    def test_044_group_does_not_auto_select_participants(self):
        p=[{'actor_id':'A','value':60,'recorded_roll':20}]
        self.assertFalse(g.resolve_group_skill_roll(participants=p,difficulty='REGULAR',success_mode='ANY_SUCCESS')['automatic_participant_selection'])

    def test_045_same_actor_retry_requires_push(self):
        r=g.subsequent_same_goal_attempt_gate(actor_already_rolled=True,keeper_allows_attempt=True,push_declared=False)
        self.assertEqual(r['code'],'SAME_INVESTIGATOR_RETRY_REQUIRES_PUSH')

    def test_046_same_actor_pushed_retry_allowed(self):
        r=g.subsequent_same_goal_attempt_gate(actor_already_rolled=True,keeper_allows_attempt=True,push_declared=True)
        self.assertEqual(r['attempt_type'],'PUSHED')

    def test_047_new_actor_normal_retry_allowed_by_keeper(self):
        r=g.subsequent_same_goal_attempt_gate(actor_already_rolled=False,keeper_allows_attempt=True,push_declared=False)
        self.assertEqual(r['attempt_type'],'NORMAL')

    def test_048_new_actor_must_not_be_marked_pushed(self):
        r=g.subsequent_same_goal_attempt_gate(actor_already_rolled=False,keeper_allows_attempt=True,push_declared=True)
        self.assertEqual(r['code'],'NEW_INVESTIGATOR_NORMAL_ATTEMPT_MUST_NOT_BE_MARKED_PUSHED')

    def test_049_keeper_can_block_additional_attempt(self):
        r=g.subsequent_same_goal_attempt_gate(actor_already_rolled=False,keeper_allows_attempt=False,push_declared=False)
        self.assertEqual(r['code'],'KEEPER_DOES_NOT_ALLOW_ADDITIONAL_ATTEMPT')

    def test_050_physical_single_cecil_vs150_impossible(self):
        r=g.physical_human_limit_plan(opposition_value=150,investigators=[{'actor_id':'Cecil','characteristic':40}],reducer_actor_ids=[])
        self.assertEqual(r['code'],'OPPOSITION_BEYOND_REMAINING_HUMAN_LIMITS')

    def test_051_physical_cecil_plus_martin_source_example(self):
        inv=[{'actor_id':'Cecil','characteristic':40},{'actor_id':'Martin','characteristic':45}]
        r=g.physical_human_limit_plan(opposition_value=150,investigators=inv,reducer_actor_ids=['Cecil'])
        self.assertEqual(r['opposition_after_reductions'],110)
        self.assertEqual(r['difficulty'],'EXTREME')
        self.assertEqual(r['eligible_rollers'],['Martin'])

    def test_052_physical_five_person_source_pattern(self):
        inv=[{'actor_id':'Cecil','characteristic':40},{'actor_id':'Harvey','characteristic':20},{'actor_id':'Martin','characteristic':45},{'actor_id':'Helen','characteristic':60},{'actor_id':'Belinda','characteristic':75}]
        r=g.physical_human_limit_plan(opposition_value=150,investigators=inv,reducer_actor_ids=['Harvey','Cecil','Martin'])
        self.assertEqual(r['opposition_after_reductions'],45)
        self.assertEqual(r['difficulty'],'REGULAR')
        self.assertEqual(r['reducers'],['Harvey','Cecil','Martin'])
        self.assertEqual(r['eligible_rollers'],['Helen','Belinda'])

    def test_053_physical_can_choose_fewer_reducers_for_extreme(self):
        inv=[{'actor_id':'Harvey','characteristic':20},{'actor_id':'Belinda','characteristic':75}]
        r=g.physical_human_limit_plan(opposition_value=150,investigators=inv,reducer_actor_ids=[])
        self.assertEqual(r['difficulty'],'EXTREME')
        self.assertEqual(r['eligible_rollers'],['Harvey','Belinda'])

    def test_054_physical_reducers_must_be_lowest_first(self):
        inv=[{'actor_id':'A','characteristic':20},{'actor_id':'B','characteristic':40},{'actor_id':'C','characteristic':60}]
        r=g.physical_human_limit_plan(opposition_value=180,investigators=inv,reducer_actor_ids=['B'])
        self.assertEqual(r['code'],'PHYSICAL_REDUCERS_MUST_BE_USED_LOWEST_CHARACTERISTIC_FIRST')

    def test_055_physical_tied_lowest_can_be_keeper_selected_explicitly(self):
        inv=[{'actor_id':'A','characteristic':20},{'actor_id':'B','characteristic':20},{'actor_id':'C','characteristic':60}]
        r=g.physical_human_limit_plan(opposition_value=170,investigators=inv,reducer_actor_ids=['B'])
        self.assertEqual(r['status'],'RESOLVED')
        self.assertEqual(r['reducers'],['B'])

    def test_056_physical_reducer_not_participant_blocks(self):
        inv=[{'actor_id':'A','characteristic':20},{'actor_id':'B','characteristic':60}]
        self.assertEqual(g.physical_human_limit_plan(opposition_value=170,investigators=inv,reducer_actor_ids=['X'])['code'],'PHYSICAL_REDUCER_NOT_A_PARTICIPANT')

    def test_057_physical_duplicate_reducer_blocks(self):
        inv=[{'actor_id':'A','characteristic':20},{'actor_id':'B','characteristic':60}]
        self.assertEqual(g.physical_human_limit_plan(opposition_value=170,investigators=inv,reducer_actor_ids=['A','A'])['code'],'PHYSICAL_REDUCER_DUPLICATE')

    def test_058_physical_must_leave_roller(self):
        inv=[{'actor_id':'A','characteristic':20},{'actor_id':'B','characteristic':60}]
        r=g.physical_human_limit_plan(opposition_value=170,investigators=inv,reducer_actor_ids=['A','B'])
        self.assertEqual(r['code'],'PHYSICAL_PLAN_MUST_LEAVE_AT_LEAST_ONE_ROLLER')

    def test_059_physical_cannot_reduce_to_zero(self):
        inv=[{'actor_id':'A','characteristic':50},{'actor_id':'B','characteristic':60}]
        r=g.physical_human_limit_plan(opposition_value=50,investigators=inv,reducer_actor_ids=['A'])
        self.assertEqual(r['code'],'PHYSICAL_OPPOSITION_MAY_NOT_BE_REDUCED_TO_ZERO_OR_BELOW')

    def test_060_physical_roll_always_required(self):
        inv=[{'actor_id':'A','characteristic':40},{'actor_id':'B','characteristic':80}]
        r=g.physical_human_limit_plan(opposition_value=80,investigators=inv,reducer_actor_ids=[])
        self.assertTrue(r['a_roll_is_still_required'])

    def test_061_physical_no_auto_helper_selection(self):
        inv=[{'actor_id':'A','characteristic':40},{'actor_id':'B','characteristic':80}]
        r=g.physical_human_limit_plan(opposition_value=80,investigators=inv,reducer_actor_ids=[])
        self.assertFalse(r['automatic_helper_selection'])

    def test_062_group_luck_selects_unique_lowest(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20},{'actor_id':'C','luck':70}]
        r=g.group_luck_selector(investigators=inv,mode='GROUP_LUCK_ROLL')
        self.assertEqual(r['actor_id'],'B')
        self.assertTrue(r['roll_required'])

    def test_063_lowest_luck_bad_event_needs_no_roll(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20}]
        r=g.group_luck_selector(investigators=inv,mode='LOWEST_LUCK_BAD_EVENT')
        self.assertEqual(r['actor_id'],'B')
        self.assertFalse(r['roll_required'])

    def test_064_group_luck_tie_fails_closed(self):
        inv=[{'actor_id':'A','luck':20},{'actor_id':'B','luck':20}]
        self.assertEqual(g.group_luck_selector(investigators=inv,mode='GROUP_LUCK_ROLL')['code'],'LOWEST_LUCK_TIE_KEEPER_RESOLUTION_REQUIRED')

    def test_065_group_luck_wrong_actor_blocks(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20}]
        r=g.resolve_group_luck_roll(investigators=inv,actor_id='A',recorded_roll=10)
        self.assertEqual(r['code'],'GROUP_LUCK_WRONG_ACTOR')

    def test_066_group_luck_success(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20}]
        r=g.resolve_group_luck_roll(investigators=inv,actor_id='B',recorded_roll=15)
        self.assertTrue(r['success'])

    def test_067_group_luck_failure(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20}]
        r=g.resolve_group_luck_roll(investigators=inv,actor_id='B',recorded_roll=80)
        self.assertFalse(r['success'])

    def test_068_group_luck_duplicate_actor_blocks(self):
        inv=[{'actor_id':'A','luck':50},{'actor_id':'A','luck':20}]
        self.assertEqual(g.group_luck_selector(investigators=inv,mode='GROUP_LUCK_ROLL')['code'],'GROUP_LUCK_PARTICIPANT_INVALID')

    def test_069_intelligence_roll_uses_int(self):
        r=g.intelligence_or_idea_roll(INT=60,recorded_roll=50,roll_type='INTELLIGENCE')
        self.assertTrue(r['success'])

    def test_070_idea_roll_uses_int(self):
        r=g.intelligence_or_idea_roll(INT=60,recorded_roll=50,roll_type='IDEA')
        self.assertTrue(r['success'])
        self.assertFalse(r['automatic_solution_generated'])
        self.assertFalse(r['automatic_cost_generated'])

    def test_071_int_idea_invalid_type_blocks(self):
        self.assertEqual(g.intelligence_or_idea_roll(INT=60,recorded_roll=50,roll_type='KNOW')['code'],'INT_IDEA_ROLL_TYPE_INVALID')

    def test_072_know_roll_uses_edu(self):
        r=g.know_roll(EDU=70,recorded_roll=60,specific_skill_applicable=False)
        self.assertTrue(r['success'])
        self.assertFalse(r['automatic_information_generated'])

    def test_073_know_defers_to_specific_skill(self):
        r=g.know_roll(EDU=70,recorded_roll=None,specific_skill_applicable=True,specific_skill_id='CHEMISTRY')
        self.assertEqual(r['status'],'PENDING')
        self.assertEqual(r['code'],'SPECIFIC_SKILL_PREFERRED_BY_KEEPER')

    def test_074_know_specific_skill_requires_id(self):
        r=g.know_roll(EDU=70,recorded_roll=None,specific_skill_applicable=True)
        self.assertEqual(r['code'],'SPECIFIC_SKILL_ID_REQUIRED')

    def test_075_know_deferral_must_not_consume_roll(self):
        r=g.know_roll(EDU=70,recorded_roll=20,specific_skill_applicable=True,specific_skill_id='CHEMISTRY')
        self.assertEqual(r['code'],'KNOW_ROLL_MUST_DEFER_BEFORE_CONSUMING_ROLL')

    def test_076_know_no_specific_skill_rejects_unused_id(self):
        r=g.know_roll(EDU=70,recorded_roll=20,specific_skill_applicable=False,specific_skill_id='CHEMISTRY')
        self.assertEqual(r['code'],'SPECIFIC_SKILL_ID_UNUSED')

    def test_077_core_success_engine_reused(self):
        self.assertEqual(g.core_rules.success_level(60,30),'HARD')

    def test_078_core_opposed_engine_reused(self):
        self.assertEqual(g.core_rules.opposed(60,20,50,40)['winner'],'A')

    def test_079_core_bonus_penalty_digits_reused(self):
        self.assertEqual(g.core_rules.percentile_from_digits(4,[4,2],net_bonus=1),24)

    def test_080_no_randomness_push(self):
        r=g.resolve_pushed_roll(value=40,recorded_roll=80,difficulty='REGULAR',keeper_failure_consequence_id='X')
        self.assertFalse(r['randomness_generated'])

    def test_081_no_randomness_group(self):
        r=g.resolve_group_skill_roll(participants=[{'actor_id':'A','value':50,'recorded_roll':20}],difficulty='REGULAR',success_mode='ANY_SUCCESS')
        self.assertFalse(r['randomness_generated'])

    def test_082_no_randomness_physical(self):
        r=g.physical_human_limit_plan(opposition_value=110,investigators=[{'actor_id':'A','characteristic':40}],reducer_actor_ids=[])
        self.assertFalse(r['randomness_generated'])

    def test_083_no_randomness_luck(self):
        r=g.resolve_group_luck_roll(investigators=[{'actor_id':'A','luck':20}],actor_id='A',recorded_roll=10)
        self.assertFalse(r['randomness_generated'])

    def test_084_no_randomness_idea(self):
        self.assertFalse(g.intelligence_or_idea_roll(INT=60,recorded_roll=20,roll_type='IDEA')['randomness_generated'])

    def test_085_push_replay_stable(self):
        kwargs=dict(value=40,recorded_roll=80,difficulty='REGULAR',keeper_failure_consequence_id='X')
        self.assertEqual(g.resolve_pushed_roll(**kwargs),g.resolve_pushed_roll(**kwargs))

    def test_086_group_replay_stable(self):
        kwargs=dict(participants=[{'actor_id':'A','value':50,'recorded_roll':20},{'actor_id':'B','value':30,'recorded_roll':80}],difficulty='REGULAR',success_mode='ANY_SUCCESS')
        self.assertEqual(g.resolve_group_skill_roll(**kwargs),g.resolve_group_skill_roll(**kwargs))

    def test_087_physical_replay_stable(self):
        kwargs=dict(opposition_value=150,investigators=[{'actor_id':'Cecil','characteristic':40},{'actor_id':'Martin','characteristic':45}],reducer_actor_ids=['Cecil'])
        self.assertEqual(g.physical_human_limit_plan(**kwargs),g.physical_human_limit_plan(**kwargs))

    def test_088_group_luck_replay_stable(self):
        kwargs=dict(investigators=[{'actor_id':'A','luck':50},{'actor_id':'B','luck':20}],actor_id='B',recorded_roll=15)
        self.assertEqual(g.resolve_group_luck_roll(**kwargs),g.resolve_group_luck_roll(**kwargs))

    def test_089_know_replay_stable(self):
        kwargs=dict(EDU=70,recorded_roll=60,specific_skill_applicable=False)
        self.assertEqual(g.know_roll(**kwargs),g.know_roll(**kwargs))


def _make_difficulty_boundary_test(value, expected):
    def _test(self):
        r=g.living_opponent_difficulty(value)
        self.assertEqual(r['difficulty'],expected)
        self.assertFalse(r['randomness_generated'])
    return _test


for _idx, (_value,_expected) in enumerate([
    (0,'REGULAR'),(1,'REGULAR'),(25,'REGULAR'),(48,'REGULAR'),
    (51,'HARD'),(60,'HARD'),(75,'HARD'),(88,'HARD'),
    (91,'EXTREME'),(99,'EXTREME'),(100,'EXTREME'),(101,'EXTREME'),
    (120,'EXTREME'),(200,'EXTREME'),(999,'EXTREME')
], start=1):
    setattr(GeneralSkillResolutionBatch1Tests,f'test_generated_difficulty_{_idx:02d}',_make_difficulty_boundary_test(_value,_expected))


if __name__ == '__main__':
    unittest.main()
