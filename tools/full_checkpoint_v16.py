"""Complete private backup of original project source; excludes private reference images/caches."""
from pathlib import Path
import hashlib,json,zipfile,datetime
R=Path(__file__).resolve().parents[1];O=R.parent/'kerala_racing_recovery/checkpoints';O.mkdir(exist_ok=True);files=[]
for folder in ['web','assets','blender','tools','tests','docs','references/route']:
 for p in sorted((R/folder).rglob('*')):
  if p.relative_to(R).as_posix().startswith('assets/surface_test/proof/'):continue
  if not p.is_file()or'node_modules'in p.parts or'__pycache__'in p.parts or p.name.startswith('.')or p.name.endswith('.blend1'):continue
  if p.suffix=='.blend'and any(s in p.name.lower()for s in ['preview','runtime_roundtrip','helper_smoke']):continue
  if 'early_v12_ui' in p.name or p.name=='full_checkpoint_receipt.json':continue
  files.append(p)
files += [R/x for x in ['README.md','LICENSES.md','STATUS.md']]
rows=[];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=O/f'malabar-v16-full-{stamp}.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:
  b=p.read_bytes();rel=p.relative_to(R).as_posix();assert not rel.startswith('references/')or rel.startswith('references/route/');z.writestr(rel,b);rows.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 z.writestr('FULL_BACKUP_MANIFEST.json',json.dumps({'kind':'Complete V16 original-project source backup, not public publication authorization','private_user_reference_images_included':False,'dependencies':'npm ci --ignore-scripts from pinned web/package-lock.json; vendored runtime Three/font files are included','derived_preview_omitted':'The optional staged car-on-wall proof renders are reproducible preview derivatives, not runtime or native route source. The exact original route source and its four frozen QA previews are included.','generated_dist_omitted':'Reproduce via npm run build; frozen expected standalone hash in tests/release/V16_RELEASE.json','files':rows},indent=2))
stable=all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256']for x in rows);assert stable
parts=[];size=24*1024*1024
with out.open('rb')as f:
 i=1
 while b:=f.read(size):
  p=out.with_name(out.name+f'.part{i:02d}');p.write_bytes(b);parts.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});i+=1
receipt={'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(rows),'stable_during_capture':stable,'parts':parts,'restore':'Concatenate .part01, .part02, ... in order to reconstruct ZIP; verify ZIP SHA256; extract into an empty directory. No previous baseline needed.'};out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
