"""Actual-GLB articulation intersections and sampled vertex clearances; not continuous proof."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Quaternion,Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];O=R/'assets/cars/midnight';f=R/'assets/web/car_midnight.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(f));bpy.context.view_layer.update();sha=hashlib.sha256(f.read_bytes()).hexdigest()
def geom(obs,predicate=None):
 v=[];fs=[];names=[]
 for o in obs:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles();off=len(v);v.extend(o.matrix_world@x.co for x in o.data.vertices)
  for t in o.data.loop_triangles:
   mat=o.data.materials[t.material_index].name
   if predicate and not predicate(mat):continue
   fs.append(tuple(off+i for i in t.vertices));names.append(o.name+'/'+mat)
 return v,fs,names

def tree(obs,predicate=None):
 v,f,n=geom(obs,predicate);return BVHTree.FromPolygons(v,f,all_triangles=True,epsilon=0),v,n
allmesh=[o for o in bpy.data.objects if o.type=='MESH'];out=[]
for name,axis in [('Hood',(0,-1,0)),('DoorHinge_Left',(0,0,-1)),('DoorHinge_Right',(0,0,1))]:
 group=bpy.data.objects[name];moving=[o for o in[group,*group.children_recursive]if o.type=='MESH'];fixed=[o for o in allmesh if o not in moving];bt,bv,bn=tree(fixed);group.rotation_mode='QUATERNION'
 for a in [0,.1,.2,.35,.5,.6]if name=='Hood'else[0,.1,.2,.35,.5,.7]:
  group.rotation_quaternion=Quaternion(Vector(axis),a);bpy.context.view_layer.update();wt,wv,wn=tree(moving);pairs=bt.overlap(wt);out.append({'part':name,'angle_rad':a,'intersection_pairs':len(pairs),'intentional_closed_seal_contact':a==0,'fixed_parts':list(set(bn[i]for i,j in pairs))})
 group.rotation_quaternion=Quaternion();bpy.context.view_layer.update()
# Distances from sampled exported tire vertices to closed body triangle surfaces at zero and full steer.
body=bpy.data.objects['CarBody'];bt,bv,bn=tree([body,*body.children_recursive]);dist=[]
for k in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
 st=bpy.data.objects['Steer_'+k];wh=bpy.data.objects['Wheel_'+k];st.rotation_mode='QUATERNION'
 for a in ([-.45,0,.45]if k.startswith('Front')else[0]):
  st.rotation_quaternion=Quaternion(Vector((0,0,1)),a);bpy.context.view_layer.update();_,v,fs=tree([wh],lambda m:'Tire rubber'in m);wh.data.calc_loop_triangles();tireverts={i for t in wh.data.loop_triangles if'Tire rubber'in wh.data.materials[t.material_index].name for i in t.vertices};ds=[]
  for i in tireverts:
   hit=bt.find_nearest(wh.matrix_world@wh.data.vertices[i].co)
   if hit:ds.append(hit[3])
  dist.append({'wheel':k,'steer_rad':a,'sampled_vertices':len(tireverts),'minimum_sampled_vertex_to_body_m':min(ds)})
 st.rotation_quaternion=Quaternion();bpy.context.view_layer.update()
r={'result':'PASS'if not any(x['intersection_pairs']for x in out if x['angle_rad']>0)else'FAIL','source_glb_sha256':sha,'articulation':out,'vertex_clearances':dist,'scope':'Discrete exported-mesh angles and tire vertex distances; closed panel seals may intentionally meet. Not a continuous mechanical proof.'};(O/'inspection_validation.json').write_text(json.dumps(r,indent=2));print('INSPECTION',r['result'],[(q['part'],q['angle_rad'],q['intersection_pairs'])for q in out if q['intersection_pairs']])
