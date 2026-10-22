import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/landscape_reference_kit';results=[]
for key in ('BirdRockLookout','CanalRainTree','CanalShikara'):
 bpy.ops.wm.open_mainfile(filepath=str(OUT/(key+'.blend')))
 root=bpy.data.objects.get(key);parts=[o for o in root.children_recursive if o.type=='MESH'] if root else[]
 finite=all(math.isfinite(c)for o in parts for v in o.data.vertices for c in v.co)
 external_images=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath]
 r={'asset':key,'source_root_exists':bool(root),'independently_editable_mesh_parts':len(parts),'finite_geometry':finite,'external_image_dependencies':external_images,'result':'PASS'if root and len(parts)>20 and finite and not external_images else'FAIL'}
 results.append(r)
(OUT/'native_source_validation.json').write_text(json.dumps({'result':'PASS'if all(x['result']=='PASS'for x in results)else'FAIL','assets':results},indent=2));print(results)
