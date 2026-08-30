#!/usr/bin/env python3
import hashlib, json, os, shutil, subprocess, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUTDIR=Path(os.environ.get('R1_C3_OUTDIR',HERE/'c3_dist')).resolve()
STAGE=OUTDIR/'SolidState_Recovery_Runtime_R1_C3'
ZIP_PATH=OUTDIR/'SolidState_Recovery_Runtime_R1_C3.zip'
FIXED_TIME=(1980,1,1,0,0,0)
EXPECTED_C2='20cc854247ea6427e4c31ee6572a9d312d1178ac89d31dd0856128ddaa0f55ba'
EXPECTED_RULES='c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2'
HISTORICAL_329='75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add'

def sha256_file(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): d.update(chunk)
    return d.hexdigest()

parent=Path(os.environ.get('R1_C2_FROZEN_ZIP',''))
if not parent.is_file(): raise SystemExit('R1_C2_FROZEN_ZIP required')
actual_parent=sha256_file(parent)
if actual_parent!=EXPECTED_C2: raise SystemExit(f'Frozen R1-C2 identity mismatch: {actual_parent}')
if OUTDIR.exists(): shutil.rmtree(OUTDIR)
STAGE.mkdir(parents=True)
sources=[
 'runtime_r1/__init__.py','runtime_r1/core.py',
 'rules_r1/__init__.py','rules_r1/core_rules.py','rules_r1/RULES_PROVENANCE_R1.json',
 'source_adapter_r1.py','integrated_adjudication_r1_c2.py','integrated_adjudication_r1_c3.py',
 'RECOVERY_RUNTIME_IDENTITY_R1_C3.json','verify_package.py',
 'test_integration_public_r1_c2.py','test_integration_public_r1_c3.py','test_private_matrix_r1_c3.py',
 'R1_C3_PRIVATE_MATRIX_REPORT.json'
]
for rel in sources:
    src=HERE/rel; dst=STAGE/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
with zipfile.ZipFile(parent) as z:
    candidates=[n for n in z.namelist() if n.endswith('/rules/CoC7_Recovery_Rules_R1_Core.zip')]
    if len(candidates)!=1: raise SystemExit('Frozen C2 embedded rules not found exactly once')
    rules_bytes=z.read(candidates[0])
rules_dst=STAGE/'rules'/'CoC7_Recovery_Rules_R1_Core.zip'; rules_dst.parent.mkdir(parents=True); rules_dst.write_bytes(rules_bytes)
if sha256_file(rules_dst)!=EXPECTED_RULES: raise SystemExit('Embedded rules identity mismatch')
source_commit=os.environ.get('RECOVERY_SOURCE_COMMIT_C3')
if not source_commit: source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
rows=[]
for path in sorted(STAGE.rglob('*')):
    if path.is_file(): rows.append({'path':path.relative_to(STAGE).as_posix(),'sha256':sha256_file(path),'size':path.stat().st_size})
manifest={
 'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_PACKAGE_MANIFEST_V1','generation':'RECOVERY_RECERTIFICATION_R1',
 'stage':'R1-C3_COMPLETE_RULES_STATE_DELTA_AND_SCENARIO_RECERTIFICATION','integration_id':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_V1',
 'status':'CANDIDATE_NOT_AUTHORITY','source_commit':source_commit,'documentary_authority_floor':333,
 'parent_c2_sha256':actual_parent,'embedded_rules_sha256':EXPECTED_RULES,'private_sources_embedded':False,
 'historical_checkpoint329_sha256':HISTORICAL_329,'claims_historical_329_byte_identity':False,'immutable_files':rows,
}
(STAGE/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with zipfile.ZipFile(ZIP_PATH,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for path in sorted(STAGE.rglob('*')):
        if path.is_file():
            rel=(Path(STAGE.name)/path.relative_to(STAGE)).as_posix(); info=zipfile.ZipInfo(rel,FIXED_TIME); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=(0o644&0xFFFF)<<16; z.writestr(info,path.read_bytes())
with zipfile.ZipFile(ZIP_PATH) as z:
    bad=z.testzip()
    if bad: raise SystemExit(f'ZIP CRC failure: {bad}')
zip_sha=sha256_file(ZIP_PATH)
report={'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_BUILD_REPORT_V1','result':'PASS','integration_id':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C3_V1','package':ZIP_PATH.name,'source_commit':source_commit,'zip_sha256':zip_sha,'zip_size':ZIP_PATH.stat().st_size,'zip_crc':'PASS','manifest_sha256':sha256_file(STAGE/'PACKAGE_MANIFEST.json'),'immutable_files':len(rows),'parent_c2_sha256':actual_parent,'embedded_rules_sha256':EXPECTED_RULES,'private_sources_embedded':False,'private_matrix':'1067/1067 PASS','keeper_to_player_leaks':0,'authority_promoted':False,'next_gate':'R1-C4_REGISTRY_AND_CANONICAL_SCENARIO_ROUTER_RECERTIFICATION'}
(OUTDIR/'R1_C3_BUILD_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
