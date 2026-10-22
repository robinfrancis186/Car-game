"""Independent GLB payload check, no Blender or third-party packages needed."""
from pathlib import Path
import json, struct, math, hashlib
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
manifest=json.loads((BASE/'urban_assets_manifest.json').read_text())
reports=[]

def read_accessor(doc,binary,idx):
    a=doc['accessors'][idx];view=doc['bufferViews'][a['bufferView']]
    fmt={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    size=struct.calcsize('<'+fmt*n);stride=view.get('byteStride',size)
    start=view.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*n,binary,start+i*stride) for i in range(a['count'])]

for asset in manifest['assets']:
    path=ROOT/asset['file'];data=path.read_bytes()
    magic,ver,total=struct.unpack_from('<III',data,0)
    assert magic==0x46546c67 and ver==2 and total==len(data)
    jslen,jstype=struct.unpack_from('<II',data,12)
    assert jstype==0x4e4f534a
    doc=json.loads(data[20:20+jslen]);offset=20+jslen
    blen,btype=struct.unpack_from('<II',data,offset)
    assert btype==0x004e4942
    binary=data[offset+8:offset+8+blen]
    assert not doc.get('images') and not doc.get('textures')
    assert all('uri' not in b for b in doc['buffers'])
    assert all('matrix' not in n and 'translation' not in n and 'rotation' not in n and 'scale' not in n for n in doc['nodes'])
    count=0;degenerate=0;positions=[]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4
            verts=read_accessor(doc,binary,primitive['attributes']['POSITION']);positions.extend(verts)
            indices=[x[0] for x in read_accessor(doc,binary,primitive['indices'])]
            assert all(math.isfinite(x) for p in verts for x in p)
            assert all(0<=i<len(verts) for i in indices)
            if 'NORMAL' in primitive['attributes']:
                normals=read_accessor(doc,binary,primitive['attributes']['NORMAL'])
                assert all(math.isfinite(x) for n in normals for x in n)
            count+=len(indices)//3
            for i in range(0,len(indices),3):
                a,b,c=[verts[indices[j]] for j in (i,i+1,i+2)]
                u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
                cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                if sum(x*x for x in cross)<1e-16:degenerate+=1
    assert count==asset['triangles'] and count<=asset['triangle_budget']
    lo=[min(v[k] for v in positions) for k in range(3)];hi=[max(v[k] for v in positions) for k in range(3)]
    assert all(abs(lo[k]-asset['bounds_gltf_xyz_m']['min'][k])<1e-4 and abs(hi[k]-asset['bounds_gltf_xyz_m']['max'][k])<1e-4 for k in range(3))
    assert hashlib.sha256(data).hexdigest()==asset['sha256']
    assert (ROOT/'web/public/assets'/path.name).read_bytes()==data
    assert degenerate==0,(asset['name'],degenerate)
    reports.append({'name':asset['name'],'triangles':count,'finite_binary_vertices':True,'degenerate_triangles':degenerate,'bounds_exact':True,'public_copy_identical':True,'external_dependencies':0})
report={'status':'pass','assets':reports}
(BASE/'binary_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
