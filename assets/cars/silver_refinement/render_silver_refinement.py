"""Direct actual-Silver-GLB studio QA; no image retouching or gameplay claim."""
import bpy,os,hashlib,json,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[3];O=R/'assets/cars/silver_refinement';G=R/'assets/web/car_silver.glb';sha=hashlib.sha256(G.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(G));s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=int(os.environ.get('SILVER_SAMPLES','96'));s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.018;s.cycles.adaptive_min_samples=32;s.cycles.max_bounces=6;s.cycles.transparent_max_bounces=8
s.render.resolution_x=1280;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.compression=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
w=bpy.data.worlds.new('Silver neutral reflected studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.20,.25,.30,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;s.world=w
m=bpy.data.materials.new('Studio floor, not car asset');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.10,.13,.16,1);p.inputs['Roughness'].default_value=.48
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object;floor.data.materials.append(m)
def aim(o,at):o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,sy,color):
 d=bpy.data.lights.new(name,'AREA');d.shape='RECTANGLE';d.size=size;d.size_y=sy;d.energy=power;d.color=color;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;aim(o,(0,0,.7))
area('Long soft key',(-1.2,4,6),1050,5,.7,(1,.95,.88));area('Cool shoulder strip',(-1,-4,2.2),900,5,.7,(.78,.88,1));area('Rear rim',(-4,1.5,3),800,3,2,(1,.95,.88));area('Front fill',(5,1,2.5),450,3,2,(.9,.95,1))
d=bpy.data.cameras.new('Close actual-asset camera');d.lens=57;o=bpy.data.objects.new('Silver studio camera',d);s.collection.objects.link(o);s.camera=o;images={}
prior=O/'render_provenance.json'
if prior.exists():
 old=json.loads(prior.read_text())
 if old.get('source_glb_sha256')==sha:images=old.get('images',{})
for key in os.environ.get('SILVER_VIEWS','front,side,thumb').split(','):
 loc={'front':(5.8,6.7,2.55),'side':(.6,9.30,2.40),'rear':(-5.7,-6.5,2.55),'thumb':(6.1,6.8,2.7)}[key];o.location=loc;aim(o,(.12,0,.70))
 if key=='thumb':
  s.render.resolution_x=512;s.render.resolution_y=320;s.cycles.samples=160;s.render.film_transparent=True;floor.is_shadow_catcher=True;dest=R/'assets/gallery_thumbnails/car_thumb_silver.png';dest.parent.mkdir(parents=True,exist_ok=True)
 else:s.render.resolution_x=1280;s.render.resolution_y=800;s.render.film_transparent=False;floor.is_shadow_catcher=False;dest=O/f'preview_{key}.png'
 s.render.filepath=str(dest);bpy.ops.wm.save_as_mainfile(filepath=str(O/f'preview_{key}.blend'),compress=True);bpy.ops.render.render(write_still=True);images[key]={'path':str(dest.relative_to(R)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()};print('SILVER_PREVIEW_READY',key,str(dest),flush=True)
 if key=='thumb':
  for q in [R/'assets/web',R/'web/public/assets']:shutil.copy2(dest,q/dest.name)
(O/'render_provenance.json').write_text(json.dumps({'source_glb_sha256':sha,'engine':'Cycles CPU, no denoising','scope':'Direct actual exported car, studio only; not gameplay','images':images},indent=2))
