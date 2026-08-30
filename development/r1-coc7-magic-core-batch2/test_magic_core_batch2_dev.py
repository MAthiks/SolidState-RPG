from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))

import magic_core_batch2_dev as m


class MagicCoreBatch2Tests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.MODULE_ID,'COC7_MAGIC_CORE_R1_BATCH2_DEV_V1')
        self.assertEqual(m.PARENT_MAGIC_MODULE_ID,'COC7_MAGIC_CORE_R1_BATCH1_DEV_V1')

    def test_disruption_false(self):
        r=m.disrupted_casting(significant_distraction=False,mp_cost=4,san_cost=2)
        self.assertFalse(r['disrupted']); self.assertTrue(r['spell_effect_proceeds']); self.assertEqual(r['mp_cost_still_due'],0)

    def test_disruption_true_costs_still_due(self):
        r=m.disrupted_casting(significant_distraction=True,mp_cost=4,san_cost=2)
        self.assertTrue(r['disrupted']); self.assertFalse(r['spell_effect_proceeds']); self.assertEqual(r['mp_cost_still_due'],4); self.assertEqual(r['san_cost_still_due'],2)
        self.assertFalse(r['automatic_side_effect_selection'])

    def test_disruption_invalid_cost(self): self.assertEqual(m.disrupted_casting(significant_distraction=True,mp_cost=-1,san_cost=0)['status'],'BLOCKED')

    def test_player_choice_belief(self):
        r=m.believer_transition(believer_before=False,current_san=70,current_mythos=8,reason='PLAYER_CHOICE')
        self.assertTrue(r['believer']); self.assertTrue(r['changed']); self.assertEqual(r['additional_san_loss'],8); self.assertEqual(r['SAN'],62)

    def test_player_choice_belief_caps_at_zero(self):
        r=m.believer_transition(believer_before=False,current_san=3,current_mythos=10,reason='PLAYER_CHOICE')
        self.assertEqual(r['additional_san_loss'],3); self.assertEqual(r['SAN'],0)

    def test_firsthand_loss_forces_belief(self):
        r=m.believer_transition(believer_before=False,current_san=60,current_mythos=7,reason='FIRSTHAND_MYTHOS_SAN_LOSS',firsthand_mythos_san_loss=2)
        self.assertTrue(r['changed']); self.assertEqual(r['SAN'],53); self.assertTrue(r['feed_loss_into_sanity_state_machine'])

    def test_firsthand_zero_loss_does_not_force(self):
        r=m.believer_transition(believer_before=False,current_san=60,current_mythos=7,reason='FIRSTHAND_MYTHOS_SAN_LOSS',firsthand_mythos_san_loss=0)
        self.assertEqual(r['status'],'BLOCKED')

    def test_clearly_unearthly_keeper_gate(self):
        r=m.believer_transition(believer_before=False,current_san=60,current_mythos=7,reason='CLEARLY_UNEARTHLY_KEEPER_GATE',keeper_confirms_clearly_unearthly=True)
        self.assertTrue(r['believer']); self.assertEqual(r['additional_san_loss'],7)

    def test_clearly_unearthly_without_keeper_gate_blocked(self):
        self.assertEqual(m.believer_transition(believer_before=False,current_san=60,current_mythos=7,reason='CLEARLY_UNEARTHLY_KEEPER_GATE')['status'],'BLOCKED')

    def test_already_believer_no_second_loss(self):
        r=m.believer_transition(believer_before=True,current_san=60,current_mythos=7,reason='PLAYER_CHOICE')
        self.assertFalse(r['changed']); self.assertEqual(r['additional_san_loss'],0); self.assertEqual(r['SAN'],60)

    def test_inconsistent_san_mythos_blocked(self):
        self.assertEqual(m.believer_transition(believer_before=False,current_san=90,current_mythos=20,reason='PLAYER_CHOICE')['status'],'BLOCKED')

    def test_human_horror_never_forces_belief(self):
        for loss in (0,1,5,20): self.assertFalse(m.human_horror_belief_gate(san_loss=loss)['forces_mythos_belief'])

    def test_nonbeliever_may_learn_not_cast(self):
        r=m.nonbeliever_spell_access(believer=False,spell_learned=True)
        self.assertTrue(r['may_learn_spell']); self.assertFalse(r['may_cast_spell']); self.assertEqual(r['blocked_reason'],'NONBELIEVER_CANNOT_CAST')

    def test_believer_learned_may_cast(self): self.assertTrue(m.nonbeliever_spell_access(believer=True,spell_learned=True)['may_cast_spell'])
    def test_believer_unlearned_cannot_cast(self): self.assertEqual(m.nonbeliever_spell_access(believer=True,spell_learned=False)['blocked_reason'],'SPELL_NOT_LEARNED')

    def test_pow_exercise_spell_win(self): self.assertTrue(m.pow_exercise_chance(source='SPELL_OPPOSED_POW_WIN',opposed_pow_won=True)['exercise_eligible'])
    def test_pow_exercise_spell_loss(self): self.assertFalse(m.pow_exercise_chance(source='SPELL_OPPOSED_POW_WIN',opposed_pow_won=False)['exercise_eligible'])
    def test_pow_exercise_luck01(self): self.assertTrue(m.pow_exercise_chance(source='LUCK_ROLL_01',luck_roll=1)['exercise_eligible'])
    def test_pow_exercise_luck02(self): self.assertFalse(m.pow_exercise_chance(source='LUCK_ROLL_01',luck_roll=2)['exercise_eligible'])
    def test_pow_exercise_luck_requires_roll(self): self.assertEqual(m.pow_exercise_chance(source='LUCK_ROLL_01')['status'],'BLOCKED')

    def test_pow_exercise_roll_greater_than_pow(self):
        r=m.resolve_pow_exercise(current_pow=60,exercise_eligible=True,recorded_percentile=61,recorded_gain_d10=7)
        self.assertTrue(r['exercise_success']); self.assertEqual(r['POW'],67); self.assertEqual(r['current_san_increase'],0)

    def test_pow_exercise_96_succeeds_even_high_pow(self):
        r=m.resolve_pow_exercise(current_pow=99,exercise_eligible=True,recorded_percentile=96,recorded_gain_d10=2)
        self.assertTrue(r['exercise_success']); self.assertEqual(r['POW'],101)

    def test_pow_exercise_equal_pow_fails_below96(self):
        r=m.resolve_pow_exercise(current_pow=60,exercise_eligible=True,recorded_percentile=60,recorded_gain_d10=None)
        self.assertFalse(r['exercise_success']); self.assertEqual(r['POW'],60)

    def test_pow_exercise_failed_must_not_use_d10(self):
        self.assertEqual(m.resolve_pow_exercise(current_pow=60,exercise_eligible=True,recorded_percentile=50,recorded_gain_d10=3)['status'],'BLOCKED')

    def test_pow_exercise_success_requires_d10(self):
        self.assertEqual(m.resolve_pow_exercise(current_pow=60,exercise_eligible=True,recorded_percentile=70,recorded_gain_d10=None)['status'],'BLOCKED')

    def test_pow_ineligible_consumes_no_dice(self):
        r=m.resolve_pow_exercise(current_pow=60,exercise_eligible=False,recorded_percentile=None,recorded_gain_d10=None)
        self.assertEqual(r['pow_gain'],0)

    def test_pow_ineligible_rejects_dice(self): self.assertEqual(m.resolve_pow_exercise(current_pow=60,exercise_eligible=False,recorded_percentile=70,recorded_gain_d10=4)['status'],'BLOCKED')

    def test_non_mythos_disabled(self):
        self.assertEqual(m.non_mythos_magic_plan(keeper_enabled=False,skill_id='OCCULT',effect_truth_status='KEEPER_DEFINED',horrific_deed=False,keeper_san_cost=None)['status'],'BLOCKED')

    def test_non_mythos_occult(self):
        r=m.non_mythos_magic_plan(keeper_enabled=True,skill_id='OCCULT',effect_truth_status='KEEPER_DEFINED_REAL_OR_FRAUDULENT',horrific_deed=False,keeper_san_cost=None)
        self.assertTrue(r['uses_mythos_magic_generic_procedure']); self.assertFalse(r['automatic_effect_generation'])

    def test_non_mythos_other_skill_blocked(self):
        self.assertEqual(m.non_mythos_magic_plan(keeper_enabled=True,skill_id='ARCANA',effect_truth_status='KEEPER_DEFINED',horrific_deed=False,keeper_san_cost=None)['status'],'BLOCKED')

    def test_non_mythos_horrific_requires_cost(self):
        self.assertEqual(m.non_mythos_magic_plan(keeper_enabled=True,skill_id='OCCULT',effect_truth_status='KEEPER_DEFINED',horrific_deed=True,keeper_san_cost=None)['status'],'BLOCKED')

    def test_non_mythos_horrific_explicit_cost(self):
        r=m.non_mythos_magic_plan(keeper_enabled=True,skill_id='OCCULT',effect_truth_status='KEEPER_DEFINED',horrific_deed=True,keeper_san_cost=3)
        self.assertEqual(r['san_cost'],3)

    def _spontaneous(self,**kw):
        base=dict(optional_rule_enabled=True,player_aim='Learn the hidden fact',keeper_accepts=True,keeper_lesser_aim=None,target_resists=False,mp_cost=3,san_cost=1)
        base.update(kw); return m.spontaneous_mythos_plan(**base)

    def test_spontaneous_optional_disabled(self): self.assertEqual(self._spontaneous(optional_rule_enabled=False)['status'],'BLOCKED')
    def test_spontaneous_regular_default(self):
        r=self._spontaneous(); self.assertEqual(r['resolution'],'REGULAR_MYTHOS'); self.assertEqual(r['difficulty'],'REGULAR'); self.assertFalse(r['automatic_cost_selection'])

    def test_spontaneous_resisted_opposed(self):
        r=self._spontaneous(target_resists=True); self.assertEqual(r['resolution'],'OPPOSED_MYTHOS_VS_POW'); self.assertIsNone(r['difficulty'])

    def test_spontaneous_lesser_aim_requires_keeper_text(self): self.assertEqual(self._spontaneous(keeper_accepts=False,keeper_lesser_aim=None)['status'],'BLOCKED')

    def test_spontaneous_lesser_aim_preserved(self):
        r=self._spontaneous(keeper_accepts=False,keeper_lesser_aim='Sense whether the object is Mythos-related')
        self.assertTrue(r['keeper_reduced_aim']); self.assertEqual(r['effective_aim'],'Sense whether the object is Mythos-related'); self.assertFalse(r['automatic_aim_rewrite'])

    def test_spontaneous_costs_required(self): self.assertEqual(self._spontaneous(mp_cost=None)['status'],'BLOCKED')

    def test_resolve_unresisted_success(self):
        p=self._spontaneous(); r=m.resolve_spontaneous_mythos(plan=p,mythos_value=40,mythos_roll=35)
        self.assertTrue(r['success']); self.assertEqual(r['resolution'],'REGULAR_MYTHOS')

    def test_resolve_unresisted_failure_pushable(self):
        p=self._spontaneous(); r=m.resolve_spontaneous_mythos(plan=p,mythos_value=40,mythos_roll=60)
        self.assertFalse(r['success']); self.assertTrue(r['push_allowed']); self.assertFalse(r['pushed_failure_aim_guaranteed'])

    def test_resolve_unresisted_rejects_target_pow(self):
        p=self._spontaneous(); self.assertEqual(m.resolve_spontaneous_mythos(plan=p,mythos_value=40,mythos_roll=20,target_pow=50,target_pow_roll=30)['status'],'BLOCKED')

    def test_resolve_resisted_caster_wins(self):
        p=self._spontaneous(target_resists=True); r=m.resolve_spontaneous_mythos(plan=p,mythos_value=60,mythos_roll=20,target_pow=50,target_pow_roll=30)
        self.assertTrue(r['success']); self.assertTrue(r['no_second_pow_vs_pow_roll'])

    def test_resolve_resisted_target_wins(self):
        p=self._spontaneous(target_resists=True); r=m.resolve_spontaneous_mythos(plan=p,mythos_value=60,mythos_roll=40,target_pow=50,target_pow_roll=20)
        self.assertFalse(r['success'])

    def test_resolve_resisted_tie_value_tie(self):
        p=self._spontaneous(target_resists=True); r=m.resolve_spontaneous_mythos(plan=p,mythos_value=50,mythos_roll=30,target_pow=50,target_pow_roll=30)
        self.assertTrue(r['tie_requires_keeper_resolution_or_reroll']); self.assertFalse(r['success'])

    def test_resisted_requires_target_roll(self):
        p=self._spontaneous(target_resists=True); self.assertEqual(m.resolve_spontaneous_mythos(plan=p,mythos_value=60,mythos_roll=20,target_pow=50,target_pow_roll=None)['status'],'BLOCKED')

    def test_spontaneous_push_costs_from_plan(self):
        p=self._spontaneous(mp_cost=4,san_cost=2); r=m.spontaneous_push_framework(plan=p,recorded_multiplier_d6=3)
        self.assertEqual(r['additional_mp_cost'],12); self.assertEqual(r['additional_san_cost'],6); self.assertFalse(r['automatic_aim_success'])

    def test_spontaneous_push_invalid_multiplier(self):
        p=self._spontaneous(); self.assertEqual(m.spontaneous_push_framework(plan=p,recorded_multiplier_d6=7)['status'],'BLOCKED')

    def test_spontaneous_push_rejects_override_cost(self):
        p=self._spontaneous(); self.assertEqual(m.spontaneous_push_framework(plan=p,recorded_multiplier_d6=2,fixed_mp_cost=99)['status'],'BLOCKED')

    def test_replay_belief_same(self):
        args=dict(believer_before=False,current_san=60,current_mythos=7,reason='FIRSTHAND_MYTHOS_SAN_LOSS',firsthand_mythos_san_loss=2)
        self.assertEqual(m.believer_transition(**args),m.believer_transition(**args))

    def test_replay_pow_same(self):
        args=dict(current_pow=60,exercise_eligible=True,recorded_percentile=70,recorded_gain_d10=5)
        self.assertEqual(m.resolve_pow_exercise(**args),m.resolve_pow_exercise(**args))

    def test_replay_spontaneous_same(self):
        p=self._spontaneous(target_resists=True); args=dict(plan=p,mythos_value=60,mythos_roll=20,target_pow=50,target_pow_roll=30)
        self.assertEqual(m.resolve_spontaneous_mythos(**args),m.resolve_spontaneous_mythos(**args))


def _add_generated_tests():
    cases=[]
    for mythos,san,expected in [(0,70,0),(1,70,1),(5,70,5),(10,70,10),(50,70,50),(99,0,0)]:
        cases.append(('belief',mythos,san,expected))
    for pow_value,roll,success in [(40,40,False),(40,41,True),(95,95,False),(95,96,True),(99,96,True),(120,96,True)]:
        cases.append(('pow',pow_value,roll,success))
    for mythos,roll,success in [(20,20,True),(20,21,False),(50,50,True),(50,51,False),(100,100,True)]:
        cases.append(('regular',mythos,roll,success))
    for mult,mp,san in [(1,3,1),(2,6,2),(3,9,3),(4,12,4),(5,15,5),(6,18,6)]:
        cases.append(('push',mult,mp,san))

    for i,case in enumerate(cases,1):
        def make_test(case):
            def test(self):
                if case[0]=='belief':
                    _,mythos,san,expected=case
                    r=m.believer_transition(believer_before=False,current_san=san,current_mythos=mythos,reason='PLAYER_CHOICE')
                    self.assertEqual(r['additional_san_loss'],expected)
                elif case[0]=='pow':
                    _,pow_value,roll,expected=case
                    gain=1 if (roll>pow_value or roll>=96) else None
                    r=m.resolve_pow_exercise(current_pow=pow_value,exercise_eligible=True,recorded_percentile=roll,recorded_gain_d10=gain)
                    self.assertEqual(r['exercise_success'],expected)
                elif case[0]=='regular':
                    _,mythos,roll,expected=case
                    p=m.spontaneous_mythos_plan(optional_rule_enabled=True,player_aim='Aim',keeper_accepts=True,keeper_lesser_aim=None,target_resists=False,mp_cost=1,san_cost=1)
                    r=m.resolve_spontaneous_mythos(plan=p,mythos_value=mythos,mythos_roll=roll)
                    self.assertEqual(r['success'],expected)
                else:
                    _,mult,mp,san=case
                    p=m.spontaneous_mythos_plan(optional_rule_enabled=True,player_aim='Aim',keeper_accepts=True,keeper_lesser_aim=None,target_resists=False,mp_cost=3,san_cost=1)
                    r=m.spontaneous_push_framework(plan=p,recorded_multiplier_d6=mult)
                    self.assertEqual(r['additional_mp_cost'],mp); self.assertEqual(r['additional_san_cost'],san)
            return test
        setattr(MagicCoreBatch2Tests,f'test_generated_{i:02d}',make_test(case))

_add_generated_tests()

if __name__=='__main__':
    unittest.main()
