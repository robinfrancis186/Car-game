"""Actual final-GLB sampled chassis poses including runtime maximum steering; not dynamic simulation."""
import bpy,json,itertools,hashlib
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];OUT=R/'assets/web';KEYS=['Front_Left','Front_Right','Rear_Left','Rear_Right'];STEERS=[0,.4,-.4,.57,-.57,.6,-.6]
def tree(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@v.co for v in me.vertices],[tuple(tr.vertices) for tr in me.loop_triangles],all_triangles=True);e.to_mesh_clear();return t
for variant in ['car','car_silver']:
 steer_angles=STEERS if variant=='car' else [0,.4,-.4] # Silver's validated mesh steering envelope, not the higher red/controller candidate.
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);path=OUT/(variant+'.glb');bpy.ops.import_scene.gltf(filepath=str(path))
 body=bpy.data.objects['CarBody'];base=body.matrix_world.copy();wheels={}
 for angle in steer_angles:
  for key in KEYS:
   st=bpy.data.objects['Steer_'+key];st.rotation_mode='XYZ';st.rotation_euler.z=angle if key.startswith('Front') else 0
  bpy.context.view_layer.update();wheels[angle]={key:tree(bpy.data.objects['Wheel_'+key]) for key in KEYS}
 checks=[]
 for roll,pitch,heave in itertools.product([-.008,0,.008],[-.005,0,.005],[-.002,0,.002]):
  body.matrix_world=Matrix.Translation((0,0,heave))@Matrix.Rotation(roll,4,'X')@Matrix.Rotation(-pitch,4,'Y')@base;bpy.context.view_layer.update();bt=tree(body)
  for steer in steer_angles:
   checks.append({'roll':roll,'pitch':pitch,'heave':heave,'steer':steer,'overlap_pairs':{key:len(bt.overlap(wheels[steer][key])) for key in KEYS}})
 failures=[c for c in checks if any(c['overlap_pairs'].values())]
 result={'result':'PASS' if not failures else 'FAIL','file':variant+'.glb','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'roll_limit_rad':.008,'pitch_limit_rad':.005,'heave_limit_m':.002,'steering_samples_rad':steer_angles,'pose_samples':len(checks),'wheel_body_checks':len(checks)*4,'failed_pose_count':len(failures),'failed_poses':failures,'note':'27 chassis pose combinations. Red includes runtime player maximum 0.57 rad and margin to 0.6; silver uses its supported +/-0.4 rad mesh limit. Larger silver angles failed the separately retained extended-steer negative test. Static surface-intersection tests only; no continuous suspension/dynamics claim.'}
 (OUT/(variant+'_common_pose_validation.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
