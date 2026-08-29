import copy, hashlib, hmac, json, os, tempfile
from pathlib import Path

from offline.runtime import OfflinePlayableRuntimeV1
from solidstate_runtime import MultiplayerRuntimeContractV2

ROOT=Path(os.environ.get('OFFLINE_PACKAGE_ROOT','/mnt/data/ss331_runtime')).resolve()
SRC={
 'ae.pdf':Path(os.environ.get('AE_SOURCE_PDF',"/mnt/data/L'Appel de Cthulhu 7 - Aventures Effroyables.pdf")),
 'brume_g.pdf':Path(os.environ.get('BRUME_KEEPER_PDF','/mnt/data/Les_Registres_de_Brume_v1.1_Gardien_SPOILERS_Natif.pdf')),
 'brume_j.pdf':Path(os.environ.get('BRUME_PLAYER_PDF','/mnt/data/Les_Registres_de_Brume_v1.1_Joueur_Protege_Natif.pdf')),
 'antre.pdf':Path(os.environ.get('ANTRE_SOURCE_PDF','/mnt/data/antre.pdf')),
}
SCENARIOS=['scenario3','scenario4','scenario5','scenario6','scenario7']; checks=[]
def ck(n,c,d=None):
 checks.append({'name':n,'pass':bool(c)}); assert c,(n,d)
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def install_sources():
 d=ROOT/'sources'; d.mkdir(exist_ok=True)
 for p in d.iterdir():
  if p.is_symlink() or p.is_file():p.unlink()
 for n,s in SRC.items():os.symlink(s,d/n)
def clear_sources():
 d=ROOT/'sources'; d.mkdir(exist_ok=True)
 for p in d.iterdir():
  if p.is_symlink() or p.is_file():p.unlink()
def players(n):return [{'name':f'Investigateur {i}','stats':{'HP':12+i,'SAN':60+i,'MP':8+i,'Luck':40+i},'inventory':[f'objet_{i}',f'carnet_{i}']} for i in range(1,n+1)]
def tables(rt):return {t:rt.save_manager._rows(t) for t in rt.save_manager.TABLES}
def snap(rt):
 s,c=rt.db.state();return {'state':s,'commit':c,'tables':tables(rt),'views':rt.player_views()}
def reauth(rt,b):
 p=b['payload'];raw=rt.save_manager._canon(p).encode();b['auth']['payload_sha256']=hashlib.sha256(raw).hexdigest();b['auth']['hmac_sha256']=hmac.new(rt._secret,raw,hashlib.sha256).hexdigest()
def write(n,b):(ROOT/'saves'/n).write_text(json.dumps(b,ensure_ascii=False,indent=2),encoding='utf-8')
def clean(n):(ROOT/'saves'/n).unlink(missing_ok=True)
install_sources()
try:
 probe=OfflinePlayableRuntimeV1(ROOT,Path(tempfile.mkdtemp())/'probe.sqlite');ck('all_five_private_sources_ready',all(probe.source.public_status()['scenarios'].values()));probe.close()
 case=0
 for sk in SCENARIOS:
  for n in (1,2,3,4):
   case+=1;td=Path(tempfile.mkdtemp(prefix=f'ss331_{sk}_{n}_'));rt=OfflinePlayableRuntimeV1(ROOT,td/'live.sqlite');o=rt.new_session(sk,players(n),require_sources=True);ck(f'c{case}_session_ready',o.get('status')=='SESSION_READY',o)
   st,_=rt.db.state();cmap=st['interface_session']['control_map'];pids=list(cmap);ck(f'c{case}_party_v2_pre',MultiplayerRuntimeContractV2.validate_party(rt.engine,pids,True)['status']=='PASS')
   for i,(pid,cid) in enumerate(cmap.items(),1):
    ck(f'c{case}_{pid}_player_knowledge',rt.engine.knowledge.grant(cid,f'K_PLAYER_{case}_{i}','PLAYER',f'SRC_{case}_{i}')['status']=='COMMIT');ck(f'c{case}_{pid}_keeper_knowledge',rt.engine.knowledge.grant(cid,f'K_KEEPER_{case}_{i}','KEEPER',f'SRC_{case}_{i}')['status']=='COMMIT');ck(f'c{case}_{pid}_san_delta',rt.engine.mechanics.apply_delta(cid,'SAN',-i,minimum=0)['status']=='COMMIT');ck(f'c{case}_{pid}_luck_delta',rt.engine.mechanics.apply_delta(cid,'Luck',i)['status']=='COMMIT');w=rt.engine.wounds.state(cid);dmg=((w['max_hp']+1)//2 if i%2==0 else 1);ck(f'c{case}_{pid}_wound_change',rt.engine.wounds.apply_damage(cid,dmg)['status']=='COMMIT')
   ck(f'c{case}_action',rt.record_action('P1',f'SAVE_POINT_{case}',roll=((case*7)%100)+1)['status']=='COMMIT');views=copy.deepcopy(rt.player_views())
   for i,v in enumerate(views,1):
    ser=canon(v);ck(f'c{case}_view_{i}_own_knowledge',f'K_PLAYER_{case}_{i}' in ser);ck(f'c{case}_view_{i}_no_keeper','K_KEEPER_' not in ser)
    for j in range(1,n+1):
     if j!=i:ck(f'c{case}_view_{i}_no_foreign_{j}',f'K_PLAYER_{case}_{j}' not in ser)
   sid=f'cp331_case_{case}';sv=rt.save(sid);ck(f'c{case}_save',sv.get('status')=='SAVED',sv);b=json.loads((ROOT/'saves'/f'{sid}.json').read_text());ck(f'c{case}_schema_v2',b['payload']['schema']=='SOLIDSTATE_MULTIPLAYER_SAVE_RESUME_V2');ck(f'c{case}_floor_330',b['payload']['checkpoint_floor']==330);ck(f'c{case}_authority_v2',b['payload']['authority_id']=='MULTIPLAYER_1_TO_4_STATE_KNOWLEDGE_RECERTIFICATION_V2');saved=b['payload']['commit_sequence'];es=copy.deepcopy(b['payload']['canonical_state']);et=copy.deepcopy(b['payload']['tables'])
   rr=rt.restore_file(f'{sid}.json',require_sources=True);ck(f'c{case}_restore_same_runtime',rr.get('status')=='RESTORED_STRICT',rr);a=snap(rt);ck(f'c{case}_commit_exact',a['commit']==saved);ck(f'c{case}_canonical_exact',a['state']==es);ck(f'c{case}_tables_exact',a['tables']==et);ck(f'c{case}_views_exact',a['views']==views);ck(f'c{case}_party_v2_post',MultiplayerRuntimeContractV2.validate_party(rt.engine,pids,True)['status']=='PASS')
   for i,(pid,cid) in enumerate(cmap.items(),1):
    ck(f'c{case}_{pid}_cross_interface_self',rt.interface.status_panel(pid,cid)['status']=='READY')
    if n>1:ck(f'c{case}_{pid}_cross_interface_block',rt.interface.status_panel(pid,list(cmap.values())[i%n]).get('code')=='CHARACTER_NOT_CONTROLLED_BY_PLAYER')
   rt2=OfflinePlayableRuntimeV1(ROOT,td/'fresh.sqlite');rr2=rt2.restore_file(f'{sid}.json',require_sources=True);ck(f'c{case}_restore_new_engine',rr2.get('status')=='RESTORED_STRICT',rr2);a2=snap(rt2);ck(f'c{case}_new_engine_state_exact',a2['state']==es);ck(f'c{case}_new_engine_tables_exact',a2['tables']==et);ck(f'c{case}_new_engine_views_exact',a2['views']==views)
   hb={p:rt2.engine.mechanics.get_value(c,'HP') for p,c in cmap.items()};delta=rt2.engine.mechanics.apply_delta(cmap['P1'],'HP',-1,minimum=0);ck(f'c{case}_post_resume_commit',delta.get('status')=='COMMIT' and delta['commit']==saved+1,delta);ha={p:rt2.engine.mechanics.get_value(c,'HP') for p,c in cmap.items()};ck(f'c{case}_post_resume_target_only',ha['P1']==hb['P1']-1 and all(ha[p]==hb[p] for p in pids if p!='P1'));seq=[r['commit_sequence'] for r in rt2.db.conn.execute('SELECT commit_sequence FROM commits ORDER BY commit_sequence')];ck(f'c{case}_commit_ledger_contiguous',seq==list(range(1,saved+2)));rt.close();rt2.close();clean(f'{sid}.json')
 td=Path(tempfile.mkdtemp(prefix='ss331_negative_'));rt=OfflinePlayableRuntimeV1(ROOT,td/'live.sqlite');ck('neg_session',rt.new_session('scenario3',players(4),require_sources=True)['status']=='SESSION_READY');st,_=rt.db.state();cmap=st['interface_session']['control_map']
 for i,(pid,cid) in enumerate(cmap.items(),1):rt.engine.knowledge.grant(cid,f'NEG_PLAYER_{i}','PLAYER','NEG_SRC');rt.engine.knowledge.grant(cid,f'NEG_KEEPER_{i}','KEEPER','NEG_SRC')
 ck('neg_save',rt.save('neg_base')['status']=='SAVED');base=json.loads((ROOT/'saves'/'neg_base.json').read_text())
 def reject(name,mutator,rea=False,expected=None):
  b=copy.deepcopy(base);mutator(b)
  if rea:reauth(rt,b)
  fn=f'neg_{name}.json';write(fn,b);before=snap(rt);res=rt.restore_file(fn,require_sources=True);after=snap(rt);ck(f'neg_{name}_rejected',res.get('status')=='FAIL_CLOSED',res)
  if expected:ck(f'neg_{name}_code',res.get('code')==expected or res.get('reason')==expected,res)
  ck(f'neg_{name}_live_unchanged',after==before);clean(fn)
 reject('bad_hmac',lambda b:b['auth'].__setitem__('hmac_sha256','00'*32),False,'SAVE_AUTHENTICATION_FAILED');reject('downgrade_floor',lambda b:b['payload'].__setitem__('checkpoint_floor',326),True,'AUTHORITY_FLOOR_INVALID');reject('wrong_schema',lambda b:b['payload'].__setitem__('schema','SOLIDSTATE_SAVE_RESUME_V1'),True,'AUTHORITY_FLOOR_INVALID');reject('swap_control',lambda b:b['payload']['canonical_state']['interface_session']['control_map'].update({'P1':cmap['P2'],'P2':cmap['P1']}),True,'PARTY_CONTROL_MAP_MISMATCH');reject('owner_mismatch',lambda b:b['payload']['tables']['characters'][0].__setitem__('owner_id','P4'),True,'CONTROL_OWNERSHIP_INVALID')
 def mech(b):
  cid=cmap['P1']
  for r in b['payload']['tables']['mechanical_values']:
   if r['entity_id']==cid and r['key']=='SAN':r['value']+=7;return
 reject('mechanical_split_brain',mech,True,'MECHANICAL_CANONICAL_SQL_MISMATCH')
 def wound(b):
  cid=cmap['P2']
  for r in b['payload']['tables']['wounds_state']:
   if r['entity_id']==cid:r['major_wound']=1-r['major_wound'];return
 reject('wound_split_brain',wound,True,'WOUND_CANONICAL_SQL_MISMATCH')
 def inv(b):
  cid=cmap['P1']
  for r in b['payload']['tables']['inventory']:
   if r['owner_id']==cid:r['owner_id']=cmap['P2'];return
 reject('inventory_split_brain',inv,True,'REGISTRY_ITEM_MISSING_FROM_INVENTORY')
 def know(b):
  cid=cmap['P1']
  for r in b['payload']['tables']['knowledge_partitions']:
   if r['character_id']==cid and r['visibility']=='PLAYER':r['knowledge_id']='INJECTED_FOREIGN';return
 reject('knowledge_split_brain',know,True,'KNOWLEDGE_CANONICAL_SQL_MISMATCH')
 def char(b):
  cid=cmap['P1']
  for r in b['payload']['tables']['characters']:
   if r['character_id']==cid:r['state_json']=json.dumps({'name':'TAMPERED'});return
 reject('character_split_brain',char,True,'CHARACTER_CANONICAL_SQL_MISMATCH')
 def gap(b):
  rows=b['payload']['tables']['commits'];rows.pop(len(rows)//2) if len(rows)>2 else None
 reject('commit_gap',gap,True,'COMMIT_LEDGER_NOT_CONTIGUOUS')
 (ROOT/'saves'/'neg_json.json').write_text('{not-json');before=snap(rt);res=rt.restore_file('neg_json.json',require_sources=True);after=snap(rt);ck('neg_invalid_json_rejected',res.get('code')=='SAVE_FILE_INVALID_JSON');ck('neg_invalid_json_live_unchanged',before==after);clean('neg_json.json')
 write('neg_source.json',copy.deepcopy(base));before=snap(rt);clear_sources();rt.source._cache=None;res=rt.restore_file('neg_source.json',require_sources=True);after=snap(rt);ck('neg_missing_source_rejected',res.get('code')=='PRIVATE_SOURCE_PACK_REQUIRED_AFTER_RESTORE');ck('neg_missing_source_live_unchanged',before==after);install_sources();rt.source._cache=None;clean('neg_source.json')
 before=snap(rt);dr=rt.save_manager.restore(base);after=snap(rt);ck('neg_direct_nonpristine_rejected',dr.get('code')=='TARGET_NOT_PRISTINE');ck('neg_direct_nonpristine_unchanged',before==after);rt.close();clean('neg_base.json')
finally:clear_sources()
passed=sum(x['pass'] for x in checks);print(json.dumps({'checkpoint':331,'id':'MULTIPLAYER_SAVE_RESUME_RECERTIFICATION_V2','result':'PASS','passed':passed,'total':len(checks),'player_counts':[1,2,3,4],'scenarios':SCENARIOS,'checks':checks},ensure_ascii=False,indent=2))
