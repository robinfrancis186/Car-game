import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
manifest=json.loads((OUT/'manifest.json').read_text())
report={'tool':'Blender '+bpy.app.version_string,'tests':[],'limitations':['Unreal import and in-engine performance not tested: Unreal unavailable in this cloud.','Procedural Blender noise materials are intentionally not baked into FBX/GLB.']}
for name,a in manifest['assets'].items():
    for ext in ('fbx','glb'):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        if ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(OUT/a[ext]))
        else:bpy.ops.import_scene.gltf(filepath=str(OUT/a[ext]))
        meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];coords=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
        lo=[min(v[k] for v in coords) for k in range(3)];hi=[max(v[k] for v in coords) for k in range(3)]
        dims=[hi[k]-lo[k] for k in range(3)];err=max(abs(dims[k]-a['dimensions_m'][k]) for k in range(3))
        bad=sum(1 for o in meshes for v in o.data.vertices if not all(math.isfinite(c) for c in v.co))
        zero=sum(1 for o in meshes for p in o.data.polygons if p.area<1e-10)
        r={'asset':name,'format':ext,'exists':True,'imported_meshes':len(meshes),'finite_vertices':bad==0,'degenerate_polygons':zero,'dimensions_m':dims,'max_dimension_error_m':err,'pass':bool(meshes) and bad==0 and err<.01 and zero==0}
        report['tests'].append(r);print('QA',name,ext,r['pass'],'degenerate',zero,'dim_error',err)
report['passed']=sum(t['pass'] for t in report['tests']);report['total']=len(report['tests'])
(OUT/'export_validation.json').write_text(json.dumps(report,indent=2))
print('VALIDATION_COMPLETE',report['passed'],report['total'])
