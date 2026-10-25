"""Self-contained unpublished R3.1 CSS-only patch checkpoint; no publish side effects."""
from pathlib import Path
import hashlib,json,zipfile,datetime
R=Path(__file__).resolve().parents[1];O=R.parent/'kerala_racing_recovery/checkpoints';O.mkdir(exist_ok=True,parents=True)
H=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((R/'tests/v17/r3-1/FINAL_RELEASE.json').read_text())
assert m['candidate']=='MALABAR V17 R3.1 target-size patch'
for x in m['runtime_files']:assert H((R/x['path']).read_bytes())==x['sha256'],'Runtime drift: '+x['path']
for p,x in m['anchors'].items():assert H((R/p).read_bytes())==x['sha256'],'Anchor drift: '+p
private=set()
for d in ['ui_references','ui_references_latest','ui_reference_inspection_r3','current_ui_feedback']:
 for p in (R.parent/d).glob('*'):
  if p.is_file():private.add(H(p.read_bytes()))
files=[]
for folder in ['web','assets','blender','tools','tests','docs','references/route']:
 for p in sorted((R/folder).rglob('*')):
  rel=p.relative_to(R).as_posix()
  if not p.is_file() or 'node_modules' in p.parts or '__pycache__' in p.parts or p.name.startswith('.') or p.name.endswith('.blend1'):continue
  if rel.startswith('assets/surface_test/proof/'):continue
  if any(rel.startswith('tools/scene-proof-r3/'+v+'/') for v in ['proof-v1','proof-final']):continue
  if p.suffix=='.blend' and any(s in p.name.lower() for s in ['preview','runtime_roundtrip','helper_smoke']):continue
  if 'early_v12_ui' in p.name or p.name=='full_checkpoint_receipt.json':continue
  files.append(p)
files += [R/x for x in ['README.md','LICENSES.md','STATUS.md','design-qa.md']]
rows=[];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=O/f'malabar-v17-r3-1-unpublished-full-{stamp}.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:
  b=p.read_bytes();rel=p.relative_to(R).as_posix();sha=H(b);assert sha not in private,rel
  z.writestr(rel,b);rows.append({'path':rel,'bytes':len(b),'sha256':sha})
 z.writestr('FULL_BACKUP_MANIFEST.json',json.dumps({'kind':'Complete unpublished V17 R3.1 CSS-only patch original source','current_release_manifest':'tests/v17/r3-1/FINAL_RELEASE.json','status':'Source-tested only; R3.1 rendered target dimensions/header spacing pending. R3 actual CSS screenshot evidence is baseline, not this patch. Full WebGL/native/reference-photo acceptance not achieved. Not publication authorization.','runtime_tree_sha256':m['runtime_tree_sha256'],'private_user_reference_images_included':False,'baseline_provenance':'tests/v17/CANDIDATE_MANIFEST.json and docs/provenance/r3-baseline preserve R3 metadata. Only current FINAL_RELEASE.json anchors this patch.','dependencies':'npm ci --ignore-scripts from pinned web/package-lock.json; vendored runtime dependencies/assets included.','generated_dist_omitted':'Reproduce via npm run build; current expected SHA in FINAL_RELEASE.json.','files':rows},indent=2))
assert all(H((R/x['path']).read_bytes())==x['sha256'] for x in rows),'Source changed during capture'
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for x in rows:assert H(z.read(x['path']))==x['sha256']
receipt={'path':str(out),'bytes':out.stat().st_size,'sha256':H(out.read_bytes()),'files':len(rows),'runtime_files':len(m['runtime_files']),'runtime_tree_sha256':m['runtime_tree_sha256'],'stable_during_capture':True,'archive_crc_and_all_file_hashes_verified':True,'private_reference_originals_and_inspection_copies_absent':True,'restore':'Extract empty directory; npm ci --ignore-scripts in web; npm test; npm run build. No earlier source backup needed. See current FINAL_RELEASE and R3.1 acceptance gates.'}
out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
