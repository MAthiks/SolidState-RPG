import json
import tempfile
from copy import deepcopy
from pathlib import Path

from solidstate_runtime.db import SolidStateDB
from solidstate_runtime.engine import SolidStateEngine
from solidstate_runtime.player_interface_v1 import PlayerInterfaceV1, LaunchChainV1
from solidstate_runtime.multiplayer_partition import MultiplayerPartition
from solidstate_runtime.multiplayer_session_loop import MultiplayerSessionLoop
from solidstate_runtime.character_transaction_isolation import CharacterTransactionIsolation
from solidstate_runtime.multiplayer_certification_v2 import MultiplayerRuntimeContractV2
from offline.registry import OfflineScenarioSelectionV1
from offline.source_pack import SourcePackValidatorV1
from offline.runtime import OfflinePlayableRuntimeV1

ROOT=Path(__file__).resolve().parent
checks=[]
def ck(name, ok, details=None):
    checks.append({'name':name,'pass':bool(ok),'details':details})
    if not ok:
        raise AssertionError(f'{name}: {details}')

def new_engine():
    d=Path(tempfile.mkdtemp(prefix='ss330_mp_'))
    return SolidStateEngine(SolidStateDB(d/'runtime.sqlite'))

def setup_engine(n, launch=True):
    e=new_engine(); players=[f'P{i}' for i in range(1,n+1)]; chars=[f'C{i}' for i in range(1,n+1)]
    for i,(p,c) in enumerate(zip(players,chars),1):
        ck(f'{n}p_create_{i}',e.set_character(c,p,{'name':f'Investigator {i}','slot':i,'hp_marker':10+i})['status']=='COMMIT')
        ar=e.attach_character(p,c); ck(f'{n}p_attach_{i}',ar['status']=='COMMIT',ar)
        for k,v in [('HP',10+i),('SAN',60+i),('MP',8+i),('Luck',40+i)]:
            ck(f'{n}p_{k}_{i}',e.mechanics.set_value(c,k,v)['status']=='COMMIT')
        ck(f'{n}p_wound_{i}',e.wounds.initialize(c,10+i,10+i)['status']=='COMMIT')
        ck(f'{n}p_item_{i}',e.registry.register(f'ITEM_{i}','item',c,{'label':f'Owned {i}'},f'SOURCE_{i}')['status']=='COMMIT')
        ck(f'{n}p_kplayer_{i}',e.knowledge.grant(c,f'K_PLAYER_{i}','PLAYER',f'SOURCE_{i}')['status']=='COMMIT')
        ck(f'{n}p_kkeeper_{i}',e.knowledge.grant(c,f'K_KEEPER_{i}','KEEPER',f'SOURCE_{i}')['status']=='COMMIT')
    if launch:
        selection=OfflineScenarioSelectionV1(ROOT,SourcePackValidatorV1(ROOT))
        out=LaunchChainV1(e,selection).prepare_session('scenario3',players)
        ck(f'{n}p_launch_ready',out['status']=='SESSION_READY',out)
    return e,players,chars

def sql_snapshot(e):
    tables=('characters','party','mechanical_values','mechanical_registry','inventory','knowledge_partitions','wounds_state')
    return {t:[dict(r) for r in e.db.conn.execute(f'SELECT * FROM {t} ORDER BY rowid').fetchall()] for t in tables}

def live_pristine(runtime):
    st,c=runtime.db.state()
    return c==0 and st=={'scenario_started':False} and runtime.db.conn.execute('SELECT COUNT(*) n FROM characters').fetchone()['n']==0 and runtime.db.conn.execute('SELECT COUNT(*) n FROM party').fetchone()['n']==0

selection=OfflineScenarioSelectionV1(ROOT,SourcePackValidatorV1(ROOT))
rows=selection.list_scenarios()['scenarios']
ck('five_scenarios_still_pass_real',len(rows)==5 and all(r['status']=='PASS_REAL' and r['selectable'] for r in rows),rows)

for n in (1,2,3,4):
    e,players,chars=setup_engine(n)
    party=MultiplayerRuntimeContractV2.validate_party(e,players,require_interface=True)
    ck(f'{n}p_contract_valid',party['status']=='PASS' and party['player_count']==n,party)
    ck(f'{n}p_exact_unique_bindings',party['bindings']==dict(zip(players,chars)) and len(set(party['bindings'].values()))==n,party)

    built=MultiplayerRuntimeContractV2.build_session_state(e,players,f'CERT330_{n}')
    ck(f'{n}p_build_projection_state',built['status']=='READY',built)
    st=built['session_state']
    ck(f'{n}p_legacy_partition_compatible',MultiplayerPartition.validate_control_map(st['character_states'],st['control_map'])['valid'],st['control_map'])

    ui=PlayerInterfaceV1(e)
    for i,(p,c) in enumerate(zip(players,chars),1):
        proj=MultiplayerRuntimeContractV2.player_projection(e,p); ser=json.dumps(proj,sort_keys=True)
        ck(f'{n}p_proj_{i}_ready',proj['status']=='READY',proj)
        ck(f'{n}p_proj_{i}_own_char',proj['character']['character_id']==c,proj)
        ck(f'{n}p_proj_{i}_own_knowledge',proj['knowledge']==[f'K_PLAYER_{i}'],proj)
        ck(f'{n}p_proj_{i}_no_keeper','K_KEEPER_' not in ser,ser)
        for j in range(1,n+1):
            if j!=i:
                ck(f'{n}p_proj_{i}_no_foreign_k{j}',f'K_PLAYER_{j}' not in ser,ser)
                ck(f'{n}p_proj_{i}_no_foreign_c{j}',f'"character_id": "C{j}"' not in ser,ser)

        panel=ui.status_panel(p,c)
        ck(f'{n}p_ui_{i}_ready',panel['status']=='READY',panel)
        ck(f'{n}p_ui_{i}_stats',panel['PV']==10+i and panel['SAN']==60+i and panel['PM']==8+i and panel['Chance']==40+i,panel)
        ck(f'{n}p_ui_{i}_inventory',panel['inventory']==[{'object_id':f'ITEM_{i}','object_type':'item','quantity':1}],panel['inventory'])
        normal=ui.decision_prompt(p,c,'NORMAL_LIBRE')
        ck(f'{n}p_ui_{i}_normal',normal['status']=='DECISION_READY' and normal['prompt']=='Que fais-tu ?' and normal['menu'] is None,normal)
        opts=[
          {'id':'A','label':'A','visibility':'PLAYER_SAFE','requires_knowledge':[f'K_PLAYER_{i}']},
          {'id':'B','label':'B','visibility':'PLAYER_SAFE','requires_knowledge':[]},
          {'id':'C','label':'C','visibility':'PLAYER_SAFE','requires_knowledge':[]},
        ]
        assisted=ui.decision_prompt(p,c,'FACILE_ASSISTE',opts)
        ck(f'{n}p_ui_{i}_assisted_3_free',assisted['status']=='DECISION_READY' and len(assisted['menu']['choices'])==3 and assisted['menu']['free_action']['id']=='FREE_ACTION',assisted)
        keeper=[dict(x) for x in opts]; keeper[0]={'id':'A','label':'Keeper','visibility':'PLAYER_SAFE','requires_knowledge':[f'K_KEEPER_{i}']}
        ck(f'{n}p_ui_{i}_keeper_choice_blocked',ui.decision_prompt(p,c,'FACILE_ASSISTE',keeper)['code']=='CHOICE_KNOWLEDGE_NOT_VISIBLE')
        if n>=2:
            foreign=chars[1] if i==1 else chars[0]
            ck(f'{n}p_ui_{i}_foreign_char_blocked',ui.status_panel(p,foreign)['code']=='CHARACTER_NOT_CONTROLLED_BY_PLAYER')
            fk='K_PLAYER_2' if i!=2 else 'K_PLAYER_1'
            bad=[dict(x) for x in opts]; bad[0]={'id':'A','label':'Foreign','visibility':'PLAYER_SAFE','requires_knowledge':[fk]}
            ck(f'{n}p_ui_{i}_foreign_knowledge_blocked',ui.decision_prompt(p,c,'FACILE_ASSISTE',bad)['code']=='CHOICE_KNOWLEDGE_NOT_VISIBLE')

    before={c:{k:e.mechanics.get_value(c,k) for k in ('HP','SAN','MP','Luck')} for c in chars}
    for idx,c in enumerate(chars):
        old={x:e.mechanics.get_value(x,'HP') for x in chars}
        r=e.mechanics.apply_delta(c,'HP',-1,minimum=0)
        new={x:e.mechanics.get_value(x,'HP') for x in chars}
        ck(f'{n}p_hp_target_{idx+1}_commit',r['status']=='COMMIT',r)
        ck(f'{n}p_hp_target_{idx+1}_isolated',new[c]==old[c]-1 and all(new[x]==old[x] for x in chars if x!=c),{'old':old,'new':new})

    for idx,c in enumerate(chars):
        state0,commit0=e.db.state(); sql0=sql_snapshot(e)
        r=e.mechanics.apply_delta(c,'HP',-9999,minimum=0)
        state1,commit1=e.db.state(); sql1=sql_snapshot(e)
        ck(f'{n}p_failed_mech_{idx+1}_blocked',r['status']=='BLOCKED',r)
        ck(f'{n}p_failed_mech_{idx+1}_no_commit',commit1==commit0,(commit0,commit1))
        ck(f'{n}p_failed_mech_{idx+1}_no_cross_corruption',state1==state0 and sql1==sql0)

    pure=deepcopy(st['character_states']); target=chars[0]
    failed=CharacterTransactionIsolation.apply(pure,target,lambda c:{'committed':False,'reason':'PLAYER_FAILURE','character_state':{**c,'hp_marker':0}})
    ck(f'{n}p_character_tx_failure_all_unchanged',failed['status']=='ROLLBACK' and failed['character_states']==pure,failed)
    succeeded=CharacterTransactionIsolation.apply(pure,target,lambda c:{'committed':True,'character_state':{**c,'hp_marker':777}})
    ck(f'{n}p_character_tx_success_target_only',succeeded['status']=='COMMIT' and succeeded['character_states'][0]['hp_marker']==777 and succeeded['character_states'][1:]==pure[1:],succeeded)

    s0,c0=e.db.state(); q0=sql_snapshot(e)
    def explode(state):
        state.setdefault('characters',{}).setdefault(chars[0],{})['corrupt_attempt']=True
        raise RuntimeError('EXPECTED_PLAYER_FAILURE')
    tx=e.transact(explode,[f'characters.{chars[0]}.corrupt_attempt'])
    s1,c1=e.db.state(); q1=sql_snapshot(e)
    ck(f'{n}p_engine_tx_exception_rolls_back',tx['status']=='ROLLBACK_TRANSACTION' and c1==c0 and s1==s0 and q1==q0,tx)

    for i,(p,c) in enumerate(zip(players,chars),1):
        other='P_X' if n==1 else players[1] if p==players[0] else players[0]
        s0,c0=e.db.state(); q0=sql_snapshot(e)
        r=e.set_character(c,other,{'name':'HIJACK'})
        s1,c1=e.db.state(); q1=sql_snapshot(e)
        ck(f'{n}p_owner_hijack_{i}_blocked',r['status']=='ROLLBACK_TRANSACTION' and r.get('code')=='CHARACTER_OWNER_IMMUTABLE',r)
        ck(f'{n}p_owner_hijack_{i}_no_mutation',c1==c0 and s1==s0 and q1==q0)

    if n>=2:
        loop=MultiplayerSessionLoop(None,None)
        for i,p in enumerate(players):
            for j,c in enumerate(chars):
                if i==j: continue
                v=loop.act(st,p,c,'ANY_ACTION')
                ck(f'{n}p_cross_loop_{i+1}_{j+1}',v['status']=='ROLLBACK' and v['reason']=='CONTROL_VIOLATION',v)
                s0,c0=e.db.state(); q0=sql_snapshot(e)
                a=e.attach_character(p,c); s1,c1=e.db.state(); q1=sql_snapshot(e)
                ck(f'{n}p_cross_attach_{i+1}_{j+1}',a['status']=='ROLLBACK_TRANSACTION' and a.get('code')=='CHARACTER_OWNER_MISMATCH',a)
                ck(f'{n}p_cross_attach_{i+1}_{j+1}_no_mutation',c1==c0 and s1==s0 and q1==q0)

        extra='C_EXTRA'; p0=players[0]
        ck(f'{n}p_extra_owned_create',e.set_character(extra,p0,{'name':'Extra'})['status']=='COMMIT')
        s0,c0=e.db.state(); party0=[dict(r) for r in e.db.conn.execute('SELECT * FROM party ORDER BY player_id')]
        a=e.attach_character(p0,extra); s1,c1=e.db.state(); party1=[dict(r) for r in e.db.conn.execute('SELECT * FROM party ORDER BY player_id')]
        ck(f'{n}p_silent_rebind_blocked',a['status']=='ROLLBACK_TRANSACTION' and a.get('code')=='PLAYER_ALREADY_CONTROLS_CHARACTER',a)
        ck(f'{n}p_silent_rebind_no_party_mutation',c1==c0 and s1==s0 and party1==party0)

e=new_engine()
for name,ids,code in [
 ('zero_players',[],'PLAYER_COUNT_OUT_OF_RANGE'),('five_players',['P1','P2','P3','P4','P5'],'PLAYER_COUNT_OUT_OF_RANGE'),
 ('duplicate_players',['P1','P1'],'DUPLICATE_PLAYER_ID'),('empty_player',['P1',''],'PLAYER_ID_INVALID')]:
    ck(name,MultiplayerRuntimeContractV2.validate_player_ids(ids)['code']==code)
ck('tuple_players_blocked',MultiplayerRuntimeContractV2.validate_player_ids(('P1',))['code']=='PLAYER_IDS_LIST_REQUIRED')

e,players,chars=setup_engine(2)
ui=PlayerInterfaceV1(e)
e.db.conn.execute('UPDATE characters SET owner_id=? WHERE character_id=?',('P2','C1')); e.db.conn.commit()
ck('tamper_owner_contract_blocked',MultiplayerRuntimeContractV2.validate_party(e,players,True)['status']=='BLOCKED')
ck('tamper_owner_interface_blocked',ui.status_panel('P1','C1')['status']=='BLOCKED')

e,players,chars=setup_engine(2)
e.db.conn.execute('UPDATE party SET character_id=? WHERE player_id=?',('C2','P1')); e.db.conn.commit()
ck('tamper_sql_party_contract_blocked',MultiplayerRuntimeContractV2.validate_party(e,players,True)['status']=='BLOCKED')
ck('tamper_sql_party_interface_blocked',PlayerInterfaceV1(e).status_panel('P1','C2')['status']=='BLOCKED')

e,players,chars=setup_engine(2)
state,commit=e.db.state(); state['interface_session']['control_map']['P1']='C2'; e.db.set_state(state,commit); e.db.conn.commit()
ck('tamper_interface_control_map_blocked',MultiplayerRuntimeContractV2.validate_party(e,players,True)['code']=='INTERFACE_CONTROL_MAP_MISMATCH')

valid=lambda n:[{'name':f'Player {i}','stats':{'HP':10+i,'SAN':50+i,'MP':8+i,'Luck':40+i},'inventory':[f'Item {i}']} for i in range(1,n+1)]
for n in (1,2,3,4):
    rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp(prefix='ss330_off_'))/'slot.sqlite')
    out=rt.new_session('scenario3',valid(n),require_sources=False)
    ck(f'offline_{n}p_success',out['status']=='SESSION_READY' and len(out['players'])==n,out)
    ck(f'offline_{n}p_control_exact',list(out['session']['control_map'])==[f'P{i}' for i in range(1,n+1)],out['session'])
    rt.close()

for bad_pos in (1,2,3,4):
    rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp(prefix='ss330_off_bad_'))/'slot.sqlite')
    pp=valid(4); pp[bad_pos-1]['stats']['HP']='BAD'
    out=rt.new_session('scenario3',pp,require_sources=False)
    ck(f'offline_bad_player_{bad_pos}_blocked',out['status']=='BLOCKED' and out['code']=='USER_PROVIDED_STATS_REQUIRED',out)
    ck(f'offline_bad_player_{bad_pos}_live_slot_pristine',live_pristine(rt),rt.db.state())
    rt.close()

rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp(prefix='ss330_off_inject_'))/'slot.sqlite')
orig=SolidStateEngine.attach_character
def injected(self,pid,cid):
    if pid=='P2':
        st,cm=self.db.state(); return {'status':'ROLLBACK_TRANSACTION','code':'INJECTED_P2_FAILURE','previous_commit':cm,'new_commit':cm,'changed_paths':[]}
    return orig(self,pid,cid)
SolidStateEngine.attach_character=injected
try:
    out=rt.new_session('scenario3',valid(3),require_sources=False)
finally:
    SolidStateEngine.attach_character=orig
ck('offline_midbuild_p2_failure_reported',out['status']=='ROLLBACK' and out['code']=='CHARACTER_ATTACH_FAILED',out)
ck('offline_midbuild_p2_failure_live_slot_pristine',live_pristine(rt),rt.db.state())
rt.close()

rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp(prefix='ss330_self_'))/'slot.sqlite')
selftest=rt.self_test(); ck('checkpoint329_offline_selftest_regression',selftest['status']=='PASS',selftest); rt.close()

print(json.dumps({
  'checkpoint_candidate':330,
  'id':'MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2',
  'result':'PASS','passed':len(checks),'total':len(checks),
  'player_counts_certified':[1,2,3,4],
  'scope':'MULTIPLAYER_ONLY_SAVE_RESUME_AND_STRICT_REPLAY_RECERTIFICATION_DEFERRED',
  'checks':checks,
},ensure_ascii=False,indent=2))
