"""Original coastal glass/steel showroom loft. Reconstructed, not recovered V12 bytes.
Reference pixels guide composition only; no external geometry, photos or textures.
"""
import bpy,bmesh,math,json,hashlib,shutil,struct,sys,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]; O=R/'assets/showroom'; W=R/'assets/web'; P=R/'web/public/assets'
for p in (O,W,P):p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.name='Coastal_Showroom_Loft';s.unit_settings.system='METRIC';c=bpy.data.collections.new('ServiceShowroomLoft');s.collection.children.link(c)
M=[]
def mat(n,col,rough=.4,metal=0,emit=0,alpha=1):
 m=bpy.data.materials.new(n);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,alpha);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Alpha'].default_value=alpha;m.diffuse_color=(*col,alpha)
 if emit:bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=emit
 if alpha<1:m.surface_render_method='DITHERED'
 M.append(m);return m
floor=mat('Loft_Polished_Basalt',(.055,.073,.080),.34,.07)
steel=mat('Loft_Graphite_Steel',(.028,.043,.049),.28,.78)
stone=mat('Loft_Pale_Limestone',(.36,.38,.34),.64,.03)
wood=mat('Loft_Warm_Timber',(.17,.075,.031),.48,.03)
glass=mat('Loft_Clear_Coastal_Glass',(.31,.48,.53),.12,.02,alpha=.105)
light=mat('Loft_Warm_Luminous_Strips',(.96,.51,.19),.3,.1,emit=4)
brass=mat('Loft_Brushed_Brass',(.41,.26,.085),.28,.77)
leaf=mat('Loft_Palm_Leaf',(.058,.151,.033),.77)
trunk=mat('Loft_Palm_Trunk',(.18,.13,.082),.83)
grass=mat('Loft_Coastal_Grass',(.12,.19,.09),.93)
sea=mat('Loft_Arabian_Sea',(.075,.22,.25),.29,.12)
nearbank=mat('Loft_Coastal_Bank',(.12,.185,.12),.94)
farbank=mat('Loft_Distant_Headland',(.22,.33,.33),.96)
# Original periodic microstructure, authored mathematically. No image references.
# Both textures are packed in native source and embedded in GLB for exact PBR parity.
import numpy as np
texdir=O/'materials';texdir.mkdir(exist_ok=True)
N=128;xx,yy=np.meshgrid(np.arange(N)/N,np.arange(N)/N);rng=np.random.default_rng(1313)
# Isotropic periodic grain: radial spectral filter avoids visible directional hatching.
fx,fy=np.meshgrid(np.fft.fftfreq(N),np.fft.fftfreq(N));kernel=np.exp(-(fx*fx+fy*fy)/(.18*.18))
h=np.fft.ifft2(np.fft.fft2(rng.standard_normal((N,N)))*kernel).real
h/=max(abs(h.min()),abs(h.max()));dx=(np.roll(h,-1,1)-np.roll(h,1,1))*.08;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*.08
normal=np.stack([-dx,-dy,np.ones_like(h)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
for name,data in [('Loft_Basalt_Micro_Normal',normal*.5+.5),('Loft_Basalt_Roughness',np.repeat((.34+.032*h)[...,None],3,axis=-1))]:
 im=bpy.data.images.new(name,width=N,height=N,alpha=False);im.colorspace_settings.name='Non-Color';rgba=np.concatenate([data,np.ones((N,N,1))],axis=-1).astype(np.float32);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(texdir/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 no=floor.node_tree.nodes.new('ShaderNodeTexImage');no.name=name;no.image=im;no.extension='REPEAT';bs=floor.node_tree.nodes.get('Principled BSDF')
 if name.endswith('Normal'):
  nm=floor.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.30;floor.node_tree.links.new(no.outputs['Color'],nm.inputs['Color']);floor.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 else:floor.node_tree.links.new(no.outputs['Color'],bs.inputs['Roughness'])


def add(o,m):
 for co in list(o.users_collection):co.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m);return o

def mesh(n,v,f,m,smooth=False):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);c.objects.link(o);me.materials.append(m)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for q in me.polygons:q.use_smooth=smooth
 return o

def box(n,p,sz,m,b=.0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=n;o.scale=sz;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);add(o,m)
 if b:
  be=o.modifiers.new('Physical edge chamfer','BEVEL');be.width=b;be.segments=2;bpy.ops.object.modifier_apply(modifier=be.name)
 return o

def rod(n,a,b,r,m,nv=8):
 a=Vector(a);b=Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=nv,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=n;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return add(o,m)
# Floor at exactly ground zero, no platform that lifts the live vehicle.
slab=box('Continuous dark polished stone slab',(0,0,-.12),(20,16,.24),floor,.025)
uv=slab.data.uv_layers.active or slab.data.uv_layers.new(name='UVMap')
for poly in slab.data.polygons:
 for li in poly.loop_indices:
  v=slab.data.vertices[slab.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/.38,v.y/.38)

for x in range(-8,10,2):box('Thin floor inlay',(x,0,.0006),(.009,15.9,.0012),steel)
for y in range(-6,8,2):box('Thin floor inlay',(0,y,.0006),(19.9,.009,.0012),steel)
# Open front native -Y / glTF +Z. Back and side frames carry real transparent glazing.
for x in [-9.75,-4.875,0,4.875,9.75]:
 box('Rear steel mullion',(x,7.74,3.24),(.16,.20,6.48),steel,.012)
 box('Rear column footplate',(x,7.74,.045),(.34,.37,.09),steel,.012)
for side in [-1,1]:
 for y in [-4.5,0,4.5,7.74]:box('Side structural post',(side*9.75,y,3.24),(.20,.16,6.48),steel,.012)
 for y in [-6.14,-2.25,2.25,6.14]:
  width=3.0 if abs(y)>6 else 4.32
  box('Tall side clear pane',(side*9.76,y,3.28),(.015,width,6.15),glass)
 for z in [.18,3.62,6.4]:box('Side glazing rail',(side*9.75,0,z),(.20,15.55,.075),steel,.01)
 # Angled rigid braces at outer edges, clear of car and hero camera rays.
 rod('Slanted side brace',(side*9.65,4.5,.18),(side*9.65,7.65,6.25),.075,steel,8)
for x in [-7.32,-2.44,2.44,7.32]:box('Tall rear clear pane',(x,7.77,3.28),(4.70,.015,6.15),glass)
for z in [.18,3.62,6.40]:box('Rear glazing rail',(0,7.74,z),(19.6,.20,.075),steel,.01)
# Overhead I-beams; high enough not to obscure the full hero-car orbit.
for y in [-5.8,0,5.8]:
 for z in [6.29,6.55]:box('Roof structural flange',(0,y,z),(19.7,.28,.065),steel,.009)
 box('Roof structural web',(0,y,6.42),(19.7,.07,.22),steel)
for x in [-9.7,0,9.7]:box('Longitudinal roof beam',(x,0,6.45),(.18,15.7,.28),steel,.012)
# Warm rear timber soffit; camera-front roof remains a glazed skylight.
for x in [i*.32-9.6 for i in range(61)]:box('Timber ceiling slat',(x,5.0,6.61),(.28,5.6,.08),wood,.006)
for x in [-8,-4,4,8]:
 box('Suspended warm luminaire casing',(x,1.5,6.03),(.09,6.1,.10),steel,.01)
 box('Luminous down strip',(x,1.5,5.975),(.052,5.9,.01),light)
 for y in [-1,4]:rod('Luminaire suspension',(x,y,6.08),(x,y,6.28),.007,steel,6)
# Quiet premium showroom furniture outside hero centre and approach aisle.
for side in [-1,1]:
 box('Stone built in bench',(side*7.5,5.9,.30),(3.6,1.05,.60),stone,.06)
 box('Timber bench seat',(side*7.5,5.9,.64),(3.65,1.08,.075),wood,.025)
 for x in [side*7.5-.9,side*7.5+.9]:box('Bench brass seam',(x,5.9,.681),(.018,1.08,.007),brass)
box('Low workshop console',(-8.7,-1.7,.8),(1.15,3.2,1.6),steel,.04)
for y in [-2.7,-1.7,-.7]:
 box('Console bronze front',(-8.10,y,.82),(.028,.91,1.26),wood,.018)
 box('Console pull',(-8.06,y,1.19),(.035,.41,.025),brass,.005)
box('Console stone counter',(-8.7,-1.7,1.64),(1.25,3.3,.09),stone,.025)
# Exterior remains contained and below the clear inspection volume.
box('Coastal terrace',(0,11,-.055),(26,6,.11),stone)
for x in range(-12,14,2):box('Terrace stone joint',(x,11,.0002),(.012,5.99,.0004),steel)
# A gently irregular low bank replaces the ruler-straight lawn/ocean join.
vs=[];fs=[]
for i in range(81):
 x=-80+i*2
 for j in range(6):
  y=14+j*2.65+.28*math.sin(x*.12+j*.7);z=-.03+.17*math.sin(math.pi*j/5)*(1+.23*math.sin(x*.22))
  vs.append((x,y,z))
for i in range(80):
 for j in range(5):a=i*6+j;fs.append((a,a+6,a+7,a+1))
mesh('Low undulating planted coastal bank',vs,fs,grass,True)
# Subtle curved pale shore face, not a giant new island or photograph.
vs=[];fs=[]
for i in range(81):
 x=-80+i*2;y=27.25+.28*math.sin(x*.12+3.5)
 vs.extend([(x,y,-.025),(x,y+1.1+.22*math.sin(x*.2),-.065)])
 if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
mesh('Thin natural coastal shore',vs,fs,stone,True)
mesh('Calm coastal water',[(-260,26,-.07),(260,26,-.07),(260,600,-.07),(-260,600,-.07)],[(0,1,2,3)],sea)
# Two restrained distant land layers: low hazy headlands with uneven tree-line.
for layer,cy,lo,hi,base,amp,ma in [(0,180,-220,12,.3,3.0,nearbank),(1,330,-290,270,.0,4.6,farbank)]:
 vs=[];fs=[]
 for i in range(101):
  t=i/100;x=lo+(hi-lo)*t;envelope=math.sin(math.pi*t)**.7
  z=base+amp*envelope*(.58+.19*math.sin(t*19)+.13*math.sin(t*41)+.06*math.sin(t*109))
  vs.extend([(x,cy,-.12),(x,cy,z)])
  if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
 mesh('Low coastal headland layer '+str(layer),vs,fs,ma,False)
# Every palm has a different curved, tapering trunk and multi-level crown.
# Leaflets are folded tapered ribbons, not a flat umbrella or crossed broad cards.
def palm(seed,x,y,height,lean,heading):
 rng=random.Random(seed);direction=Vector((math.cos(heading),math.sin(heading),0));vs=[];fs=[];rings=19;sides=10
 for i in range(rings):
  t=i/(rings-1);p=Vector((x,y,height*t))+direction*(lean*t*t)+Vector((-.10*math.sin(t*3),.06*math.sin(t*4),0));rad=.18*(1-t)+.095*t
  # small alternating growth ridges integrated into trunk, not floating rings
  rad*=1+.055*math.sin(t*math.pi*18)
  for j in range(sides):
   a=j*math.tau/sides;vs.append(tuple(p+Vector((rad*math.cos(a),rad*math.sin(a),0))))
 for i in range(rings-1):
  for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(reversed(range(sides))));fs.append(tuple((rings-1)*sides+j for j in range(sides)))
 mesh('Palm curved tapered ringed trunk '+str(seed),vs,fs,trunk,True)
 crown=Vector((x,y,height))+direction*lean+Vector((-.10*math.sin(3),.06*math.sin(4),0))
 for j in range(17):
  a=j*2.399+rng.uniform(-.17,.17);d=Vector((math.cos(a),math.sin(a),0));side=Vector((-d.y,d.x,0))
  tier=j%4;L=rng.uniform(2.7,3.45) if tier else rng.uniform(1.6,2.25)
  lift=rng.uniform(.9,1.3) if tier else rng.uniform(1.7,2.2);drop=rng.uniform(.65,1.10) if tier in (1,2) else (rng.uniform(1.7,2.3) if tier==3 else -.15)
  def point(t):return crown+d*(L*t)+side*(.15*math.sin(t*2.3+a))+Vector((0,0,lift*math.sin(math.pi*t*.92)-drop*t))
  path=[point(k/7)for k in range(8)]
  # Tapered triangular-section rachis (one connected mesh).
  rv=[];rf=[]
  for k,p in enumerate(path):
   rr=.025*(1-k/8)+.003
   rv.extend([p-side*rr,p+side*rr,p+Vector((0,0,rr))])
  for k in range(7):
   for z in range(3):rf.append((k*3+z,k*3+(z+1)%3,(k+1)*3+(z+1)%3,(k+1)*3+z))
  mesh('Arched palm rachis',rv,rf,leaf,True)
  for k in range(1,25):
   t=k/26;length=(.50*math.sin(math.pi*t)**.6+.10)*rng.uniform(.85,1.12);width=rng.uniform(.055,.079)*(1-.32*t)
   for sign in [-1,1]:
    base=point(t+sign*.006);tip=base+side*(sign*length)+d*(.23+.10*t)+Vector((0,0,-.15-.19*t));mid=base.lerp(tip,.53)+Vector((0,0,.055));edge=d*width
    # convex crease provides highlights and a naturally drooping broken silhouette
    mesh('Folded narrow coconut leaflet',[base,mid-edge,tip,mid+edge,mid+Vector((0,0,.025))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],leaf,False)
 # Compact crown sheath and coconuts add organic attachment rather than a star joint.
 for j in range(5):
  a=j*2.399;pos=crown+Vector((.18*math.cos(a),.18*math.sin(a),-.16-.07*(j%2)))
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.105,location=pos);o=bpy.context.object;o.name='Original coconut cluster';o.scale=(.9,1,1.2);add(o,trunk)
for cfg in [(3,-7,18,5.35,1.15,.6),(8,5.5,19.7,6.15,-.75,2.3),(11,14,23,5.7,.85,-.8),(15,-16,25,6.4,1.2,1.5)]:palm(*cfg)
# Low broken grass clumps root the trees in the bank; no new obstructive foreground.
rng=random.Random(112)
for i in range(48):
 x=rng.uniform(-25,25);y=rng.uniform(16,26)
 for j in range(5):
  a=rng.uniform(0,math.tau);h=rng.uniform(.18,.42);d=Vector((math.cos(a),math.sin(a),0));base=Vector((x,y,.015));tip=base+d*h*.6+Vector((0,0,h));mid=base.lerp(tip,.6)+Vector((0,0,.08));side=Vector((-d.y,d.x,0))*.023
  mesh('Fine coastal grass blade',[base-side,base+side,mid+side,tip,mid-side],[(0,1,2),(0,2,4),(2,3,4)],leaf)
# Rounded tapered ceramic vessels with a genuine recessed soil opening.
for x in [-8.1,8.1]:
 vs=[];fs=[];prof=[(.30,.0),(.35,.06),(.41,.68),(.405,.76),(.35,.76),(.34,.68)]
 for rad,z in prof:
  for j in range(32):a=j*math.tau/32;vs.append((x+rad*math.cos(a),6.1+rad*math.sin(a),z))
 for k in range(len(prof)-1):
  for j in range(32):a=k*32+j;b=k*32+(j+1)%32;fs.append((a,b,b+32,a+32))
 mesh('Rounded honed ceramic planter',vs,fs,stone,True)
 mesh('Recessed planter soil',[(x+.337*math.cos(j*math.tau/32),6.1+.337*math.sin(j*math.tau/32),.685)for j in range(32)],[tuple(range(32))],trunk)
 for k in range(14):
  a=k*2.399;d=Vector((math.cos(a),math.sin(a),0));side=Vector((-d.y,d.x,0));base=Vector((x,6.1,.70));tip=base+d*(.35+.09*(k%3))+Vector((0,0,.75+.19*(k%4)));mid=base.lerp(tip,.58)+Vector((0,0,.16));w=.075
  mesh('Folded lance planter leaf',[base,mid-side*w,tip,mid+side*w,mid+Vector((0,0,.035))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],leaf)
# Place tabletop planters on the actual bench seat rather than intersecting it.
for o in c.objects:
 if o.type=='MESH' and o.name.startswith(('Rounded honed ceramic planter','Recessed planter soil','Folded lance planter leaf')):
  for v in o.data.vertices:
   center_x=8.1 if v.co.x>0 else -8.1
   v.co.x=center_x+(v.co.x-center_x)*.75;v.co.y=6.1+(v.co.y-6.1)*.75;v.co.z=.69+v.co.z*.75
root=bpy.data.objects.new('ServiceShowroomLoft',None);c.objects.link(root)
for o in list(c.objects):
 if o!=root:o.parent=root
root['provenance']='Original reconstructed project geometry; references for composition only. No project-wide reuse license selected by owner.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'ServiceShowroomLoft.blend'))
# Group geometry by material with evaluated world transforms; source remains editable.
source=[o for o in c.objects if o.type=='MESH'];bpy.context.view_layer.update();exports=[]
for ma in M:
 vs=[];fs=[];smooth=[];uvs=[]
 for o in source:
  if o.data.materials[0]!=ma:continue
  off=len(vs);vs.extend([tuple(o.matrix_world@v.co)for v in o.data.vertices]);fs.extend([tuple(off+i for i in q.vertices)for q in o.data.polygons]);smooth.extend([q.use_smooth for q in o.data.polygons]);uvs.extend([tuple(o.data.uv_layers.active.data[li].uv) if o.data.uv_layers.active else (0,0) for q in o.data.polygons for li in q.loop_indices])
 if not fs:continue
 me=bpy.data.meshes.new('Export_'+ma.name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('ServiceShowroomLoft_'+ma.name,me);s.collection.objects.link(ob);me.materials.append(ma)
 for q,sm in zip(me.polygons,smooth):q.use_smooth=sm
 uv=me.uv_layers.new(name="UVMap")
 for i,co in enumerate(uvs):uv.data[i].uv=co
 exports.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for o in exports:o.select_set(True)
path=W/'ServiceShowroomLoft.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
# Remove zero-area bevel triangles after float32 encoding, without changing vertices/materials.
raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jl]);bo=20+jl;bl=struct.unpack_from('<I',raw,bo)[0];binary=bytearray(raw[bo+8:bo+8+bl]);removed=0
for mm in g['meshes']:
 for pr in mm['primitives']:
  a=g['accessors'][pr['attributes']['POSITION']];av=g['bufferViews'][a['bufferView']];aoff=av.get('byteOffset',0)+a.get('byteOffset',0);step=av.get('byteStride',12)
  ia=g['accessors'][pr['indices']];iv=g['bufferViews'][ia['bufferView']];io=iv.get('byteOffset',0)+ia.get('byteOffset',0);fmt={5123:'H',5125:'I'}[ia['componentType']];sz=struct.calcsize('<'+fmt);ids=struct.unpack_from('<'+str(ia['count'])+fmt,binary,io);valid=[]
  for j in range(0,len(ids),3):
   pts=[Vector(struct.unpack_from('<fff',binary,aoff+ids[j+k]*step))for k in range(3)]
   if (pts[1]-pts[0]).cross(pts[2]-pts[0]).length_squared<1e-18:removed+=1
   else:valid.extend(ids[j:j+3])
  struct.pack_into('<'+str(len(valid))+fmt,binary,io,*valid);ia['count']=len(valid);iv['byteLength']=len(valid)*sz
  if 'min'in ia:ia['min']=[min(valid)]
  if 'max'in ia:ia['max']=[max(valid)]
jb=json.dumps(g,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);new=struct.pack('<III',0x46546c67,2,28+len(jb)+len(binary))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(binary),0x004e4942)+binary;path.write_bytes(new)
print('Removed degenerate exported bevel triangles',removed,flush=True)
shutil.copy2(path,P/path.name)
d=path.read_bytes();ln=struct.unpack_from('<I',d,12)[0];doc=json.loads(d[20:20+ln]);tri=sum(doc['accessors'][pr['indices']]['count']//3 for me in doc['meshes']for pr in me['primitives']);draws=sum(len(me['primitives'])for me in doc['meshes'])
m={'asset':'ServiceShowroomLoft','file':path.name,'reconstructed':True,'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d),'triangles':tri,'draws':draws,'native_source':'assets/showroom/ServiceShowroomLoft.blend','native_collection':'ServiceShowroomLoft','native_parts':len(source),'degenerate_bevel_triangles_removed':removed,'floor_y':0,'stage_y':0,'interior_footprint_m':[20,16],'roof_y_m':[6.25,6.65],'open_front_axis':'+Z','car_forward':'+X','car_included':False,'hero_camera_three':[7.5,2.5,8.5],'hero_target_three':[0,.75,0],'portrait_camera_three':[8,2.7,9.2],'lamp_anchors_three':[{'position':[1,5.6,2],'color':'#ffd2a0','intensity_hint':1500},{'position':[-4,4.7,-3],'color':'#d8edff','intensity_hint':1700},{'position':[5,5.5,-4],'color':'#fff2dc','intensity_hint':1100}],'materials':[ma.name for ma in M],'purpose':'Menu-only coastal loft with modeled exterior. No gameplay collision. Strip emission is decorative; runtime needs scene lights. Actual interactive car must be loaded independently.','provenance':'Original project geometry and original mathematical microstructure maps; reuse license not selected by owner. No downloaded geometry or reference pixels embedded.', 'revision':'V13 bounded believable-material and coastal-foliage refinement', 'pbr_microstructure':{'material':'Loft_Polished_Basalt','original_maps_px':[128,128],'uv_period_m':.38,'roughness_range':[.308,.372],'metallic':.07,'normal_scale':.30,'images_embedded':True}, 'camera_volume_preserved':True}
for out in [O/'loft_manifest.json',W/'showroom_loft_manifest.json',P/'showroom_loft_manifest.json']:out.write_text(json.dumps(m,indent=2))
print('LOFT_EXPORTED',json.dumps(m),flush=True)
for o in exports:bpy.data.objects.remove(o,do_unlink=True)
if '--no-render' in sys.argv:sys.exit()
# Scene preview contains actual recovered runtime car separately, never in architecture GLB.
bpy.ops.import_scene.gltf(filepath=str(P/'car.glb'))
s.render.engine='CYCLES';s.cycles.samples=96;s.cycles.use_denoising=False;s.cycles.max_bounces=5;s.cycles.transparent_max_bounces=8
s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.35
w=bpy.data.worlds.new('Soft coastal daylight');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.44,.57,.69,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;s.world=w
for loc,power,size,color in [((1,-2,5.6),1700,5,(1,.82,.63)),((-4,3,4.7),2100,5,(.75,.88,1)),((5,4,5.5),1500,4,(1,.92,.76))]:
 ld=bpy.data.lights.new('Preview soft key','AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color;ob=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
ld=bpy.data.lights.new('Coastal late afternoon sun','SUN');ld.energy=2.0;ld.angle=.12;ld.color=(1,.84,.62);ob=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(ob);ob.rotation_euler=(.48,-.42,-.6)
cam=bpy.data.cameras.new('Loft hero camera');ob=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(ob);ob.location=(7.5,-8.5,2.5);ob.rotation_euler=(Vector((0,0,.78))-ob.location).to_track_quat('-Z','Y').to_euler();cam.lens=40;s.camera=ob
s.render.filepath=str(O/'ServiceShowroomLoft_preview.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'ServiceShowroomLoft_Preview.blend'));bpy.ops.render.render(write_still=True)
print('LOFT_PREVIEW_READY',s.render.filepath,flush=True)
