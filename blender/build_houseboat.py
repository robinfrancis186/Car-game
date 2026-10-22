"""Original stylized Kerala houseboat, geometry-only; no photograph textures/models.
Reference-only user images: D741BBC2-9AFD-40B0-AC01-784FF1A92D99.png,
2D597ABA-5859-4E77-B6F6-1F2F563923F6.png. Do not package those photographs.
Blender +X bow/forward, +Z up; GLB +X forward,+Y up. Waterline origin=0.
"""
import bpy,bmesh,math,json,struct,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/infrastructure/backwater';WEB=ROOT/'assets/web';PUB=ROOT/'web/public/assets'
for p in (OUT,WEB,PUB):p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
bpy.context.preferences.filepaths.save_version=0
SC=bpy.context.scene;SC.unit_settings.system='METRIC';SC.unit_settings.scale_length=1
NAME='KeralaHouseboat';COL=bpy.data.collections.new(NAME);SC.collection.children.link(COL)
ROOTOBJ=bpy.data.objects.new(NAME,None);COL.objects.link(ROOTOBJ)
ROOTOBJ['forward']='+X';ROOTOBJ['waterline_z']=0;ROOTOBJ['provenance']='Original procedural Blender asset; fictional Kerala-inspired houseboat'
BUFF={i:[[],[]] for i in range(4)};MATS=[]
for name,color,rough in [('Hull_And_Window',(.032,.038,.034),.58),('Bamboo_And_Timber',(.45,.245,.09),.87),('Woven_Thatch',(.62,.43,.22),.94),('Cream_Trim_And_Fenders',(.79,.76,.62),.78)]:
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);m.use_backface_culling=False
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;MATS.append(m)
def mesh(v,f,m):
 vs,fs=BUFF[m];off=len(vs);vs.extend(v);fs.extend(tuple(i+off for i in face) for face in f)
def quad(a,b,c,d,m):mesh([a,b,c,d],[(0,1,2,3)],m)
def box(x,y,z,l,w,h,m):
 a,b,c=l/2,w/2,h/2
 mesh([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),(x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],m)
def tube(a,b,r,m=1,n=6):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u)
 vv=[tuple(p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for p in (a,b) for i in range(n)]
 ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh(vv,ff,m)
def tire(x,y,z):
 # 14x5 torus, hole actually open, ring lies in vertical XZ plane.
 vs=[];major=.20;minor=.062;N=14;M=5
 for a in range(N):
  t=math.tau*a/N
  for b in range(M):
   q=math.tau*b/M;r=major+minor*math.cos(q)
   vs.append((x+r*math.cos(t),y+minor*math.sin(q),z+r*math.sin(t)))
 ff=[(a*M+b,((a+1)%N)*M+b,((a+1)%N)*M+(b+1)%M,a*M+(b+1)%M) for a in range(N) for b in range(M)]
 mesh(vs,ff,3)
def archroof(x0,x1,width,base,rise,m=2,segments=12):
 # Shallow barrel roof with curved eaves, represented by true mesh strips.
 def coord(x,j):
  t=math.pi*j/segments
  return (x,math.cos(t)*width/2,base+math.sin(t)*rise)
 vs=[coord(x,j) for x in (x0,x1) for j in range(segments+1)]
 ff=[(j,j+1,segments+1+j+1,segments+1+j) for j in range(segments)]
 ff += [tuple(range(segments,-1,-1)),tuple(range(segments+1,2*(segments+1)))]
 mesh(vs,ff,m)
 # Narrow bamboo seams follow the surface, using strips not cylinders.
 for x in [x0+(x1-x0)*i/8 for i in range(9)]:
  for j in range(segments):
   a=Vector(coord(x,j));b=Vector(coord(x,j+1));a.z+=.016;b.z+=.016
   quad(tuple(a+Vector((-.026,0,0))),tuple(a+Vector((.026,0,0))),tuple(b+Vector((.026,0,0))),tuple(b+Vector((-.026,0,0))),1)
 for side in (-1,1):box((x0+x1)/2,side*width/2,base,(x1-x0),.075,.09,1)

# Boat-shaped hull: three tapered cross-section rings with upturned pointed ends.
xs=[-9,-8.1,-6,-3,0,3,6,8,9];widths=[.05,1.5,2.45,2.50,2.50,2.50,2.35,1.25,.05]
vs=[]
for x,w in zip(xs,widths):
 tip=max(0,(abs(x)-6)/3)
 vs.extend([(x*.94,-w*.42,-.75+tip*.65),(x,-w,.84+tip*.28),(x,w,.84+tip*.28),(x*.94,w*.42,-.75+tip*.65)])
ff=[]
for i in range(len(xs)-1):
 for j in range(4):ff.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
ff += [(3,2,1,0),tuple((len(xs)-1)*4+j for j in range(4))];mesh(vs,ff,0)
# Timber deck and perimeter gunwale strip, no box hull shortcut.
for i in range(len(xs)-1):
 x0,x1=xs[i:i+2];w0,w1=widths[i:i+2]
 z0=.85+max(0,(abs(x0)-6)/3)*.28;z1=.85+max(0,(abs(x1)-6)/3)*.28
 quad((x0,-w0,z0),(x1,-w1,z1),(x1,w1,z1),(x0,w0,z0),1)
 for side in (-1,1):
  tube((x0,side*w0,z0+.03),(x1,side*w1,z1+.03),.045,3,5)
# Main cabin walls, curved thatch cap; windows stay dark, no fake reflections.
box(-1.55,0,2.04,9.1,4.15,2.30,1)
archroof(-6.3,3.25,4.65,3.20,.76)
for side in (-1,1):
 y=side*2.085
 for x in (-4.85,-2.75,-.65,1.45):
  # Wide bamboo frame, dark inset, light shutters/crossbars.
  quad((x-.68,y,1.50),(x+.68,y,1.50),(x+.68,y,2.83),(x-.68,y,2.83),3)
  quad((x-.58,y+side*.008,1.60),(x+.58,y+side*.008,1.60),(x+.58,y+side*.008,2.73),(x-.58,y+side*.008,2.73),0)
  box(x,y+side*.018,2.165,.055,.045,1.13,3)
  box(x,y+side*.018,2.16,1.16,.045,.05,3)
 # Repeated bamboo wattle strips, interrupted around the fenestration by lower apron/upper clerestory placement.
 for z in (1.02,1.15,1.30,2.98,3.10):box(-1.55,y+side*.015,z,9.05,.045,.025,2)
 for x in (-5.9,-3.8,-1.7,.4,2.5):box(x,y+side*.02,2.05,.055,.05,2.10,2)
# Forward open shaded veranda: columns and rail, seating, framed doorway.
box(3.01,0,1.95,.08,1.18,2.10,0)
for y in (-.67,.67):box(3.09,y,1.95,.12,.12,2.1,3)
box(3.09,0,3.03,.12,1.46,.12,3)
archroof(3.12,7.25,4.6,3.18,.68)
for x in (3.35,5.15,7.0):
 for y in (-2.12,2.12):
  tube((x,y,.89),(x,y,3.20),.065,1,6)
  tube((x,y,.91),(x,y,1.73),.035,3,5)
for side in (-1,1):
 y=side*2.12
 for z in (1.27,1.73):tube((3.35,y,z),(7.0,y,z),.036,3,5)
 for x in (3.7,4.3,4.9,5.5,6.1,6.7):tube((x,y,.94),(x,y,1.73),.022,3,4)
 box(5.1,side*1.66,1.16,2.60,.60,.12,1)
 box(5.1,side*1.91,1.52,2.60,.09,.55,2)
 # Deck fenders hang slightly below waterline, preserve clean water root.
 for x in (-6,-3.6,-1.2,1.2,3.6,6):
  tire(x,side*2.56,.34)
  tube((x,side*2.48,.89),(x,side*2.56,.58),.017,1,4)
# Stern porch, simple back rail and mooring cleats.
archroof(-8,-6.15,4.0,2.90,.55)
for y in (-1.75,1.75):
 tube((-7.8,y,1.00),(-7.8,y,2.91),.06,1,6)
 tube((-7.75,y,1.68),(-6.3,y,1.68),.035,3,5)
 tube((-7.75,y,1.05),(-7.75,y,1.68),.035,3,5)
# Upper viewing deck / bamboo canopy captures reference's double-level silhouette.
box(1.48,0,3.98,5.25,3.25,.14,1)
for side in (-1,1):
 y=side*1.55
 for x in (-1.0,.25,1.5,2.75,4.0):
  tube((x,y,4.02),(x,y,4.85),.028,3,4)
 for z in (4.45,4.85):tube((-1.02,y,z),(4.02,y,z),.035,3,5)
 for x in (-1.0,4.0):tube((x,y,4.05),(x,y,5.20),.052,1,6)
archroof(-1.25,4.25,3.70,5.20,.60)
# Upper end safety rails and slim center bench.
for x in (-1.02,4.02):tube((x,-1.55,4.85),(x,1.55,4.85),.035,3,5)
box(1.5,0,4.35,2.5,.65,.12,1)
for x in (.4,2.6):box(x,0,4.16,.12,.53,.30,1)
# Bow cleats and small steering pedestal remain within boat envelope.
for x,y in ((8.05,0),(-8.05,0)):
 box(x,y,1.21,.55,.16,.10,0);box(x,y,1.10,.14,.12,.15,0)
box(6.6,0,1.33,.44,.48,.85,1)

OBJECTS=[]
for i,(v,f) in BUFF.items():
 if not v:continue
 me=bpy.data.meshes.new(NAME+'_'+MATS[i].name);me.from_pydata(v,[],f);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.delete(bm,geom=[a for a in bm.faces if a.calc_area()<1e-7],context='FACES');bm.normal_update();bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(me.name,me);COL.objects.link(ob);ob.parent=ROOTOBJ;ob.data.materials.append(MATS[i]);OBJECTS.append(ob)
bpy.ops.object.select_all(action='DESELECT');ROOTOBJ.select_set(True)
for ob in OBJECTS:ob.select_set(True)
bpy.context.view_layer.objects.active=ROOTOBJ
path=WEB/(NAME+'.glb')
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_extras=True,export_animations=False)
shutil.copy2(path,PUB/path.name)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(NAME+'.blend')))
data=path.read_bytes();jlen=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+jlen])
tris=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']);draws=sum(len(m['primitives']) for m in doc['meshes'])
pos=[doc['accessors'][p['attributes']['POSITION']] for m in doc['meshes'] for p in m['primitives']]
lo=[min(a['min'][k] for a in pos) for k in range(3)];hi=[max(a['max'][k] for a in pos) for k in range(3)]
report={'name':NAME,'source':'blender/build_houseboat.py','native':'assets/infrastructure/backwater/KeralaHouseboat.blend','native_collection':NAME,'root_object':NAME,'preview':'assets/infrastructure/backwater/KeralaHouseboat_preview.png','file':'assets/web/KeralaHouseboat.glb','triangles':tris,'materials':len(doc['materials']),'draw_primitives':draws,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'bounds_gltf_xyz_m':{'min':lo,'max':hi},'dimensions_gltf_xyz_m':[hi[k]-lo[k] for k in range(3)],'axes_blender':'+X forward, +Z up','axes_gltf':'+X forward, +Y up','pivot':'Waterline at zero, hull extends below; longitudinal and transverse center at origin','provenance':'Original procedural Blender geometry/materials. User reference photos visually studied only; no source photos, logos, models or textures included. Fictional Kerala-inspired houseboat, not exact vessel reproduction.','reference_files_study_only':['D741BBC2-9AFD-40B0-AC01-784FF1A92D99.png','2D597ABA-5859-4E77-B6F6-1F2F563923F6.png'],'qa':{'under_5000_triangles':tris<=5000,'max_4_draws':draws<=4,'max_4_materials':len(doc['materials'])<=4,'no_texture_images':not doc.get('images'),'waterline_straddled':lo[1]<0<hi[1]}}
(OUT/'houseboat_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
for d in (WEB,PUB):shutil.copy2(OUT/'houseboat_manifest.json',d/'houseboat_manifest.json')
print('HOUSEBOAT_EXPORTED',json.dumps(report),flush=True)
assert all(report['qa'].values()),report
# Isolated asset preview; water plane is presentation only and not exported.
world=bpy.data.worlds.new('Backwater_Preview_World');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.23,.34,.38,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.65;SC.world=world
water=bpy.data.materials.new('Preview_Only_Water');water.use_nodes=True
p=water.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.045,.17,.14,1);p.inputs['Metallic'].default_value=.3;p.inputs['Roughness'].default_value=.27
bpy.ops.mesh.primitive_plane_add(size=180,location=(0,0,-.06));bpy.context.object.data.materials.append(water)
bpy.ops.object.light_add(type='SUN',location=(-10,-8,20));bpy.context.object.data.energy=2.2;bpy.context.object.rotation_euler=(math.radians(25),math.radians(-18),math.radians(-30));bpy.context.object.data.angle=.12
bpy.ops.object.camera_add(location=(17,-24,13));cam=bpy.context.object;aim=Vector((0,0,2.2));cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=23;SC.camera=cam
SC.render.engine='CYCLES';SC.cycles.device='CPU';SC.cycles.samples=24;SC.cycles.use_denoising=False;SC.render.threads_mode='FIXED';SC.render.threads=4
SC.render.resolution_x=1152;SC.render.resolution_y=760;SC.render.resolution_percentage=100;SC.view_settings.view_transform='AgX';SC.render.image_settings.file_format='PNG';SC.render.filepath=str(OUT/'KeralaHouseboat_preview.png');bpy.ops.render.render(write_still=True)
print('HOUSEBOAT_READY',flush=True)
