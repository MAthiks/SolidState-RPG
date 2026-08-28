import re
class SourceRoleMarkerDetector:
 START_PATTERNS=(r"\bintroduction\b",r"\bacte\s+i\s*:",r"\bl[’']enquête commence\b",r"\bcommencez\b")
 TERMINAL_PATTERNS=(r"\bconclusion\b",r"\bépilogue\b",r"\bs[’']achève\b",r"\bfin de l['’]histoire\b",r"\bfin idéale\b")
 @staticmethod
 def scan(text):
  out={"start_markers":[],"terminal_markers":[]}
  for i,line in enumerate(text.splitlines(),1):
   s=line.strip()
   if not s: continue
   if any(re.search(p,s,re.I) for p in SourceRoleMarkerDetector.START_PATTERNS):out["start_markers"].append({"line":i,"text":s})
   if any(re.search(p,s,re.I) for p in SourceRoleMarkerDetector.TERMINAL_PATTERNS):out["terminal_markers"].append({"line":i,"text":s})
  return out
