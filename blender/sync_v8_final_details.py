"""Apply final reviewed non-route detail corrections to the already built native course.
Full regeneration with build_course.py applies the same updated layout automatically.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'assets/course/Kappil_Coast.blend';bpy.ops.wm.open_mainfile(filepath=str(p));manifest=json.loads((ROOT/'assets/course/manifest.json').read_text());r=next(p for p in manifest['prop_instances'] if p['asset']=='ChineseFishingNet')
for o in bpy.context.scene.objects:
 if o.instance_type=='COLLECTION' and o.instance_collection and o.instance_collection.name=='ChineseFishingNet':o.location=r['location_m'];o.rotation_euler.z=math.radians(r['yaw_deg'])
# Collinear font cap triangles have no visible area; cleaned source and runtime models agree.
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith(('CoastMetroSign','WaterTransitSign')):
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-7]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(o.data);bm.free();o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p));print('FINAL_NATIVE_DETAILS_SYNCED')
