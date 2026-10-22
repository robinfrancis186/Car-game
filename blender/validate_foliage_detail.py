"""Actual-buffer V10 foliage QA; CPU only, not browser/GPU evidence."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets';OUT=ROOT/'assets/foliage_detail'
def load(path):
 data=path.read_bytes();size,kind=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+size]);offset=20+size;n,t=struct.unpack_from('<II',data,offset);blob=data[offset+8:offset+8+n];dt={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'};comps={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 def acc(idx):
  a=doc['accessors'][idx];view=doc['bufferViews'][a['bufferView']];dtype=np.dtype(dt[a['componentType']]);c=comps[a['type']];stride=view.get('byteStride',c*dtype.itemsize);return np.ndarray((a['count'],c),dtype=dtype,buffer=blob,offset=view.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dtype.itemsize)).copy()
 def local(node):
  if 'matrix'in node:return np.array(node['matrix']).reshape(4,4).T
  x,y,z,r=node.get('rotation',[0,0,0,1]);m=np.eye(4);m[:3,:3]=[[1-2*y*y-2*z*z,2*x*y-2*z*r,2*x*z+2*y*r],[2*x*y+2*z*r,1-2*x*x-2*z*z,2*y*z-2*x*r],[2*x*z-2*y*r,2*y*z+2*x*r,1-2*x*x-2*y*y]];m[:3,:3]*=np.array(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
 result=[]
 def walk(i,parent):
  node=doc['nodes'][i];m=parent@local(node)
  if 'mesh'in node:
   for p in doc['meshes'][node['mesh']]['primitives']:
    vv=acc(p['attributes']['POSITION']).astype(float);vv=vv@m[:3,:3].T+m[:3,3];ii=acc(p['indices']).reshape(-1,3).astype(int);normal=acc(p['attributes']['NORMAL']).astype(float) if 'NORMAL'in p['attributes'] else None;mat=doc.get('materials',[{}])[p.get('material',0)];result.append({'vertices':vv,'indices':ii,'triangles':vv[ii],'material':mat.get('name',''),'normals':normal,'node':node.get('name',''),'colors':acc(p['attributes']['COLOR_0']) if 'COLOR_0' in p['attributes'] else None})
  for child in node.get('children',[]):walk(child,m)
 for node in doc['scenes'][doc.get('scene',0)]['nodes']:walk(node,np.eye(4))
 return result,doc

report={'scope':'Actual GLB buffer inspection and unchanged-source comparison; no GPU/performance claim.','assets':{},'failures':[]}
loaded={}
for name,budget in [('HighlandShadeTreeNear',6000),('TeaLeafCluster',180)]:
 parts,doc=load(WEB/(name+'.glb'));loaded[name]=parts;tri=np.concatenate([p['triangles']for p in parts]);cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);areas=np.linalg.norm(cross,axis=1)/2;bad=int(np.sum(areas<1e-10));colors=np.concatenate([p['colors']for p in parts if p['colors']is not None]);normal=np.concatenate([p['normals']for p in parts]);finite=bool(np.all(np.isfinite(tri))and np.all(np.isfinite(normal))and np.all(np.isfinite(colors)));entry={'triangles':len(tri),'draws':len(parts),'zero_area':bad,'finite':finite,'unique_vertex_colors':len(np.unique(colors,axis=0)),'normal_length_max_error':float(np.max(abs(np.linalg.norm(normal,axis=1)-1))),'images':len(doc.get('images',[])),'external_buffers':sum('uri'in b for b in doc['buffers']),'double_sided_materials':[m.get('doubleSided',False)for m in doc['materials']],'bounds_three':{'min':tri.reshape(-1,3).min(axis=0).tolist(),'max':tri.reshape(-1,3).max(axis=0).tolist()},'bytes':(WEB/(name+'.glb')).stat().st_size,'sha256':hashlib.sha256((WEB/(name+'.glb')).read_bytes()).hexdigest(),'public_identical':(WEB/(name+'.glb')).read_bytes()==(PUBLIC/(name+'.glb')).read_bytes()};report['assets'][name]=entry
 if bad or not finite or len(tri)>budget or len(parts)>3 or entry['images'] or entry['external_buffers'] or not entry['public_identical']:report['failures'].append(name+' geometry/budget/provenance failed')
far,_=load(WEB/'HighlandShadeTree.glb');old=np.concatenate([p['triangles']for p in far if 'Bark'in p['material']]);near=np.concatenate([p['triangles']for p in loaded['HighlandShadeTreeNear']if 'Bark'in p['material']])
def canonical(t):return tuple(sorted(tuple(np.round(v,6))for v in t))
newset={canonical(t)for t in near};missing=[t for t in old if canonical(t)not in newset];report['original_trunk_and_branches']={'old_triangles':len(old),'preserved_exact_triangles':len(old)-len(missing),'missing':len(missing),'tolerance_m':1e-6}
if missing:report['failures'].append('Original trunk/branch triangles not preserved')
base=json.loads((OUT/'immutable_baseline_hashes.json').read_text());unchanged={name:hashlib.sha256((WEB/name).read_bytes()).hexdigest()==data['sha256']for name,data in base.items()};report['immutable_files_unchanged']=unchanged
runtime_diffs={}
for name in ['course_runtime.json','course_runtime_highlands.json']:
 before=json.loads((ROOT.parent/'kerala_racing_v9/assets/web'/name).read_text());after=json.loads((WEB/name).read_text());changed=[k for k in set(before)|set(after)if before.get(k)!=after.get(k)];runtime_diffs[name]=changed
 for key in changed:
  if key not in ['explore_starts','world']:report['failures'].append(name+' unexpected changed field '+key)
 if 'world'in changed:
  nested=[k for k in set(before['world'])|set(after['world'])if before['world'].get(k)!=after['world'].get(k)];runtime_diffs[name+'_world_keys']=nested
  if any(k!='explore_starts'for k in nested):report['failures'].append(name+' unexpected changed world field')
report['builder_owned_explore_metadata_changes']=runtime_diffs
if not all(ok for name,ok in unchanged.items()if name not in runtime_diffs):report['failures'].append('Existing immutable mesh/grid/collider baseline changed')
report['passed']=not report['failures'];(OUT/'binary_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
