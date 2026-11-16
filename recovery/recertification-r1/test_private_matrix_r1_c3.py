import copy, json, os, tempfile
from pathlib import Path
from integrated_adjudication_r1_c3 import SourceBackedRuntimeR1C3

checks=[]; leaks=0
def ck(name,cond,detail=None):
    checks.append((name,bool(cond)))
    if not cond: raise AssertionError((name,detail))
def players(n): return [{'name':f'I{i}','stats':{'HP':18,'SAN':70,'MP':12,'Luck':50}} for i in range(1,n+1)]
SCENARIOS={
 'MAISON_PENDU':('AE_COLLECTION',),
 'BRUME':('BRUME_KEEPER','BRUME_PLAYER'),
 'ANTRE':('ANTRE_SOURCE',),
 'MUSE':('AE_COLLECTION',),
 'EXPLORATEUR':('AE_COLLECTION',),
 'SOLEIL_NOIR':('SOLEIL_NOIR_KEEPER','SOLEIL_NOIR_PLAYER'),
}

def runtime(db,sid,n,rules,sources):
    r=SourceBackedRuntimeR1C3(db,rules,sources,b'r1-c3-private-matrix')
    out=r.new_session(players(n),sid); ck(f'{sid}_ready',out['status']=='SESSION_READY',out); return r

def apply_event(r,scen,srcs,n,i,tag):
    pid=f'P{((i-1)%n)+1}'; cid=f'C{((i-1)%n)+1}'
    if i%3==1:
        roll=((i*17+n*7)%60)+1
        out=r.adjudicate_skill(player_id=pid,character_id=cid,skill_value=70,scenario_sources=srcs,recorded_roll=roll,replay=True,event_id=f'{tag}-E{i}')
    elif i%3==2:
        out=r.adjudicate_sanity_loss(player_id=pid,character_id=cid,loss=1,sanity_start_of_day=70,daily_loss_before=(i//3),scenario_sources=srcs,san_roll=((i*13)%100)+1,event_id=f'{tag}-E{i}',loss_provenance=f'{scen}:matrix-loss')
    else:
        out=r.adjudicate_damage_after_hit(player_id=pid,character_id=cid,skill_value=80,attack_roll=20,damage=1,scenario_sources=srcs,event_id=f'{tag}-E{i}',damage_provenance=f'{scen}:matrix-damage')
    ck(f'{tag}_e{i}_commit',out.get('status')=='COMMIT',out)

def firewall(r,tag,n):
    global leaks
    for idx in range(1,n+1):
        cid=f'C{idx}'; pid=f'P{idx}'
        ck(f'{tag}_{pid}_pk',r.add_knowledge(cid,f'PK_{tag}_{pid}','PLAYER',{'safe':True}).get('status')=='COMMIT')
        ck(f'{tag}_{pid}_kk',r.add_knowledge(cid,f'KK_{tag}_{pid}','KEEPER',{'secret':True}).get('status')=='COMMIT')
        view=r.player_view(pid); ids={x['knowledge_id'] for x in view['knowledge']}; bad=[x for x in ids if x.startswith('KK_')]
        leaks+=len(bad); ck(f'{tag}_{pid}_no_keeper_leak',not bad,bad)

def core_matrix(rules,sources):
    cases=0
    for scen,srcs in SCENARIOS.items():
        for n in (1,2,3,4):
            cases+=1; tag=f'CORE_{scen}_{n}P'; td=Path(tempfile.mkdtemp()); r=runtime(td/'live.sqlite',tag,n,rules,sources)
            firewall(r,tag,n)
            for i in range(1,13): apply_event(r,scen,srcs,n,i,tag)
            v=r.verify_journal(r.state()); ck(f'{tag}_replay',v['status']=='REPLAY_MATCH',v)
            st=r.state()
            for idx in range(1,n+1):
                c=st['characters'][f'C{idx}']['stats']; ck(f'{tag}_san_nonnegative_{idx}',0<=c['SAN']<=99,c); ck(f'{tag}_hp_nonnegative_{idx}',c['HP']>=0,c)
            r.close()
    return cases

def run_stream(r,scen,srcs,n,tag,start=1,end=12):
    for i in range(start,end+1): apply_event(r,scen,srcs,n,i,tag)

def save_resume_case(scen,srcs,n,cuts,rules,sources):
    tag=f'SR_{scen}_{n}P'; td=Path(tempfile.mkdtemp())
    cont=runtime(td/'cont.sqlite',tag,n,rules,sources); run_stream(cont,scen,srcs,n,tag); ref=cont.state(); ref_fp=cont.continuity_fingerprint(); cont.close()
    for cut in cuts:
        pre=runtime(td/f'pre{cut}.sqlite',tag,n,rules,sources); run_stream(pre,scen,srcs,n,tag,1,cut); bundle=pre.save_bundle(); pre.close()
        rr=runtime(td/f'res{cut}.sqlite',tag,n,rules,sources); rs=rr.restore_bundle(bundle); ck(f'{tag}_{cut}_restore',rs['status']=='RESTORED_STRICT',rs); ck(f'{tag}_{cut}_replay0',rr.verify_journal(rr.state())['status']=='REPLAY_MATCH')
        run_stream(rr,scen,srcs,n,tag,cut+1,12); got=rr.state(); got_fp=rr.continuity_fingerprint()
        ck(f'{tag}_{cut}_state_equal',got==ref); ck(f'{tag}_{cut}_fp_equal',got_fp==ref_fp,(got_fp,ref_fp)); rr.close()

def negatives(rules,sources):
    td=Path(tempfile.mkdtemp()); r=runtime(td/'neg.sqlite','NEG',2,rules,sources); srcs=SCENARIOS['SOLEIL_NOIR']
    before=r.state_digest(); bad=r.adjudicate_sanity_loss(player_id='P1',character_id='C2',loss=1,sanity_start_of_day=70,scenario_sources=srcs,san_roll=50,event_id='N1'); ck('neg_wrong_actor',bad['code']=='ACTOR_CONTROL_MISMATCH',bad); ck('neg_wrong_actor_no_mut',r.state_digest()==before)
    before=r.state_digest(); bad=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='OVER',roll=50,deltas=[{'stat':'SAN','op':'ADD','value':-999}],mechanic='NEG',event_id='N2'); ck('neg_bound',bad['code']=='MECHANICAL_DELTA_BELOW_MINIMUM',bad); ck('neg_bound_no_mut',r.state_digest()==before)
    ok=r.adjudicate_sanity_loss(player_id='P1',character_id='C1',loss=5,sanity_start_of_day=70,scenario_sources=srcs,san_roll=50,event_id='N3'); ck('neg_setup_san_commit',ok['status']=='COMMIT',ok); original=r.state()
    tam=copy.deepcopy(original); row=tam['journal'][-1]; row['event']['payload']['mechanical_deltas'][0]['value']=-6; row['event_hash']=r._event_hash(row['previous_hash'],row['event']); v=r.verify_journal(tam); ck('neg_delta_reattribution_detected',v['status']=='REPLAY_DIVERGENCE',v)
    tam=copy.deepcopy(original); row=tam['journal'][-1]; row['event']['payload']['player_id']='P2'; row['event']['payload']['character_id']='C2'; row['event_hash']=r._event_hash(row['previous_hash'],row['event']); v=r.verify_journal(tam); ck('neg_actor_reattribution_detected',v['status']=='REPLAY_DIVERGENCE',v)
    r.close()

def run():
    rules=Path(os.environ['R1_C1_RULES_ZIP']); sources={k:Path(v) for k,v in json.loads(os.environ['R1_PRIVATE_SOURCE_MAP']).items()}
    cases=core_matrix(rules,sources)
    for n in (1,2,3,4): save_resume_case('MAISON_PENDU',SCENARIOS['MAISON_PENDU'],n,[1,6,11],rules,sources)
    for scen in ('BRUME','ANTRE','MUSE','EXPLORATEUR','SOLEIL_NOIR'): save_resume_case(scen,SCENARIOS[scen],4,[6],rules,sources)
    negatives(rules,sources)
    report={'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_PRIVATE_MATRIX_V1','generation':'RECOVERY_RECERTIFICATION_R1','stage':'R1-C3_COMPLETE_RULES_STATE_DELTA_AND_SCENARIO_RECERTIFICATION','qualification':'PRIVATE_SOURCE_IDENTITY_BACKED_RUNTIME_MATRIX','result':'PASS','authority_promoted':False,'private_source_content_embedded':False,'core_matrix':f'{len(SCENARIOS)} scenario identities x 1-4 players = {cases} cases','events_per_core_case':12,'save_resume_cuts':{'MAISON_PENDU_1_TO_4':[1,6,11],'OTHER_5_4P':[6]},'keeper_to_player_leaks':leaks,'passed':len(checks),'total':len(checks),'scope_limits':['Scenario sources are cryptographically identity-gated; this matrix does not claim full canonical scenario-event interpretation.','Rules Package R1 remains a partial source-grounded mechanical core.','Full occupation/skill/equipment/weapon registries and remaining CoC7 mechanics still require migration before authority promotion.'],'next_gate':'R1-C4_REGISTRY_AND_CANONICAL_SCENARIO_ROUTER_RECERTIFICATION'}
    print(json.dumps(report,indent=2)); return report

if __name__=='__main__': run()
