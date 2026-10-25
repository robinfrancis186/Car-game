"""Protect the frozen simulation, economy, storage, renderer and assets during V14 UI work."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];manifest=json.loads((R/'tests/ui_audit_v14/protected_v13_manifest.json').read_text());bad=[]
for item in manifest['files']:
 p=R/item['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest()if p.exists()else None
 if actual!=item['sha256']:bad.append({'path':item['path'],'expected':item['sha256'],'actual':actual})
assert not bad,json.dumps(bad,indent=2)
print(f"PASS {len(manifest['files'])} protected V13 files exact; main.js presentation changes require independent controller review.")
