"""Original SOLO bank/wall proof course from one canonical analytic profile.
No source-video pixels/geometry, no inherited coast edits, no reuse license grant.
Run Blender -b --factory-startup --python this_file.py; previews are separate.
"""
import bpy,math,json,sys,hashlib,shutil,struct
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'assets/surface_test';W=R/'assets/web';P=R/'web/public/assets'
O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'blender'));import rebuild_car_helpers as h
profile_path=R/'docs/v16/surface_profile.json';cfg=json.loads(profile_path.read_text())
L=cfg['length'];H=cfg['baseY'];HW=cfg['halfWidth'];K=cfg['bankKnots']
assert cfg['sign']=='positive-right-rises' and cfg['interpolation']=='quintic-smoothstep'
def angle(s):
 for a,b in zip(K,K[1:]):
  if a['s']<=s<=b['s']:
   t=max(0,min(1,(s-a['s'])/(b['s']-a['s'])));d=math.radians(b['degrees']-a['degrees']);q=t*t*t*(10+t*(-15+6*t));qd=30*t*t*(t-1)*(t-1)/(b['s']-a['s']);return math.radians(a['degrees'])+d*q,d*qd
 return math.radians(K[-1]['degrees'] if s>L else K[0]['degrees']),0

def three(s,l,n=0):
 a,d=angle(s);base=Vector((s,H+l*math.sin(a),l*math.cos(a)));normal=Vector((-l*d,math.cos(a),-math.sin(a))).normalized();return base+normal*n

def native(v):return (v[0],-v[2],v[1])
def v(s,l,n=0):return native(three(s,l,n))
def p3(q):return (q[0],q[2],-q[1])
def face_mesh(name,vertices,faces,material):
 ob=h.mesh(name,vertices,faces,material,False)
 # BMesh's recalc on disconnected open patches can choose either orientation.
 # Explicitly orient each driving/paint triangle against the shared analytic normal.
 if h.CURRENT and h.CURRENT.name=='SurfaceTest_Road' and any(t in material.name for t in ('asphalt','lane white','safety amber')):
  for f in ob.data.polygons:
   c=f.center;q=Vector((c.x,c.z,-c.y));aa,dd=angle(q.x);u=(q.y-H)*math.sin(aa)+q.z*math.cos(aa);expected=Vector((-u*dd,math.cos(aa),-math.sin(aa)));actual=Vector((f.normal.x,f.normal.z,-f.normal.y))
   if actual.dot(expected)<0:f.flip()
  ob.data.update()
 return ob

h.reset();roots={name:h.empty('SurfaceTest_'+name)for name in ('Road','Furniture','Terrain')}
asphalt=h.material('SurfaceTest asphalt aggregate',(.065,.073,.072),rough=.94,coat=0);asphalt['double_sided']=True
white=h.material('SurfaceTest weathered lane white',(.78,.80,.72),rough=.72,coat=0)
yellow=h.material('SurfaceTest safety amber',(.96,.55,.035),rough=.68,coat=0)
concrete=h.material('SurfaceTest precast concrete',(.32,.35,.34),rough=.89,coat=0)
metal=h.material('SurfaceTest galvanised steel',(.33,.40,.41),metal=.68,rough=.43,coat=0)
dark=h.material('SurfaceTest graphite signs',(.018,.033,.038),rough=.69,coat=0)
ground=h.material('SurfaceTest dry coastal gravel',(.30,.33,.25),rough=.99,coat=0)
# Original procedural microtexture in native view; runtime uses existing asphalt shader.
n=asphalt.node_tree.nodes;l=asphalt.node_tree.links;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
ss=[float(i)for i in range(0,int(L)+1,4)]
deckss=[float(i)for i in range(0,int(L)+1,8)]+[float(L)]
h.CURRENT=roots['Road']
# Adaptive tessellation limits bank-angle and lateral-normal changes separately.
# Cross-rows are mathematically straight, so differing lateral counts share
# precisely coincident boundaries (no position cracks despite T-junctions).
adaptive=[];angular_tolerance=math.radians(.36)
for ka,kb in zip(K,K[1:]):
 change=abs(math.radians(kb['degrees']-ka['degrees']))
 if change<1e-9:
  count=math.ceil((kb['s']-ka['s'])/10);segment_s=[ka['s']+(kb['s']-ka['s'])*j/count for j in range(count+1)]
 else:
  count=math.ceil(change/angular_tolerance);segment_s=[]
  for j in range(count+1):
   target=j/count;lo=0.;hi=1.
   for iteration in range(45):
    t=(lo+hi)/2;q=t*t*t*(10+t*(-15+6*t))
    if q<target:lo=t
    else:hi=t
   segment_s.append(ka['s']+(kb['s']-ka['s'])*(lo+hi)/2)
  segment_s[0]=float(ka['s']);segment_s[-1]=float(kb['s'])
 fine_s=[]
 for sa,sb in zip(segment_s,segment_s[1:]):
  divisions=math.ceil((sb-sa)/4);fine_s.extend(sa+(sb-sa)*j/divisions for j in range(divisions))
 fine_s.append(segment_s[-1]);segment_s=fine_s
 for sa,sb in zip(segment_s,segment_s[1:]):
  md=max(abs(angle(sa)[1]),abs(angle(sb)[1]),abs(angle((sa+sb)/2)[1]));nd=max(1,math.ceil(2*HW*md/angular_tolerance));adaptive.append((sa,sb,nd))
vs=[];fs=[];uvcoords=[]
for sa,sb,nd in adaptive:
 start=len(vs)
 for sx in(sa,sb):
  for j in range(nd+1):
   u=-HW+2*HW*j/nd;vs.append(v(sx,u));uvcoords.append((sx,u))
 for j in range(nd):
  a=start+j;b=a+nd+1;c=b+1;d=a+1;fs.extend([(a,c,b),(a,d,c)])
road=face_mesh('SurfaceTest_Driveable_Asphalt',vs,fs,asphalt)
uv=road.data.uv_layers.new(name='Metres')
for poly in road.data.polygons:
 for li in poly.loop_indices:uv.data[li].uv=uvcoords[road.data.loops[li].vertex_index]
# Edge fascia envelope: 24cm below local support normal; not another driveable lane.
for side in(-1,1):
 vv=[v(s,side*HW,n)for s in deckss for n in(0,-.24)];ff=[]
 for i in range(len(deckss)-1):
  a=i*2;ff.append((a,a+1,a+3,a+2)if side>0 else(a+2,a+3,a+1,a))
 face_mesh('Deck exposed edge',vv,ff,concrete)
# No broad cosmetic underside: a coarsely tessellated sheet would intersect
# the twisting top. The analytic proof is a two-sided zero-thickness ribbon;
# edge fascia and real open supports provide the visible structural thickness.
# Flat approach and runout paint plus bank guidance remain surface-following.
def stripe(name,start,end,u0,u1,mat):
 ts=[start]+sorted(set(s for a,b,n in adaptive for s in(a,b)if start<s<end))+[end];vv=[v(s,u,.007)for s in ts for u in(u0,u1)];ff=[]
 for i in range(len(ts)-1):a=i*2;ff.extend([(a,a+3,a+2),(a,a+1,a+3)])
 return face_mesh(name,vv,ff,mat)
for side in(-1,1):
 for start in range(0,int(L),8):stripe('Broken safety edge guidance',start,min(L,start+4),side*5.68,side*5.80,white)
for s in range(0,int(L)-4,16):stripe('Dashed centre guidance',s,s+5,-.06,.06,white)
for s0 in(132,150,750,768,850,868):
 for j in range(12):stripe('Entry and runout hazard paint',s0,s0+.50,-5.8+j*.96,-5.8+(j+1)*.96,yellow if j%2==0 else asphalt)
# Low-poly guidance beams outside the12m driving strip; no solid rail/cross-road barrier.
h.CURRENT=roots['Furniture']
for side in(-1,1):
 railss=[float(i)for i in range(0,int(L)+1,8)]+[float(L)]
 vv=[v(s,side*(HW+.38)+du,.52+dn)for s in railss for du,dn in[(-.075,-.075),(.075,-.075),(.075,.075),(-.075,.075)]];ff=[]
 for i in range(len(railss)-1):
  for j in (1,2):a=i*4+j;b=i*4+(j+1)%4;ff.append((a,b,b+4,a+4))
 face_mesh('Outer segmented safety beam',vv,ff,metal)
 for s in range(0,int(L)+1,24):h.line('Safety rail stanchion',[v(s,side*(HW+.38),-.16),v(s,side*(HW+.38),.52)],.055,metal,4)
# Structural bents: real ground-to-deck supports, outside the vehicle inspection path.
colliders=[]
for s in range(12,int(L),30):
 a,da=angle(s)
 for u in(-4.8,4.8):
  top=three(s,u,-.42);foot=Vector((top.x,0,top.z));mid=(top+foot)/2
  h.box('Precast support pier',native(mid),(.50,.50,top.y),concrete,0)
  colliders.append({'id':f'surface-pier-{s}-{u}','shape':'box','x':mid.x,'z':mid.z,'halfLength':.25,'halfWidth':.25,'heading':0,'radius':.36,'y':0,'height':top.y})
 h.line('Transverse deck support',[v(s,-5.65,-.36),v(s,5.65,-.36)],.16,metal,4)
 # Twin outboard concrete foundation pads keep structure readable against ground.
 for u in(-4.8,4.8):
  top=three(s,u,-.42)
  if s==12 or s>850:h.box('Pier foundation pad',(top.x,-top.z,.12),(1.1,1.1,.24),concrete,0)
# Direction-facing original sign lettering; no bitmap/reference textures.
def label(name,body,loc,size,mat):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=0;cu.resolution_u=2;ob=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(ob);cu.materials.append(mat);ob.location=loc
 ob.rotation_euler=Matrix(((0,0,-1),(-1,0,0),(0,1,0))).to_quaternion().to_euler();h.parent_keep(ob,h.CURRENT)
for s,z,textbody in[(110,-9.5,'BANK LAB\nSOLO'),(210,-9.5,'9°'),(260,-9.5,'45°'),(310,-9.5,'81°'),(390,-9.5,'90° WALL'),(690,-9.5,'FLATTEN'),(840,-9.5,'SLOW\nRETURN'),(884,-9.5,'END')]:
 h.box('Upright angle marker panel',(s,-z,9.15),(.14,3.3,1.2),dark,0)
 for zz in(-1.25,1.25):h.box('Sign support',(s,-z+zz,4.4),(.11,.11,8.8),metal,0)
 label('Original bank direction marker',textbody,(s-.082,-z,9.15),.38,yellow)
 # Upright panel is entirely outside the road and its swept rail extent.
 colliders.append({'id':f'surface-sign-{s}','shape':'box','x':s,'z':z,'halfLength':.09,'halfWidth':1.7,'heading':0,'radius':1.71,'y':0,'height':9.8})
# Contained dryland scene: no water or ocean collision semantics.
h.CURRENT=roots['Terrain']
face_mesh('Safe ground below course',[(-600,500,0),(1500,500,0),(1500,-500,0),(-600,-500,0)],[(0,2,1),(0,3,2)],ground)
# Low distant mound silhouettes original/restrained; do not intrude test play space.
for i in range(8):
 x=-80+i*145;z=95+(i%3)*16;h.box('Distant harbour service block',(x,-z,1.1+(i%2)*.4),(24+4*(i%3),12,2.2+(i%2)*.8),concrete,0)
# Freeze editable source BEFORE exporting anything; no car or reference scene included.
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Surface_Test_Route.blend'))
reports=[]
for name,root in roots.items():
 manifest={};out=W/f'SurfaceTest_{name}.glb';h.export_glb([root],out,manifest)
 if name=='Road':
  # Shared rigid serializer intentionally omits UVs. Add this new course's
  # authored metric ribbon coordinates without modifying that shared helper.
  raw=out.read_bytes();jn=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jn]);bn=struct.unpack_from('<I',raw,20+jn)[0];binary=bytearray(raw[28+jn:28+jn+bn])
  for me in doc['meshes']:
   for prim in me['primitives']:
    if 'asphalt' not in doc['materials'][prim['material']]['name']:continue
    ac=doc['accessors'][prim['attributes']['POSITION']];bv=doc['bufferViews'][ac['bufferView']];off=bv.get('byteOffset',0)+ac.get('byteOffset',0);uvs=[]
    for i in range(ac['count']):
     x,y,z=struct.unpack_from('<fff',binary,off+i*12);aa,_=angle(x);u=(y-H)*math.sin(aa)+z*math.cos(aa);uvs.extend((x*.5,u*.5))
    while len(binary)%4:binary.append(0)
    off=len(binary);binary.extend(struct.pack('<'+str(len(uvs))+'f',*uvs));bi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(uvs)*4,'target':34962});ai=len(doc['accessors']);doc['accessors'].append({'bufferView':bi,'componentType':5126,'count':ac['count'],'type':'VEC2'});prim['attributes']['TEXCOORD_0']=ai
  doc['buffers'][0]['byteLength']=len(binary);jb=json.dumps(doc,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);binary+=b'\0'*((-len(binary))%4);raw=struct.pack('<III',0x46546c67,2,12+8+len(jb)+8+len(binary))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(binary),0x004E4942)+binary;out.write_bytes(raw);manifest.update({'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'uv_contract':'Asphalt TEXCOORD_0=(s*.5,l*.5), including vertical wall; no world-XZ collapse.'})
 shutil.copyfile(out,P/out.name)
 reports.append({'name':root.name,'file':out.name,**manifest})
# Dedicated empty furniture file avoids renderer's old Coast default.
furn={'colliders':[],'note':'Bank ribbon edge support is handled by analytic surface mode; no Coast furniture borrowed.'}
static={'colliders':colliders,'note':'Visible dryland support piers/signs only; no rewards, vehicles, water or automatic traffic.'}
runtime={'id':'surface-test','name':'Harbour Wall Run — Solo Surface Proof','version':16,'free_drive_only':True,'surface_test':True,'surface_profile':cfg,'surface_profile_file':'surface_test_profile.json','axes':{'forward':'+X','up':'+Y','right':'+Z'},'route_points':[[s,H,0]for s in range(int(L)+1)],'smoothed_length_m':L,'source_route_length_m':L,'garage_s':50,'course_meshes':[{'name':r['name'],'file':r['file'],'collision':r['name']=='SurfaceTest_Road'}for r in reports],'prop_instances':[],'checkpoints':[],'districts':[{'name':'Flat Approach','start_s':0,'end_s':160,'description':'Solo controlled entry.'},{'name':'Bank Transition','start_s':160,'end_s':360,'description':'Smooth positive-right-rise bank.'},{'name':'90° Wall','start_s':360,'end_s':540,'description':'Upright-to-wall proof only, not ceiling or loop.'},{'name':'Return and Runout','start_s':540,'end_s':L,'description':'Smoothly flatten then slow and return.'}],'explore_starts':[{'id':'approach','name':'Flat Approach','s':50}],'furniture_file':'surface_test_furniture_colliders.json','collision_file':'surface_test_colliders.json','terrain_grid':{'origin':[-600,-500],'step':[1050,1000],'count':[3,2],'heights':[0]*6,'diagonal':'sw-ne'},'road_sections':[{'startS':0,'endS':L,'halfWidth':HW,'shoulderHalfWidth':HW,'shoulderDrop':0}],'transit_routes':[],'minimap_roads':[[[s,H,0]for s in range(0,int(L)+1,10)]],'rewards_enabled':False,'traffic_enabled':False,'fictional_geography_notice':'Entirely original isolated test structure, not an OSM-derived public road or a video reconstruction.','provenance':'Original project geometry/materials; reuse license not selected by owner.'}
for filename,data in [('surface_test_profile.json',cfg),('surface_test_furniture_colliders.json',furn),('surface_test_colliders.json',static),('course_runtime_surface_test.json',runtime)]:
 for folder in(O,W,P):(folder/filename).write_text(json.dumps(data,indent=2)+'\n')
report={'source':'blender/build_surface_test_route.py','native':'assets/surface_test/Surface_Test_Route.blend','canonical_profile':'docs/v16/surface_profile.json','canonical_profile_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),'mesh_sampling':{'mode':'adaptive-angle-and-derivative','maximum_target_angle_change_degrees':.36,'segments':[[a,b,n]for a,b,n in adaptive],'diagonal':'sw-ne','analytic_normal':'normalize([-l*bankDerivative,cos(bank),-sin(bank)])'},'assets':reports,'total_triangles':sum(r['triangles']for r in reports),'total_draws':sum(r['draw_calls']for r in reports),'provenance':'Original authored proof course; reuse license not selected by owner. No source images or third-party meshes.'}
(O/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('SURFACE_TEST_READY',json.dumps({k:report[k]for k in('total_triangles','total_draws','canonical_profile_sha256')}))
