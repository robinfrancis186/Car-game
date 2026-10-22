"""CPU evidence renders of the actual authored Highland course, not image synthesis."""
import bpy,math,json,bisect,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders/highlands';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/highlands/Highland_Run.blend'));scene=bpy.context.scene
for o in list(scene.objects):
 if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2;scene.render.resolution_x=1100;scene.render.resolution_y=680;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.35
world=bpy.data.worlds.new('Highlands_Daylight');world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.48,.64,.86,1);bg.inputs['Strength'].default_value=.65;scene.world=world
ld=bpy.data.lights.new('HighlandSun','SUN');lo=bpy.data.objects.new('HighlandSun',ld);scene.collection.objects.link(lo);ld.energy=2.3;ld.angle=math.radians(4);lo.rotation_euler=(math.radians(27),math.radians(-32),math.radians(-20))
cam=bpy.data.cameras.new('EvidenceCamera');co=bpy.data.objects.new('EvidenceCamera',cam);scene.collection.objects.link(co);scene.camera=co;cam.clip_end=14000
views={
 'Highland_Overview':((1350,-260,710),(540,490,65),34),
 'Tea_Hairpins':((1120,790,360),(630,325,50),42),
 'NH66_Driver':((145,0,1.85),(260,-.2,2.5),29),
 'Tea_RoadDriver':((340,330,42),(440,330,46),29),
 'BirdRock_Approach':((420,780,120),(490,850,111),36),
}
# Driver eye uses actual road elevation, not guessed height.
plan=json.loads((ROOT/'assets/highlands/highlands_plan.json').read_text());rr=plan['route_points_blender_m'];ds=plan['horizontal_route_distances_m']
def at(s):
 i=max(0,min(len(ds)-2,bisect.bisect_right(ds,s)-1));f=(s-ds[i])/(ds[i+1]-ds[i]);return Vector([rr[i][k]*(1-f)+rr[i+1][k]*f for k in range(3)])
p,q=at(1880),at(1990);p.z+=1.65;q.z+=1.7;views['Tea_RoadDriver']=(tuple(p),tuple(q),30)
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(views)
for name in requested:
 eye,target,lens=views[name];co.location=eye;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();cam.lens=lens;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('RENDER_READY',scene.render.filepath,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Highland_Preview.blend'))
