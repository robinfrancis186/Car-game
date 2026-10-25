import sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[3];sys.path.insert(0,str(p/'blender'));import rebuild_car_helpers as h
h.reset();root=h.empty('CAR_ROOT');groups=[root];paint=h.material('paint',(.4,.01,.01));alloy=h.material('alloy',(.2,.2,.2));rubber=h.material('rubber',(.01,.01,.01));w=h.build_wheels(root,groups,paint,alloy,rubber,prefix='Helper smoke',spokes=5);m=h.export_glb(groups,Path(__file__).parent/'helper_smoke.glb',{});print('HELPER_SMOKE',json.dumps(m))
import bpy;bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(__file__).parent/'helper_smoke.glb'));assert len([o for o in bpy.data.objects if o.name.startswith('Steer_')])==4;print('IMPORT_PASS')
