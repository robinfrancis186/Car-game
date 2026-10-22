import bpy,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];items=[('assets/foliage_detail/Highland_Foliage_Detail.blend','HighlandShadeTreeNear',5688),('assets/foliage_detail/Highland_Foliage_Detail.blend','TeaLeafCluster',160),('assets/foliage_detail/CanalRainTreeFar.blend','CanalRainTreeFar',3496),('assets/showroom/ServiceShowroomBay.blend','ServiceShowroomBay',8562)];report={'scope':'Read-only Blender native-library loading, not a screenshot test.','assets':{},'passed':True}
for source,name,budget in items:
 with bpy.data.libraries.load(str(R/source),link=False)as(src,dst):
  assert name in src.collections,name;dst.collections=[name]
 col=dst.collections[0];objects=[o for o in col.all_objects if o.type=='MESH'];tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons)for o in objects);finite=all(math.isfinite(c)for o in objects for v in o.data.vertices for c in v.co);assert tri==budget,(name,tri,budget);assert finite
 report['assets'][name]={'source':source,'collection':name,'editable_mesh_objects':len(objects),'triangles':tri,'finite':finite,'materials':sorted({m.name for o in objects for m in o.data.materials}),'source_sha256':hashlib.sha256((R/source).read_bytes()).hexdigest()}
(R/'assets/foliage_detail/native_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
