import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'assets/car'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_studio.blend'))
s=bpy.context.scene;s.cycles.use_denoising=False;s.cycles.samples=32;s.render.resolution_x=1000;s.render.resolution_y=625
s.render.filepath=str(OUT/'preview_refined.png');bpy.ops.render.render(write_still=True)
