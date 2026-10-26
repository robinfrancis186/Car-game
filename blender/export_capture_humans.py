"""Export editable, skinned capture LODs with existing Blender only."""
import bpy,json,struct,hashlib,shutil
from mathutils.kdtree import KDTree
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'assets/capture_humans/capture_officer_garment_fix.blend';OUT=ROOT/'assets/capture_humans/exports';OUT.mkdir(parents=True,exist_ok=True)
reports=[]
for role in ['Officer','Driver']:
 for lod in ['Near','Mobile']:
  bpy.ops.wm.open_mainfile(filepath=str(SOURCE));arm=bpy.data.objects['CAPTURE_OFFICER_RIG']
  for bone in arm.pose.bones:
   for c in list(bone.constraints):bone.constraints.remove(c)
   bone.matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update()
  meshes=[];protected_checks=[]
  for obj in list(bpy.data.objects):
   if obj.type!='MESH' or obj.parent!=arm:continue
   if role=='Driver' and any(k.lower()in obj.name.lower()for k in ['CPO','pocket','epaulette','shoulder KP','lanyard','whistle','shirt fastening','placket','patrol identification']):
    bpy.data.objects.remove(obj,do_unlink=True);continue
   if role=='Driver':
    for mat in obj.data.materials:
     if 'khaki cotton'in mat.name:mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.035,.12,.19,1)
     elif 'trouser fabric'in mat.name:mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.035,.045,.06,1)
   bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
   for modifier in list(obj.modifiers):
    if modifier.type=='SUBSURF'and lod=='Mobile':obj.modifiers.remove(modifier)
    elif modifier.type!='ARMATURE':bpy.ops.object.modifier_apply(modifier=modifier.name)
   ratio=(.62 if lod=='Near'else .25)if obj.name.startswith('MakeHuman')else(.25 if lod=='Near'else .075)
   garment=obj.name in ['Original short-sleeve uniform shirt','Original tailored uniform trousers','CPO fitted black leather belt']
   protected=[]
   if garment:
    # The entire belt zone is immutable in both LODs. Protect original seam loops too.
    uses={}
    for poly in obj.data.polygons:
     for edge in poly.edge_keys:uses[tuple(sorted(edge))]=uses.get(tuple(sorted(edge)),0)+1
    boundary={i for edge,n in uses.items()if n==1 for i in edge}
    protected=[v.co.copy()for v in obj.data.vertices if .95<=v.co.z<=1.08 or v.index in boundary or(obj.name.endswith('shirt')and v.co.z>1.37)]
   # Clothing keeps its connected surface; aggressive interior collapse tears it
   # into the body even when seam vertices are locked. Mobile omits subdivision.
   if len(obj.data.polygons)>30 and not garment:
    dec=obj.modifiers.new('Measured '+lod+' geometry reduction','DECIMATE');dec.ratio=ratio;dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
   if garment:
    tree=KDTree(len(obj.data.vertices))
    for v in obj.data.vertices:tree.insert(v.co,v.index)
    tree.balance();error=max(tree.find(p)[2]for p in protected)
    assert error<.0001,('LOD moved protected garment seams',obj.name,lod,error)
    # Keep the belt region rigid and normalized after all modifiers/reduction.
    count=0
    for v in obj.data.vertices:
     if .988<=v.co.z<=1.028:
      for g in obj.vertex_groups:g.remove([v.index])
      (obj.vertex_groups.get('pelvis')or obj.vertex_groups.new(name='pelvis')).add([v.index],1,'REPLACE');count+=1
    protected_checks.append({'garment':obj.name,'protected_vertices':len(protected),'max_seam_drift_m':error,'pelvis_waist_vertices':count})
   meshes.append(obj)
  # Consolidate by shared material into a single skinned object, keeping weights.
  bpy.ops.object.select_all(action='DESELECT')
  for obj in meshes:obj.select_set(True)
  bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();human=bpy.context.object;human.name='Capture'+role+lod
  # Existing packed CC0 texture, resized for the measured runtime LOD.
  for image in list(bpy.data.images):
   if image.source=='GENERATED' or not image.packed_file:continue
   image.scale(1024 if lod=='Near'else 512,1024 if lod=='Near'else 512)
   image.filepath_raw=str(OUT/('CaptureSkin'+lod+'.jpg'));image.file_format='JPEG';image.save();image.pack()
  bpy.ops.object.select_all(action='DESELECT');human.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
  filename='Capture'+role+lod+'.glb';target=OUT/filename
  bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_animations=False,export_skins=True,export_yup=True,export_apply=False,export_image_format='AUTO',export_extras=False)
  blob=target.read_bytes();magic,version,total=struct.unpack_from('<III',blob);assert magic==0x46546c67 and version==2 and total==len(blob)
  length,kind=struct.unpack_from('<II',blob,12);gltf=json.loads(blob[20:20+length]);
  # Blender does not export this Multiply-node constant; preserve it explicitly.
  skins=[m for m in gltf['materials']if m.get('name','').startswith('CC0 MakeHuman skin')]
  assert len(skins)==1
  skins[0]['pbrMetallicRoughness']['baseColorFactor']=[.56,.37,.26,1]
  encoded=json.dumps(gltf,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
  blob=struct.pack('<III',magic,version,20+len(encoded)+len(blob[20+length:]))+struct.pack('<II',len(encoded),kind)+encoded+blob[20+length:];target.write_bytes(blob)
  assert gltf['skins']and len(gltf['skins'][0]['joints'])>=53
  triangles=0;draws=0;vertices=0
  for mesh in gltf['meshes']:
   for primitive in mesh['primitives']:
    a=primitive['attributes'];assert 'JOINTS_0'in a and 'WEIGHTS_0'in a;assert primitive.get('mode',4)==4
    triangles+=gltf['accessors'][primitive['indices']]['count']//3;vertices+=gltf['accessors'][a['POSITION']]['count'];draws+=1
  assert any('baseColorTexture'in m.get('pbrMetallicRoughness',{})for m in gltf['materials']),'Skin texture not exported'
  assert triangles<(60000 if lod=='Near'else 35000)
  receipt={'file':filename,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'triangles':triangles,'draws':draws,'vertices':vertices,'bones':len(gltf['skins'][0]['joints']),'texture_size':1024 if lod=='Near'else 512,'role':role,'lod':lod,'skin_base_color_factor':[.56,.37,.26,1],'protected_garments':protected_checks,'garment_lod_strategy':'near subdivided / mobile connected base; no garment edge collapse'}
  reports.append(receipt);shutil.copy2(target,ROOT/'web/public/assets'/filename)
  # Preserve the exact reduced editable mesh, skeleton and materials.
  for image in bpy.data.images:
   if image.packed_file:image.filepath='//'+Path(image.filepath).name
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(target.stem+'.blend')))
  print('CAPTURE_EXPORT='+json.dumps(receipt),flush=True)
(OUT/'capture-lod-manifest.json').write_text(json.dumps(reports,indent=2)+'\n');shutil.copy2(OUT/'capture-lod-manifest.json',ROOT/'web/public/assets/capture-lod-manifest.json')
