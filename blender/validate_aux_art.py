"""Actual GLB buffer/ray QA for the far canal tree and isolated showroom."""
import json,struct,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
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


report={'scope':'Actual GLB buffers and CPU triangle rays, not browser frame-rate evidence.','assets':{},'failures':[]};loaded={}
for name,budget,draws in [('CanalRainTreeFar',3500,2),('ServiceShowroomBay',12000,6)]:
 parts,doc=load(WEB/(name+'.glb'));loaded[name]=parts;tri=np.concatenate([p['triangles']for p in parts]);areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;entry={'triangles':len(tri),'draws':len(parts),'degenerate_triangles':int(np.sum(areas<1e-10)),'finite':bool(np.all(np.isfinite(tri))and all(np.all(np.isfinite(p['normals']))for p in parts)),'bounds_three':{'min':tri.reshape(-1,3).min(axis=0).tolist(),'max':tri.reshape(-1,3).max(axis=0).tolist()},'images':len(doc.get('images',[])),'external_buffers':sum('uri'in b for b in doc['buffers']),'sha256':hashlib.sha256((WEB/(name+'.glb')).read_bytes()).hexdigest(),'public_identical':(WEB/(name+'.glb')).read_bytes()==(PUBLIC/(name+'.glb')).read_bytes()};report['assets'][name]=entry
 if len(tri)>budget or len(parts)>draws or entry['degenerate_triangles']or not entry['finite']or entry['images']or entry['external_buffers']or not entry['public_identical']:report['failures'].append(name+' buffer/budget validation failed')
def canon(t):return tuple(sorted(tuple(np.round(v,6))for v in t))
old,_=load(WEB/'CanalRainTree.glb');oldb=np.concatenate([p['triangles']for p in old if 'Bark'in p['material']]);newb=np.concatenate([p['triangles']for p in loaded['CanalRainTreeFar']if 'Bark'in p['material']]);newset={canon(t)for t in newb};miss=sum(canon(t)not in newset for t in oldb);report['canal_bark_preservation']={'original':len(oldb),'preserved':len(oldb)-miss,'missing':miss,'tolerance_m':1e-6}
if miss:report['failures'].append('Canal bark geometry changed')
oldv=np.concatenate([p['triangles'].reshape(-1,3)for p in old]);newv=np.concatenate([p['triangles'].reshape(-1,3)for p in loaded['CanalRainTreeFar']]);delta=float(max(np.max(abs(oldv.min(axis=0)-newv.min(axis=0))),np.max(abs(oldv.max(axis=0)-newv.max(axis=0)))));report['canal_overall_bounds_max_error_m']=delta
if delta>1e-5:report['failures'].append('Far canopy overall bounds changed')
original=WEB/'CanalRainTree.glb';report['original_canal_unchanged']=(ROOT.parent/'kerala_racing_v9/assets/web/CanalRainTree.glb').read_bytes()==original.read_bytes()
if not report['original_canal_unchanged']:report['failures'].append('Original canal tree changed')
tri=np.concatenate([p['triangles']for p in loaded['ServiceShowroomBay']]);e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
def hits(o,d):
 o=np.array(o,dtype=float);d=np.array(d,dtype=float);pv=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,pv);ok=abs(det)>1e-10;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);tv=o-tri[:,0];u=np.einsum('ij,ij->i',tv,pv)*inv;q=np.cross(tv,e1);v=np.einsum('j,ij->i',d,q)*inv;t=np.einsum('ij,ij->i',e2,q)*inv;return t[ok&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>1e-6)]
anchors=[[-2,.5,0],[2,.5,0],[0,1.4,0],[0,.6,0]]+[[x,.35,z]for x in [-1.6,1.6]for z in [-.9,.9]];blocked=[]
for camera in [[7.5,2.4,8.2],[12.4,3.5,13.5]]:
 for anchor in anchors:
  delta=np.array(anchor)-camera;length=np.linalg.norm(delta);hh=hits(camera,delta/length)
  if np.any(hh<length-.02):blocked.append({'camera':camera,'anchor':anchor,'nearest':float(hh.min())})
report['showroom_hero_sightlines']={'tested':16,'blocked':blocked}
if blocked:report['failures'].append('Bay geometry blocks hero camera')
heights=[]
for x,z in [(0,0),(-2,-.9),(-2,.9),(2,-.9),(2,.9)]:
 hh=hits([x,2,z],[0,-1,0]);heights.append(float(2-hh.min()))
report['showroom_stage_height_samples']=heights
if any(abs(h)>1e-6 for h in heights):report['failures'].append('Inspection stage not at Y0')
report['passed']=not report['failures'];(ROOT/'assets/foliage_detail/aux_art_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed']else 1)
