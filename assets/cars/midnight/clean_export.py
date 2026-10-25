"""Remove only triangles that become degenerate after runtime float32 quantization."""
def clean(path,manifest):
 import struct,json,math,hashlib
 raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jl]);bo=20+jl;bl=struct.unpack_from('<I',raw,bo)[0];binary=bytearray(raw[bo+8:bo+8+bl]);removed=0;normal_repairs=0;unused_normal_repairs=0
 for mi,mesh in enumerate(g['meshes']):
  nr=0
  for pr in mesh['primitives']:
   a=g['accessors'][pr['attributes']['POSITION']];av=g['bufferViews'][a['bufferView']];ao=av.get('byteOffset',0)+a.get('byteOffset',0);step=av.get('byteStride',12);ia=g['accessors'][pr['indices']];iv=g['bufferViews'][ia['bufferView']];io=iv.get('byteOffset',0)+ia.get('byteOffset',0);fmt={5123:'H',5125:'I'}[ia['componentType']];sz=struct.calcsize('<'+fmt);ids=struct.unpack_from('<'+str(ia['count'])+fmt,binary,io);valid=[]
   for j in range(0,len(ids),3):
    p=[struct.unpack_from('<fff',binary,ao+ids[j+k]*step)for k in range(3)];a=[p[1][k]-p[0][k]for k in range(3)];b=[p[2][k]-p[0][k]for k in range(3)];cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    if sum(x*x for x in cross)<1e-18:nr+=1
    else:valid.extend(ids[j:j+3])
   struct.pack_into('<'+str(len(valid))+fmt,binary,io,*valid);ia['count']=len(valid);iv['byteLength']=len(valid)*sz
   # Blender's hardened Boolean bevel emits occasional zero corner normals.
   # Fill only invalid normals from the surviving incident triangle geometry;
   # valid manufactured normals and every position remain byte-identical.
   na=g['accessors'][pr['attributes']['NORMAL']];nv=g['bufferViews'][na['bufferView']];no=nv.get('byteOffset',0)+na.get('byteOffset',0);ns=nv.get('byteStride',12);norms=[list(struct.unpack_from('<fff',binary,no+i*ns))for i in range(na['count'])];bad={i for i,n in enumerate(norms)if sum(x*x for x in n)<.25};sums={i:[0.,0.,0.]for i in bad};first={}
   for j in range(0,len(valid),3):
    ids3=valid[j:j+3];p3=[struct.unpack_from('<fff',binary,ao+i*step)for i in ids3];aa=[p3[1][k]-p3[0][k]for k in range(3)];bb=[p3[2][k]-p3[0][k]for k in range(3)];cc=[aa[1]*bb[2]-aa[2]*bb[1],aa[2]*bb[0]-aa[0]*bb[2],aa[0]*bb[1]-aa[1]*bb[0]]
    for i in ids3:
     if i in bad:sums[i]=[sums[i][k]+cc[k]for k in range(3)];first.setdefault(i,cc)
   for i in bad:
    v=sums[i];length=math.sqrt(sum(x*x for x in v))
    if length<1e-12:v=first.get(i,[0.,0.,1.]);length=math.sqrt(sum(x*x for x in v));unused_normal_repairs+=int(i not in first)
    struct.pack_into('<fff',binary,no+i*ns,*(x/length for x in v));normal_repairs+=1

  for node in g['nodes']:
   if node.get('mesh')==mi:manifest['rigid_groups'][node['name']]['triangles']-=nr
  removed+=nr
 jb=json.dumps(g,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);blob=struct.pack('<III',0x46546c67,2,28+len(jb)+len(binary))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(binary),0x004e4942)+binary;path.write_bytes(blob)
 manifest.update({'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'triangles':manifest['triangles']-removed,'float32_degenerate_triangles_removed':removed,'invalid_runtime_corner_normals_repaired_from_incident_faces':normal_repairs,'unused_normal_repairs':unused_normal_repairs});return manifest
if __name__=='__main__':
 import json
 from pathlib import Path
 p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text());clean(p/'car_midnight.glb',m);(p/'manifest.json').write_text(json.dumps(m,indent=2));print(m['sha256'],m['triangles'])
