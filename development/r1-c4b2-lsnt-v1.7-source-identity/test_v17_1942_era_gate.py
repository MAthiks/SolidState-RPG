from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = ROOT / 'development' / 'r1-coc7-registry-batch5'
CREATION2_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
CREATION3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
for p in (REGISTRY_DIR, CREATION2_DIR, CREATION3_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import registry_batch5_dev as registry
import investigator_creation_batch2_dev as creation2
import investigator_creation_batch3_dev as creation3


def dice():
    return {
        'STR':[3,3,3], 'CON':[4,4,4], 'DEX':[5,4,3], 'APP':[3,4,5],
        'POW':[4,4,4], 'LUCK':[3,3,3], 'SIZ':[4,4], 'INT':[5,5], 'EDU':[5,4],
    }


def choices():
    return [
        {'slot_index':0,'skill_id':'APPRAISE','points':20},
        {'slot_index':1,'skill_id':'ARCHAEOLOGY','points':20},
        {'slot_index':2,'skill_id':'HISTORY','points':20},
        {'slot_index':3,'skill_id':'LANGUAGE_OTHER','specialization':'FRENCH','points':20},
        {'slot_index':4,'skill_id':'LIBRARY_USE','points':20},
        {'slot_index':5,'skill_id':'SPOT_HIDDEN','points':20},
        {'slot_index':6,'skill_id':'MECHANICAL_REPAIR','points':20},
        {'slot_index':7,'skill_id':'NAVIGATE','points':20},
    ]


def personal():
    return [
        {'skill_id':'DODGE','points':40}, {'skill_id':'PSYCHOLOGY','points':40},
        {'skill_id':'SPOT_HIDDEN','points':20}, {'skill_id':'FIREARMS_HANDGUN','points':20},
        {'skill_id':'CHARM','points':40},
    ]


def story():
    return {
        'PERSONAL_DESCRIPTION':['Cultured and carefully dressed.'],
        'IDEOLOGY_BELIEFS':['Knowledge should be preserved.'],
        'SIGNIFICANT_PEOPLE':['A trusted former professor.'],
        'MEANINGFUL_LOCATIONS':['The reading room of an old library.'],
        'TREASURED_POSSESSIONS':['A family notebook.'],
        'TRAITS':['Curious and persistent.'],
    }


def batch1_1942(occupation='ARCHAEOLOGIST'):
    return creation2.batch1.creation_preflight(
        recorded_dice=dice(), age=37, physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}],
        occupation_id=occupation, credit_rating=20, era='1942',
    )


class V17Era1942GateTests(unittest.TestCase):
    def test_001_computer_use_blocked_1942(self):
        r = registry.resolve_skill('COMPUTER_USE', edu=60, era='1942')
        self.assertEqual((r['status'], r['code']), ('BLOCKED', 'SKILL_NOT_AVAILABLE_IN_ERA'))

    def test_002_electronics_blocked_1942(self):
        r = registry.resolve_skill('ELECTRONICS', era='1942')
        self.assertEqual((r['status'], r['code']), ('BLOCKED', 'SKILL_NOT_AVAILABLE_IN_ERA'))

    def test_003_modern_occupation_blocked_1942(self):
        r = registry.resolve_occupation('COMPUTER_PROGRAMMER_TECHNICIAN', era='1942')
        self.assertEqual((r['status'], r['code']), ('BLOCKED', 'OCCUPATION_NOT_AVAILABLE_IN_ERA'))

    def test_004_modern_batch5_occupation_blocked_1942(self):
        r = registry.resolve_occupation('DEPROGRAMMER', era='1942')
        self.assertEqual((r['status'], r['code']), ('BLOCKED', 'OCCUPATION_NOT_AVAILABLE_IN_ERA'))

    def test_005_classic_scope_not_assumed_valid_1942(self):
        r = registry.resolve_occupation('EXPLORER', era='1942')
        self.assertEqual((r['status'], r['code']), ('BLOCKED', 'OCCUPATION_NOT_AVAILABLE_IN_ERA'))

    def test_006_unscoped_archaeologist_resolves_1942(self):
        r = registry.resolve_occupation('ARCHAEOLOGIST', era='1942')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_007_creation_batch1_archaeologist_1942_ready(self):
        p1 = batch1_1942()
        self.assertEqual(p1['status'], 'READY_FOR_SKILL_ALLOCATION_BATCH2')
        self.assertEqual(p1['budgets']['occupation_id'], 'ARCHAEOLOGIST')

    def test_008_creation_batch1_modern_occupation_1942_blocked(self):
        p1 = batch1_1942('COMPUTER_PROGRAMMER_TECHNICIAN')
        self.assertEqual(p1['status'], 'BLOCKED')
        self.assertEqual(p1['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')
        self.assertEqual(p1['creation_stage'], 'OCCUPATION_RESOLUTION')

    def test_009_creation_batch2_1942_ready(self):
        p1 = batch1_1942()
        p2 = creation2.creation_batch2_preflight(
            batch1_preflight=p1,
            occupation_selections=choices(),
            personal_interest_allocations=personal(),
            era='1942',
            identity={'name':'V17 1942 Test','gender':'Male','birthplace':'Paris, France'},
            backstory=story(),
            key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0},
        )
        self.assertEqual(p2['status'], 'READY_FOR_EQUIPMENT_FINANCE_BATCH3')

    def test_010_creation_to_atomic_boundary_1942(self):
        p1 = batch1_1942()
        p2 = creation2.creation_batch2_preflight(
            batch1_preflight=p1,
            occupation_selections=choices(), personal_interest_allocations=personal(), era='1942',
            identity={'name':'V17 1942 Atomic','gender':'Male','birthplace':'Paris, France'},
            backstory=story(), key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0},
        )
        r = creation3.prepare_creation_commit(
            batch2_preflight=p2,
            finance_profile={
                'credit_rating':20, 'spending_level_units':10, 'cash_refresh_units':100,
                'asset_value_units':500, 'living_standard_id':'SYNTHETIC_DEV_CR20',
                'adapter_verified':True,
            },
            possessions=[],
        )
        self.assertEqual(r['status'], 'READY_FOR_ATOMIC_COMMIT')
        self.assertEqual(len(r['payload_sha256']), 64)

    def test_011_1920s_behavior_preserved(self):
        self.assertEqual(registry.resolve_skill('COMPUTER_USE', edu=60, era='1920S')['status'], 'BLOCKED')
        self.assertEqual(registry.resolve_occupation('EXPLORER', era='1920S')['status'], 'RESOLVED')

    def test_012_modern_behavior_preserved(self):
        self.assertEqual(registry.resolve_skill('COMPUTER_USE', edu=60, era='MODERN')['status'], 'RESOLVED')
        self.assertEqual(registry.resolve_occupation('DEPROGRAMMER', era='MODERN')['status'], 'RESOLVED')

    def test_013_no_era_reference_materialization_preserved(self):
        self.assertEqual(registry.resolve_occupation('DEPROGRAMMER')['status'], 'RESOLVED')
        self.assertEqual(registry.resolve_occupation('EXPLORER')['status'], 'RESOLVED')

    def test_014_registry_not_promoted(self):
        s = registry.registry_summary()
        self.assertFalse(s['authority_promoted'])
        self.assertFalse(s['frozen_parent_modified'])


if __name__ == '__main__':
    unittest.main()
