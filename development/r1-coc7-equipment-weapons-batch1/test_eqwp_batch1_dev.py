from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_eqwp_batch1_dev as reg

HERE = Path(__file__).resolve().parent
E = json.loads((HERE / 'equipment_batch1.json').read_text())
W = json.loads((HERE / 'weapons_batch1.json').read_text())


class EquipmentWeaponsBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(reg.REGISTRY_ID, 'COC7_RECOVERY_EQUIPMENT_WEAPONS_R1_BATCH1_DEV_V1')
        self.assertEqual(reg.PARENT_REGISTRY_ID, 'COC7_RECOVERY_REGISTRY_R1_BATCH5_DEV_V1')
        self.assertEqual(reg.FROZEN_ANCESTOR_REGISTRY_ID, 'COC7_RECOVERY_REGISTRY_R1_C4_V1')

    def test_002_source_identity(self):
        self.assertEqual(reg.SOURCE_SHA256, 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17')
        self.assertEqual(E['source']['source_pages'], [242,243,244])
        self.assertEqual(W['source']['source_pages'], [250,251,252,253,254])

    def test_003_counts(self):
        self.assertEqual(len(reg.EQUIPMENT), 92)
        self.assertEqual(len(reg.WEAPONS), 61)
        self.assertEqual(len(reg.SKILL_EXTENSIONS), 12)

    def test_004_non_authoritative(self):
        self.assertFalse(E['authority_promoted'])
        self.assertFalse(W['authority_promoted'])
        self.assertFalse(reg.registry_summary()['authority_promoted'])

    def test_005_no_auto_possession_global(self):
        self.assertFalse(E['auto_possession'])
        self.assertFalse(W['auto_possession'])
        self.assertFalse(reg.registry_summary()['auto_possession'])

    def test_006_all_equipment_no_auto_possession(self):
        self.assertTrue(all(not x['auto_possession'] for x in reg.EQUIPMENT.values()))

    def test_007_all_weapons_no_auto_possession(self):
        self.assertTrue(all(not x['auto_possession'] for x in reg.WEAPONS.values()))

    def test_008_unknown_equipment_fail_closed(self):
        self.assertEqual(reg.resolve_equipment('PORTABLE_SHOGGOTH_CONTAINER')['code'], 'EQUIPMENT_RECORD_UNMATERIALIZED')

    def test_009_unknown_weapon_fail_closed(self):
        self.assertEqual(reg.resolve_weapon('MYTHOS_RAY_GUN')['code'], 'WEAPON_RECORD_UNMATERIALIZED')

    def test_010_all_weapon_skill_refs_resolve(self):
        result = reg.validate_all_references()
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(result['weapon_count'], 61)

    def test_011_frozen_c4_weapon_compatibility(self):
        self.assertEqual(reg.frozen_c4_weapon_compatibility()['status'], 'PASS')

    def test_012_parent_occupation_survives(self):
        r = reg.parent.resolve_occupation('ARCHAEOLOGIST', characteristics={'EDU':70})
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['record']['occupation_skill_points'], 280)

    def test_013_source_prices_omitted(self):
        serialized = json.dumps(E) + json.dumps(W)
        self.assertNotIn('cost_20s', serialized.lower())
        self.assertNotIn('price', serialized.lower())

    def test_014_equipment_categories_exact(self):
        cats = {x['category'] for x in reg.EQUIPMENT.values()}
        self.assertEqual(cats, {'OUTDOOR_TRAVEL','WATER_STORAGE','TOOLS','INVESTIGATOR_TOOLS','SHELTER','VEHICLE_ACCESSORY'})

    def test_015_key_equipment_resolves(self):
        for eid in ['BINOCULARS','COMPASS_WITH_LID','ROPE_50_FEET','HANDCUFFS','POCKET_MICROSCOPE','TIRE_REPAIR_KIT']:
            r = reg.resolve_equipment(eid)
            self.assertEqual(r['status'], 'RESOLVED_REFERENCE', eid)
            self.assertFalse(r['auto_possession'])

    def test_016_skill_extension_bases(self):
        expected = {
            'FIGHTING_AXE':15,'FIGHTING_FLAIL':10,'FIGHTING_GARROTE':15,'FIGHTING_SPEAR':20,'FIGHTING_SWORD':20,'FIGHTING_WHIP':5,
            'FIREARMS_BOW':15,'FIREARMS_FLAMETHROWER':10,'FIREARMS_HEAVY_WEAPONS':10,'FIREARMS_MACHINE_GUN':10,'ARTILLERY':1,'DEMOLITIONS':1,
        }
        for sid,base in expected.items():
            r=reg.resolve_skill(sid)
            self.assertEqual(r['status'],'RESOLVED',sid)
            self.assertEqual(r['record']['base'],base,sid)

    def test_017_parent_weapon_skills_still_resolve(self):
        for sid in ['FIREARMS_HANDGUN','FIREARMS_RIFLE','FIREARMS_SHOTGUN','FIREARMS_SMG','FIGHTING_BRAWL','THROW','ELECTRICAL_REPAIR']:
            self.assertEqual(reg.resolve_skill(sid,dex=50,edu=50,era='1920S')['status'],'RESOLVED',sid)

    def test_018_sword_cane_record(self):
        r=reg.resolve_weapon('SWORD_LIGHT')['record']
        self.assertEqual(r['skill_id'],'FIGHTING_SWORD')
        self.assertEqual(r['damage'],'1D6+DB')
        self.assertTrue(r['impale'])

    def test_019_tobrouk_relevant_weapons_present(self):
        for wid in ['GARAND_M1_M2','LEE_ENFIELD_303','THOMPSON_SMG','BREN_GUN','BROWNING_AUTO_RIFLE_M1918','HAND_GRENADE','FLAMETHROWER']:
            self.assertEqual(reg.resolve_weapon(wid)['status'],'RESOLVED_MECHANICS',wid)

    def test_020_weapon_records_carry_provenance(self):
        self.assertTrue(all(250 <= x['source_page'] <= 254 for x in reg.WEAPONS.values()))


def add_per_equipment_tests():
    for eid in sorted(reg.EQUIPMENT):
        def test(self, eid=eid):
            r=reg.resolve_equipment(eid)
            self.assertEqual(r['status'],'RESOLVED_REFERENCE')
            self.assertEqual(r['record']['equipment_id'],eid)
            self.assertFalse(r['record']['auto_possession'])
        setattr(EquipmentWeaponsBatch1Tests, f'test_equipment_{eid.lower()}', test)


def add_per_weapon_tests():
    for wid in sorted(reg.WEAPONS):
        def test(self, wid=wid):
            r=reg.resolve_weapon(wid)
            self.assertEqual(r['status'],'RESOLVED_MECHANICS',r)
            self.assertEqual(r['record']['weapon_id'],wid)
            self.assertFalse(r['auto_possession'])
            self.assertIn(r['record']['source_page'], [250,251,252,253,254])
        setattr(EquipmentWeaponsBatch1Tests, f'test_weapon_{wid.lower()}', test)

add_per_equipment_tests()
add_per_weapon_tests()

if __name__ == '__main__':
    unittest.main()
