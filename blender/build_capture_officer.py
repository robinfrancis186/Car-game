"""Original officer authoring from CC0 MakeHuman data; no MPFB add-on is used.

Run with Blender --background --factory-startup --disable-autoexec --python.
The source OBJ, target, groups and skeleton/weight JSON are data only. No shader
or Python file from an asset download is imported. Original uniform geometry and
materials follow the existing project's original-work rights scope.
"""
import bpy, json, gzip, math, sys, argparse
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--source',default=str(ROOT/'assets/capture_humans/source'))
parser.add_argument('--output',default=str(ROOT/'assets/capture_humans'))
parser.add_argument('--evidence',default=str(ROOT/'renders/capture_humans'))
parser.add_argument('--skin',default='')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[])
SOURCE,OUT,EVIDENCE=map(Path,[args.source,args.output,args.evidence])
OUT.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)

raw=[];texcoords=[];faces=[];face_uv=[]
for line in (SOURCE/'base.obj').read_text().splitlines():
 fields=line.split()
 if not fields:continue
 if fields[0]=='v':raw.append(Vector(tuple(map(float,fields[1:4]))))
 elif fields[0]=='vt':texcoords.append(tuple(map(float,fields[1:3])))
 elif fields[0]=='f':
  pairs=[v.split('/')for v in fields[1:]];ids=[int(v[0])-1 for v in pairs]
  if all(v<13380 for v in ids):faces.append(ids);face_uv.append([int(v[1])-1 for v in pairs])
assert len(raw)==19158
for line in gzip.decompress((SOURCE/'asian-male-young.target.gz').read_bytes()).decode().splitlines():
 if line and not line.startswith('#'):
  i,*delta=line.split();raw[int(i)]+=Vector(tuple(map(float,delta)))
floor=min(v.y for v in raw[:13380]);scale=1.76/(max(v.y for v in raw[:13380])-floor)
coords=[Vector((v.x*scale,-v.z*scale,(v.y-floor)*scale))for v in raw]
body_surface=BVHTree.FromPolygons(coords[:13380],faces,all_triangles=False)
groups=json.loads((SOURCE/'basemesh_vertex_groups.json').read_text())
rigdata=json.loads((SOURCE/'rig.game_engine.json').read_text())
weightdata=json.loads((SOURCE/'weights.game_engine.json').read_text());assert weightdata['license']=='CC0'
weights=[[]for _ in raw]
for name,entries in weightdata['weights'].items():
 for index,value in entries:
  if value>0:weights[index].append((name,value))
for i,entries in enumerate(weights):
 entries=sorted(entries,key=lambda p:p[1],reverse=True)[:4];total=sum(v for _,v in entries)
 weights[i]=[(n,v/total)for n,v in entries]if total else [('Root',1)]
def group_point(name):
 ids=[i for lo,hi in groups[name]for i in range(lo,hi+1)]
 return sum((coords[i]for i in ids),Vector())/len(ids)
def joint(definition):
 if definition['strategy']=='CUBE':return group_point(definition['cube_name'])
 ids=definition['vertex_indices'];return sum((coords[i]for i in ids),Vector())/len(ids)

armdata=bpy.data.armatures.new('Capture anatomical 53-bone skeleton')
arm=bpy.data.objects.new('CAPTURE_OFFICER_RIG',armdata);bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,definition in rigdata.items():
 bone=armdata.edit_bones.new(name);bone.head=joint(definition['head']);bone.tail=joint(definition['tail']);bone.roll=definition['roll']
 if(bone.tail-bone.head).length<.001:bone.tail.z+=.01
for name,definition in rigdata.items():
 if definition['parent']:armdata.edit_bones[name].parent=armdata.edit_bones[definition['parent']]
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True

def material(name,color,roughness=.65,metallic=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=roughness;p.inputs['Metallic'].default_value=metallic;return m
skin=material('Temporary authored medium-brown skin — texture pending',(.245,.112,.065),.49)
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.075
shirt=material('Original khaki cotton twill',(.225,.173,.099),.88)
pants=material('Original khaki trouser fabric',(.19,.151,.089),.91)
leather=material('CPO black leather belt and shoes',(.012,.011,.01),.43)
navy=material('Navy wool beret',(.012,.021,.045),.92)
metal=material('Brushed steel fasteners',(.48,.5,.48),.31,.8)
dark=material('Dark brown brows and seams',(.022,.012,.008),.82)
gold=material('CPO yellow cap ribbon and khaki lanyard',(.43,.29,.065),.75)
def bump(m,frequency,distance,strength):
 nodes=m.node_tree.nodes;links=m.node_tree.links;noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=frequency;noise.inputs['Detail'].default_value=2
 b=nodes.new('ShaderNodeBump');b.inputs['Distance'].default_value=distance;b.inputs['Strength'].default_value=strength;links.new(noise.outputs['Fac'],b.inputs['Height']);links.new(b.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
for m in [shirt,pants]:bump(m,310,.00025,.16)
bump(skin,190,.00012,.12);bump(navy,270,.0003,.22);bump(leather,180,.0001,.1)
if args.skin and Path(args.skin).is_file():
 image=bpy.data.images.load(str(Path(args.skin).resolve()));image.pack();tex=skin.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
 tint=skin.node_tree.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.56,.37,.26,1)
 skin.node_tree.links.new(tex.outputs['Color'],tint.inputs[1]);skin.node_tree.links.new(tint.outputs[0],skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);skin.name='CC0 MakeHuman skin with authored material tint'

objects=[]
def bind(mesh,source_ids=None,bone=None):
 if source_ids is not None:
  buckets={}
  for j,index in enumerate(source_ids):
   for name,value in weights[index]:buckets.setdefault(name,[]).append((j,value))
  for name,entries in buckets.items():
   group=mesh.vertex_groups.new(name=name)
   for index,value in entries:group.add([index],value,'REPLACE')
 elif bone:
  group=mesh.vertex_groups.new(name=bone);group.add(list(range(len(mesh.data.vertices))),1,'REPLACE')
 modifier=mesh.modifiers.new('CC0 skeletal deformation','ARMATURE');modifier.object=arm;mesh.parent=arm;objects.append(mesh)
def make_mesh(name,ids,polygons,mat,uv_indices=None,offset=0):
 selected=sorted({i for f in polygons for i in f});mapping={v:i for i,v in enumerate(selected)}
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([coords[i]for i in selected],[],[[mapping[i]for i in f]for f in polygons]);mesh.update()
 obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
 if uv_indices is not None:
  layer=mesh.uv_layers.new(name='MakeHuman UV')
  for p,uvs in zip(mesh.polygons,uv_indices):
   for loop,uv in zip(p.loop_indices,uvs):layer.data[loop].uv=texcoords[uv]
 for p in mesh.polygons:p.use_smooth=True
 if offset:
  normals=[v.normal.copy()for v in mesh.vertices]
  for v,n in zip(mesh.vertices,normals):
   amount=offset+(math.sin(v.co.z*65+v.co.x*47)*.0008 if mat in[shirt,pants]else 0)
   v.co+=n*amount
 bind(obj,selected)
 return obj
body=make_mesh('MakeHuman CC0 anatomical body',None,faces,skin,face_uv)
def dominant(face):
 bucket={}
 for i in face:
  for name,value in weights[i]:bucket[name]=bucket.get(name,0)+value
 return max(bucket,key=bucket.get)
shirt_faces=[];pant_faces=[]
for f in faces:
 center=sum((coords[i]for i in f),Vector())/len(f);bone=dominant(f)
 is_shirt=.99<center.z<1.47 and (abs(center.x)<.24 or bone.startswith('upperarm'))
 if bone.startswith('upperarm'):
  b=armdata.bones[bone];axis=b.tail_local-b.head_local;t=(center-b.head_local).dot(axis)/axis.length_squared;is_shirt=is_shirt and t<.64
 if is_shirt:shirt_faces.append(f)
 if .115<center.z<1.01 and bone.startswith(('pelvis','thigh','calf')):pant_faces.append(f)
uniform=make_mesh('Original short-sleeve uniform shirt',None,shirt_faces,shirt,offset=.012)
trousers=make_mesh('Original tailored uniform trousers',None,pant_faces,pants,offset=.019)
def neck_opening(a):
 frontness=max(0,-math.sin(a));drop=max(0,(frontness-.65)/.35)**2
 z=1.485+.008*math.sin(a)-.038*drop
 origin=Vector((0,-.01,z));direction=Vector((math.cos(a),math.sin(a),0));hit,normal,_,_=body_surface.ray_cast(origin,direction)
 assert hit,'Neck opening missed body'
 return hit+normal*.009
def garment_boundaries(obj,kind):
 mesh=obj.data;uses={}
 for polygon in mesh.polygons:
  for a,b in polygon.edge_keys:uses[tuple(sorted((a,b)))]=uses.get(tuple(sorted((a,b))),0)+1
 graph={}
 for(a,b),count in uses.items():
  if count==1:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
 components=[];unseen=set(graph)
 while unseen:
  todo=[unseen.pop()];component=[]
  while todo:
   index=todo.pop();component.append(index)
   for near in graph[index]:
    if near in unseen:unseen.remove(near);todo.append(near)
  components.append(component)
 for component in components:
  center=sum((mesh.vertices[i].co for i in component),Vector())/len(component)
  for i in component:
   p=mesh.vertices[i].co
   if kind=='shirt' and center.z>1.35 and abs(center.x)<.20:
    a=math.atan2((p.y+.025)/.086,p.x/.105);p[:]=neck_opening(a)
   elif abs(center.x)<.25 and center.z>.85 and center.z<1.2:p.z=1.008 if kind=='shirt'else 1.024
   elif kind=='shirt':
    bone=armdata.bones['upperarm_l'if center.x>0 else'upperarm_r'];axis=(bone.tail_local-bone.head_local);t=(p-bone.head_local).dot(axis)/axis.length_squared;p-=axis*(t-.64)
   else:p.z=.119
 # Relax the inherited anatomical surface into cloth, while keeping every seam fixed.
 fixed=set(graph);neighbors=[set()for _ in mesh.vertices]
 for edge in mesh.edges:
  a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
 for _ in range(65 if kind=='shirt'else 5):
  old=[v.co.copy()for v in mesh.vertices]
  for i,v in enumerate(mesh.vertices):
   if i not in fixed and neighbors[i]:
    average=sum((old[j]for j in neighbors[i]),Vector())/len(neighbors[i]);strength=.4 if kind=='shirt'and old[i].z>1.36 else(.005 if kind=='shirt'else .28)
    v.co=old[i].lerp(average,strength)
    if kind=='shirt'and old[i].z>1.36:
     near,normal,_,distance=body_surface.find_nearest(v.co)
     if (v.co-near).dot(normal)<.009:v.co=near+normal*.009
 mesh.update()
 for v in mesh.vertices:
  if v.index in fixed:continue
  p=v.co;waist=math.exp(-((p.z-1.08)/.095)**2)if kind=='shirt'else math.exp(-((p.z-.48)/.09)**2)
  v.co+=v.normal*(waist*.003*math.sin(p.x*72+p.z*43))
 mesh.update();return {'loops':len(components),'boundary_vertices':len(fixed)}
garment_checks={'shirt':garment_boundaries(uniform,'shirt'),'trousers':garment_boundaries(trousers,'trousers')}
for obj in [uniform,trousers]:
 solid=obj.modifiers.new('Cloth seam thickness','SOLIDIFY');solid.thickness=.0015
def box(name,position,size,mat,bone='spine_03',bevel=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=position);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Stitched edge radius','BEVEL');mod.width=bevel;mod.segments=2
 bind(o,bone=bone);return o
def sphere(name,position,size,mat,bone='head',segments=24,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=position);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 bind(o,bone=bone);return o
def front(x,z):
 hit,normal,_,_=body_surface.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 return hit.y-.016 if hit else -.13
def panel(name,verts,polys,mat,bone='spine_03'):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],polys);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);mesh.materials.append(mat);bind(o,bone=bone);return o
def stroke(name,points,radius,mat,bone='spine_03',closed=False):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius;curve.bevel_resolution=1
 spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
 for point,co in zip(spline.points,points):point.co=(*co,1)
 spline.use_cyclic_u=closed;obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);curve.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');bind(bpy.context.object,bone=bone);return bpy.context.object
def lettering(name,text,position,size,mat,bone='spine_03',rotation=(0,0,0)):
 curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.size=size;curve.align_x='CENTER';curve.extrude=.00015;obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.location=position;obj.rotation_euler=rotation;curve.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);bind(bpy.context.object,bone=bone);return bpy.context.object
# Reconstruct the collar in the SAME garment mesh, sharing the neckline edge.
# Traverse real topology rather than sorting vertices into a floating ring.
import bmesh
bm=bmesh.new();bm.from_mesh(uniform.data);bm.verts.ensure_lookup_table()
neck_edges=[e for e in bm.edges if e.is_boundary and all(v.co.z>1.38 for v in e.verts)]
neck_vertices={v for e in neck_edges for v in e.verts};assert len(neck_edges)==len(neck_vertices)==56
adj={v:[e.other_vert(v)for e in v.link_edges if e in neck_edges]for v in neck_vertices}
assert all(len(n)==2 for n in adj.values())
first=min(neck_vertices,key=lambda v:math.atan2(v.co.y+.01,v.co.x));ordered=[first];previous=None;current=first
while True:
 nxt=next(v for v in adj[current]if v!=previous)
 if nxt==first:break
 ordered.append(nxt);previous,current=current,nxt
assert len(ordered)==56
# Orient loop consistently, then select one contiguous rear arc, leaving a V front.
if sum((ordered[(i+1)%56].co.x-v.co.x)*(ordered[(i+1)%56].co.y+v.co.y)for i,v in enumerate(ordered))>0:ordered.reverse()
angles=[math.atan2(v.co.y+.01,v.co.x)for v in ordered]
front_index=min(range(56),key=lambda i:abs(((angles[i]+math.pi/2+math.pi)%math.tau)-math.pi))
ordered=ordered[front_index:]+ordered[:front_index]
# Keep the front opening wider than the folded rear stand.
rear=[v for v in ordered if v.co.y>-.01 or abs(v.co.x)>.065]
# Retain actual cyclic order; no disconnected collar patch or overlap at the seam.
indices=[i for i,v in enumerate(ordered)if v in rear]
# Rear vertices occupy a contiguous interval after the front split.
lo,hi=min(indices),max(indices);arc=ordered[lo:hi+1]
assert all(v in rear for v in arc),'Open collar arc must be contiguous'
previous_row=arc;rows=[arc]
for row in range(1,7):
 t=row/6;new=[]
 for i,base in enumerate(arc):
  p=base.co;direction=Vector((p.x,p.y+.01,0)).normalized();fold=Vector((p.x,p.y,p.z))
  # Rise to a narrow fold, then turn outward/down onto the chest and shoulders.
  if t<=.5:
   q=p+Vector((0,0,.028*t*2))-direction*(.005*t*2)
  else:
   u=(t-.5)*2;crease=p+Vector((0,0,.028))-direction*.005
   outside=p+direction*.032+Vector((0,0,-.018))
   tip=max(0,1-min(i,len(arc)-1-i)/5)**2
   outside.z-=tip*.025;outside.y-=tip*.012
   q=crease.lerp(outside,u)
  new.append(bm.verts.new(q))
 for i in range(len(arc)-1):bm.faces.new((previous_row[i],previous_row[i+1],new[i+1],new[i]))
 previous_row=new;rows.append(new)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(uniform.data);bm.free();uniform.data.update()
# New collar vertices share the upper torso deformation; no independent object.
collar_start=len(uniform.data.vertices)-6*len(arc)
for group in uniform.vertex_groups:group.remove(list(range(collar_start,len(uniform.data.vertices))))
g=uniform.vertex_groups.get('spine_03')or uniform.vertex_groups.new(name='spine_03');g.add(list(range(collar_start,len(uniform.data.vertices))),1,'REPLACE')
for v in uniform.data.vertices:
 if v.co.z>1.38 and abs(v.co.x)<.15:
  for group in uniform.vertex_groups:group.remove([v.index])
  g.add([v.index],1,'REPLACE')
for polygon in uniform.data.polygons:polygon.use_smooth=True
collar_topology={'shared_neckline_vertices':len(arc),'new_vertices':6*len(arc),'connected_mesh':True}
# Check the actual sewn surface: one connected component and the original four
# openings (neck, waist, two sleeve cuffs), with no branching boundary edges.
uses={};neighbors={v.index:set()for v in uniform.data.vertices}
for polygon in uniform.data.polygons:
 for a,b in polygon.edge_keys:
  key=tuple(sorted((a,b)));uses[key]=uses.get(key,0)+1;neighbors[a].add(b);neighbors[b].add(a)
assert max(uses.values())==2
unseen=set(neighbors);component_count=0
while unseen:
 todo=[unseen.pop()];component_count+=1
 while todo:
  for j in neighbors[todo.pop()]:
   if j in unseen:unseen.remove(j);todo.append(j)
assert component_count==1
boundary={}
for(a,b),count in uses.items():
 if count==1:boundary.setdefault(a,set()).add(b);boundary.setdefault(b,set()).add(a)
assert all(len(v)==2 for v in boundary.values())
unseen=set(boundary);boundary_loops=0
while unseen:
 todo=[unseen.pop()];boundary_loops+=1
 while todo:
  for j in boundary[todo.pop()]:
   if j in unseen:unseen.remove(j);todo.append(j)
assert boundary_loops==4
collar_topology.update({'surface_components':component_count,'boundary_loops':boundary_loops,'maximum_edge_face_valence':max(uses.values()),'branching_boundary_vertices':0})

# One subdivision level fairs the connected upper garment and fold silhouette.
# This is editable authoring geometry, not the eventual mobile LOD.
fair=uniform.modifiers.new('Connected garment surface fairing','SUBSURF');fair.levels=1;fair.render_levels=1
bpy.context.view_layer.objects.active=uniform
bpy.ops.object.modifier_move_to_index(modifier=fair.name,index=0)
# Matching waist deformation: rigid pelvis zone under belt, graded transition above/below.
waist_weight_checks={}
for obj,kind in [(uniform,'shirt'),(trousers,'trousers')]:
 count=0;maximum_thigh=0
 for v in obj.data.vertices:
  z=v.co.z
  blend=max(0,min(1,(1.16-z)/.10))if kind=='shirt'else max(0,min(1,(z-.95)/.038))
  if not blend:continue
  old={obj.vertex_groups[g.group].name:g.weight for g in v.groups}
  for group in obj.vertex_groups:group.remove([v.index])
  new={name:value*(1-blend)for name,value in old.items()};new['pelvis']=new.get('pelvis',0)+blend
  new=dict(sorted(new.items(),key=lambda item:item[1],reverse=True)[:4]);total=sum(new.values());new={name:value/total for name,value in new.items()}
  for name,value in new.items():
   if value>1e-6:(obj.vertex_groups.get(name)or obj.vertex_groups.new(name=name)).add([v.index],value,'REPLACE')
  if .988<=z<=1.028:
   maximum_thigh=max(maximum_thigh,sum(value for name,value in new.items()if name.startswith('thigh')));count+=1
 waist_weight_checks[kind]={'waist_vertices':count,'max_thigh_weight':maximum_thigh,'pelvis_weight':1.0}
 assert maximum_thigh<1e-6
for side in [-1,1]:
 x=side*.093;z=1.275;y=front(x,z)
 box('Original breast pocket '+str(side),(x,y-.002,z),(.076,.006,.088),shirt)
 panel('Pointed pocket flap '+str(side),[(x-.041,y-.007,z+.044),(x+.041,y-.007,z+.044),(x+.036,y-.011,z+.015),(x,y-.015,z+.004),(x-.036,y-.011,z+.015)],[(0,1,2,3,4)],shirt)
 sphere('Pocket button '+str(side),(x,y-.017,z+.023),(.003,.002,.003),metal,bone='spine_03',segments=12,rings=8)
 stroke('Pocket stitched edge '+str(side),[(x-.034,y-.006,z+.035),(x-.034,y-.006,z-.036),(x+.034,y-.006,z-.036),(x+.034,y-.006,z+.035)],.00045,pants)
 box('Plain shoulder epaulette '+str(side),(side*.16,.003,1.408),(.075,.035,.006),shirt,bevel=.003)
 lettering('CPO shoulder KP letters '+str(side),'KP',(side*.184,-.008,1.413),.009,metal)
for z in [1.08,1.15,1.22,1.29,1.36,1.415]:
 y=front(0,z);sphere('Shirt fastening',(0,y-.004,z),(.0032,.002,.0032),metal,bone='spine_03',segments=12,rings=8)
stroke('Shirt placket stitching',[(-.009,front(-.009,1.04+i*.017)-.001,1.04+i*.017)for i in range(23)],.00045,pants)
box('Generic patrol identification',(.09,front(.09,1.365)-.005,1.365),(.067,.004,.013),navy,bevel=.001)

# Fit the belt outside the actual shirt/trouser surfaces, rather than bare skin.
cloth_surfaces=[BVHTree.FromPolygons([v.co for v in obj.data.vertices],[tuple(poly.vertices)for poly in obj.data.polygons],all_triangles=False)for obj in [uniform,trousers]]
segments=128;cy=-.025;belt_envelope=[]
for i in range(segments):
 a=i*math.tau/segments;direction=Vector((math.cos(a),math.sin(a),0));radii=[]
 for z in [.995,1.005,1.017]:
  origin=Vector((0,cy,z))
  for surface in cloth_surfaces:
   hit,_,_,_=surface.ray_cast(origin,direction)
   if hit:radii.append((hit-origin).length)
 assert radii,'The closed waistband must have a surface in every direction'
 belt_envelope.append(max(radii)+.010)
# Enclose every waist vertex as well as sampled rays; smoothing can place a
# local extremum between the three sampled heights.
for obj in [uniform,trousers]:
 for v in obj.data.vertices:
  if .984<=v.co.z<=1.032:
   u=(math.atan2(v.co.y-cy,v.co.x)%math.tau)/math.tau*segments;i=int(u);required=math.hypot(v.co.x,v.co.y-cy)+.010
   for j in [i,(i+1)%segments]:belt_envelope[j]=max(belt_envelope[j],required)
verts=[]
for z in [.988,1.028]:
 for inset in [0,.004]:
  for i,radius in enumerate(belt_envelope):
   a=i*math.tau/segments;verts.append(((radius-inset)*math.cos(a),cy+(radius-inset)*math.sin(a),z))
polys=[]
for i in range(segments):
 j=(i+1)%segments
 for a,b in [(0,2*segments),(segments,3*segments),(0,segments),(2*segments,3*segments)]:polys.append((a+i,a+j,b+j,b+i))
waist_clearances=[]
for obj in [uniform,trousers]:
 for v in obj.data.vertices:
  if .988<=v.co.z<=1.028:
   a=math.atan2(v.co.y-cy,v.co.x)%math.tau;u=a/math.tau*segments;i=int(u);radius=belt_envelope[i]*(1-(u-i))+belt_envelope[(i+1)%segments]*(u-i)
   waist_clearances.append(radius-.004-math.hypot(v.co.x,v.co.y-cy))
waist_min_clearance=min(waist_clearances);assert waist_min_clearance>.001,'Belt/trouser surface intersection'
belt=panel('CPO fitted black leather belt',verts,polys,leather,bone='pelvis')
low=cy-belt_envelope[segments*3//4]
box('Plain steel belt buckle',(0,low-.004,1.007),(.046,.008,.033),metal,bone='pelvis',bevel=.003)
# CPO reference: khaki lanyard on the left, no officer stars or SCPO chevrons.
lanyard=[(.18,-.015,1.407),(.204,-.06,1.36),(.205,-.105,1.29),(.185,-.14,1.23),(.14,-.16,1.225),(.1,front(.1,1.285)-.012,1.285)]
for shift in [-.0015,.0015]:stroke('CPO khaki lanyard',[(x+shift,y,z)for x,y,z in lanyard],.0016,gold)
box('Lanyard whistle',(.108,front(.108,1.275)-.018,1.267),(.009,.006,.025),metal,bevel=.002)
for side in [-1,1]:
 foot=group_point('joint-'+('l'if side>0 else'r')+'-ankle');bone='foot_l'if side>0 else'foot_r'
 stations=[(-.255,.012,.045),(-.23,.055,.067),(-.15,.067,.085),(-.04,.059,.105),(.055,.045,.11)]
 shoe=[]
 for y,radius,top in stations:
  for i in range(24):
   a=i*math.tau/24;shoe.append((foot.x+radius*math.cos(a),foot.y+y,(.018+top)/2+(top-.018)/2*math.sin(a)))
 polys=[tuple(range(23,-1,-1))]
 for j in range(len(stations)-1):
  for i in range(24):polys.append((j*24+i,j*24+(i+1)%24,(j+1)*24+(i+1)%24,(j+1)*24+i))
 polys.append(tuple(range((len(stations)-1)*24,len(stations)*24)))
 shoe_mesh=panel('Original closed leather shoe '+str(side),shoe,polys,leather,bone=bone)
 for polygon in shoe_mesh.data.polygons:polygon.use_smooth=True
 outline=[]
 for i in range(48):
  a=i*math.tau/48;front_factor=(1-math.cos(a))/2;outline.append((foot.x+(.053+.012*front_factor)*math.sin(a),foot.y-.095+.17*math.cos(a)))
 sole=[(x,y,z)for z in [.007,.022]for x,y in outline]
 sole_faces=[tuple(range(47,-1,-1)),tuple(range(48,96))]+[(i,(i+1)%48,(i+1)%48+48,i+48)for i in range(48)]
 panel('Original rounded shoe sole '+str(side),sole,sole_faces,dark,bone=bone)
 stroke('Shoe welt '+str(side),[(x,y,.024)for x,y in outline],.0011,leather,bone=bone,closed=True)
 # Restrained oxford-style toe cap, quarters and crossed laces give scale cues.
 stroke('Toe cap seam '+str(side),[(foot.x+.051*math.sin(a),foot.y-.17+.008*math.cos(a),.068+.015*math.cos(a))for a in [i*math.pi/16-math.pi/2 for i in range(17)]],.0007,dark,bone=bone)
 for j in range(4):
  y=foot.y-.065+j*.023;z=.103+j*.001
  stroke('Shoe lace '+str(side)+' '+str(j),[(foot.x-.026,y,z),(foot.x+.024,y+.018,z+.002)],.00085,dark,bone=bone)
  sphere('Shoe eyelet',(foot.x-.027,y,z),(.002,.002,.0013),metal,bone=bone,segments=10,rings=6)
  sphere('Shoe eyelet',(foot.x+.027,y+.018,z+.002),(.002,.002,.0013),metal,bone=bone,segments=10,rings=6)

# Anatomical eyes occupy the source mesh's own sockets. No reference photo is used.
eye_white=material('Warm sclera',(.6,.58,.52),.28);iris=material('Dark brown iris',(.055,.023,.009),.24);pupil=material('Pupil',(.002,.002,.002),.2)
for side in ['l','r']:
 center=group_point('joint-'+side+'-eye');sphere('Sclera '+side,center,(.0125,.0125,.0125),eye_white)
 sphere('Iris '+side,(center.x,center.y-.0118,center.z),(.0055,.0015,.0055),iris)
 sphere('Pupil '+side,(center.x,center.y-.013,center.z),(.0025,.0008,.0025),pupil,segments=16,rings=10)
 # Original tapered brow strand cluster follows the brow ridge.
 for j in range(26):
  u=j/25;x=center.x-.019+u*.038;z=center.z+.020+math.sin(u*math.pi)*.004;length=.0012+.0025*math.sin(u*math.pi)
  points=[]
  for k in range(3):
   xx=x+k*.0005;zz=z+(k/2-.4)*length;points.append((xx,front(xx,zz)+.0154,zz))
  stroke('Original brow strands '+side+' '+str(j),points,.00018,dark,bone='head')

headtop=max(p.z for p in coords[:13380]);cap_axis_y=-.045;cap_bottom=headtop-.055
# Sample the actual anatomical head cross-section for a true outside fit.
def cap_outline(z,a,clearance):
 sample_z=min(z,headtop-.024);origin=Vector((0,cap_axis_y,sample_z));direction=Vector((math.cos(a),math.sin(a),0))
 hit,_,_,_=body_surface.ray_cast(origin,direction)
 assert hit,'Cap fitting ray missed the head'
 q=hit+direction*clearance;q.z=z;return q
cap=[];cap_rows=[(cap_bottom,.008),(headtop-.024,.009),(headtop+.012,.022),(headtop+.030,.014)]
for z,clearance in cap_rows:
 for i in range(64):cap.append(cap_outline(z,i*math.tau/64,clearance))
cap_faces=[(r*64+i,r*64+(i+1)%64,(r+1)*64+(i+1)%64,(r+1)*64+i)for r in range(3)for i in range(64)]+[tuple(range(192,256))]
crown=panel('CPO head-fitted blue peaked cap',cap,cap_faces,navy,bone='head')
for polygon in crown.data.polygons:polygon.use_smooth=True
cap_clearances=[]
for point in cap[:128]:
 nearest,normal,_,_=body_surface.find_nearest(point);cap_clearances.append((point-nearest).dot(normal))
cap_min_clearance=min(cap_clearances)
assert cap_min_clearance>.002,'Cap band intersects anatomical head'
for z in [cap_bottom+.018,cap_bottom+.025]:
 stroke('CPO yellow cap ribbon',[cap_outline(z,i*math.tau/64,.013)for i in range(64)],.0025,gold,bone='head',closed=True)
visor=[]
for ring in range(2):
 for i in range(33):
  a=math.pi+i*math.pi/32;direction=Vector((math.cos(a),math.sin(a),0));q=cap_outline(cap_bottom+.003,a,.009)
  if ring:q+=direction*(.004+.065*max(0,-math.sin(a)));q.z-=.014*max(0,-math.sin(a))
  visor.append(q)
peak=panel('CPO fitted curved visor',visor,[(i,i+1,i+34,i+33)for i in range(32)],leather,bone='head');solid=peak.modifiers.new('Visor edge thickness','SOLIDIFY');solid.thickness=.0028
# Original small relief interpretation of the reference KP badge outline;
# no photograph is used as a texture and no rank star/stripe is added.
badge_y=cap_outline(headtop+.006,math.pi*1.5,.026).y-.002;badge_z=headtop+.006
for side in[-1,1]:
 for j in range(7):
  a=.25+j*.20;x=side*math.sin(a)*.011;z=badge_z-.010+math.cos(a)*.012
  leaf=sphere('Reference-based KP wreath relief',(x,badge_y,z),(.002,.0013,.0038),metal,bone='head',segments=10,rings=6);leaf.rotation_euler.y=side*(.4+j*.1)
box('KP badge plinth',(0,badge_y-.001,badge_z-.005),(.012,.002,.004),metal,bone='head',bevel=.001)
for x in[-.003,0,.003]:sphere('KP capital relief',(x,badge_y-.001,badge_z+.004),(.0025,.0015,.004),metal,bone='head',segments=10,rings=6)
for a in[-.42,math.pi+.42]:
 q=cap_outline(cap_bottom+.007,a,.013);sphere('CPO cap strap button',q,(.003,.002,.003),metal,bone='head',segments=12,rings=8)
stroke('CPO fitted black cap strap',[cap_outline(cap_bottom+.007,math.pi+i*math.pi/32,.013)for i in range(33)],.0018,leather,bone='head')

# Left sleeve patch: reference colors/outline and service name, no invented rank.
bone=armdata.bones['upperarm_l'];axis=(bone.tail_local-bone.head_local).normalized();up=-axis;across=Vector((0,-1,0));normal=up.cross(across).normalized();origin=bone.head_local+(bone.tail_local-bone.head_local)*.3+normal*.048
def patchpoint(x,y,depth=0):return origin+across*x+up*y+normal*depth
shield=[(-.024,.034),(.024,.034),(.025,-.012),(.018,-.027),(0,-.038),(-.018,-.027),(-.025,-.012)]
panel('CPO left sleeve Kerala Police patch',[patchpoint(x,y)for x,y in shield],[tuple(range(7))],navy,bone='upperarm_l')
stroke('CPO patch gold edging',[patchpoint(x,y,.0008)for x,y in shield],.001,gold,bone='upperarm_l',closed=True)
red=material('Reference patch red field',(.34,.019,.018),.9)
panel('CPO patch red field',[patchpoint(x,y,.001)for x,y in[(-.019,.016),(.019,.016),(.019,-.004),(-.019,-.004)]],[(0,1,2,3)],red,bone='upperarm_l')
for j in range(20):
 a=j*math.tau/20;p=patchpoint(math.cos(a)*.012,-.008+math.sin(a)*.016,.002)
 sphere('CPO patch wreath',p,(.0014,.0014,.0014),gold,bone='upperarm_l',segments=8,rings=6)
# Fine embroidered lettering will be baked for runtime after geometry review.
from mathutils import Matrix
patch_text=lettering('CPO Kerala Police patch text','KERALA POLICE',(0,0,0),.0042,metal,bone='upperarm_l')
matrix=Matrix((across,up,normal)).transposed().to_4x4();matrix.translation=patchpoint(0,.024,.002)
for vertex in patch_text.data.vertices:vertex.co=matrix@vertex.co

# Two-bone IK relaxes the skinned arms; fingers retain anatomical mesh topology.
targets={}
for side,sign in [('l',1),('r',-1)]:
 t=bpy.data.objects.new('Authored wrist target '+side,None);bpy.context.collection.objects.link(t);t.location=(sign*.275,-.035,.88);targets[side]=t
 c=arm.pose.bones['lowerarm_'+side].constraints.new('IK');c.target=t;c.chain_count=2;c.use_tail=True
from mathutils import Matrix
from mathutils.kdtree import KDTree
root_rest=armdata.bones['Root'].matrix_local.copy()
def align_bone(name,head,tail):
 rest=armdata.bones[name];direction=(tail-head).normalized()
 q=(rest.tail_local-rest.head_local).normalized().rotation_difference(direction)@rest.matrix_local.to_quaternion()
 arm.pose.bones[name].matrix=Matrix.Translation(head)@q.to_matrix().to_4x4()
 bpy.context.view_layer.update()
def solve_leg(side,ankle):
 thigh=armdata.bones['thigh_'+side];calf=armdata.bones['calf_'+side]
 hip=arm.pose.bones[thigh.name].head.copy();delta=ankle-hip;distance=delta.length
 assert abs(thigh.length-calf.length)<distance<thigh.length+calf.length
 direction=delta.normalized();a=(thigh.length**2-calf.length**2+distance**2)/(2*distance)
 b=math.sqrt(max(0,thigh.length**2-a*a));pole=Vector((0,-1,0))
 bend=(pole-direction*pole.dot(direction)).normalized();knee=hip+direction*a+bend*b
 align_bone(thigh.name,hip,knee);align_bone(calf.name,knee,ankle)
 foot=arm.pose.bones['foot_'+side];foot.matrix=Matrix.Translation(ankle)@armdata.bones[foot.name].matrix_local.to_quaternion().to_matrix().to_4x4()
 bpy.context.view_layer.update()
 return {'hip':list(hip),'knee':list(knee),'ankle':list(ankle),'ankle_error_m':(arm.pose.bones[calf.name].tail-ankle).length}
def set_pose(kind):
 for bone in arm.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 root=arm.pose.bones['Root'];root.matrix=root_rest.copy();spine=arm.pose.bones['spine_02'];spine.rotation_mode='XYZ'
 ankle_goals={side:armdata.bones['foot_'+side].head_local.copy()for side in ['l','r']}
 for side,sign in [('l',1),('r',-1)]:targets[side].location=(sign*.275,-.035,.88)
 if kind=='seated':
  root.matrix=Matrix.Translation((0,0,-.44))@root_rest;spine.rotation_euler.x=.09
  for side,sign in [('l',1),('r',-1)]:ankle_goals[side]=Vector((sign*.17,-.46,.075));targets[side].location=(sign*.22,-.28,.79)
 elif kind=='walk':
  root.matrix=Matrix.Translation((0,0,-.045))@root_rest
  ankle_goals['l']=Vector((.16,-.18,.075));ankle_goals['r']=Vector((-.16,.16,.10));targets['l'].location=(.26,.10,.91);targets['r'].location=(-.26,-.15,.94)
 elif kind=='secure':
  for side,sign in [('l',1),('r',-1)]:targets[side].location=(sign*.23,-.40,1.17)
 elif kind=='raised':targets['l'].location=(.35,-.30,1.24)
 bpy.context.view_layer.update();checks={}
 if kind in ['seated','walk']:
  for side in ['l','r']:checks[side]=solve_leg(side,ankle_goals[side])
 if kind=='seated':
  for check in checks.values():
   h,k,f=map(Vector,[check['hip'],check['knee'],check['ankle']])
   assert k.y<h.y-.2 and abs(k.z-h.z)<.15 and k.z>f.z+.25,'Seated knee anatomy failed'
 if kind=='secure':
  for side in ['l','r']:
   h=arm.pose.bones['hand_'+side].head.copy();align_bone('hand_'+side,h,h+Vector((0,-.12,-.012)))
  deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh();points={}
  for side in ['l','r']:
   ids=[i for i,w in enumerate(weights[:13380])if sum(v for n,v in w if n.endswith('_'+side)and('hand' in n or 'finger' in n))>.5]
   points[side]=[mesh.vertices[i].co.copy()for i in ids]
  tree=KDTree(len(points['l']))
  for i,v in enumerate(points['l']):tree.insert(v,i)
  tree.balance();gap=min(tree.find(v)[2]for v in points['r']);evaluated.to_mesh_clear()
  assert gap>.02,'Securing hands intersect';checks['minimum_hand_surface_gap_m']=gap
 return checks

# Preview studio only; these lights/ground are not exported into the game.
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.08,.08,.08);scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
groundmat=material('Preview ground',(.12,.14,.15),.85)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));ground=bpy.context.object;ground.name='Preview ground only';ground.data.materials.append(groundmat)
def area(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large neutral key',(-2,-3,4),450,3,(1,.92,.82));area('Soft cool fill',(2,-1,2.6),170,2.5,(.75,.85,1));area('Shoulder rim',(1,2,3.5),350,2,(1,.9,.75))
camdata=bpy.data.cameras.new('Officer review camera');camera=bpy.data.objects.new('Officer review camera',camdata);bpy.context.collection.objects.link(camera);scene.camera=camera
def render(name,position,target,lens,resolution):
 camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camdata.lens=lens
 scene.render.resolution_x,scene.render.resolution_y=resolution;scene.render.filepath=str(EVIDENCE/(name+'.png'));bpy.ops.render.render(write_still=True)
set_pose('idle')
render('officer-garment-fix-fullbody',(2.25,-4.1,1.85),(0,0,.91),70,(1000,1400))
render('officer-garment-fix-cap',(.4,-1.25,1.86),(0,-.025,1.68),78,(1100,1100))
render('officer-garment-fix-collar',(.25,-.95,1.60),(0,-.025,1.445),78,(1100,1100))
render('officer-garment-fix-waist',(.45,-1.15,1.13),(0,-.025,1.01),78,(1100,900))
def posed_waist_check():
 fair.show_viewport=False;bpy.context.view_layer.update()
 deps=bpy.context.evaluated_depsgraph_get();transform=arm.pose.bones['pelvis'].matrix@armdata.bones['pelvis'].matrix_local.inverted();inverse=transform.inverted();drift=[];clearances=[]
 for obj in [uniform,trousers]:
  evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
  for v in obj.data.vertices:
   if .988<=v.co.z<=1.028:
    p=inverse@mesh.vertices[v.index].co;drift.append((p-v.co).length)
    u=(math.atan2(p.y-cy,p.x)%math.tau)/math.tau*segments;i=int(u);radius=belt_envelope[i]*(1-(u-i))+belt_envelope[(i+1)%segments]*(u-i)
    clearances.append(radius-.004-math.hypot(p.x,p.y-cy))
  evaluated.to_mesh_clear()
 fair.show_viewport=True;bpy.context.view_layer.update()
 return {'checked_surface':'base skin vertices; rendered subdivision inspected separately','waist_pelvis_space_max_drift_m':max(drift),'minimum_belt_waist_clearance_m':min(clearances),'passed':max(drift)<.00001 and min(clearances)>.001}
render('officer-garment-fix-collar-back',(.35,1.0,1.62),(0,0,1.47),78,(1100,1000))
render('officer-garment-fix-collar-side',(1.05,-.15,1.60),(0,-.01,1.46),78,(1100,1000))
pose_checks=[]
for kind in ['seated','walk']:
 checks=set_pose(kind);checks['waist']=posed_waist_check()
 assert checks['waist']['passed'],'Posed waist lost its belt clearance'
 for bone in arm.pose.bones:assert all(math.isfinite(v)for row in bone.matrix for v in row)
 pose_checks.append({'pose':kind,'finite_bone_transforms':True,'geometry':checks,'wrist_target_errors_m':{side:(arm.pose.bones['lowerarm_'+side].tail-targets[side].location).length for side in ['l','r']}})
 render('officer-garment-fix-'+kind,(2.0,-3.7,1.5),(0,0,.70 if kind=='seated'else.95),70,(1000,1400))
 render('officer-garment-fix-waist-'+kind,(.65,-1.25,.88 if kind=='seated'else 1.13),(0,-.08,.57 if kind=='seated'else.98),65,(1100,1000))
 render('officer-garment-fix-waist-back-'+kind,(.6,1.15,.85 if kind=='seated'else 1.1),(0,0,.55 if kind=='seated'else.98),65,(1100,1000))
set_pose('idle')
deps=bpy.context.evaluated_depsgraph_get();triangles=0
for obj in objects:
 evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
 assert all(math.isfinite(v)for p in mesh.vertices for v in p.co)
 evaluated.to_mesh_clear()
report={'stage':'refined CPO authoring checkpoint, not integrated','uniform_reference':'Kerala Police Uniforms January 2020, printed page 16 / PDF page 19, Civil Police Officer','height_m':1.76,'bones':len(armdata.bones),'max_skin_influences':4,'preview_character_triangles':triangles,'source_body_vertices':13380,'garment_boundaries':garment_checks,'collar_topology':collar_topology,'waist_weights':waist_weight_checks,'belt_minimum_clearance_m':waist_min_clearance,'cap_minimum_clearance_m':cap_min_clearance,'pose_checks':pose_checks,'downloaded_code_executed':False,'addon_installed':False,'skin_texture':bool(args.skin and Path(args.skin).is_file()),'limitations':['CPO reference configuration selected; badge relief remains simplified.','Uniform fitting and facial/hand deformation require image review.','Preview studio is not the game lighting.','LOD/export/runtime animation and mobile cost not yet validated.']}
(OUT/'garment-fix-review.json').write_text(json.dumps(report,indent=2)+'\n')
for image in bpy.data.images:
 if image.packed_file:image.filepath='//source/'+Path(image.filepath).name
scene.render.filepath=''
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'capture_officer_garment_fix.blend'))
print('OFFICER_CHECKPOINT='+json.dumps(report),flush=True)
