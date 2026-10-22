"""Original Blender-built OSM-derived Kappil course and staged coastal preview.
OSM centerline/coast/water geometry: © OpenStreetMap contributors, ODbL.
Elevation, road width, buildings, vegetation, styling and race furniture are artistic.
Run: blender -b --factory-startup -t 4 --python blender/build_course.py [-- --render]
"""
import bpy, bmesh, math, json, random, sys
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon, delaunay_2d_cdt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/course';OUT.mkdir(parents=True,exist_ok=True)
random.seed(267)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Kappil_Coast';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
route=json.loads((ROOT/'references/route/kappil_route_local_meters.json').read_text());raw=[Vector(p) for p in route['points']]
# Catmull-Rom smoothing is an artistic driving surface derived from the source line.
def cat(a,b,c,d,t):return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
points=[]
for k in range(len(raw)-1):
 a,b,c,d=raw[max(0,k-1)],raw[k],raw[k+1],raw[min(len(raw)-1,k+2)]
 for j in range(max(2,int((c-b).length/3))):points.append(cat(a,b,c,d,j/max(2,int((c-b).length/3))))
points.append(raw[-1])
# Uniform arc-length samples avoid sharp ribbon normals where OSM node spacing varies.
_tmp=[0]
for a,b in zip(points,points[1:]):_tmp.append(_tmp[-1]+(b-a).length)
import bisect
_uniform=[]
for ss in [i*3.0 for i in range(int(_tmp[-1]/3))]+[_tmp[-1]]:
 ii=min(len(points)-2,max(0,bisect.bisect_right(_tmp,ss)-1));_uniform.append(points[ii].lerp(points[ii+1],(ss-_tmp[ii])/max(.001,_tmp[ii+1]-_tmp[ii])))
points=_uniform
for _ in range(3):
 points=[points[0]]+[sum((points[min(len(points)-1,max(0,i+j))]*w for j,w in [(-2,1),(-1,2),(0,3),(1,2),(2,1)]),Vector())/9 for i in range(1,len(points)-1)]+[points[-1]]
dist=[0]
for a,b in zip(points,points[1:]):dist.append(dist[-1]+(b-a).length)
def road_height(s):
 def sm(t):return t*t*(3-2*t)
 if s<2480 or s>3010:return .18
 if s<2630:return .18+9.82*sm((s-2480)/150)
 if s<=2860:return 10.
 return .18+9.82*(1-sm((s-2860)/150))
def sample(s):
 import bisect
 i=min(len(points)-2,max(0,bisect.bisect_right(dist,s)-1));f=(s-dist[i])/max(.001,dist[i+1]-dist[i]);p=points[i].lerp(points[i+1],f);v=(points[i+1]-points[i]).normalized();return p,v,Vector((-v.y,v.x,0))
def material(name,c,rough=.6,metal=0,noise=0,bump=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=noise;n.inputs['Detail'].default_value=3
  ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(v*.7 for v in c),1);ramp.color_ramp.elements[1].color=(*(min(1,v*1.22) for v in c),1);m.node_tree.links.new(n.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
  if bump:
   bn=m.node_tree.nodes.new('ShaderNodeBump');bn.inputs['Strength'].default_value=bump;bn.inputs['Distance'].default_value=.06;m.node_tree.links.new(n.outputs['Fac'],bn.inputs['Height']);m.node_tree.links.new(bn.outputs[0],p.inputs['Normal'])
 return m
asphalt=material('Course_Asphalt',(.045,.052,.049),.81,noise=70,bump=.24)
paint=material('Course_WeatheredWhite',(.87,.85,.71),.65,noise=65,bump=.1)
sand=material('Course_GoldenSand',(.62,.48,.27),.95,noise=38,bump=.25)
grass=material('Course_TropicalGround',(.13,.22,.045),.95,noise=4,bump=.3)
water=material('Course_IndianOcean',(.013,.19,.23),.19,.3,noise=.33,bump=.28)
foam=material('Course_SurfFoam',(.77,.87,.78),.65,noise=4,bump=.4)
stone=material('Course_BridgeConcrete',(.33,.35,.32),.85,noise=9,bump=.25)
rail=material('Course_Railing',(.78,.8,.73),.55,.12)
yellow=material('Course_SafetyOchre',(.92,.55,.05),.7)
dark=material('Course_RaceGraphite',(.015,.03,.033),.35,.2)
mint=material('Course_RaceMint',(.035,.68,.43),.35,.1)
course=[];placements=[];placement_objects=[]
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.normal_update()
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-9],context='FACES')
 for face in bm.faces:
  if face.normal.z<0:face.normal_flip()
 bm.to_mesh(me);bm.free();me.update();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);ob.data.materials.append(mat);course.append(ob);return ob
def ribbon(name,a,b,z,mat,start=0,end=None,step=3):
 end=dist[-1] if end is None else end;ss=[start+i*step for i in range(int((end-start)/step)+1)];ss+=([end] if abs(ss[-1]-end)>1e-6 else []);vs=[];fs=[]
 for s in ss:
  p,t,n=sample(s);vs.extend([tuple(p+n*a+Vector((0,0,z+road_height(s)-.18))),tuple(p+n*b+Vector((0,0,z+road_height(s)-.18)))])
 for i in range(len(ss)-1):fs.append((2*i,2*i+1,2*i+3,2*i+2))
 return mesh(name,vs,fs,mat)
# Road follows OSM, flattened artistic elevation .18m, lane width 3.5m.
ribbon('Road_Surface',3.6,-3.6,.18,asphalt)
ribbon('Road_LeftShoulder',4.6,3.6,.12,sand);ribbon('Road_RightShoulder',-3.6,-4.6,.12,sand)
ribbon('Road_Edge_Left',3.36,3.24,.188,paint);ribbon('Road_Edge_Right',-3.24,-3.36,.188,paint)
# Dashed center line: individual strips, joined at export to preserve low object count.
for s in range(0,int(dist[-1])-4,9):ribbon('CenterDash',.055,-.055,.192,paint,s,s+4,2)
# Actual OSM coast and water outlines in local equirectangular coordinates.
lon0,lat0=route['origin_wgs84_lon_lat'];earth=6371000
project=lambda q:Vector(((q[0]-lon0)*math.pi/180*earth*math.cos(lat0*math.pi/180),(q[1]-lat0)*math.pi/180*earth,0))
features=json.loads((ROOT/'references/route/kappil_osm_environment.geojson').read_text())['features']
coast=[]
for f in features:
 if f['properties'].get('natural')=='coastline':coast.extend(project(p) for p in f['geometry']['coordinates'])
coast.sort(key=lambda p:p.y)
# Coast beyond extracted data extent is linearly extended and explicitly artistic.
if coast[-1].y<6000:
 v=(coast[-1]-coast[-2]).normalized();coast.append(coast[-1]+v*((6200-coast[-1].y)/v.y))
if coast[0].y>-500:
 v=(coast[1]-coast[0]).normalized();coast.insert(0,coast[0]-v*((coast[0].y+500)/v.y))
def inside(p,poly):
 hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a.y>p.y)!=(b.y>p.y) and p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x:hit=not hit
 return hit
water_shapes=[[project(q) for q in f['geometry']['coordinates'][0][:-1]] for f in features if f['properties'].get('natural')=='water' and f['geometry']['type']=='Polygon']
def polygon(name,coords,z,mat,holes=None):
 # Treat every outer/lake boundary as a planar constraint. tessellate_polygon's
 # multi-loop output can bridge across unrelated water rings and lose large land
 # areas when centroid-filtered. CDT splits at all constraints first, so this
 # classification retains every dry triangle and exact shoreline holes.
 if holes:
  vertices=[];edges=[]
  for loop in [coords]+holes:
   start=len(vertices);vertices.extend(Vector((p.x,p.y)) for p in loop)
   edges.extend((start+i,start+(i+1)%len(loop)) for i in range(len(loop)))
  vertices,_,faces,*_=delaunay_2d_cdt(vertices,edges,[],0,1e-5,False)
  dry=[]
  for face in faces:
   center=sum((vertices[i] for i in face),Vector((0,0)))/len(face)
   if inside(center,coords) and not any(inside(center,h) for h in holes):dry.append(face)
  return mesh(name,[(p.x,p.y,z) for p in vertices],dry,mat)
 loops=[[Vector((v.x,v.y,z)) for v in coords]]
 if holes:loops.extend([[Vector((v.x,v.y,z)) for v in h] for h in holes])
 ps=sum(loops,[]);tris=tessellate_polygon(loops);vs=[];fs=[]
 for tri in tris:
  tri=[ps[v] if isinstance(v,int) else v for v in tri]
  if holes and any(inside(sum(tri,Vector())/3,h) for h in holes):continue
  fs.append(tuple(range(len(vs),len(vs)+3)));vs.extend([tuple(v) for v in tri])
 return mesh(name,vs,fs,mat)
land_outline=coast+[Vector((4500,coast[-1].y,0)),Vector((4500,coast[0].y,0))]
polygon('Coastal_Terrain',land_outline,-.04,grass,water_shapes)
polygon('Arabian_Sea',coast+[Vector((-6500,coast[-1].y,0)),Vector((-6500,coast[0].y,0))],-.18,water)
# Continuous sandy coastline / surf, directly derived from OSM line; no invented route coastline.
for name,a,b,z,mat in [('Beach',0,24,-.015,sand),('WetSand',-4,0,-.09,sand),('Surf',-7,-4,-.11,foam)]:
 vs=[];fs=[]
 for i,p in enumerate(coast):
  v=(coast[min(i+1,len(coast)-1)]-coast[max(0,i-1)]).normalized();inland=Vector((v.y,-v.x,0));vs.extend([tuple(p+inland*a+Vector((0,0,z))),tuple(p+inland*b+Vector((0,0,z)))])
 for i in range(len(coast)-1):fs.append((i*2,i*2+1,i*2+3,i*2+2))
 mesh(name,vs,fs,mat)
for f in features:
 if f['properties'].get('natural')=='water' and f['geometry']['type']=='Polygon':
  ps=[project(q) for q in f['geometry']['coordinates'][0]];polygon('OSM_Water_'+f['properties']['osm_way_id'],ps,.015,water)
# Append reusable Blender collections without linking their source originals to the scene.
asset_names=['CoconutPalm_A','CoconutPalm_B','KeralaHouse','FishingBoat','RoadReflector','TropicalGrass','SeaWallRock']
with bpy.data.libraries.load(str(ROOT/'assets/environment/Kerala_Coastal_Assets.blend'),link=False) as (src,dst):dst.collections=[n for n in asset_names if n in src.collections]
collections={c.name:c for c in dst.collections}
def instance(name,pos,angle=0,scale=1,record=True):
 ob=bpy.data.objects.new(name+'_Instance',None);ob.instance_type='COLLECTION';ob.instance_collection=collections[name];scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler[2]=angle;ob.scale=(scale,scale,scale)
 if record:placements.append({'asset':name,'location_m':list(pos),'yaw_deg':math.degrees(angle),'scale':scale});placement_objects.append(ob)
 return ob
# Keep road corridor unobstructed. Vegetation/props are artistic, not a survey.
for s in range(20,int(dist[-1])-10,17):
 p,t,n=sample(s)
 for side in [-1,1]:
  if random.random()<.23:continue
  offset=side*random.uniform(7.8,20);v=p+n*offset;v.z=0
  # Do not plant in the actual bridge waterway interval.
  if any(inside(v,h) for h in water_shapes) or not inside(v,land_outline):continue
  instance(random.choice(['CoconutPalm_A','CoconutPalm_B']),v,random.random()*6.28,random.uniform(.78,1.15))
  if s%34==20:instance('TropicalGrass',p+n*side*random.uniform(5.4,7.4),random.random()*6.28,random.uniform(.8,1.8))
for s in range(12,int(dist[-1]),28):
 p,t,n=sample(s)
 for side in [-1,1]:instance('RoadReflector',p+n*(4.15*side),math.atan2(t.y,t.x))
for s in range(140,int(dist[-1])-80,230):
 p,t,n=sample(s);instance('KeralaHouse',p-n*random.uniform(16,30),math.atan2(t.y,t.x)+math.pi/2,random.uniform(.85,1.1))
for s in [500,760,1030,1300,2170]:
 p,t,n=sample(s);instance('FishingBoat',p+n*24,math.atan2(t.y,t.x)+.55,.85)
# Secondary original Blender vegetation, concentrated on the playable coastal leg.
# Independent RNG and append-only records preserve every pre-existing prop/collider.
# A footprint ring must be on dry OSM land and clear of the entire road, not only
# its current local sample. These placements are artistic landscaping, not OSM data.
vegetation_rng=random.Random(812206)
vegetation_start=len(placements)
def road_clearance_xy(p):
 best=1e30
 for a,b in zip(points,points[1:]):
  vx=b.x-a.x;vy=b.y-a.y;den=vx*vx+vy*vy
  f=max(0,min(1,((p.x-a.x)*vx+(p.y-a.y)*vy)/max(1e-12,den)))
  best=min(best,(p.x-a.x-f*vx)**2+(p.y-a.y-f*vy)**2)
 return math.sqrt(best)
def dry_footprint(p,radius):
 ring=[p]+[p+Vector((math.cos(i*math.pi/4)*radius,math.sin(i*math.pi/4)*radius,0)) for i in range(8)]
 return all(inside(q,land_outline) and not any(inside(q,h) for h in water_shapes) for q in ring)
def add_landscaping(name,p,angle,scale):
 instance(name,p,angle,scale)
 placements[-1]['placement_pass']='coastal_dry_land_detail_2026_10_22'
for s in range(2200,min(4350,int(dist[-1])-10),19):
 p,t,n=sample(s)
 for side in [-1,1]:
  if vegetation_rng.random()>.83:continue
  center=p+n*side*vegetation_rng.uniform(7.0,10.5)
  for _ in range(vegetation_rng.randint(2,4)):
   scale=vegetation_rng.uniform(.72,1.8)
   q=center+t*vegetation_rng.uniform(-3.5,3.5)+n*vegetation_rng.uniform(-1.2,2.2);q.z=0
   if road_clearance_xy(q)<4.95+.75*scale or not dry_footprint(q,.75*scale):continue
   add_landscaping('TropicalGrass',q,vegetation_rng.uniform(0,math.tau),scale)
occupied=[(Vector(r['location_m']),6.0 if r['asset'].startswith('CoconutPalm') else 11.0) for r in placements[:vegetation_start] if r['asset'].startswith('CoconutPalm') or r['asset']=='KeralaHouse']
for s in range(2208,min(4350,int(dist[-1])-10),25):
 p,t,n=sample(s)
 for side in [-1,1]:
  if vegetation_rng.random()>.72:continue
  q=p+n*side*vegetation_rng.uniform(17,43)+t*vegetation_rng.uniform(-6,6);q.z=0
  scale=vegetation_rng.uniform(.73,1.07)
  if road_clearance_xy(q)<9.2 or not dry_footprint(q,1.6*scale):continue
  if any((q-v).length<r for v,r in occupied):continue
  add_landscaping(vegetation_rng.choice(['CoconutPalm_A','CoconutPalm_B']),q,vegetation_rng.uniform(0,math.tau),scale)
  occupied.append((q,6.0))
print('DRY_LAND_DETAIL',len(placements)-vegetation_start,'new instances')
# Blender-built race checkpoint arches are fictional installations on a closed game road.
def cube(name,pos,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);be=o.modifiers.new('Soft edges','BEVEL');be.width=.06;be.segments=2;course.append(o);return o
exec((ROOT/'blender/assemble_v8_districts.py').read_text(),globals())
checkpoints=[]
for k,s in enumerate(list(range(0,int(dist[-1]),150))+[dist[-1]]):
 p,t,n=sample(s);p.z=road_height(s);checkpoints.append(list(p));yaw=math.atan2(t.y,t.x)
 if k%4==0 or s==dist[-1]:
  for side in [-1,1]:
   o=cube('Gate_Pillar',p+n*side*4.9+Vector((0,0,2.5)),(.45,.45,5),dark);o.rotation_euler[2]=yaw
   o=cube('Gate_Mint',p+n*side*4.9+Vector((0,0,2.5)),(.47,.49,.3),mint);o.rotation_euler[2]=yaw
  o=cube('Gate_Crossbar',p+Vector((0,0,5)),(.48,10.25,.6),dark);o.rotation_euler[2]=yaw
# Source bridge route range is set after research validation; mesh based on OSM way vertices.
roads=json.loads((ROOT/'references/route/kappil_osm_roads.geojson').read_text())['features']
for f in roads:
 if str(f['properties'].get('osm_way_id'))=='239443918':
  coords=[project(q) for q in f['geometry']['coordinates']];a,b=coords[0],coords[-1];v=(b-a).normalized();n=Vector((-v.y,v.x,0));length=(b-a).length;yaw=math.atan2(v.y,v.x)
  for side in [-1,1]:
   for z in [.45,1.1]:
    o=cube('Bridge_Rail',(a+b)/2+n*side*4.2+Vector((0,0,z)),(length,.18,.15),rail);o.rotation_euler[2]=yaw
   for j in range(int(length/3)+1):
    p=a+v*j*3+n*side*4.2+Vector((0,0,.65));o=cube('Bridge_Post',p,(.17,.17,1.2),stone);o.rotation_euler[2]=yaw
# Export collision-separated groups; water must never become a drivable hull.
groups={'Course_Road':[], 'Course_Terrain':[], 'Course_Water':[], 'Course_Furniture':[]}
for o in course:
 name=o.name
 if name.startswith(('Road_','CenterDash')):key='Course_Road'
 elif name.startswith(('Arabian_Sea','OSM_Water_','Surf')):key='Course_Water'
 elif name.startswith(('Coastal_Terrain','Beach','WetSand')):key='Course_Terrain'
 else:key='Course_Furniture'
 groups[key].append(o)
for key,objects in groups.items():
 if '--terrain-refresh' in sys.argv and key!='Course_Terrain':continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.fbx(filepath=str(OUT/(key+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,axis_forward='X',axis_up='Z',use_mesh_modifiers=True,bake_anim=False)
# Manifest keeps placement in Blender basis. Unreal bootstrap performs a documented axis conversion.
manifest={'name':'Kappil Coast','source_route_length_m':route['length_m_approx'],'smoothed_length_m':dist[-1],'axes':'Blender +X east,+Y north,+Z up; meters','route_elevation':'artistic .18 m base with a smooth 10 m flyover; NOT surveyed','osm_attribution':'© OpenStreetMap contributors / ODbL; see references/route/README.md','course_meshes':[{'name':k,'file':k+'.fbx','collision':k!='Course_Water'} for k in groups],'route_points_m':[list(p+Vector((0,0,road_height(dist[i])))) for i,p in enumerate(points)],'checkpoints_m':checkpoints,'prop_instances':placements,'materials':{m.name:{'base_color':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value} for m in [asphalt,paint,sand,grass,water,foam,stone,rail,yellow,dark,mint]}}
manifest.update({'world':world_metadata,'elevation_profile':elevation_profile,'elevated_corridors':elevated_corridors,'horizontal_route_distances_m':dist,'collision_file':world_metadata['collision_file']})
manifest.update({k:world_metadata[k] for k in ['districts','transit_routes','collision_file','fictional_geography_notice']})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
# Pose car at scenic middle course, replacing original root transform only; every mesh remains articulated.
with bpy.data.libraries.load(str(ROOT/'assets/car/roadster_concept.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n=='CAR_ROOT' or n.startswith(('Body','Wheel','Steer','Spin'))] if False else list(src.objects)
carobjects=[o for o in dst.objects if o and o.type not in {'CAMERA','LIGHT'}]
carcollection=bpy.data.collections.new('Hero_Car');scene.collection.children.link(carcollection)
for o in carobjects:carcollection.objects.link(o)
carroot=bpy.data.objects.get('CAR_ROOT');heroS=2550
p,t,n=sample(heroS);yaw=math.atan2(t.y,t.x)
if carroot:carroot.location=p-n*1.65+Vector((0,0,road_height(heroS)));carroot.rotation_euler=(0,-math.atan2(road_height(heroS+1)-road_height(heroS-1),2),yaw)
# Sky and sun designed for coastal golden hour with readable material color.
world=bpy.data.worlds.new('Kerala_Coastal_Sky');scene.world=world;world.use_nodes=True;nodes=world.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputWorld');bg=nodes.new('ShaderNodeBackground');sky=nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=.38;sky.sun_rotation=2.2;sky.air_density=1.1;sky.dust_density=1.7;bg.inputs['Strength'].default_value=.28;world.node_tree.links.new(sky.outputs[0],bg.inputs[0]);world.node_tree.links.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=bpy.context.object;sun.name='Coastal_LateAfternoon';sun.rotation_euler=(.45,-.4,-.7);sun.data.energy=1.3;sun.data.angle=.075
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Hero_Camera';scene.camera=cam;target=p-n*1.65+Vector((0,0,road_height(heroS)+.75));cam.location=target+t*9-n*8+Vector((0,0,1.8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=36;cam.data.clip_end=10000
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=128;scene.cycles.use_denoising=False;scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'renders/coast_hero.png');scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-1.1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Kappil_Coast.blend'))
if '--render' in sys.argv:bpy.ops.render.render(write_still=True)
print('COURSE_READY',len(points),'route samples',len(placements),'prop instances',len(checkpoints),'checkpoints')
