"""Actual exported test-course GLBs, CPU Blender preview; not gameplay."""
import bpy,json,math,hashlib,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/surface_test'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sources={}
for name in('Road','Furniture','Terrain'):
 p=R/'assets/web'/f'SurfaceTest_{name}.glb';sources[p.name]=hashlib.sha256(p.read_bytes()).hexdigest();bpy.ops.import_scene.gltf(filepath=str(p))
for m in bpy.data.materials:
 if 'asphalt' in m.name:
  n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
world=bpy.data.worlds.new('Original test-course daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.34,.44,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;bpy.context.scene.world=world
bpy.ops.object.light_add(type='SUN');bpy.context.object.data.energy=2.3;bpy.context.object.data.angle=.08;bpy.context.object.rotation_euler=(.45,-.35,-.8)
bpy.ops.object.light_add(type='AREA',location=(370,70,95));bpy.context.object.data.energy=90000;bpy.context.object.data.size=130
bpy.ops.object.camera_add();cam=bpy.context.object;bpy.context.scene.camera=cam;cam.data.clip_end=3000
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=1400;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
cameras={'overview':((390,700,460),(450,0,6),28),'bank_entry':((190,38,22),(265,0,8),42),'wall_hold':((375,57,21),(450,0,8),42),'runout':((670,38,20),(757,0,8),42)}
for name,(pos,target,lens)in cameras.items():
 if os.environ.get('SURFACE_RENDER_MODES') and name not in os.environ['SURFACE_RENDER_MODES'].split(','):continue
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;sc.render.filepath=str(O/f'preview_{name}.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/f'preview_{name}.blend'));bpy.ops.render.render(write_still=True)
 proof={'scope':'Actual exported GLBs imported into CPU Blender; original studio/environment preview, not gameplay. No reference pixels.','source_glb_sha256':sources,'image':f'assets/surface_test/preview_{name}.png','sha256':hashlib.sha256((O/f'preview_{name}.png').read_bytes()).hexdigest(),'samples':48,'denoising':False,'camera_blender':pos,'target_blender':target,'lens_mm':lens}
 (O/f'preview_{name}_provenance.json').write_text(json.dumps(proof,indent=2)+'\n');print('SURFACE_PREVIEW_READY',name,flush=True)
