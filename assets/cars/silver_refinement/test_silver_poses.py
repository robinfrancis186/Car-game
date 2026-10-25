"""Actual V13 Silver exported-mesh regression; sampled, not engineering certification."""
import bpy,json,itertools,hashlib,math
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[3];O=R/'assets/cars/silver_refinement';P=R/'assets/web/car_silver.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P));body=bpy.data.objects['CarBody'];base=body.matrix_world.copy();keys=['Front_Left','Front_Right','Rear_Left','Rear_Right']
def tree(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return t
angles=[-.4,-.2666666667,-.1333333333,0,.1333333333,.2666666667,.4];wheels={}
for a in angles:
 for k in keys:st=bpy.data.objects['Steer_'+k];st.rotation_mode='XYZ';st.rotation_euler.z=a if k.startswith('Front')else 0
 bpy.context.view_layer.update();wheels[a]={k:tree(bpy.data.objects['Wheel_'+k]) for k in keys}
failures=[];checks=0
for roll,pitch,heave in itertools.product([-.008,0,.008],[-.005,0,.005],[-.002,0,.002]):
 body.matrix_world=Matrix.Translation((0,0,heave))@Matrix.Rotation(roll,4,'X')@Matrix.Rotation(-pitch,4,'Y')@base;bpy.context.view_layer.update();bt=tree(body)
 for a in angles:
  for k in keys:
   n=len(bt.overlap(wheels[a][k]));checks+=1
   if n:failures.append({'roll':roll,'pitch':pitch,'heave':heave,'steer':a,'wheel':k,'surface_overlap_pairs':n})
body.matrix_world=base;bpy.context.view_layer.update();bt=tree(body);wing=bpy.data.objects['AeroWing'];hinge=bpy.data.objects['AeroWing_Hinge'];hinge.rotation_mode='XYZ';wing_checks=[]
for a in [0,.1,.2,.236]:
 hinge.rotation_euler.y=a;bpy.context.view_layer.update();n=len(bt.overlap(tree(wing)));wing_checks.append({'runtime_three_z_rad':-a,'body_overlap_pairs':n})
result={'result':'PASS'if not failures and not any(x['body_overlap_pairs']for x in wing_checks)else'FAIL','sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'whole_wheel_body_checks':checks,'failed_checks':len(failures),'failures':failures,'active_wing_checks':wing_checks,'scope':'Actual exported body versus full wheel meshes, 27 body cosmetic poses and seven steering samples per wheel; fixed wheels. Discrete surface tests, not continuous dynamics/engineering proof.'}
(O/'pose_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
