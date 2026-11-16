import json
import tempfile
from pathlib import Path

from source_adapter_r1_c4b import SOURCE_SPECS_C4B, verify_source_c4b
from scenario_router_r1_c4b import MAISON_PATH, ROUTES, resolve_route_c4b
from integrated_adjudication_r1_c4b import SourceBackedRuntimeR1C4B

checks=[]
def ck(name,cond,detail=None):
    checks.append((name,bool(cond)))
    if not cond: raise AssertionError((name,detail))


def run():
    spec=SOURCE_SPECS_C4B['MAISON_PENDU_SOURCE']
    ck('maison_hash_registered',spec.sha256=='03867cec90056dfb2777bdc6ff38013dd44acad9d8b08ecd571e795518ba1ee0')
    ck('maison_role',spec.role=='SCENARIO_SOURCE')
    route=ROUTES['MAISON_PENDU']
    ck('maison_route_compiled',route.canonical_path_ready is True,route)
    ck('maison_not_ae_collection',route.source_ids==('MAISON_PENDU_SOURCE',),route.source_ids)
    ck('maison_new_identity',route.scenario_id=='SCENARIO3_MAISON_DU_PENDU_R1_C4B',route.scenario_id)
    ck('graph_start',MAISON_PATH['start']=='MP_START_PARIS_CASE')
    ck('graph_has_paris_hub','MP_HUB_PARIS_INVESTIGATION' in MAISON_PATH['nodes'])
    ck('graph_has_gernec','MP_NODE_GERNEC' in MAISON_PATH['nodes'])
    ck('graph_has_lannion','MP_NODE_LANNION' in MAISON_PATH['nodes'])
    ck('graph_alternatives',MAISON_PATH['alternative_routes_preserved'] is True)
    ck('graph_no_forced_clue_order',MAISON_PATH['clue_order_forced'] is False)
    ck('graph_open_resolution',MAISON_PATH['open_resolution_preserved'] is True)
    ck('page_evidence_four',set(MAISON_PATH['source_page_text_sha256'])=={'1','2','3','4'})
    empty=resolve_route_c4b('MAISON_PENDU',{})
    ck('missing_private_source_closed',empty['status']=='BLOCKED' and empty['failed_source']=='MAISON_PENDU_SOURCE',empty)
    td=Path(tempfile.mkdtemp(prefix='r1c4b_public_'))
    fake=td/'wrong.pdf'; fake.write_bytes(b'not the scenario')
    bad=resolve_route_c4b('MAISON_PENDU',{'MAISON_PENDU_SOURCE':fake})
    ck('wrong_source_hash_closed',bad['status']=='BLOCKED' and bad['source_result']['code']=='SOURCE_HASH_MISMATCH',bad)
    ck('unknown_scenario_closed',resolve_route_c4b('NOT_REAL',{})['code']=='SCENARIO_NOT_REGISTERED')
    # Public CI has no private PDFs: runtime must stay mutation-free when startup dependencies are absent.
    rules=td/'missing_rules.zip'
    rt=SourceBackedRuntimeR1C4B(td/'r.sqlite',rules,{},b'c4b-public')
    before=rt.state_digest()
    out=rt.new_canonical_session('MAISON_PENDU',[{'name':'A','stats':{'HP':10,'SAN':50,'MP':10,'Luck':50}}])
    ck('public_start_fail_closed',out['status']=='FAIL_CLOSED',out)
    ck('public_start_no_state_mutation',rt.state_digest()==before)
    rt.close()
    report={'schema':'SOLIDSTATE_R1_C4B_MAISON_PUBLIC_TEST_V1','result':'PASS','passed':len(checks),'total':len(checks),'scope':'exact source identity contract + non-linear canonical graph + private-source fail-closed'}
    print(json.dumps(report,indent=2)); return report

if __name__=='__main__': run()
