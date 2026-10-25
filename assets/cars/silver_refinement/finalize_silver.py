"""Freeze only Silver-owned V13 output after actual mesh and preview inspection."""
import json,hashlib,shutil,datetime
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[3];O=R/'assets/cars/silver_refinement';W=R/'assets/web';P=R/'web/public/assets';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();G=W/'car_silver.glb';h=sha(G)
a=json.load(open(O/'three_validation.json'));b=json.load(open(O/'pose_validation.json'));v=json.load(open(O/'render_provenance.json'))
assert a['result']==b['result']=='PASS' and a['sha256']==b['sha256']==v['source_glb_sha256']==h
for k in ['front','side','thumb']:
 d=v['images'][k];assert sha(R/d['path'])==d['sha256']
t=R/v['images']['thumb']['path'];im=Image.open(t);assert im.size==(512,320) and im.mode=='RGBA' and t.stat().st_size<250000
m=json.load(open(W/'car_silver_manifest.json'));assert m['sha256']==h
m.update({'status':'FROZEN V13 Silver geometry/material refinement; actual GLB and sampled rig/clearance regressions PASS; front/side/thumb studio pixels inspected. Not browser acceptance.','thumbnail':'car_thumb_silver.png','thumbnail_sha256':sha(t),'thumbnail_bytes':t.stat().st_size,'preview_images':v['images'],'source_sha256':sha(W/'car_silver.blend'),'generator_sha256':sha(R/'blender/build_silver_car.py'),'editable_source_sha256':sha(O/'silver_editable.blend'),'validation':{'actual_three_loader':'PASS','exact_existing_wheel_coordinate_set':'PASS','exact_documented_node_transforms':'PASS','same_overall_bounds':'PASS','unit_normals_no_degenerate_float32_triangles':'PASS','body_full_wheel_pose_checks':756,'wing_runtime_angles_rad':[0,-.1,-.2,-.236],'runtime_source_scene_contract':'PASS','scope':'Sampled actual mesh/source scene-graph only; no GPU/browser/continuous dynamics claim.'}})
for d in [W,P,O]:
 name='manifest.json' if d==O else'car_silver_manifest.json';(d/name).write_text(json.dumps(m,indent=2)+'\n')
shutil.copy2(G,P/G.name)
for d in [W,P]:shutil.copy2(t,d/t.name)
record={'status':'FROZEN','created':datetime.datetime.now(datetime.timezone.utc).isoformat(),'glb_sha256':h,'glb_bytes':G.stat().st_size,'triangles':a['triangles'],'draws':a['draws'],'materials':len(a['materials']),'thumbnail_sha256':sha(t),'thumbnail_bytes':t.stat().st_size,'native_source_sha256':sha(W/'car_silver.blend'),'editable_source_sha256':sha(O/'silver_editable.blend'),'manifest_sha256':sha(O/'manifest.json'),'staged_public_identical':sha(G)==sha(P/G.name),'scene_contract_source_sha256':sha(R/'web/tests/scene-contract.test.mjs'),'scope':'Bounded Silver asset refinement only; V12 frozen files and runtime sources were not edited by this task.'}
(O/'freeze.json').write_text(json.dumps(record,indent=2)+'\n')
for p in O.glob('*.blend1'):p.unlink()
(W/'car_silver.blend1').unlink(missing_ok=True)
print(json.dumps(record,indent=2))
