"""Actual CPU previews of the two original Highland modular Blender assets."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/highlands';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/highlands/Highland_Props.blend'));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=48;s.cycles.use_denoising=False;s.cycles.max_bounces=4;s.render.resolution_x=800;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0
w=bpy.data.worlds.new('Soft daylight');w.use_nodes=True;w.node_tree.nodes.get('Background').inputs['Color'].default_value=(.6,.72,.85,1);w.node_tree.nodes.get('Background').inputs['Strength'].default_value=.7;s.world=w
ld=bpy.data.lights.new('KeySun','SUN');lo=bpy.data.objects.new('KeySun',ld);s.collection.objects.link(lo);ld.energy=3;ld.angle=math.radians(9);lo.rotation_euler=(math.radians(28),math.radians(-30),math.radians(-25))
bpy.ops.mesh.primitive_plane_add(size=200);ground=bpy.context.object;ground.name='PreviewGround';ground.location.z=-.025;m=bpy.data.materials.new('PreviewGround');m.diffuse_color=(.28,.31,.25,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.28,.31,.25,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=1;ground.data.materials.append(m)
ca=bpy.data.cameras.new('ModulePreviewCamera');co=bpy.data.objects.new('ModulePreviewCamera',ca);s.collection.objects.link(co);s.camera=co;ca.type='ORTHO'
for name,eye,target,scale in [('HighlandShadeTree',(16,-21,14),(0,0,5.7),15.8),('HighlandGateway',(-19,-17,11),(0,0,3.9),17.5)]:
 for c in s.collection.children:c.hide_render=c.name!=name
 co.location=eye;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();ca.ortho_scale=scale;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('MODULE_PREVIEW_READY',s.render.filepath,flush=True)
