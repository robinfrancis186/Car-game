"""Native editable source/analytic-vertex/UV validation, not gameplay."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/surface_test';f=O/'Surface_Test_Route.blend';cfg=json.loads((R/'docs/v16/surface_profile.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(f))
def angle(s):
 for a,b in zip(cfg['bankKnots'],cfg['bankKnots'][1:]):
  if a['s']-1e-4<=s<=b['s']+1e-4:
   t=max(0,min(1,(s-a['s'])/(b['s']-a['s'])));return math.radians(a['degrees']+(b['degrees']-a['degrees'])*t*t*t*(10-15*t+6*t*t))
 return 0
road=bpy.data.objects['SurfaceTest_Driveable_Asphalt'];maximum=0
for vv in road.data.vertices:
 q=road.matrix_world@vv.co;s=q.x;y=q.z;z=-q.y;a=angle(s);l=(y-cfg['baseY'])*math.sin(a)+z*math.cos(a);expected=Vector((s,cfg['baseY']+l*math.sin(a),l*math.cos(a)));maximum=max(maximum,(Vector((s,y,z))-expected).length)
images=[i.name for i in bpy.data.images if i.source in('FILE','GENERATED')];roots=[n for n in('SurfaceTest_Road','SurfaceTest_Furniture','SurfaceTest_Terrain')if bpy.data.objects.get(n)];report={'result':'PASS' if maximum<.0001 and len(roots)==3 and len(road.data.uv_layers)==1 and not images else'FAIL','native_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'editable_mesh_parts':sum(o.type=='MESH' for o in bpy.context.scene.objects),'editable_text_parts':sum(o.type=='FONT' for o in bpy.context.scene.objects),'named_roots':roots,'native_axes':'+X forward/+Z up/-Y right','surface_vertex_count':len(road.data.vertices),'max_analytic_surface_vertex_error_m':maximum,'native_metric_uv_layer_count':len(road.data.uv_layers),'external_or_packed_images':images,'scope':'Editable native source and analytic vertex equality within stored-float tolerance. No gameplay/continuous-mesh equality claim.'};(O/'native_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
