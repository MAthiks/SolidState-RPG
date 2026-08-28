import copy,json,random
from spec_model import *
checks=[]
def check(name,fn):
    try: fn(); checks.append((name,True,None))
    except Exception as e: checks.append((name,False,repr(e)))
def expect(c,m='expectation failed'):
    if not c: raise AssertionError(m)

def valid_state(n=1):
    s=StartupState(engine_rules_validated=True,scenario_accessible=True,partitions_active=True,initial_save_ready=True,preflight_critical_ok=True)
    s.configure_players(n); return s

def t_no_auto_start(): expect(not StartupState(scenario_accessible=True).can_start_scenario())
def t_new_game_gates():
    s=valid_state(1); expect(s.can_start_scenario())
    gates=['engine_rules_validated','scenario_accessible','party_state_initialized','character_states_initialized','partitions_active','initial_save_ready','preflight_critical_ok']
    for g in gates:
        q=copy.deepcopy(s); setattr(q,g,False); expect(not q.can_start_scenario(),g)
    q=copy.deepcopy(s); q.slots[0].interrupted=True; expect(not q.can_start_scenario())
def t_player_count():
    for n in (1,2,3,4): expect(valid_state(n).can_start_scenario())
    for bad in (0,5,-1):
        try: StartupState().configure_players(bad)
        except ValueError: pass
        else: raise AssertionError('bad player count accepted')
def t_assistance():
    s=valid_state(4); s.set_assistance(2,ASSISTED); expect(s.assistance==[NORMAL,NORMAL,ASSISTED,NORMAL])
    normal=interface_rule(NORMAL); assist=interface_rule(ASSISTED)
    expect(normal['prompt']=='OPEN' and normal['suggestions']==0 and normal['help_control'])
    expect(assist['prompt']=='OPEN' and assist['suggestions']==3 and assist['free_action'] and assist['source']=='PLAYER_KNOWLEDGE_ONLY')
def t_continue_no_save(): expect(continue_status(False)=='NO_SAVE_CLEAN')
def t_diagnostic():
    s=valid_state(1); s.diagnostic_mode=True; expect(not s.can_start_scenario())
def t_validator_negative_battery():
    base=CharacterDraft(); expect(base.status==READY)
    fields=['source_accessible','occupation_resolved','occupation_total_ok','credit_in_range','required_skills_present','personal_total_ok','backstory_ok','finances_ok','equipment_ok']
    for f in fields:
        d=copy.deepcopy(base); setattr(d,f,False); expect(d.status==PENDING,f)
    d=copy.deepcopy(base); d.interrupted=True; expect(d.status==PENDING)
def t_tx_isolation(n):
    s=valid_state(n); before=[x.tx_version for x in s.slots]; s.slots[n//2].tx_version+=1; after=[x.tx_version for x in s.slots]
    expect(sum(a!=b for a,b in zip(before,after))==1)
def t_pending_locks_party():
    s=valid_state(4); s.slots[3].occupation_total_ok=False; expect(not s.can_start_scenario())
    s.slots[3].occupation_total_ok=True; expect(s.can_start_scenario())
def t_knowledge_partition(n):
    s=valid_state(n); s.observe(0,'CLUE_A')
    for i in range(1,n): expect('CLUE_A' not in s.knowledge[i])
    if n>1:
        s.transmit(0,1,'CLUE_A'); expect('CLUE_A' in s.knowledge[1])
        for i in range(2,n): expect('CLUE_A' not in s.knowledge[i])
def t_roll_immutable():
    s=valid_state(1); s.commit_roll('R1',42); rev=s.autosave_revision
    try: s.commit_roll('R1',7)
    except RuntimeError: pass
    else: raise AssertionError('reroll accepted')
    expect(s.committed_rolls['R1']==42 and s.autosave_revision==rev)
def t_fuzz_gate():
    rng=random.Random(7801)
    for _ in range(20000):
        n=rng.choice([1,2,3,4]); s=StartupState(); s.configure_players(n)
        for f in ['engine_rules_validated','scenario_accessible','partitions_active','initial_save_ready','preflight_critical_ok','party_state_initialized','character_states_initialized']:
            setattr(s,f,rng.choice([True,False]))
        s.diagnostic_mode=rng.choice([True,False])
        for slot in s.slots:
            if rng.random()<.25: slot.occupation_total_ok=False
            if rng.random()<.1: slot.interrupted=True
        expected=(s.engine_rules_validated and s.scenario_accessible and all(x.status==READY for x in s.slots)
                  and s.party_state_initialized and s.character_states_initialized and s.partitions_active and s.initial_save_ready
                  and s.preflight_critical_ok and not s.diagnostic_mode)
        expect(s.can_start_scenario()==expected)
def t_fuzz_interface():
    rng=random.Random(7802)
    for _ in range(20000):
        mode=rng.choice([NORMAL,ASSISTED]); r=interface_rule(mode)
        expect(r['prompt']=='OPEN' and r['free_action'] and r['help_control'])
        expect(r['suggestions']==(0 if mode==NORMAL else 3))
        if mode==ASSISTED: expect(r['source']=='PLAYER_KNOWLEDGE_ONLY')

TESTS=[('startup/no_auto_start',t_no_auto_start),('startup/all_required_gates',t_new_game_gates),('startup/player_count_1_4',t_player_count),('startup/per_player_assistance',t_assistance),('startup/continue_no_save_clean',t_continue_no_save),('startup/diagnostic_never_starts',t_diagnostic),('character/negative_validator_battery',t_validator_negative_battery),('multiplayer/2_player_tx_isolation',lambda:t_tx_isolation(2)),('multiplayer/4_player_tx_isolation',lambda:t_tx_isolation(4)),('multiplayer/pending_slot_locks_gate',t_pending_locks_party),('knowledge/2_player_partition',lambda:t_knowledge_partition(2)),('knowledge/4_player_partition',lambda:t_knowledge_partition(4)),('ironman/committed_roll_immutable',t_roll_immutable),('fuzz/startup_gate_20000',t_fuzz_gate),('fuzz/interface_20000',t_fuzz_interface)]
for n,f in TESTS: check(n,f)
out={'schema':'SOLIDSTATE_RC1_SPEC_CERT_V1','target':'Solid State v7.8-RC1','level':'SPECIFICATION_CONFORMANCE_MODEL','important_limit':'This is not an executable-engine certification. It tests a model derived from the versioned migration/directive contracts.','seeded_deterministic':True,'checks':[{'name':n,'status':'PASS' if ok else 'FAIL','error':e} for n,ok,e in checks],'summary':{'passed':sum(ok for _,ok,_ in checks),'failed':sum(not ok for _,ok,_ in checks),'total':len(checks)},'blocked_engine_checks':['canonical archaeologist registry resolution against actual CoC7 Rules Core payload','real Startup Gate execution in engine','real save/load persistence','real documentary retrieval/preflight','real scenario narration non-start','real DiceProvider persistence across process reload']}
print(json.dumps(out,indent=2,ensure_ascii=False))
if out['summary']['failed']: raise SystemExit(1)
