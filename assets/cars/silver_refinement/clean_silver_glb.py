"""Remove only zero-area float32 triangles from the Silver export; no vertex edits."""
import struct,json,math
from pathlib import Path
def clean(path):
 p=Path(path);blob=p.read_bytes();jn=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+jn]);off=20+jn;bn=struct.unpack_from('<I',blob,off)[0];binary=bytearray(blob[off+8:off+8+bn]);removed=0;details=[]
 def offset(a):return g['bufferViews'][a['bufferView']].get('byteOffset',0)+a.get('byteOffset',0)
 for me in g['meshes']:
  for prim in me['primitives']:
   pa=g['accessors'][prim['attributes']['POSITION']];pv=g['bufferViews'][pa['bufferView']];ps=pv.get('byteStride',12);po=offset(pa)
   ia=g['accessors'][prim['indices']];iv=g['bufferViews'][ia['bufferView']];fmt={5121:'B',5123:'H',5125:'I'}[ia['componentType']];sz=struct.calcsize(fmt);io=offset(ia);indices=struct.unpack_from('<'+str(ia['count'])+fmt,binary,io);keep=[]
   for i in range(0,len(indices),3):
    a,b,c=[struct.unpack_from('<3f',binary,po+indices[i+j]*ps) for j in range(3)];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    if sum(x*x for x in cross)<1e-20:removed+=1
    else:keep.extend(indices[i:i+3])
   if len(keep)!=len(indices):
    binary[io:io+len(keep)*sz]=struct.pack('<'+str(len(keep))+fmt,*keep);iv['byteLength']=ia.get('byteOffset',0)+len(keep)*sz;ia['count']=len(keep)
    if 'min'in ia:ia['min']=[min(keep)]
    if 'max'in ia:ia['max']=[max(keep)]
    details.append({'mesh':me.get('name'),'material':g['materials'][prim['material']]['name'],'removed':(len(indices)-len(keep))//3})
 jb=json.dumps(g,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);binary+=b'\0'*((-len(binary))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(jb)+len(binary))+struct.pack('<II',len(jb),0x4E4F534A)+jb+struct.pack('<II',len(binary),0x004E4942)+binary)
 return {'removed_zero_area_triangles':removed,'details':details,'scope':'Only degenerate index triples removed after float32 export; positions/normals/materials/rig are unmodified.'}
