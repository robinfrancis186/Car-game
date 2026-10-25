"""Matched actual-GLB Blender comparison; not browser/gameplay evidence."""
import bpy,math,hashlib,json,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/showroom';modes=os.environ.get('LOFT_MODES','before,after').split(',');records={}
for mode in modes:
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
 p=O/'v12_baseline/ServiceShowroomLoft.glb' if mode=='before' else R/'assets/web/ServiceShowroomLoft.glb'
 source_hash=hashlib.sha256(p.read_bytes()).hexdigest();bpy.ops.import_scene.gltf(filepath=str(p));bpy.ops.import_scene.gltf(filepath=str(R/'web/public/assets/car.glb'))
 s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=False;s.cycles.max_bounces=5;s.cycles.transparent_max_bounces=8
 s.render.resolution_x=1100;s.render.resolution_y=760;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.35
 w=bpy.data.worlds.new('Matched coastal daylight');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.44,.57,.69,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;s.world=w
 for loc,power,size,col in [((1,-2,5.6),1700,5,(1,.82,.63)),((-4,3,4.7),2100,5,(.75,.88,1)),((5,4,5.5),1500,4,(1,.92,.76))]:
  ld=bpy.data.lights.new('Matched soft key','AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=col;ob=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
 ld=bpy.data.lights.new('Matched coastal sun','SUN');ld.energy=2;ld.angle=.12;ld.color=(1,.84,.62);ob=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(ob);ob.rotation_euler=(.48,-.42,-.6)
 cam=bpy.data.cameras.new('Matched hero camera');ob=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(ob);ob.location=(7.5,-8.5,2.5);ob.rotation_euler=(Vector((0,0,.78))-ob.location).to_track_quat('-Z','Y').to_euler();cam.lens=35;s.camera=ob
 out=O/('ServiceShowroomLoft_V13_'+mode+'.png');s.render.filepath=str(out);bpy.ops.wm.save_as_mainfile(filepath=str(O/('ServiceShowroomLoft_V13_'+mode+'.blend')));bpy.ops.render.render(write_still=True)
 records[mode]={'source_loft_sha256':source_hash,'source_car_sha256':hashlib.sha256((R/'web/public/assets/car.glb').read_bytes()).hexdigest(),'image':str(out.relative_to(R)),'image_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'samples':64,'denoising':False,'camera_native':[7.5,-8.5,2.5],'target_native':[0,0,.78],'lens_mm':35,'resolution':[1100,760],'scope':'Blender CPU Cycles of actual GLB; matched lighting/camera/materials; not runtime gameplay. No reference pixels.'}
 (O/('v13_'+mode+'_render_provenance.json')).write_text(json.dumps(records[mode],indent=2))
 print('V13_COMPARISON_READY',out,flush=True)
