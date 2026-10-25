"""Original editable highland shade tree and highway/estate gateway modules."""
import bpy,bmesh,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/highlands';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.name='Highland_Prop_Library';scene.unit_settings.system='METRIC'
def mat(n,c,rough=.8):
 m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;return m
wood=mat('Highlands_Tree_Bark',(.21,.12,.063));leaf=mat('Highlands_Shade_Leaf',(.12,.30,.075));steel=mat('Highlands_Gateway_Steel',(.48,.52,.50),.43);green=mat('Highlands_Estate_Sign_Green',(.035,.17,.12));white=mat('Highlands_WeatheredWhite',(.85,.84,.74));assets={};active=None
F=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def mesh(n,v,f,m):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);active.objects.link(o);o.data.materials.append(m);return o
def box(n,c,s,m):
 x,y,z=c;a,b,d=[v/2 for v in s];return mesh(n,[(x-a,y-b,z-d),(x+a,y-b,z-d),(x+a,y+b,z-d),(x-a,y+b,z-d),(x-a,y-b,z+d),(x+a,y-b,z+d),(x+a,y+b,z+d),(x-a,y+b,z+d)],F,m)
def beam(n,a,b,r,m,sides=8):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0))).normalized();v=d.cross(u);vs=[tuple(p+r*(math.cos(k*math.tau/sides)*u+math.sin(k*math.tau/sides)*v)) for p in [a,b] for k in range(sides)];fs=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))]+[(k,(k+1)%sides,(k+1)%sides+sides,k+sides) for k in range(sides)];return mesh(n,vs,fs,m)
def canopy(n,c,s):
 # Original irregular ellipsoidal leaf clusters; smooth crown, no downloaded geometry.
 v=[(c[0],c[1],c[2]-s[2])];rings=5;segments=12
 for j in range(1,rings+1):
  lat=-math.pi/2+math.pi*j/(rings+1)
  for k in range(segments):
   a=k*math.tau/segments;noise=1+.07*math.sin(k*2.7+j*1.8);v.append((c[0]+s[0]*math.cos(lat)*math.cos(a)*noise,c[1]+s[1]*math.cos(lat)*math.sin(a)*noise,c[2]+s[2]*math.sin(lat)))
 v.append((c[0],c[1],c[2]+s[2]));f=[]
 for k in range(segments):f.append((0,1+(k+1)%segments,1+k))
 for j in range(rings-1):
  for k in range(segments):a=1+j*segments+k;b=1+j*segments+(k+1)%segments;f.append((a,b,b+segments,a+segments))
 for k in range(segments):f.append((len(v)-1,1+(rings-1)*segments+k,1+(rings-1)*segments+(k+1)%segments))
 o=mesh(n,v,f,leaf)
 for p in o.data.polygons:p.use_smooth=True
 return o
active=bpy.data.collections.new('HighlandShadeTree');scene.collection.children.link(active);assets[active.name]={'collection':active,'description':'Original tall shade tree for tea estates, branching trunk and irregular umbrella crowns.','proxies':[{'center_blender':[0,0,4.9],'size_blender':[.6,.6,9.8],'kind':'tree_trunk'}]}
beam('Trunk',(0,0,0),(.20,.1,9.3),.23,wood)
for k in range(7):
 a=k*math.tau/7;p=(math.cos(a)*2.6,math.sin(a)*2.6,8.3+(k%3)*.65);beam('Branch',(.12,0,5.8+(k%2)),p,.10,wood,6);canopy('LeafCrown',p,(2.45,2.2,1.35))
canopy('TopCrown',(.15,.0,10.0),(2.8,2.6,1.45))
active=bpy.data.collections.new('HighlandGateway');scene.collection.children.link(active);assets[active.name]={'collection':active,'description':'Original unbranded highway exit gantry, front faces local -X.','proxies':[]}
for y in [-6.3,6.3]:box('GantryPost',(0,y,3.7),(.30,.30,7.4),steel);assets[active.name]['proxies'].append({'center_blender':[0,y,3.7],'size_blender':[.30,.30,7.4],'kind':'sign_post'})
box('Crossbeam',(0,0,7.0),(.32,12.9,.32),steel);box('DirectionBoard',(-.09,0,6.2),(.18,11.8,1.55),green);assets[active.name]['proxies'].append({'center_blender':[0,0,6.2],'size_blender':[.32,11.8,1.55],'kind':'sign_board'})
for text,z,size in [('TEA HILLS',6.27,.63),('BIRD ROCK VIEWPOINT',5.76,.36)]:
 cu=bpy.data.curves.new('GantryLettering','FONT');cu.body=text;cu.size=size;cu.align_x='CENTER';cu.extrude=.003;cu.resolution_u=1;o=bpy.data.objects.new('GantryLettering',cu);active.objects.link(o);o.location=(-.195,0,z);o.rotation_euler=(math.pi/2,0,-math.pi/2);cu.materials.append(white);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
for a in assets.values():
 for o in a['collection'].objects:
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-7]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Highland_Props.blend'))
report={'license':'Original procedural geometry. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No external geometry/photo textures.','axes':'Blender X forward,Y left,Z up; GLB X forward,Y up,-Z left.','assets':{}}
for name,a in assets.items():
 groups={};copies=[]
 for original in a['collection'].objects:
  o=original.copy();o.data=original.data.copy();scene.collection.objects.link(o);copies.append(o);groups.setdefault(o.data.materials[0].name,[]).append(o)
 merged=[]
 for key,obs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in obs:o.select_set(True)
  bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name+'_'+key;bm=bmesh.new();bm.from_mesh(o.data);bad=[f for f in bm.faces if f.calc_area()<1e-7]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(o.data);bm.free();merged.append(o)
 bpy.ops.object.select_all(action='DESELECT')
 for o in merged:o.select_set(True)
 path=WEB/(name+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
 pts=[o.matrix_world@v.co for o in merged for v in o.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];report['assets'][name]={'file':path.name,'triangles':sum(len(p.vertices)-2 for o in merged for p in o.data.polygons),'draws':len(merged),'bytes':path.stat().st_size,'bounds_blender':{'min':lo,'max':hi},'description':a['description'],'collision_boxes_blender':a['proxies'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()};shutil.copy2(path,PUBLIC/path.name)
 for o in merged:bpy.data.objects.remove(o,do_unlink=True)
for p in [OUT/'highland_prop_manifest.json',WEB/'highland_prop_manifest.json',PUBLIC/'highland_prop_manifest.json']:p.write_text(json.dumps(report,indent=2))
print('HIGHLAND_PROPS_READY',report)
