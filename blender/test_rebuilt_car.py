"""Actual exported-geometry sampled clearances, not continuous engineering proof."""
import bpy,json,itertools,hashlib,math,os
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];key=os.environ.get('CAR_ID','vermilion');OUT=ROOT/'assets/cars'/key;FILE=ROOT/'assets/web'/f'car_{key}.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(FILE));bpy.context.view_layer.update();sha=hashlib.sha256(FILE.read_bytes()).hexdigest();keys=('Front_Left','Front_Right','Rear_Left','Rear_Right')
def geom(obs,fn=None):
 v=[];f=[];labels=[]
 for o in obs:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();off=len(v);v.extend(o.matrix_world@p.co for p in o.data.vertices)
  for t in o.data.loop_triangles:
   if fn and not fn(o,t):continue
   f.append(tuple(off+i for i in t.vertices));labels.append(o.name+' / '+o.data.materials[t.material_index].name)
 return v,f,labels
def tree(v,f,xf=None):return BVHTree.FromPolygons([xf@p for p in v]if xf else v,f,all_triangles=True,epsilon=0)
body=bpy.data.objects['CarBody'];bv,bf,bl=geom([body,*body.children_recursive]);wd={}
for k in keys:wd[k]=geom([bpy.data.objects['Wheel_'+k]],lambda o,t:'Tire rubber' in o.data.materials[t.material_index].name)[:2]
checks=[];fails=[]
for roll,pitch,heave in itertools.product((-.008,0,.008),(-.005,0,.005),(-.002,0,.002)):
 xf=Matrix.Translation((0,0,heave))@Matrix.Rotation(pitch,4,'Y')@Matrix.Rotation(roll,4,'X');bt=tree(bv,bf,xf)
 for angle in(-.45,-.30,-.15,0,.15,.30,.45):
  for k,(v,f)in wd.items():
   hub=bpy.data.objects['Steer_'+k].matrix_world.translation;a=angle if k.startswith('Front')else 0;xf=Matrix.Translation(hub)@Matrix.Rotation(a,4,'Z')@Matrix.Translation(-hub);ov=bt.overlap(tree(v,f,xf));c={'roll':roll,'pitch':pitch,'heave':heave,'steer':a,'wheel':k,'pairs':len(ov)};checks.append(c)
   if ov:c['parts']={n:sum(bl[i]==n for i,j in ov)for n in set(bl[i]for i,j in ov)};fails.append(c)
r={'result':'PASS'if not fails else'FAIL','sha256':sha,'checks':len(checks),'body_poses':27,'max_steer_rad':.45,'failed_checks':len(fails),'failures':fails,'scope':'Sampled actual GLB tires versus all closed body/hood/doors/wing at combined cosmetic poses. Not continuous proof.'};(OUT/'pose_validation.json').write_text(json.dumps(r,indent=2));print('BODY_POSES',key,r['result'],len(fails),flush=True)
br=[]
for k in keys:
 wh=bpy.data.objects['Wheel_'+k];cal=bpy.data.objects['Caliper_'+k];v,f,l=geom([wh],lambda o,t:'alloy' in o.data.materials[t.material_index].name.lower());cv,cf,cl=geom([cal]);cb=tree(cv,cf);hub=bpy.data.objects['Steer_'+k].matrix_world.translation
 for deg in range(0,361,4):
  xf=Matrix.Translation(hub)@Matrix.Rotation(math.radians(deg),4,'Y')@Matrix.Translation(-hub);ov=cb.overlap(tree(v,f,xf));br.append({'wheel':k,'spin_degrees':deg,'pairs':len(ov)})
r={'result':'PASS'if not any(c['pairs']for c in br)else'FAIL','sha256':sha,'checks':len(br),'failed_checks':[c for c in br if c['pairs']],'scope':'Actual GLB fixed caliper versus alloy spokes/barrel/hub and ventilated rotor at4degree intervals over360degrees.'};(OUT/'brake_validation.json').write_text(json.dumps(r,indent=2));print('BRAKES',key,r['result'],len(r['failed_checks']),flush=True)
# Validate source hierarchy and independent motion without overwriting the saved source.
native=OUT/os.environ.get('CAR_NATIVE',key+'.blend');bpy.ops.wm.open_mainfile(filepath=str(native));bpy.context.view_layer.update();checks=[]
for k in keys:
 sp=bpy.data.objects['Spin_'+k];wg=bpy.data.objects['Wheel_'+k];part=next(o for o in wg.children if o.type=='MESH' and 'tire contact casing' in o.name.lower());ca=bpy.data.objects['Caliper_'+k];old=part.matrix_world@part.data.vertices[0].co;cm=ca.matrix_world.copy();sp.rotation_euler.y=.7;bpy.context.view_layer.update();movement=((part.matrix_world@part.data.vertices[0].co)-old).length;delta=max(abs(ca.matrix_world[r][c]-cm[r][c])for r in range(4)for c in range(4));checks.append({'wheel':k,'vertex_motion_m':movement,'caliper_matrix_delta':delta,'pass':movement>.1 and delta<1e-6});sp.rotation_euler.y=0
source={'source_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'editable_mesh_parts':sum(o.type=='MESH'for o in bpy.data.objects),'independent_spin_checks':checks,'image_dependencies':[i.filepath for i in bpy.data.images if i.source=='FILE'and i.filepath]};source['result']='PASS'if all(c['pass']for c in checks)and not source['image_dependencies']else'FAIL';(OUT/'source_validation.json').write_text(json.dumps(source,indent=2));print('NATIVE',key,source['result'],flush=True)
# Fixed wing, ignoring intentional support attachment only.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();wing=bpy.data.objects['RearWing'];wp=[o for o in wing.children_recursive if o.type=='MESH'];moving=[o for o in wp if'support'not in o.name.lower()];fixed=[o for o in bpy.data.objects if o.type=='MESH'and o not in wp]
def evgeom(obs):
 v=[];f=[];names=[]
 for o in obs:
  e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles();off=len(v);v.extend(o.matrix_world@p.co for p in me.vertices)
  for t in me.loop_triangles:f.append(tuple(off+i for i in t.vertices));names.append(o.name)
  e.to_mesh_clear()
 return v,f,names
fv,ff,fl=evgeom(fixed);wv,wf,wl=evgeom(moving);ov=tree(fv,ff).overlap(tree(wv,wf));r={'result':'PASS'if not ov else'FAIL','sha256':sha,'intersection_pairs':len(ov),'parts':list(set(fl[i]+' <-> '+wl[j]for i,j in ov)),'scope':'Fixed wing blade/endplates at rest versus all other native meshes. Intentional support attachment omitted; no active-wing API.'};(OUT/'wing_validation.json').write_text(json.dumps(r,indent=2));print('WING',key,r['result'],flush=True)
