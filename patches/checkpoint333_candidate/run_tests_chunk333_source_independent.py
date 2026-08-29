import copy, hashlib, hmac, json, shutil, tempfile
from pathlib import Path
from offline.runtime import OfflinePlayableRuntimeV1
from solidstate_runtime import MultiplayerRuntimeContractV2
from solidstate_runtime.strict_replay_multiplayer_v2 import MultiplayerStrictReplayRecertificationV2 as MP
from solidstate_runtime.strict_replay_save_resume_v1 import StrictReplaySaveResumeContinuityV1 as V1
from solidstate_runtime.strict_recovery_journal import StrictRecoveryJournal

ROOT=Path(__file__).resolve().parent
SC=['scenario3','scenario4','scenario5','scenario6','scenario7']
checks=[]; leaks=0

def ck(n,c,d=None):
 checks.append((n,bool(c)))
 if not c: raise AssertionError((n,d))

def players(n): return [{'name':f'I{i}','stats':{'HP':14+i,'SAN':60+i,'MP':8+i,'Luck':40+i},'inventory':[f'item{i}']} for i in range(1,n+1)]

def minimal(rt):
 st,c=rt.db.state(); cmap=(st.get('interface_session') or {}).get('control_map',{})
 hp={p:rt.engine.mechanics.get_value(cid,'HP') for p,cid in cmap.items()}
 views={p:rt.engine.knowledge.player_visible_ids(cid) for p,cid in cmap.items()}
 return (copy.deepcopy(st),c,copy.deepcopy(MP.actor_trace(rt.engine)),hp,views)

def view_check(rt,tag):
 global leaks
 st,_=rt.db.state(); cmap=st['interface_session']['control_map']
 for p,cid in cmap.items():
  ids=rt.engine.knowledge.player_visible_ids(cid)
  bad=[x for x in ids if x.startswith('KK_') or (x.startswith('PK_') and f'_{p}_' not in x)]
  if bad: leaks+=len(bad)
  ck(f'{tag}_{p}_no_leak',not bad,bad)
  pr=MultiplayerRuntimeContractV2.player_projection(rt.engine,p)
  ck(f'{tag}_{p}_projection',pr.get('status')=='READY',pr)

def apply_event(rt,tag,i,cmap,negative=False):
 pids=list(cmap); pid=pids[(i-1)%len(pids)]; cid=cmap[pid]
 if i in (1,5,9):
  ck(f'{tag}_e{i}_pk',rt.engine.knowledge.grant(cid,f'PK_{tag}_{pid}_{i}','PLAYER',f'SRC_{tag}_{i}').get('status')=='COMMIT')
  ck(f'{tag}_e{i}_kk',rt.engine.knowledge.grant(cid,f'KK_{tag}_{pid}_{i}','KEEPER',f'SRC_{tag}_{i}').get('status')=='COMMIT')
  ck(f'{tag}_e{i}_luck',rt.engine.mechanics.apply_delta(cid,'Luck',1).get('status')=='COMMIT')
  view_check(rt,f'{tag}_e{i}')
 if negative and i in (3,7):
  b=minimal(rt); r=MP.append_player_action(rt.engine,pid,'NOT_OWNED',f'BADACT_{i}',50,event_id=f'BADACT_{tag}_{i}'); a=minimal(rt)
  ck(f'{tag}_e{i}_bad_actor',r.get('code')=='ACTOR_CONTROL_MISMATCH',r); ck(f'{tag}_e{i}_bad_actor_no_mut',a==b)
  b=minimal(rt); r=MP.append_player_action(rt.engine,pid,cid,f'BADROLL_{i}',0,event_id=f'BADROLL_{tag}_{i}'); a=minimal(rt)
  ck(f'{tag}_e{i}_bad_roll',r.get('code')=='ROLL_INVALID',r); ck(f'{tag}_e{i}_bad_roll_no_mut',a==b)
  b=minimal(rt); r=rt.engine.mechanics.apply_delta(cid,'HP',-99999,minimum=0); a=minimal(rt)
  ck(f'{tag}_e{i}_bad_mech',r.get('status')=='BLOCKED',r); ck(f'{tag}_e{i}_bad_mech_no_mut',a==b)
 roll=((i*37+len(pids)*11+sum(map(ord,tag)))%100)+1
 r=MP.append_player_action(rt.engine,pid,cid,f'A_{tag}_{i}',roll,event_id=f'E_{tag}_{i}',session_id=f'S_{tag}')
 ck(f'{tag}_e{i}_commit',r.get('status')=='COMMIT',r)

def normalized_tables(rt):
 names=('characters','party','mechanical_values','mechanical_registry','inventory','knowledge_partitions','wounds_state','commits')
 out={}
 for t in names:
  rows=[dict(r) for r in rt.db.conn.execute(f'SELECT * FROM {t}')]
  if t=='commits':
   for r in rows:r.pop('transaction_id',None)
  out[t]=sorted(rows,key=lambda r:json.dumps(r,sort_keys=True,separators=(',',':')))
 return out

def final(rt):
 st,c=rt.db.state(); return {'state':copy.deepcopy(st),'commit':c,'fp':MP.continuity_fingerprint(rt.engine),'tables':normalized_tables(rt),'views':copy.deepcopy(rt.player_views())}

# A. Full 5 scenarios x 1-4 players integrated state/control/knowledge/replay stress.
case=0
for sk in SC:
 for n in (1,2,3,4):
  case+=1; tag=f'CORE{case:02d}_{sk}_{n}P'; rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp())/'live.sqlite')
  o=rt.new_session(sk,players(n),require_sources=False); ck(tag+'_session',o.get('status')=='SESSION_READY',o)
  st,_=rt.db.state(); cmap=st['interface_session']['control_map']; ck(tag+'_party',MultiplayerRuntimeContractV2.validate_party(rt.engine,list(cmap),True).get('status')=='PASS')
  for i in range(1,13): apply_event(rt,tag,i,cmap,negative=True)
  v=MP.verify_engine(rt.engine); ck(tag+'_replay',v.get('status')=='REPLAY_MATCH',v); view_check(rt,tag+'_final')
  rt.close()

# B. Multiple save/resume cuts on all player counts (scenario3), plus cross-scenario 4P cut.
def save_resume_case(sk,n,cuts):
 tag=f'SR_{sk}_{n}P'; td=Path(tempfile.mkdtemp()); base=td/'base.sqlite'; r=OfflinePlayableRuntimeV1(ROOT,base)
 ck(tag+'_session',r.new_session(sk,players(n),False).get('status')=='SESSION_READY'); st,_=r.db.state(); cmap=copy.deepcopy(st['interface_session']['control_map']); r.close()
 cont=td/'cont.sqlite'; shutil.copy2(base,cont); rc=OfflinePlayableRuntimeV1(ROOT,cont)
 for i in range(1,13):apply_event(rc,tag,i,cmap,False)
 ck(tag+'_cont_replay',MP.verify_engine(rc.engine).get('status')=='REPLAY_MATCH'); ref=final(rc); rc.close()
 for cut in cuts:
  rp=td/f'r{cut}.sqlite'; shutil.copy2(base,rp); rr=OfflinePlayableRuntimeV1(ROOT,rp)
  for i in range(1,cut+1):apply_event(rr,tag,i,cmap,False)
  sid=f'{tag}_{cut}'; sv=rr.save(sid); ck(f'{tag}_{cut}_save',sv.get('status')=='SAVED',sv); rs=rr.restore_file(f'{sid}.json',False); ck(f'{tag}_{cut}_restore',rs.get('status')=='RESTORED_STRICT',rs)
  ck(f'{tag}_{cut}_party',MultiplayerRuntimeContractV2.validate_party(rr.engine,list(cmap),True).get('status')=='PASS')
  ck(f'{tag}_{cut}_replay0',MP.verify_engine(rr.engine).get('status')=='REPLAY_MATCH')
  for i in range(cut+1,13):
   apply_event(rr,tag,i,cmap,False)
   if (i-cut)%4==0 or i==12: ck(f'{tag}_{cut}_replay{i}',MP.verify_engine(rr.engine).get('status')=='REPLAY_MATCH')
  got=final(rr); cmp=MP.compare(ref['fp'],got['fp'])
  ck(f'{tag}_{cut}_fp',cmp.get('status')=='REPLAY_MATCH',cmp); ck(f'{tag}_{cut}_state',ref['state']==got['state']); ck(f'{tag}_{cut}_commit',ref['commit']==got['commit']); ck(f'{tag}_{cut}_tables',ref['tables']==got['tables']); ck(f'{tag}_{cut}_views',ref['views']==got['views'])
  rr.close(); (ROOT/'saves'/f'{sid}.json').unlink(missing_ok=True)

for n in (1,2,3,4): save_resume_case('scenario3',n,[1,6,11])
for sk in ('scenario4','scenario5','scenario6','scenario7'): save_resume_case(sk,4,[6])

# C. Tampered save / ownership / knowledge / actor replay battery.
rt=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp())/'tamper.sqlite'); ck('T_session',rt.new_session('scenario3',players(4),False).get('status')=='SESSION_READY'); st,_=rt.db.state(); cmap=st['interface_session']['control_map']
for i in range(1,9):apply_event(rt,'T',i,cmap,False)
ck('T_save',rt.save('ss333_tbase').get('status')=='SAVED'); base=json.loads((ROOT/'saves'/'ss333_tbase.json').read_text())
def reauth(b):
 p=b['payload'];raw=rt.save_manager._canon(p).encode();b['auth']['payload_sha256']=hashlib.sha256(raw).hexdigest();b['auth']['hmac_sha256']=hmac.new(rt._secret,raw,hashlib.sha256).hexdigest()
def reject(name,mut,rea=False):
 b=copy.deepcopy(base);mut(b);reauth(b) if rea else None;fn=f'ss333_{name}.json';(ROOT/'saves'/fn).write_text(json.dumps(b));before=minimal(rt);res=rt.restore_file(fn,False);after=minimal(rt);ck('T_'+name+'_closed',res.get('status')=='FAIL_CLOSED',res);ck('T_'+name+'_unchanged',before==after);(ROOT/'saves'/fn).unlink(missing_ok=True)
reject('bad_hmac',lambda b:b['auth'].__setitem__('hmac_sha256','00'*32))
reject('floor',lambda b:b['payload'].__setitem__('checkpoint_floor',329),True)
reject('control',lambda b:b['payload']['canonical_state']['interface_session']['control_map'].__setitem__('P1',cmap['P2']),True)
def owner(b):
 for r in b['payload']['tables']['characters']:
  if r['character_id']==cmap['P1']:r['owner_id']='P4';break
reject('owner',owner,True)
def know(b):
 for r in b['payload']['tables']['knowledge_partitions']:
  if r['character_id']==cmap['P1'] and r['visibility']=='PLAYER':r['knowledge_id']='FOREIGN';break
reject('knowledge',know,True)
expected=MP.actor_trace(rt.engine); state,_=rt.db.state();tam=copy.deepcopy(state[V1.JOURNAL_KEY]);tam[1]['event']['payload']['player_id']='P3';tam[1]['event']['payload']['character_id']=cmap['P3'];rebuilt=[]
for row in tam:
 a=StrictRecoveryJournal.append(rebuilt,row['event']);ck('T_rehash_append',a.get('status')=='APPENDED',a);rebuilt=a['journal']
def mutate(s):s[V1.JOURNAL_KEY]=rebuilt
rt.engine.transact(mutate,[V1.JOURNAL_KEY]);ck('T_rehash_v1_valid',V1.verify_engine(rt.engine).get('status')=='REPLAY_MATCH');v=MP.verify_engine(rt.engine,expected);ck('T_actor_reattribution_detected',v.get('reason')=='ACTOR_TRACE_MISMATCH',v);rt.close();(ROOT/'saves'/'ss333_tbase.json').unlink(missing_ok=True)

passed=sum(x[1] for x in checks)
report={'checkpoint_candidate':333,'id':'MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2','result':'PARTIAL_PASS_SOURCE_INDEPENDENT','parent':332,'promotion_allowed':False,'source_backed_recertification_executed':False,'reason_not_promoted':'Private source PDFs found in Library but raw materialization returned 403; exact source-backed PASS_REAL gates were not rerun.','core_matrix':'5 scenarios x 1-4 players','core_events_per_case':12,'save_resume_multi_cuts':{'scenario3_1_to_4_players':[1,6,11],'scenario4_to_7_4players':[6]},'keeper_to_player_leaks':leaks,'passed':passed,'total':len(checks)}
Path('/mnt/data/ss333_partial_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
