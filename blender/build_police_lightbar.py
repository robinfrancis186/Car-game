"""Original fictional lightbar, no police emblem or official vehicle claim."""
import bpy,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/web';OUT.mkdir(exist_ok=True,parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
root=bpy.data.objects.new('PoliceLightbar',None);bpy.context.collection.objects.link(root);root['fictional']='Generic game lightbar; not an official Kerala Police equipment model.'
def mat(name,color,metal=.0,rough=.25,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission;return m
black=mat('PoliceLightbar_Base',(.012,.015,.022),.5,.4);red=mat('PoliceLightbar_Red',(.8,.008,.018),.1,.2,2.5);blue=mat('PoliceLightbar_Blue',(.008,.08,.9),.1,.2,2.5)
def box(name,loc,size,m,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.parent=root;mod=o.modifiers.new('Manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
    for p in o.data.polygons:p.use_smooth=True
box('Lightbar_Base',(0,0,.022),(.29,1.02,.044),black,.018)
box('Lightbar_Lens_Red',(0,-.255,.075),(.25,.47,.08),red,.025)
box('Lightbar_Lens_Blue',(0,.255,.075),(.25,.47,.08),blue,.025)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'police_lightbar.blend'));bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(OUT/'police_lightbar.glb'),export_format='GLB',use_selection=True,export_animations=False,export_apply=True)
public=ROOT/'web/public/assets';public.mkdir(exist_ok=True,parents=True);shutil.copyfile(OUT/'police_lightbar.glb',public/'police_lightbar.glb')
(OUT/'police_lightbar.json').write_text(json.dumps({'root':'PoliceLightbar','dimensions_three_m':[.29,.115,1.02],'origin':'bottom center','runtime_roof_position_three':[0,1.232,0],'animated_emissive_materials':['PoliceLightbar_Red','PoliceLightbar_Blue'],'fictional':True},indent=2));print('LIGHTBAR_READY')
