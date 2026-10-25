"""Original route-aligned kicker decks; existing route geometry remains unchanged.
No project-wide reuse license has been selected for original project material;
third-party components retain their stated licenses. Coastal positions derive
from the attributed OSM centerline. This is authored arcade infrastructure.
"""
import bpy,math,json,sys,shutil,hashlib,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'blender'));import rebuild_car_helpers as h
O=R/'assets/airtime';W=R/'assets/web';P=R/'web/public/assets';O.mkdir(exist_ok=True)
CONFIG=[('course_runtime.json','Coast_AirtimeRamp',{'id':'skyline-rise','startS':2675,'lipS':2710,'rise':2.6,'centerOffset':0,'halfWidth':3.6}),('course_runtime_highlands.json','Highland_AirtimeRamp',{'id':'highway-rise','startS':330,'lipS':365,'rise':2.3,'centerOffset':0,'halfWidth':5.25})]
reports=[]
for file,name,cfg in CONFIG:
 h.reset();d=json.loads((P/file).read_text());route=d['route_points'];lengths=[0]
 for a,b in zip(route,route[1:]):lengths.append(lengths[-1]+math.hypot(b[0]-a[0],b[2]-a[2]))
 def sample(s,offset=0,raiseY=0):
  from bisect import bisect_right
  i=max(0,min(len(route)-2,bisect_right(lengths,s)-1));a,b=route[i:i+2];t=(s-lengths[i])/(lengths[i+1]-lengths[i]);dx=b[0]-a[0];dz=b[2]-a[2];n=math.hypot(dx,dz);x=a[0]+t*dx-dz/n*offset;z=a[2]+t*dz+dx/n*offset;y=a[1]+t*(b[1]-a[1])+raiseY
  return (x,-z,y)
 def rise(s):return max(0,min(1,(s-cfg['startS'])/(cfg['lipS']-cfg['startS'])))*cfg['rise']
 asphalt=h.material('Ramp asphalt aggregate',(.085,.097,.10),rough=.92,coat=0)
 concrete=h.material('Ramp precast side concrete',(.29,.32,.31),rough=.86,coat=0)
 yellow=h.material('Ramp hazard warm yellow',(.93,.57,.045),rough=.62,coat=0)
 white=h.material('Ramp road weathered white',(.76,.78,.70),rough=.64,coat=0)
 graphite=h.material('Ramp anti skid graphite',(.012,.018,.020),rough=.85,coat=0)
 # A procedural preview material is baked into no texture; runtime road micro detail uses original shared shader.
 n=asphalt.node_tree.nodes;l=asphalt.node_tree.links;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=110;noise.inputs['Roughness'].default_value=.72;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.012;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
 root=h.empty(name);root['provenance']='Original authored arcade ramp; no reference images or third-party mesh';h.CURRENT=root
 ss=[cfg['startS']+i for i in range(int(cfg['lipS']-cfg['startS'])+1)]
 # Top is exactly the model's piecewise graded support; no artificial lip bump.
 verts=[sample(s,side*cfg['halfWidth'],rise(s))for s in ss for side in(-1,1)];faces=[(i*2,i*2+1,i*2+3,i*2+2)for i in range(len(ss)-1)]
 h.mesh(name+'_Driveable_Asphalt',verts,faces,asphalt,False,normal_hint=(0,0,1))
 for side in(-1,1):
  v=[sample(s,side*cfg['halfWidth'],y)for s in ss for y in(-.12,rise(s))];f=[(i*2,i*2+1,i*2+3,i*2+2)for i in range(len(ss)-1)];h.mesh('Deck side precast panels',v,f,concrete,False)
  # Edge lines sit 6 mm above support, with reflective chevrons and anti-slip lip band.
  for s0 in [cfg['startS']+i*3 for i in range(12)]:
   s1=min(cfg['lipS'],s0+2);a=side*(cfg['halfWidth']-.18);b=side*(cfg['halfWidth']-.30)
   h.mesh('Broken safety edge stripe',[sample(s,a,rise(s)+.006)for s,a in[(s0,a),(s1,a),(s1,b),(s0,b)]],[(0,1,2,3)],white,False,normal_hint=(0,0,1))
  for s0 in [cfg['lipS']-.95]:
   # Alternating black/yellow paint is surface paint, not a collision barrier.
   for k in range(8):
    a=-cfg['halfWidth']+k*(2*cfg['halfWidth']/8);b=a+2*cfg['halfWidth']/8
    if side==1:h.mesh('Lip hazard paint',[sample(s,o,rise(s)+.008)for s,o in[(s0,a),(cfg['lipS']-.05,a),(cfg['lipS']-.05,b),(s0,b)]],[(0,1,2,3)],yellow if k%2==0 else graphite,False,normal_hint=(0,0,1))
 for s0 in [cfg['startS']+8,cfg['startS']+18,cfg['startS']+27]:
  # Unambiguous forward white chevrons without text textures.
  outline=[(s0-1.8,-1.2),(s0,-.0),(s0-1.8,1.2),(s0-1.8,.65),(s0-.85,0),(s0-1.8,-.65)]
  h.mesh('Forward ramp chevron',[sample(s,o,rise(s)+.009)for s,o in outline],[(0,1,4,5),(1,2,3,4)],white,False,normal_hint=(0,0,1))
 # Rear face visible on a reverse approach; model handles its collision separately.
 s=cfg['lipS'];h.mesh('Raised lip rear face',[sample(s,o,y)for o,y in[(-cfg['halfWidth'],-.12),(cfg['halfWidth'],-.12),(cfg['halfWidth'],cfg['rise']),(-cfg['halfWidth'],cfg['rise'])]],[(0,1,2,3)],concrete,False)
 # Landing-zone edge dashes sit on the original road, never an elevated invisible landing platform.
 for side in(-1,1):
  for s0 in range(int(cfg['lipS']+45),int(cfg['lipS']+160),12):
   a=side*(cfg['halfWidth']-.15);b=side*(cfg['halfWidth']-.31);h.mesh('Landing runway guidance',[sample(s,o,.008)for s,o in[(s0,a),(s0+5,a),(s0+5,b),(s0,b)]],[(0,1,2,3)],yellow,False,normal_hint=(0,0,1))
 # Merge same-material stationary meshes for five bounded draw calls.
 for m in [asphalt,concrete,yellow,white,graphite]:
  obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials[0]==m]
  if not obs:continue
  bpy.ops.object.select_all(action='DESELECT')
  for o in obs:o.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();bpy.context.object.name=name+'_'+m.name.replace(' ','_');bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 native=O/(name+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.object.select_all(action='SELECT');out=W/(name+'.glb');bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_extras=True,export_cameras=False,export_lights=False);shutil.copy2(out,P/out.name)
 raw=out.read_bytes();doc=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]]);report={**cfg,'asset':out.name,'native':str(native.relative_to(R)),'generator':'blender/build_airtime_ramps.py','coordinate_contract':'World-space glTF +Y up; no extra transform','triangles':sum(doc['accessors'][p['indices']]['count']//3 for me in doc['meshes']for p in me['primitives']),'draws':sum(len(m['primitives'])for m in doc['meshes']),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'collision':'Actual graded support and authored lip/side handling in gameplay; painted guidance is non-solid','source':'Original authored arcade geometry; coastal location uses attributed OSM route. No reuse license selected for original material.'};reports.append(report)
 # Preview actual exported ramp with a short neutral existing-grade road around it.
 h.CURRENT=None
 for j in range(int(cfg['startS']-35),int(cfg['lipS']+160),3):
  h.mesh('Preview road context',[sample(s,o,-.015)for s,o in[(j,-cfg['halfWidth']-.7),(j+3,-cfg['halfWidth']-.7),(j+3,cfg['halfWidth']+.7),(j,cfg['halfWidth']+.7)]],[(0,1,2,3)],asphalt,False,normal_hint=(0,0,1))
 # Render close enough to distinguish grade and surface, not claim an integrated game scene.
 center=Vector(sample((cfg['startS']+cfg['lipS'])/2));ahead=Vector(sample(cfg['lipS']))-Vector(sample(cfg['startS']));ahead.z=0;ahead.normalize();right=Vector((-ahead.y,ahead.x,0));target=center+Vector((0,0,1.2));campos=target-ahead*28+right*25+Vector((0,0,15))
 world=bpy.data.worlds.new('Ramp studio daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.19,.25,.31,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;bpy.context.scene.world=world
 bpy.ops.object.light_add(type='AREA',location=target+Vector((0,0,35)));bpy.context.object.data.energy=16000;bpy.context.object.data.size=35
 bpy.ops.object.light_add(type='SUN');bpy.context.object.data.energy=2;bpy.context.object.rotation_euler=(.35,-.4,-.4)
 bpy.ops.object.camera_add(location=campos);cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=40;bpy.context.scene.camera=cam
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.resolution_x=1200;sc.render.resolution_y=760;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(O/(name+'_preview.png'));bpy.ops.render.render(write_still=True)
(O/'ramp_manifest.json').write_text(json.dumps(reports,indent=2));print('AIRTIME_RAMPS_READY',json.dumps(reports))
