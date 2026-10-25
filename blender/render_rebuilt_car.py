"""Actual reconstructed GLB studio render, no beauty-mesh substitute. CAR_ID required."""
import bpy,os,hashlib,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];key=os.environ.get('CAR_ID','vermilion');OUT=ROOT/'assets/cars'/key;WEB=ROOT/'assets/web';file=WEB/f'car_{key}.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(file));scene=bpy.context.scene;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{key}_runtime_roundtrip.blend'));sha=hashlib.sha256(file.read_bytes()).hexdigest()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=int(os.environ.get('CAR_SAMPLES','64'));scene.cycles.use_denoising=False;scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.compression=100
w=bpy.data.worlds.new('Neutral vehicle studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.20,.25,.30,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.48;scene.world=w
floor=bpy.data.materials.new('Studio floor only');floor.use_nodes=True;p=floor.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.12,.15,.18,1);p.inputs['Roughness'].default_value=.45;bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));fo=bpy.context.object;fo.data.materials.append(floor)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size,color,sy=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size;d.size_y=sy or size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,(0,0,.7))
light('Long warm key',(1,4,6),1250,5,(1,.94,.86),3);light('Cool side strip',(-1,-4,4),1050,5,(.78,.89,1),1.6);light('Rear rim',(-4,1.5,3),850,3,(1,.94,.83));light('Front face fill',(5,1,2.5),450,3,(.88,.94,1))
d=bpy.data.cameras.new('57mm consistent gallery camera');d.lens=57;cam=bpy.data.objects.new('Studio camera',d);scene.collection.objects.link(cam);scene.camera=cam;images={}
for tag in os.environ.get('CAR_RENDER_MODES','front,rear,thumb').split(','):
 loc,target={'front':((6.1,6.8,2.7),(.12,0,.72)),'rear':((-5.9,-6.6,2.8),(-.1,0,.75)),'thumb':((6.1,6.8,2.7),(.12,0,.72))}[tag];cam.location=loc;aim(cam,target)
 if tag=='thumb':scene.render.resolution_x=512;scene.render.resolution_y=320;scene.cycles.samples=128;scene.render.film_transparent=True;fo.is_shadow_catcher=True;dest=ROOT/'assets/gallery_thumbnails'/f'car_thumb_{key}.png';dest.parent.mkdir(parents=True,exist_ok=True)
 else:scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.film_transparent=False;fo.is_shadow_catcher=False;dest=OUT/f'preview_{tag}.png'
 scene.render.filepath=str(dest);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'preview_{tag}.blend'));bpy.ops.render.render(write_still=True);images[tag]={'path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
 if tag=='thumb':
  for p in(WEB,ROOT/'web/public/assets'):shutil.copy2(dest,p/dest.name)
 print('REBUILT_PREVIEW_READY',key,tag,str(dest),flush=True)
(OUT/'render_provenance.json').write_text(json.dumps({'source_glb_sha256':sha,'images':images,'source':'Actual final GLB imported into Blender. These are studio renders, not gameplay.','reconstruction':True},indent=2))
