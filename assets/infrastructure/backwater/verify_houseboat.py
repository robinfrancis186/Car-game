"""Independent actual GLB payload verification; standard library only."""
from pathlib import Path
import json,struct,hashlib,math
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
m=json.loads((BASE/'houseboat_manifest.json').read_text());data=(ROOT/m['file']).read_bytes()
assert struct.unpack_from('<III',data,0)==(0x46546c67,2,len(data))
jlen=struct.unpack_from('<I',data,12)[0];d=json.loads(data[20:20+jlen]);binary=data[28+jlen:]
assert not d.get('images') and not d.get('textures') and all('uri' not in b for b in d['buffers'])
assert all(not any(k in n for k in ('translation','rotation','scale','matrix')) for n in d['nodes'])
def acc(i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];f={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=struct.calcsize('<'+f*n);off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from('<'+f*n,binary,off+j*v.get('byteStride',size)) for j in range(a['count'])]
verts=[];triangles=0;degens=0
for mesh in d['meshes']:
 for p in mesh['primitives']:
  v=acc(p['attributes']['POSITION']);ix=[x[0] for x in acc(p['indices'])];verts+=v;triangles+=len(ix)//3
  assert all(math.isfinite(x) for a in v for x in a)
  assert all(0<=i<len(v) for i in ix)
  if 'NORMAL' in p['attributes']:assert all(math.isfinite(x) for a in acc(p['attributes']['NORMAL']) for x in a)
  for i in range(0,len(ix),3):
   a,b,c=[v[ix[j]] for j in (i,i+1,i+2)];u=[b[k]-a[k] for k in range(3)];w=[c[k]-a[k] for k in range(3)];cr=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]]
   if sum(x*x for x in cr)<1e-16:degens+=1
lo=[min(a[k] for a in verts) for k in range(3)];hi=[max(a[k] for a in verts) for k in range(3)]
assert triangles==m['triangles'] and triangles<=5000
assert degens==0,degens
assert all(abs(lo[k]-m['bounds_gltf_xyz_m']['min'][k])<1e-5 and abs(hi[k]-m['bounds_gltf_xyz_m']['max'][k])<1e-5 for k in range(3))
assert hashlib.sha256(data).hexdigest()==m['sha256']
assert data==(ROOT/'web/public/assets/KeralaHouseboat.glb').read_bytes()
r={'status':'pass','triangles':triangles,'degenerate_triangles':degens,'finite_positions_normals':True,'waterline_pivot_and_exact_bounds':True,'identity_node_transforms':True,'no_external_buffers_or_texture_images':True,'public_copy_identical':True,'sha256_verified':True}
(BASE/'binary_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
