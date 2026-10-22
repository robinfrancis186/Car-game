"""Original compact six-material service/showroom bay. No route, collision or existing asset writes."""
import bpy,bmesh,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];OUT=R/'assets/showroom';OUT.mkdir(parents=True,exist_ok=True);WEB=R/'assets/web';PUB=R/'web/public/assets'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);s=bpy.context.scene;s.name='Original_Service_Showroom';s.unit_settings.system='METRIC';col=bpy.data.collections.new('ServiceShowroomBay');s.collection.children.link(col)
def mat(name,c,rough=.7,metal=0,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emission
 return m
concrete=mat('Bay_Concrete',(.10,.12,.14),.83);steel=mat('Bay_Steel',(.22,.27,.30),.38,.78);teal=mat('Bay_Teal',(.018,.27,.25),.36,.35);dark=mat('Bay_DarkFinish',(.018,.027,.035),.35,.23);light=mat('Bay_LightStrip',(.74,.91,1),.27,.05,5);amber=mat('Bay_SafetyAmber',(.82,.43,.055),.6,.1)
def link(o,m):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m);return o

def box(name,p,size,m,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o,m)
 if bevel:
  mod=o.modifiers.new('Small real edge chamfer','BEVEL');mod.width=bevel;mod.segments=1;mod.affect='EDGES';bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

def mesh(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(m);return o

def cylinder(name,p,r,depth,m,n=12,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=p,rotation=rot);o=bpy.context.object;o.name=name;return link(o,m)

def text(name,body,p,size,m):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.001;cu.resolution_u=2;o=bpy.data.objects.new(name,cu);col.objects.link(o);o.location=p;o.rotation_euler=(math.pi/2,0,0);cu.materials.append(m);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
# Coplanar floor and stage, genuinely no overlapping/z-fighting top faces. Both tops exactly Z=0.
N=96;vs=[]
for k in range(N):
 a=k*math.tau/N;c=math.cos(a);d=math.sin(a);t=min(9/abs(c)if abs(c)>1e-8 else 1e8,7/abs(d)if abs(d)>1e-8 else 1e8);vs.extend([(c*t,d*t,0),(c*3.35,d*3.35,0)])
mesh('Concrete floor with circular inspection inset',vs,[(2*k,2*((k+1)%N),2*((k+1)%N)+1,2*k+1)for k in range(N)],concrete)
mesh('Flush inspection stage',[(0,0,0)]+[(math.cos(k*math.tau/N)*3.35,math.sin(k*math.tau/N)*3.35,0)for k in range(N)],[(0,k+1,(k+1)%N+1)for k in range(N)],dark)
mesh('Floor slab perimeter',[(-9,-7,0),(9,-7,0),(9,7,0),(-9,7,0),(-9,-7,-.18),(9,-7,-.18),(9,7,-.18),(-9,7,-.18)],[(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)],concrete)
for k in range(72):
 a=k*math.tau/72;b=(k+.76)*math.tau/72;r1=3.38;r2=3.405;mesh('Segmented stage light %02d'%k,[(math.cos(a)*r1,math.sin(a)*r1,.004),(math.cos(b)*r1,math.sin(b)*r1,.004),(math.cos(b)*r2,math.sin(b)*r2,.004),(math.cos(a)*r2,math.sin(a)*r2,.004)],[(0,1,2,3)],light)
for x in [-8,-6,-4,4,6,8]:box('Floor expansion joint',(x,0,.001),(.015,13.8,.002),dark)
for y in [-6,-4,4,6]:box('Floor expansion joint',(0,y,.001),(17.8,.015,.002),dark)
# Back wall and low side returns. +Z in glTF (native -Y) stays fully open for hero cameras.
box('Back concrete wall',(0,6.88,3.05),(18,.24,6.1),concrete,.035)
for x in [-8.88,8.88]:
 box('Low side return',(x,0,1.85),(.24,13.7,3.7),concrete,.025);box('Continuous teal wall datum',(x*.987,0,3.5),(.025,13.5,.12),teal)
for x in [-8.6,8.6]:
 for y in [-6.6,6.6]:
  box('Structural column',(x,y,2.9),(.24,.28,5.8),steel,.015);box('Column footplate',(x,y,.055),(.52,.55,.11),dark,.012)
for y in [-6.6,0,6.6]:
 for z in [5.72,5.98]:box('Roof I-beam flange',(0,y,z),(17.4,.34,.08),steel)
 box('Roof I-beam web',(0,y,5.85),(17.4,.07,.24),steel)
for x in [-5.5,0,5.5]:
 box('Suspended luminaire housing',(x,0,5.46),(.32,6,.12),dark,.015);box('Long diffused light strip',(x,0,5.39),(.23,5.8,.015),light)
 for y in [-2.5,2.5]:cylinder('Luminaire suspension',(x,y,5.63),.009,.32,steel,6)
# Closed segmented service door at the back, with robust tracks and lintel.
box('Garage door recess',(-1.0,6.71,2.24),(8.15,.06,4.48),dark)
for k in range(14):
 z=.18+k*.29;box('Horizontal insulated door panel',(-1,6.645,z),(7.8,.08,.264),steel,.012)
for x in [-5.08,3.08]:box('Garage door guide',(x,6.54,2.22),(.18,.25,4.44),teal,.015)
box('Garage door lintel',(-1,6.54,4.5),(8.36,.25,.22),teal,.018);box('Door vision band',(-1,6.588,3.18),(6.7,.015,.19),dark)
for x in [-4,-2.5,-1,.5,2]:box('Door window divider',(x,6.57,3.18),(.035,.04,.20),steel)
text('Workshop title','PERFORMANCE LAB',(-1,6.735,5.14),.38,light)
# Tool chest bank: inset drawer fronts, handles, wheeled lower cabinet and worktop.
for x in [-7.4,5.25,7.05]:
 width=1.55;box('Tool cabinet body',(x,5.92,.78),(width,1.15,1.46),teal,.045)
 for k in range(6):
  z=.24+k*.205;box('Inset drawer face',(x,5.325,z),(width-.10,.045,.18),dark,.008);box('Brushed drawer handle',(x,5.275,z+.035),(width-.34,.055,.025),steel,.004)
 box('Heavy workshop counter',(x,5.92,1.55),(width+.10,1.3,.09),steel,.018)
 for dx in [-.53,.53]:
  for y in [5.52,6.31]:cylinder('Cabinet castor',(x+dx,y,.10),.09,.055,dark,10,(math.pi/2,0,0))
# Pegboard, repeated perforations and visible tool silhouettes.
box('Tool wall panel',(6.15,6.665,2.85),(3.8,.05,2.1),dark,.02)
for i in range(12):
 for j in range(5):cylinder('Pegboard hole',(4.55+i*.29,6.63,2.02+j*.35),.012,.006,steel,6,(math.pi/2,0,0))
for k in range(8):
 x=4.65+k*.41;z=2.45+(k%2)*.43;box('Tool handle',(x,6.54,z),(.045,.065,.45),teal,.008);box('Tool head',(x,6.54,z+.25),(.18,.07,.07),steel,.012)
# Side service cart, cable coil, wheel rack, safety stripes and drain grates.
box('Rolling side cart',(-7.25,1.8,.6),(1.5,.9,1.1),dark,.05)
for z in [.26,.7,1.16]:box('Cart shelf',(-7.25,1.8,z),(1.6,1.0,.045),steel,.01)
for i in range(4):
 bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,major_radius=.38+i*.025,minor_radius=.012,location=(-8.66,2.5,1.7),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name='Open service cable coil';link(o,dark)
for x in [-7.1,7.1]:
 box('Floor drain',(x,-4.9,.004),(2,.30,.008),dark)
 for k in range(12):box('Drain grate bar',(x-.9+k*.16,-4.9,.012),(.035,.28,.012),steel)
for side in [-1,1]:
 for k in range(9):
  o=box('Safety approach stripe',(side*4.6,-3.4+k*.38,.006),(.48,.10,.012),amber);o.rotation_euler[2]=side*math.radians(35)
# Source stays editable with descriptive individual parts.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ServiceShowroomBay.blend'))
# Merge by material only in an export copy; six draws maximum, all transforms baked.
source=list(col.objects);exports=[]
for m in [concrete,steel,teal,dark,light,amber]:
 group=[]
 for o in source:
  if o.type=='MESH'and o.data.materials[0]==m:
   c=o.copy();c.data=o.data.copy();s.collection.objects.link(c);group.append(c)
 bpy.ops.object.select_all(action='DESELECT')
 for o in group:o.select_set(True)
 bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();o=bpy.context.object;o.name='ServiceShowroomBay_'+m.name;exports.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in exports:o.select_set(True)
p=WEB/'ServiceShowroomBay.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False);shutil.copy2(p,PUB/p.name)
tri=sum(sum(len(q.vertices)-2 for q in o.data.polygons)for o in exports)
manifest={'asset':'ServiceShowroomBay','file':p.name,'native_source':'assets/showroom/ServiceShowroomBay.blend','native_collection':'ServiceShowroomBay','triangles':tri,'draws':len(exports),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'axes':'glTF X forward, Y up; open front +Z; native Blender open front -Y','footprint_m':[18,14],'floor_y':0,'stage_y':0,'stage_radius_m':3.35,'back_wall_z':-6.88,'roof_beam_y':[5.68,6.02],'lamp_anchors_three':[[1,4.8,2],[-3,3,-4],[-5.5,5.3,0],[0,5.3,0],[5.5,5.3,0]],'safe_hero_cameras_three':[[7.5,2.4,8.2],[12.4,3.5,13.5]],'materials':[m.name for m in [concrete,steel,teal,dark,light,amber]],'purpose':'Menu-only isolated car inspection bay. No race placement, physics or colliders. Emissive strips need scene lights to illuminate the car.','license':'Original procedural geometry/materials; no reference photos, downloaded textures or third-party model geometry.'}
assert tri<=12000,tri
for d in [OUT,WEB,PUB]:(d/'showroom_manifest.json').write_text(json.dumps(manifest,indent=2))
for o in exports:bpy.data.objects.remove(o,do_unlink=True)
# Actual car-in-bay preview; existing car file remains byte-identical and is not embedded in bay GLB.
bpy.ops.import_scene.gltf(filepath=str(WEB/'car_silver.glb'));s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=False;s.cycles.max_bounces=5;s.render.resolution_x=1250;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
w=bpy.data.worlds.new('Bay ambient');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.20,.26,.34,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.35;s.world=w
for loc,power,size,color in [((1,-2,4.8),1600,5,(.75,.88,1)),((-3,4,3),1400,4,(1,.75,.5)),((5,0,5.3),1200,4,(.8,1,.95)),((-5,0,5.3),1000,4,(.7,.85,1))]:
 ld=bpy.data.lights.new('Preview softbox','AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color;lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);lo.location=loc;lo.rotation_euler=(Vector((0,0,.6))-lo.location).to_track_quat('-Z','Y').to_euler()
ca=bpy.data.cameras.new('Bay hero');co=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(co);co.location=(7.5,-8.2,2.4);co.rotation_euler=(Vector((0,0,.78))-co.location).to_track_quat('-Z','Y').to_euler();ca.lens=35;s.camera=co;s.render.filepath=str(OUT/'ServiceShowroomBay_preview.png');bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ServiceShowroomBay_Preview.blend'));print('SHOWROOM_READY',manifest,flush=True)
co.location=(12,-15,7.1);co.rotation_euler=(Vector((0,1,2.4))-co.location).to_track_quat('-Z','Y').to_euler();ca.lens=32;s.cycles.samples=32;s.render.resolution_x=1100;s.render.resolution_y=760;s.render.filepath=str(OUT/'ServiceShowroomBay_overview.png');bpy.ops.render.render(write_still=True)
