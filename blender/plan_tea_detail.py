"""Compact, deterministic near-road tea centerlines; all terrain/physics files are read-only."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/foliage_detail';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets';w=json.loads((WEB/'course_runtime_highlands.json').read_text());tea=json.loads((ROOT/'assets/highlands/tea_rows.json').read_text());grid=w['terrain_grid'];nx,nz=grid['count'];dx,dz=grid['step'];x0,z0=grid['origin'];H=np.array(grid['heights']).reshape(nz,nx);route=np.array(w['route_points']);tree=cKDTree(route[:,[0,2]])
def height(x,z):
 u=(x-x0)/dx;v=(z-z0)/dz;i=max(0,min(nx-2,int(math.floor(u))));j=max(0,min(nz-2,int(math.floor(v))));u=max(0,min(1,u-i));v=max(0,min(1,v-j));a,b,c,d=H[j,i],H[j,i+1],H[j+1,i],H[j+1,i+1];return a+(b-a)*u+(d-b)*v if v<=u else a+(d-c)*u+(c-a)*v
runs=[]
for rowid,row in enumerate(tea['paths']):
 p=np.array(row['points']);xz=np.c_[p[:,0],-p[:,1]];ss=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xz,axis=0),axis=1))];d,_=tree.query((xz[:-1]+xz[1:])/2);keep=d<=110;i=0;runid=0
 while i<len(keep):
  if not keep[i]:i+=1;continue
  a=i
  while i<len(keep) and keep[i]:i+=1
  b=i;coords=xz[a:b+1];points=[[round(float(x),4),round(float(height(x,z)),5),round(float(z),4)]for x,z in coords]
  runs.append({'id':f'row-{rowid:03d}-{runid}','row_id':rowid,'points':points,'distances_m':[round(float(v),6)for v in ss[a:b+1]],'bounds_xz':[round(float(coords[:,0].min()),4),round(float(coords[:,1].min()),4),round(float(coords[:,0].max()),4),round(float(coords[:,1].max()),4)]});runid+=1
manifest={'version':1,'asset':'TeaLeafCluster','coordinate_system':'Three X east/Y up/Z south, metres. Local asset X follows row; local +Z is row right.','root_y_semantics':'Each instance root is sampled on the exact terrain triangle at its final laterally offset X/Z. It is NOT placed on top of the coarse hedge. Centerline point Y is terrain height.','source':'Original authored tea rows in assets/highlands/tea_rows.json; clipped only for detail, not changing any existing mesh.','source_sha256':hashlib.sha256((ROOT/'assets/highlands/tea_rows.json').read_bytes()).hexdigest(),'near_route_clip_m':110,'route_reference_xz':[[round(float(p[0]),4),round(float(p[2]),4)] for p in route[::4]],'fade_route_margin_m':12,'scatter':{'pitch_m':.70,'lateral_offsets_m':[-.52,.52],'band_stagger_m':.35,'lateral_jitter_m':.08,'yaw_jitter_rad':.18,'scale_range':[.90,1.08],'seed':102207},'recommended':{'high':{'query_radius_m':85,'max_instances':1250,'triangle_budget':200000},'balanced':{'query_radius_m':50,'max_instances':500,'triangle_budget':80000},'coarse_fade_note':'Keep coarse hedge unless a complete dense near coverage region is admitted. Use coverage_radius_m returned by the reference selector, with a feather/dither transition inside it; outside stays unchanged. Near/far must not both disappear at the instance cap.'},'runs':runs,'run_count':len(runs),'point_count':sum(len(r['points'])for r in runs),'total_detail_centerline_length_m':sum(r['distances_m'][-1]-r['distances_m'][0]for r in runs)}
for out in [OUT,WEB,PUBLIC]:(out/'tea_detail_rows.json').write_text(json.dumps(manifest,separators=(',',':')))
print(json.dumps({k:manifest[k]for k in ['run_count','point_count','total_detail_centerline_length_m']},indent=2));print('bytes',(WEB/'tea_detail_rows.json').stat().st_size)
