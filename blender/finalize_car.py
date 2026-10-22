"""Fix directional normals on left glazing / thin pillar strips; re-export contract."""
import bpy, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/car'
# Existing high-sample rendering process uses a loaded snapshot. This corrects export-side facing.
for fname in ['roadster_concept.blend','roadster_studio.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(OUT/fname))
    scene=bpy.context.scene;scene.frame_set(1)
    for name in ['Glass_Side_1','A_Pillar_1','Rear_Buttress_-1']:
        o=bpy.data.objects[name]
        if not o.get('outward_normal_fix'):
            for p in o.data.polygons:p.flip()
            o.data.update();o['outward_normal_fix']=True
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/fname))
# Re-export the clean original, not the studio.
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_concept.blend'))
scene=bpy.context.scene;scene.frame_set(1);bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT/'roadster_concept.glb'),export_format='GLB',use_selection=True,export_animations=True,export_apply=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/'roadster_concept.fbx'),use_selection=True,axis_forward='X',axis_up='Z',apply_unit_scale=True,bake_anim=False,object_types={'MESH','EMPTY'},use_mesh_modifiers=True)
export_col=bpy.data.collections.new('ENGINE_EXPORT_TEMP');scene.collection.children.link(export_col)
source=(ROOT/'blender/build_car.py').read_text();exec(source[source.index('def joined_export'):source.index('# Calipers fixed')])
def is_spinning(o):
    p=o.parent
    while p:
        if p.name.startswith('Spin_'):return True
        p=p.parent
    return False
joined_export('SM_CarBody',[o for o in bpy.data.objects if o.type=='MESH' and not is_spinning(o)],(0,0,0))
shutil.copyfile(OUT/'SM_CarBody.fbx',OUT/'car_body.fbx')
shutil.copyfile(OUT/'SM_CarBody.glb',OUT/'car_body.glb')
# Metadata: track coordinates and explicit PBR constants, including thin glass.
d=json.loads((OUT/'manifest.json').read_text());d['normal_facing']='Windshield/roof/rear face up; side glass and thin pillars face outward.'
d['materials']=[{'name':m.name,'base_color':list(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'transmission':m.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value,'emission_strength':m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value} for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')]
(OUT/'manifest.json').write_text(json.dumps(d,indent=2));(OUT/'materials.json').write_text(json.dumps({m['name']:{k:m[k] for k in ['base_color','roughness','metallic','transmission','emission_strength']} for m in d['materials']},indent=2))
print('NORMALS_AND_EXPORTS_FINALIZED')
