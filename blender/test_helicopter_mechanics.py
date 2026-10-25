"""Sampled actual-GLB rotor/pod clearance, not engineering certification."""
import bpy,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'assets/helicopter'
def meshes(group):return [o for o in [group]+list(group.children_recursive)if o.type=='MESH']
def tree(objects,predicate=None):
 vs=[];fs=[];bpy.context.view_layer.update()
 for o in objects:
  dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();off=len(vs);vs.extend(o.matrix_world@v.co for v in me.vertices)
  for t in me.loop_triangles:
   ma=me.materials[t.material_index]
   if not predicate or predicate(ma.name):fs.append(tuple(off+i for i in t.vertices))
  ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs,all_triangles=True,epsilon=0)
for key in os.environ.get('HELI_VARIANTS','civilian,police').split(','):
 bpy.ops.wm.read_factory_settings(use_empty=True);file=R/'assets/web'/('helicopter_'+key+'.glb');bpy.ops.import_scene.gltf(filepath=str(file));body=bpy.data.objects['Airframe'];main=bpy.data.objects['MainRotor'];tail=bpy.data.objects['TailRotor'];yaw=bpy.data.objects['SearchlightYaw'];pitch=bpy.data.objects['SearchlightPitch'];yaw.rotation_mode='XYZ';pitch.rotation_mode='XYZ';fixed=tree(meshes(body));checks=[]
 for tag,node,axis in [('main',main,'Z'),('tail',tail,'Y')]:
  for degree in range(0,360,5):
   node.rotation_mode='XYZ';node.rotation_euler=(0,0,0);node.rotation_euler['XYZ'.index(axis)]=math.radians(degree);bpy.context.view_layer.update();moving=tree(meshes(node),lambda n:'graphite composite'in n);hits=moving.overlap(fixed);checks.append({'rotor':tag,'degrees':degree,'intersection_pairs':len(hits)})
  node.rotation_euler=(0,0,0)
 # Test articulated optical pod against solid skin/glazing, excluding intended mount bearing.
 shell=tree(meshes(body),lambda n:'airframe'in n or 'navy'in n or 'petrol teal'in n or 'canopy'in n);pod=[]
 for ya in[-math.pi,-math.pi/2,0,math.pi/2,math.pi]:
  for angle in[-.7,-.5,0,.5,.7]:
   yaw.rotation_euler.z=ya;pitch.rotation_euler.y=-angle;bpy.context.view_layer.update();hits=tree(meshes(pitch)).overlap(shell);pod.append({'yaw_rad':ya,'forward_pitch_rad':angle,'intersection_pairs':len(hits)})
 yaw.rotation_euler=(0,0,0);pitch.rotation_euler=(0,0,0)
 report={'result':'PASS'if all(q['intersection_pairs']==0 for q in checks+pod)else'FAIL','source_glb_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'rotor_samples':len(checks),'rotor_checks':checks,'pod_samples':len(pod),'pod_checks':pod,'scope':'Actual GLB reimport: composite blades versus entire fixed airframe every5degrees. Main metallic bearing/hub intentional attachment excluded. Pod25discrete yaw/pitch combinations versus skin/glazing; gimbal bearing attachment excluded. Not continuous or flightworthy engineering proof.'};(O/key/'mechanics_validation.json').write_text(json.dumps(report,indent=2));print('MECHANICS_RESULT',key,report['result'],[(q)for q in checks+pod if q['intersection_pairs']],flush=True)
