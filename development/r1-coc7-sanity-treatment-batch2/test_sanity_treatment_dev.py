from __future__ import annotations

import unittest

import sanity_treatment_dev as treatment


class SanityTreatmentBatch2Tests(unittest.TestCase):
    def private(self, **kwargs):
        base=dict(care_type='PRIVATE',current_san=50,cthulhu_mythos=0,recorded_treatment_roll=50,recorded_gain_d3=2,san_units=0,san_tens=[4])
        base.update(kwargs)
        return treatment.monthly_indefinite_care(**base)

    def institution(self, **kwargs):
        base=dict(care_type='INSTITUTION',current_san=50,cthulhu_mythos=0,recorded_treatment_roll=40,recorded_gain_d3=2,san_units=0,san_tens=[4],institution_rating=50)
        base.update(kwargs)
        return treatment.monthly_indefinite_care(**base)

    def test_001_identity(self):
        self.assertEqual(treatment.MODULE_ID,'COC7_SANITY_TREATMENT_R1_BATCH2_DEV_V1')
        self.assertEqual(treatment.PARENT_SANITY_MODULE_ID,'COC7_SANITY_INSANITY_R1_BATCH1_DEV_V1')
        self.assertEqual(treatment.KEEPER_SHA256,'691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_private_roll_95_is_success(self):
        r=self.private(recorded_treatment_roll=95)
        self.assertIn(r['outcome'],{'TREATMENT_PROGRESS_CURED','TREATMENT_PROGRESS_NOT_YET_CURED'})

    def test_003_private_roll_96_is_rebellion(self):
        r=self.private(recorded_treatment_roll=96,recorded_gain_d3=None,san_units=None,san_tens=None,recorded_loss_d6=3)
        self.assertEqual(r['outcome'],'REBELLION_OR_SERIOUS_SETBACK')
        self.assertEqual(r['SAN'],47)

    def test_004_private_rebellion_blocks_next_month(self):
        r=self.private(recorded_treatment_roll=100,recorded_gain_d3=None,san_units=None,san_tens=None,recorded_loss_d6=2)
        self.assertTrue(r['next_month_blocked'])

    def test_005_private_rebellion_requires_recorded_d6(self):
        r=self.private(recorded_treatment_roll=96,recorded_gain_d3=None,san_units=None,san_tens=None,recorded_loss_d6=None)
        self.assertEqual(r['code'],'RECORDED_REBELLION_D6_REQUIRED')

    def test_006_private_success_requires_recorded_d3(self):
        r=self.private(recorded_gain_d3=None)
        self.assertEqual(r['code'],'RECORDED_CARE_D3_REQUIRED')

    def test_007_private_success_requires_post_care_san_roll(self):
        r=self.private(san_units=None,san_tens=None)
        self.assertEqual(r['code'],'POST_CARE_SAN_ROLL_REQUIRED')

    def test_008_private_success_gain_then_san_roll_cures(self):
        r=self.private(recorded_gain_d3=3,san_units=0,san_tens=[4])
        self.assertEqual(r['SAN'],53)
        self.assertTrue(r['cured'])

    def test_009_private_success_san_fail_not_cured(self):
        r=self.private(recorded_gain_d3=3,san_units=0,san_tens=[7])
        self.assertFalse(r['cured'])
        self.assertTrue(r['next_month_retry_allowed'])

    def test_010_institution_default_50_success(self):
        r=self.institution(recorded_treatment_roll=50)
        self.assertNotEqual(r['outcome'],'NO_PROGRESS')

    def test_011_institution_51_no_progress(self):
        r=self.institution(recorded_treatment_roll=51,recorded_gain_d3=None,san_units=None,san_tens=None)
        self.assertEqual(r['outcome'],'NO_PROGRESS')
        self.assertEqual(r['SAN'],50)

    def test_012_institution_95_no_progress(self):
        r=self.institution(recorded_treatment_roll=95,recorded_gain_d3=None,san_units=None,san_tens=None)
        self.assertEqual(r['outcome'],'NO_PROGRESS')

    def test_013_institution_96_rebellion(self):
        r=self.institution(recorded_treatment_roll=96,recorded_gain_d3=None,san_units=None,san_tens=None,recorded_loss_d6=4)
        self.assertEqual(r['outcome'],'REBELLION_OR_SERIOUS_SETBACK')
        self.assertEqual(r['SAN'],46)

    def test_014_institution_rating_75_extends_success(self):
        r=self.institution(recorded_treatment_roll=75,institution_rating=75)
        self.assertNotEqual(r['outcome'],'NO_PROGRESS')

    def test_015_institution_rating_5_valid(self):
        r=self.institution(recorded_treatment_roll=5,institution_rating=5)
        self.assertEqual(r['status'],'RESOLVED')

    def test_016_institution_rating_below_5_blocks(self):
        r=self.institution(institution_rating=4)
        self.assertEqual(r['code'],'INSTITUTION_RATING_INVALID')

    def test_017_institution_rating_above_95_blocks(self):
        r=self.institution(institution_rating=96)
        self.assertEqual(r['code'],'INSTITUTION_RATING_INVALID')

    def test_018_prior_rebellion_consumes_blocked_month(self):
        r=self.private(blocked_by_prior_rebellion=True,recorded_gain_d3=None,san_units=None,san_tens=None)
        self.assertEqual(r['outcome'],'PRIOR_REBELLION_BLOCKS_PROGRESS_THIS_MONTH')
        self.assertFalse(r['next_month_blocked'])

    def test_019_care_requires_indefinite_insanity(self):
        r=self.private(indefinite_insanity_active=False)
        self.assertEqual(r['code'],'INDEFINITE_INSANITY_REQUIRED')

    def test_020_invalid_care_type_blocks(self):
        r=self.private(care_type='UNKNOWN')
        self.assertEqual(r['code'],'CARE_TYPE_INVALID')

    def test_021_care_roll_bounds(self):
        r=self.private(recorded_treatment_roll=0)
        self.assertEqual(r['code'],'RECORDED_TREATMENT_D100_INVALID')

    def test_022_care_gain_capped_by_mythos_max(self):
        r=self.private(current_san=78,cthulhu_mythos=20,recorded_gain_d3=3,san_units=0,san_tens=[4])
        self.assertEqual(r['SAN'],79)
        self.assertEqual(r['san_gain'],1)

    def test_023_rebellion_can_reach_permanent_insanity(self):
        r=self.private(current_san=2,recorded_treatment_roll=96,recorded_gain_d3=None,san_units=None,san_tens=None,recorded_loss_d6=6)
        self.assertEqual(r['SAN'],0)
        self.assertTrue(r['permanent_insanity'])
        self.assertFalse(r['next_month_blocked'])

    def test_024_development_phase_explicit_keeper_gate_recovers(self):
        r=treatment.keeper_development_phase_recovery(indefinite_insanity_active=True,at_end_of_chapter_or_scenario=True,keeper_ends_insanity=True)
        self.assertTrue(r['recovered_from_indefinite_insanity'])

    def test_025_development_phase_without_keeper_gate_does_not_recover(self):
        r=treatment.keeper_development_phase_recovery(indefinite_insanity_active=True,at_end_of_chapter_or_scenario=True,keeper_ends_insanity=False)
        self.assertFalse(r['recovered_from_indefinite_insanity'])

    def test_026_development_phase_not_at_end_does_not_recover(self):
        r=treatment.keeper_development_phase_recovery(indefinite_insanity_active=True,at_end_of_chapter_or_scenario=False,keeper_ends_insanity=True)
        self.assertFalse(r['recovered_from_indefinite_insanity'])

    def test_027_keeper_award_gain(self):
        r=treatment.keeper_award(current_san=50,cthulhu_mythos=0,recorded_gain=6)
        self.assertEqual(r['SAN'],56)
        self.assertEqual(r['actual_gain'],6)

    def test_028_keeper_award_zero_allowed(self):
        r=treatment.keeper_award(current_san=50,cthulhu_mythos=0,recorded_gain=0)
        self.assertEqual(r['SAN'],50)

    def test_029_keeper_award_caps_at_max(self):
        r=treatment.keeper_award(current_san=75,cthulhu_mythos=20,recorded_gain=10)
        self.assertEqual(r['SAN'],79)
        self.assertEqual(r['actual_gain'],4)

    def test_030_skill_90_award_2d6(self):
        r=treatment.skill_reaches_90_award(current_san=50,cthulhu_mythos=0,reached_90=True,recorded_2d6_total=9)
        self.assertEqual(r['SAN'],59)

    def test_031_skill_90_award_bounds_low(self):
        r=treatment.skill_reaches_90_award(current_san=50,cthulhu_mythos=0,reached_90=True,recorded_2d6_total=1)
        self.assertEqual(r['code'],'RECORDED_2D6_TOTAL_REQUIRED')

    def test_032_skill_90_false_no_gain(self):
        r=treatment.skill_reaches_90_award(current_san=50,cthulhu_mythos=0,reached_90=False,recorded_2d6_total=None)
        self.assertEqual(r['san_gain'],0)

    def test_033_skill_90_false_rejects_dice(self):
        r=treatment.skill_reaches_90_award(current_san=50,cthulhu_mythos=0,reached_90=False,recorded_2d6_total=7)
        self.assertEqual(r['code'],'SKILL_90_AWARD_NOT_APPLICABLE')

    def test_034_psychotherapy_success_gain(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[4],recorded_gain_d3=2)
        self.assertEqual(r['outcome'],'SAN_GAIN')
        self.assertEqual(r['SAN'],52)

    def test_035_psychotherapy_failure_no_gain(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[8])
        self.assertEqual(r['outcome'],'NO_GAIN')
        self.assertEqual(r['SAN'],50)

    def test_036_psychotherapy_fumble_loss(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=40,units=0,tens=[0],recorded_loss_d6=5)
        self.assertEqual(r['outcome'],'FUMBLE_SETBACK')
        self.assertEqual(r['SAN'],45)

    def test_037_psychotherapy_fumble_terminates_analyst(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=40,units=0,tens=[0],recorded_loss_d6=5)
        self.assertTrue(r['analyst_relationship_terminated'])

    def test_038_psychotherapy_fumble_requires_d6(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=40,units=0,tens=[0])
        self.assertEqual(r['code'],'RECORDED_PSYCHOTHERAPY_FUMBLE_D6_REQUIRED')

    def test_039_psychotherapy_success_requires_d3(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[4])
        self.assertEqual(r['code'],'RECORDED_PSYCHOTHERAPY_D3_REQUIRED')

    def test_040_psychotherapy_permanent_insanity_blocks(self):
        r=treatment.psychotherapy_month(current_san=1,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[4],recorded_gain_d3=2,permanent_insanity=True)
        self.assertEqual(r['code'],'PERMANENT_INSANITY_CANNOT_PARTICIPATE')

    def test_041_psychotherapy_caps_at_max(self):
        r=treatment.psychotherapy_month(current_san=78,cthulhu_mythos=20,analyst_skill=60,units=0,tens=[4],recorded_gain_d3=3)
        self.assertEqual(r['SAN'],79)
        self.assertEqual(r['san_gain'],1)

    def test_042_phobia_both_success_cures(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[4])
        self.assertTrue(r['cured'])
        self.assertEqual(r['outcome'],'CURED')

    def test_043_mania_both_success_cures(self):
        r=treatment.phobia_mania_therapy_month(condition_type='MANIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[4])
        self.assertTrue(r['cured'])

    def test_044_phobia_cure_has_no_san_gain(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[4])
        self.assertEqual(r['san_gain'],0)

    def test_045_analyst_failure_no_benefit(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[8])
        self.assertFalse(r['cured'])
        self.assertEqual(r['outcome'],'ANALYST_FAILURE_NO_BENEFIT')

    def test_046_patient_failure_no_benefit(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[8])
        self.assertFalse(r['cured'])
        self.assertEqual(r['outcome'],'PATIENT_SAN_FAILURE_NO_BENEFIT')

    def test_047_analyst_fumble_causes_loss(self):
        r=treatment.phobia_mania_therapy_month(condition_type='MANIA',current_san=60,analyst_skill=40,analyst_units=0,analyst_tens=[0],recorded_loss_d6=4)
        self.assertEqual(r['SAN'],56)
        self.assertTrue(r['analyst_relationship_terminated'])

    def test_048_patient_fumble_causes_loss(self):
        r=treatment.phobia_mania_therapy_month(condition_type='MANIA',current_san=40,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[0],recorded_loss_d6=4)
        self.assertEqual(r['SAN'],36)
        self.assertEqual(r['outcome'],'PATIENT_SAN_FUMBLE')

    def test_049_patient_fumble_relationship_effect_fail_closed(self):
        r=treatment.phobia_mania_therapy_month(condition_type='MANIA',current_san=40,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[0],recorded_loss_d6=4)
        self.assertTrue(r['relationship_effect_unmaterialized'])

    def test_050_phobia_therapy_no_auto_backstory_edit(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4],patient_units=0,patient_tens=[4])
        self.assertTrue(r['backstory_edit_required'])
        self.assertFalse(r['automatic_backstory_edit'])

    def test_051_invalid_condition_type_blocks(self):
        r=treatment.phobia_mania_therapy_month(condition_type='OTHER',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4])
        self.assertEqual(r['code'],'CONDITION_TYPE_INVALID')

    def test_052_patient_roll_required_after_analyst_success(self):
        r=treatment.phobia_mania_therapy_month(condition_type='PHOBIA',current_san=60,analyst_skill=60,analyst_units=0,analyst_tens=[4])
        self.assertEqual(r['code'],'PATIENT_SAN_ROLL_REQUIRED')

    def test_053_self_help_other_support_success(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[4],recorded_gain_d6=5)
        self.assertTrue(r['success'])
        self.assertEqual(r['SAN'],65)

    def test_054_self_help_other_support_failure_loses_one(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[8])
        self.assertFalse(r['success'])
        self.assertEqual(r['SAN'],59)
        self.assertEqual(r['san_loss'],1)

    def test_055_self_help_failure_requires_backstory_revision(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[8])
        self.assertTrue(r['backstory_revision_required'])
        self.assertFalse(r['automatic_backstory_edit'])

    def test_056_key_connection_uses_bonus_die(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='KEY_CONNECTION',units=5,tens=[7,2],recorded_gain_d6=4)
        self.assertTrue(r['success'])
        self.assertEqual(r['roll'],25)
        self.assertEqual(r['bonus_die_used'],1)

    def test_057_key_connection_success_recovers_indefinite(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='KEY_CONNECTION',units=5,tens=[7,2],recorded_gain_d6=4,indefinite_insanity_active=True)
        self.assertTrue(r['recovered_from_indefinite_insanity'])
        self.assertFalse(r['indefinite_insanity_active'])

    def test_058_key_connection_failure_loses_key_status(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='KEY_CONNECTION',units=0,tens=[8,9],indefinite_insanity_active=True)
        self.assertFalse(r['success'])
        self.assertTrue(r['key_connection_lost'])
        self.assertTrue(r['indefinite_insanity_active'])

    def test_059_self_help_success_requires_recorded_d6(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[4])
        self.assertEqual(r['code'],'RECORDED_SELF_HELP_D6_REQUIRED')

    def test_060_self_help_phobia_ineligible(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='PHOBIA',units=0,tens=[4],recorded_gain_d6=3)
        self.assertEqual(r['code'],'SELF_HELP_SUPPORT_INELIGIBLE')

    def test_061_self_help_mania_ineligible(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='MANIA',units=0,tens=[4],recorded_gain_d6=3)
        self.assertEqual(r['code'],'SELF_HELP_SUPPORT_INELIGIBLE')

    def test_062_self_help_wound_ineligible(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='WOUND',units=0,tens=[4],recorded_gain_d6=3)
        self.assertEqual(r['code'],'SELF_HELP_SUPPORT_INELIGIBLE')

    def test_063_self_help_mythos_ineligible(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='CTHULHU_MYTHOS',units=0,tens=[4],recorded_gain_d6=3)
        self.assertEqual(r['code'],'SELF_HELP_SUPPORT_INELIGIBLE')

    def test_064_self_help_critical_allows_new_key_nomination(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=1,tens=[0],recorded_gain_d6=3)
        self.assertEqual(r['success_level'],'CRITICAL')
        self.assertTrue(r['new_key_connection_nomination_allowed'])

    def test_065_key_critical_also_allows_nomination(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='KEY_CONNECTION',units=1,tens=[0,5],recorded_gain_d6=3)
        self.assertTrue(r['new_key_connection_nomination_allowed'])

    def test_066_self_help_caps_at_max(self):
        r=treatment.self_help(current_san=78,cthulhu_mythos=20,support_type='OTHER_SUPPORT',units=0,tens=[4],recorded_gain_d6=6)
        self.assertEqual(r['SAN'],79)
        self.assertEqual(r['san_gain'],1)

    def test_067_self_help_failure_at_one_san_becomes_permanent(self):
        r=treatment.self_help(current_san=1,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[8])
        self.assertEqual(r['SAN'],0)
        self.assertTrue(r['permanent_insanity'])

    def test_068_private_care_replay_stable(self):
        kwargs=dict(care_type='PRIVATE',current_san=50,cthulhu_mythos=0,recorded_treatment_roll=50,recorded_gain_d3=2,san_units=0,san_tens=[4])
        self.assertEqual(treatment.monthly_indefinite_care(**kwargs),treatment.monthly_indefinite_care(**kwargs))

    def test_069_psychotherapy_replay_stable(self):
        kwargs=dict(current_san=50,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[4],recorded_gain_d3=2)
        self.assertEqual(treatment.psychotherapy_month(**kwargs),treatment.psychotherapy_month(**kwargs))

    def test_070_self_help_replay_stable(self):
        kwargs=dict(current_san=60,cthulhu_mythos=0,support_type='KEY_CONNECTION',units=5,tens=[7,2],recorded_gain_d6=4,indefinite_insanity_active=True)
        self.assertEqual(treatment.self_help(**kwargs),treatment.self_help(**kwargs))

    def test_071_no_randomness_private_care(self):
        self.assertFalse(self.private()['randomness_generated'])

    def test_072_no_randomness_psychotherapy(self):
        r=treatment.psychotherapy_month(current_san=50,cthulhu_mythos=0,analyst_skill=60,units=0,tens=[4],recorded_gain_d3=2)
        self.assertFalse(r['randomness_generated'])

    def test_073_no_randomness_self_help(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[4],recorded_gain_d6=2)
        self.assertFalse(r['randomness_generated'])

    def test_074_no_automatic_backstory_text(self):
        r=treatment.self_help(current_san=60,cthulhu_mythos=0,support_type='OTHER_SUPPORT',units=0,tens=[8])
        self.assertNotIn('backstory_text',r)

    def test_075_no_optional_insane_insight_or_mythos_hardened(self):
        self.assertFalse(hasattr(treatment,'insane_insight'))
        self.assertFalse(hasattr(treatment,'mythos_hardened'))


if __name__ == '__main__':
    unittest.main()
