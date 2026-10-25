from pathlib import Path
import json,struct,hashlib,io,math
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'assets/showroom'
def read(p):
 d=p.read_bytes();n=struct.unpack_from('<I',d,12)[0];return json.loads(d[20:20+n]),d[28+n:]
def arr(g,b,n):
 a=g['accessors'][n];v=g['bufferViews'][a['bufferView']];fmt={5126:'f',5125:'I',5123:'H'}[a['componentType']];cnt={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=struct.calcsize('<'+fmt)*cnt;st=v.get('byteStride',size);off=v.get('byteOffset',0)+a.get('byteOffset',0);return [struct.unpack_from('<'+fmt*cnt,b,off+i*st)for i in range(a['count'])]
def mats(g,b):
 out={}
 for m in g['meshes']:
  for pr in m['primitives']:
   n=g['materials'][pr['material']]['name'];ps=arr(g,b,pr['attributes']['POSITION']);ids=[i[0]for i in arr(g,b,pr['indices'])];out[n]=sorted(tuple(sorted(ps[i]for i in ids[j:j+3]))for j in range(0,len(ids),3))
 return out
old,ob=read(O/'v12_baseline/ServiceShowroomLoft.glb');new,nb=read(R/'assets/web/ServiceShowroomLoft.glb');om=mats(old,ob);nm=mats(new,nb)
unchanged={n:om[n]==nm[n]for n in ['Loft_Polished_Basalt','Loft_Graphite_Steel','Loft_Warm_Timber','Loft_Clear_Coastal_Glass','Loft_Warm_Luminous_Strips','Loft_Brushed_Brass']}
normal_error=0
for me in new['meshes']:
 for pr in me['primitives']:
  for n in arr(new,nb,pr['attributes']['NORMAL']):normal_error=max(normal_error,abs(math.sqrt(sum(x*x for x in n))-1))
images=[]
for im in new['images']:
 v=new['bufferViews'][im['bufferView']];d=nb[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];i=Image.open(io.BytesIO(d));i.load();images.append({'name':im['name'],'dimensions':i.size,'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest(),'channel_extrema':i.getextrema(),'decoded_by_Pillow':True})
floor=next(m for m in new['materials']if m['name']=='Loft_Polished_Basalt');pbr=floor['pbrMetallicRoughness']
rep={'result':'PASS' if all(unchanged.values()) and normal_error<1e-5 else 'FAIL','unchanged_actual_triangle_positions_by_material':unchanged,'normal_max_unit_error':normal_error,'embedded_original_maps':images,'floor_pbr':{'roughness_factor':pbr.get('roughnessFactor',1),'metallic_factor':pbr.get('metallicFactor',1),'normal_scale':floor['normalTexture'].get('scale',1),'roughness_tex_G_range':[v/255 for v in images[1]['channel_extrema'][1]],'metallic_tex_B':1},'baseline_glb_sha256':hashlib.sha256((O/'v12_baseline/ServiceShowroomLoft.glb').read_bytes()).hexdigest(),'final_glb_sha256':hashlib.sha256((R/'assets/web/ServiceShowroomLoft.glb').read_bytes()).hexdigest(),'scope':'Decoded original PNG data, numerical GLB mesh normals and exact inner stage/structure triangle-position comparison ignoring UV-driven vertex splits. No GPU rendering claim.'};(O/'loft_v13_binary_validation.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
assert rep['result']=='PASS'
