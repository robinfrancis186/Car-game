import bpy,json,struct,math,hashlib
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parent
manifest=json.loads((OUT/'environment_web_manifest.json').read_text());result={'tool':'Blender '+bpy.app.version_string,'tests':[]}
for name,a in manifest['assets'].items():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    p=OUT/a['file'];data=p.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n])
    bpy.ops.import_scene.gltf(filepath=str(p))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)];src=a['source_bounds_blender_m'];err=max(abs(v-src[key][i]) for key,vals in [('min',lo),('max',hi)] for i,v in enumerate(vals))
    zero=sum(1 for o in meshes for f in o.data.polygons if f.area<1e-10)
    finite=all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co)
    normal_fail=0
    if name in ('Course_Road','Course_Terrain','Course_Water'):
        normal_fail=sum(1 for o in meshes for f in o.data.polygons if (o.matrix_world.to_3x3()@f.normal).z < -.01)
    leaf_prims=[p for mesh in doc.get('meshes',[]) for p in mesh['primitives'] if 'Palm_LeafColor' in doc['materials'][p['material']].get('name','')]
    colors=all('COLOR_0' in p['attributes'] and doc['materials'][p['material']].get('doubleSided',False) for p in leaf_prims)
    record={'asset':name,'mesh_count':len(meshes),'finite':finite,'degenerate_polygons':zero,'max_bounds_error_m':err,'downward_course_faces':normal_fail,'palm_vertex_color_and_two_sided':colors,'sha256_match':hashlib.sha256(data).hexdigest()==a['sha256']}
    record['pass']=bool(meshes) and finite and zero==0 and err<.015 and normal_fail==0 and colors and record['sha256_match'];result['tests'].append(record);print('WEB_QA',name,record)
result['passed']=sum(t['pass'] for t in result['tests']);result['total']=len(result['tests']);(OUT/'environment_web_validation.json').write_text(json.dumps(result,indent=2));print('WEB_VALIDATION_COMPLETE',result['passed'],result['total'])
