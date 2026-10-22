import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/environment/Kerala_Coastal_Assets.blend'))
s=bpy.context.scene
for o in list(s.objects):
    if o.type not in ('CAMERA','LIGHT'):o.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=1000,location=(0,0,-.05));g=bpy.context.object;m=bpy.data.materials.new('WebQA_Backdrop');m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.12,.13,.115,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8;g.data.materials.append(m)
s.render.resolution_x=900;s.render.resolution_y=700;s.cycles.samples=32;s.render.threads=2;s.view_settings.exposure=-2
for name,cam,target in [('CoconutPalm_A',(13,-18,11),(0,0,5)),('KeralaHouse',(11,-13,8),(0,0,2)),('FishingBoat',(7,-7,5),(0,0,.4))]:
    previous=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(OUT/(name+'.glb')));created=set(bpy.data.objects)-previous
    s.camera.location=cam;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=48
    s.render.filepath=str(OUT/(name+'_optimized_preview.png'));bpy.ops.render.render(write_still=True)
    for o in created:bpy.data.objects.remove(o,do_unlink=True)
print('OPTIMIZED_PREVIEWS_COMPLETE')
