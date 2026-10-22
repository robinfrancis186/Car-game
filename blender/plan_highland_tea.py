"""Extract original contour-following planted rows from the actual triangle terrain."""
from pathlib import Path
import json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/highlands';a=np.load(OUT/'terrain_cache.npz');X,Y,H,D=[a[n] for n in ['x','y','h','distance_to_route']];ny,nx=H.shape
plots=[(550,110,255,72),(630,265,320,48),(650,395,310,48),(690,610,260,130),(900,860,290,190),(100,740,180,250),(620,1130,330,110)]
ids=np.arange(nx*ny).reshape(ny,nx);i00=ids[:-1,:-1].ravel();i10=ids[:-1,1:].ravel();i01=ids[1:,:-1].ravel();i11=ids[1:,1:].ravel();indices=np.concatenate([np.c_[i00,i10,i11],np.c_[i00,i11,i01]]);v=np.c_[X.ravel(),Y.ravel(),H.ravel()];tr=v[indices];center=tr.mean(axis=1);mask=np.zeros(len(tr),bool);plotid=np.zeros(len(tr),int)
for k,(x,y,rx,ry) in enumerate(plots):
 m=((center[:,0]-x)/rx)**2+((center[:,1]-y)/ry)**2<1;plotid[m]=k;mask|=m
mask&=np.min(D.ravel()[indices],axis=1)>17;mask&=np.maximum(abs(center[:,0]-490),abs(center[:,1]-850))>58;tr=tr[mask];plotid=plotid[mask];lo=tr[:,:,2].min(axis=1);hi=tr[:,:,2].max(axis=1);paths=[];total_length=0
all_triangles=tr.copy();intervals=[.38,1.4,1.4,.60,.71,.57,.48]
for plot_index,interval in enumerate(intervals):
 tr=all_triangles[plotid==plot_index];lo=tr[:,:,2].min(axis=1);hi=tr[:,:,2].max(axis=1)
 for level in np.arange(.17,165,interval):
  sel=(lo<level)&(hi>level);tt=tr[sel]
  if not len(tt):continue
  crossings=[]
  for k in range(3):
   aa=tt[:,k];bb=tt[:,(k+1)%3];m=(aa[:,2]<level)!=(bb[:,2]<level);f=(level-aa[m,2])/(bb[m,2]-aa[m,2]);pp=aa[m,:2]+f[:,None]*(bb[m,:2]-aa[m,:2]);crossings.extend((int(i),p) for i,p in zip(np.flatnonzero(m),pp))
  bytri={}
  for i,p in crossings:bytri.setdefault(i,[]).append(p)
  edges=[];points={};adj={}
  for pp in bytri.values():
   if len(pp)!=2:continue
   keys=[tuple(np.round(p,4)) for p in pp]
   if keys[0]==keys[1]:continue
   ei=len(edges);edges.append(keys)
   for key,p in zip(keys,pp):points[key]=p;adj.setdefault(key,[]).append(ei)
  used=set()
  starts=[k for k,ee in adj.items() if len(ee)==1]+list(adj)
  for start in starts:
   if all(e in used for e in adj[start]):continue
   current=start;chain=[points[start]]
   while True:
    remaining=[e for e in adj[current] if e not in used]
    if not remaining:break
    e=remaining[0];used.add(e);u,w=edges[e];current=w if current==u else u;chain.append(points[current])
    if current==start:break
   chain=np.array(chain)
   if len(chain)<3:continue
   ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(chain,axis=0),axis=1))]
   if ds[-1]<17:continue
   ss=np.r_[np.arange(0,ds[-1],7.5),ds[-1]];q=np.c_[np.interp(ss,ds,chain[:,0]),np.interp(ss,ds,chain[:,1])]
   if len(q)>4:q[1:-1]=(q[:-2]+2*q[1:-1]+q[2:])/4
   paths.append({'contour_height_m':round(float(level),3),'points':np.round(q,4).tolist(),'shade':len(paths)%3});total_length+=float(ds[-1])
result={'source':'Actual terrain triangular contour extraction, then light smoothing; every hedge base is sampled back onto exact terrain.','row_cross_section_width_m':2.3,'row_height_m':1.12,'contour_intervals_by_plot_m':intervals,'plots':plots,'paths':paths,'total_row_length_m':total_length,'estimated_triangles':sum((len(p['points'])-1)*14+10 for p in paths)}
(OUT/'tea_rows.json').write_text(json.dumps(result,separators=(',',':')));print('TEA_ROWS',len(paths),'length',total_length,'tris',result['estimated_triangles'])
