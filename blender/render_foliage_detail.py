"""Integrated before/after CPU evidence using exact JS-selected positions on the frozen course."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/foliage_detail';OUT.mkdir(parents=True,exist_ok=True);cases=json.loads((ROOT/'assets/foliage_detail/integrated_preview_cases.json').read_text())
def native(p):return(p[0],-p[2],p[1])
def setup():
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/highlands/Highland_Run.blend'));s=bpy.context.scene
 for o in list(s.objects):
  if o.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=48;s.cycles.use_denoising=False;s.cycles.max_bounces=4;s.cycles.transparent_max_bounces=12;s.render.resolution_x=1100;s.render.resolution_y=680;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.15
 w=bpy.data.worlds.new('DetailDaylight');w.use_nodes=True;bg=w.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.48,.64,.86,1);bg.inputs['Strength'].default_value=.65;s.world=w
 ld=bpy.data.lights.new('DetailSun','SUN');lo=bpy.data.objects.new('DetailSun',ld);s.collection.objects.link(lo);ld.energy=2.5;ld.angle=math.radians(4);lo.rotation_euler=(math.radians(27),math.radians(-32),math.radians(-20));ca=bpy.data.cameras.new('EvidenceCamera');co=bpy.data.objects.new('EvidenceCamera',ca);s.collection.objects.link(co);s.camera=co;ca.clip_end=14000;return s,co

def detail(s,case):
 with bpy.data.libraries.load(str(ROOT/'assets/foliage_detail/Highland_Foliage_Detail.blend'),link=False) as(src,dst):dst.collections=['HighlandShadeTreeNear','TeaLeafCluster']
 tree,tea=dst.collections;eye=native(case['eye']);near=0
 for o in s.objects:
  if o.instance_collection and o.instance_collection.name.startswith('HighlandShadeTree') and math.hypot(o.location.x-eye[0],o.location.y-eye[1])<75:o.instance_collection=tree;near+=1
 for p in case['placements']:
  o=bpy.data.objects.new('TeaDetail_'+p['id'],None);s.collection.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=tea;o.location=native(p['position']);o.rotation_euler[2]=-p['yaw_rad'];o.scale=(p['scale'],)*3
 # Preview-only analogue of runtime's safe coarse-core fade. Existing source/GLBs remain untouched.
 for m in bpy.data.materials:
  if not m.name.startswith('Highlands_TeaCanopy'):continue
  nt=m.node_tree;n=nt.nodes;l=nt.links;geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');combine=n.new('ShaderNodeCombineXYZ');distance=n.new('ShaderNodeVectorMath');distance.operation='DISTANCE';distance.inputs[1].default_value=(eye[0],eye[1],0);ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=max(0,case['coverage_radius_m']-7);ramp.inputs['From Max'].default_value=case['coverage_radius_m'];ramp.inputs['To Min'].default_value=0;ramp.inputs['To Max'].default_value=1;ramp.clamp=True;trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');out=n.get('Material Output');shader=n.get('Principled BSDF');l.new(geo.outputs['Position'],sep.inputs[0]);l.new(sep.outputs['X'],combine.inputs['X']);l.new(sep.outputs['Y'],combine.inputs['Y']);l.new(combine.outputs[0],distance.inputs[0]);l.new(distance.outputs['Value'],ramp.inputs['Value']);l.new(ramp.outputs['Result'],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(shader.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
 return near
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Driver_After','Shoulder_Before','Shoulder_After']
for name in requested:
 s,co=setup();case=cases[name.split('_')[0].lower()];near=detail(s,case) if name.endswith('After') else 0;co.location=native(case['eye']);co.rotation_euler=(Vector(native(case['target']))-co.location).to_track_quat('-Z','Y').to_euler();co.data.lens=case['lens'];s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('DETAIL_PREVIEW_READY',name,'near_trees',near,'tea',len(case['placements']) if name.endswith('After') else 0,flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
