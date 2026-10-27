import bpy,pathlib,json
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'web/public/assets';reports=[]
for name,label in [('barrier_fence_metal_a02','SimReadyFence'),('crate_blue_a01','SimReadyCrate')]:
 for lod,ratio in [('Near',1 if label=='SimReadyFence' else .22),('Far',.35 if label=='SimReadyFence' else .055)]:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  bpy.ops.wm.usd_import(filepath=str(root/'assets/simready/source'/name/'simready_usd/payloads/base.usda'),import_materials=True)
  meshes=[o for o in bpy.data.objects if o.type=='MESH']
  # USD imports retain both prototype geometry and a collection instance.
  # Export each authored mesh once, avoiding coincident duplicate rendering.
  for obj in bpy.data.objects:
   if obj.instance_type=='COLLECTION':obj.instance_type='NONE'
  for o in meshes:
   bpy.context.view_layer.objects.active=o;o.select_set(True)
   if ratio<1:
    mod=o.modifiers.new('Web geometry reduction','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
   o.data.calc_loop_triangles()
  for img in bpy.data.images:
   if img.source=='FILE' and img.size[0]:
    img.scale(min(img.size[0],512 if lod=='Near' else 256),min(img.size[1],512 if lod=='Near' else 256));img.pack()
  triangles=sum(len(o.data.loop_triangles) for o in meshes)
  dest=out/(label+lod+'.glb')
  bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_yup=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=False)
  reports.append({'asset':name,'lod':lod,'triangles':triangles,'vertices':sum(len(o.data.vertices) for o in meshes),'bytes':dest.stat().st_size,'file':dest.name,'texture_limit':512 if lod=='Near' else 256})
(root/'assets/simready/export-receipt.json').write_text(json.dumps(reports,indent=2)+'\n');print('EXPORT_RECEIPT',json.dumps(reports))
