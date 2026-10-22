"""Deterministic artistic Kerala district layout on the original OSM land masks.
No horizontal racing route edits. Original v7 geography is retained.
"""
from pathlib import Path
import json,math,bisect,random,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/course';rng=random.Random(822710)
spec=importlib.util.spec_from_file_location('geo',ROOT/'assets/course/audit_terrain_coverage.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
base=json.loads((OUT/'manifest.json').read_text());route=np.array(base['route_points_m']);route[:,2]=0;distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(route,axis=0),axis=1))]
def sample(s):
 i=min(len(route)-2,max(0,bisect.bisect_right(distance,s)-1));t=route[i+1]-route[i];t/=np.linalg.norm(t);p=route[i]+t*(s-distance[i]);return p,t,np.array([-t[1],t[0],0])
def dry(p):return geo.inside(p[:2],geo.land) and not any(geo.inside(p[:2],h) for h in geo.waters)
def wet(p):return any(geo.inside(p[:2],h) for h in geo.waters)
def road_clear(p):
 aa=route[:-1,:2];delta=route[1:,:2]-aa;f=np.clip(np.sum((p[:2]-aa)*delta,axis=1)/np.sum(delta*delta,axis=1),0,1);return math.sqrt(float(np.min(np.sum((p[:2]-aa-f[:,None]*delta)**2,axis=1))))
def basis(angle):return np.array([math.cos(angle),math.sin(angle),0]),np.array([-math.sin(angle),math.cos(angle),0])
def footprint(p,angle,hx,hy,step=4):
 u,v=basis(angle);pts=[p]
 for x in np.linspace(-hx,hx,max(2,math.ceil(hx*2/step)+1)):
  for y in [-hy,hy]:pts.append(p+u*x+v*y)
 for y in np.linspace(-hy,hy,max(2,math.ceil(hy*2/step)+1)):
  for x in [-hx,hx]:pts.append(p+u*x+v*y)
 return pts
reserved=[];new=[];errors=[]
def overlap(p,ang,hx,hy):
 u,v=basis(ang)
 for o in reserved:
  q=np.array(o['center']);a,b=basis(o['yaw']);delta=p-q
  if all(abs(np.dot(delta,axis))<(hx*abs(np.dot(u,axis))+hy*abs(np.dot(v,axis))+o['hx']*abs(np.dot(a,axis))+o['hy']*abs(np.dot(b,axis))+.7) for axis in [u,v,a,b]):return True
 return False
def reserve(p,angle,hx,hy,label):reserved.append({'center':p.tolist(),'yaw':angle,'hx':hx,'hy':hy,'asset':label})
def add(name,p,angle=0,scale=1,**extra):
 d={'asset':name,'location_m':[float(x) for x in p],'yaw_deg':math.degrees(angle),'scale':scale};d.update(extra);new.append(d);return d

def road_height(s):
 def sm(t):return t*t*(3-2*t)
 if s<2480 or s>3010:return .18
 if s<2630:return .18+9.82*sm((s-2480)/150)
 if s<=2860:return 10.
 return .18+9.82*(1-sm((s-2860)/150))

# A true straight metro alignment parallel to the straight commercial street.
# Single module train articulation is handled by the runtime; track remains smooth.
a,ta,na=sample(1900);b,tb,nb=sample(2225);direction=b-a;direction[2]=0;direction/=np.linalg.norm(direction);normal=np.array([-direction[1],direction[0],0]);start=a+normal*30;angle=math.atan2(direction[1],direction[0]);span_count=math.floor(np.linalg.norm(b-a)/25);metro_end=start+direction*(span_count*25)
for i in range(span_count):
 p=start+direction*(12.5+i*25);p[2]=13
 if not all(dry(q) for q in footprint(p,angle,1.5,1.6,2)):errors.append('metro pier not on dry land')
 add('MetroViaductSpan',p,angle,district='metro_market');reserve(p,angle,12.5,3,'metro_track')
station_dist=180.;station=start+direction*station_dist;station[2]=13;add('MetroStation',station,angle,district='metro_market');reserve(station+normal*3+direction*5,angle,49,8,'metro_station')
train_points=[]
for f in np.linspace(0,1,span_count+1):
 p=start*(1-f)+metro_end*f;train_points.append([float(p[0]),13.,float(-p[1])])
train_len=float(np.linalg.norm(metro_end-start));train_travel=1.5*(train_len-62)/12;train_fraction=np.clip((station_dist-31)/(train_len-62),0,1)
# Inverse smoothstep puts the first view near the station, not at an empty endpoint.
lo,hi=0.,1.
for _ in range(40):
 m=(lo+hi)/2
 if m*m*(3-2*m)<train_fraction:lo=m
 else:hi=m
train_phase=8+train_travel*(lo+hi)/2
transit=[{'id':'coast_metro_shuttle','type':'metro','asset':'coast_metro_train','points':train_points,'speed_mps':12,'loop':False,'dwell_seconds':8,'end_margin_m':31,'phase_seconds':train_phase,'description':'Fictional Kochi-inspired elevated three-car metro, not an actual Kappil service.'}]

# Find an actual lake edge near the waterfront racing sector. Keep terminal on dry
# land, but deliberately allow its gangway/pontoon to enter the lake.
terminal_candidates=[]
for lake_i,ring in enumerate(geo.waters[:2]):
 for p2,q2 in zip(ring,ring[1:]+ring[:1]):
  delta=q2-p2;length=np.linalg.norm(delta)
  if length<3:continue
  tangent=np.r_[delta/length,0];normal=np.array([-tangent[1],tangent[0],0]);c=np.r_[(p2+q2)/2,0]
  if not wet(c+normal):normal=-normal;tangent=-tangent
  if not wet(c+normal*3):continue
  distroad=road_clear(c)
  if not 38<distroad<145:continue
  near_i=int(np.argmin(np.sum((route[:,:2]-c[:2])**2,axis=1)));s=float(distance[near_i])
  if not 3000<s<3450:continue
  yaw=math.atan2(tangent[1],tangent[0]);root=c-normal*8
  if not all(dry(q) for q in footprint(root-normal*3,yaw,21,7.5,3)):continue
  # A 160 m shuttle, with its berth near the terminal and hull entirely in water.
  for sign in [1,-1]:
   path_start=c+normal*24;path_end=path_start+tangent*sign*160
   samples=[path_start*(1-f)+path_end*f for f in np.linspace(0,1,33)]
   if all(wet(q+normal*off) for q in samples for off in [-5,0,5]):
    terminal_candidates.append((abs(s-3175)+distroad*.3,root,c,tangent,normal,yaw,s,path_start,path_end,lake_i));break
if not terminal_candidates:raise RuntimeError('No dry terminal + navigable lake ferry corridor found; do not place on arbitrary water.')
_,terminal,shore,shore_t,water_n,shore_yaw,terminal_s,ferry_a,ferry_b,lake_i=min(terminal_candidates,key=lambda x:x[0]);add('WaterTransitTerminal',terminal,shore_yaw,district='backwater_quarter');reserve(terminal-water_n*2,shore_yaw,25,11,'terminal_forecourt')
ferry_points=[[float(p[0]),.015,float(-p[1])] for p in [ferry_a,ferry_b]]
transit.append({'id':'backwater_ferry_shuttle','type':'ferry','asset':'water_transit_ferry','points':ferry_points,'speed_mps':4.3,'loop':False,'dwell_seconds':10,'end_margin_m':4,'phase_seconds':3,'description':'Fictional low-wake water-transit shuttle, not an official route or navigational chart.'})
# Promenade follows the shoreline tangent only where its full paving footprint is dry.
for d in [-80,-60,-40,40,60,80]:
 p=shore+shore_t*d-water_n*5
 if all(dry(q) for q in footprint(p,shore_yaw,10,3.5,3)) and not overlap(p,shore_yaw,10,3.5):
  add('PromenadeSegment',p,shore_yaw,district='backwater_quarter');reserve(p,shore_yaw,10,3.5,'promenade')
# Optional original houseboat, entirely water-supported and outside the ferry capsule.
if (ROOT/'assets/infrastructure/backwater/KeralaHouseboat.blend').exists():
 for along in [65,90,40,115]:
  for offshore in [23,30,40]:
   hp=ferry_a+(ferry_b-ferry_a)/160*along+water_n*offshore;hp[2]=.015
   if all(wet(q) for q in footprint(hp,shore_yaw,9.1,2.7,2)):
    add('KeralaHouseboat',hp,shore_yaw,district='backwater_quarter');break
  else:continue
  break

# Side lanes create actual block edges; they are not racing on a pedestrian promenade.
for s in [1880,2010,2170,3270,3460,3660,3860,4110]:
 p,t,n=sample(s)
 for side in [-1,1]:
  direction=n*side;yaw=math.atan2(direction[1],direction[0])
  for k in range(3):
   q=p+direction*(4.6+12.5+k*25)
   if all(dry(v) for v in footprint(q,yaw,12.5,5,4)) and not overlap(q,yaw,12.5,5):
    add('SideStreetSegment',q,yaw,district='metro_market' if s<2300 else 'backwater_quarter');reserve(q,yaw,12.5,5,'side_street')
# Terminal access lane toward road. Two-piece straight connector, only on dry land.
p,t,n=sample(terminal_s);toward=(terminal-water_n*13)-p;toward[2]=0;length=np.linalg.norm(toward);direction=toward/length;yaw=math.atan2(direction[1],direction[0])
for k in range(max(0,int((length-6)/25))):
 q=p+direction*(6+12.5+k*25)
 if all(dry(v) for v in footprint(q,yaw,12.5,5,3)) and not overlap(q,yaw,12.5,5):
  add('SideStreetSegment',q,yaw,district='backwater_quarter');reserve(q,yaw,12.5,5,'terminal_access')

urban=json.loads((ROOT/'assets/infrastructure/urban/urban_assets_manifest.json').read_text());dims={a['name']:a['dimensions_blender_xyz_m'] for a in urban['assets']}
palettes=[('#d5d0b8','#855344'),('#d0b376','#596f63'),('#b7cad0','#435867'),('#ddd8c8','#7a6c57')]
def place_building(name,s,side,offset,scale=1,district='metro_market'):
 p,t,n=sample(s);yaw=math.atan2(t[1],t[0])+(math.pi if side<0 else 0);q=p+n*side*offset;hx,hy=[dims[name][i]*scale/2 for i in [0,1]]
 probes=footprint(q,yaw,hx,hy,3)
 if not all(dry(v) and road_clear(v)>5.5 for v in probes) or overlap(q,yaw,hx,hy):return False
 palette=palettes[(int(s//90)+(0 if side>0 else 2))%len(palettes)]
 add(name,q,yaw,scale,district=district,facade_color=palette[0],accent_color=palette[1]);reserve(q,yaw,hx,hy,name);return True
# Coastal villages retain open beach views, then tightly spaced commercial blocks.
for s in range(240,1750,110):
 for side in [-1,1]:place_building('KeralaShopRow_B' if s%220==20 else 'KeralaTeaStall',s,side,12.5, .85,district='coastal_villages')
for s in range(1830,2250,18):
 for side in [-1,1]:
  name='KeralaShopRow_A' if (s//18+side)%3 else 'KeralaShopRow_B';place_building(name,s+rng.uniform(-1.0,1.0),side,13.8+rng.uniform(0,2.8),rng.uniform(.92,1.07))
for s in range(1850,2240,35):
 for side in [-1,1]:place_building('KeralaApartment_A' if (s//35+side)%3 else 'KeralaOffice_A',s,side,51+rng.uniform(0,13),rng.uniform(.8,1.18))
# The narrow coastal flyover leg supports smaller roadside shops, not invented land fill.
for s in range(2420,3050,38):
 for side in [-1,1]:
  name='KeralaShopRow_B' if (s//38+side)%3 else 'KeralaTeaStall';place_building(name,s,side,13.0,.82,district='skyline_flyover')
# Waterfront/mid-rise district with a varied, two-row street wall and side lanes.
for s in range(3080,4320,24):
 for side in [-1,1]:
  name=['KeralaShopRow_A','KeralaShopRow_B','KeralaTeaStall'][(s//24+side)%5%3];place_building(name,s+rng.uniform(-1.5,1.5),side,14.5+rng.uniform(0,4),rng.uniform(.86,1.08),district='backwater_quarter')
for s in range(3120,4300,48):
 for side in [-1,1]:place_building('KeralaApartment_A' if (s//48+side)%3 else 'KeralaOffice_A',s,side,43+rng.uniform(0,22),rng.uniform(.84,1.18),district='backwater_quarter')
# Deliberate street rhythm, not random scatter: lamps and palms between facades.
for s in range(1815,4350,42):
 p,t,n=sample(s)
 for side in [-1,1]:
  elevated=2480<=s<=3010;offset=4.70 if elevated else 5.9;q=p+n*side*offset;q[2]=road_height(s) if elevated else 0
  if elevated or dry(q):add('Streetlight',q,math.atan2(t[1],t[0])+(math.pi if side<0 else 0),district='street_furniture')
for s in range(1845,4350,62):
 p,t,n=sample(s)
 for side in [-1,1]:
  if 2460<s<3030:continue
  q=p+n*side*7.0
  if dry(q) and not overlap(q,0,1,1):add('CoconutPalm_A' if side>0 else 'CoconutPalm_B',q,rng.uniform(0,math.tau),.8,district='street_landscaping')

# Put the cantilever over water, not merely near the terminal. Native front is -Y.
net_candidates=[]
for ring in geo.waters[:2]:
 for aa,bb in zip(ring,ring[1:]+ring[:1]):
  tt=bb-aa;length=np.linalg.norm(tt)
  if length<1:continue
  tt/=length;nn=np.array([-tt[1],tt[0]])
  if not wet(np.r_[(aa+bb)/2+nn,0]):nn=-nn;tt=-tt
  for f in np.linspace(.1,.9,max(2,int(length/5))):
   pp=aa*(1-f)+bb*f-nn*.2;dd=np.linalg.norm(pp-terminal[:2]);yaw=math.atan2(tt[1],tt[0])+math.pi
   if not 40<dd<150:continue
   if not all(dry(np.r_[pp-tt*x*.8-nn*y*.8,0]) for x in [-2.6,0,2.6] for y in [2.3,5.6,8.8]):continue
   if not all(wet(np.r_[pp-tt*x*.8-nn*y*.8,0]) for x in [-7,-3.5,0,3.5,7] for y in [-9,-7,-5,-3,-.6]):continue
   if overlap(np.r_[pp-nn*4.48,0],yaw,2.3,2.8):continue
   net_candidates.append((abs(dd-65),np.r_[pp,0],yaw))
if net_candidates:
 _,net_p,net_yaw=min(net_candidates,key=lambda x:x[0]);add('ChineseFishingNet',net_p,net_yaw,.8,district='backwater_quarter')
 # Placed after all building reservations; small existing grass may remain below its raised timber platform.

world={'version':'v8-kerala-infrastructure','fictional_geography_notice':'OSM-derived Kappil road/coast with an artistic Kochi-inspired infrastructure remix. Metro, transit route, buildings, promenade and flyover are fictional, not a geographic/survey claim. Marine Drive itself is pedestrian-only; this race road runs alongside an inspired promenade, not on it.','districts':[{'name':'Coastal Villages','start_s':0,'end_s':1800,'description':'Coconut coastline, fishing houses and small roadside shops.'},{'name':'Metro Market','start_s':1800,'end_s':2350,'description':'Dense commercial blocks, mid-rise homes and elevated metro station.'},{'name':'Skyline Flyover','start_s':2350,'end_s':3050,'description':'Smooth raised racing roadway above a narrow coastal neighborhood.'},{'name':'Backwater Quarter','start_s':3050,'end_s':3950,'description':'Water-transit terminal, waterfront promenade, fishing nets and varied urban blocks.'},{'name':'Harbour Avenue','start_s':3950,'end_s':float(distance[-1]),'description':'Palm-lined shop streets and mid-rise residential blocks.'}],'transit_routes':transit,'collision_file':'infrastructure_colliders.json','terminal_route_s':terminal_s,'terminal_lake_index':lake_i,'landscape_policy':'Building footprints and metro pier foundations tested against original OSM land minus water. Docks, submerged ferry hull and fishing-net booms intentionally extend over water.','new_prop_count':len(new)}
profile={'base_height_m':.18,'deck_height_m':10.,'curve':'smoothstep t*t*(3-2*t)','segments':[{'startS':2480,'endS':2630,'fromY':.18,'toY':10.},{'startS':2630,'endS':2860,'fromY':10.,'toY':10.},{'startS':2860,'endS':3010,'fromY':10.,'toY':.18}]}
corridors=[{'id':'coastal_flyover_01','startS':2480,'endS':3010,'halfWidth':4.42,'railHeight':1.10,'railThickness':.30,'roadHalfWidth':3.6,'shoulderHalfWidth':4.6,'deckHalfWidth':4.8,'deckThickness':.55,'deckTopBelowRoad':.10}]
result={'new_prop_instances':new,'reserved_footprints':reserved,'world':world,'elevation_profile':profile,'elevated_corridors':corridors,'validation_errors':errors,'source_planar_route_points':route.tolist()}
if errors:raise RuntimeError(errors)
(OUT/'v8_world_layout.json').write_text(json.dumps(result,indent=2))
from collections import Counter
print('V8_LAYOUT',len(new),dict(Counter(p['asset'] for p in new)),'terminal_s',terminal_s,'metro_length',train_len)
