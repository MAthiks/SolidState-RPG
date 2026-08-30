from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BATCH2_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for p in (HERE, BATCH2_DIR, RUNTIME_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import investigator_creation_batch3_dev as creation3
import investigator_creation_batch2_dev as creation2
from runtime_r1.core import RecoveryRuntimeR1


def dice():
    return {
        'STR':[3,3,3], 'CON':[4,4,4], 'DEX':[5,4,3], 'APP':[3,4,5],
        'POW':[4,4,4], 'LUCK':[3,3,3], 'SIZ':[4,4], 'INT':[5,5], 'EDU':[5,4],
    }


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


def story():
    return {
        'PERSONAL_DESCRIPTION':['Cultured and carefully dressed.'],
        'IDEOLOGY_BELIEFS':['Knowledge should be preserved.'],
        'SIGNIFICANT_PEOPLE':['A trusted former professor.'],
        'MEANINGFUL_LOCATIONS':['The reading room of an old library.'],
        'TREASURED_POSSESSIONS':['A family notebook.'],
        'TRAITS':['Curious and persistent.'],
    }


def batch2_ready(name='Mathieu Test'):
    p1 = creation2.batch1.creation_preflight(
        recorded_dice=dice(), age=37, physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST',
        credit_rating=20, era='1920S',
    )
    assert p1['status'] == 'READY_FOR_SKILL_ALLOCATION_BATCH2', p1
    p2 = creation2.creation_batch2_preflight(
        batch1_preflight=p1,
        occupation_selections=arch_choices(),
        personal_interest_allocations=personal(),
        era='1920S',
        identity={'name':name,'gender':'Male','birthplace':'Paris, France'},
        backstory=story(),
        key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0},
    )
    assert p2['status'] == 'READY_FOR_EQUIPMENT_FINANCE_BATCH3', p2
    return p2


def finance_profile(cr=20, verified=True, cash=100, assets=500, spending=10):
    return {
        'credit_rating':cr,
        'spending_level_units':spending,
        'cash_refresh_units':cash,
        'asset_value_units':assets,
        'living_standard_id':'SYNTHETIC_DEV_CR20',
        'adapter_verified':verified,
    }


def possessions():
    return [
        {'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1},
        {'kind':'EQUIPMENT','record_id':'COMPASS_WITH_LID','quantity':1},
        {'kind':'WEAPON','record_id':'SWORD_LIGHT','quantity':1},
    ]


def prepared(name='Mathieu Test', poss=None, profile=None):
    return creation3.prepare_creation_commit(
        batch2_preflight=batch2_ready(name),
        finance_profile=profile or finance_profile(),
        possessions=possessions() if poss is None else poss,
    )


def make_runtime(player_count=1):
    td = tempfile.TemporaryDirectory()
    runtime = RecoveryRuntimeR1(Path(td.name)/'runtime.sqlite')
    result = runtime.new_session([{'name':f'Placeholder {i+1}'} for i in range(player_count)], 'CREATION-B3-TEST')
    assert result['status'] == 'SESSION_READY', result
    runtime._test_tmpdir = td
    return runtime


class InvestigatorCreationBatch3Tests(unittest.TestCase):
    def test_001_module_identity(self):
        self.assertEqual(creation3.MODULE_ID,'COC7_INVESTIGATOR_CREATION_R1_BATCH3_DEV_V1')
    def test_002_parent_identity(self):
        self.assertEqual(creation3.PARENT_MODULE_ID,'COC7_INVESTIGATOR_CREATION_R1_BATCH2_DEV_V1')
    def test_003_parent_proof(self):
        self.assertEqual(creation3.PARENT_HARDENED_PROOF,2514)
    def test_004_finance_identity(self):
        self.assertEqual(creation3.FINANCE_MODULE_ID,'COC7_FINANCE_CREDIT_RATING_R1_BATCH1_DEV_V1')
    def test_005_registry_identity(self):
        self.assertEqual(creation3.EQUIPMENT_WEAPON_REGISTRY_ID,'COC7_RECOVERY_EQUIPMENT_WEAPONS_R1_BATCH1_DEV_V1')
    def test_006_prepare_ready(self):
        self.assertEqual(prepared()['status'],'READY_FOR_ATOMIC_COMMIT')
    def test_007_prepare_hash_present(self):
        self.assertEqual(len(prepared()['payload_sha256']),64)
    def test_008_prepare_no_randomness(self):
        self.assertFalse(prepared()['payload']['randomness_generated'])
    def test_009_prepare_no_auto_equipment(self):
        self.assertFalse(prepared()['payload']['automatic_equipment_selection'])
    def test_010_prepare_no_auto_weapon(self):
        self.assertFalse(prepared()['payload']['automatic_weapon_selection'])
    def test_011_empty_possessions_allowed(self):
        self.assertEqual(prepared(poss=[])['status'],'READY_FOR_ATOMIC_COMMIT')
    def test_012_equipment_resolves(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1}])
        self.assertEqual(r['payload']['inventory'][0]['record_id'],'BINOCULARS')
    def test_013_weapon_resolves(self):
        r=prepared(poss=[{'kind':'WEAPON','record_id':'SWORD_LIGHT','quantity':1}])
        self.assertEqual(r['payload']['inventory'][0]['record_id'],'SWORD_LIGHT')
    def test_014_unknown_equipment_blocks(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'NOPE','quantity':1}])
        self.assertEqual(r['code'],'POSSESSION_REGISTRY_RECORD_UNRESOLVED')
    def test_015_unknown_weapon_blocks(self):
        r=prepared(poss=[{'kind':'WEAPON','record_id':'NOPE','quantity':1}])
        self.assertEqual(r['code'],'POSSESSION_REGISTRY_RECORD_UNRESOLVED')
    def test_016_bad_kind_blocks(self):
        r=prepared(poss=[{'kind':'MAGIC','record_id':'BINOCULARS','quantity':1}])
        self.assertEqual(r['code'],'POSSESSION_KIND_INVALID')
    def test_017_zero_quantity_blocks(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':0}])
        self.assertEqual(r['code'],'POSSESSION_QUANTITY_INVALID')
    def test_018_bool_quantity_blocks(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':True}])
        self.assertEqual(r['code'],'POSSESSION_QUANTITY_INVALID')
    def test_019_duplicate_possession_blocks(self):
        p=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1},{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':2}]
        self.assertEqual(prepared(poss=p)['code'],'DUPLICATE_POSSESSION_ENTRY')
    def test_020_malformed_possession_blocks(self):
        self.assertEqual(prepared(poss=[{'kind':'EQUIPMENT'}])['code'],'POSSESSION_ENTRY_SHAPE_INVALID')
    def test_021_finance_cr_match(self):
        self.assertEqual(prepared()['payload']['finance']['credit_rating'],20)
    def test_022_finance_cr_mismatch_blocks(self):
        self.assertEqual(prepared(profile=finance_profile(cr=21))['code'],'FINANCE_CREDIT_RATING_MISMATCH')
    def test_023_unverified_finance_blocks(self):
        self.assertEqual(prepared(profile=finance_profile(verified=False))['code'],'PRIVATE_FINANCE_PROFILE_UNRESOLVED')
    def test_024_negative_cash_blocks(self):
        self.assertEqual(prepared(profile=finance_profile(cash=-1))['code'],'PRIVATE_FINANCE_PROFILE_UNRESOLVED')
    def test_025_negative_assets_blocks(self):
        self.assertEqual(prepared(profile=finance_profile(assets=-1))['code'],'PRIVATE_FINANCE_PROFILE_UNRESOLVED')
    def test_026_negative_spending_blocks(self):
        self.assertEqual(prepared(profile=finance_profile(spending=-1))['code'],'PRIVATE_FINANCE_PROFILE_UNRESOLVED')
    def test_027_bad_finance_shape_blocks(self):
        p=finance_profile(); p['extra']=1
        self.assertEqual(prepared(profile=p)['code'],'FINANCE_PROFILE_SHAPE_INVALID')
    def test_028_batch2_required(self):
        r=creation3.prepare_creation_commit(batch2_preflight={},finance_profile=finance_profile(),possessions=[])
        self.assertEqual(r['code'],'BATCH2_PREFLIGHT_REQUIRED')
    def test_029_materialize_resolves(self):
        self.assertEqual(creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())['status'],'RESOLVED')
    def test_030_materialized_name(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared('Mathieu X'))
        self.assertEqual(r['character']['name'],'Mathieu X')
    def test_031_materialized_owner(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['owner_id'],'P1')
    def test_032_materialized_age(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['age'],37)
    def test_033_materialized_hp(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertGreater(r['character']['stats']['HP'],0)
    def test_034_materialized_san(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['stats']['SAN'],r['character']['stats']['POW'])
    def test_035_materialized_luck(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertIn('Luck',r['character']['stats'])
    def test_036_materialized_archaeologist(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['occupation']['occupation_id'],'ARCHAEOLOGIST')
    def test_037_materialized_credit_rating(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['occupation']['credit_rating'],20)
    def test_038_materialized_finance_adapter(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertTrue(r['character']['finance']['private_adapter_verified'])
    def test_039_materialized_private_table_not_embedded(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertFalse(r['character']['finance']['private_table_values_embedded'])
    def test_040_materialized_inventory_count(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(len(r['character']['inventory']),3)
    def test_041_materialized_backstory(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertIn('TRAITS',r['character']['backstory'])
    def test_042_materialized_key_connection(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['character']['key_connection']['category'],'TREASURED_POSSESSIONS')
    def test_043_materialized_creation_complete(self):
        r=creation3.materialize_character_state(player_id='P1',character_id='C1',ready=prepared())
        self.assertTrue(r['character']['creation']['complete'])
    def test_044_tampered_ready_hash_blocks(self):
        r=prepared(); r['payload']['finance']['cash_refresh_units']+=1
        self.assertEqual(creation3.materialize_character_state(player_id='P1',character_id='C1',ready=r)['code'],'CREATION_COMMIT_PAYLOAD_HASH_MISMATCH')
    def test_045_atomic_commit_success(self):
        rt=make_runtime(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['status'],'COMMIT'); rt.close()
    def test_046_atomic_commit_changes_digest(self):
        rt=make_runtime(); before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared())
        self.assertNotEqual(before,r['after']); rt.close()
    def test_047_wrong_actor_zero_mutation(self):
        rt=make_runtime(); before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P2',character_id='C1',ready=prepared())
        self.assertEqual(r['code'],'ACTOR_CONTROL_MISMATCH'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_048_wrong_character_zero_mutation(self):
        rt=make_runtime(2); before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C2',ready=prepared())
        self.assertEqual(r['code'],'ACTOR_CONTROL_MISMATCH'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_049_duplicate_commit_zero_mutation(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['code'],'CHARACTER_CREATION_ALREADY_COMMITTED'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_050_tampered_ready_zero_mutation(self):
        rt=make_runtime(); ready=prepared(); ready['payload']['inventory']=[]; before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=ready)
        self.assertEqual(r['code'],'CREATION_COMMIT_PAYLOAD_HASH_MISMATCH'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_051_current_and_initial_match_after_creation(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); s=rt.state()
        self.assertEqual(s['characters']['C1'],s['initial_characters']['C1']); rt.close()
    def test_052_creation_commit_recorded(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); s=rt.state()
        self.assertEqual(s['creation_commits'][0]['player_id'],'P1'); rt.close()
    def test_053_player_view_sees_own_created_character(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); v=rt.player_view('P1')
        self.assertEqual(v['character']['name'],'Mathieu Test'); rt.close()
    def test_054_verify_journal_matches_after_creation(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH'); rt.close()
    def test_055_action_after_creation_replays(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); rt.append_player_action('P1','C1','TEST',50,-1)
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH'); rt.close()
    def test_056_save_restore_after_creation(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); bundle=rt.save_bundle(); before=rt.state_digest(); r=rt.restore_bundle(bundle)
        self.assertEqual(r['status'],'RESTORED_STRICT'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_057_play_started_blocks_creation(self):
        rt=make_runtime(); rt.append_player_action('P1','C1','BEFORE_CREATION',50,0); before=rt.state_digest(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared())
        self.assertEqual(r['code'],'CREATION_AFTER_PLAY_STARTED_BLOCKED'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_058_four_players_commit(self):
        rt=make_runtime(4)
        for i in range(1,5): self.assertEqual(creation3.commit_investigator_atomic(runtime=rt,player_id=f'P{i}',character_id=f'C{i}',ready=prepared(f'Investigator {i}'))['status'],'COMMIT')
        self.assertEqual(len(rt.state()['creation_commits']),4); rt.close()
    def test_059_four_players_replay_baseline(self):
        rt=make_runtime(4)
        for i in range(1,5): creation3.commit_investigator_atomic(runtime=rt,player_id=f'P{i}',character_id=f'C{i}',ready=prepared(f'Investigator {i}'))
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH'); rt.close()
    def test_060_four_players_ownership_preserved(self):
        rt=make_runtime(4)
        for i in range(1,5): creation3.commit_investigator_atomic(runtime=rt,player_id=f'P{i}',character_id=f'C{i}',ready=prepared(f'Investigator {i}'))
        self.assertTrue(all(rt.state()['characters'][f'C{i}']['owner_id']==f'P{i}' for i in range(1,5))); rt.close()
    def test_061_commit_sequence_increments(self):
        rt=make_runtime(2); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); creation3.commit_investigator_atomic(runtime=rt,player_id='P2',character_id='C2',ready=prepared('B'))
        self.assertEqual(rt.state()['commit_sequence'],2); rt.close()
    def test_062_empty_inventory_commits(self):
        rt=make_runtime(); r=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared(poss=[]))
        self.assertEqual(r['status'],'COMMIT'); self.assertEqual(rt.state()['characters']['C1']['inventory'],[]); rt.close()
    def test_063_quantity_preserved(self):
        p=[{'kind':'EQUIPMENT','record_id':'BATTERIES','quantity':3}]; rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared(poss=p))
        self.assertEqual(rt.state()['characters']['C1']['inventory'][0]['quantity'],3); rt.close()
    def test_064_registry_metadata_preserved(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1}])
        self.assertEqual(r['payload']['inventory'][0]['registry_id'],creation3.EQUIPMENT_WEAPON_REGISTRY_ID)
    def test_065_source_hash_preserved_not_prose(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1}])
        self.assertEqual(len(r['payload']['inventory'][0]['source_sha256']),64)
    def test_066_no_item_name_copied_into_inventory(self):
        r=prepared(poss=[{'kind':'EQUIPMENT','record_id':'BINOCULARS','quantity':1}])
        self.assertNotIn('name',r['payload']['inventory'][0])
    def test_067_finance_cash_starts_from_verified_refresh(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); self.assertEqual(rt.state()['characters']['C1']['finance']['cash_units'],100); rt.close()
    def test_068_finance_assets_preserved(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); self.assertEqual(rt.state()['characters']['C1']['finance']['asset_value_units'],500); rt.close()
    def test_069_finance_spending_preserved(self):
        rt=make_runtime(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=prepared()); self.assertEqual(rt.state()['characters']['C1']['finance']['spending_level_units'],10); rt.close()
    def test_070_creation_payload_hash_stored(self):
        rt=make_runtime(); ready=prepared(); creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=ready); self.assertEqual(rt.state()['characters']['C1']['creation']['payload_sha256'],ready['payload_sha256']); rt.close()


# 15 quantity/replay stress cases => tests 071..085
for offset, quantity in enumerate(range(1,16), start=71):
    def make_quantity_test(q):
        def test(self):
            poss=[{'kind':'EQUIPMENT','record_id':'BATTERIES','quantity':q}]
            ready=prepared(poss=poss)
            self.assertEqual(ready['status'],'READY_FOR_ATOMIC_COMMIT')
            rt=make_runtime(); result=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C1',ready=ready)
            self.assertEqual(result['status'],'COMMIT')
            self.assertEqual(rt.state()['characters']['C1']['inventory'][0]['quantity'],q)
            self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH')
            rt.close()
        return test
    setattr(InvestigatorCreationBatch3Tests, f'test_{offset:03d}_quantity_{quantity}', make_quantity_test(quantity))

# 10 deterministic prepare repetitions => tests 086..095
for offset in range(86,96):
    def make_determinism_test(index):
        def test(self):
            a=prepared(name=f'Deterministic {index}')
            b=prepared(name=f'Deterministic {index}')
            self.assertEqual(a,b)
            self.assertEqual(a['payload_sha256'],b['payload_sha256'])
        return test
    setattr(InvestigatorCreationBatch3Tests, f'test_{offset:03d}_deterministic_prepare', make_determinism_test(offset))

# 5 player-count/save-resume stress cases => tests 096..100
for offset, count in enumerate([1,2,3,4,4], start=96):
    def make_party_test(player_count, marker):
        def test(self):
            rt=make_runtime(player_count)
            for i in range(1,player_count+1):
                ready=prepared(name=f'Party {marker} Investigator {i}')
                r=creation3.commit_investigator_atomic(runtime=rt,player_id=f'P{i}',character_id=f'C{i}',ready=ready)
                self.assertEqual(r['status'],'COMMIT')
            bundle=rt.save_bundle(); digest=rt.state_digest()
            self.assertEqual(rt.restore_bundle(bundle)['status'],'RESTORED_STRICT')
            self.assertEqual(rt.state_digest(),digest)
            self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH')
            rt.close()
        return test
    setattr(InvestigatorCreationBatch3Tests, f'test_{offset:03d}_party_{count}_save_resume', make_party_test(count,offset))


if __name__ == '__main__':
    unittest.main()
