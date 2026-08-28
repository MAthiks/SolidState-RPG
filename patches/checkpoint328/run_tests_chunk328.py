import json, tempfile, shutil, hashlib, hmac
from pathlib import Path
from solidstate_runtime import SolidStateDB, SolidStateEngine
from solidstate_runtime.save_resume_v1 import SaveResumeSelectedScenarioAndFullInterfaceV1
from solidstate_runtime.strict_replay_save_resume_v1 import StrictReplaySaveResumeContinuityV1 as C

SECRET=b'checkpoint328-save-secret-32bytes!!'
SCENARIOS=['scenario3','scenario4','scenario5','scenario6','scenario7']
ACTIONS=[
 ('OBSERVE', {'roll':23,'delta':1}),('SEARCH',{'roll':61,'delta':2}),('TALK',{'roll':44,'delta':1}),
 ('MOVE',{'roll':82,'delta':0}),('EXAMINE',{'roll':17,'delta':3}),('RESOLVE',{'roll':52,'delta':2}),
 ('ESCAPE',{'roll':76,'delta':1}),('END',{'roll':9,'delta':4})]

class Selection:
 def select(self,key):
  if key not in SCENARIOS:return {'status':'BLOCKED'}
  return {'status':'SELECTED','selection':{'certification_status':'PASS_REAL','title':key}}

def mkengine(path): return SolidStateEngine(SolidStateDB(path))

def setup(e,scenario,n):
 players=[f'P{i}' for i in range(1,n+1)]
 cmap={}
 for i,p in enumerate(players,1):
  cid=f'C{i}'
  assert e.set_character(cid,p,{'name':cid})['status']=='COMMIT'
  assert e.attach_character(p,cid)['status']=='COMMIT'
  cmap[p]=cid
 def mut(s):
  s['interface_session']={'interface_version':'PLAYER_INTERFACE_V1','scenario_key':scenario,'scenario_title':scenario,
   'certification_status':'PASS_REAL','players':players,'control_map':cmap,'phase':'SESSION_READY'}
  s[C.STATE_KEY]=C.initial_state();s[C.JOURNAL_KEY]=[]
 assert e.transact(mut,['interface_session',C.STATE_KEY,C.JOURNAL_KEY])['status']=='COMMIT'
 return players,cmap

def play(e,scenario,n,start=0,end=None):
 end=len(ACTIONS) if end is None else end
 sid=f'{scenario}-{n}'
 for i in range(start,end):
  aid,payload=ACTIONS[i]
  r=C.append_action(e,sid,aid,payload,f'{sid}-E{i+1:02d}')
  assert r['status']=='COMMIT',r

def fp(e):
 v=C.verify_engine(e);assert v['status']=='REPLAY_MATCH',v
 return C.continuity_fingerprint(e)

def reauth(bundle):
 p=bundle['payload']; raw=json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 bundle['auth']['payload_sha256']=hashlib.sha256(raw).hexdigest()
 bundle['auth']['hmac_sha256']=hmac.new(SECRET,raw,hashlib.sha256).hexdigest()

passes=0
for scenario in SCENARIOS:
 for n in range(1,5):
  td=Path(tempfile.mkdtemp())
  try:
   e1=mkengine(td/'continuous.db');setup(e1,scenario,n);play(e1,scenario,n);a=fp(e1)
   e2=mkengine(td/'split.db');setup(e2,scenario,n);play(e2,scenario,n,0,4)
   sm=SaveResumeSelectedScenarioAndFullInterfaceV1(e2,Selection(),SECRET)
   sv=sm.save(f'{scenario}-{n}');assert sv['status']=='SAVED'
   saved_commit=sv['bundle']['payload']['commit_sequence']
   e2.db.close()
   e3=mkengine(td/'resumed.db');sm3=SaveResumeSelectedScenarioAndFullInterfaceV1(e3,Selection(),SECRET)
   rr=C.restore_verified(sm3,sv['bundle']);assert rr['status']=='RESTORED_STRICT',rr
   assert rr['commit']==saved_commit
   play(e3,scenario,n,4,None);b=fp(e3)
   cmp=C.compare(a,b);assert cmp['status']=='REPLAY_MATCH',cmp
   assert b['rolls']==[p['roll'] for _,p in ACTIONS]
   assert b['actions']==[x for x,_ in ACTIONS]
   passes += 10
  finally: shutil.rmtree(td,ignore_errors=True)

with tempfile.TemporaryDirectory() as td:
 e=mkengine(Path(td)/'a.db');setup(e,'scenario3',2);play(e,'scenario3',2,0,4)
 sm=SaveResumeSelectedScenarioAndFullInterfaceV1(e,Selection(),SECRET);sv=sm.save('tamper')
 bad=json.loads(json.dumps(sv['bundle']));j=bad['payload']['canonical_state'][C.JOURNAL_KEY];j[0],j[1]=j[1],j[0];reauth(bad)
 fresh=mkengine(Path(td)/'b.db');smf=SaveResumeSelectedScenarioAndFullInterfaceV1(fresh,Selection(),SECRET)
 r=C.restore_verified(smf,bad);assert r['status']=='FAIL_CLOSED' and r['reason']=='STRICT_SAVE_REPLAY_INVALID';passes+=3
 bad2=json.loads(json.dumps(sv['bundle']));bad2['payload']['canonical_state'][C.JOURNAL_KEY].append(bad2['payload']['canonical_state'][C.JOURNAL_KEY][-1]);reauth(bad2)
 fresh2=mkengine(Path(td)/'c.db');r2=C.restore_verified(SaveResumeSelectedScenarioAndFullInterfaceV1(fresh2,Selection(),SECRET),bad2)
 assert r2['status']=='FAIL_CLOSED';passes+=2
 bad3=json.loads(json.dumps(sv['bundle']));bad3['payload']['canonical_state'][C.STATE_KEY]['score']+=99;reauth(bad3)
 fresh3=mkengine(Path(td)/'d.db');r3=C.restore_verified(SaveResumeSelectedScenarioAndFullInterfaceV1(fresh3,Selection(),SECRET),bad3)
 assert r3['status']=='FAIL_CLOSED';passes+=2

print(f'{passes}/{passes} PASS')
