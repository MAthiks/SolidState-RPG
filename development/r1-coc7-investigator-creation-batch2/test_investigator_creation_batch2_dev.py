from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import investigator_creation_batch2_dev as creation


def dice():
    return {
        'STR': [3,3,3], 'CON': [4,4,4], 'DEX': [5,4,3], 'APP': [3,4,5],
        'POW': [4,4,4], 'LUCK': [3,3,3], 'SIZ': [4,4], 'INT': [5,5], 'EDU': [5,4],
    }


def batch1_preflight(occupation='ARCHAEOLOGIST', credit=20, choice=None):
    return creation.batch1.creation_preflight(
        recorded_dice=dice(), age=37, physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id=occupation,
        credit_rating=credit, era='1920S', occupation_choice_characteristic=choice,
    )


def arch_choices(points=20):
    return [
        {'slot_index':0,'skill_id':'APPRAISE','points':points},
        {'slot_index':1,'skill_id':'ARCHAEOLOGY','points':points},
        {'slot_index':2,'skill_id':'HISTORY','points':points},
        {'slot_index':3,'skill_id':'LANGUAGE_OTHER','specialization':'FRENCH','points':points},
        {'slot_index':4,'skill_id':'LIBRARY_USE','points':points},
        {'slot_index':5,'skill_id':'SPOT_HIDDEN','points':points},
        {'slot_index':6,'skill_id':'MECHANICAL_REPAIR','points':points},
        {'slot_index':7,'skill_id':'NAVIGATE','points':points},
    ]


def personal():
    return [
        {'skill_id':'DODGE','points':40},
        {'skill_id':'PSYCHOLOGY','points':40},
        {'skill_id':'SPOT_HIDDEN','points':20},
        {'skill_id':'FIREARMS_HANDGUN','points':20},
        {'skill_id':'CHARM','points':40},
    ]


def identity():
    return {'name':'Mathieu Test','gender':'Male','birthplace':'Paris, France'}


def story():
    return {
        'PERSONAL_DESCRIPTION':['Cultured and carefully dressed.'],
        'IDEOLOGY_BELIEFS':['Knowledge should be preserved.'],
        'SIGNIFICANT_PEOPLE':['A trusted former professor.'],
        'MEANINGFUL_LOCATIONS':['The reading room of an old library.'],
        'TREASURED_POSSESSIONS':['A family notebook.'],
        'TRAITS':['Curious and persistent.'],
    }


def key():
    return {'category':'TREASURED_POSSESSIONS','entry_index':0}


class InvestigatorCreationBatch2Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(creation.MODULE_ID, 'COC7_INVESTIGATOR_CREATION_R1_BATCH2_DEV_V1')

    def test_002_parent_identity(self):
        self.assertEqual(creation.PARENT_MODULE_ID, 'COC7_INVESTIGATOR_CREATION_R1_BATCH1_DEV_V1')

    def test_003_parent_proof(self):
        self.assertEqual(creation.PARENT_HARDENED_PROOF, 2414)

    def test_004_source_hash(self):
        self.assertEqual(creation.INVESTIGATOR_SHA256, 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17')

    def test_005_registry_identity(self):
        self.assertEqual(creation.REGISTRY_ID, 'COC7_RECOVERY_REGISTRY_R1_BATCH5_DEV_V1')

    def test_006_slot_schema_audit_pass(self):
        r=creation.occupation_slot_schema_audit()
        self.assertEqual(r['status'],'PASS',r)

    def test_007_slot_schema_audit_114(self):
        self.assertEqual(creation.occupation_slot_schema_audit()['occupation_count'],114)

    def test_008_archaeologist_eight_slots(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices(),characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['status'],'RESOLVED')
        self.assertEqual(len(r['selections']),8)

    def test_009_arch_language_specialization_required(self):
        c=arch_choices(); c[3].pop('specialization')
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SPECIALIZATION_REQUIRED')

    def test_010_arch_wrong_skill_blocks(self):
        c=arch_choices(); c[0]['skill_id']='CHARM'
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SKILL_SLOT_MISMATCH')

    def test_011_arch_wrong_slot_index_blocks(self):
        c=arch_choices(); c[0]['slot_index']=1
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SELECTION_SLOT_INDEX_MISMATCH')

    def test_012_arch_requires_exactly_eight(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices()[:-1],characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'EXACTLY_EIGHT_OCCUPATION_SKILL_SELECTIONS_REQUIRED')

    def test_013_arch_points_nonnegative(self):
        c=arch_choices(); c[1]['points']=-1
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SKILL_POINTS_INVALID')

    def test_014_arch_points_bool_blocks(self):
        c=arch_choices(); c[1]['points']=True
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SKILL_POINTS_INVALID')

    def test_015_arch_choice_navigate_valid(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices(),characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['selections'][7]['skill']['skill_id'],'NAVIGATE')

    def test_016_arch_choice_wrong_eighth_blocks(self):
        c=arch_choices(); c[7]['skill_id']='CHARM'
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_CHOICE_NOT_ALLOWED')

    def test_017_no_auto_skill_selection(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices(),characteristics=p['aged']['characteristics'],era='1920S')
        self.assertFalse(r['automatic_skill_selection'])

    def test_018_no_auto_specialization(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices(),characteristics=p['aged']['characteristics'],era='1920S')
        self.assertFalse(r['automatic_specialization_selection'])

    def test_019_skill_allocation_resolves(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['status'],'RESOLVED')

    def test_020_occupation_budget_300(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['occupation_budget'],300)

    def test_021_occupation_spent_160(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['occupation_spent'],160)

    def test_022_unspent_occupation_lost(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['occupation_points_lost_unspent'],140)

    def test_023_personal_budget_160(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['personal_interest_budget'],160)

    def test_024_personal_spent_160(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['personal_interest_spent'],160)

    def test_025_no_personal_points_lost(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['personal_interest_points_lost_unspent'],0)

    def test_026_personal_can_raise_occupation_skill(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['skills']['SPOT_HIDDEN']['personal_interest_points'],20)
        self.assertEqual(r['skills']['SPOT_HIDDEN']['occupation_points'],20)

    def test_027_skill_total_base_plus_points(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        s=r['skills']['SPOT_HIDDEN']
        self.assertEqual(s['full'],s['base']+40)

    def test_028_skill_half(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        s=r['skills']['SPOT_HIDDEN']; self.assertEqual(s['half'],s['full']//2)

    def test_029_skill_fifth(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        s=r['skills']['SPOT_HIDDEN']; self.assertEqual(s['fifth'],s['full']//5)

    def test_030_credit_rating_preserved(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S')
        self.assertEqual(r['credit_rating'],20)

    def test_031_occupation_overbudget_blocks(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(points=50),personal_interest_allocations=[],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_ALLOCATION_EXCEEDS_BUDGET')

    def test_032_personal_overbudget_blocks(self):
        p=[{'skill_id':'DODGE','points':161}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['code'],'PERSONAL_INTEREST_ALLOCATION_EXCEEDS_BUDGET')

    def test_033_personal_negative_blocks(self):
        p=[{'skill_id':'DODGE','points':-1}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['code'],'PERSONAL_INTEREST_POINTS_INVALID')

    def test_034_personal_mythos_unauthorized_blocks(self):
        p=[{'skill_id':'CTHULHU_MYTHOS','points':1}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['code'],'CTHULHU_MYTHOS_PERSONAL_INTEREST_REQUIRES_KEEPER_AUTHORIZATION')

    def test_035_personal_entry_requires_skill_and_points(self):
        p=[{'skill_id':'DODGE'}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['code'],'PERSONAL_INTEREST_ENTRY_INVALID')

    def test_036_personal_unknown_skill_blocks(self):
        p=[{'skill_id':'NOT_REAL','points':1}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['code'],'SKILL_OR_SPECIALIZATION_UNRESOLVED')

    def test_037_duplicate_personal_entries_sum(self):
        p=[{'skill_id':'DODGE','points':10},{'skill_id':'DODGE','points':15}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertEqual(r['skills']['DODGE']['personal_interest_points'],25)

    def test_038_dodge_base_uses_dex(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=[{'skill_id':'DODGE','points':0}],era='1920S')
        self.assertEqual(r['skills']['DODGE']['base'],batch1_preflight()['aged']['characteristics']['DEX']//2)

    def test_039_language_specialization_key_distinct(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=[],era='1920S')
        self.assertIn('LANGUAGE_OTHER:FRENCH',r['skills'])

    def test_040_batch1_preflight_required(self):
        r=creation.allocate_skills(batch1_preflight={},occupation_selections=arch_choices(),personal_interest_allocations=[],era='1920S')
        self.assertEqual(r['code'],'BATCH1_PREFLIGHT_REQUIRED')

    def test_041_backstory_resolves(self):
        r=creation.validate_backstory(identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(r['status'],'RESOLVED')

    def test_042_backstory_key_text(self):
        r=creation.validate_backstory(identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(r['key_connection']['text'],'A family notebook.')

    def test_043_backstory_no_auto_generation(self):
        self.assertFalse(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=key())['automatic_backstory_generation'])

    def test_044_backstory_no_auto_key(self):
        self.assertFalse(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=key())['automatic_key_connection_selection'])

    def test_045_identity_name_required(self):
        i=identity(); i['name']=' '
        self.assertEqual(creation.validate_backstory(identity=i,backstory=story(),key_connection=key())['code'],'IDENTITY_FIELD_EMPTY')

    def test_046_identity_gender_required(self):
        i=identity(); i['gender']=''
        self.assertEqual(creation.validate_backstory(identity=i,backstory=story(),key_connection=key())['code'],'IDENTITY_FIELD_EMPTY')

    def test_047_identity_birthplace_required(self):
        i=identity(); i['birthplace']=''
        self.assertEqual(creation.validate_backstory(identity=i,backstory=story(),key_connection=key())['code'],'IDENTITY_FIELD_EMPTY')

    def test_048_identity_exact_fields(self):
        i=identity(); i['age']=37
        self.assertEqual(creation.validate_backstory(identity=i,backstory=story(),key_connection=key())['code'],'IDENTITY_FIELDS_REQUIRED')

    def test_049_unknown_backstory_category_blocks(self):
        s=story(); s['SECRET']='x'
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['code'],'BACKSTORY_CATEGORY_UNSUPPORTED')

    def test_050_optional_injury_allowed(self):
        s=story(); s['INJURIES_SCARS']=['Old scar.']
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['status'],'RESOLVED')

    def test_051_optional_phobia_allowed(self):
        s=story(); s['PHOBIAS_MANIAS']=['Fear of enclosed tunnels.']
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['status'],'RESOLVED')

    def test_052_optional_arcane_allowed(self):
        s=story(); s['ARCANE_TOMES_SPELLS_ARTIFACTS']=['None known.']
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['status'],'RESOLVED')

    def test_053_optional_encounter_allowed(self):
        s=story(); s['ENCOUNTERS_WITH_STRANGE_ENTITIES']=['None known.']
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['status'],'RESOLVED')

    def test_054_string_backstory_normalizes_to_list(self):
        s=story(); s['TRAITS']='Curious.'
        r=creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())
        self.assertEqual(r['backstory']['TRAITS'],['Curious.'])

    def test_055_empty_entry_blocks(self):
        s=story(); s['TRAITS']=['']
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())['code'],'BACKSTORY_ENTRY_INVALID')

    def test_056_key_missing_category_blocks(self):
        k={'category':'PHOBIAS_MANIAS','entry_index':0}
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=k)['code'],'KEY_CONNECTION_NOT_PRESENT_IN_BACKSTORY')

    def test_057_key_bad_index_blocks(self):
        k={'category':'TRAITS','entry_index':9}
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=k)['code'],'KEY_CONNECTION_NOT_PRESENT_IN_BACKSTORY')

    def test_058_key_bool_index_blocks(self):
        k={'category':'TRAITS','entry_index':True}
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=k)['code'],'KEY_CONNECTION_NOT_PRESENT_IN_BACKSTORY')

    def test_059_key_exact_fields_required(self):
        k={'category':'TRAITS','entry_index':0,'x':1}
        self.assertEqual(creation.validate_backstory(identity=identity(),backstory=story(),key_connection=k)['code'],'KEY_CONNECTION_REFERENCE_INVALID')

    def test_060_batch2_preflight_ready(self):
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(r['status'],'READY_FOR_EQUIPMENT_FINANCE_BATCH3')

    def test_061_batch2_preflight_not_committed(self):
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertFalse(r['character_state_committed'])

    def test_062_batch2_next_stage(self):
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(r['next_stage'],'EQUIPMENT_FINANCE_AND_ATOMIC_COMMIT_BATCH3')

    def test_063_batch2_no_randomness(self):
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertFalse(r['randomness_generated'])

    def test_064_batch2_skill_failure_stage(self):
        c=arch_choices(); c[0]['skill_id']='CHARM'
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=c,personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(r['creation_stage'],'SKILL_ALLOCATION')

    def test_065_batch2_story_failure_stage(self):
        s=story(); s.pop('TRAITS')
        r=creation.creation_batch2_preflight(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=s,key_connection=key())
        self.assertEqual(r['creation_stage'],'BACKSTORY')

    def test_066_batch2_replay_stable(self):
        kwargs=dict(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=personal(),era='1920S',identity=identity(),backstory=story(),key_connection=key())
        self.assertEqual(creation.creation_batch2_preflight(**copy.deepcopy(kwargs)),creation.creation_batch2_preflight(**copy.deepcopy(kwargs)))

    def test_067_zero_occupation_points_allowed(self):
        c=arch_choices(points=0)
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=c,personal_interest_allocations=[],era='1920S')
        self.assertEqual(r['occupation_spent'],0)
        self.assertEqual(r['occupation_points_lost_unspent'],300)

    def test_068_zero_personal_points_allowed(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=[],era='1920S')
        self.assertEqual(r['personal_interest_spent'],0)
        self.assertEqual(r['personal_interest_points_lost_unspent'],160)

    def test_069_points_can_make_skill_over_100(self):
        c=arch_choices(points=0); c[5]['points']=200
        p=[{'skill_id':'SPOT_HIDDEN','points':100}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=c,personal_interest_allocations=p,era='1920S')
        self.assertGreater(r['skills']['SPOT_HIDDEN']['full'],100)

    def test_070_personal_specialization_distinct(self):
        p=[{'skill_id':'LANGUAGE_OTHER','specialization':'GERMAN','points':10}]
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=p,era='1920S')
        self.assertIn('LANGUAGE_OTHER:GERMAN',r['skills'])

    def test_071_keeper_mythos_flag_must_be_bool(self):
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=arch_choices(),characteristics=p['aged']['characteristics'],era='1920S',keeper_authorized_mythos=1)
        self.assertEqual(r['code'],'KEEPER_MYTHOS_AUTH_FLAG_INVALID')

    def test_072_selection_record_must_be_dict(self):
        c=arch_choices(); c[2]='x'
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_SELECTION_INVALID')

    def test_073_duplicate_occupation_skill_blocks(self):
        c=arch_choices(); c[7]={'slot_index':7,'skill_id':'SCIENCE','specialization':'NAVIGATE','points':0}
        p=batch1_preflight()
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertNotEqual(r['status'],'RESOLVED')

    def test_074_fixed_science_specialization_alienist(self):
        p=batch1_preflight('ALIENIST',20)
        self.assertEqual(p['status'],'READY_FOR_SKILL_ALLOCATION_BATCH2')
        c=[
          {'slot_index':0,'skill_id':'LAW','points':0},{'slot_index':1,'skill_id':'LISTEN','points':0},
          {'slot_index':2,'skill_id':'MEDICINE','points':0},{'slot_index':3,'skill_id':'LANGUAGE_OTHER','specialization':'LATIN','points':0},
          {'slot_index':4,'skill_id':'PSYCHOANALYSIS','points':0},{'slot_index':5,'skill_id':'PSYCHOLOGY','points':0},
          {'slot_index':6,'skill_id':'SCIENCE','specialization':'BIOLOGY','points':0},{'slot_index':7,'skill_id':'SCIENCE','specialization':'CHEMISTRY','points':0},
        ]
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['status'],'RESOLVED')

    def test_075_wrong_fixed_science_specialization_blocks(self):
        p=batch1_preflight('ALIENIST',20)
        c=[
          {'slot_index':0,'skill_id':'LAW','points':0},{'slot_index':1,'skill_id':'LISTEN','points':0},
          {'slot_index':2,'skill_id':'MEDICINE','points':0},{'slot_index':3,'skill_id':'LANGUAGE_OTHER','specialization':'LATIN','points':0},
          {'slot_index':4,'skill_id':'PSYCHOANALYSIS','points':0},{'slot_index':5,'skill_id':'PSYCHOLOGY','points':0},
          {'slot_index':6,'skill_id':'SCIENCE','specialization':'CHEMISTRY','points':0},{'slot_index':7,'skill_id':'SCIENCE','specialization':'CHEMISTRY','points':0},
        ]
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_FIXED_SPECIALIZATION_MISMATCH')

    def test_076_interpersonal_choices_antique_dealer(self):
        p=batch1_preflight('ANTIQUE_DEALER',40)
        c=[
          {'slot_index':0,'skill_id':'ACCOUNTING','points':0},{'slot_index':1,'skill_id':'APPRAISE','points':0},
          {'slot_index':2,'skill_id':'DRIVE_AUTO','points':0},{'slot_index':3,'skill_id':'CHARM','points':0},
          {'slot_index':4,'skill_id':'PERSUADE','points':0},{'slot_index':5,'skill_id':'HISTORY','points':0},
          {'slot_index':6,'skill_id':'LIBRARY_USE','points':0},{'slot_index':7,'skill_id':'NAVIGATE','points':0},
        ]
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['status'],'RESOLVED')

    def test_077_duplicate_interpersonal_choice_blocks(self):
        p=batch1_preflight('ANTIQUE_DEALER',40)
        c=[
          {'slot_index':0,'skill_id':'ACCOUNTING','points':0},{'slot_index':1,'skill_id':'APPRAISE','points':0},
          {'slot_index':2,'skill_id':'DRIVE_AUTO','points':0},{'slot_index':3,'skill_id':'CHARM','points':0},
          {'slot_index':4,'skill_id':'CHARM','points':0},{'slot_index':5,'skill_id':'HISTORY','points':0},
          {'slot_index':6,'skill_id':'LIBRARY_USE','points':0},{'slot_index':7,'skill_id':'NAVIGATE','points':0},
        ]
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'DUPLICATE_OCCUPATION_SKILL_SELECTION')

    def test_078_invalid_interpersonal_choice_blocks(self):
        p=batch1_preflight('ANTIQUE_DEALER',40)
        c=[
          {'slot_index':0,'skill_id':'ACCOUNTING','points':0},{'slot_index':1,'skill_id':'APPRAISE','points':0},
          {'slot_index':2,'skill_id':'DRIVE_AUTO','points':0},{'slot_index':3,'skill_id':'SWIM','points':0},
          {'slot_index':4,'skill_id':'PERSUADE','points':0},{'slot_index':5,'skill_id':'HISTORY','points':0},
          {'slot_index':6,'skill_id':'LIBRARY_USE','points':0},{'slot_index':7,'skill_id':'NAVIGATE','points':0},
        ]
        r=creation.resolve_occupation_skill_choices(occupation_record=p['budgets']['occupation_record'],selections=c,characteristics=p['aged']['characteristics'],era='1920S')
        self.assertEqual(r['code'],'OCCUPATION_INTERPERSONAL_CHOICE_INVALID')

    def test_079_personal_interest_is_list(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations={},era='1920S')
        self.assertEqual(r['code'],'PERSONAL_INTEREST_ALLOCATIONS_INVALID')

    def test_080_story_whitespace_normalizes(self):
        i=identity(); i['name']='  Mathieu Test  '
        r=creation.validate_backstory(identity=i,backstory=story(),key_connection=key())
        self.assertEqual(r['identity']['name'],'Mathieu Test')


def _make_missing_story_test(category):
    def test(self):
        s=story(); s.pop(category)
        r=creation.validate_backstory(identity=identity(),backstory=s,key_connection=key())
        self.assertEqual(r['code'],'BACKSTORY_REQUIRED_CATEGORY_MISSING')
        self.assertIn(category,r['missing'])
    return test

for i, category in enumerate(creation.REQUIRED_BACKSTORY, start=81):
    setattr(InvestigatorCreationBatch2Tests,f'test_{i:03d}_missing_{category.lower()}',_make_missing_story_test(category))


def _make_personal_budget_test(points):
    def test(self):
        r=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=arch_choices(),personal_interest_allocations=[{'skill_id':'DODGE','points':points}],era='1920S')
        self.assertEqual(r['status'],'RESOLVED')
        self.assertEqual(r['personal_interest_spent'],points)
        self.assertEqual(r['personal_interest_points_lost_unspent'],160-points)
    return test

for i, points in enumerate([0,1,10,20,40,60,80,100,120,140,150,160], start=87):
    setattr(InvestigatorCreationBatch2Tests,f'test_{i:03d}_personal_budget_{points}',_make_personal_budget_test(points))


def _make_replay_allocation_test(points):
    def test(self):
        c=arch_choices(points=points)
        a=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=c,personal_interest_allocations=[],era='1920S')
        b=creation.allocate_skills(batch1_preflight=batch1_preflight(),occupation_selections=copy.deepcopy(c),personal_interest_allocations=[],era='1920S')
        self.assertEqual(a,b)
        self.assertFalse(a['randomness_generated'])
    return test

for i, points in enumerate([0,1], start=99):
    setattr(InvestigatorCreationBatch2Tests,f'test_{i:03d}_replay_alloc_{points}',_make_replay_allocation_test(points))


if __name__ == '__main__':
    unittest.main()
