from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BATCH3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
BATCH2_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for p in (HERE, BATCH3_DIR, BATCH2_DIR, RUNTIME_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import investigator_creation_batch4_dev as creation4
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


def batch2_ready(name):
    p1 = creation2.batch1.creation_preflight(
        recorded_dice=dice(), age=37, physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST',
        credit_rating=20, era='1920S',
    )
    assert p1['status'] == 'READY_FOR_SKILL_ALLOCATION_BATCH2', p1
    p2 = creation2.creation_batch2_preflight(
        batch1_preflight=p1, occupation_selections=arch_choices(),
        personal_interest_allocations=personal(), era='1920S',
        identity={'name':name,'gender':'Male','birthplace':'Paris, France'},
        backstory=story(), key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0},
    )
    assert p2['status'] == 'READY_FOR_EQUIPMENT_FINANCE_BATCH3', p2
    return p2


def prepared(name='Mathieu Test'):
    return creation3.prepare_creation_commit(
        batch2_preflight=batch2_ready(name),
        finance_profile={
            'credit_rating':20, 'spending_level_units':10, 'cash_refresh_units':100,
            'asset_value_units':500, 'living_standard_id':'SYNTHETIC_DEV_CR20',
            'adapter_verified':True,
        },
        possessions=[],
    )


def make_runtime(player_count=1, session='CREATION-B4-TEST'):
    td = tempfile.TemporaryDirectory()
    runtime = RecoveryRuntimeR1(Path(td.name)/'runtime.sqlite')
    result = runtime.new_session([{'name':f'Placeholder {i+1}'} for i in range(player_count)], session)
    assert result['status'] == 'SESSION_READY', result
    runtime._test_tmpdir = td
    return runtime


def commit_player(runtime, number, name=None):
    pid=f'P{number}'; cid=f'C{number}'
    return creation3.commit_investigator_atomic(
        runtime=runtime, player_id=pid, character_id=cid,
        ready=prepared(name or f'Investigator {number}'),
    )


class InvestigatorCreationBatch4Tests(unittest.TestCase):
    def test_001_module_identity(self):
        self.assertEqual(creation4.MODULE_ID,'COC7_INVESTIGATOR_CREATION_R1_BATCH4_DEV_V1')

    def test_002_parent_identity(self):
        self.assertEqual(creation4.PARENT_MODULE_ID,'COC7_INVESTIGATOR_CREATION_R1_BATCH3_DEV_V1')

    def test_003_parent_proof(self):
        self.assertEqual(creation4.PARENT_HARDENED_PROOF,2614)

    def test_004_fresh_party_pending(self):
        rt=make_runtime(); r=creation4.party_creation_status(runtime=rt)
        self.assertEqual(r['status'],'PENDING_CREATION'); rt.close()

    def test_005_pending_list_exact(self):
        rt=make_runtime(2); r=creation4.party_creation_status(runtime=rt)
        self.assertEqual([x['player_id'] for x in r['pending']],['P1','P2']); rt.close()

    def test_006_single_commit_ready_to_finalize(self):
        rt=make_runtime(); self.assertEqual(commit_player(rt,1)['status'],'COMMIT')
        self.assertEqual(creation4.party_creation_status(runtime=rt)['status'],'READY_TO_FINALIZE'); rt.close()

    def test_007_finalize_commit(self):
        rt=make_runtime(); commit_player(rt,1); r=creation4.finalize_party_creation_atomic(runtime=rt)
        self.assertEqual(r['status'],'COMMIT'); rt.close()

    def test_008_finalize_sets_play_ready(self):
        rt=make_runtime(); commit_player(rt,1); creation4.finalize_party_creation_atomic(runtime=rt)
        self.assertEqual(rt.state()['interface_session']['phase'],'PLAY_READY'); rt.close()

    def test_009_finalization_record_bound(self):
        rt=make_runtime(); commit_player(rt,1); creation4.finalize_party_creation_atomic(runtime=rt)
        s=rt.state(); self.assertEqual(s['creation_finalization']['schema'],creation4.FINALIZATION_SCHEMA)
        self.assertEqual(len(s['creation_finalization']['roster_sha256']),64); rt.close()

    def test_010_duplicate_finalize_zero_mutation(self):
        rt=make_runtime(); commit_player(rt,1); creation4.finalize_party_creation_atomic(runtime=rt); before=rt.state_digest()
        r=creation4.finalize_party_creation_atomic(runtime=rt)
        self.assertEqual(r['code'],'PARTY_CREATION_ALREADY_FINALIZED'); self.assertEqual(before,rt.state_digest()); rt.close()

    def test_011_incomplete_finalize_zero_mutation(self):
        rt=make_runtime(2); commit_player(rt,1); before=rt.state_digest(); r=creation4.finalize_party_creation_atomic(runtime=rt)
        self.assertEqual(r['code'],'PARTY_CREATION_INCOMPLETE'); self.assertEqual(before,rt.state_digest()); rt.close()

    def test_012_independent_failed_second_creation_preserves_first(self):
        rt=make_runtime(2); commit_player(rt,1); first=copy.deepcopy(rt.state()['characters']['C1']); before=rt.state_digest()
        bad=creation3.commit_investigator_atomic(runtime=rt,player_id='P1',character_id='C2',ready=prepared('Bad Actor'))
        self.assertEqual(bad['code'],'ACTOR_CONTROL_MISMATCH'); self.assertEqual(before,rt.state_digest())
        self.assertEqual(first,rt.state()['characters']['C1']); self.assertEqual(creation4.party_creation_status(runtime=rt)['status'],'PENDING_CREATION'); rt.close()

    def test_013_two_complete_ready(self):
        rt=make_runtime(2); commit_player(rt,1); commit_player(rt,2)
        self.assertEqual(creation4.party_creation_status(runtime=rt)['status'],'READY_TO_FINALIZE'); rt.close()

    def test_014_action_before_finalize_zero_mutation(self):
        rt=make_runtime(); commit_player(rt,1); before=rt.state_digest()
        r=creation4.append_player_action_after_creation(runtime=rt,player_id='P1',character_id='C1',action_id='WAIT',roll=50)
        self.assertEqual(r['code'],'PARTY_NOT_PLAY_READY'); self.assertEqual(before,rt.state_digest()); rt.close()

    def test_015_action_after_finalize_commits(self):
        rt=make_runtime(); commit_player(rt,1); creation4.finalize_party_creation_atomic(runtime=rt)
        r=creation4.append_player_action_after_creation(runtime=rt,player_id='P1',character_id='C1',action_id='MOVE',roll=50)
        self.assertEqual(r['status'],'COMMIT'); rt.close()

    def test_016_strict_replay_after_finalization_and_action(self):
        rt=make_runtime(); commit_player(rt,1); creation4.finalize_party_creation_atomic(runtime=rt)
        creation4.append_player_action_after_creation(runtime=rt,player_id='P1',character_id='C1',action_id='HURT',roll=50,delta=-1)
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH'); rt.close()

    def test_017_save_restore_preserves_finalization(self):
        rt=make_runtime(2); commit_player(rt,1); commit_player(rt,2); creation4.finalize_party_creation_atomic(runtime=rt); bundle=rt.save_bundle()
        td=tempfile.TemporaryDirectory(); restored=RecoveryRuntimeR1(Path(td.name)/'restore.sqlite')
        self.assertEqual(restored.restore_bundle(bundle)['status'],'RESTORED_STRICT')
        self.assertEqual(creation4.party_creation_status(runtime=restored)['status'],'FINALIZED')
        restored.close(); rt.close(); td.cleanup()

    def test_018_wrong_actor_play_zero_mutation(self):
        rt=make_runtime(2); commit_player(rt,1); commit_player(rt,2); creation4.finalize_party_creation_atomic(runtime=rt); before=rt.state_digest()
        r=creation4.append_player_action_after_creation(runtime=rt,player_id='P1',character_id='C2',action_id='NOPE',roll=50)
        self.assertEqual(r['code'],'ACTOR_CONTROL_MISMATCH'); self.assertEqual(before,rt.state_digest()); rt.close()

    def test_019_tampered_creation_commit_detected(self):
        rt=make_runtime(); commit_player(rt,1); s=rt.state(); s['creation_commits'][0]['creation_payload_sha256']='0'*64; rt._commit_state(s)
        self.assertEqual(creation4.party_creation_status(runtime=rt)['code'],'CREATION_COMMIT_BINDING_MISMATCH'); rt.close()

    def test_020_baseline_mismatch_before_play_detected(self):
        rt=make_runtime(); commit_player(rt,1); s=rt.state(); s['initial_characters']['C1']['name']='Tampered'; rt._commit_state(s)
        self.assertEqual(creation4.party_creation_status(runtime=rt)['code'],'CURRENT_INITIAL_BASELINE_MISMATCH_BEFORE_PLAY'); rt.close()


def _make_matrix_test(index: int):
    player_count = (index % 4) + 1
    def test(self):
        rt=make_runtime(player_count,session=f'B4-MATRIX-{index:02d}')
        initial=creation4.party_creation_status(runtime=rt)
        self.assertEqual(initial['status'],'PENDING_CREATION')
        for n in range(1,player_count+1):
            result=commit_player(rt,n,name=f'Matrix {index} Player {n}')
            self.assertEqual(result['status'],'COMMIT')
            status=creation4.party_creation_status(runtime=rt)
            expected='READY_TO_FINALIZE' if n==player_count else 'PENDING_CREATION'
            self.assertEqual(status['status'],expected)
        finalized=creation4.finalize_party_creation_atomic(runtime=rt)
        self.assertEqual(finalized['status'],'COMMIT')
        self.assertEqual(len(finalized['roster_sha256']),64)
        for n in range(1,player_count+1):
            gate=creation4.play_gate(runtime=rt,player_id=f'P{n}',character_id=f'C{n}')
            self.assertEqual(gate['status'],'READY')
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH')
        rt.close()
    return test


for _offset in range(80):
    _number=21+_offset
    setattr(InvestigatorCreationBatch4Tests,f'test_{_number:03d}_party_matrix_{_offset:02d}',_make_matrix_test(_offset))


if __name__ == '__main__':
    unittest.main()
