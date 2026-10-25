"""Actual exported helicopter GLBs, CPU Blender studio previews, not gameplay."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/helicopter'
for key in os.environ.get('HELI_VARIANTS','civilian,police').split(','):
 bpy.ops.wm.read_factory_settings(use_empty=True);file=R/'assets/web'/('helicopter_'+key+'.glb');hash_=hashlib.sha256(file.read_bytes()).hexdigest();bpy.ops.import_scene.gltf(filepath=str(file));s=bpy.context.scene
 s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('HELI_SAMPLES','64'));s.cycles.use_denoising=False;s.cycles.max_bounces=5;s.cycles.transparent_max_bounces=8;s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25
 w=bpy.data.worlds.new('Soft coastal aircraft studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.28,.36,.44,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.55;s.world=w
 mat=bpy.data.materials.new('Studio ground only');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.15,.19,.22,1);bs.inputs['Roughness'].default_value=.62;bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));bpy.context.object.data.materials.append(mat)
 def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 for name,loc,power,size,col in [('Warm long key',(3,6,10),2900,7,(1,.92,.8)),('Sky fill',(1,-5,6),2300,6,(.76,.89,1)),('Tail rim',(-7,4,6),1900,5,(1,.96,.89)),('Nose fill',(7,0,3),1100,4,(.9,.96,1))]:
  ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=col;ob=bpy.data.objects.new(name,ld);s.collection.objects.link(ob);ob.location=loc;aim(ob,(-1,0,1.4))
 cam=bpy.data.cameras.new('Aircraft studio camera');ob=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(ob);s.camera=ob;images={}
 for mode in os.environ.get('HELI_MODES','front,rear').split(','):
  loc,target,lens={'front':((11,13,6.7),(-1.6,0,1.7),46),'rear':((-13,-12,6.3),(-2.1,0,1.7),46),'detail':((7,7.5,3.8),(.10,0,1.6),52)}[mode];ob.location=loc;aim(ob,target);cam.lens=lens;out=O/key/('preview_'+mode+'.png');s.render.filepath=str(out);bpy.ops.wm.save_as_mainfile(filepath=str(O/key/('preview_'+mode+'.blend')));bpy.ops.render.render(write_still=True);images[mode]={'file':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_glb_sha256':hash_,'samples':s.cycles.samples,'denoising':False,'camera_native':loc,'target_native':target,'lens_mm':lens,'resolution':[1200,800]};print('HELICOPTER_PREVIEW_READY',str(out),flush=True)
  (O/key/('preview_'+mode+'_provenance.json')).write_text(json.dumps({'scope':'Actual GLB imported into Blender CPU Cycles; studio render, not gameplay. No reference pixels.','image':images[mode]},indent=2))
