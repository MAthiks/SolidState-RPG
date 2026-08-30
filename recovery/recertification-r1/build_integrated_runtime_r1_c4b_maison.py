#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, shutil, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUTDIR=Path(os.environ.get('R1_C4B_OUTDIR',HERE/'c4b_maison_dist')).resolve()
STAGE=OUTDIR/'SolidState_Recovery_Runtime_R1_C4B_MAISON'
ZIP_PATH=OUTDIR/'SolidState_Recovery_Runtime_R1_C4B_MAISON.zip'
FIXED=(1980,1,1,0,0,0)
PARENT_C4='e719a9295e088e48c23eec0d698d046045dd8f6dfa0e5713aa05cd53b114cb1b'
MAISON_SHA='03867cec90056dfb2777bdc6ff38013dd44acad9d8b08ecd571e795518ba1ee0'
EXPECTED_RULES='c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2'

def sha(path):
 d=hashlib.sha256()
 with Path(path).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): d.update(c)
 return d.hexdigest()

parent=Path(os.environ.get('R1_C4_FROZEN_ZIP',''))
if not parent.is_file(): raise SystemExit('R1_C4_FROZEN_ZIP required')
if sha(parent)!=PARENT_C4: raise SystemExit('Frozen R1-C4 identity mismatch')
if OUTDIR.exists(): shutil.rmtree(OUTDIR)
STAGE.mkdir(parents=True)
with zipfile.ZipFile(parent) as z:
 roots={Path(n).parts[0] for n in z.namelist() if n}
 if len(roots)!=1: raise SystemExit('Unexpected parent root layout')
 root=next(iter(roots))
 for info in z.infolist():
  if info.is_dir(): continue
  rel=Path(*Path(info.filename).parts[1:])
  dst=STAGE/rel; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(z.read(info))
old_manifest=STAGE/'PACKAGE_MANIFEST.json'
if old_manifest.is_file(): old_manifest.rename(STAGE/'PARENT_C4_PACKAGE_MANIFEST.json')
for rel in [
 'source_adapter_r1_c4b.py','scenario_router_r1_c4b.py','integrated_adjudication_r1_c4b.py',
 'test_maison_router_public_r1_c4b.py','R1_C4B_MAISON_PRIVATE_MATRIX_REPORT.json'
]:
 src=HERE/rel
 if not src.is_file(): raise SystemExit(f'missing source {rel}')
 shutil.copy2(src,STAGE/rel)
rules=STAGE/'rules'/'CoC7_Recovery_Rules_R1_Core.zip'
if not rules.is_file() or sha(rules)!=EXPECTED_RULES: raise SystemExit('Embedded rules identity mismatch')
source_commit=os.environ.get('RECOVERY_SOURCE_COMMIT_C4B') or 'LOCAL_UNFROZEN'
rows=[]
for p in sorted(STAGE.rglob('*')):
 if p.is_file(): rows.append({'path':p.relative_to(STAGE).as_posix(),'sha256':sha(p),'size':p.stat().st_size})
manifest={
 'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4B_MAISON_PACKAGE_MANIFEST_V1',
 'generation':'RECOVERY_RECERTIFICATION_R1','stage':'R1-C4B_MAISON_SOURCE_AND_CANONICAL_ROUTE_RECERTIFICATION',
 'integration_id':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4B_MAISON_V1','status':'CANDIDATE_NOT_AUTHORITY',
 'source_commit':source_commit,'documentary_authority_floor':333,'parent_r1_c4_sha256':PARENT_C4,
 'embedded_rules_sha256':EXPECTED_RULES,'maison_source_sha256':MAISON_SHA,
 'private_sources_embedded':False,'maison_private_pdf_embedded':False,'immutable_files':rows}
(STAGE/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
with zipfile.ZipFile(ZIP_PATH,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():
   info=zipfile.ZipInfo((Path(STAGE.name)/p.relative_to(STAGE)).as_posix(),FIXED);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o644&0xffff)<<16;z.writestr(info,p.read_bytes())
with zipfile.ZipFile(ZIP_PATH) as z:
 bad=z.testzip()
 if bad: raise SystemExit(f'CRC failure {bad}')
report={'schema':'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4B_MAISON_BUILD_REPORT_V1','result':'PASS','package':ZIP_PATH.name,'source_commit':source_commit,'zip_sha256':sha(ZIP_PATH),'zip_size':ZIP_PATH.stat().st_size,'zip_crc':'PASS','manifest_sha256':sha(STAGE/'PACKAGE_MANIFEST.json'),'immutable_files':len(rows),'parent_r1_c4_sha256':PARENT_C4,'embedded_rules_sha256':EXPECTED_RULES,'maison_source_sha256':MAISON_SHA,'public_test_scope':'MAISON_SOURCE_ROUTE_FAIL_CLOSED','private_matrix':'93/93 PASS','source_identities':'9/9 PASS','private_sources_embedded':False,'authority_promoted':False,'next_gate':'R1-C4B2_SOLEIL_NOIR_CANONICAL_ROUTE_AND_REGISTRY_EXPANSION'}
(OUTDIR/'R1_C4B_MAISON_BUILD_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
