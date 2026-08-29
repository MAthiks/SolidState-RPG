import copy, hashlib, json, os, shutil, tempfile
from pathlib import Path
ROOT=Path(os.environ.get('OFFLINE_PACKAGE_ROOT','/mnt/data/ss332_runtime/SolidState_Offline_Runtime_Checkpoint329')).resolve()
import sys;sys.path.insert(0,str(ROOT))
from offline.runtime import OfflinePlayableRuntimeV1
from solidstate_runtime.strict_replay_multiplayer_v2 import MultiplayerStrictReplayRecertificationV2 as MP
from solidstate_runtime.strict_replay_save_resume_v1 import StrictReplaySaveResumeContinuityV1 as V1
from solidstate_runtime.strict_recovery_journal import StrictRecoveryJournal
SC=['scenario3','scenario4','scenario5','scenario6','scenario7']; checks=[]
def ck(n,c,d=None):checks.append((n,bool(c))); assert c,(n,d)
def players(n):return [{'name':f'I{i}','stats':{'HP':12+i,'SAN':60+i,'MP':8+i,'Luck':40+i},'inventory':[f'item{i}']} for i in range(1,n+1)]
src={'ae.pdf':Path(os.environ.get('AE_SOURCE_PDF',"/mnt/data/L'Appel de Cthulhu 7 - Aventures Effroyables.pdf")),'bg.pdf':Path(os.environ.get('BRUME_KEEPER_PDF','/mnt/data/Les_Registres_de_Brume_v1.1_Gardien_SPOILERS_Natif.pdf')),'bj.pdf':Path(os.environ.get('BRUME_PLAYER_PDF','/mnt/data/Les_Registres_de_Brume_v1.1_Joueur_Protege_Natif.pdf')),'antre.pdf':Path(os.environ.get('ANTRE_SOURCE_PDF','/mnt/data/antre.pdf'))}
sd=ROOT/'sources'
for p in sd.iterdir():
 if p.is_file() or p.is_symlink():p.unlink()
for n,p in src.items():os.symlink(p,sd/n)
case=0
try:
 for sk in SC:
  for n in (1,2,3,4):
   case+=1; td=Path(tempfile.mkdtemp(prefix='cp332_')); base=td/'base.sqlite'; r=OfflinePlayableRuntimeV1(ROOT,base); o=r.new_session(sk,players(n),True); ck(f'c{case}_setup',o.get('status')=='SESSION_READY',o); r.close()
   cont=td/'cont.sqlite'; resume=td/'resume.sqlite'; shutil.copy2(base,cont); shutil.copy2(base,resume)
   rc=OfflinePlayableRuntimeV1(ROOT,cont); rr=OfflinePlayableRuntimeV1(ROOT,resume)
   st,_=rc.db.state(); cmap=st['interface_session']['control_map']; ids=list(cmap)
   tape=[]
   for i in range(8):
    pid=ids[i % n]; cid=cmap[pid]; tape.append((pid,cid,f'ACTION_{case}_{i+1}',((case*17+i*13)%100)+1,f'E{case:02d}_{i+1:02d}'))
   for pid,cid,a,roll,eid in tape:
    x=MP.append_player_action(rc.engine,pid,cid,a,roll,event_id=eid,session_id=f'S{case}'); ck(f'c{case}_continuous_{eid}',x.get('status')=='COMMIT',x)
   for pid,cid,a,roll,eid in tape[:4]:
    x=MP.append_player_action(rr.engine,pid,cid,a,roll,event_id=eid,session_id=f'S{case}'); ck(f'c{case}_pre_save_{eid}',x.get('status')=='COMMIT',x)
   sv=rr.save(f'cp332_{case}');ck(f'c{case}_save',sv.get('status')=='SAVED',sv);rs=rr.restore_file(f'cp332_{case}.json',True);ck(f'c{case}_restore',rs.get('status')=='RESTORED_STRICT',rs)
   for pid,cid,a,roll,eid in tape[4:]:
    x=MP.append_player_action(rr.engine,pid,cid,a,roll,event_id=eid,session_id=f'S{case}'); ck(f'c{case}_post_save_{eid}',x.get('status')=='COMMIT',x)
   vc=MP.verify_engine(rc.engine);vr=MP.verify_engine(rr.engine);ck(f'c{case}_verify_cont',vc.get('status')=='REPLAY_MATCH',vc);ck(f'c{case}_verify_resume',vr.get('status')=='REPLAY_MATCH',vr)
   fc=MP.continuity_fingerprint(rc.engine);fr=MP.continuity_fingerprint(rr.engine);cmp=MP.compare(fc,fr);ck(f'c{case}_fingerprint_equal',cmp['status']=='REPLAY_MATCH',cmp);ck(f'c{case}_actor_trace_equal',fc['actor_trace']==fr['actor_trace']);ck(f'c{case}_rolls_equal',fc['rolls']==fr['rolls']==[t[3] for t in tape]);ck(f'c{case}_actions_equal',fc['actions']==fr['actions']==[t[2] for t in tape]);ck(f'c{case}_hash_chain_equal',fc['journal_hashes']==fr['journal_hashes'])
   if n>1:
    before=rr.db.state(); bad=MP.append_player_action(rr.engine,ids[0],cmap[ids[1]],'WRONG_ACTOR',50,event_id=f'BAD{case}'); after=rr.db.state();ck(f'c{case}_wrong_actor_blocked',bad.get('code')=='ACTOR_CONTROL_MISMATCH',bad);ck(f'c{case}_wrong_actor_no_commit',before==after)
   rc.close();rr.close();(ROOT/'saves'/f'cp332_{case}.json').unlink(missing_ok=True)
 td=Path(tempfile.mkdtemp());rt=OfflinePlayableRuntimeV1(ROOT,td/'neg.sqlite');rt.new_session('scenario3',players(4),True);st,_=rt.db.state();cmap=st['interface_session']['control_map']
 for i in range(4):
  pid=f'P{i+1}';MP.append_player_action(rt.engine,pid,cmap[pid],f'N{i+1}',10+i,event_id=f'N{i+1}')
 expected=MP.actor_trace(rt.engine); state,commit=rt.db.state(); journal=copy.deepcopy(state[V1.JOURNAL_KEY])
 tam=copy.deepcopy(journal); tam[1]['event']['payload']['player_id']='P3';tam[1]['event']['payload']['character_id']=cmap['P3']; rebuilt=[]
 for row in tam:
  a=StrictRecoveryJournal.append(rebuilt,row['event']); assert a['status']=='APPENDED';rebuilt=a['journal']
 def mutate(s):s[V1.JOURNAL_KEY]=rebuilt
 rt.engine.transact(mutate,[V1.JOURNAL_KEY]);ck('neg_reauth_hash_chain_valid',V1.verify_engine(rt.engine).get('status')=='REPLAY_MATCH');v=MP.verify_engine(rt.engine,expected);ck('neg_reattributed_actor_detected',v.get('reason')=='ACTOR_TRACE_MISMATCH',v)
 orig=journal
 dup=copy.deepcopy(orig); dup.insert(2,copy.deepcopy(orig[1])); ck('neg_duplicate_event_rejected',not StrictRecoveryJournal.verify(dup).get('valid'))
 omit=copy.deepcopy(orig); omit.pop(1); ck('neg_omitted_event_rejected',not StrictRecoveryJournal.verify(omit).get('valid'))
 reorder=copy.deepcopy(orig); reorder[1],reorder[2]=reorder[2],reorder[1]; ck('neg_reordered_event_rejected',not StrictRecoveryJournal.verify(reorder).get('valid'))
 for label,bad_journal in [('duplicate',dup),('omit',omit),('reorder',reorder)]:
  rebuilt2=[]; blocked=False
  for row in bad_journal:
   a=StrictRecoveryJournal.append(rebuilt2,row['event'])
   if a.get('status')!='APPENDED': blocked=True; break
   rebuilt2=a['journal']
  ck(f'neg_{label}_rehash_blocked',blocked)
 rt.close()
finally:
 for p in sd.iterdir():
  if p.is_symlink() or p.is_file():p.unlink()
print(json.dumps({'checkpoint':332,'result':'PASS','passed':len(checks),'total':len(checks),'cases':case},indent=2))
