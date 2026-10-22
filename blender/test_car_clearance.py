"""Geometric tire-to-body visual clearance check, not collision/dynamics validation."""
import bpy,json
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/car'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_concept.blend'));bpy.context.scene.frame_set(1)
def tree(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    b=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return b
body=tree(bpy.data.objects['Body_SculptedShell']);tray=tree(bpy.data.objects['Undertray']);r={}
for angle in [0,.4,-.4]:
    r[str(angle)]={}
    for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
        bpy.data.objects['Steer_'+key].rotation_euler.z=angle if key.startswith('Front') else 0;bpy.context.view_layer.update()
        tire=tree(bpy.data.objects['Tire_'+key]);r[str(angle)][key]={'shell_triangle_overlaps':len(tire.overlap(body)),'undertray_triangle_overlaps':len(tire.overlap(tray))}
(OUT/'clearance_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
