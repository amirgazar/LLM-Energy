"""Scan release files without printing credentials or personal values."""
from pathlib import Path
import re,json
root=Path(__file__).parent
patterns=[re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"),re.compile(r"(?i)(?:api_key|access_token|password)\s*[:=]\s*[\"'](?!YOUR_|EXAMPLE|test|dummy)[A-Za-z0-9_+/=-]{20,}[\"']")]
issues=[]
def walk(x,path):
 if isinstance(x,dict):
  if any(k.lower() in {'email','responseid','ipaddress','dob','date_of_birth','firstname','lastname','contact','profile_index'} for k in x):issues.append(str(path.relative_to(root))+': identifying record fields')
  for v in x.values():walk(v,path)
 elif isinstance(x,list):
  for v in x:walk(v,path)
for p in root.rglob('*'):
 if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
 if p.suffix in {'.png','.jpg','.pdf'}:continue
 t=p.read_text(errors='replace')
 if any(rx.search(t) for rx in patterns):issues.append(str(p.relative_to(root))+': possible credential')
 if p.suffix=='.json':walk(json.loads(t),p)
print('Release scan: '+('PASS' if not issues else 'REVIEW REQUIRED'))
for x in sorted(set(issues)):print(x)
raise SystemExit(bool(issues))
