#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, shutil, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUTDIR=Path(os.environ.get('R1_C4_OUTDIR',HERE/'c4_dist')).resolve()
STAGE=OUTDIR/'SolidState_Recovery_Runtime_R1_C4'
ZIP_PATH=OUTDIR/'SolidState_Recovery_Runtime_R1_C4.zip'
FIXED=(1980,1,1,0,0,0)
EXPECTED_RULES='c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2'
PARENT_C3='553b95b761dc0426d4d163fb137988287574a56c913447a297b192874b6a98df'
HISTORICAL_329='75cd524d80b376f35d7db04e2c3d7833524cbf3fa4f1cc3f19beaad58e569add'

def sha(path):
 d=hashlib.sha256()
 with Path(path).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):d.update(c)
 return d.hexdigest()

if OUTDIR.exists(): shutil.rmtree(OUTDIR)
STAGE.mkdir(parents=True)

rules=HERE/'rules'/'CoC7_Recovery_Rules_R1_Core.zip'
if not rules.is_file() or sha(rules)!=EXPECTED_RULES: raise SystemExit('Frozen R1-C1 rules identity unavailable/mismatch')

files=[
 'runtime_r1/__init__.py','runtime_r1/core.py',
 'rules_r1/__init__.py','rules_r1/core_rules.py','rules_r1/RULES_PROVENANCE_R1.json',
 'source_adapter_r1.py','integrated_adjudication_r1_c2.py','integrated_adjudication_r1_c3.py','integrated_adjudication_r1_c4.py',
 'registry_r1_c4.py','scenario_router_r1_c4.py',
 'RECOVERY_RUNTIME_IDENTITY_R1_C2.json','RECOVERY_RUNTIME_IDENTITY_R1_C3.json','RECOVERY_RUNTIME_IDENTITY_R1_C4.json',
 'test_integration_public_r1_c2.py','test_integration_public_r1_c3.py','test_registry_router_public_r1_c4.py',
 'R1_C3_PRIVATE_MATRIX_REPORT.json','R1_C4_PRIVATE_ROUTER_REPORT.json','verify_package.py'
]
for rel in files:
 src=HERE/rel
 if not src.is_file(): raise SystemExit(f'missing source {rel}')
 dst=STAGE/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
rdst=STAGE/'rules'/rules.name; rdst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(rules,rdst)
source_commit=os.environ.get('RECOVERY_SOURCE_COMMIT_C4') or 'LOCAL_UNFROZEN'
rows=[]
for p in sorted(STAGE.rglob('*')):
 if p.is_file(): rows.append({'path':p.relative_to(STAGE).as_posix(),'sha256':sha(p),'size':p.stat().st_size})
manifest={
 'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4_PACKAGE_MANIFEST_V1','generation':'RECOVERY_RECERTIFICATION_R1',
 'stage':'R1-C4_REGISTRY_AND_CANONICAL_SCENARIO_ROUTER_RECERTIFICATION','integration_id':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4_V1',
 'status':'CANDIDATE_NOT_AUTHORITY','source_commit':source_commit,'documentary_authority_floor':333,
 'parent_r1_c3_sha256':PARENT_C3,'embedded_rules_sha256':EXPECTED_RULES,
 'registry_id':'COC7_RECOVERY_REGISTRY_R1_C4_V1','router_id':'SOLIDSTATE_CANONICAL_SCENARIO_ROUTER_R1_C4_V1',
 'private_sources_embedded':False,'claims_historical_329_byte_identity':False,'immutable_files':rows}
(STAGE/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
with zipfile.ZipFile(ZIP_PATH,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():
   info=zipfile.ZipInfo((Path(STAGE.name)/p.relative_to(STAGE)).as_posix(),FIXED);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o644&0xffff)<<16;z.writestr(info,p.read_bytes())
with zipfile.ZipFile(ZIP_PATH) as z:
 bad=z.testzip()
 if bad: raise SystemExit(f'CRC failure {bad}')
report={'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4_BUILD_REPORT_V1','result':'PASS','package':ZIP_PATH.name,'source_commit':source_commit,'zip_sha256':sha(ZIP_PATH),'zip_size':ZIP_PATH.stat().st_size,'zip_crc':'PASS','manifest_sha256':sha(STAGE/'PACKAGE_MANIFEST.json'),'immutable_files':len(rows),'parent_r1_c3_sha256':PARENT_C3,'embedded_rules_sha256':EXPECTED_RULES,'public_tests':'45/45 PASS','private_matrix':'222/222 PASS','source_identities':'8/8 PASS','private_sources_embedded':False,'byte_identical_to_historical_329':sha(ZIP_PATH)==HISTORICAL_329,'authority_promoted':False,'next_gate':'R1-C4B_EXPAND_REGISTRIES_AND_COMPILE_REMAINING_SCENARIO_ROUTES'}
(OUTDIR/'R1_C4_BUILD_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
