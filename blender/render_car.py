import bpy
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'assets/car'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_studio.blend'))
s=bpy.context.scene;s.cycles.use_denoising=False;s.cycles.samples=96
s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
cam=s.camera
s.render.filepath=str(OUT/'hero_front.png');bpy.ops.render.render(write_still=True)
cam.location=(-5.4,5.9,2.6);cam.rotation_euler=(Vector((-.1,0,.6))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/'hero_rear.png');bpy.ops.render.render(write_still=True)
cam.location=(5.7,-6.6,3.2);cam.rotation_euler=(Vector((0,0,.62))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'roadster_studio.blend'))
