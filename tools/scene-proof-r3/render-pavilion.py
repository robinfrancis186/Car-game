"""Original R3 pavilion lighting proof from the exact runtime mesh export.
Offline Blender/Cycles proof, NOT a browser screenshot or runtime-fidelity acceptance.
No reference images are loaded. Actual original car GLB materials remain unchanged.
"""
import bpy,json,math,sys,argparse,hashlib
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,default=H.parent.parent/'web/public/assets');p.add_argument('--geometry',type=Path,default=H/'pavilion-geometry.json');p.add_argument('--output',type=Path,default=H/'proof');p.add_argument('--width',type=int,default=960);p.add_argument('--samples',type=int,default=256);p.add_argument('--car',default='car.glb');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.output.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=a.samples;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=False;s.cycles.max_bounces=7;s.cycles.transparent_max_bounces=6;s.cycles.sample_clamp_indirect=4
s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*692/1280);s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.compression=50;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.15
source=a.source_root/a.car;bpy.ops.import_scene.gltf(filepath=str(source));car=list(s.objects)
# GLTF import is y-up -> Blender z-up; its original geometry and materials are untouched.
def material(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color[:3],1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;return m
materials={}
def to_blender(v):return (v[0],-v[2],v[1])
def mesh(name,verts,faces,mats):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
 for m in mats:d.materials.append(m)
 return o
floor=material('Original R3 honed slate proof',(.035,.046,.057),.21,.22)
n=floor.node_tree.nodes;l=floor.node_tree.links;b=n.get('Principled BSDF');coord=n.new('ShaderNodeTexCoord');brick=n.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=1.65;brick.inputs['Row Height'].default_value=1.65;brick.offset=0;brick.inputs['Mortar Size'].default_value=.006;brick.inputs['Mortar Smooth'].default_value=.006;brick.inputs['Color1'].default_value=(.025,.036,.046,1);brick.inputs['Color2'].default_value=(.07,.079,.082,1);brick.inputs['Mortar'].default_value=(.011,.018,.023,1);l.new(coord.outputs['Object'],brick.inputs['Vector']);l.new(brick.outputs['Color'],b.inputs['Base Color']);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=22;noise.inputs['Detail'].default_value=2;l.new(coord.outputs['Object'],noise.inputs[0]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.012;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],b.inputs['Normal'])
water=material('Original R3 sea proof',(.012,.10,.14),.19,.35);n=water.node_tree.nodes;l=water.node_tree.links;tc=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(.5,4,1);l.new(tc.outputs['Object'],v.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.85;noise.inputs['Detail'].default_value=3;l.new(v.outputs[0],noise.inputs[0]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.38;bump.inputs['Distance'].default_value=.085;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],n.get('Principled BSDF').inputs['Normal']);n.get('Principled BSDF').inputs['IOR'].default_value=1.333;n.get('Principled BSDF').inputs['Emission Color'].default_value=(.012,.08,.11,1);n.get('Principled BSDF').inputs['Emission Strength'].default_value=.10
# Real original procedural cloud sky, emitted from the same runtime dome mesh.
sky=bpy.data.materials.new('Original R3 warm cloud sky proof');sky.use_nodes=True;n=sky.node_tree.nodes;l=sky.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');em.inputs['Strength'].default_value=.8;l.new(em.outputs[0],out.inputs[0]);tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Generated'],sep.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.49;r.color_ramp.elements[0].color=(.8,.28,.075,1);r.color_ramp.elements[1].position=.68;r.color_ramp.elements[1].color=(.065,.13,.24,1)
for pos,col in [(.52,(.9,.52,.25,1)),(.565,(.25,.32,.40,1))]:e=r.color_ramp.elements.new(pos);e.color=col
l.new(sep.outputs['Z'],r.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=26;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.7;l.new(tc.outputs['Generated'],noise.inputs[0]);mask=n.new('ShaderNodeValToRGB');mask.color_ramp.elements[0].position=.49;mask.color_ramp.elements[1].position=.66;mask.color_ramp.elements[1].color=(.58,.58,.58,1);l.new(noise.outputs['Fac'],mask.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(.68,.47,.29,1);l.new(mask.outputs['Color'],mix.inputs[0]);l.new(r.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],em.inputs[0])
geo=json.loads(a.geometry.read_text())
for item in geo['meshes']:
 name=item['name'];mats=[];special=None
 for mt in item['materials']:
  mn=mt['name']
  if 'slate' in mn.lower():m=floor;special='floor'
  elif 'sunset ocean' in mn.lower():m=water;special='water'
  elif 'sunset sky' in mn.lower():m=sky;special='sky'
  elif mn in materials:m=materials[mn]
  else:
   m=material(mn,mt['color'],mt['roughness'],mt['metalness']);pb=m.node_tree.nodes.get('Principled BSDF')
   if mt['basic']:
    pb.inputs['Emission Color'].default_value=(*mt['color'],1);pb.inputs['Emission Strength'].default_value=1
   elif max(mt['emission'])>0:
    pb.inputs['Emission Color'].default_value=(*mt['emission'],1);pb.inputs['Emission Strength'].default_value=mt['emissionIntensity']
   if 'glazing' in mn.lower():pb.inputs['Transmission Weight'].default_value=1;pb.inputs['Roughness'].default_value=.02;pb.inputs['Alpha'].default_value=.04
   if 'cedar ceiling' in mn.lower():
    nd=m.node_tree.nodes;lk=m.node_tree.links;tc=nd.new('ShaderNodeTexCoord');scale=nd.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(.35,22,12);lk.new(tc.outputs['Object'],scale.inputs[0]);no=nd.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=2;no.inputs['Detail'].default_value=2;lk.new(scale.outputs[0],no.inputs[0]);ra=nd.new('ShaderNodeValToRGB');ra.color_ramp.elements[0].color=(.055,.021,.007,1);ra.color_ramp.elements[1].color=(.28,.11,.032,1);lk.new(no.outputs['Fac'],ra.inputs[0]);lk.new(ra.outputs[0],pb.inputs['Base Color'])
   materials[mn]=m
  mats.append(m)
 idx=item['index'];faces=[idx[i:i+3] for i in range(0,len(idx),3)];o=mesh(name,[to_blender(v) for v in item['vertices']],faces,mats)
 for group in item['groups']:
  for poly in o.data.polygons[group['start']//3:(group['start']+group['count'])//3]:poly.material_index=group['materialIndex']
 if special=='sky':o.visible_diffuse=False;o.visible_shadow=False
 elif not any('steel' in m.name.lower() or 'ceiling' in m.name.lower() for m in mats):
  for poly in o.data.polygons:poly.use_smooth=True
# Physical sky ambient + warm low-angle direct light, independent of gameplay world.
w=bpy.data.worlds.new('R3 cool restrained ambient');w.use_nodes=True;s.world=w;w.node_tree.nodes['Background'].inputs[0].default_value=(.10,.15,.23,1);w.node_tree.nodes['Background'].inputs[1].default_value=.20
sun=bpy.data.lights.new('R3 low sunset key','SUN');sun.energy=2.5;sun.color=(1,.56,.26);sun.angle=math.radians(1.8);o=bpy.data.objects.new('R3 low sunset key',sun);s.collection.objects.link(o);o.location=(-20,100,8.5);o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
# A visible sun mesh aligns with key; fully original, no photographic background.
m=bpy.data.materials.new('Original low sunset disc');m.use_nodes=True;nd=m.node_tree.nodes;nd.clear();em=nd.new('ShaderNodeEmission');em.inputs[0].default_value=(1,.56,.2,1);em.inputs[1].default_value=7;out=nd.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0]);bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=9,location=(-200,1000,85));o=bpy.context.object;o.name='Original setting sun';o.data.materials.append(m);o.visible_shadow=False;o.visible_diffuse=False
# Large physical photographic lights create long body highlights without editing car materials.
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,energy,size,size_y,color,target=(0,0,.6)):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='RECTANGLE';d.size=size;d.size_y=size_y;d.color=color;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;aim(o,target)
area('R3 long warm ceiling bounce',(-1,2,5.95),850,7,.65,(1,.72,.42))
area('R3 cool camera soft fill',(4,-4,4),280,6,3,(.64,.77,1))
area('R3 wide horizon window fill',(-1,7,3),450,12,3,(1,.66,.35))
d=bpy.data.cameras.new('R3 original pavilion composition');d.lens=40;d.sensor_fit='VERTICAL';d.sensor_height=24;d.clip_end=6500;d.shift_x=-.39;d.shift_y=.07;cam=bpy.data.objects.new('R3 original pavilion composition',d);s.collection.objects.link(cam);s.camera=cam;cam.location=(7.5,-8.2,2.40);aim(cam,(0,0,.65));d.dof.use_dof=False
out=a.output/'pavilion-crimson.png';s.render.filepath=str(out);bpy.ops.wm.save_as_mainfile(filepath=str(a.output/'pavilion-crimson.blend'),compress=True);print('PAVILION_RENDER_START',flush=True);bpy.ops.render.render(write_still=True)
receipt={'scope':'Original offline pavilion proof; runtime geometry exported exactly, Blender lighting/shader equivalents are not WebGL evidence. No UI overlay. No private reference pixels.','source_car':a.car,'source_car_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'car_geometry_materials_modified':False,'geometry_sha256':hashlib.sha256(a.geometry.read_bytes()).hexdigest(),'geometry_meshes':len(geo['meshes']),'geometry_triangles':geo['triangles'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'render_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'dimensions':[s.render.resolution_x,s.render.resolution_y],'engine':'Cycles CPU','samples':a.samples,'denoising':False,'runtime_integrated':False,'runtime_source_hashes':{n:hashlib.sha256((H.parent.parent/n).read_bytes()).hexdigest() for n in ['web/src/scene.js','web/src/showroom-scene.js','web/src/showroom-reflector.js']},'camera':{'position':list(cam.location),'rotation_euler':list(cam.rotation_euler),'lens_mm':d.lens,'sensor_fit':d.sensor_fit,'sensor_height':d.sensor_height,'shift_x':d.shift_x,'shift_y':d.shift_y,'clip_end':d.clip_end},'approximations':['Three.js procedural sky shader replaced by original Blender cloud emission nodes on the same dome mesh.','Three.js view-dependent ocean shader replaced by physical blue wave-normal water on the same mesh.','Three.js 512px planar reflected slate shader replaced by Cycles physical glossy tiled floor on the same mesh.','Blender soft area lights plus sunset sun replace runtime point lights and PMREM environment.','Offline camera is a reference-composition proof, not a captured runtime camera or UI.']};(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2));print('PAVILION_READY',json.dumps(receipt),flush=True)
