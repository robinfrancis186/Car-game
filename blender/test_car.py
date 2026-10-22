import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]/'assets/car'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_concept.blend'))
r={'checks':[]}
meshes=[o for o in bpy.data.objects if o.type=='MESH']
r['mesh_count']=len(meshes);r['original_polygons']=sum(len(o.data.polygons) for o in meshes)
body=bpy.data.objects['Body_SculptedShell'];bm=bmesh.new();bm.from_mesh(body.data);r['shell_signed_volume']=bm.calc_volume(signed=True);r['shell_boundary_edges']=sum(e.is_boundary for e in bm.edges);bm.free()
bounds=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
r['bounds_m']={'min':[min(v[i] for v in bounds) for i in range(3)],'max':[max(v[i] for v in bounds) for i in range(3)]}
for name in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    p=bpy.data.objects['Steer_'+name];s=bpy.data.objects['Spin_'+name];t=bpy.data.objects['Tire_'+name]
    r['checks'].append({'name':name,'center':list(p.matrix_world.translation),'tire_local_location':list(t.location),'tire_world_origin':list(t.matrix_world.translation),'spin_is_child_of_steer':s.parent==p,'tire_is_child_of_spin':t.parent==s})
# Shared boundaries eliminate detached canopy panels; outward side normals survive one-sided materials.
w=bpy.data.objects['Glass_Windshield'];roof=bpy.data.objects['Glass_Targa_Roof'];rear=bpy.data.objects['Glass_Rear']
r['canopy_seam_max_m']=max(max((w.data.vertices[len(w.data.vertices)-25+i].co-roof.data.vertices[i].co).length for i in range(25)),max((rear.data.vertices[i].co-roof.data.vertices[len(roof.data.vertices)-25+i].co).length for i in range(25)))
r['side_glass_normal_y']={str(s):sum(p.normal.y*p.area for p in bpy.data.objects['Glass_Side_'+str(s)].data.polygons) for s in [-1,1]}
r['fender_crown_clearance_m']={}
for name in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    p=bpy.data.objects['Steer_'+name].matrix_world.translation
    found,hit,normal,idx=body.ray_cast(Vector((p.x,p.y,3)),Vector((0,0,-1)))
    r['fender_crown_clearance_m'][name]=(hit.z-(p.z+.366)) if found else None
bpy.context.scene.frame_set(31);bpy.context.view_layer.update()
r['frame31_front_steer_rad']=bpy.data.objects['Steer_Front_Left'].rotation_euler.z;r['frame31_spin_rad']=bpy.data.objects['Spin_Front_Left'].rotation_euler.y
# Reimport each static FBX and audit bounds, transforms, material slots.
r['fbx_roundtrip']={}
for fname in ['SM_CarBody','SM_Wheel_Front_Left','SM_Wheel_Front_Right','SM_Wheel_Rear_Left','SM_Wheel_Rear_Right']:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(OUT/(fname+'.fbx')))
    obs=[o for o in bpy.data.objects if o.type=='MESH'];bound=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
    r['fbx_roundtrip'][fname]={'mesh_count':len(obs),'bounds_min':[min(v[i] for v in bound) for i in range(3)],'bounds_max':[max(v[i] for v in bound) for i in range(3)],'material_slots':sum(len(o.data.materials) for o in obs),'origins':[list(o.location) for o in obs]}
# Full GLB roundtrip: hierarchy and materials survive interchange.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'roadster_concept.glb'))
obs=[o for o in bpy.data.objects if o.type=='MESH'];r['glb_roundtrip']={'mesh_count':len(obs),'pivot_count':len([o for o in bpy.data.objects if o.name.startswith(('Steer_','Spin_'))]),'material_count':len({m.name for o in obs for m in o.data.materials})}
failures=[]
def check(ok,label):
    if not ok:failures.append(label)
check(r['canopy_seam_max_m']<1e-6,'continuous canopy shared boundary')
check(r['side_glass_normal_y']['1']>0 and r['side_glass_normal_y']['-1']<0,'side glass outward normals')
check(all(v is not None and v>0 for v in r['fender_crown_clearance_m'].values()),'fender crowns above tire tops')
check(r['shell_boundary_edges']==0,'body shell must be closed')
check(r['shell_signed_volume']>0,'body shell must have outward volume')
check(all(c['spin_is_child_of_steer'] and c['tire_is_child_of_spin'] for c in r['checks']),'all articulated parent chains')
check(abs(r['frame31_front_steer_rad']-.4)<1e-5,'front steer animation')
check(abs(r['frame31_spin_rad']-math.pi)<1e-5,'wheel spin animation')
for name,v in r['fbx_roundtrip'].items():
    check(v['mesh_count']==1,name+' combined mesh count')
    check(max(abs(a) for a in v['origins'][0])<1e-5,name+' centered origin')
    if 'Wheel' in name:
        check(abs(v['bounds_min'][0]+.3672)<.003 and abs(v['bounds_max'][0]-.3672)<.003,name+' X radius')
        check(abs(v['bounds_min'][2]+.3672)<.003 and abs(v['bounds_max'][2]-.3672)<.003,name+' Z radius')
        check(max(abs(v['bounds_min'][1]),abs(v['bounds_max'][1]))<.16,name+' axle width')
check(r['glb_roundtrip']['pivot_count']==8,'eight pivots in GLB')
r['result']='PASS' if not failures else 'FAIL';r['failed_checks']=failures
(OUT/'validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
assert not failures,failures

