from __future__ import annotations

import unittest

import registry_batch5_dev as registry


class RegistryBatch5EraHardeningTests(unittest.TestCase):
    def test_001_computer_use_blocked_in_1942(self):
        r = registry.resolve_skill('COMPUTER_USE', edu=60, era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'SKILL_NOT_AVAILABLE_IN_ERA')

    def test_002_electronics_blocked_in_1942(self):
        r = registry.resolve_skill('ELECTRONICS', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'SKILL_NOT_AVAILABLE_IN_ERA')

    def test_003_computer_use_still_blocked_in_1920s(self):
        r = registry.resolve_skill('COMPUTER_USE', edu=60, era='1920S')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'SKILL_NOT_AVAILABLE_IN_ERA')

    def test_004_computer_use_resolves_modern(self):
        r = registry.resolve_skill('COMPUTER_USE', edu=60, era='MODERN')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_005_archaeologist_resolves_1942(self):
        r = registry.resolve_occupation('ARCHAEOLOGIST', era='1942')
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['record']['occupation_id'], 'ARCHAEOLOGIST')

    def test_006_computer_programmer_blocked_1942(self):
        r = registry.resolve_occupation('COMPUTER_PROGRAMMER_TECHNICIAN', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_007_hacker_blocked_1942(self):
        r = registry.resolve_occupation('HACKER', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_008_deprogrammer_blocked_1942(self):
        r = registry.resolve_occupation('DEPROGRAMMER', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_009_explorer_classic_scope_not_silently_extended_to_1942(self):
        r = registry.resolve_occupation('EXPLORER', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_010_explorer_resolves_classic(self):
        r = registry.resolve_occupation('EXPLORER', era='CLASSIC')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_011_gun_moll_classic_scope_not_silently_extended_to_1942(self):
        r = registry.resolve_occupation('GUN_MOLL', era='1942')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_012_gun_moll_resolves_classic(self):
        r = registry.resolve_occupation('GUN_MOLL', era='1920S')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_013_modern_occupation_resolves_modern(self):
        r = registry.resolve_occupation('DEPROGRAMMER', era='MODERN')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_014_no_era_materialization_unchanged_modern(self):
        r = registry.resolve_occupation('DEPROGRAMMER')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_015_no_era_materialization_unchanged_classic(self):
        r = registry.resolve_occupation('EXPLORER')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_016_unknown_concrete_era_fails_closed_for_scoped_skill(self):
        r = registry.resolve_skill('COMPUTER_USE', edu=60, era='UNCLASSIFIED_ERA')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'SKILL_NOT_AVAILABLE_IN_ERA')

    def test_017_unknown_concrete_era_fails_closed_for_scoped_occupation(self):
        r = registry.resolve_occupation('DEPROGRAMMER', era='UNCLASSIFIED_ERA')
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['code'], 'OCCUPATION_NOT_AVAILABLE_IN_ERA')

    def test_018_unscoped_record_not_blocked_by_unknown_era(self):
        r = registry.resolve_occupation('ARCHAEOLOGIST', era='UNCLASSIFIED_ERA')
        self.assertEqual(r['status'], 'RESOLVED')

    def test_019_parent_compatibility_without_era_preserved(self):
        self.assertEqual(registry.batch4_compatibility()['status'], 'PASS')

    def test_020_registry_identity_not_promoted(self):
        s = registry.registry_summary()
        self.assertFalse(s['authority_promoted'])
        self.assertFalse(s['frozen_parent_modified'])


if __name__ == '__main__':
    unittest.main()
