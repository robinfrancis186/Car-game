import bpy,json,math,hashlib,sys,ast
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'assets/helicopter';sys.path.insert(0,str(R/'blender'));import rebuild_car_helpers as h
parsed=ast.parse((R/'blender/build_helicopter.py').read_text());rows=next(ast.literal_eval(n.value)for n in parsed.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='rows'for t in n.targets))
for key in ['civilian','police']:
 D=O/key;p=D/('Coastal_Twin_'+key.title()+'.blend');bpy.ops.wm.open_mainfile(filepath=str(p));root=bpy.data.objects['HELICOPTER_ROOT'];body=bpy.data.objects['Airframe'];main=bpy.data.objects['MainRotor'];tail=bpy.data.objects['TailRotor'];bpy.context.view_layer.update();before_body=body.matrix_world.copy();before_tail=tail.matrix_world.copy();moves=[]
 for node,axis in[(main,'Z'),(tail,'Y')]:
  best=None;radius=0
  for o in node.children:
   if o.type!='MESH':continue
   for i,v in enumerate(o.data.vertices):
    p0=o.matrix_world@v.co;r=(p0-node.matrix_world.translation).length
    if r>radius:radius=r;best=(o,i,p0.copy())
  node.rotation_euler['XYZ'.index(axis)]=.5;bpy.context.view_layer.update();moved=(best[0].matrix_world@best[0].data.vertices[best[1]].co-best[2]).length;moves.append({'node':node.name,'half_radian_vertex_motion_m':moved,'pass':moved>.1});node.rotation_euler=(0,0,0);bpy.context.view_layer.update()
 frames_unchanged=all(abs(body.matrix_world[r][c]-before_body[r][c])<1e-8 and abs(tail.matrix_world[r][c]-before_tail[r][c])<1e-8 for r in range(4)for c in range(4))
 image_sources=[i.filepath for i in bpy.data.images if i.type=='IMAGE'];mesh_count=len([o for o in bpy.data.objects if o.type=='MESH']);text_count=len([o for o in bpy.data.objects if o.type=='FONT']);m=json.loads((D/'manifest.json').read_text());hole_apothem=.69*math.cos(math.pi/48);tail_radius=m['rotors']['tail']['measured_swept_radius_m']
 contain=[]
 for o in bpy.data.objects:
  if o.type!='MESH' or not o.name.startswith(('Cabin flat interior floor','Fitted aft cabin bulkhead','Seat mounting pedestal','Individual seat cushion','Upholstered seat back','Seat head restraint','Instrument panel housing','Unbranded glass flight display','Cyclic flight control','Anti torque pedal')):continue
  worst=0;dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);me=ev.to_mesh()
  for v in me.vertices:
   q=o.matrix_world@v.co;width,z,hh=h.smooth_interp(rows,q.x);worst=max(worst,(q.y/width)**2+((q.z-z)/hh)**2)
  ev.to_mesh_clear();contain.append({'part':o.name,'max_elliptic_skin_fraction':worst,'pass':worst<=1.0001})
 report={'interior_skin_containment':contain,'result':'PASS'if all(q['pass']for q in moves)and frames_unchanged and not image_sources and all(q['pass']for q in contain) else'FAIL','native_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_glb_sha256':m['sha256'],'editable_mesh_parts':mesh_count,'generic_text_objects':text_count,'native_root':root.name,'native_forward':'+X','native_up':'+Z','independent_rotor_motion':moves,'static_airframe_and_restored_tail_unchanged':frames_unchanged,'external_or_packed_images':image_sources,'tail_duct_clearance':{'conservative_inner_48gon_apothem_m':hole_apothem,'measured_blade_swept_radius_m':tail_radius,'radial_gap_m':hole_apothem-tail_radius,'scope':'Radial aperture clearance; combined actual mesh motion tested separately.'},'provenance':'Original procedural geometry with Blender built-in generic text outlines; no imported geometry/font/image files; reuse license not selected by owner.'};(D/'native_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
