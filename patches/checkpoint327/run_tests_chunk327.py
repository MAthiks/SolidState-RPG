import tempfile, json, copy
from pathlib import Path
from solidstate_runtime.db import SolidStateDB
from solidstate_runtime.engine import SolidStateEngine
from solidstate_runtime.interface_v1 import ScenarioSelectionInterfaceV1
from solidstate_runtime.player_interface_v1 import PlayerInterfaceV1, LaunchChainV1
from solidstate_runtime.save_resume_v1 import SaveResumeSelectedScenarioAndFullInterfaceV1
ROOT=Path(__file__).resolve().parent; SECRET=b'checkpoint327-save-secret-32-bytes-minimum!!'
def make_engine():
 p=Path(tempfile.mktemp(suffix='.db')); db=SolidStateDB(p); return p,db,SolidStateEngine(db)
def setup(n):
 p,db,e=make_engine(); sel=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates')
 for i in range(1,n+1):
  pid=f'P{i}'; cid=f'C{i}'; e.set_character(cid,pid,{'name':cid}); e.attach_character(pid,cid)
  e.wounds.initialize(cid,10+i,9+i); e.mechanics.set_value(cid,'SAN',60+i); e.mechanics.set_value(cid,'MP',10+i); e.mechanics.set_value(cid,'Luck',40+i)
  e.registry.register(f'ITEM{i}','item',cid,{'label':f'item{i}'},'TEST_FIXTURE')
  e.knowledge.grant(cid,f'K_PLAYER_{i}','PLAYER','TEST'); e.knowledge.grant(cid,f'K_KEEPER_{i}','KEEPER','TEST')
 r=LaunchChainV1(e,sel).prepare_session('scenario3',[f'P{i}' for i in range(1,n+1)])
 assert r['status']=='SESSION_READY'
 return p,db,e,sel
checks=[]
def ck(name,v): checks.append((name,bool(v)))
for n in (1,2,3,4):
 p,db,e,sel=setup(n); ui=PlayerInterfaceV1(e)
 before={f'P{i}':ui.status_panel(f'P{i}',f'C{i}') for i in range(1,n+1)}
 mgr=SaveResumeSelectedScenarioAndFullInterfaceV1(e,sel,SECRET); sv=mgr.save(f'S{n}'); ck(f'{n}:save',sv['status']=='SAVED')
 bundle=sv['bundle']; saved_commit=bundle['payload']['commit_sequence']; db.close()
 p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); mgr2=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET)
 rr=mgr2.restore(bundle); ck(f'{n}:restore',rr['status']=='RESTORED' and rr['commit']==saved_commit)
 ui2=PlayerInterfaceV1(e2)
 for i in range(1,n+1):
  pid=f'P{i}'; cid=f'C{i}'; ck(f'{n}:{pid}:panel',ui2.status_panel(pid,cid)==before[pid])
  ck(f'{n}:{pid}:knowledge',e2.knowledge.player_visible_ids(cid)==[f'K_PLAYER_{i}'] and not e2.knowledge.can_expose(cid,f'K_KEEPER_{i}'))
  normal=ui2.decision_prompt(pid,cid,'NORMAL_LIBRE'); ck(f'{n}:{pid}:normal',normal['code']=='OPEN_PROMPT_ONLY' and normal['prompt']=='Que fais-tu ?')
  opts=[{'id':'a','label':'A','visibility':'PLAYER_SAFE'},{'id':'b','label':'B','visibility':'PLAYER_SAFE'},{'id':'c','label':'C','visibility':'PLAYER_SAFE'}]
  assist=ui2.decision_prompt(pid,cid,'FACILE_ASSISTE',opts); ck(f'{n}:{pid}:assist',assist['code']=='ASSISTED_THREE_PLUS_FREE' and len(assist['menu']['choices'])==3 and assist['menu']['free_action']['id']=='FREE_ACTION')
 state,c=e2.db.state(); ck(f'{n}:session',state['interface_session']['scenario_key']=='scenario3' and len(state['interface_session']['control_map'])==n)
 nxt=e2.mechanics.set_value('C1','SAN',55); ck(f'{n}:next_commit',nxt['status']=='COMMIT' and nxt['commit']==saved_commit+1)
 db2.close(); Path(p2).unlink(missing_ok=True); Path(p).unlink(missing_ok=True)
# tamper matrix
p,db,e,sel=setup(4); mgr=SaveResumeSelectedScenarioAndFullInterfaceV1(e,sel,SECRET); base=mgr.save('T')['bundle']; db.close(); Path(p).unlink(missing_ok=True)
for label,mut in [
 ('payload',lambda b:b['payload']['canonical_state']['interface_session'].__setitem__('scenario_key','scenario7')),
 ('control',lambda b:b['payload']['canonical_state']['interface_session']['control_map'].__setitem__('P1','C2')),
 ('stats',lambda b:b['payload']['tables']['mechanical_values'][0].__setitem__('value',999)),
 ('knowledge',lambda b:b['payload']['tables']['knowledge_partitions'][0].__setitem__('visibility','PLAYER')),
 ('auth',lambda b:b['auth'].__setitem__('hmac_sha256','0'*64))]:
 b=copy.deepcopy(base); mut(b); p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); r=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET).restore(b); ck('tamper:'+label,r['status']=='FAIL_CLOSED'); db2.close(); Path(p2).unlink(missing_ok=True)
# wrong secret and dirty target
p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); r=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,b'X'*40).restore(base); ck('wrong_secret',r['status']=='FAIL_CLOSED'); db2.close(); Path(p2).unlink(missing_ok=True)
p2,db2,e2=make_engine(); e2.set_character('X','X',{}); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); r=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET).restore(base); ck('dirty_target',r['status']=='FAIL_CLOSED'); db2.close(); Path(p2).unlink(missing_ok=True)

# authenticated-but-semantically-invalid bundles must also fail closed
p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); mgr2=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET)
b=copy.deepcopy(base); b['payload']['canonical_state']['interface_session']['control_map']['P1']='C2'; b['auth']['payload_sha256']=__import__('hashlib').sha256(mgr2._canon(b['payload']).encode()).hexdigest(); b['auth']['hmac_sha256']=mgr2._mac(b['payload']); r=mgr2.restore(b); ck('semantic:control_map',r['status']=='FAIL_CLOSED' and r['code'] in ('CONTROL_MAP_INVALID','PARTY_CONTROL_MAP_MISMATCH','CONTROL_OWNERSHIP_INVALID')); db2.close(); Path(p2).unlink(missing_ok=True)
p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); mgr2=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET)
b=copy.deepcopy(base); b['payload']['commit_sequence']+=7; b['auth']['payload_sha256']=__import__('hashlib').sha256(mgr2._canon(b['payload']).encode()).hexdigest(); b['auth']['hmac_sha256']=mgr2._mac(b['payload']); r=mgr2.restore(b); ck('semantic:commit_ledger',r['status']=='FAIL_CLOSED' and r['code']=='COMMIT_LEDGER_MISMATCH'); db2.close(); Path(p2).unlink(missing_ok=True)
p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); mgr2=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET)
b=copy.deepcopy(base); b['payload']['canonical_state']['interface_session']['scenario_key']='scenario_missing'; b['auth']['payload_sha256']=__import__('hashlib').sha256(mgr2._canon(b['payload']).encode()).hexdigest(); b['auth']['hmac_sha256']=mgr2._mac(b['payload']); r=mgr2.restore(b); ck('semantic:scenario_cert',r['status']=='FAIL_CLOSED' and r['code']=='SCENARIO_NOT_PASS_REAL'); db2.close(); Path(p2).unlink(missing_ok=True)
# all five PASS_REAL scenario selections survive save/resume
for sk in ('scenario3','scenario4','scenario5','scenario6','scenario7'):
 p,db,e,sel=setup(1); LaunchChainV1(e,sel).prepare_session(sk,['P1']); mgr=SaveResumeSelectedScenarioAndFullInterfaceV1(e,sel,SECRET); b=mgr.save('SCEN')['bundle']; db.close(); Path(p).unlink(missing_ok=True)
 p2,db2,e2=make_engine(); sel2=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates'); r=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,sel2,SECRET).restore(b); ck('scenario:'+sk,r['status']=='RESTORED' and r['session']['scenario_key']==sk and r['session']['certification_status']=='PASS_REAL'); db2.close(); Path(p2).unlink(missing_ok=True)

passed=sum(v for _,v in checks); print(json.dumps({'status':'PASS' if passed==len(checks) else 'FAIL','passed':passed,'total':len(checks),'failed':[n for n,v in checks if not v]},indent=2)); raise SystemExit(0 if passed==len(checks) else 1)
