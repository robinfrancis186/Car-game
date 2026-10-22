"""Representative static combined-pose mesh tests, not a dynamics/suspension simulation."""
import bpy,json,itertools
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];OUT=R/'assets/web'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(OUT/'car.glb'))
body=bpy.data.objects['CarBody'];base=body.matrix_world.copy();keys=['Front_Left','Front_Right','Rear_Left','Rear_Right']
def tree(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles();result=BVHTree.FromPolygons([e.matrix_world@v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True);e.to_mesh_clear();return result
wheels={}
for steer in [0,.4,-.4]:
 for key in keys:
  st=bpy.data.objects['Steer_'+key];st.rotation_mode='XYZ';st.rotation_euler.z=steer if key.startswith('Front') else 0
 bpy.context.view_layer.update();wheels[steer]={key:tree(bpy.data.objects['Wheel_'+key]) for key in keys}
report={'note':'Static sampled cosmetic chassis poses only. Does not prove continuous dynamic clearance, tire contact or engineering accuracy. Three Euler XYZ chassis rotation converted explicitly to Blender axes.','variants':{}}
for name,roll,pn,pp,heave in [('requested',.08,.055,.04,.018),('conservative',.006,.004,.004,.004),('balanced',.008,.005,.005,.004)]:
 results=[]
 for r,p,h in itertools.product([-roll,roll],[-pn,pp],[-heave,heave]):
  body.matrix_world=Matrix.Translation((0,0,h))@Matrix.Rotation(r,4,'X')@Matrix.Rotation(-p,4,'Y')@base;bpy.context.view_layer.update();bt=tree(body)
  for s in [0,.4,-.4]:
   contacts={key:len(bt.overlap(wheels[s][key])) for key in keys};results.append({'roll_x_three_rad':r,'pitch_z_three_rad':p,'body_y_offset_m':h,'steer_rad':s,'surface_overlap_pairs':contacts})
 report['variants'][name]={'roll_limit_rad':roll,'pitch_negative_limit_rad':pn,'pitch_positive_limit_rad':pp,'heave_limit_m':heave,'pose_count':len(results),'pass':all(not any(v['surface_overlap_pairs'].values()) for v in results),'worst_overlap_pairs':max(max(v['surface_overlap_pairs'].values()) for v in results),'poses':results}
(OUT/'car_cosmetic_pose_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:{i:v[i] for i in ['roll_limit_rad','pitch_negative_limit_rad','pitch_positive_limit_rad','heave_limit_m','pass','worst_overlap_pairs']} for k,v in report['variants'].items()},indent=2))
