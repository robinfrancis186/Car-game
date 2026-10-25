import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'assets/cars/midnight';F=R/'assets/web/car_midnight.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(F));bpy.context.view_layer.update();rows=[]
for k in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
 wh=bpy.data.objects['Wheel_'+k];ca=bpy.data.objects['Caliper_'+k];wh.data.calc_loop_triangles();vs=[wh.matrix_world@v.co for v in wh.data.vertices];fs=[tuple(t.vertices)for t in wh.data.loop_triangles if'alloy'in wh.data.materials[t.material_index].name.lower()];cv=[ca.matrix_world@v.co for v in ca.data.vertices];hub=bpy.data.objects['Steer_'+k].matrix_world.translation;minimum=999;when=None
 for deg in range(0,361,12):
  xf=Matrix.Translation(hub)@Matrix.Rotation(math.radians(deg),4,'Y')@Matrix.Translation(-hub);bt=BVHTree.FromPolygons([xf@v for v in vs],fs,all_triangles=True)
  dist=min(bt.find_nearest(v)[3]for v in cv)
  if dist<minimum:minimum=dist;when=deg
 rows.append({'wheel':k,'minimum_sampled_caliper_vertex_to_alloy_m':minimum,'spin_degrees_at_minimum':when,'sampled_spins':31,'sampled_caliper_vertices':len(cv)})
r={'result':'PASS'if all(x['minimum_sampled_caliper_vertex_to_alloy_m']>.002 for x in rows)else'FAIL','source_glb_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'checks':rows,'scope':'Caliper vertex distances to actual wheel alloy/rotor triangle surfaces at12degree intervals, separate from4degree triangle intersection test. Not continuous exact mechanical clearance.'};(O/'brake_distance_validation.json').write_text(json.dumps(r,indent=2));print('BRAKE_DISTANCE',r,flush=True)
