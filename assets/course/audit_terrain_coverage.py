import json,struct,math,bisect,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def glb_triangles(path):
 data=Path(path).read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);offset=20+length;blen,btype=struct.unpack_from('<II',data,offset);binary=data[offset+8:offset+8+blen]
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];size={'VEC3':3,'SCALAR':1,'VEC2':2,'VEC4':4}[a['type']];item=np.dtype(dtype).itemsize;stride=v.get('byteStride',size*item)
  return np.ndarray((a['count'],size),dtype=dtype,buffer=binary,offset=start,strides=(stride,item)).copy()
 out=[]
 for me in doc['meshes']:
  for p in me['primitives']:
   vs=acc(p['attributes']['POSITION']);ii=acc(p['indices']).reshape(-1,3);out.append(vs[ii])
 return np.concatenate(out)
def hits(points,tris):
 # Inputs in Three basis; horizontal X/Z test.
 tri=tris[:,:,[0,2]];a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;den=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=np.abs(den)>1e-10;den=np.where(valid,den,1)
 result=[]
 for point in points:
  q=np.array([point[0],point[2]])-a;u=(q[:,0]*c[:,1]-q[:,1]*c[:,0])/den;v=(b[:,0]*q[:,1]-b[:,1]*q[:,0])/den;result.append(bool(np.any(valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9))))
 return result
raw=json.loads((ROOT/'references/route/kappil_route_local_meters.json').read_text());lon0,lat0=raw['origin_wgs84_lon_lat'];R=6371000
project=lambda p:np.array([(p[0]-lon0)*math.pi/180*R*math.cos(lat0*math.pi/180),(p[1]-lat0)*math.pi/180*R])
features=json.loads((ROOT/'references/route/kappil_osm_environment.geojson').read_text())['features'];coast=[]
for f in features:
 if f['properties'].get('natural')=='coastline':coast.extend(project(p) for p in f['geometry']['coordinates'])
coast.sort(key=lambda p:p[1])
if coast[-1][1]<6000:
 v=coast[-1]-coast[-2];v=v/np.linalg.norm(v);coast.append(coast[-1]+v*((6200-coast[-1][1])/v[1]))
if coast[0][1]>-500:
 v=coast[1]-coast[0];v=v/np.linalg.norm(v);coast.insert(0,coast[0]-v*((coast[0][1]+500)/v[1]))
land=coast+[np.array([4500,coast[-1][1]]),np.array([4500,coast[0][1]])]
waters=[[project(p) for p in f['geometry']['coordinates'][0][:-1]] for f in features if f['properties'].get('natural')=='water' and f['geometry']['type']=='Polygon']
def inside(point,poly):
 x,y=point;result=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
 return result
def audit_corridor(label):
 runtime=json.loads((ROOT/'assets/web/course_runtime.json').read_text());route=np.array(runtime['route_points']);dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route,axis=0),axis=1))]
 def sample(s):
  i=min(len(route)-2,max(0,bisect.bisect_right(dist,s)-1));a,b=route[i:i+2];f=(s-dist[i])/(dist[i+1]-dist[i]);p=a*(1-f)+b*f;t=(b-a)/np.linalg.norm(b-a);n=np.array([-t[2],0,t[0]]);return p,n
 records=[]
 for s in range(1800,4501,25):
  p,n=sample(s)
  for lateral in (-100,-50,-25,-12,-7,7,12,25,50,100):
   q=p+n*lateral;xy=(q[0],-q[2]);expected=inside(xy,land) and not any(inside(xy,w) for w in waters)
   records.append({'s':s,'lateral':lateral,'point':q.tolist(),'expected_dry_land':expected})
 terrain=glb_triangles(ROOT/'assets/web/Course_Terrain.glb');water=glb_triangles(ROOT/'assets/web/Course_Water.glb');th=hits([r['point'] for r in records],terrain);wh=hits([r['point'] for r in records],water)
 for r,t,w in zip(records,th,wh):r.update(terrain_hit=t,water_hit=w)
 dry=[r for r in records if r['expected_dry_land']];missing=[r for r in dry if not r['terrain_hit'] and not r['water_hit']]
 report={'samples':len(records),'expected_dry_land_samples':len(dry),'missing_ground_samples':len(missing),'dry_terrain_coverage_percent':100*sum(r['terrain_hit'] for r in dry)/len(dry),'around_2200':[r for r in records if r['s']==2200],'missing_examples':missing[:30],'records':records}
 file=ROOT/'assets/course'/('terrain_coverage_'+label+'.json');file.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('records','missing_examples')},indent=2));print('REPORT',file)
 return report

if __name__=="__main__":audit_corridor(sys.argv[1] if len(sys.argv)>1 else "baseline")
