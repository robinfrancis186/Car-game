import bpy,json,hashlib,math,os
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[3];P=R/'assets/web/car_vermilion.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P))
def geom(obs):
 v=[];f=[];names=[]
 for o in obs:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();off=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices)
  for t in o.data.loop_triangles:f.append(tuple(off+i for i in t.vertices));names.append(o.name)
 return BVHTree.FromPolygons(v,f,all_triangles=True),names
checks=[];travel=float(os.environ.get('DOOR_PRETRAVEL','.04'))
for name,s in [('Left',1),('Right',-1)]:
 hinge=bpy.data.objects['DoorHinge_'+name];door=bpy.data.objects['Door_'+name];orig=hinge.location.copy();parts=[door,*door.children_recursive];fixed=[o for o in bpy.data.objects if o.type=='MESH'and o not in parts];bpy.context.view_layer.update();ft,fl=geom(fixed)
 for angle in(0,.10,.25,.45,.65,.85,1.10):
  hinge.location=orig+Vector((0,s*travel,0));hinge.rotation_mode='QUATERNION';hinge.rotation_quaternion=Quaternion(Vector((-s*.45,1,0)).normalized(),angle);bpy.context.view_layer.update();dt,dl=geom(parts);ov=ft.overlap(dt);checks.append({'door':name,'outward_pretravel_m':travel,'angle_rad':angle,'intersection_pairs':len(ov),'parts':list(set(fl[i]+' <-> '+dl[j]for i,j in ov))})
 hinge.location=orig;hinge.rotation_quaternion=Quaternion();bpy.context.view_layer.update()
r={'result':'PASS'if not any(c['intersection_pairs']for c in checks)else'FAIL','sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'checks':checks,'scope':'Actual GLB display opening after declared outward translation, seven sampled angles through1.10rad, versus all fixed car components. Closed seal seating excluded. Not an engineered mechanism or gameplay implementation.'};(Path(__file__).parent/'door_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
