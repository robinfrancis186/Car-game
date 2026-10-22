import bpy,json,math,shutil,struct
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'CheckpointGate.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];vs=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
zero=sum(1 for o in meshes for p in o.data.polygons if p.area<1e-10);clear=2*min(abs(v.y) for v in vs);height=max(v.z for v in vs)-min(v.z for v in vs)
x={'reimport_meshes':len(meshes),'degenerate_polygons':zero,'finite_coordinates':all(math.isfinite(c) for v in vs for c in v),'clear_road_width_m':clear,'height_m':height,'pass':len(meshes)==2 and zero==0 and clear>=7.2}
(OUT/'checkpoint_validation.json').write_text(json.dumps(x,indent=2))
m=json.loads((OUT/'CheckpointGate_manifest.json').read_text());m['height_m']=height;m['actual_unobstructed_width_m']=clear;m['validation'].update(x);(OUT/'CheckpointGate_manifest.json').write_text(json.dumps(m,indent=2));shutil.copy2(OUT/'CheckpointGate_manifest.json',OUT.parents[1]/'web/public/assets/CheckpointGate_manifest.json')
print('CHECKPOINT_QA',json.dumps(x))
