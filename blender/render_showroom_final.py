"""Higher-sample honest CPU preview. This Blender build lacks OpenImageDenoise."""
import bpy
from pathlib import Path
R=Path(__file__).resolve().parents[1];OUT=R/'assets/showroom';bpy.ops.wm.open_mainfile(filepath=str(OUT/'ServiceShowroomBay_Preview.blend'));s=bpy.context.scene;s.cycles.samples=192;s.cycles.use_denoising=False;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.025;s.cycles.adaptive_min_samples=32;s.render.filepath=str(OUT/'ServiceShowroomBay_preview_final.png');bpy.ops.render.render(write_still=True);print('FINAL_SHOWROOM_CPU_RENDER_READY',flush=True)
