"""Assert final original surface-course asset evidence and record immutable hashes."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[1];W=R/'assets/web';P=R/'web/public/assets'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
m=read(O/'manifest.json');qa=read(O/'glb_validation.json');native=read(O/'native_validation.json');old=read(O/'unchanged_existing_worlds.json')
assert qa['result']==native['result']==old['result']=='PASS'
assert sha(R/m['native'])==native['native_sha256']
canonical=R/'docs/v16/surface_profile.json';assert sha(canonical)==m['canonical_profile_sha256']==qa['canonical_profile_sha256']
copies=[]
for a in m['assets']:
 assert sha(W/a['file'])==a['sha256']==sha(P/a['file'])
 copies += [W/a['file'],P/a['file']]
for name in ('course_runtime_surface_test.json','surface_test_profile.json','surface_test_furniture_colliders.json','surface_test_colliders.json'):
 assert (O/name).read_bytes()==(W/name).read_bytes()==(P/name).read_bytes()
 copies += [O/name,W/name,P/name]
assert read(O/'surface_test_profile.json')==read(canonical)==read(O/'course_runtime_surface_test.json')['surface_profile']
previews=[]
for mode in ('overview','bank_entry','wall_hold','runout'):
 proof=read(O/f'preview_{mode}_provenance.json');assert sha(R/proof['image'])==proof['sha256'];assert proof['samples']==48 and not proof['denoising']
 for a in m['assets']:assert proof['source_glb_sha256'][a['file']]==a['sha256']
 previews.append(proof)
files=[p for p in O.rglob('*')if p.is_file()and p.name!='freeze.json'and p.suffix not in('.blend1','.pyc')]
files += copies+[canonical]+[R/'blender'/n for n in('build_surface_test_route.py','render_surface_test_route.py','test_surface_test_native.py','rebuild_car_helpers.py')]
report={'status':'ASSET_FREEZE_PASS','date':'2026-10-23','scope':'Original isolated course assets/native and measured geometry QA. Runtime gameplay, WebGL, chase camera and solo end-to-end acceptance remain separate.','course_id':'surface-test','canonical_profile_id':'harbour-wall-run','triangles':qa['triangles'],'draws':qa['draws'],'max_measured_contact_error_m':qa['rays']['max_contact_distance_m'],'max_measured_geometric_normal_error_degrees':qa['rays']['max_geometric_normal_error_degrees'],'rays':qa['rays']['samples'],'structural_intrusions':qa['rays']['structural_intrusions'],'visual_review':'All four final actual-GLB Blender previews inspected; removed coarse underside penetration and fixed paint-to-road sampling. CPU48 samples, no denoise, not gameplay.','collision_limits':'Zero-thickness analytic driving ribbon, no closed underside; edge rails are non-solid guidance. Separate box proxies only for visible piers/signs.','previews':previews,'provenance':'Original project geometry/materials; reuse license not selected by owner. No source-video pixels, photo textures, logos or downloaded meshes.','hashes':{str(p.relative_to(R)):{'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(set(files))}}
(O/'freeze.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'triangles':qa['triangles'],'draws':qa['draws'],'hashed_files':len(report['hashes']),'previews':len(previews)}))
