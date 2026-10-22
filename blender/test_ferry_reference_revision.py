import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];D=R/'assets/infrastructure/vehicles'
bpy.ops.wm.open_mainfile(filepath=str(D/'transit_vehicles.blend'))
root=bpy.data.objects['WaterTransitFerry'];objs=list(root.children_recursive)
ring=[o for o in objs if 'orange lifebuoy' in o.name]
pillar=[o for o in objs if 'structural pink diagonal' in o.name]
res={'result':'PASS','scope':'Actual source features plus exported GLB geometric checks; not hydrodynamic or rendered gameplay simulation.','lifebuoys':len(ring),'lifebuoy_white_face_counts':[sum(p.material_index==1 for p in o.data.polygons) for o in ring],'solid_diagonal_pillars':len(pillar)}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(R/'assets/web/water_transit_ferry.glb'))
vs=[];fs=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 o.data.calc_loop_triangles();offset=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles)
bvh=BVHTree.FromPolygons(vs,fs,all_triangles=True)
results=[]
for y in (0,-3.08,3.08):
 hit,norm,idx,dist=bvh.ray_cast(Vector((15,y,.35)),Vector((-1,0,0)),30)
 results.append({'lateral_y_blender_m':y,'hit':hit is not None,'hit_x':hit.x if hit is not None else None})
res['bow_underdeck_horizontal_ray_checks']=results;res['open_center_channel_and_two_pontoons']=not results[0]['hit'] and all(t['hit'] and 11<t['hit_x']<12 for t in results[1:])
res['train_sha256']=hashlib.sha256((R/'assets/web/coast_metro_train.glb').read_bytes()).hexdigest()
res['train_matches_current_manifest']=res['train_sha256']==json.loads((D/'coast_metro_train_manifest.json').read_text())['sha256']
if not(res['lifebuoys']==4 and res['solid_diagonal_pillars']==2 and all(x>0 for x in res['lifebuoy_white_face_counts']) and res['open_center_channel_and_two_pontoons'] and res['train_matches_current_manifest']):res['result']='FAIL'
(D/'ferry_reference_revision_validation.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
