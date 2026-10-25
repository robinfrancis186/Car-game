"""V10 original near foliage: individual folded leaves, no photos or alpha textures.
Only new assets are written. Validated V9 route/terrain/course/collision files stay immutable.
"""
import bpy,bmesh,math,json,random,hashlib,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/foliage_detail';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets';rng=random.Random(102207)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);scene=bpy.context.scene;scene.name='Original_Near_Foliage_Library';scene.unit_settings.system='METRIC';batches={};collections={};source_bark=[]
def mat(name,color,vertices=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.88;m.use_backface_culling=False
 if vertices:
  vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='LeafTint';m.node_tree.links.new(vc.outputs['Color'],p.inputs['Base Color'])
 return m
leaf=mat('Highlands_Shade_Leaf_Detail',(1,1,1),True);tea_leaf=mat('Highlands_Tea_Leaf_Detail',(1,1,1),True);tea_stem=mat('Highlands_Tea_Stem_Detail',(.20,.27,.055));wood=mat('Highlands_Tree_Bark',(.21,.12,.063));materials={m.name:m for m in [leaf,tea_leaf,tea_stem,wood]}
def add(asset,material,verts,faces,colors=None):
 b=batches.setdefault((asset,material.name),[[],[],[]]);off=len(b[0]);b[0].extend([tuple(v) for v in verts]);b[1].extend(tuple(off+i for i in f) for f in faces);b[2].extend(colors or [(1,1,1,1)]*len(verts))
def beam(asset,a,b,r,material,sides=3):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0))).normalized();v=d.cross(u);vs=[p+r*(math.cos(k*math.tau/sides)*u+math.sin(k*math.tau/sides)*v) for p in [a,b] for k in range(sides)];fs=[(k,(k+1)%sides,(k+1)%sides+sides,k+sides) for k in range(sides)];add(asset,material,vs,fs)
def leaf_blade(asset,base,direction,length,width,color,material,six=False,normal=None,two=False):
 # Closed outline, pointed tip, folded midrib and different vertex tones. No alpha-cutout image.
 d=Vector(direction).normalized();normal=Vector(normal or (0,0,1));u=normal.cross(d)
 if u.length<.01:u=Vector((1,0,0)).cross(d)
 u.normalize();n=d.cross(u).normalized();base=Vector(base)
 if six:
  outline=[(0,0,0),(.30,-.43,.025),(.70,-.48,.04),(1,0,.065),(.70,.48,.04),(.30,.43,.025)];center=(.51,0,.065)
 else:outline=[(0,0,0),(.46,-.5,.028),(1,0,.075),(.46,.5,.028)];center=(.48,0,.08)
 vs=[base+d*(x*length)+u*(y*width)+n*(z*length) for x,y,z in outline+[center]];cc=[]
 for j in range(len(vs)):
  shade=1.08 if j==len(vs)-1 else (.87 if j in [0,1] else .98);cc.append(tuple(min(1,c*shade) for c in color)+(1,))
 # Outline above is counterclockwise when viewed from +normal.
 faces=[(len(vs)-1,j,(j+1)%(len(vs)-1)) for j in range(len(vs)-1)]
 if two:
  vs=vs[:4];cc=cc[:4];faces=[(0,1,2),(0,2,3)]
 add(asset,material,vs,faces,cc)
# Keep original trunk and seven structural branches EXACTLY, including the pivot and bark geometry.
with bpy.data.libraries.load(str(ROOT/'assets/highlands/Highland_Props.blend'),link=False) as (src,dst):dst.collections=['HighlandShadeTree']
original=dst.collections[0]
for o in original.objects:
 if o.type=='MESH' and o.data.materials and 'Bark' in o.data.materials[0].name:
  verts=[o.matrix_world@v.co for v in o.data.vertices];faces=[tuple(p.vertices) for p in o.data.polygons];add('HighlandShadeTreeNear',wood,verts,faces);source_bark.append({'name':o.name,'vertices':[list(v) for v in verts],'faces':faces})
centers=[]
for k in range(7):
 a=k*math.tau/7;centers.append(((math.cos(a)*2.6,math.sin(a)*2.6,8.3+(k%3)*.65),(2.45,2.2,1.35)))
centers.append(((.15,0,10),(2.8,2.6,1.45)))
# 120 branching sprays × 10 folded individual leaves. No smooth solid crown balloons remain.
for crown,(center,radii) in enumerate(centers):
 c=Vector(center)
 for j in range(15):
  z=1-2*(j+.5)/15;angle=j*math.pi*(3-math.sqrt(5))+crown*.77;direction=Vector((math.sqrt(1-z*z)*math.cos(angle),math.sqrt(1-z*z)*math.sin(angle),z));outer=Vector(tuple(direction[i]*radii[i] for i in range(3)));start=c+outer*.18;end=c+outer*.79;axis=(end-start).normalized();side=axis.cross(Vector((0,0,1)) if abs(axis.z)<.9 else Vector((1,0,0))).normalized();up=side.cross(axis).normalized();beam('HighlandShadeTreeNear',start,end,.012,wood)
  for pair in range(5):
   t=.2+pair*.155;base=start.lerp(end,t)
   for sign in [-1,1]:
    d=(axis*.63+side*(sign*.80)+up*rng.uniform(-.2,.2)).normalized();normal=(Vector((0,0,1))*.7+direction*.3).normalized();color=(rng.uniform(.09,.155),rng.uniform(.235,.35),rng.uniform(.035,.075));leaf_blade('HighlandShadeTreeNear',base,d,rng.uniform(.57,.76),rng.uniform(.26,.36),color,leaf,normal=normal)
# Dense tea shrub: 4 irregular dark foliage lobes (80 triangles), 36 outer leaves (72),
# and four short visible basal stems (8). Individual clumps replace, rather than cover, the tube.
for k in range(4):
 angle=k*math.tau/3 if k<3 else .4;center=Vector((math.cos(angle)*(.22 if k<3 else 0),math.sin(angle)*(.20 if k<3 else 0),.69+(k%3)*.085));radii=(.34,.31,.33)
 bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1);bm.verts.ensure_lookup_table();bm.verts.index_update();vs=[];cc=[]
 for v in bm.verts:
  fac=rng.uniform(.89,1.1);vs.append(center+Vector(tuple(v.co[i]*radii[i]*fac for i in range(3))));cc.append((rng.uniform(.07,.115),rng.uniform(.19,.27),rng.uniform(.025,.055),1))
 fs=[tuple(v.index for v in f.verts)for f in bm.faces];add('TeaLeafCluster',tea_leaf,vs,fs,cc);bm.free();base=Vector((center.x*.35,center.y*.35,0));side=Vector((-math.sin(angle),math.cos(angle),0))*.01;add('TeaLeafCluster',tea_stem,[base-side,base+side,center+side,center-side],[(0,1,2),(0,2,3)])
for j in range(36):
 ring=j//12;angle=(j%12)*math.tau/12+ring*.31;rad=.34 if ring<2 else .19;base=Vector((math.cos(angle)*rad,math.sin(angle)*rad,.55+ring*.235));d=Vector((math.cos(angle+.28),math.sin(angle+.28),.15+ring*.14)).normalized();color=(rng.uniform(.12,.20),rng.uniform(.28,.40),rng.uniform(.035,.075));leaf_blade('TeaLeafCluster',base,d,rng.uniform(.22,.30),rng.uniform(.13,.19),color,tea_leaf,two=True)
manifest={'license':'Original procedural meshes and per-vertex colors. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No photos, imported geometry, image textures or alpha cutouts.','axes':'Blender X forward/Y left/Z up; glTF X forward/Y up/-Z left.','assets':{},'tree_contract':'Original trunk and structural branch vertices/faces preserved exactly; original placement/root/scale and all physics proxies unchanged. Individual leaves and fine twigs are visual only.','tea_contract':'Local X follows tea row; root sits on the exact terrain surface, not on top of the coarse hedge. Individual foliage is visual only.'}
for (asset,matname),(verts,faces,colors) in batches.items():
 if asset not in collections:collections[asset]=bpy.data.collections.new(asset);scene.collection.children.link(collections[asset])
 me=bpy.data.meshes.new(asset+'_'+matname);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(me.name,me);collections[asset].objects.link(o);me.materials.append(materials[matname])
 if 'Leaf' in matname:
  col=me.color_attributes.new(name='LeafTint',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(colors):col.data[i].color=c
  me.color_attributes.active_color=col
 # Dark small interior lobes shade softly; individual pointed outer leaves retain their folds.
 if asset=='TeaLeafCluster' and matname=='Highlands_Tea_Leaf_Detail':
  for polygon in me.polygons[:80]:polygon.use_smooth=True
 # Avoid smoothing the individual leaf fold away.
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-10]
 if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
 bm.normal_update();bm.to_mesh(me);bm.free();me.update()
 o['provenance']='Original procedural mesh. Generator: blender/build_foliage_detail.py'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Highland_Foliage_Detail.blend'))
for asset,col in collections.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in col.objects:o.select_set(True)
 path=WEB/(asset+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
 vv=[o.matrix_world@v.co for o in col.objects for v in o.data.vertices];lo=[min(v[i] for v in vv) for i in range(3)];hi=[max(v[i] for v in vv) for i in range(3)];count=sum(len(p.vertices)-2 for o in col.objects for p in o.data.polygons);budget=6000 if asset=='HighlandShadeTreeNear' else 180
 if count>budget:raise RuntimeError(f'{asset} budget exceeded: {count}')
 manifest['assets'][asset]={'file':path.name,'triangles':count,'draws':len(col.objects),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds_blender':{'min':lo,'max':hi},'native_collection':asset,'images':0,'vertex_color_attribute':'LeafTint','visual_only':True};shutil.copy2(path,PUBLIC/path.name)
(OUT/'original_trunk_geometry.json').write_text(json.dumps(source_bark,separators=(',',':')))
for parent in [OUT,WEB,PUBLIC]:(parent/'foliage_detail_manifest.json').write_text(json.dumps(manifest,indent=2))
print('FOLIAGE_DETAIL_READY',json.dumps(manifest,indent=2))
