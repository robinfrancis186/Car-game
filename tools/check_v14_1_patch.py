"""Verify that V14.1 changes only approved interface files over frozen V14."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
base=json.loads((R/'tests/ui_audit_v14_1/BASELINE.json').read_text())
allowed={'web/src/main.js','web/src/style.css'}
changes=[]
for row in base['files']:
 p=R/row['path']; assert p.is_file(),row['path']
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=row['sha256']:
  assert row['path'] in allowed,'Unapproved runtime change: '+row['path']
  changes.append({'path':row['path'],'before':row['sha256'],'after':h})
actual={str(p.relative_to(R)) for p in [R/'web/index.html']+[p for f in ['web/src','web/public'] for p in (R/f).rglob('*') if p.is_file()]}
assert actual=={r['path'] for r in base['files']},'Runtime file inventory changed'
main=(R/'web/src/main.js').read_text()
old='NEED ${(cost-profile.credits).toLocaleString()}'
new='${(cost-profile.credits).toLocaleString()} more coins'
assert main.count(new)==1,'Expected one precise shortage-copy change'
normalized=main.replace(new,old)
assert hashlib.sha256(normalized.encode()).hexdigest()==next(r['sha256'] for r in base['files'] if r['path']=='web/src/main.js'),'Controller changed beyond shortage copy'
report={'result':'PASS','base':base['base'],'changes':changes,'unchanged_runtime_files':len(base['files'])-len(changes),'controller_scope':'Only the shortage-copy literal differs; all other controller bytes are identical.'}
(R/'tests/ui_audit_v14_1/patch_scope.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
