import json
from pathlib import Path
from .scenario4_release_gate import Scenario4ReleaseGateV1

class MultiScenarioStatusResolver:
 @staticmethod
 def resolve(root,key):
  b=Path(root)/key
  if key=="scenario3":
   d=json.loads((b/"LES_MAUDITS_RELEASE_READINESS.json").read_text());return {"status":d["release_class"],"pass_real":d["checks"]["pass_real"],"authority":"LES_MAUDITS_RELEASE_READINESS.json"}
  if key=="scenario4":
   release=Scenario4ReleaseGateV1.load_and_validate(b)
   if release.get("status")=="PASS":
    return {"status":"PASS_REAL","pass_real":True,"authority":"BRUME_PASS_REAL_RELEASE_319.json","parent_authority":"BRUME_FINAL_CLASSIFICATION.json"}
   d=json.loads((b/"BRUME_FINAL_CLASSIFICATION.json").read_text());return {"status":d["classification"],"pass_real":d["pass_real"],"authority":"BRUME_FINAL_CLASSIFICATION.json"}
  if key=="scenario5":
   d=json.loads((b/"ANTRE_PATH_PROOF_V2.json").read_text());return {"status":"COMPILED_CANDIDATE_NOT_PATH_PROVEN","pass_real":False,"authority":"ANTRE_PATH_PROOF_V2.json","blocker":d["status"]}
  if key=="scenario6":
   d=json.loads((b/"MUSE_FREEZE_125.json").read_text());return {"status":d["classification"],"pass_real":d["pass_real"],"authority":"MUSE_FREEZE_125.json"}
  if key=="scenario7":
   d=json.loads((b/"EXPLORATEUR_INVESTIGATION_TOPOLOGY.json").read_text());return {"status":"COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN","pass_real":False,"authority":"EXPLORATEUR_INVESTIGATION_TOPOLOGY.json","anchors":len(d.get("clue_scene_anchors",[]))}
  return {"status":"UNKNOWN","pass_real":False,"authority":None}
