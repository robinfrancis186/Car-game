import bpy, sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Kerala_Coastal_Assets.blend'))
s=bpy.context.scene
for o in s.objects:
    if o.type not in ('CAMERA','LIGHT'):o.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.03));g=bpy.context.object
m=bpy.data.materials.new('Detail_Backdrop');m.diffuse_color=(.12,.13,.115,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.12,.13,.115,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85;g.data.materials.append(m)
s.render.resolution_x=1100;s.render.resolution_y=850;s.cycles.samples=64;s.render.threads=2;s.view_settings.exposure=-2.0
for name,cam,target in [('KeralaHouse',(11,-13,8),(0,0,2)),('CoconutPalm_A',(13,-18,11),(0,0,5)),('FishingBoat',(7,-7,5),(0,0,.4))]:
    if '--palm-only' in sys.argv and name!='CoconutPalm_A': continue
    if '--boat-only' in sys.argv and name!='FishingBoat': continue
    obj=bpy.data.objects.new('Detail_'+name,None);s.collection.objects.link(obj);obj.instance_type='COLLECTION';obj.instance_collection=bpy.data.collections[name]
    s.camera.location=cam;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=48
    s.render.filepath=str(OUT/'previews'/f'{name}_detail.png');bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(obj,do_unlink=True)
print('DETAIL_RENDERS_COMPLETE')
