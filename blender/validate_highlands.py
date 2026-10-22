"""Numerical QA of actual exported GLB buffers against the runtime height/grid contract.
CPU geometry audit, not browser rendering/FPS or user play evidence.
"""
from pathlib import Path
import json,struct,hashlib,math
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets';w=json.loads((WEB/'course_runtime_highlands.json').read_text());grid=w['terrain_grid'];nx,nz=grid['count'];dx,dz=grid['step'];xmin,zmin=grid['origin'];H=np.array(grid['heights']).reshape(nz,nx)
def sample(x,z):
 u=(np.asarray(x)-xmin)/dx;v=(np.asarray(z)-zmin)/dz;i=np.clip(np.floor(u).astype(int),0,nx-2);j=np.clip(np.floor(v).astype(int),0,nz-2);u=np.clip(u-i,0,1);v=np.clip(v-j,0,1);a,b,c,d=H[j,i],H[j,i+1],H[j+1,i],H[j+1,i+1];return np.where(v<=u,a+(b-a)*u+(d-b)*v,a+(d-c)*u+(c-a)*v)
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
    vv=acc(p['attributes']['POSITION']).astype(float);vv=vv@m[:3,:3].T+m[:3,3];ii=acc(p['indices']).reshape(-1,3).astype(int);normal=acc(p['attributes']['NORMAL']).astype(float) if 'NORMAL'in p['attributes'] else None;mat=doc.get('materials',[{}])[p.get('material',0)];result.append({'vertices':vv,'indices':ii,'triangles':vv[ii],'material':mat.get('name',''),'normals':normal,'node':node.get('name','')})
  for child in node.get('children',[]):walk(child,m)
 for node in doc['scenes'][doc.get('scene',0)]['nodes']:walk(node,np.eye(4))
 return result,doc
report={'scope':'Actual GLB binary geometry and runtime JSON CPU audit; no GPU/browser/performance assertion.','files':{},'failures':[]};meshes={}
for name in ['Highlands_Terrain.glb','Highlands_Road.glb','Highlands_Tea.glb','Highlands_Furniture.glb','HighlandShadeTree.glb','HighlandGateway.glb']:
 parts,doc=load(WEB/name);meshes[name]=parts;tris=np.concatenate([p['triangles'] for p in parts]);cross=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);areas=np.linalg.norm(cross,axis=1)/2;bad=int(np.sum(areas<1e-10));finite=bool(np.all(np.isfinite(tris)));normalfinite=all(p['normals'] is None or np.all(np.isfinite(p['normals'])) for p in parts);same=(WEB/name).read_bytes()==(PUBLIC/name).read_bytes();report['files'][name]={'sha256':hashlib.sha256((WEB/name).read_bytes()).hexdigest(),'bytes':(WEB/name).stat().st_size,'triangles':len(tris),'primitives':len(parts),'zero_area_triangles':bad,'finite_vertices_normals':finite and normalfinite,'public_identical':same,'materials':[m.get('name') for m in doc.get('materials',[])]}
 if bad or not finite or not normalfinite or not same:report['failures'].append(name+' failed binary validation')
terrain=np.concatenate([p['triangles'] for p in meshes['Highlands_Terrain.glb']]);centers=terrain.mean(axis=1);inside=(centers[:,0]>=xmin)&(centers[:,0]<=xmin+(nx-1)*dx)&(centers[:,2]>=zmin)&(centers[:,2]<=zmin+(nz-1)*dz);error=np.abs(centers[inside,1]-sample(centers[inside,0],centers[inside,2]));up=np.cross(terrain[:,1]-terrain[:,0],terrain[:,2]-terrain[:,0])[:,1]
report['terrain']={'inside_triangle_centroids':int(inside.sum()),'max_exact_grid_error_m':float(error.max()),'downward_or_vertical_faces':int(np.sum(up<=0)),'height_range_m':[float(terrain[:,:,1].min()),float(terrain[:,:,1].max())],'flat_horizon_apron_extends_m':6000}
if error.max()>.00003 or np.any(up<=0):report['failures'].append('Terrain triangles mismatch grid or winding')
asphalt=np.concatenate([p['triangles'] for p in meshes['Highlands_Road.glb'] if 'Asphalt'in p['material']]);cent=asphalt[:,:,::2].mean(axis=1);tree=cKDTree(cent);rr=np.array(w['route_points']);ss=np.array(w['horizontal_route_distances_m']);queries=[]
for section in w['road_sections']:
 for s in np.arange(section['startS']+.1,section['endS']-.1,4):
  i=min(len(ss)-2,max(0,np.searchsorted(ss,s,side='right')-1));f=(s-ss[i])/(ss[i+1]-ss[i]);p=rr[i]*(1-f)+rr[i+1]*f;d=rr[i+1,[0,2]]-rr[i,[0,2]];d/=np.linalg.norm(d);n=np.array([-d[1],d[0]])
  for strip in section['driveableStrips']:
   for l in [-strip['halfWidth']+.12,0,strip['halfWidth']-.12]:
    xz=p[[0,2]]+n*(strip['centerOffset']+l);queries.append([xz[0],xz[1],p[1],s])
queries=np.array(queries);_,near=tree.query(queries[:,:2],k=40);tri=asphalt[near];a=tri[:,:,0][:,:,[0,2]];b=tri[:,:,1][:,:,[0,2]];c=tri[:,:,2][:,:,[0,2]];d=b-a;e=c-a;v=queries[:,None,:2]-a;den=d[:,:,0]*e[:,:,1]-d[:,:,1]*e[:,:,0];u=(v[:,:,0]*e[:,:,1]-v[:,:,1]*e[:,:,0])/den;t=(d[:,:,0]*v[:,:,1]-d[:,:,1]*v[:,:,0])/den;hits=(u>=-2e-5)&(t>=-2e-5)&(u+t<=1.00002);yy=tri[:,:,0,1]+u*(tri[:,:,1,1]-tri[:,:,0,1])+t*(tri[:,:,2,1]-tri[:,:,0,1]);yy=np.where(hits,yy,np.nan);hitcount=np.any(hits,axis=1);errors=np.abs(np.nanmax(yy[hitcount],axis=1)-queries[hitcount,2]);report['road']={'asphalt_queries':len(queries),'hits':int(hitcount.sum()),'misses':int(np.sum(~hitcount)),'max_height_error_m':float(errors.max()),'mean_error_m':float(errors.mean()),'upward_faces':int(np.sum(np.cross(asphalt[:,1]-asphalt[:,0],asphalt[:,2]-asphalt[:,0])[:,1]>0)),'miss_samples':queries[~hitcount][:10].tolist()}
if not np.all(hitcount) or errors.max()>.035:report['failures'].append('Road actual-asphalt coverage/height mismatch')
# All route samples are earth-supported at exactly +.18m; hill elevation is not an implicit flyover.
route_error=np.abs(rr[:,1]-sample(rr[:,0],rr[:,2])-.18);grade=np.abs(np.diff(rr[:,1])/np.diff(ss));report['route']={'length_m':float(ss[-1]),'samples':len(rr),'max_grade':float(grade.max()),'grid_support_max_error_m':float(route_error.max()),'elevated_corridor_count':len(w['elevated_corridors']),'districts':[d['name'] for d in w['districts']],'explore_starts':w['explore_starts']}
if grade.max()>.08 or route_error.max()>1e-7 or w['elevated_corridors']:report['failures'].append('Route grade/support contract failed')
for key in ['collision_file','furniture_file']:
 data=json.loads((WEB/w[key]).read_text());cs=data['colliders'];report[key]={'count':len(cs),'shapes':{shape:sum(c.get('shape')==shape for c in cs) for shape in ['box','capsule','circle']},'finite':all(np.isfinite(v) for c in cs for v in c.values() if isinstance(v,(float,int))),'public_identical':(WEB/w[key]).read_bytes()==(PUBLIC/w[key]).read_bytes()}
report['placement_count']=len(w['prop_instances']);report['missing_prop_glbs']=sorted(set(p['asset'] for p in w['prop_instances'] if not (PUBLIC/(p['asset']+'.glb')).exists()));report['passed']=not report['failures'] and not report['missing_prop_glbs'];(ROOT/'tests/highlands_geometry_qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
