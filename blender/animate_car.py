import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]/'assets/car';FR=OUT/'articulation_frames';FR.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_studio.blend'))
s=bpy.context.scene;s.cycles.use_denoising=False;s.cycles.samples=16;s.render.resolution_x=800;s.render.resolution_y=500
s.camera.location=(5.1,-6.0,2.8);s.camera.rotation_euler=(Vector((0,0,.55))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=52
for n,frame in enumerate(range(1,122,3)):
    s.frame_set(frame);s.render.filepath=str(FR/f'{n:03d}.png');bpy.ops.render.render(write_still=True)
print('ARTICULATION_RENDER_DONE',n+1)
