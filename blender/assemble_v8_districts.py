"""Executed by build_course.py after the original vegetation pass and cube helper.
Appends original Blender infrastructure, clears intersecting old landscaping,
constructs the graded flyover volume and exports simple oriented collision proxies.
"""
layout=json.loads((OUT/'v8_world_layout.json').read_text());world_metadata=layout['world'];elevation_profile=layout['elevation_profile'];elevated_corridors=layout['elevated_corridors']
world_metadata['transit_axes']='Three.js X east,Y up,-Z north; transit points already converted.'
# Append collection references: source architecture remains editable and instanced.
transit_manifest=json.loads((ROOT/'assets/infrastructure/transit/manifest.json').read_text())
with bpy.data.libraries.load(str(ROOT/'assets/infrastructure/transit/Kerala_Transit_Infrastructure.blend'),link=False) as (src,dst):dst.collections=list(transit_manifest['assets'])
for c in dst.collections:collections[c.name]=c
urban_manifest=json.loads((ROOT/'assets/infrastructure/urban/urban_assets_manifest.json').read_text());urban_assets={a['name']:a for a in urban_manifest['assets']}
for name in urban_assets:
 with bpy.data.libraries.load(str(ROOT/'assets/infrastructure/urban/native'/(name+'.blend')),link=False) as (src,dst):dst.collections=[name]
 collections[name]=dst.collections[0]

if any(p['asset']=='KeralaHouseboat' for p in layout['new_prop_instances']):
 with bpy.data.libraries.load(str(ROOT/'assets/infrastructure/backwater/KeralaHouseboat.blend'),link=False) as (src,dst):dst.collections=['KeralaHouseboat']
 collections['KeralaHouseboat']=dst.collections[0]

def v8nearest(p):
 best=(1e30,0)
 for k,(a,b) in enumerate(zip(points,points[1:])):
  d=b-a;f=max(0,min(1,(p-a).dot(d)/max(1e-12,d.length_squared)));distance=(p-a-d*f).length_squared
  if distance<best[0]:best=(distance,dist[k]+f*(dist[k+1]-dist[k]))
 return math.sqrt(best[0]),best[1]
def v8_reserved_hit(p,margin):
 for r in layout['reserved_footprints']:
  x=p.x-r['center'][0];y=p.y-r['center'][1];a=r['yaw'];u=x*math.cos(a)+y*math.sin(a);v=-x*math.sin(a)+y*math.cos(a)
  if abs(u)<r['hx']+margin and abs(v)<r['hy']+margin:return True
 return False
old_count=len(placements);kept=[];kept_objects=[];removed=[]
for r,o in zip(placements,placement_objects):
 p=Vector(r['location_m']);asset=r['asset'];remove=False
 if asset!='RoadReflector':
  margin=5.5 if asset=='KeralaHouse' else (2.2 if asset.startswith('CoconutPalm') else .6)
  remove=v8_reserved_hit(p,margin)
  if asset.startswith('CoconutPalm'):
   nearest,s=v8nearest(p)
   if 2460<s<3030 and nearest<10:remove=True
 if remove:removed.append(r);bpy.data.objects.remove(o,do_unlink=True);continue
 if asset=='RoadReflector':
  _,s=v8nearest(p);lift=road_height(s)-.18;r['location_m'][2]+=lift;o.location.z+=lift
 kept.append(r);kept_objects.append(o)
placements[:]=kept;placement_objects[:]=kept_objects
infrastructure_colliders=[]
def v8_box_proxy(tag,location,angle,scale,center,size,kind):
 local=Vector(center)*scale;world=Vector(location)+Vector((local.x*math.cos(angle)-local.y*math.sin(angle),local.x*math.sin(angle)+local.y*math.cos(angle),local.z));sx,sy,sz=[v*scale for v in size]
 infrastructure_colliders.append({'id':tag,'kind':kind,'shape':'box','x':world.x,'z':-world.y,'radius':math.hypot(sx/2,sy/2),'halfLength':sx/2,'halfWidth':sy/2,'heading':-angle,'y':world.z-sz/2,'height':sz})
for index,r in enumerate(layout['new_prop_instances']):
 name=r['asset'];angle=math.radians(r['yaw_deg']);o=instance(name,Vector(r['location_m']),angle,r['scale'])
 for k,v in r.items():
  if k not in ['asset','location_m','yaw_deg','scale']:placements[-1][k]=v;o[k]=v
 if name in transit_manifest['assets']:
  for j,b in enumerate(transit_manifest['assets'][name]['collision_boxes_blender']):v8_box_proxy(f'v8-{name}-{index}-{j}',r['location_m'],angle,r['scale'],b['center_blender'],b['size_blender'],b['kind'])
 elif name=='KeralaHouseboat':
  v8_box_proxy(f'v8-houseboat-{index}',r['location_m'],angle,r['scale'],[0,0,2.533],[18.1,5.25,6.566],'moored_houseboat')
 elif name in urban_assets:
  a=urban_assets[name];bounds=a['bounds_blender'];lo=bounds['min'];hi=bounds['max'];center=[(lo[k]+hi[k])/2 for k in range(3)];size=[hi[k]-lo[k] for k in range(3)]
  if name=='ChineseFishingNet':
   # Netting/boom is not a giant solid box: only two timber foundation posts.
   for j,(x,y) in enumerate([(x,y) for x in [-2.45,2.45] for y in [2.55,8.65]]):v8_box_proxy(f'v8-net-foundation-{index}-{j}',r['location_m'],angle,r['scale'],[x,y,1.125],[.28,.28,2.25],'fishing_net_post')
  else:v8_box_proxy(f'v8-building-{index}',r['location_m'],angle,r['scale'],center,size,'building')
world_metadata['original_prop_count']=old_count;world_metadata['removed_intersecting_original_props']=len(removed);world_metadata['total_prop_instances']=len(placements)

# Proper closed solid normals, unlike the flat terrain helper's upward-only policy.
def v8_solid(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.data.materials.append(mat);course.append(o);return o
def v8_route_volume(name,start,end,lateral,section,mat,step=3):
 ss=[start+i*step for i in range(int((end-start)/step)+1)]
 if abs(ss[-1]-end)>1e-6:ss.append(end)
 verts=[];faces=[];count=len(section)
 for s in ss:
  p,t,n=sample(s);height=road_height(s)
  for offset,z in section:verts.append(tuple(p+n*(lateral+offset)+Vector((0,0,height+z))))
 for i in range(len(ss)-1):
  for j in range(count):faces.append((i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j))
 faces.extend([tuple(reversed(range(count))),tuple((len(ss)-1)*count+j for j in range(count))]);return v8_solid(name,verts,faces,mat)
v8_route_volume('Flyover_Deck',2480,3010,0,[(-4.8,-.1),(4.8,-.1),(4.8,-.65),(-4.8,-.65)],stone)
for side in [-1,1]:
 v8_route_volume('Flyover_Barrier',2480,3010,side*4.42,[(-.15,0),(.15,0),(.08,.72),(-.08,.72)],stone)
 v8_route_volume('Flyover_TopRail',2480,3010,side*4.42,[(-.05,1.0),(.05,1.0),(.05,1.1),(-.05,1.1)],rail)
 for s in range(2480,3010,5):
  p,t,n=sample(s);o=cube('Flyover_RailPost',p+n*side*4.42+Vector((0,0,road_height(s)+.87)),(.065,.065,.36),rail);o.rotation_euler[2]=math.atan2(t.y,t.x)
 for k,s in enumerate(range(2480,3010,4)):v8_route_volume('Flyover_SafetyStripe',s,min(s+3.9,3010),side*4.264,[(-.006,.18),(.006,.18),(.006,.5),(-.006,.5)],yellow if k%2==0 else dark,2)
for k,s in enumerate(range(2510,2991,30)):
 h=road_height(s)
 if h<2.5:continue
 p,t,n=sample(s);yaw=math.atan2(t.y,t.x);shaft_top=h-.65-.7;bottom=-.04
 o=cube('Flyover_PierShaft',p+Vector((0,0,(shaft_top+bottom)/2)),(1.8,2.2,shaft_top-bottom),stone);o.rotation_euler[2]=yaw
 o=cube('Flyover_PierCap',p+Vector((0,0,h-.65-.35)),(3.5,8,.7),stone);o.rotation_euler[2]=yaw
 o=cube('Flyover_PierFoot',p+Vector((0,0,.16)),(3.4,4.0,.4),stone);o.rotation_euler[2]=yaw
 v8_box_proxy(f'flyover-pier-{k}',p,yaw,1,[0,0,(shaft_top+bottom)/2],[1.8,2.2,shaft_top-bottom],'flyover_pier')
 v8_box_proxy(f'flyover-pier-cap-{k}',p,yaw,1,[0,0,h-.65-.35],[3.5,8,.7],'flyover_pier_cap')
# Barriers and underside use the continuous elevated_corridors solver, not duplicate beads.
collision_report={'basis':'Three X east,Y up,Z south. OBB heading atan2(+Z,+X); y is bottom elevation.','type':'Original simplified OBB infrastructure collision proxies; continuous flyover deck/rails come from elevated_corridors.','source':'blender/assemble_v8_districts.py and authored asset manifests','colliders':infrastructure_colliders}
for folder in ['assets/web','web/public/assets']:(ROOT/folder/'infrastructure_colliders.json').write_text(json.dumps(collision_report,separators=(',',':'))+'\n')
(OUT/'v8_assembly_report.json').write_text(json.dumps({'old_prop_count':old_count,'removed_old_intersections':len(removed),'new_placements':len(layout['new_prop_instances']),'total_placements':len(placements),'infrastructure_colliders':len(infrastructure_colliders),'new_asset_names':sorted({p['asset'] for p in layout['new_prop_instances']}),'world':world_metadata,'planar_route_preserved':True},indent=2))
print('V8_ASSEMBLY',len(placements),'props',len(infrastructure_colliders),'OBBs',len(removed),'old intersections cleared')
