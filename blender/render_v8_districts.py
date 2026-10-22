"""CPU art-direction previews of the integrated authored district; not browser screenshots."""
import bpy,json,math,bisect
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/v8_districts';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/course/Kappil_Coast.blend'));scene=bpy.context.scene
# Replace only original high-detail landscaping with its actual optimized web GLBs.
replacements={};instances=[o for o in scene.objects if o.instance_type=='COLLECTION' and o.instance_collection]
for name in sorted({o.instance_collection.name for o in instances}):
 if name not in ['CoconutPalm_A','CoconutPalm_B','KeralaHouse','FishingBoat','RoadReflector','TropicalGrass','SeaWallRock']:continue
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/web'/(name+'.glb')));objects=set(bpy.data.objects)-before;c=bpy.data.collections.new('PREVIEW_WEB_'+name)
 for o in objects:
  for old in list(o.users_collection):old.objects.unlink(o)
  c.objects.link(o)
 replacements[name]=c
for o in instances:
 if o.instance_collection.name in replacements:o.instance_collection=replacements[o.instance_collection.name]
# Match authored per-block facade/accent choices without altering source libraries.
def rgb(h):
 return tuple((int(h[i:i+2],16)/255/12.92 if int(h[i:i+2],16)/255<=.04045 else ((int(h[i:i+2],16)/255+.055)/1.055)**2.4) for i in [1,3,5])
variants={}
for ob in instances:
 if 'facade_color' not in ob:continue
 key=(ob.instance_collection.name,ob['facade_color'],ob['accent_color'])
 if key not in variants:
  old=ob.instance_collection;c=bpy.data.collections.new('PALETTE_'+str(len(variants)));mapping={}
  for o in old.objects:
   q=o.copy();q.data=o.data.copy() if o.data else None;c.objects.link(q);mapping[o]=q
   if q.type=='MESH':
    for k,m in enumerate(q.data.materials):
     color=ob['facade_color'] if 'Warm_Lime_Plaster' in m.name else ob['accent_color'] if 'Kerala_Teal_Trim' in m.name else None
     if color:
      mm=m.copy();mm.diffuse_color=(*rgb(color),1);mm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*rgb(color),1);q.data.materials[k]=mm
  for old,q in mapping.items():q.parent=mapping.get(old.parent)
  variants[key]=c
 ob.instance_collection=variants[key]
# Dynamic vehicle preview at the station/berth; production runtime animates separately.
world=json.loads((ROOT/'assets/course/manifest.json').read_text())['world']
for tr in world['transit_routes']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/web'/(tr['asset']+'.glb')));objects=set(bpy.data.objects)-before;roots=[o for o in objects if o.parent not in objects];a=Vector((tr['points'][0][0],-tr['points'][0][2],tr['points'][0][1]));b=Vector((tr['points'][-1][0],-tr['points'][-1][2],tr['points'][-1][1]));d=(b-a).normalized();p=a+d*(110 if tr['type']=='metro' else 4)
 holder=bpy.data.objects.new('PREVIEW_'+tr['id'],None);scene.collection.objects.link(holder);holder.location=p;holder.rotation_euler.z=math.atan2(d.y,d.x)
 for o in roots:o.parent=holder
# Avoid hero car floating at a non-preview camera location; no authored scene edits saved.
if bpy.data.collections.get('Hero_Car'):
 for o in bpy.data.collections['Hero_Car'].objects:o.hide_render=True
manifest=json.loads((ROOT/'assets/course/manifest.json').read_text());route=[Vector(p) for p in manifest['route_points_m']];dist=manifest['horizontal_route_distances_m']
def sample(s):
 k=min(len(route)-2,max(0,bisect.bisect_right(dist,s)-1));f=(s-dist[k])/(dist[k+1]-dist[k]);p=route[k].lerp(route[k+1],f);t=route[k+1]-route[k];t.z=0;t.normalize();return p,t,Vector((-t.y,t.x,0))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.exposure=-.75
cam=scene.camera;cam.data.type='PERSP';cam.data.lens=42;cam.data.clip_end=10000
shots=[];p,t,n=sample(2045);shots.append(('MetroMarket_Integrated',p-t*95-n*75+Vector((0,0,57)),p+t*20+n*12+Vector((0,0,8))))
p,t,n=sample(2545);shots.append(('FlyoverApproach_Integrated',p-t*46-n*19+Vector((0,0,11)),p+t*48+Vector((0,0,2))))
terminal=next(p for p in manifest['prop_instances'] if p['asset']=='WaterTransitTerminal');p=Vector(terminal['location_m']);a=math.radians(terminal['yaw_deg']);t=Vector((math.cos(a),math.sin(a),0));n=Vector((-t.y,t.x,0));shots.append(('BackwaterQuarter_Integrated',p-t*58+n*95+Vector((0,0,43)),p-n*18+Vector((0,0,3))))
for name,pos,target in shots:
 cam.location=pos;cam.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('V8_INTEGRATED_PREVIEW',name,flush=True)
(OUT/'README.md').write_text('Integrated Blender CPU art-direction previews of the authored v8 district, not browser captures or performance evidence. Uses the actual web landscaping GLBs, original authored architecture, per-block color choices and stationary transit at station/berth. Production renderer provides its own water, road detail, lighting and animation. Original source/project files were not modified by rendering.\n')
