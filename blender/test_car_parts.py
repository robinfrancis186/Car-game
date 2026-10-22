"""Geometry evidence for refined original cockpit and brake parts, not engineering validation."""
import bpy,bmesh,json,math
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'assets/car';bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_concept.blend'));s=bpy.context.scene;s.frame_set(1)
def audit(name):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);v=len(bm.verts);e=len(bm.edges);f=len(bm.faces);boundary=sum(edge.is_boundary for edge in bm.edges);nonmanifold=sum(not edge.is_manifold for edge in bm.edges);volume=bm.calc_volume(signed=True);result={'vertices':v,'edges':e,'faces':f,'euler_characteristic':v-e+f,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'signed_volume_m3':volume};bm.free();return result
r={'rotors':{},'seat_harness_panels':{},'dashboard_graphics':'Original modeled vector labels/map, static parked-state design props; game HUD is separate.'};errors=[]
for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
 a=audit('Brake_Rotor_'+key);r['rotors'][key]=a
 if a['euler_characteristic']!=-94 or a['nonmanifold_edges']!=0:errors.append('48 actual through-holes '+key)
for side in [-1,1]:
 for part in ['Seat_BackShell_','Seat_BackPad_']:
  name=part+str(side);a=audit(name);r['seat_harness_panels'][name]=a
  if a['euler_characteristic']!=-2 or a['nonmanifold_edges']!=0:errors.append('two harness through-slots '+name)
s.frame_set(31);r['handwheel_frame31_rotation_x']=bpy.data.objects['Interior_Steering_Pivot'].rotation_euler.x
if abs(r['handwheel_frame31_rotation_x']-1.28)>1e-5:errors.append('handwheel animation follows steering')
r['rhd_handwheel_y_m']=bpy.data.objects['Interior_Steering_Pivot'].location.y
r['source_only_note']='Detailed editable source has the animated handwheel and perforations. Browser LOD omits subpixel cabin graphics and uses simplified rotor discs.'
r['result']='PASS' if not errors else 'FAIL';r['failures']=errors;(OUT/'parts_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));assert not errors,errors
