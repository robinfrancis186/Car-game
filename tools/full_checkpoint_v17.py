"""Full self-contained original-source checkpoint, explicitly unpublished."""
from pathlib import Path
import hashlib,json,zipfile,datetime
R=Path(__file__).resolve().parents[1];O=R.parent/'kerala_racing_recovery/checkpoints';O.mkdir(exist_ok=True,parents=True)
candidate=json.loads((R/'tests/v17/CANDIDATE_MANIFEST.json').read_text());assert candidate['candidate']=='MALABAR V17 UI CANDIDATE R3','Freeze R3 first'
for row in candidate['runtime_files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256'],'Runtime changed after freeze: '+row['path']
for rel,row in candidate['anchors'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==row['sha256'],'Anchor changed after freeze: '+rel
private={'78186c597582de327dee7a4f25b1884765dac262fccfe32289c85c07c37eed3b','82421f0f9de3a5cda88e7ff4f0574f3736cd4331476e7742630b6abafc3b7c97','c9165be11338a88e5aa90be971dfb7734c1502ac4a8d382f70f6bbd04a63ff5d','e8498e0070256a7dcedc110f2c8118e16c2649d246015a1ed378524112d0ef1d'}
# Also exclude all known locally derived inspection copies, not only uploaded hashes.
for d in [R.parent/'ui_references',R.parent/'ui_references_latest',R.parent/'ui_reference_inspection_r3',R.parent/'current_ui_feedback']:
 for p in d.glob('*'):
  if p.is_file():private.add(hashlib.sha256(p.read_bytes()).hexdigest())
for p in Path('/tmp').glob('ui_ref*.jpg'):private.add(hashlib.sha256(p.read_bytes()).hexdigest())
files=[]
for folder in ['web','assets','blender','tools','tests','docs','references/route']:
 for p in sorted((R/folder).rglob('*')):
  if p.relative_to(R).as_posix().startswith('assets/surface_test/proof/'):continue
  if any(p.relative_to(R).as_posix().startswith('tools/scene-proof-r3/'+v+'/') for v in ['proof-v1','proof-final']):continue # superseded generated proofs; editable source/corrected proof retained
  if not p.is_file()or'node_modules'in p.parts or'__pycache__'in p.parts or p.name.startswith('.')or p.name.endswith('.blend1'):continue
  if p.suffix=='.blend'and any(s in p.name.lower()for s in ['preview','runtime_roundtrip','helper_smoke']):continue
  if 'early_v12_ui'in p.name or p.name=='full_checkpoint_receipt.json':continue
  files.append(p)
files += [R/x for x in ['README.md','LICENSES.md','STATUS.md','design-qa.md']]
rows=[];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=O/f'malabar-v17-ui-r3-unpublished-full-{stamp}.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:
  b=p.read_bytes();rel=p.relative_to(R).as_posix();sha=hashlib.sha256(b).hexdigest();assert sha not in private,rel;assert not rel.startswith('references/')or rel.startswith('references/route/');z.writestr(rel,b);rows.append({'path':rel,'bytes':len(b),'sha256':sha})
 z.writestr('FULL_BACKUP_MANIFEST.json',json.dumps({'kind':'Complete unpublished V17 R3 UI original-source checkpoint','status':'Not fully visually accepted. R3 DOM/CSS and original-scene work are isolated; actual WebGL scene/native FPS remain unaccepted. See design-qa.md for exact rendered evidence and limits. Not publication authorization.','private_user_reference_images_included':False,'dependencies':'npm ci --ignore-scripts from pinned web/package-lock.json; vendored runtime Three/font files included','generated_dist_omitted':'Reproduce via npm run build; frozen expected hash in tests/v17/CANDIDATE_MANIFEST.json','files':rows},indent=2))
assert all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256']for x in rows),'Source changed during capture'
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 for x in rows:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
receipt={'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':len(rows),'stable_during_capture':True,'archive_crc_and_all_file_hashes_verified':True,'private_reference_originals_and_inspection_copies_absent':True,'restore':'Extract into an empty directory; npm ci --ignore-scripts in web; npm run build. Source is self-contained; no earlier backup needed. Browser visual approval still required.'}
out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
