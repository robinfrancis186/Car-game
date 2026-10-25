"""Build the original Highland Run in Blender and export a playable exact-height course.
No coastal runtime is modified. Geometry is original; user photographs are visual cues only.
"""
import bpy,bmesh,math,json,random,bisect,hashlib,shutil
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/highlands';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
plan=json.loads((OUT/'highlands_plan.json').read_text());tea=json.loads((OUT/'tea_rows.json').read_text());grid=plan['terrain_grid'];nx,nz=grid['count'];dx,dz=grid['step'];xmin,zmin=grid['origin'];H=np.array(grid['heights']).reshape(nz,nx);route=plan['route_points_blender_m'];dist=plan['horizontal_route_distances_m'];length=dist[-1];rng=random.Random(7048)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.name='Highland_Run_Original';scene.unit_settings.system='METRIC'
M={};batches={};groups={};props=[];furniture=[];infra=[];library={};placement_stats={}
def material(name,color,rough=.9,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;M[name]=m;return m
material('Highlands_Ground',(.27,.37,.105));material('Highlands_Rock',(.32,.32,.265));material('Highlands_Asphalt',(.095,.11,.12));material('Highlands_GravelShoulder',(.42,.36,.27));material('Highlands_WeatheredWhite',(.84,.84,.74));material('Highlands_SafetyYellow',(.91,.62,.025));material('Highlands_BarrierBlack',(.045,.05,.044));material('Highlands_GuardrailMetal',(.49,.55,.55),.5,.55);material('Highlands_FoundationStone',(.38,.35,.29));material('Highlands_MedianPlanting',(.22,.37,.065))
for k,c in enumerate([(.14,.32,.045),(.18,.36,.055),(.115,.275,.035)]):material('Highlands_TeaCanopy_'+str(k),c)
F=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def add(group,mat,verts,faces):
 b=batches.setdefault((group,mat),[[],[]]);off=len(b[0]);b[0].extend(verts);b[1].extend(tuple(off+i for i in f) for f in faces)
def box(group,mat,c,size,angle=0):
 x,y,z=c;a,b,d=[v/2 for v in size];ca,sa=math.cos(angle),math.sin(angle);vv=[]
 for xx,yy,zz in [(-a,-b,-d),(a,-b,-d),(a,b,-d),(-a,b,-d),(-a,-b,d),(a,-b,d),(a,b,d),(-a,b,d)]:vv.append((x+ca*xx-sa*yy,y+sa*xx+ca*yy,z+zz))
 add(group,mat,vv,F)
def height(x,y):
 u=(x-xmin)/dx;v=(-y-zmin)/dz;i=max(0,min(nx-2,math.floor(u)));j=max(0,min(nz-2,math.floor(v)));u=max(0,min(1,u-i));v=max(0,min(1,v-j));a,b,c,d=H[j,i],H[j,i+1],H[j+1,i],H[j+1,i+1];return float(a+(b-a)*u+(d-b)*v if v<=u else a+(d-c)*u+(c-a)*v)
def at(s):
 s=max(0,min(length,s));i=max(0,min(len(dist)-2,bisect.bisect_right(dist,s)-1));f=(s-dist[i])/(dist[i+1]-dist[i]);a,b=route[i],route[i+1];p=tuple(a[k]+f*(b[k]-a[k]) for k in range(3));tx,ty=b[0]-a[0],b[1]-a[1];norm=math.hypot(tx,ty);return p,(tx/norm,ty/norm)
def offset(s,l,zadd=0):
 p,t=at(s);return(p[0]-t[1]*l,p[1]+t[0]*l,p[2]+zadd)
def ribbon(group,mat,start,end,a,b,za=0,zb=0,step=3):
 if end<=start:return
 ss=sorted(set([start,end]+[d for d in dist if start<d<end]+list(np.arange(start,end,step))));vv=[]
 for s in ss:vv.extend([offset(s,a,za),offset(s,b,zb)])
 add(group,mat,vv,[(2*i,2*i+2,2*i+3,2*i+1) for i in range(len(ss)-1)])
def capsule(s0,s1,l,r,h,kind='rail'):
 a=offset(s0,l);b=offset(s1,l);bottom=min(a[2],b[2])-.04;furniture.append({'id':f'highlands-{kind}-{len(furniture)}','kind':kind,'shape':'capsule','x':a[0],'z':-a[1],'endX':b[0],'endZ':-b[1],'radius':r,'y':bottom,'height':h+abs(a[2]-b[2])+.04})
def obb(c,size,angle,kind,asset=None):
 x,y,z=c;lx,ly,lz=size;infra.append({'id':f'highlands-{kind}-{len(infra)}','asset':asset,'kind':kind,'shape':'box','x':x,'z':-y,'halfLength':lx/2,'halfWidth':ly/2,'heading':-angle,'radius':math.hypot(lx,ly)/2,'y':z-lz/2,'height':lz})
def load(name,path):
 if name not in library:
  with bpy.data.libraries.load(str(path),link=False) as (src,dst):
   has_collection=name in src.collections
   if has_collection:dst.collections=[name]
   else:dst.objects=list(src.objects)
  if has_collection:library[name]=dst.collections[0]
  else:
   collection=bpy.data.collections.new(name+'_SourceWrapper')
   for o in dst.objects:
    if o and o.type in ['MESH','EMPTY']:collection.objects.link(o)
   library[name]=collection
 return library[name]
def place(name,p,angle=0,scale=1,source=None,extras=None):
 if source:
  c=load(name,source);o=bpy.data.objects.new(name+'_placement',None);scene.collection.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=c;o.location=p;o.rotation_euler[2]=angle;o.scale=(scale,)*3
 q={'asset':name,'position':[p[0],p[2],-p[1]],'yaw_rad':-angle,'scale':scale}
 if extras:q.update(extras)
 props.append(q);placement_stats[name]=placement_stats.get(name,0)+1
 return q
# Exact canonical diagonal, reversed winding in native XYZ to make all terrain normals upward.
v=[(xmin+i*dx,-(zmin+j*dz),float(H[j,i])) for j in range(nz) for i in range(nx)];f=[]
for j in range(nz-1):
 for i in range(nx-1):a=j*nx+i;f.extend([(a,a+nx+1,a+1),(a,a+nx,a+nx+1)])
add('Highlands_Terrain','Highlands_Ground',v,f)
# Flat zero-height horizon apron matches the flattened grid edge and physics grace area.
xmax=xmin+(nx-1)*dx;ymax=-zmin;ymin=-(zmin+(nz-1)*dz);outer=6000
for vv in [[(-outer,-outer,0),(outer,-outer,0),(xmax,ymin,0),(xmin,ymin,0)],[(outer,-outer,0),(outer,outer,0),(xmax,ymax,0),(xmax,ymin,0)],[(outer,outer,0),(-outer,outer,0),(xmin,ymax,0),(xmax,ymax,0)],[(-outer,outer,0),(-outer,-outer,0),(xmin,ymin,0),(xmin,ymax,0)]]:add('Highlands_Terrain','Highlands_Ground',vv,[(0,1,2,3)])
# Six-lane divided highway, generous junction, then winding estate road.
for section in plan['road_sections']:
 a,b=section['startS'],section['endS']
 for strip in section['driveableStrips']:
  c=-strip['centerOffset'];w=strip['halfWidth'];sw=strip['shoulderHalfWidth'];ribbon('Highlands_Road','Highlands_Asphalt',a,b,c-w,c+w)
  ribbon('Highlands_Road','Highlands_GravelShoulder',a,b,c-sw,c-w,-.06,0);ribbon('Highlands_Road','Highlands_GravelShoulder',a,b,c+w,c+sw,0,-.06)
  for edge in [c-w+.16,c+w-.16]:ribbon('Highlands_Road','Highlands_WeatheredWhite',a+.2,b-.2,edge-.065,edge+.065,.012,.012)
  lanes=[c-1.75,c+1.75] if a<760 else ([0] if a>=820 else [])
  for l in lanes:
   for s in np.arange(a+2,b-2,12):ribbon('Highlands_Road','Highlands_WeatheredWhite' if a<760 else 'Highlands_SafetyYellow',s,min(s+4.5,b-.1),l-.055,l+.055,.014,.014)
# Low planted median and reference-inspired black/yellow kerbs, with a safe merge opening.
ribbon('Highlands_Furniture','Highlands_MedianPlanting',10,744,-8.5,-5.5,.15,.15)
for s in np.arange(14,734,22):
 hedge=[(-.95,.22),(-.85,.65),(-.45,.88),(.45,.88),(.85,.65),(.95,.22)]
 for (a,za),(b,zb) in zip(hedge,hedge[1:]):ribbon('Highlands_Furniture','Highlands_MedianPlanting',float(s),float(s+19),-7+a,-7+b,za,zb)
for s in np.arange(10,742,4):
 for l in [-8.6,-5.4]:
  p,t=at(s+2);q=offset(s+2,l,.29);box('Highlands_Furniture','Highlands_BarrierBlack' if int(s/4)%2 else 'Highlands_SafetyYellow',q,(3.98,.28,.58),math.atan2(t[1],t[0]))
for s in np.arange(10,744,16):capsule(float(s),min(float(s+16),744),-7,1.72,.60,'median')
# Highway outer black-yellow barriers, broken only near the entry/junction.
for l in [6.78,-20.78]:
 for s in np.arange(24,738,4):
  p,t=at(s+2);box('Highlands_Furniture','Highlands_SafetyYellow' if int(s/4)%2 else 'Highlands_BarrierBlack',offset(s+2,l,.32),(3.96,.28,.64),math.atan2(t[1],t[0]))
 for s in np.arange(24,738,16):capsule(float(s),min(float(s+16),738),l,.14,.64,'highway_edge')
# Yellow rumble strips are paint only, not physical speed bumps.
for c in [0,-14]:
 for center in [210,510,705]:
  for k in range(6):ribbon('Highlands_Road','Highlands_SafetyYellow',center+k*1.5,center+k*1.5+.24,c-4.9,c+4.9,.017,.017)
# Guardrail beams, repeated posts and authored continuous capsule colliders on hill road.
for l in [-4.95,4.95]:
 for s in np.arange(836,length-3,6):
  s1=min(s+6,length-3);a=offset(float(s),l,.86);b=offset(float(s1),l,.86);delta=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2;angle=math.atan2(delta.y,delta.x)
  # Thin horizontal two-sided steel section follows grade via eight end vertices.
  vv=[]
  for q in [a,b]:
   p,t=at(float(s if q==a else s1));n=(-t[1],t[0])
   for side,z in [(-.10,-.13),(.10,-.13),(.10,.13),(-.10,.13)]:vv.append((q[0]+n[0]*side,q[1]+n[1]*side,q[2]+z))
  add('Highlands_Furniture','Highlands_GuardrailMetal',vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
  p,t=at(float(s));box('Highlands_Furniture','Highlands_GuardrailMetal',offset(float(s),l,.44),(.12,.12,.88),math.atan2(t[1],t[0]))
 for s in np.arange(836,length-3,6):capsule(float(s),min(float(s+6),length-3),l,.12,1.0,'hill_guardrail')
# True 3D contour-following tea hedges. Each ring base samples the exact triangle mesh.
section=[(-1.05,0),(-1.15,.45),(-.75,.95),(0,1.12),(.75,.95),(1.15,.45),(1.05,0)]
for index,row in enumerate(tea['paths']):
 points=row['points'];vv=[]
 for k,(x,y) in enumerate(points):
  aa=points[max(0,k-1)];bb=points[min(len(points)-1,k+1)];tx,ty=bb[0]-aa[0],bb[1]-aa[1];ll=math.hypot(tx,ty);normal=(-ty/ll,tx/ll);noise=1+.045*math.sin(index*1.3+k*2.7)
  for lateral,up in section:
   xx=x+normal[0]*lateral;yy=y+normal[1]*lateral;vv.append((xx,yy,height(xx,yy)+up*noise+.015))
 fs=[];n=len(section)
 for k in range(len(points)-1):
  for j in range(n):fs.append((k*n+j,(k+1)*n+j,(k+1)*n+(j+1)%n,k*n+(j+1)%n))
 fs.extend([tuple(range(n)),tuple((len(points)-1)*n+j for j in reversed(range(n)))]);add('Highlands_Tea','Highlands_TeaCanopy_'+str(row['shade']),vv,fs)
# Instantiate original, reusable Blender vegetation. Road center remains clear.
prop_source=OUT/'Highland_Props.blend';env_source=ROOT/'assets/environment/Kerala_Coastal_Props.blend'
if not env_source.exists():
 candidates=list((ROOT/'assets/environment').glob('*.blend'));env_source=candidates[0]
# Names in original environment library are verified below; no geometry download.
with bpy.data.libraries.load(str(env_source),link=False) as (src,dst):environment_collections=set(src.collections)
for name in ['CoconutPalm_A','CoconutPalm_B']:
 if name not in environment_collections:raise RuntimeError(f'Palm {name} missing from {env_source}')
for s in np.arange(20,755,22):
 for l in [13,-28]:
  p=offset(float(s+rng.uniform(-3,3)),l+rng.uniform(-1.7,1.7));x,y=p[:2];place('CoconutPalm_A' if rng.random()<.55 else 'CoconutPalm_B',(x,y,height(x,y)),rng.uniform(0,math.tau),rng.uniform(.82,1.08),env_source)
# Shade trees both in tea estates and on the distant upper ridges, sparse beneath the crown.
cache=np.load(OUT/'terrain_cache.npz');D=cache['distance_to_route'];S=cache['near_s'];tree_count=0
for y in np.arange(100,1420,43):
 for x in np.arange(-130,1390,43):
  if rng.random()>.47:continue
  xx=float(x+rng.uniform(-16,16));yy=float(y+rng.uniform(-16,16));i=int(round((xx-xmin)/dx));j=int(round((-yy-zmin)/dz))
  if not(0<=i<nx and 0<=j<nz) or D[j,i]<12 or max(abs(xx-490),abs(yy-850))<55:continue
  h=height(xx,yy)
  if h<2 or h>175:continue
  scale=rng.uniform(.82,1.2);place('HighlandShadeTree',(xx,yy,h),rng.uniform(0,math.tau),scale,prop_source);obb((xx,yy,h+4.9*scale),(.6*scale,.6*scale,9.8*scale),0,'shade_tree_trunk','HighlandShadeTree');tree_count+=1
# Near-road rhythm: ten trees at lower estate boundaries and a few small roadside businesses.
for s in [880,1060,1340,1600,1900,2300,2640,2950,3370,3600]:
 p=offset(s,18 if int(s)%2 else -18);x,y=p[:2];scale=.93;place('HighlandShadeTree',(x,y,height(x,y)),.7,scale,prop_source);obb((x,y,height(x,y)+4.9*scale),(.6*scale,.6*scale,9.8*scale),0,'shade_tree_trunk','HighlandShadeTree')
# Gantry remains well above car clearance. Exact post and board OBBs support flight collisions.
p,t=at(690);angle=math.atan2(t[1],t[0]);place('HighlandGateway',p,angle,1,prop_source)
prop_manifest=json.loads((OUT/'highland_prop_manifest.json').read_text())
for q in prop_manifest['assets']['HighlandGateway']['collision_boxes_blender']:
 c=q['center_blender'];cc=(p[0]+math.cos(angle)*c[0]-math.sin(angle)*c[1],p[1]+math.sin(angle)*c[0]+math.cos(angle)*c[1],p[2]+c[2]);obb(cc,q['size_blender'],angle,q['kind'],'HighlandGateway')
urban=ROOT/'assets/infrastructure/urban/native'
for idx,s in enumerate([80,175,315,455,610,875,1590,2350,3350]):
 name='KeralaShopRow_B' if s<760 else 'KeralaTeaStall';dims=(10,9,7) if s<760 else (4,3,3.2);l=-35 if s<760 else 17;p,t=at(s);x,y,_=offset(s,l);angle=math.atan2(t[1],t[0])+(0 if l>0 else math.pi);corners=[]
 for xx in [-dims[0]/2,dims[0]/2]:
  for yy in [-dims[1]/2,dims[1]/2]:corners.append(height(x+math.cos(angle)*xx-math.sin(angle)*yy,y+math.sin(angle)*xx+math.cos(angle)*yy))
 floor=max(corners)+.09;bottom=min(corners)-.12;box('Highlands_Furniture','Highlands_FoundationStone',(x,y,(floor+bottom)/2),(dims[0]+.5,dims[1]+.5,floor-bottom),angle);place(name,(x,y,floor),angle,1,urban/(name+'.blend'),{'facade_color':['#e5d7b5','#c2d9db','#d9bb80'][idx%3],'accent_color':['#9b5d3c','#516b75','#7e6c43'][idx%3]});obb((x,y,(floor+bottom+dims[2])/2),(dims[0],dims[1],dims[2]+floor-bottom),angle,'estate_building',name)
# Original reclining bird landmark: source-author supplied upper-body and rock proxies.
land_source=ROOT/'assets/landscape_reference_kit/BirdRockLookout.blend';land_manifest=ROOT/'assets/landscape_reference_kit/BirdRockLookout_manifest.json'
if not land_source.exists() or not land_manifest.exists():raise RuntimeError('BirdRock source must be ready before final export')
land=plan['landmark_plan'];lp=land['location_blender_m'];la=math.radians(land['yaw_deg']);place('BirdRockLookout',lp,la,1,land_source)
lm=json.loads(land_manifest.read_text());(OUT/'bird_manifest_input.json').write_text(json.dumps(lm,indent=2))
# Supports both explicit center/size and the source kit's named OBB schema.
proxies=lm.get('collision_proxies',lm.get('collision_boxes_blender',[]))
if not proxies:raise RuntimeError('Bird landmark collision manifest needs authored solid proxies')
for q in proxies:
 if q.get('type')=='obb':
  c=q['center_local_m'];e=q['half_extents_m'];c=[c[0],-c[2],c[1]];sz=[e[0]*2,e[2]*2,e[1]*2];cc=(lp[0]+math.cos(la)*c[0]-math.sin(la)*c[1],lp[1]+math.sin(la)*c[0]+math.cos(la)*c[1],lp[2]+c[2]);obb(cc,sz,la,'bird_'+q['part'],'BirdRockLookout')
 elif q.get('type')=='capsule':
  aa,bb=q['a_local_m'],q['b_local_m'];r=q['radius_m']
  def bird_xz(c):
   x,y=c[0],-c[2];return(lp[0]+math.cos(la)*x-math.sin(la)*y,-(lp[1]+math.sin(la)*x+math.cos(la)*y))
  aa2,bb2=bird_xz(aa),bird_xz(bb);infra.append({'id':f'highlands-bird-{len(infra)}','asset':'BirdRockLookout','kind':'bird_'+q['part'],'shape':'capsule','x':aa2[0],'z':aa2[1],'endX':bb2[0],'endZ':bb2[1],'radius':r,'y':lp[2]+min(aa[1],bb[1])-r,'height':abs(aa[1]-bb[1])+2*r})
 else:raise RuntimeError(f'Unsupported bird proxy schema: {q}')
# Spatial chunks keep real terrain/tea/furniture frustum-cullable on mobile GPUs.
# Material sharing is retained; each chunk contains only nearby vertices.
chunked={}
for (group,mname),(vertices,faces) in batches.items():
 local={}
 for face in faces:
  cx=sum(vertices[i][0] for i in face)/len(face);cy=sum(vertices[i][1] for i in face)/len(face);key=(math.floor(cx/256),math.floor(cy/256));bucket=local.setdefault(key,[[],[],{}]);newface=[]
  for i in face:
   if i not in bucket[2]:bucket[2][i]=len(bucket[0]);bucket[0].append(vertices[i])
   newface.append(bucket[2][i])
  bucket[1].append(tuple(newface))
 for key,(vv,ff,_) in local.items():chunked[(group,mname,key)]=[vv,ff]
batches=chunked
# Create editable native component meshes. Terrain and foliage smoothing is authored, not inferred by the renderer.
for (group,mname,chunk),(verts,faces) in batches.items():
 me=bpy.data.meshes.new(group+'_'+mname+'_'+str(chunk));me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(group+'_'+mname,me);scene.collection.objects.link(o);me.materials.append(M[mname]);groups.setdefault(group,[]).append(o)
 if group in ['Highlands_Terrain','Highlands_Tea']:
  for p in me.polygons:p.use_smooth=True
 o['provenance']='Original procedural Blender geometry; see blender/build_highlands.py';o['runtime_group']=group
 # Explicitly triangulate and remove zero-area caps to make exported triangle QA reproducible.
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-8]
 if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
 bm.normal_update();bm.to_mesh(me);bm.free();me.update()
 # Smooth terrain color variation gives actual art variation without downloaded photo textures.
 if group=='Highlands_Terrain':
  col=me.color_attributes.new(name='TerrainColor',type='FLOAT_COLOR',domain='POINT')
  for i,vtx in enumerate(me.vertices):
   x,y,z=vtx.co;shade=.82+.11*math.sin(x*.018)*math.cos(y*.016)+.04*math.sin(x*.07+y*.03);col.data[i].color=(shade,min(1,shade+.04),max(.65,shade-.03),1)
  normals=[]
  for vtx in me.vertices:
   x,y,z=vtx.co
   if xmin<=x<=xmax and ymin<=y<=ymax:
    gx=(height(x+1,y)-height(x-1,y))/2;gy=(height(x,y+1)-height(x,y-1))/2;n=Vector((-gx,-gy,1)).normalized();normals.append(tuple(n))
   else:normals.append((0,0,1))
  me.normals_split_custom_set_from_vertices(normals)
  nodes=M[mname].node_tree.nodes;links=M[mname].node_tree.links
  if not nodes.get('TerrainVertexTint'):
   vc=nodes.new('ShaderNodeVertexColor');vc.name='TerrainVertexTint';vc.layer_name='TerrainColor';mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=M[mname].diffuse_color;links.new(vc.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
scene.world.color=(.55,.7,.8);scene['description']=plan['description'];scene['height_grid_contract']='terrain_grid sw-ne exact planar triangles; no implicit hill bridge';scene['reference_files']=';'.join(plan['reference_files'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Highland_Run.blend'))
manifest={'name':'Highland Run','license':'Original procedural geometry. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.  existing original props retain their source manifests.','route_length_m':length,'max_grade':plan['max_grade'],'terrain_grid_count':grid['count'],'tea_row_count':len(tea['paths']),'tea_total_length_m':tea['total_row_length_m'],'placement_counts':placement_stats,'mesh_files':{},'geometry_source':'blender/build_highlands.py','route_source':'blender/plan_highlands.py','tea_source':'blender/plan_highland_tea.py','notes':plan['provenance']}
for group,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 path=WEB/(group+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
 manifest['mesh_files'][path.name]={'bytes':path.stat().st_size,'triangles':sum(len(p.vertices)-2 for o in objects for p in o.data.polygons),'draws':len(objects),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};shutil.copy2(path,PUBLIC/path.name)
# Runtime fields stay at ROOT; no coastal metadata, water plane or OSM attribution is implied.
checkpoints=[]
for s in np.arange(125,length,125):p,t=at(float(s));checkpoints.append({'s':float(s),'position':[p[0],p[2],-p[1]],'yaw_rad':-math.atan2(t[1],t[0])})
runtime={'name':'Highland Run','id':'highlands','version':'v9-original-highlands','description':plan['description'],'fictional_geography_notice':plan['description'],'source_route_length_m':length,'smoothed_length_m':length,'route_elevation':'Earth-supported climb from0.18m to100.18m; maximum authored grade5.34%.','axes':'Three.js X east/Y up/Z south, metres','coordinate_conversion_note':'Blender [x,y,z] -> Three [x,z,-y]; yaw sign flips.','route_points':[[p[0],p[2],-p[1]] for p in route],'horizontal_route_distances_m':dist,'road_sections':plan['road_sections'],'elevated_corridors':[],'terrain_grid':grid,'course_meshes':[{'name':g,'file':g+'.glb','collision':g!='Highlands_Tea'} for g in groups],'prop_instances':props,'checkpoints':checkpoints,'collision_file':'highlands_infrastructure_colliders.json','furniture_file':'highlands_furniture_colliders.json','districts':plan['districts'],'transit_routes':[],'garage_s':plan['garage_s'],'event_slices':plan['event_slices'],'explore_starts':[{'name':d['name'],'s':d['start_s']+30} for d in plan['districts']],'minimap_roads':[[[offset(float(s),l)[0],offset(float(s),l)[2],-offset(float(s),l)[1]] for s in np.arange(0,761,6)] for l in [0,-14]],'materials':{},'world':{'geography':'Original fictional tea-estate setting, intentionally separate from the coastal OSM map.'}}
for name,data in [('course_runtime_highlands.json',runtime),('highlands_infrastructure_colliders.json',{'colliders':infra,'count':len(infra),'source':'Original Blender placement/proxy generation; buildings/tree trunks/gantry and bird solids.'}),('highlands_furniture_colliders.json',{'colliders':furniture,'count':len(furniture),'source':'Continuous original median/highway-edge/hill-rail capsules; no bead chains.'}),('highlands_terrain_grid.json',grid),('highlands_manifest.json',manifest)]:
 for parent in [OUT,WEB,PUBLIC]:(parent/name).write_text(json.dumps(data,separators=(',',':')))
print('HIGHLANDS_EXPORT_READY',json.dumps({'route_length':length,'grade':plan['max_grade'],'props':len(props),'infra':len(infra),'furniture':len(furniture),'meshes':manifest['mesh_files']},indent=2))
