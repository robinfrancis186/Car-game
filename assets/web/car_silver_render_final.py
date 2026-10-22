"""Higher-sample asset QA renders from the immutable final GLB, no mesh rebuild."""
import bpy, json, sys, hashlib, time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/web'
source=(ROOT/'blender/build_silver_car.py').read_text()
start=time.monotonic();asset=OUT/'car_silver.glb';sha=hashlib.sha256(asset.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(asset));bpy.context.view_layer.update()
# Reuse the exact studio materials and placement, not a generated/retouched picture.
helper='def mat('+source.split('def mat(',1)[1].split("paint=mat(",1)[0]
exec(helper)
code=source.split('# Neutral studio test renders, geometry is actual GLB round trip.',1)[1].split("print('SILVER_CAR_READY'",1)[0]
code=code.replace('scene.cycles.samples=72','scene.cycles.samples=384')
code=code.replace("scene.cycles.use_denoising=False", "scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.015;scene.cycles.adaptive_min_samples=64;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2;scene.cycles.transmission_bounces=0;scene.cycles.sample_clamp_indirect=1.5")
exec(code)
record={'source':'car_silver.glb','source_sha256':sha,'source_unchanged':sha==hashlib.sha256(asset.read_bytes()).hexdigest(),'engine':'Cycles CPU','maximum_samples':384,'adaptive_threshold':.015,'minimum_samples':64,'denoiser':False,'denoiser_reason':'This installed Blender build has no OpenImageDenoise support, confirmed in assets/car/build.log.','resolution':[1280,800],'max_bounces':4,'elapsed_seconds':time.monotonic()-start,'images':['car_silver_preview_front.png','car_silver_preview_rear.png'],'image_editing':'None; direct renderer output.'}
(OUT/'car_silver_render_validation.json').write_text(json.dumps(record,indent=2))
p=OUT/'car_silver_README.md';s=p.read_text().replace('72 samples, no denoiser','up to 384 adaptive samples (minimum 64, threshold 0.015), no denoiser');p.write_text(s)
print('FINAL_SILVER_PREVIEWS',json.dumps(record))
