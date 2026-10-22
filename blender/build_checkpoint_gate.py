"""Original low-poly checkpoint flags, built in Blender; no third-party assets.
Exported GLB: Three.js +X forward, +Y up; road spans Z. No collision.
"""
import bpy, math, json, shutil, struct, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
root=bpy.data.objects.new('CheckpointGate',None);scene.collection.objects.link(root)
root['collision']=False;root['road_clear_width_m']=7.2;root['origin']='Road center at road surface; no overhead or cross-road barrier';root['provenance']='Original Blender-generated geometry, no external assets'
def material(name,base,emission):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*base,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*base,1);p.inputs['Roughness'].default_value=.35;p.inputs['Metallic'].default_value=.15;p.inputs['Emission Color'].default_value=(*emission,1);p.inputs['Emission Strength'].default_value=1;m.use_backface_culling=False;return m
cyan=material('Checkpoint_Cyan',(.025,.38,.47),(.015,.74,.90));orange=material('Checkpoint_Orange',(.95,.23,.025),(.9,.16,.008))
parts=[]
def reg(o,name,m):o.name=name;o.parent=root;o.data.materials.append(m);parts.append(o);return o
def mesh(name,verts,faces,m):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);return reg(o,name,m)
def cylinder(name,loc,radius,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=radius,depth=depth,location=loc);return reg(bpy.context.object,name,m)
for side in (-1,1):
 y=side*4.16
 cylinder('FlagPole_'+str(side),(0,y,1.88),.036,3.76,cyan)
 cylinder('FlagFoot_'+str(side),(0,y,.045),.17,.09,orange)
 cylinder('FlagCollar_'+str(side),(0,y,.18),.063,.20,orange)
 # Cyan outer pennant extends away from traffic, keeping the full road clear.
 poly=[(0,y,1.05),(0,y,3.77),(0,side*4.83,3.40),(0,side*4.68,1.52)]
 mesh('Flag_CyanBorder_'+str(side),poly,[(0,1,2,3)],cyan)
 inner=[(-.008,side*4.23,1.34),(-.008,side*4.23,3.58),(-.008,side*4.72,3.32),(-.008,side*4.59,1.64)]
 mesh('Flag_OrangePanel_'+str(side),inner,[(0,1,2,3)],orange)
 # Two clear inward chevrons, fully outside the paved road corridor.
 for j,z in enumerate((1.91,2.54)):
  verts=[(-.02,side*4.54,z-.22),(-.02,side*4.35,z),(-.02,side*4.54,z+.22),(-.02,side*4.63,z+.14),(-.02,side*4.51,z),(-.02,side*4.63,z-.14)]
  mesh('Flag_DirectionChevron_'+str(side)+'_'+str(j),verts,[(0,1,4,5),(1,2,3,4)],cyan)
 # Small top locator glint, octahedron for a clean distant silhouette.
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.085,location=(0,y,3.83));reg(bpy.context.object,'Flag_TopMarker_'+str(side),cyan)
# Merge by material; two draw primitives total.
merged=[]
for m in (cyan,orange):
 bpy.ops.object.select_all(action='DESELECT')
 selected=[o for o in scene.objects if o.type=='MESH' and o.data.materials[0]==m]
 for o in selected:o.select_set(True)
 bpy.context.view_layer.objects.active=selected[0];bpy.ops.object.join();o=bpy.context.object;o.name=m.name+'_Mesh'
 # Bake transform to origin so exported POSITION axes are already Y-up after glTF conversion.
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);merged.append(o)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in merged:o.select_set(True)
bpy.context.view_layer.objects.active=root
path=OUT/'CheckpointGate.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_extras=True)
shutil.copy2(path,PUBLIC/path.name)
# Native checkpoint asset only, before adding presentation geometry.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'CheckpointGate.blend'))
data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);tris=sum(doc['accessors'][p['indices']]['count']//3 for me in doc['meshes'] for p in me['primitives'])
all_positions=[o.matrix_world@v.co for o in merged for v in o.data.vertices]
measured_height=max(v.z for v in all_positions)-min(v.z for v in all_positions)
measured_clear=2*min(abs(v.y) for v in all_positions)
report={'name':'CheckpointGate','source':'blender/build_checkpoint_gate.py','triangles':tris,'materials':len(doc['materials']),'draw_primitives':sum(len(m['primitives']) for m in doc['meshes']),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'axes':'Three/glTF +X forward,+Y up; road spans Z; already converted','pivot':'Road center at road surface','collision':False,'road_clear_width_m':7.2,'flag_poles_lateral_m':4.16,'height_m':measured_height,'actual_unobstructed_width_m':measured_clear,'license':'Original generated asset; same original-asset provenance as environment library','validation':{'under_500_triangles':tris<=500,'two_materials':len(doc['materials'])==2}}
(OUT/'CheckpointGate_manifest.json').write_text(json.dumps(report,indent=2));shutil.copy2(OUT/'CheckpointGate_manifest.json',PUBLIC/'CheckpointGate_manifest.json')
# Preview context is not exported.
road=bpy.data.materials.new('Preview_Road');road.use_nodes=True;road.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.035,.046,.05,1);road.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
bpy.ops.mesh.primitive_plane_add(size=1,location=(0,0,-.005));o=bpy.context.object;o.scale=(16,7.2,1);o.data.materials.append(road)
ground=bpy.data.materials.new('Preview_Ground');ground.use_nodes=True;ground.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.09,.11,.10,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.03));bpy.context.object.data.materials.append(ground)
world=bpy.data.worlds.new('Checkpoint_Preview_World');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.22,.3,.36,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.5;scene.world=world
bpy.ops.object.light_add(type='AREA',location=(-3,-2,9));bpy.context.object.data.energy=1500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=10
bpy.ops.object.camera_add(location=(-9,-10,5.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=42;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=1000;scene.render.resolution_y=650;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.filepath=str(OUT/'CheckpointGate_preview.png');bpy.ops.render.render(write_still=True)
print('CHECKPOINT_READY',json.dumps(report))
