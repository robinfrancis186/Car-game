"""Preview the two small authored utility modules without regenerating frozen assets."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/infrastructure/transit/previews'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/infrastructure/transit/Kerala_Transit_Infrastructure.blend'));s=bpy.context.scene
w=bpy.data.worlds.new('UtilityPreviewSky');w.use_nodes=True;w.node_tree.nodes.get('Background').inputs[0].default_value=(.42,.53,.61,1);w.node_tree.nodes.get('Background').inputs[1].default_value=.5;s.world=w
bpy.ops.object.light_add(type='AREA',location=(4,-6,12));o=bpy.context.object;o.data.energy=1000;o.data.size=8;o.rotation_euler=(Vector((0,0,2))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN');o=bpy.context.object;o.data.energy=1.7;o.rotation_euler=(.4,-.5,-.6)
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=768;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
for name,pos,target,scale in [('Streetlight',(10,-14,9),(0,-.5,4.2),17),('SideStreetSegment',(19,-25,20),(0,0,.1),29)]:
 for c in s.collection.children:
  for o in c.objects:o.hide_render=c.name!=name
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('UTILITY_PREVIEW',name,flush=True)
