import json
import tempfile
from pathlib import Path

from solidstate_runtime import (
    SolidStateDB, SolidStateEngine, MultiplayerPartition,
    CharacterTransactionIsolation, MultiplayerSessionLoop,
    MultiplayerRuntimeContractV1, ScenarioSelectionInterfaceV1,
    PlayerInterfaceV1, LaunchChainV1,
)

checks=[]
def ck(name, ok, details=None):
    checks.append({"name":name,"pass":bool(ok),"details":details})
    if not ok:
        raise AssertionError(f"{name}: {details}")

def new_engine():
    root=Path(tempfile.mkdtemp(prefix='ss326_'))
    db=SolidStateDB(root/'runtime.db')
    return SolidStateEngine(db)

rows=ScenarioSelectionInterfaceV1('scenario_candidates').list_scenarios()['scenarios']
ck('all_five_scenarios_remain_pass_real', all(r['status']=='PASS_REAL' and r['selectable'] for r in rows), rows)

for n in (1,2,3,4):
    e=new_engine()
    players=[f'P{i}' for i in range(1,n+1)]
    chars=[f'C{i}' for i in range(1,n+1)]

    for i,(p,c) in enumerate(zip(players,chars), start=1):
        r=e.set_character(c,p,{"name":f"Investigator {i}","slot":i,"hp":10+i})
        ck(f'{n}p_create_{i}', r['status']=='COMMIT', r)
        r=e.attach_character(p,c)
        ck(f'{n}p_attach_owned_{i}', r['status']=='COMMIT', r)
        ck(f'{n}p_hp_init_{i}', e.mechanics.set_value(c,'HP',10+i)['status']=='COMMIT')
        ck(f'{n}p_san_init_{i}', e.mechanics.set_value(c,'SAN',60+i)['status']=='COMMIT')
        ck(f'{n}p_pm_init_{i}', e.mechanics.set_value(c,'MP',8+i)['status']=='COMMIT')
        ck(f'{n}p_luck_init_{i}', e.mechanics.set_value(c,'Luck',40+i)['status']=='COMMIT')
        ck(f'{n}p_inventory_init_{i}', e.registry.register(f'ITEM_{i}','item',c,{'label':f'Owned {i}'},f'SOURCE_{i}')['status']=='COMMIT')
        ck(f'{n}p_knowledge_player_{i}', e.knowledge.grant(c,f'K_PLAYER_{i}','PLAYER',f'SOURCE_{i}')['status']=='COMMIT')
        ck(f'{n}p_knowledge_keeper_{i}', e.knowledge.grant(c,f'K_KEEPER_{i}','KEEPER',f'SOURCE_{i}')['status']=='COMMIT')

    party=MultiplayerRuntimeContractV1.validate_party(e,players)
    ck(f'{n}p_party_contract', party['status']=='PASS' and party['player_count']==n, party)
    ck(f'{n}p_exact_one_character_each', all(len(v)==1 for v in party['control_map'].values()), party['control_map'])
    ck(f'{n}p_unique_character_control', len({v[0] for v in party['control_map'].values()})==n, party['control_map'])

    built=MultiplayerRuntimeContractV1.build_session_state(e,players,session_id=f'CERT_{n}')
    ck(f'{n}p_session_build', built['status']=='READY', built)
    st=built['session_state']
    ck(f'{n}p_partition_control_map_valid', MultiplayerPartition.validate_control_map(st['character_states'],st['control_map'])['valid'])

    for i,(p,c) in enumerate(zip(players,chars), start=1):
        projection=MultiplayerRuntimeContractV1.player_projection(e,p)
        ser=json.dumps(projection,sort_keys=True)
        ck(f'{n}p_projection_ready_{i}', projection['status']=='READY')
        ck(f'{n}p_projection_own_character_{i}', projection['character']['character_id']==c, projection)
        ck(f'{n}p_projection_own_player_knowledge_{i}', projection['knowledge']==[f'K_PLAYER_{i}'], projection['knowledge'])
        ck(f'{n}p_projection_no_keeper_knowledge_{i}', 'K_KEEPER_' not in ser, ser)
        for j in range(1,n+1):
            if j!=i:
                ck(f'{n}p_projection_no_foreign_knowledge_{i}_{j}', f'K_PLAYER_{j}' not in ser, ser)
                ck(f'{n}p_projection_no_foreign_character_{i}_{j}', f'"character_id": "C{j}"' not in ser, ser)

        view=MultiplayerPartition.player_view(st,p)
        view_ser=json.dumps(view,sort_keys=True)
        ck(f'{n}p_pure_partition_character_{i}', [x['character_id'] for x in view['character_states']]==[c], view)
        ck(f'{n}p_pure_partition_knowledge_{i}', view['knowledge']['refs']==[f'K_PLAYER_{i}'], view)
        ck(f'{n}p_pure_partition_no_foreign_{i}', all((j==i or f'K_PLAYER_{j}' not in view_ser) for j in range(1,n+1)), view_ser)

    ui=PlayerInterfaceV1(e)
    for i,(p,c) in enumerate(zip(players,chars), start=1):
        panel=ui.status_panel(p,c)
        ck(f'{n}p_ui_panel_ready_{i}', panel['status']=='READY', panel)
        ck(f'{n}p_ui_panel_values_{i}', panel['PV']==10+i and panel['SAN']==60+i and panel['PM']==8+i and panel['Chance']==40+i, panel)
        ck(f'{n}p_ui_inventory_owned_only_{i}', panel['inventory']==[{'object_id':f'ITEM_{i}','object_type':'item','quantity':1}], panel['inventory'])
        if n>=2:
            foreign=chars[1] if i==1 else chars[0]
            ck(f'{n}p_ui_cross_character_blocked_{i}', ui.status_panel(p,foreign)['code']=='CHARACTER_NOT_CONTROLLED_BY_PLAYER')
        normal=ui.decision_prompt(p,c,'NORMAL_LIBRE')
        ck(f'{n}p_ui_normal_open_prompt_{i}', normal['status']=='DECISION_READY' and normal['code']=='OPEN_PROMPT_ONLY' and normal['menu'] is None and normal['prompt']=='Que fais-tu ?', normal)
        options=[
            {'id':'A','label':'Option A','visibility':'PLAYER_SAFE','requires_knowledge':[f'K_PLAYER_{i}']},
            {'id':'B','label':'Option B','visibility':'PLAYER_SAFE','requires_knowledge':[]},
            {'id':'C','label':'Option C','visibility':'PLAYER_SAFE','requires_knowledge':[]},
        ]
        assisted=ui.decision_prompt(p,c,'FACILE_ASSISTE',options)
        ck(f'{n}p_ui_assisted_3_plus_free_{i}', assisted['status']=='DECISION_READY' and assisted['code']=='ASSISTED_THREE_PLUS_FREE' and len(assisted['menu']['choices'])==3 and assisted['menu']['free_action']['id']=='FREE_ACTION', assisted)
        if n>=2:
            bad=[dict(x) for x in options]
            bad[0]={'id':'A','label':'Foreign knowledge','visibility':'PLAYER_SAFE','requires_knowledge':['K_PLAYER_2' if i!=2 else 'K_PLAYER_1']}
            ck(f'{n}p_ui_foreign_knowledge_choice_blocked_{i}', ui.decision_prompt(p,c,'FACILE_ASSISTE',bad)['code']=='CHOICE_KNOWLEDGE_NOT_VISIBLE')

    launch=LaunchChainV1(e,ScenarioSelectionInterfaceV1('scenario_candidates'))
    launched=launch.prepare_session('scenario3',players)
    ck(f'{n}p_launch_chain_ready', launched['status']=='SESSION_READY' and launched['session']['phase']=='SESSION_READY', launched)
    ck(f'{n}p_launch_control_map_exact', launched['session']['control_map']=={p:c for p,c in zip(players,chars)}, launched['session'])

    before={c:e.mechanics.get_value(c,'HP') for c in chars}
    target=chars[0]
    r=e.mechanics.apply_delta(target,'HP',-2,minimum=0)
    ck(f'{n}p_target_hp_commit', r['status']=='COMMIT', r)
    after={c:e.mechanics.get_value(c,'HP') for c in chars}
    ck(f'{n}p_target_hp_changed_only', after[target]==before[target]-2 and all(after[c]==before[c] for c in chars[1:]), {'before':before,'after':after})

    char_states=st['character_states']
    failed=CharacterTransactionIsolation.apply(char_states,target,lambda c:{'committed':False,'reason':'CERT_FAILURE','character_state':{**c,'hp':0}})
    ck(f'{n}p_character_tx_failure_rolls_back', failed['status']=='ROLLBACK' and failed['character_states']==char_states, failed)
    succeeded=CharacterTransactionIsolation.apply(char_states,target,lambda c:{'committed':True,'character_state':{**c,'hp':77}})
    ck(f'{n}p_character_tx_success_target_only', succeeded['status']=='COMMIT' and succeeded['character_states'][0]['hp']==77 and succeeded['character_states'][1:]==char_states[1:], succeeded)

    ck(f'{n}p_unknown_player_blocked', MultiplayerRuntimeContractV1.player_projection(e,'P_UNKNOWN')['status']=='BLOCKED')

    if n>=2:
        loop=MultiplayerSessionLoop(None,None)
        violation=loop.act(st,players[0],chars[1],'ANY_ACTION')
        ck(f'{n}p_cross_control_rolls_back', violation['status']=='ROLLBACK' and violation['reason']=='CONTROL_VIOLATION', violation)

        state_before,commit_before=e.db.state()
        sql_before=[tuple(r) for r in e.db.conn.execute('SELECT player_id,character_id FROM party ORDER BY player_id')]
        wrong=e.attach_character(players[0],chars[1])
        state_after,commit_after=e.db.state()
        sql_after=[tuple(r) for r in e.db.conn.execute('SELECT player_id,character_id FROM party ORDER BY player_id')]
        ck(f'{n}p_wrong_owner_attach_blocked', wrong['status']=='ROLLBACK_TRANSACTION' and wrong.get('code')=='CHARACTER_OWNER_MISMATCH', wrong)
        ck(f'{n}p_wrong_owner_no_commit_advance', commit_after==commit_before, {'before':commit_before,'after':commit_after})
        ck(f'{n}p_wrong_owner_no_state_change', state_after==state_before and sql_after==sql_before, {'sql_before':sql_before,'sql_after':sql_after})

e=new_engine()
ck('zero_players_blocked', MultiplayerRuntimeContractV1.validate_player_ids([])['code']=='PLAYER_COUNT_OUT_OF_RANGE')
ck('five_players_blocked', MultiplayerRuntimeContractV1.validate_player_ids(['P1','P2','P3','P4','P5'])['code']=='PLAYER_COUNT_OUT_OF_RANGE')
ck('duplicate_player_ids_blocked', MultiplayerRuntimeContractV1.validate_player_ids(['P1','P1'])['code']=='DUPLICATE_PLAYER_ID')
ck('non_list_player_ids_blocked', MultiplayerRuntimeContractV1.validate_player_ids(('P1',))['code']=='PLAYER_IDS_LIST_REQUIRED')

chars=[{'character_id':'C1'},{'character_id':'C2'}]
ck('duplicate_character_control_map_rejected', not MultiplayerPartition.validate_control_map(chars,{'P1':['C1'],'P2':['C1']})['valid'])

print(json.dumps({
    'checkpoint':326,
    'result':'PASS',
    'passed':len(checks),
    'total':len(checks),
    'player_counts_certified':[1,2,3,4],
    'checks':checks,
},ensure_ascii=False,indent=2))
