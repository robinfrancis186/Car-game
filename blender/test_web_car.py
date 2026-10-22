import bpy,json,struct,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/web';p=OUT/'car.glb';b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n])
parents={c:i for i,node in enumerate(g['nodes']) for c in node.get('children',[])};names={node.get('name'):i for i,node in enumerate(g['nodes'])};errors=[]
def check(condition,label):
    if not condition:errors.append(label)
for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    check(g['nodes'][parents[names['Spin_'+key]]]['name']=='Steer_'+key,'spin parent '+key)
    check(g['nodes'][parents[names['Wheel_'+key]]]['name']=='Spin_'+key,'wheel parent '+key)
    check(g['nodes'][parents[names['Caliper_'+key]]]['name']=='Steer_'+key,'caliper parent '+key)
check('Crimson multi-coat | original fan concept' in [m['name'] for m in g['materials']],'recolorable paint')
check(hashlib.sha256(b).hexdigest()==hashlib.sha256((ROOT/'web/public/assets/car.glb').read_bytes()).hexdigest(),'public copy hash')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(p))
meshes=[o for o in bpy.data.objects if o.type=='MESH'];bounds=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
d={'bounds_blender_m':{'min':[min(c[i] for c in bounds) for i in range(3)],'max':[max(c[i] for c in bounds) for i in range(3)]},'mesh_count':len(meshes),'draw_calls':sum(len(m['primitives']) for m in g['meshes']),'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives']),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
check(d['mesh_count']==9,'9 merged assemblies');check(d['triangles']<=30000,'30k triangle budget');check(d['draw_calls']<=40,'draw call budget')
# Actual mesh surface intersection checks through a useful steering envelope.
from mathutils.bvhtree import BVHTree
def collision_tree(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles()
    tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True);e.to_mesh_clear();return tree
body_tree=collision_tree(bpy.data.objects['CarBody']);clearance={};displacement={}
baseline={key:(bpy.data.objects['Wheel_'+key].matrix_world@bpy.data.objects['Wheel_'+key].data.vertices[0].co).copy() for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']}
for angle in [0,.4,-.4,.6,-.6]:
    clearance[str(angle)]={}
    for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
        st=bpy.data.objects['Steer_'+key];st.rotation_mode='XYZ';st.rotation_euler.z=angle if key.startswith('Front') else 0;bpy.context.view_layer.update()
        wheel=bpy.data.objects['Wheel_'+key];moved=(wheel.matrix_world@wheel.data.vertices[0].co-baseline[key]).length
        displacement[str(angle)+' '+key]=moved
        if key.startswith('Front') and angle!=0:check(moved>.02,'steering moves actual wheel vertices '+key+' at '+str(angle))
        count=len(body_tree.overlap(collision_tree(bpy.data.objects['Wheel_'+key])));clearance[str(angle)][key]=count;check(count==0,'wheel/body surface clearance '+key+' at '+str(angle))
for key in ['Front_Left','Front_Right']:bpy.data.objects['Steer_'+key].rotation_euler.z=0
bpy.context.view_layer.update();d['wheel_body_intersection_pairs_by_blender_steer_rad']=clearance;d['steered_sample_vertex_displacement_m']=displacement
d['result']='PASS' if not errors else 'FAIL';d['failures']=errors;(OUT/'car_validation.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));assert not errors,errors
# Render the actual reimported GLB under the same neutral studio lighting.
with bpy.data.libraries.load(str(ROOT/'assets/car/roadster_studio.blend'),link=False) as (src,dst):dst.collections=['STUDIO_ONLY'];dst.worlds=['Soft studio']
for c in dst.collections:bpy.context.scene.collection.children.link(c)
s=bpy.context.scene;s.world=dst.worlds[0];s.camera=bpy.data.objects.get('Camera_Hero');s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=625;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.render.filepath=str(OUT/'car_web_preview.png');bpy.ops.render.render(write_still=True)
