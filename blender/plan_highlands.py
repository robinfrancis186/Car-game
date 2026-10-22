"""Original artistic Highland Run: no OSM relocation, no external geometry.
Generate a deterministic drivable route, exact terrain height grid and district plan.
"""
from pathlib import Path
import json,math,bisect
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/highlands';OUT.mkdir(parents=True,exist_ok=True)
raw=[]
def line(a,b,step=2):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);n=max(1,math.ceil(np.linalg.norm(b-a)/step));raw.extend(a+(b-a)*i/n for i in range(n))
def arc(c,r,a,b,step=2):
 n=max(2,math.ceil(abs(b-a)*r/step));raw.extend(np.array(c)+r*np.array([math.cos(a+(b-a)*i/n),math.sin(a+(b-a)*i/n)]) for i in range(n))
line((0,0),(800,0));arc((800,100),100,-math.pi/2,math.pi/2);line((800,200),(300,200));arc((300,265),65,-math.pi/2,-3*math.pi/2);line((300,330),(1000,330));arc((1000,395),65,-math.pi/2,math.pi/2);line((1000,460),(450,460));arc((450,540),80,-math.pi/2,-math.pi);line((370,540),(370,900));raw.append(np.array([370,900]));raw=np.array(raw)
d0=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];ss=np.r_[np.arange(0,d0[-1],3),d0[-1]];route=np.c_[np.interp(ss,d0,raw[:,0]),np.interp(ss,d0,raw[:,1])];distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route,axis=0),axis=1))];length=float(distance[-1]);sm=lambda t:np.clip(t,0,1)**2*(3-2*np.clip(t,0,1));design_height=lambda s:100*sm((np.asarray(s)-800)/(length-900))
# Smooth wide hill mass fitted around the intended gradual road climb, not a flat plane.
anchors=np.unique(np.r_[np.arange(0,len(route),32),len(route)-1]);rbf=RBFInterpolator(route[anchors],design_height(distance[anchors]),kernel='thin_plate_spline',smoothing=3)
xmin,xmax,ymin,ymax,step=-800,2000,-600,1800,8;xs=np.arange(xmin,xmax+step,step,dtype=float);zs=np.arange(-ymax,-ymin+step,step,dtype=float);X,Z=np.meshgrid(xs,zs);Y=-Z;flat=np.c_[X.ravel(),Y.ravel()]
base=rbf(flat).reshape(X.shape);base=np.clip(base,0,150);base+=10*np.sin(X/195)*np.cos(Y/220)*sm((Y-30)/220)
base+=72*np.exp(-((X-1120)/370)**2-((Y-1160)/430)**2)+45*np.exp(-((X+50)/410)**2-((Y-1240)/380)**2)
base=np.maximum(0,base)
# Exact nearest segment in a small KD candidate set; retain s for corridor grading.
tree=cKDTree(route);_,near=tree.query(flat,k=4);bestd=np.full(len(flat),np.inf);nears=np.zeros(len(flat));laterals=np.zeros(len(flat));seg=route[1:]-route[:-1];seglen=np.linalg.norm(seg,axis=1)
for shift in [-1,0]:
 for k in range(4):
  ii=np.clip(near[:,k]+shift,0,len(route)-2);aa=route[ii];dd=seg[ii];f=np.clip(np.sum((flat-aa)*dd,axis=1)/np.sum(dd*dd,axis=1),0,1);delta=flat-aa-f[:,None]*dd;d=np.sum(delta*delta,axis=1);mask=d<bestd;bestd[mask]=d[mask];nears[mask]=distance[ii[mask]]+f[mask]*seglen[ii[mask]];laterals[mask]=(-dd[:,1]*delta[:,0]+dd[:,0]*delta[:,1])[mask]/seglen[ii[mask]]
D=np.sqrt(bestd).reshape(X.shape);S=nears.reshape(X.shape);L=laterals.reshape(X.shape)
# Flat crossfall across both highway carriageways and broad merge, then shoulders.
cd=np.where(S<825,np.maximum.reduce([np.zeros_like(L),L-10,-L-24]),np.maximum(D-18,0));weight=1-sm(cd/28);height=base*(1-weight)+design_height(S)*weight
# Summit landmark foundation is a real terrain plateau, clear of the racing road.
landmark={'asset':'BirdRockLookout','location_blender_m':[490.,850.,100.],'yaw_deg':180.,'scale':1.,'pad_half_size_m':[39,39],'description':'Original reclining-bird rock viewpoint inspired by user reference; not an exact sculpture replica.'}
q=np.maximum(np.abs(X-490)-39,np.abs(Y-850)-39);pad=1-sm(np.maximum(q,0)/24);height=height*(1-pad)+100*pad
# Author a generous perimeter that gently returns to level horizon ground.
edge=np.minimum.reduce([X-xmin,xmax-X,Y-ymin,ymax-Y]);height*=sm(edge/230);height=np.round(np.maximum(0,height),4)
# Canonical world-grid rows run +Three Z (native -Y), exact SW-NE triangulation.
grid={'origin':[xmin,-ymax],'step':[step,step],'count':[len(xs),len(zs)],'heights':height.ravel().tolist(),'diagonal':'sw-ne','outside_policy':'Clamp edge for a short grace, then recover to route; map has at least600m route margin.','units':'meters'}
def sample_height(x,y):
 u=(x-xmin)/step;v=(-y+ymax)/step;i=np.clip(np.floor(u).astype(int),0,len(xs)-2);j=np.clip(np.floor(v).astype(int),0,len(zs)-2);u=np.clip(u-i,0,1);v=np.clip(v-j,0,1);h00=height[j,i];h10=height[j,i+1];h01=height[j+1,i];h11=height[j+1,i+1];return np.where(v<=u,h00+(h10-h00)*u+(h11-h10)*v,h00+(h11-h01)*u+(h01-h00)*v)
road_y=sample_height(route[:,0],route[:,1])+.18;route3=np.c_[route,road_y];grade=np.diff(road_y)/np.diff(distance);maxgrade=float(np.max(np.abs(grade)))
if maxgrade>.08:raise RuntimeError(f'Route grade {maxgrade:.4f} exceeds8%')
sections=[{'startS':0,'endS':760,'halfWidth':5.25,'shoulderHalfWidth':6.5,'shoulderDrop':.06,'driveableStrips':[{'centerOffset':0,'halfWidth':5.25,'shoulderHalfWidth':6.5},{'centerOffset':14,'halfWidth':5.25,'shoulderHalfWidth':6.5}],'label':'Divided Coast Highway'},{'startS':760,'endS':820,'halfWidth':12.25,'shoulderHalfWidth':13.25,'shoulderDrop':.06,'driveableStrips':[{'centerOffset':7,'halfWidth':12.25,'shoulderHalfWidth':13.25}],'label':'Tea Hills Junction'},{'startS':820,'endS':length,'halfWidth':3.6,'shoulderHalfWidth':4.6,'shoulderDrop':.06,'driveableStrips':[{'centerOffset':0,'halfWidth':3.6,'shoulderHalfWidth':4.6}],'label':'Tea Ridge Road'}]
result={'name':'Highland Run','id':'highlands','description':'A fictional Kerala-inspired highway-to-tea-estate hill climb; not a surveyed real road.','route_points_blender_m':route3.tolist(),'horizontal_route_distances_m':distance.tolist(),'route_length_m':length,'road_sections':sections,'terrain_grid':grid,'landmark_plan':landmark,'districts':[{'name':'Divided Highway','start_s':0,'end_s':820,'description':'Six lanes, planted median, palms and black-yellow edge treatments inspired by the supplied NH66 reference.'},{'name':'Lower Tea Bends','start_s':820,'end_s':1850,'description':'A genuine winding hillside road between layered tea planting.'},{'name':'Estate Switchbacks','start_s':1850,'end_s':3200,'description':'Broad switchbacks climbing through terraced green estates.'},{'name':'Bird Rock Ridge','start_s':3200,'end_s':length,'description':'Summit viewpoint and original reclining-bird rock landmark.'}],'event_slices':{'coast-sprint':{'startS':850,'endS':2450},'hot-pursuit':{'startS':0,'endS':min(3200,length)},'time-attack':{'startS':0,'endS':length}},'garage_s':90,'max_grade':maxgrade,'terrain_height_range_m':[float(height.min()),float(height.max())],'reference_files':['BB3D0705-81DD-48CA-A549-B1148590B3D6.png','AEF7FA9C-4D32-4B51-8698-96792F6486D9.png','504A8779-377F-42BD-837C-8A65D5F843CE.png'],'provenance':'Original procedural geometry and artistic route. No third-party mesh/photo texture data. User-supplied photos are visual references only; no geographic surveying claim.'}
(OUT/'highlands_plan.json').write_text(json.dumps(result,separators=(',',':')));np.savez_compressed(OUT/'terrain_cache.npz',x=X,y=Y,h=height,near_s=S,distance_to_route=D,lateral=L)
(OUT/'terrain_grid.json').write_text(json.dumps(grid,separators=(',',':')))
print(json.dumps({'length_m':length,'route_points':len(route3),'max_grade':maxgrade,'grid':grid['count'],'terrain_vertices':height.size,'terrain_triangles':(height.shape[0]-1)*(height.shape[1]-1)*2,'height_range':result['terrain_height_range_m'],'road_height_range':[float(road_y.min()),float(road_y.max())]},indent=2))
