import json, os, pathlib, shutil, tempfile, sys, subprocess, time, urllib.request
ROOT=pathlib.Path(os.environ['OFFLINE_PACKAGE_ROOT']).resolve()
sys.path.insert(0,str(ROOT))
from offline.runtime import OfflinePlayableRuntimeV1
from solidstate_runtime.strict_replay_save_resume_v1 import StrictReplaySaveResumeContinuityV1
SRC={
 'ae.pdf':pathlib.Path(os.environ['AE_SOURCE_PDF']),
 'brume_g.pdf':pathlib.Path(os.environ['BRUME_KEEPER_PDF']),
 'brume_j.pdf':pathlib.Path(os.environ['BRUME_PLAYER_PDF']),
 'antre_local.pdf':pathlib.Path(os.environ['ANTRE_SOURCE_PDF'])}
SC=['scenario3','scenario4','scenario5','scenario6','scenario7'];R=[]
def ck(n,c,d=None):R.append({'name':n,'status':'PASS' if c else 'FAIL'});assert c,(n,d)
def players(n):return [{'name':f'I{i}','stats':{'HP':10+i,'SAN':50+i,'MP':10,'Luck':40+i},'inventory':[f'item{i}']} for i in range(1,n+1)]
def clear():
 for n in SRC:
  p=ROOT/'sources'/n
  if p.exists() or p.is_symlink():p.unlink()
def install():
 clear()
 for n,s in SRC.items():os.symlink(s,ROOT/'sources'/n)
try:
 ck('checkpoint_binding',json.loads((ROOT/'certification'/'authority.json').read_text())['checkpoint']==328)
 ck('no_pdf_embedded',not any(ROOT.rglob('*.pdf')))
 clear();t=OfflinePlayableRuntimeV1(ROOT,pathlib.Path(tempfile.mkdtemp())/'t.sqlite');ck('self_test',t.self_test()['status']=='PASS');t.close()
 for sk in SC:
  t=OfflinePlayableRuntimeV1(ROOT,pathlib.Path(tempfile.mkdtemp())/'t.sqlite');ck(sk+'_source_missing',t.new_session(sk,players(1)).get('code')=='PRIVATE_SOURCE_PACK_REQUIRED');t.close()
 install();t=OfflinePlayableRuntimeV1(ROOT,pathlib.Path(tempfile.mkdtemp())/'t.sqlite');ck('all_sources_ready',all(t.source.public_status()['scenarios'].values()));t.close()
 case=0
 for sk in SC:
  for n in range(1,5):
   case+=1;t=OfflinePlayableRuntimeV1(ROOT,pathlib.Path(tempfile.mkdtemp())/'t.sqlite');o=t.new_session(sk,players(n));ck(f'case{case}_session',o['status']=='SESSION_READY',o);ck(f'case{case}_views',len(t.player_views())==n)
   state,_=t.db.state()
   for pid,cid in state['interface_session']['control_map'].items():ck(f'case{case}_{pid}_prompt',t.interface.decision_prompt(pid,cid)['prompt']=='Que fais-tu ?')
   roll=t.roll('1d100','P1');ck(f'case{case}_roll',1<=roll['result']<=100);ck(f'case{case}_action',t.record_action('P1',f'A{case}',roll['result'])['status']=='COMMIT');ck(f'case{case}_replay',StrictReplaySaveResumeContinuityV1.verify_engine(t.engine)['status']=='REPLAY_MATCH')
   sid=f'c329_{case}';ck(f'case{case}_save',t.save(sid)['status']=='SAVED');ck(f'case{case}_restore',t.restore_file(sid+'.json')['status']=='RESTORED_STRICT');t.close();(ROOT/'saves'/(sid+'.json')).unlink(missing_ok=True)
finally:clear()
print(f"{sum(x['status']=='PASS' for x in R)}/{len(R)} PASS")
