"""Browser LOD from the original car. Non-destructive to high-resolution assets."""
import bpy, bmesh, math, json, shutil, struct
from pathlib import Path
from mathutils import Matrix, Vector
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'assets/car';OUT=ROOT/'assets/web';OUT.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC/'roadster_concept.blend'))
scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
original=list(bpy.data.objects);dg=bpy.context.evaluated_depsgraph_get()
col=bpy.data.collections.new('WEB_OPTIMIZED');scene.collection.children.link(col)
root=bpy.data.objects.new('WEB_ROOT_TEMP',None);col.objects.link(root)
roots={};spins={};parts={'body':[]};pivots={}
for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    source=bpy.data.objects['Steer_'+key]
    st=bpy.data.objects.new('WEB_STEER_'+key,None);col.objects.link(st);st.parent=root;st.location=source.matrix_world.translation
    sp=bpy.data.objects.new('WEB_SPIN_'+key,None);col.objects.link(sp);sp.parent=st
    roots[key]=st;spins[key]=sp;parts[key]=[];parts['caliper_'+key]=[]
bpy.context.view_layer.update()
dropped=[];audit=[]
skip=('Rotor_Drill_','Tire_Sipe_','Tread_Groove_','Sidewall_Ring_','Rim_Inner_Lip_','Seat_Stitch_','Display_Text_','Display_Grid_','Display_Map_','Dashboard_VentFin_','Display_Line_','Lug_','Center_Cap_')
def tri_count(mesh):mesh.calc_loop_triangles();return len(mesh.loop_triangles)
def target_for(name,n):
    if name=='Body_SculptedShell':return 6000
    if name.startswith('Seat_'):return min(n,60)
    if name=='Steering_Column':return min(n,48)
    if name.startswith(('Dashboard_','Display_','Interior_')):return min(n,45)
    if name=='Undertray':return n # Preserve boolean wheel-cutout boundaries; aggressive decimation reintroduced tire intersections.
    if name.startswith('Glass_'):return n
    if name.startswith('Tire_'):return 1100
    if name.startswith('Rim_Outer_Lip'):return 280
    if name.startswith('Forged_Spoke'):return 64
    if name.startswith('Wheel_Barrel'):return 160
    if name.startswith('Brake_Rotor'):return 100
    if name.startswith(('Center_Hub','Center_Cap')):return 90
    if name.startswith(('Headlamp','Tail_Light','Roof_Rail')):return 180
    if name.startswith(('Door_Seam','Hood_Shutline','Window_','Rear_Deck_Seam')):return 140
    if name.startswith(('A_Pillar','Rear_Buttress')):return 100
    if name.startswith(('Seat','Interior_')):return 120
    if name.startswith('FICTIONAL_'):return 64
    return min(n,120)
for source in original:
    if source.type!='MESH':continue
    name=source.name
    if name.startswith(skip):dropped.append(name);continue
    parent=source.parent;key=None
    while parent:
        if parent.name.startswith('Spin_'):key=parent.name[5:];break
        parent=parent.parent
    caliper=name.startswith('Brake_Caliper_')
    if caliper:key=name[len('Brake_Caliper_'):]
    parent_new=(roots[key] if caliper else spins[key]) if key else root
    group=('caliper_'+key) if caliper else key or 'body'
    if name.startswith('Glass_'):
        for mod in list(source.modifiers):
            if mod.type=='SOLIDIFY':source.modifiers.remove(mod)
        bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    if name.startswith('Brake_Rotor_'):
        data=bpy.data.meshes.new('Browser solid rotor disc');bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=48,radius1=.218,radius2=.218,depth=.018);bm.to_mesh(data);bm.free()
        for material in source.data.materials:data.materials.append(material)
        for face in data.polygons:face.use_smooth=abs(face.normal.z)<.5
    else:data=bpy.data.meshes.new_from_object(source.evaluated_get(dg),depsgraph=dg)
    data.transform(parent_new.matrix_world.inverted()@source.matrix_world)
    if name.startswith('Wheel_Barrel'):
        bm=bmesh.new();bm.from_mesh(data);bm.normal_update();bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.normal.y)>.5],context='FACES');bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new('WEB_'+name,data);col.objects.link(obj);obj.parent=parent_new
    n=tri_count(data);target=target_for(name,n)
    if n>target:
        dec=obj.modifiers.new('Web LOD triangle budget','DECIMATE');dec.ratio=target/n;dec.use_collapse_triangulate=True
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=dec.name)
    audit.append({'part':name,'source_triangles':n,'web_triangles':tri_count(obj.data)});parts[group].append(obj)
# Delete original detailed hierarchy only in this loaded derivative scene.
for obj in original:bpy.data.objects.remove(obj,do_unlink=True)
root.name='CAR_ROOT';root['prototype']='2017-inspired fan concept; gameplay flight is fictional.'
merged=[]
for group,objects in parts.items():
    if not objects:continue
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=bpy.context.object
    obj.name='CarBody' if group=='body' else ('Caliper_'+group[8:] if group.startswith('caliper_') else 'Wheel_'+group)
    merged.append(obj)
for key,st in roots.items():st.name='Steer_'+key;spins[key].name='Spin_'+key
# Avoid expensive real-time screen-space transmission. Dark glass stays opaque/reflection-driven in browser LOD.
for m in bpy.data.materials:
    if not m.use_nodes:continue
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs and 'glass' in m.name.lower():bs.inputs['Transmission Weight'].default_value=0;bs.inputs['Metallic'].default_value=.28;bs.inputs['Roughness'].default_value=.16
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'car_web.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'car.glb'),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_yup=True)
b=bytearray((OUT/'car.glb').read_bytes());n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);triangles=sum(g['accessors'][p['indices']]['count']//3 for mesh in g['meshes'] for p in mesh['primitives']);draws=sum(len(mesh['primitives']) for mesh in g['meshes'])
manifest={'result':'PASS' if triangles<=30000 and draws<=40 else 'REVIEW','visual_revision':'user-red-reference-2','police_lightbar_mount_y_m':1.232,'format':'glTF 2.0 / GLB','file':'car.glb','bytes':len(b),'triangles':triangles,'material_draw_calls':draws,'mesh_nodes':len(g['meshes']),'forward':'+X','up':'+Y','left':'-Z','car_root':'CAR_ROOT','body_mesh':'CarBody','paint_material':'Crimson multi-coat | original fan concept','steer_axis':'Three.js local +Y','spin_axis_for_forward':'Three.js local -Z','steer_nodes':[s.name for s in roots.values()],'spin_nodes':[s.name for s in spins.values()],'wheel_radius_m':.366,'wheel_centers_three':{k:[s.location.x,s.location.z,-s.location.y] for k,s in roots.items()},'dropped_subpixel_parts':len(dropped),'glass':'Opaque dark PBR reflection material for performance; detailed source retains transmissive glass.','source_asset':'../car/roadster_concept.blend','audit':audit,'lod_notes':['Body shell decimated to ~6000 triangles, silhouette and canopy boundaries retained.','Removed subpixel tire sipes, drilled rotor dots, inner rim lip, lug bolts and stitching.','Opened wheel barrel caps so rotor/spoke depth remains visible.','Each assembly is merged with preserved materials; calipers steer but do not spin.']}
(OUT/'car_manifest.json').write_text(json.dumps(manifest,indent=2))
PUBLIC=ROOT/'web/public/assets';PUBLIC.mkdir(exist_ok=True,parents=True);shutil.copyfile(OUT/'car.glb',PUBLIC/'car.glb');shutil.copyfile(OUT/'car_manifest.json',PUBLIC/'car_manifest.json')
print('WEB_CAR_READY',json.dumps({k:manifest[k] for k in ['result','bytes','triangles','material_draw_calls','mesh_nodes']}))
