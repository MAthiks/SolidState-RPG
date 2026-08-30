import json
import tempfile
from pathlib import Path

from source_adapter_r1_c4b import SOURCE_SPECS_C4B
from registry_r1_c4b2_lsnt import (
    REGISTRY_ID,
    registry_summary,
    resolve_skill,
    resolve_weapon,
    scenario_reference_status,
)
from scenario_router_r1_c4b2_lsnt import LSNT_PATH, ROUTES, resolve_route_c4b2
from integrated_adjudication_r1_c4b2_lsnt import SourceBackedRuntimeR1C4B2LSNT

checks=[]
def ck(name,cond,detail=None):
    checks.append((name,bool(cond)))
    if not cond: raise AssertionError((name,detail))


def run():
    keeper=SOURCE_SPECS_C4B['SOLEIL_NOIR_KEEPER']
    player=SOURCE_SPECS_C4B['SOLEIL_NOIR_PLAYER']
    ck('keeper_hash_registered',keeper.sha256=='9c1e609d50250599a30fdb3ec899cf8b62cc9638944891900d0a982d958760f6')
    ck('player_hash_registered',player.sha256=='9838b2f3e816e1ce08c29fa148eef765d2d1934a334ce8a78f8313fe6dc1b889')
    route=ROUTES['SOLEIL_NOIR']
    ck('lsnt_v15_identity',route.scenario_id=='LSNT-V1.5-MULTI-1942')
    ck('protected_pair',route.source_ids==('SOLEIL_NOIR_KEEPER','SOLEIL_NOIR_PLAYER'))
    ck('route_compiled',route.canonical_path_ready is True)
    ck('route_release_class',route.release_class=='RECOVERY_SOURCE_COMPILED_C4B2')
    ck('graph_start',LSNT_PATH['start']=='LSNT_START_BIR_HALIM_BRIEFING')
    ck('oasis_distinct','LSNT_NODE_OASIS' in LSNT_PATH['nodes'])
    ck('ten_endings',len(LSNT_PATH['ending_families'])==10)
    ck('timeline_j1_j4',len(LSNT_PATH['world_timeline'])==11 and LSNT_PATH['world_clock_j1_j4_preserved'])
    ck('front_checks',LSNT_PATH['front_track_checks']==['0600','1800'])
    ck('exposure_thresholds',LSNT_PATH['exposure_thresholds']==[2,4,6])
    ck('no_single_clue',LSNT_PATH['single_clue_indispensable'] is False)
    ck('no_forced_clue_order',LSNT_PATH['clue_order_forced'] is False)
    ck('three_nonhuman_routes',LSNT_PATH['non_human_nature_routes_minimum']>=3)
    ck('knowledge_partition',LSNT_PATH['knowledge_partition_required'] is True)
    ck('timeline_split',LSNT_PATH['timeline_synchronizer_required_if_split'] is True)
    ck('individual_exposure',LSNT_PATH['individual_exposure_required'] is True)
    ck('individual_sanity',LSNT_PATH['individual_sanity_required'] is True)
    ck('party_resolution',LSNT_PATH['party_resolution_required'] is True)
    ck('bcra_autonomous',LSNT_PATH['bcra_ally_autonomous'] is True)
    ck('maison_preserved',ROUTES['MAISON_PENDU'].canonical_path_ready is True)

    demolitions=resolve_skill('DEMOLITIONS')
    machine_gun=resolve_skill('FIREARMS_MACHINE_GUN')
    ck('demolitions_resolved',demolitions['status']=='RESOLVED' and demolitions['record']['base']==1,demolitions)
    ck('demolitions_source_page',demolitions['record']['source_page']==104)
    ck('machine_gun_resolved',machine_gun['status']=='RESOLVED' and machine_gun['record']['base']==10,machine_gun)
    ck('machine_gun_source_page',machine_gun['record']['source_page']==107)
    ck('registry_identity',demolitions['registry_id']==REGISTRY_ID and machine_gun['registry_id']==REGISTRY_ID)
    ck('mg34_not_silently_substituted',resolve_weapon('MG34')['status']=='BLOCKED')
    mg34=scenario_reference_status('MG34')
    explosives=scenario_reference_status('EXPLOSIVES')
    ck('mg34_reference_only',mg34['status']=='REFERENCE_ONLY' and mg34['mechanics_status']=='UNMATERIALIZED_SPECIFIC_WEAPON',mg34)
    ck('mg34_substitution_forbidden',mg34['substitution_allowed'] is False)
    ck('explosives_reference_only',explosives['status']=='REFERENCE_ONLY' and explosives['mechanics_status']=='TYPE_UNSPECIFIED_BY_SCENARIO',explosives)
    ck('explosives_substitution_forbidden',explosives['substitution_allowed'] is False)
    summary=registry_summary()
    ck('no_specific_mg34_claim',summary['specific_mg34_mechanics_materialized'] is False)
    ck('no_auto_explosive_selection',summary['automatic_explosive_type_selection'] is False)

    empty=resolve_route_c4b2('SOLEIL_NOIR',{})
    ck('missing_keeper_closed',empty['status']=='BLOCKED' and empty['failed_source']=='SOLEIL_NOIR_KEEPER',empty)
    td=Path(tempfile.mkdtemp(prefix='r1c4b2_public_'))
    fake=td/'wrong.pdf'; fake.write_bytes(b'not lsnt')
    bad=resolve_route_c4b2('SOLEIL_NOIR',{'SOLEIL_NOIR_KEEPER':fake})
    ck('wrong_keeper_hash_closed',bad['status']=='BLOCKED' and bad['source_result']['code']=='SOURCE_HASH_MISMATCH',bad)
    ck('unknown_scenario_closed',resolve_route_c4b2('NOT_REAL',{})['code']=='SCENARIO_NOT_REGISTERED')
    rt=SourceBackedRuntimeR1C4B2LSNT(td/'r.sqlite',td/'missing_rules.zip',{},b'c4b2-public')
    ck('runtime_demolitions_registry',rt.registry_resolve('SKILL','DEMOLITIONS')['status']=='RESOLVED')
    ck('runtime_mg34_reference_only',rt.registry_resolve('SCENARIO_REFERENCE','MG34')['status']=='REFERENCE_ONLY')
    before=rt.state_digest()
    out=rt.new_canonical_session('SOLEIL_NOIR',[{'name':'A'}])
    ck('public_start_fail_closed',out['status']=='FAIL_CLOSED',out)
    ck('public_start_no_state_mutation',rt.state_digest()==before)
    rt.close()
    report={'schema':'SOLIDSTATE_R1_C4B2_LSNT_V1_5_PUBLIC_TEST_V2','result':'PASS','passed':len(checks),'total':len(checks),'scope':'exact source identity + v1.5 multiplayer route + source-grounded skills + explicit no-substitution registry + private-source fail-closed'}
    print(json.dumps(report,indent=2)); return report

if __name__=='__main__': run()
