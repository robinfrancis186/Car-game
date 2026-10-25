"""New preview only. Does not edit any frozen source/export/QA artifact."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];O=R/'assets/surface_test/proof';proof=json.loads((O/'wall_car_staged_frame.json').read_text());freeze=json.loads((R/'assets/surface_test/freeze.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={k:sha(R/k)for k in freeze['hashes']};assert all(before[k]==v['sha256']for k,v in freeze['hashes'].items())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);sources={}
for name in('SurfaceTest_Road.glb','SurfaceTest_Furniture.glb','SurfaceTest_Terrain.glb'):
 p=R/'web/public/assets'/name;sources[name]=sha(p);bpy.ops.import_scene.gltf(filepath=str(p))
old=set(bpy.context.scene.objects);car=R/'web/public/assets/car.glb';sources['car.glb']=sha(car);bpy.ops.import_scene.gltf(filepath=str(car));new=set(bpy.context.scene.objects)-old
frame=proof['frame'];B=Matrix((frame['forward'],frame['up'],frame['right'])).transposed();C=Matrix(((1,0,0),(0,0,1),(0,-1,0)));M=(C.inverted()@B@C).to_4x4();s=proof['sample']['position'];M.translation=Vector((s[0],-s[2],s[1]))
for o in new:
 if o.parent not in new:o.matrix_world=M@o.matrix_world
world=bpy.data.worlds.new('Staged surface proof daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.30,.40,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;bpy.context.scene.world=world
bpy.ops.object.light_add(type='SUN');bpy.context.object.data.energy=2.4;bpy.context.object.data.angle=.08;bpy.context.object.rotation_euler=(.35,-.4,-.65)
bpy.ops.object.light_add(type='AREA',location=(425,12,20));bpy.context.object.data.energy=2600;bpy.context.object.data.size=11
bpy.ops.object.camera_add(location=(431,24,12.5));cam=bpy.context.object;target=Vector((424,0,6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=32;cam.data.clip_end=1600;bpy.context.scene.camera=cam
mat=bpy.data.materials.new('Preview-only label white');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Emission Color'].default_value=(1,1,1,1);bs.inputs['Emission Strength'].default_value=1
cu=bpy.data.curves.new('Preview scope label','FONT');cu.body='BLENDER STAGED PROOF  /  NOT GAMEPLAY';cu.size=.026;cu.align_y='CENTER';ob=bpy.data.objects.new('Preview-only scope label',cu);bpy.context.scene.collection.objects.link(ob);cu.materials.append(mat);ob.parent=cam;ob.location=(-.54,-.32,-1);ob.rotation_euler=(0,0,0)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=1400;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX';sc.render.filepath=str(O/'Blender_Staged_Wall_Car_Not_Gameplay.png');bpy.context.view_layer.update()
from bpy_extras.object_utils import world_to_camera_view
points=[world_to_camera_view(sc,cam,o.matrix_world@v.co)for o in new if o.type=='MESH'for v in o.data.vertices]
frame_bounds={'min':[min(q[i]for q in points)for i in(0,1)],'max':[max(q[i]for q in points)for i in(0,1)]};print('PROOF_CAR_FRAME_BOUNDS',frame_bounds,flush=True);assert min(frame_bounds['min'])>.03 and max(frame_bounds['max'])<.97
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Blender_Staged_Wall_Car_Not_Gameplay.blend'));bpy.ops.render.render(write_still=True)
assert all(sha(R/k)==v for k,v in before.items())
result={'scope':'Preview-only existing Crimson GLB staged at actual sampleRibbon/vehicleFrame s420,l0,90-degree bank. Not gameplay; no new exported geometry.','source_hashes':sources,'canonical_sample':proof,'camera_native':[431,24,12.5],'target_native':list(target),'samples':48,'denoising':False,'image':'assets/surface_test/proof/Blender_Staged_Wall_Car_Not_Gameplay.png','image_sha256':sha(O/'Blender_Staged_Wall_Car_Not_Gameplay.png'),'frozen_43_file_hashes_unchanged':True,'projected_car_bounds':frame_bounds};(O/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print('WALL_CAR_PROOF_READY',flush=True)
