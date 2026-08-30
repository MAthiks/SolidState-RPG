from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))

import magic_core_dev as m


class MagicCoreBatch1Tests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.MODULE_ID,'COC7_MAGIC_CORE_R1_BATCH1_DEV_V1')
        self.assertEqual(m.PARENT_CHASE_MODULE_ID,'COC7_CHASE_R1_BATCH2_DEV_V1')

    def test_mp_pow50(self):
        r=m.magic_point_profile(pow_value=50); self.assertEqual(r['initial_mp'],10); self.assertEqual(r['regen_per_completed_hour'],1)

    def test_mp_pow100_regen_one(self): self.assertEqual(m.magic_point_profile(pow_value=100)['regen_per_completed_hour'],1)
    def test_mp_pow101_regen_two(self): self.assertEqual(m.magic_point_profile(pow_value=101)['regen_per_completed_hour'],2)
    def test_mp_pow200_regen_two(self): self.assertEqual(m.magic_point_profile(pow_value=200)['regen_per_completed_hour'],2)
    def test_mp_pow201_regen_three(self): self.assertEqual(m.magic_point_profile(pow_value=201)['regen_per_completed_hour'],3)
    def test_mp_pow_zero(self): self.assertEqual(m.magic_point_profile(pow_value=0)['initial_mp'],0)
    def test_mp_negative_blocked(self): self.assertEqual(m.magic_point_profile(pow_value=-1)['status'],'BLOCKED')

    def test_mp_excess_profile(self):
        r=m.magic_point_profile(pow_value=50,current_mp=15); self.assertEqual(r['excess_above_natural_max'],5); self.assertTrue(r['excess_can_be_spent']); self.assertFalse(r['excess_can_be_regenerated'])

    def test_regen_normal(self):
        r=m.regenerate_magic_points(pow_value=50,current_mp=5,completed_hours=3); self.assertEqual(r['MP'],8); self.assertEqual(r['regenerated_mp'],3)

    def test_regen_caps_natural(self):
        r=m.regenerate_magic_points(pow_value=50,current_mp=9,completed_hours=5); self.assertEqual(r['MP'],10); self.assertEqual(r['regenerated_mp'],1)

    def test_regen_excess_unchanged(self):
        r=m.regenerate_magic_points(pow_value=50,current_mp=12,completed_hours=20); self.assertEqual(r['MP'],12); self.assertEqual(r['regenerated_mp'],0)

    def test_spend_mp_only(self):
        r=m.spend_magic_points(current_mp=10,current_hp=12,max_hp=12,cost=6); self.assertEqual(r['MP'],4); self.assertEqual(r['hp_cost_after_mp_exhausted'],0); self.assertEqual(r['hp_state']['current_hp'],12)

    def test_spend_mp_then_hp(self):
        r=m.spend_magic_points(current_mp=5,current_hp=13,max_hp=13,cost=16); self.assertEqual(r['MP'],0); self.assertEqual(r['hp_cost_after_mp_exhausted'],11); self.assertEqual(r['hp_state']['current_hp'],2); self.assertTrue(r['hp_state']['major_wound'])

    def test_spend_can_kill(self):
        r=m.spend_magic_points(current_mp=0,current_hp=10,max_hp=10,cost=11); self.assertTrue(r['hp_state']['dead'])

    def test_initial_read_auto_believer(self):
        r=m.initial_tome_reading(language_value=0,difficulty='HARD',units=None,tens=None,keeper_auto_success=True,current_mythos=10,current_san=70,cmi=3,recorded_tome_san_loss=5,believer=True)
        self.assertTrue(r['success']); self.assertEqual(r['cthulhu_mythos'],13); self.assertEqual(r['SAN'],65); self.assertEqual(r['san_loss'],5)

    def test_initial_read_hard_success(self):
        r=m.initial_tome_reading(language_value=60,difficulty='HARD',units=0,tens=[2],keeper_auto_success=False,current_mythos=0,current_san=70,cmi=3,recorded_tome_san_loss=2,believer=True)
        self.assertTrue(r['success']); self.assertEqual(r['roll'],20)

    def test_initial_read_failure_no_gain_or_loss(self):
        r=m.initial_tome_reading(language_value=60,difficulty='HARD',units=0,tens=[4],keeper_auto_success=False,current_mythos=0,current_san=70,cmi=3,recorded_tome_san_loss=None,believer=True)
        self.assertFalse(r['success']); self.assertEqual(r['cthulhu_mythos_gain'],0); self.assertEqual(r['san_loss'],0); self.assertTrue(r['push_allowed'])

    def test_initial_read_failure_rejects_san_loss(self):
        r=m.initial_tome_reading(language_value=60,difficulty='HARD',units=0,tens=[4],keeper_auto_success=False,current_mythos=0,current_san=70,cmi=3,recorded_tome_san_loss=3,believer=True)
        self.assertEqual(r['status'],'BLOCKED')

    def test_initial_read_nonbeliever_no_san_loss(self):
        r=m.initial_tome_reading(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=0,current_san=70,cmi=3,recorded_tome_san_loss=None,believer=False)
        self.assertEqual(r['SAN'],70); self.assertEqual(r['cthulhu_mythos'],3)

    def test_initial_read_nonbeliever_rejects_loss(self):
        r=m.initial_tome_reading(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=0,current_san=70,cmi=3,recorded_tome_san_loss=2,believer=False)
        self.assertEqual(r['status'],'BLOCKED')

    def test_initial_read_mythos_reduces_max_san(self):
        r=m.initial_tome_reading(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=20,current_san=79,cmi=5,recorded_tome_san_loss=0,believer=True)
        self.assertEqual(r['maximum_san'],74); self.assertEqual(r['SAN'],74); self.assertTrue(r['san_capped_by_new_mythos_maximum'])

    def test_initial_read_overflow_blocked(self):
        r=m.initial_tome_reading(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=98,current_san=1,cmi=2,recorded_tome_san_loss=0,believer=True)
        self.assertEqual(r['status'],'BLOCKED')

    def test_inconsistent_san_mythos_blocked(self):
        r=m.initial_tome_reading(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=20,current_san=90,cmi=1,recorded_tome_san_loss=0,believer=True)
        self.assertEqual(r['status'],'BLOCKED')

    def _study(self,**kw):
        base=dict(initial_reading_completed=True,current_mythos=10,current_san=70,tome_rating=33,cmi=3,cmf=8,believer=True,recorded_tome_san_loss=3,base_full_study_weeks=32,previous_full_studies=0,elapsed_study_weeks=32)
        base.update(kw); return m.full_tome_study(**base)

    def test_full_study_initial_required(self): self.assertEqual(self._study(initial_reading_completed=False)['status'],'BLOCKED')
    def test_full_study_only_one_tome(self): self.assertEqual(self._study(other_tome_study_active=True)['status'],'BLOCKED')

    def test_full_study_incomplete(self):
        r=self._study(elapsed_study_weeks=31); self.assertFalse(r['study_complete']); self.assertEqual(r['remaining_weeks'],1); self.assertFalse(r['reading_roll_required'])

    def test_full_study_below_rating_gets_cmf(self):
        r=self._study(); self.assertTrue(r['study_complete']); self.assertEqual(r['mythos_gain_basis'],'CMF'); self.assertEqual(r['cthulhu_mythos_gain'],8); self.assertEqual(r['SAN'],67)

    def test_full_study_equal_rating_gets_cmi(self):
        r=self._study(current_mythos=33,current_san=66); self.assertEqual(r['mythos_gain_basis'],'CMI'); self.assertEqual(r['cthulhu_mythos_gain'],3)

    def test_full_study_above_rating_gets_cmi(self):
        r=self._study(current_mythos=40,current_san=59); self.assertEqual(r['cthulhu_mythos_gain'],3)

    def test_full_study_time_doubles(self):
        r=self._study(previous_full_studies=1,elapsed_study_weeks=64); self.assertEqual(r['required_weeks'],64); self.assertEqual(r['next_full_study_weeks'],128)

    def test_full_study_third_time(self):
        r=self._study(previous_full_studies=2,elapsed_study_weeks=128); self.assertEqual(r['required_weeks'],128); self.assertEqual(r['next_full_study_weeks'],256)

    def test_full_study_nonbeliever_no_loss(self):
        r=self._study(believer=False,recorded_tome_san_loss=None); self.assertEqual(r['san_loss'],0)

    def test_full_study_language_tick(self):
        r=self._study(); self.assertTrue(r['language_skill_tick_granted']); self.assertFalse(r['automatic_other_skill_increase'])

    def test_full_study_overflow_blocked(self):
        r=self._study(current_mythos=98,current_san=1,tome_rating=100,cmi=1,cmf=2); self.assertEqual(r['status'],'BLOCKED')

    def test_reference_requires_full_study(self): self.assertEqual(m.tome_reference_search(full_study_completed=False,tome_rating=33,recorded_search_hours_d4=2,roll=20)['status'],'BLOCKED')
    def test_reference_success(self): self.assertTrue(m.tome_reference_search(full_study_completed=True,tome_rating=33,recorded_search_hours_d4=2,roll=33)['fact_or_allusion_found'])
    def test_reference_failure(self): self.assertFalse(m.tome_reference_search(full_study_completed=True,tome_rating=33,recorded_search_hours_d4=4,roll=34)['fact_or_allusion_found'])
    def test_reference_hours_invalid(self): self.assertEqual(m.tome_reference_search(full_study_completed=True,tome_rating=33,recorded_search_hours_d4=5,roll=20)['status'],'BLOCKED')

    def test_book_learning_requires_initial_read(self):
        self.assertEqual(m.spell_learning_plan(method='BOOK',initial_reading_completed=False,recorded_duration_dice=[3,4])['status'],'BLOCKED')

    def test_book_learning_2d6(self):
        r=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[3,4]); self.assertEqual(r['duration'],7); self.assertEqual(r['duration_unit'],'WEEKS'); self.assertEqual(r['learning_san_cost'],0)

    def test_person_learning_1d8(self):
        r=m.spell_learning_plan(method='PERSON',recorded_duration_dice=[5]); self.assertEqual(r['duration'],5); self.assertEqual(r['duration_unit'],'DAYS')

    def test_learning_keeper_override(self):
        r=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,keeper_override_duration=3); self.assertEqual(r['duration_source'],'KEEPER_OVERRIDE')

    def test_learning_override_and_dice_blocked(self):
        r=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[2,3],keeper_override_duration=3); self.assertEqual(r['status'],'BLOCKED')

    def test_learning_bad_book_dice(self): self.assertEqual(m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[7,1])['status'],'BLOCKED')
    def test_learning_bad_person_dice(self): self.assertEqual(m.spell_learning_plan(method='PERSON',recorded_duration_dice=[9])['status'],'BLOCKED')

    def test_learning_auto_success(self):
        p=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,keeper_auto_success=True,recorded_duration_dice=[2,2]); r=m.resolve_spell_learning(plan=p,int_value=10,units=None,tens=None); self.assertTrue(r['learned']); self.assertFalse(r['push_allowed'])

    def test_learning_hard_int_success(self):
        p=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[2,2]); r=m.resolve_spell_learning(plan=p,int_value=60,units=0,tens=[2]); self.assertTrue(r['learned'])

    def test_learning_hard_int_failure_pushable(self):
        p=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[2,2]); r=m.resolve_spell_learning(plan=p,int_value=60,units=0,tens=[4]); self.assertFalse(r['learned']); self.assertTrue(r['push_allowed']); self.assertFalse(r['automatic_pushed_failure_consequence'])

    def test_first_cast_hard_pow_success(self):
        r=m.first_cast_roll(pow_value=60,units=0,tens=[2],previously_cast_successfully=False); self.assertTrue(r['spell_effect_proceeds']); self.assertTrue(r['mastered_after_cast'])

    def test_first_cast_hard_pow_failure(self):
        r=m.first_cast_roll(pow_value=60,units=0,tens=[4],previously_cast_successfully=False); self.assertFalse(r['spell_effect_proceeds']); self.assertTrue(r['push_allowed']); self.assertTrue(r['normal_cost_must_be_paid_for_this_attempt'])

    def test_subsequent_cast_no_roll(self):
        r=m.first_cast_roll(pow_value=60,units=None,tens=None,previously_cast_successfully=True); self.assertFalse(r['casting_roll_required']); self.assertTrue(r['spell_effect_proceeds'])

    def test_npc_cast_no_roll(self):
        r=m.first_cast_roll(pow_value=60,units=None,tens=None,previously_cast_successfully=False,actor_is_npc_or_monster=True); self.assertFalse(r['casting_roll_required']); self.assertTrue(r['spell_effect_proceeds'])

    def test_fixed_spell_cost(self):
        r=m.apply_fixed_spell_cost(current_mp=10,current_hp=12,max_hp=12,current_san=50,current_pow=60,mp_cost=5,san_cost=3,pow_cost=1)
        self.assertEqual(r['MP'],5); self.assertEqual(r['SAN'],47); self.assertEqual(r['POW'],59)

    def test_fixed_spell_cost_san_zero_allowed(self):
        r=m.apply_fixed_spell_cost(current_mp=10,current_hp=12,max_hp=12,current_san=0,current_pow=60,mp_cost=1,san_cost=3,pow_cost=0)
        self.assertEqual(r['status'],'RESOLVED'); self.assertEqual(r['SAN'],0); self.assertEqual(r['san_loss'],0); self.assertTrue(r['san_zero_does_not_block_casting'])

    def test_fixed_spell_cost_mp_overspend_to_hp(self):
        r=m.apply_fixed_spell_cost(current_mp=2,current_hp=10,max_hp=10,current_san=50,current_pow=60,mp_cost=7,san_cost=0,pow_cost=0); self.assertEqual(r['MP'],0); self.assertEqual(r['hp_state']['current_hp'],5)

    def test_fixed_spell_cost_pow_changes_natural_mp_cap(self):
        r=m.apply_fixed_spell_cost(current_mp=10,current_hp=10,max_hp=10,current_san=50,current_pow=60,mp_cost=0,san_cost=0,pow_cost=20); self.assertEqual(r['POW'],40); self.assertEqual(r['natural_mp_max_after_pow_cost'],8); self.assertTrue(r['current_mp_above_new_natural_max_can_be_spent_not_regenerated'])

    def test_fixed_spell_pow_overavailable_blocked(self):
        r=m.apply_fixed_spell_cost(current_mp=10,current_hp=10,max_hp=10,current_san=50,current_pow=5,mp_cost=0,san_cost=0,pow_cost=6); self.assertEqual(r['status'],'BLOCKED')

    def test_pushed_failure_fixed_cost_multiplier(self):
        r=m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=4,fixed_mp_cost=5,fixed_san_cost=2,fixed_pow_cost=1); self.assertEqual(r['additional_mp_cost'],20); self.assertEqual(r['additional_san_cost'],8); self.assertEqual(r['additional_pow_cost'],4); self.assertTrue(r['spell_still_works'])

    def test_pushed_failure_variable_san_dice(self):
        r=m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=4,fixed_mp_cost=4,san_die_count=1,san_die_sides=3,recorded_san_dice=[1,2,3,1]); self.assertEqual(r['additional_mp_cost'],16); self.assertEqual(r['additional_san_cost'],7)

    def test_pushed_failure_wrong_variable_dice_count(self):
        r=m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=4,san_die_count=1,san_die_sides=3,recorded_san_dice=[1,2,3]); self.assertEqual(r['status'],'BLOCKED')

    def test_pushed_failure_invalid_multiplier(self): self.assertEqual(m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=7)['status'],'BLOCKED')
    def test_pushed_failure_no_auto_side_effect(self):
        r=m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=2); self.assertTrue(r['keeper_side_effect_selection_required']); self.assertFalse(r['automatic_side_effect_selection'])

    def test_replay_same_mp_regen(self):
        a=m.regenerate_magic_points(pow_value=70,current_mp=5,completed_hours=4); b=m.regenerate_magic_points(pow_value=70,current_mp=5,completed_hours=4); self.assertEqual(a,b)

    def test_replay_same_tome_read(self):
        args=dict(language_value=60,difficulty='REGULAR',units=0,tens=[2],keeper_auto_success=False,current_mythos=5,current_san=70,cmi=3,recorded_tome_san_loss=4,believer=True)
        self.assertEqual(m.initial_tome_reading(**args),m.initial_tome_reading(**args))

    def test_replay_same_pushed_cost(self):
        args=dict(recorded_multiplier_d6=3,fixed_mp_cost=4,san_die_count=1,san_die_sides=3,recorded_san_dice=[1,2,3])
        self.assertEqual(m.pushed_cast_failure_cost_plan(**args),m.pushed_cast_failure_cost_plan(**args))


def _add_generated_tests():
    cases=[]
    for pow_value,regen in [(1,1),(50,1),(99,1),(100,1),(101,2),(150,2),(200,2),(201,3),(300,3),(301,4)]:
        cases.append(('regen_rate',pow_value,regen))
    for d1,d2,total in [(1,1,2),(1,6,7),(2,5,7),(3,4,7),(6,6,12)]:
        cases.append(('book_time',d1,d2,total))
    for rating,roll,found in [(1,1,True),(1,2,False),(33,33,True),(33,34,False),(100,100,True)]:
        cases.append(('reference',rating,roll,found))
    for multiplier,base,expected in [(1,5,5),(2,5,10),(3,5,15),(4,5,20),(5,5,25),(6,5,30)]:
        cases.append(('push_fixed',multiplier,base,expected))
    for previous,required in [(0,32),(1,64),(2,128),(3,256)]:
        cases.append(('study_time',previous,required))

    for i,case in enumerate(cases,1):
        def make_test(case):
            def test(self):
                kind=case[0]
                if kind=='regen_rate':
                    _,pow_value,expected=case; self.assertEqual(m.magic_point_profile(pow_value=pow_value)['regen_per_completed_hour'],expected)
                elif kind=='book_time':
                    _,d1,d2,expected=case; r=m.spell_learning_plan(method='BOOK',initial_reading_completed=True,recorded_duration_dice=[d1,d2]); self.assertEqual(r['duration'],expected)
                elif kind=='reference':
                    _,rating,roll,expected=case; self.assertEqual(m.tome_reference_search(full_study_completed=True,tome_rating=rating,recorded_search_hours_d4=1,roll=roll)['fact_or_allusion_found'],expected)
                elif kind=='push_fixed':
                    _,multiplier,base,expected=case; self.assertEqual(m.pushed_cast_failure_cost_plan(recorded_multiplier_d6=multiplier,fixed_mp_cost=base)['additional_mp_cost'],expected)
                else:
                    _,previous,required=case; r=m.full_tome_study(initial_reading_completed=True,current_mythos=10,current_san=70,tome_rating=33,cmi=3,cmf=8,believer=False,recorded_tome_san_loss=None,base_full_study_weeks=32,previous_full_studies=previous,elapsed_study_weeks=required); self.assertEqual(r['required_weeks'],required)
            return test
        setattr(MagicCoreBatch1Tests,f'test_generated_{i:02d}',make_test(case))

_add_generated_tests()

if __name__=='__main__':
    unittest.main()
