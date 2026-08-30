import json
import tempfile
from pathlib import Path

from integrated_adjudication_r1_c4 import SourceBackedRuntimeR1C4
from registry_r1_c4 import (
    EQUIPMENT, OCCUPATIONS, SKILLS, WEAPONS,
    registry_summary, resolve_equipment, resolve_occupation, resolve_skill,
    resolve_weapon, validate_custom_occupation,
)
from scenario_router_r1_c4 import ROUTES, player_projection, resolve_route

checks=[]
def ck(name, cond, detail=None):
    checks.append((name,bool(cond)))
    if not cond: raise AssertionError((name,detail))


def run():
    s=registry_summary()
    ck('skill_count',s['skills']>=40,s)
    ck('archaeologist_only_verified_occupation','ARCHAEOLOGIST' in OCCUPATIONS)
    a=resolve_occupation('ARCHAEOLOGIST',characteristics={'EDU':75})
    ck('archaeologist_resolved',a['status']=='RESOLVED',a)
    ck('archaeologist_points',a['record']['occupation_skill_points']==300,a)
    ck('archaeologist_credit',a['record']['credit_min']==10 and a['record']['credit_max']==40,a)
    ck('archaeologist_eight_slots',len(a['record']['skill_slots'])==8,a)
    ck('unknown_occupation_closed',resolve_occupation('ASTRONAUT')['code']=='OCCUPATION_RECORD_UNMATERIALIZED')
    ck('custom_requires_auth',validate_custom_occupation(authorized=False,skill_ids=['ARCHAEOLOGY'],credit_min=10,credit_max=40)['code']=='CUSTOM_OCCUPATION_NOT_AUTHORIZED')
    ck('custom_bad_skill_closed',validate_custom_occupation(authorized=True,skill_ids=['NOT_A_SKILL'],credit_min=10,credit_max=40)['code']=='CUSTOM_OCCUPATION_SKILL_UNRESOLVED')
    ck('custom_authorized',validate_custom_occupation(authorized=True,skill_ids=['ARCHAEOLOGY','HISTORY'],credit_min=10,credit_max=40)['status']=='AUTHORIZED_CUSTOM')

    ck('archaeology_base',resolve_skill('ARCHAEOLOGY')['record']['base']==1)
    ck('spot_hidden_base',resolve_skill('SPOT_HIDDEN')['record']['base']==25)
    ck('dodge_needs_dex',resolve_skill('DODGE')['code']=='DODGE_REQUIRES_VALID_DEX')
    ck('dodge_half_dex',resolve_skill('DODGE',dex=65)['record']['base']==32)
    ck('unknown_skill_closed',resolve_skill('ALIEN_TELEPATHY')['code']=='SKILL_RECORD_UNMATERIALIZED')

    for wid, dmg, rng, mal in [
        ('REVOLVER_38_OR_9MM','1D10',15,100),('LEE_ENFIELD_303','2D6+4',110,100),('THOMPSON_SMG','1D10+2',20,96)
    ]:
        w=resolve_weapon(wid); ck(wid+'_resolved',w['status']=='RESOLVED_MECHANICS',w); ck(wid+'_mechanics',(w['record']['damage'],w['record']['base_range_yards'],w['record']['malfunction'])==(dmg,rng,mal),w); ck(wid+'_no_auto_possession',w['auto_possession'] is False,w)
    ck('unknown_weapon_closed',resolve_weapon('MG34')['code']=='WEAPON_RECORD_UNMATERIALIZED')
    for eid in EQUIPMENT:
        e=resolve_equipment(eid); ck(eid+'_reference',e['status']=='RESOLVED_REFERENCE',e); ck(eid+'_not_possessed',e['auto_possession'] is False,e)
    ck('unknown_equipment_closed',resolve_equipment('MAGIC_LANTERN')['code']=='EQUIPMENT_RECORD_UNMATERIALIZED')

    ck('routes_six',set(ROUTES)=={'MAISON_PENDU','BRUME','ANTRE','MUSE','EXPLORATEUR','SOLEIL_NOIR'})
    empty={}
    maison=resolve_route('MAISON_PENDU',empty); ck('maison_mapping_corrected_closed',maison['code']=='SCENARIO_SOURCE_IDENTITY_UNVERIFIED',maison); ck('maison_ae_substitution_forbidden',maison['correction']=='AE_COLLECTION_SUBSTITUTION_FORBIDDEN',maison)
    ck('unknown_scenario_closed',resolve_route('NOT_REAL',empty)['code']=='SCENARIO_NOT_REGISTERED')
    # Missing source paths must fail closed for all known materialized routes.
    for key in ('BRUME','ANTRE','MUSE','EXPLORATEUR','SOLEIL_NOIR'):
        r=resolve_route(key,empty); ck(key+'_missing_source_closed',r['status']=='BLOCKED',r)

    # Runtime must not create any state when canonical route is not ready.
    td=Path(tempfile.mkdtemp(prefix='r1c4_public_'))
    fake_rules=td/'missing_rules.zip'
    rt=SourceBackedRuntimeR1C4(td/'r.sqlite',fake_rules,empty,b'c4-public')
    before=rt.state_digest()
    out=rt.new_canonical_session('MAISON_PENDU',[{'name':'A','stats':{'HP':10,'SAN':50,'MP':10,'Luck':50}}])
    ck('blocked_session',out['status']=='FAIL_CLOSED',out); ck('blocked_session_no_state',rt.state_digest()==before,(rt.state_digest(),before))
    rt.close()

    report={'schema':'SOLIDSTATE_R1_C4_PUBLIC_REGISTRY_ROUTER_TEST_V1','result':'PASS','passed':len(checks),'total':len(checks),'registry_summary':s,'scope':'minimal source-grounded registries + canonical source router + fail-closed C3 mapping correction'}
    print(json.dumps(report,indent=2)); return report

if __name__=='__main__': run()
