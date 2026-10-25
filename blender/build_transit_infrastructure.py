"""Original Kochi-inspired transit architecture, not official branded replicas.
Blender +X forward, +Y left, +Z up. Source parts remain separate in .blend.
GLBs merge by material for instancing. No photo textures/downloaded geometry.
"""
import bpy, bmesh, math, json, hashlib, shutil, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/infrastructure/transit';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
for p in [OUT,WEB,PUBLIC,OUT/'previews']:p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.name='Transit_Asset_Library';scene.unit_settings.system='METRIC'
materials={}
def mat(key,color,rough=.65,metal=0,emission=0):
 m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(*color,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 materials[key]=m;return m
ivory=mat('V8_Concrete_Ivory',(.74,.75,.68),.82);cement=mat('V8_Viaduct_Concrete',(.44,.49,.48),.86);teal=mat('V8_Transit_Teal',(.025,.48,.54),.42,.12);dark=mat('V8_Roof_Graphite',(.055,.085,.10),.42,.26);glass=mat('V8_Transit_Window_Glass',(.045,.13,.17),.2,.45);warm=mat('V8_Lamp_Emissive',(.96,.76,.39),.4,0,.9);stone=mat('V8_Promenade_Stone',(.63,.63,.56),.9);wood=mat('V8_Bench_Timber',(.26,.115,.045),.75);green=mat('V8_Planter_Green',(.10,.24,.09),.85);asphalt=mat('V8_Asphalt',(.07,.085,.085),.95);paint=mat('V8_WeatheredWhite',(.8,.8,.7),.8)
silver=mat('V8_Station_Silver_Roof',(.64,.69,.71),.38,.35);terracotta=mat('V8_Kerala_Terracotta_Roof',(.47,.12,.045),.78)
assets={};active=None
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def asset(name,description,pivot='ground center'):
 global active
 c=bpy.data.collections.new(name);scene.collection.children.link(c);assets[name]={'collection':c,'description':description,'pivot':pivot,'proxies':[]};active=assets[name];return c
def mesh(name,verts,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);active['collection'].objects.link(o);o.data.materials.append(material);return o
def box(name,c,s,m,bevel=0):
 x,y,z=c;a,b,d=[v/2 for v in s];o=mesh(name,[(x-a,y-b,z-d),(x+a,y-b,z-d),(x+a,y+b,z-d),(x-a,y+b,z-d),(x-a,y-b,z+d),(x+a,y-b,z+d),(x+a,y+b,z+d),(x-a,y+b,z+d)],FACES,m)
 if bevel:
  mod=o.modifiers.new('Small manufactured edge bevel','BEVEL');mod.width=bevel;mod.segments=1
 return o
def beam(name,a,b,r,m,sides=6):
 a,b=Vector(a),Vector(b);v=(b-a).normalized();ref=Vector((0,0,1)) if abs(v.z)<.9 else Vector((1,0,0));u=v.cross(ref).normalized();w=v.cross(u);verts=[]
 for p in [a,b]:verts.extend(tuple(p+r*(math.cos(i*math.tau/sides)*u+math.sin(i*math.tau/sides)*w)) for i in range(sides))
 faces=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
 return mesh(name,verts,faces,m)
def proxy(c,s,kind='solid'):
 active['proxies'].append({'center_blender':list(c),'size_blender':list(s),'kind':kind})
def text_sign(name,words,pos,size,material,rotation=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(name,'FONT');cu.body=words;cu.size=size;cu.align_x='CENTER';cu.extrude=.006;cu.resolution_u=1;ob=bpy.data.objects.new(name,cu);active['collection'].objects.link(ob);ob.location=pos;ob.rotation_euler=rotation;cu.materials.append(material);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);return ob

def lamp(x,y,base=0,height=7.5):
 box('LampFoot',(x,y,base+.12),(.48,.48,.24),cement)
 beam('LampPole',(x,y,base+.2),(x,y,base+height),.085,dark,8)
 beam('LampArm',(x,y,base+height),(x,y-1.7,base+height+.25),.07,dark)
 box('LEDHousing',(x,y-1.7,base+height+.23),(.62,.31,.15),dark,.025);box('LEDPanel',(x,y-1.7,base+height+.145),(.50,.25,.014),warm)

def rail_line(name,a,b,z=1.1):
 a,b=Vector(a),Vector(b);length=(b-a).length;n=max(1,math.ceil(length/2.5))
 for i in range(n+1):
  p=a.lerp(b,i/n);beam(name+'_Post',p,p+Vector((0,0,z)),.035,dark)
 for h in [.45,z]:beam(name+'_Rail',a+Vector((0,0,h)),b+Vector((0,0,h)),.035,dark)

asset('MetroViaductSpan','25 m original single-track urban viaduct; rail-contact pivot; pier foot at world -0.04 m when placed at rail height 13 m.','rail-contact center; local Z=0')
box('Deck',(0,0,-.65),(25,5.4,1.0),cement,.08);box('TrackBed',(0,0,-.12),(25,3.3,.16),dark)
for y in [-.7175,.7175]:box('SteelRunningRail',(0,y,-.027),(25,.075,.054),dark)
for i in range(33):box('ConcreteSleeper',(-12+i*.75,0,-.13),(.18,2.25,.14),ivory)
box('PierShaft',(0,0,-7.14),(1.6,1.9,11.8),cement,.08);box('PierCap',(0,0,-1.25),(3.3,5.4,.9),cement,.07);box('PierFoot',(0,0,-12.94),(2.8,3.0,.2),cement)
for side in [-1,1]:
 box('ViaductSafetyParapet',(0,side*2.55,.28),(25,.18,.82),ivory);box('TealEdgeStripe',(0,side*2.65,.34),(25,.025,.13),teal)
proxy((0,0,-7.14),(1.6,1.9,11.8),'metro_pier');proxy((0,0,-1.25),(3.3,5.4,.9),'metro_pier_cap');proxy((0,0,-.65),(25,5.4,1.0),'metro_deck')

asset('MetroStation','Original elevated Kerala-inspired station: ivory panels, teal fascia, covered platform, full-height piers and switchback stair. No official logos.','rail-contact center; local Z=0')
box('Platform',(0,4.8,.5),(84,6.5,1.0),ivory,.06)
box('TactilePlatformEdge',(0,1.68,1.022),(82,.25,.025),warm)
for x in [-29,-10,10,29]:
 box('StationPier',(x,5.1,-6.3),(1.5,1.6,13.4),cement,.06);box('StationPierCap',(x,5.1,-.1),(4.0,6.0,.75),cement)
 proxy((x,5.1,-6.3),(1.5,1.6,13.4),'station_pier')
for x in range(-39,40,6):
 box('CanopyColumn',(x,7.7,3.6),(.23,.26,5.4),teal);box('CanopyCrossbeam',(x,3.0,6.05),(.25,12.6,.32),ivory)
# User reference: broad silver barrel vault, cyan curved end rim, enclosed glazed body.
roof_y=[-4.6+i*15.2/16 for i in range(17)]
roof_z=lambda y:5.9+2.0*math.cos((y-3)/7.6*math.pi/2)
verts=[(x,y,roof_z(y)) for x in [-43,43] for y in roof_y]
roof=mesh('SilverBarrelVault',verts,[(i,17+i,18+i,i+1) for i in range(16)],silver)
for face in roof.data.polygons:face.use_smooth=True
for x in [-43,43]:
 for i in range(16):beam('CyanCurvedRoofRim',(x,roof_y[i],roof_z(roof_y[i])),(x,roof_y[i+1],roof_z(roof_y[i+1])),.14,teal,8)
for y in roof_y[::2]:beam('RoofStandingSeam',(-43,y,roof_z(y)+.025),(43,y,roof_z(y)+.025),.023,glass)
for y in [-4.6,10.6]:box('CyanEaveFascia',(0,y,5.83),(86,.18,.42),teal)
# Continuous panelled outer body, leaving the train portals open at both ends.
box('StationFrontSill',(0,-3.12,1.45),(84,.20,1.0),ivory)
box('StationFrontHeader',(0,-3.12,5.1),(84,.20,1.15),ivory)
for x in range(-39,40,3):
 box('StationFrontGlazing',(x,-3.13,3.15),(2.78,.06,2.35),glass)
 box('FrontPanelMullion',(x-1.45,-3.18,3.15),(.16,.15,2.45),ivory)
for x in range(-39,40,6):box('FrontFrameColumn',(x,-2.7,3.05),(.18,.18,6.1),teal)

for x in range(-39,40,3):
 box('RearWallPanel',(x,8.0,2.7),(2.9,.22,3.5),ivory);box('RearWindow',(x,7.875,3.0),(2.35,.03,2.2),glass)
for x in range(-36,37,12):
 box('StationBenchSeat',(x,5.9,1.4),(3.5,.55,.18),teal);box('StationBenchBack',(x,6.15,1.8),(3.5,.12,.7),teal)
 box('PlatformLight',(x,3.0,6.12),(2.8,.25,.07),warm)
for x in [-30,0,30]:
 box('StationSign',(x,-3.28,5.35),(10,.10,.7),glass);text_sign('CoastMetroSign','COAST METRO',(x,-3.35,5.13),.53,warm)
# Seven switchback flights climb from local -13 to +1 m; 12 treads/flight.
for level in range(7):
 z0=-13+level*2;direction=1 if level%2==0 else -1;yy=4.0 if level%2==0 else 6.8
 for step in range(12):
  x=48+direction*(-2.8+(step+.5)*5.6/12);top=z0+(step+1)*2/12;box('StairTread',(x,yy,top-.09),(5.6/12+.015,2.35,.18),ivory)
 beam('StairHandrail',(48-direction*2.8,yy-1.15,z0+.95),(48+direction*2.8,yy-1.15,z0+2.95),.045,teal)
 box('StairLanding',(48+direction*3.45,5.4,z0+2-.12),(1.3,5.2,.24),ivory)
for x in [44.5,51.5]:
 for y in [2.8,8.0]:box('StairTowerPost',(x,y,-5.8),(.3,.3,14.4),teal)
box('PlatformStairBridge',(44,5.4,.8),(4,5.4,.4),ivory)
proxy((0,4.8,.5),(84,6.5,1.0),'station_platform');proxy((48,5.4,-6),(8.8,6.0,14),'station_staircase');proxy((0,3.0,7.1),(86,15.2,1.6),'station_roof')

asset('WaterTransitTerminal','Original low Kerala waterfront transit terminal, pitched canopy, cream walls, blue fascia, forecourt and floating boarding pontoon. Water direction is local +Y.','shore-side ground origin; shoreline should cross local Y=+8m')
box('Forecourt',(0,-1,.12),(48,18,.24),stone)
box('TerminalBuilding',(0,-3,2.15),(40,14,4.3),ivory,.05)
box('TerminalFrontWindow',(0,-10.035,2.45),(37,.05,2.45),glass)
for x in range(-18,19,4):box('WindowMullion',(x,-10.08,2.4),(.13,.10,2.6),teal)
box('FrontFascia',(0,-10.18,4.08),(42,.26,.65),teal)
text_sign('WaterTransitSign','BACKWATER TRANSIT',(0,-10.33,3.88),.78,ivory)
# User reference: large terracotta Kerala roof, articulated by repeated front gables.
mesh('TerracottaMainRoof',[(-22,-12,4.6),(22,-12,4.6),(22,-3,7.3),(-22,-3,7.3),(-22,6,4.6),(22,6,4.6)],[(0,1,2,3),(3,2,5,4)],terracotta)
for x in [-22,22]:mesh('CreamGableEnd',[(x,-12,4.6),(x,-3,7.3),(x,6,4.6)],[(0,1,2)],ivory)
for x in range(-21,22,2):
 beam('TerracottaTileRidge',(x,-12,4.63),(x,-3,7.33),.025,terracotta)
 beam('TerracottaTileRidge',(x,-3,7.33),(x,6,4.63),.025,terracotta)
for x in [-13,0,13]:
 mesh('FrontCrossGableRoof',[(x-3,-13,4.9),(x,-13,6.55),(x+3,-13,4.9),(x-3,-7,5.0),(x,-7,6.65),(x+3,-7,5.0)],[(0,1,4,3),(1,2,5,4)],terracotta)
 mesh('CreamFrontGable',[(x-3,-13.03,4.9),(x,-13.03,6.55),(x+3,-13.03,4.9)],[(0,1,2)],ivory)
 box('GableWindow',(x,-13.055,5.43),(1.1,.03,.65),glass)
for x in [-20,-10,10,20]:box('FrontCanopyPost',(x,-12,2.25),(.15,.15,4.5),teal)
box('EntryAwning',(0,-11.3,4.45),(43,3,.17),dark)
box('WatersideWindows',(0,4.035,2.45),(36,.05,2.4),glass)
for x in range(-18,19,4):box('WaterWindowMullion',(x,4.08,2.4),(.13,.1,2.6),ivory)
for x in [-20,20]:
 box('BenchSeat',(x,-5,.68),(3,.65,.18),wood);box('BenchBack',(x,-4.72,1.05),(3,.12,.65),wood)
# Intentional in-water dock; foreground building and forecourt remain on land.
box('Gangway',(0,14.0,.55),(4.2,13.0,.25),stone)
box('FloatingPontoon',(0,23.0,.5),(24,7,.7),dark)
box('PontoonDeck',(0,23.0,.88),(24,7,.10),stone)
for x in [-11,11]:
 for y in [20,26]:beam('DockMooringPost',(x,y,-1.5),(x,y,1.75),.12,teal,8)
for x in [-2.05,2.05]:rail_line('GangwayRail',(x,7.5,.7),(x,19.5,.7),.95)
for x in [-10,10]:
 box('PontoonCanopyColumn',(x,22,2.7),(.14,.14,3.5),teal)
box('PontoonRoof',(0,22,4.5),(24,4.8,.18),dark)
proxy((0,-3,2.15),(40,14,4.3),'terminal_building');proxy((0,23,.5),(24,7,.7),'floating_dock')

asset('PromenadeSegment','20 m original pedestrian waterfront promenade with rail, repeated pavers, benches, planters and lamps; water is +Y.','ground-center')
box('PromenadePaving',(0,0,.1),(20,7,.2),stone)
for x in range(-9,10,2):box('PavingJoint',(x,0,.204),(.025,7,.005),dark)
rail_line('WaterfrontRail',(-10,3.35,.2),(10,3.35,.2),1.05)
for x in [-6,6]:
 box('BenchSeat',(x,1.5,.72),(2.8,.65,.16),wood);box('BenchBack',(x,1.78,1.04),(2.8,.12,.65),wood)
 for xx in [x-.9,x+.9]:box('BenchLeg',(xx,1.5,.42),(.12,.45,.58),dark)
 box('Planter',(x,-2,.46),(2.5,1.0,.65),stone)
 for k in range(5):
  xx=x-1+k*.5;box('Hedge',(xx,-2,.98),(.51,.85,.65),green,.13)
 lamp(x,-2.8,.2,6.5)
proxy((0,3.35,.75),(20,.12,1.1),'promenade_railing')

asset('Streetlight','Original warm LED streetlight with slim bent arm.','ground-center')
lamp(0,0,0,8.5);proxy((0,0,4.25),(.22,.22,8.5),'streetlight')

asset('SideStreetSegment','25 m original access street with raised sidewalks and lane markings, for dense district blocks.','road center; top at local Z=.18')
box('AccessAsphalt',(0,0,.10),(25,6,.16),asphalt)
for side in [-1,1]:
 box('AccessSidewalk',(0,side*4,.13),(25,2,.26),stone);box('AccessEdgeLine',(0,side*2.78,.185),(25,.08,.012),paint)
for x in [-9,-3,3,9]:box('AccessCenterDash',(x,0,.188),(3,.07,.016),paint)

# Consolidated authored palettes: at most five draw materials per module.
for name,replacements in {'MetroStation':{cement:ivory},'WaterTransitTerminal':{wood:teal,stone:ivory},'PromenadeSegment':{cement:stone}}.items():
 for o in assets[name]['collection'].objects:
  if o.type=='MESH' and o.data.materials and o.data.materials[0] in replacements:o.data.materials[0]=replacements[o.data.materials[0]]
# Text tessellation can emit collinear zero-area cap triangles; remove these in source.
for a in assets.values():
 for o in a['collection'].objects:
  if o.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-7]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(o.data);bm.free();o.data.update()
# Source library stores every architectural part, not only merged runtime meshes.
scene.world.color=(.35,.42,.45)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Kerala_Transit_Infrastructure.blend'))
manifest={'generator':'blender/build_transit_infrastructure.py','blender':bpy.app.version_string,'license':'Original procedural geometry. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.  no third-party model/texture data. Architectural cues from official sources in research/KERALA_INFRASTRUCTURE_REFERENCES.md. Generic names, no affiliation.','axes':'Source Blender X forward,Y left,Z up. GLB X forward,Y up,-Z left; root transforms identity.','assets':{}}
# Convert copies, apply edge bevels, then merge exactly per material.
for name,a in assets.items():
 bpy.ops.object.select_all(action='DESELECT');temps=[]
 for original in list(a['collection'].objects):
  o=original.copy();o.data=original.data.copy();scene.collection.objects.link(o);temps.append(o);o.select_set(True);bpy.context.view_layer.objects.active=o
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  o.select_set(False)
 groups={}
 for o in temps:groups.setdefault(o.data.materials[0].name,[]).append(o)
 merged=[]
 for key,obs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in obs:o.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name+'_'+key;merged.append(o)
 # Remove collinear text caps again after world-space merge/float quantization.
 for o in merged:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-7]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(o.data);bm.free();o.data.update()
 bpy.ops.object.select_all(action='DESELECT')
 for o in merged:o.select_set(True)
 bpy.context.view_layer.objects.active=merged[0];path=WEB/(name+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
 pts=[o.matrix_world@v.co for o in merged for v in o.data.vertices];lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)];tris=sum(len(p.vertices)-2 for o in merged for p in o.data.polygons)
 manifest['assets'][name]={'file':path.name,'triangles':tris,'materials':len(merged),'bytes':path.stat().st_size,'bounds_blender':{'min':lo,'max':hi},'pivot':a['pivot'],'description':a['description'],'collision_boxes_blender':a['proxies'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 shutil.copy2(path,PUBLIC/path.name)
 for o in merged:bpy.data.objects.remove(o,do_unlink=True)
 print('TRANSIT_INFRA',name,tris,'triangles',len(groups),'materials')
for p in [OUT/'manifest.json',WEB/'transit_infrastructure_manifest.json',PUBLIC/'transit_infrastructure_manifest.json']:p.write_text(json.dumps(manifest,indent=2))
(OUT/'LICENSE.txt').write_text('Original procedural geometry authored for this project. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No third-party model or texture data is included. Architectural inspiration does not imply operator affiliation. Keep OSM attribution separately for route-derived placement data.\n')
# Optional individual CPU previews; preserve native source before preview setup.
if '--render' in sys.argv:
 world=bpy.data.worlds.new('TransitPreviewWorld');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.45,.57,.65,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.45;scene.world=world
 bpy.ops.object.light_add(type='AREA',location=(15,-25,45));light=bpy.context.object;light.data.energy=7000;light.data.shape='DISK';light.data.size=35;light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.rotation_euler=(.4,-.5,-.6);sun.data.energy=2.0;sun.data.angle=.08
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.clip_end=1000
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20;scene.cycles.use_denoising=False;scene.render.resolution_x=960;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
 for name in ['MetroStation','WaterTransitTerminal','MetroViaductSpan','PromenadeSegment']:
  for key,a in assets.items():
   for o in a['collection'].objects:o.hide_render=key!=name
  a=manifest['assets'][name];lo=Vector(a['bounds_blender']['min']);hi=Vector(a['bounds_blender']['max']);center=(lo+hi)/2;size=hi-lo;cam.location=center+Vector((size.x*.65,-max(size.x,size.y)*.85,max(size.z,size.x*.45)));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(size.x,size.y,size.z)*1.25;scene.render.filepath=str(OUT/'previews'/(name+'.png'));bpy.ops.render.render(write_still=True);print('TRANSIT_PREVIEW',scene.render.filepath)
print('TRANSIT_INFRASTRUCTURE_COMPLETE')
