"""Local original-work checkpoint; no network or reference-photo inclusion."""
from pathlib import Path
import hashlib,json,zipfile,datetime
R=Path(__file__).resolve().parents[1];BASE=R.parent/'kerala_racing_recovery/sites19_v11_1/web';V10=R.parent/'kerala_racing_recovery/github_main_checkout';out=R.parent/'kerala_racing_recovery/checkpoints';out.mkdir(exist_ok=True)
files={};changed=[]
def add(p):
 rel=p.relative_to(R).as_posix();b=p.read_bytes();files[rel]=b;changed.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
for p in sorted((R/'web').rglob('*')):
 if not p.is_file()or'node_modules'in p.parts or p.name.startswith('.'):continue
 if p.suffix in {'.log'}:continue
 base=BASE/p.relative_to(R/'web')
 if not base.exists()or base.read_bytes()!=p.read_bytes():add(p)
for p in sorted((R/'blender').glob('*.py')):
 base=V10/'blender'/p.name
 if not base.exists()or base.read_bytes()!=p.read_bytes():add(p)
for p in sorted((R/'assets').rglob('*')):
 if not p.is_file()or any(s in p.name.lower()for s in ['preview','runtime_roundtrip','helper_smoke','render_']):continue
 if p.suffix not in{'.blend','.glb','.png','.json','.md','.txt'}:continue
 base=V10/p.relative_to(R)
 if not base.exists()or base.read_bytes()!=p.read_bytes():add(p)
for rel in ['README.md','LICENSES.md','STATUS.md','tools/correct_original_license.py','tools/refine_v10_discovery.mjs','tools/audit_runtime_payload.py','tools/audit_native_metadata.py','tools/checkpoint_reconstruction.py']:
 add(R/rel)
for p in sorted((R/'tests/recovery').glob('*.json')):add(p)
for p in sorted((R/'tests/independent_rebuild_asset_audit').glob('*')):
 if p.is_file() and p.suffix in {'.json','.md','.mjs'}:add(p)
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'Intermediate reconstruction checkpoint, NOT release or acceptance. Apply over exact Sites19 web plus GitHub V10 source assets. All changed files are captured by bytes, not symlink.','base_sites_commit':'0a5f07447719117a0084cffb9a525a1cd1e54ea3','base_github_commit':'cac90470ea1ff3429a77f7d752a958e1e1dc1f6c','private_inputs_included':False,'files':changed}
# Never leak private user images, environment credentials or historical private paths.
assert not any(p.startswith('references/')or'node_modules/'in p or'.git/'in p for p in files)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');dest=out/f'malabar-reconstruction-{stamp}.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for rel,b in files.items():z.writestr(rel,b)
 z.writestr('CHECKPOINT_MANIFEST.json',json.dumps(manifest,indent=2))
receipt={'path':str(dest),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(files),'stable_during_capture':all((R/x['path']).read_bytes()==files[x['path']]for x in changed)};dest.with_suffix('.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
