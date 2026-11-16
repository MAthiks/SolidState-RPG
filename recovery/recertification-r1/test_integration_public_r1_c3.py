import copy
import hashlib
import hmac
import json
import os
import tempfile
from pathlib import Path

from integrated_adjudication_r1_c3 import SourceBackedRuntimeR1C3, INTEGRATION_ID
from runtime_r1.core import canon

checks=[]
def ck(name, cond, detail=None):
    checks.append((name,bool(cond)))
    if not cond: raise AssertionError((name,detail))

def players(n=2):
    return [{"name":f"P{i}","stats":{"HP":15,"SAN":60,"MP":10,"Luck":50}} for i in range(1,n+1)]

def run():
    rules_zip=Path(os.environ['R1_C1_RULES_ZIP'])
    td=Path(tempfile.mkdtemp(prefix='r1c3_public_'))
    sources={"COC7_KEEPER":td/'missing-k.pdf',"COC7_INVESTIGATOR":td/'missing-i.pdf'}
    r=SourceBackedRuntimeR1C3(td/'r.sqlite',rules_zip,sources,b'c3-public')
    ck('ready',r.new_session(players(),'C3-PUBLIC')['status']=='SESSION_READY')
    base=r.state_digest()
    bad=r.append_mechanical_event(player_id='P1',character_id='C2',action_id='BAD',roll=50,deltas=[{'stat':'SAN','op':'ADD','value':-1}],mechanic='TEST',event_id='BAD-ACTOR')
    ck('bad_actor_blocked',bad['code']=='ACTOR_CONTROL_MISMATCH',bad); ck('bad_actor_no_mut',r.state_digest()==base)
    bad=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='BAD',roll=0,deltas=[{'stat':'SAN','op':'ADD','value':-1}],mechanic='TEST',event_id='BAD-ROLL')
    ck('bad_roll_blocked',bad['code']=='ROLL_INVALID',bad); ck('bad_roll_no_mut',r.state_digest()==base)
    bad=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='BAD',roll=50,deltas=[{'stat':'SAN','op':'ADD','value':-999}],mechanic='TEST',event_id='BAD-BOUND')
    ck('bound_blocked',bad['code']=='MECHANICAL_DELTA_BELOW_MINIMUM',bad); ck('bound_no_mut',r.state_digest()==base)
    bad=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='BAD',roll=50,deltas=[{'stat':'DEX','op':'ADD','value':1}],mechanic='TEST',event_id='BAD-STAT')
    ck('unmaterialized_stat_blocked',bad['code']=='MECHANICAL_STAT_UNMATERIALIZED',bad); ck('unmaterialized_stat_no_mut',r.state_digest()==base)
    good=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='RESOURCE',roll=42,deltas=[{'stat':'MP','op':'ADD','value':-2},{'stat':'Luck','op':'ADD','value':3}],mechanic='GENERIC_DELTA_TEST',event_id='MECH-1',provenance={'test':'public'})
    ck('generic_commit',good['status']=='COMMIT',good)
    st=r.state(); ck('mp_changed',st['characters']['C1']['stats']['MP']==8,st); ck('luck_changed',st['characters']['C1']['stats']['Luck']==53,st)
    ck('other_character_isolated',st['characters']['C2']['stats']=={'HP':15,'SAN':60,'MP':10,'Luck':50},st['characters']['C2'])
    ck('generic_replay_match',r.verify_journal(st)['status']=='REPLAY_MATCH')
    dup_before=r.state_digest(); dup=r.append_mechanical_event(player_id='P1',character_id='C1',action_id='DUP',roll=42,deltas=[],mechanic='TEST',event_id='MECH-1')
    ck('duplicate_blocked',dup['code']=='DUPLICATE_EVENT_ID',dup); ck('duplicate_no_mut',r.state_digest()==dup_before)
    bundle=r.save_bundle(); ck('save_schema',bundle['payload']['integration_id']==INTEGRATION_ID,bundle['payload'])
    rr=SourceBackedRuntimeR1C3(td/'restore.sqlite',rules_zip,sources,b'c3-public'); rr.new_session(players(),'C3-PUBLIC')
    restored=rr.restore_bundle(bundle); ck('restore_strict',restored['status']=='RESTORED_STRICT',restored); ck('restore_identical',rr.state_digest()==r.state_digest()); ck('restore_replay',rr.verify_journal(rr.state())['status']=='REPLAY_MATCH')
    tam=copy.deepcopy(bundle); tam['payload']['state']['journal'][0]['event']['payload']['mechanical_deltas'][0]['value']=-3
    raw=canon(tam['payload']).encode(); tam['auth']['payload_sha256']=hashlib.sha256(raw).hexdigest(); tam['auth']['hmac_sha256']=hmac.new(rr.secret,raw,hashlib.sha256).hexdigest()
    before=rr.state_digest(); rejected=rr.restore_bundle(tam); ck('tampered_delta_rejected',rejected['status']=='FAIL_CLOSED',rejected); ck('tampered_restore_no_mut',rr.state_digest()==before)
    source_before=r.state_digest(); san=r.adjudicate_sanity_loss(player_id='P1',character_id='C1',loss=5,sanity_start_of_day=60,san_roll=55,event_id='SAN-MISSING')
    ck('san_source_gate_blocked',san['code']=='SOURCE_PREFLIGHT_FAILED',san); ck('san_source_gate_no_mut',r.state_digest()==source_before)
    r.close(); rr.close()
    report={'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_PUBLIC_TEST_V1','result':'PASS','passed':len(checks),'total':len(checks),'scope':'generic typed mechanical deltas, strict replay/save, actor isolation, private-source fail-closed'}
    print(json.dumps(report,indent=2)); return report

if __name__=='__main__': run()
