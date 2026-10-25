"""Freeze an inspected reconstruction only after matching fresh validation evidence."""
from pathlib import Path
import json,hashlib,shutil,sys,struct
ROOT=Path(__file__).resolve().parents[1];key=sys.argv[1];OUT=ROOT/'assets/cars'/key;WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();file=WEB/f'car_{key}.glb';m=json.loads((OUT/'manifest.json').read_text());hs=sha(file);assert m['sha256']==hs
reports={}
for name in ['pose_validation','brake_validation','source_validation','wing_validation','three_validation']:
 r=json.loads((OUT/(name+'.json')).read_text());assert r['result']=='PASS',(name,r['result']);assert r.get('sha256',hs)==hs;reports[name]=r
native=ROOT/m['source'];assert reports['source_validation']['source_sha256']==sha(native)
render=json.loads((OUT/'render_provenance.json').read_text());assert render['source_glb_sha256']==hs
for tag in ['front','rear','thumb']:
 d=render['images'][tag];assert sha(ROOT/d['path'])==d['sha256']
thumb=ROOT/'assets/gallery_thumbnails'/f'car_thumb_{key}.png';raw=thumb.read_bytes();assert struct.unpack('>II',raw[16:24])==(512,320);assert raw[25]==6;assert len(raw)<240000
m.update(status='FROZEN reconstructed asset: source/actual GLB/sampled clearances validated; studio previews visually inspected. Not gameplay certification.',max_visual_steer_rad=.45,source_sha256=sha(native),thumbnail=thumb.name,thumbnail_sha256=sha(thumb),thumbnail_bytes=len(raw),dimensions_three_m=reports['three_validation']['bounds']['size'],cockpit_camera_suggested_three_m=[-.28,1,.325],validation={'actual_three_loader':'PASS','nondegenerate_finite_geometry':'PASS','body_tire_samples':reports['pose_validation']['checks'],'brake_rotor_samples':reports['brake_validation']['checks'],'editable_native_mesh_parts':reports['source_validation']['editable_mesh_parts'],'fixed_wing_rest':'PASS','scope':'Sampled actual exported mesh and editable source checks; not continuous collision proof or browser gameplay.'},preview_images=render['images'])
m['limitations']=['Fresh reconstruction after source loss, not recovery of previous V12 source bytes or old hashes.','Original stylized interpretation, not licensed manufacturer CAD or exact branded replica.','No image textures, brand emblems or photographic pixels embedded.','Common game collider remains an arcade approximation; manifest gives actual mirror-inclusive bounds.','Cosmetic body motion was tested only at roll±.008rad,pitch±.005rad,heave±.002m with wheel steering±.45rad.','RearWing is fixed; do not animate it as AeroWing_Hinge.','Cockpit-camera appearance and runtime behavior require parent integration/rendered testing.']
if key=='vermilion':
 d=json.loads((OUT/'door_validation.json').read_text());assert d['sha256']==hs;pose=[c for c in d['checks']if abs(c['angle_rad']-1.10)<1e-6];assert len(pose)==2 and all(c['intersection_pairs']==0 for c in pose)
 m['door_opening_status']='Optional static open display pose only:100mm outward offset then1.10rad about declared native axis clears. Intermediate translation/opening path has body contacts; no continuous animation or gameplay mechanism validated. Keep runtime doors closed.'
 m['door_display_pose']={'outward_offset_m':.10,'angle_rad':1.10,'endpoint_clearance':'PASS','continuous_path_clearance':'FAIL / unsupported'};m['limitations'].append(m['door_opening_status'])
for p in(OUT/'manifest.json',WEB/f'car_{key}_manifest.json'):p.write_text(json.dumps(m,indent=2))
for p in(WEB,PUBLIC):shutil.copy2(thumb,p/thumb.name)
shutil.copy2(file,PUBLIC/file.name)
for p in OUT.glob('*.blend1'):p.unlink()
print(json.dumps({'asset':key,'status':'FROZEN','sha256':hs,'triangles':m['triangles'],'draws':m['draw_calls'],'materials':m['materials'],'native_parts':m['validation']['editable_native_mesh_parts'],'thumbnail_sha256':m['thumbnail_sha256'],'thumbnail_bytes':len(raw)},indent=2))
