"""Checks geographic ground coverage, exact lake holes and append-only vegetation."""
import json,math,hashlib,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/course'
spec=importlib.util.spec_from_file_location('coverage',OUT/'audit_terrain_coverage.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
terrain=a.glb_triangles(ROOT/'assets/web/Course_Terrain.glb');ground=terrain[np.all(np.abs(terrain[:,:,1]+.04)<1e-5,axis=1)]
# Test ±20cm and ±1m perpendicular to every lake-edge midpoint.
# Cardinal offsets parallel to an edge can lie sub-millimeter from its boundary,
# below float32 glTF accuracy at kilometer coordinates; normal offsets avoid that.
boundary=[]
for ring in a.waters:
 for p,q in zip(ring,ring[1:]+ring[:1]):
  center=(p+q)/2;t=q-p;length=np.linalg.norm(t)
  if length<1e-6:continue
  normal=np.array([-t[1],t[0]])/length
  for distance in [.2,-.2,1.,-1.]:
   xy=center+normal*distance;wet=any(a.inside(xy,h) for h in a.waters);dry=a.inside(xy,a.land) and not wet
   if wet or dry:boundary.append({'p':[xy[0],10,-xy[1]],'wet':wet,'dry':dry})
hit=a.hits([r['p'] for r in boundary],ground)
lake_fail=sum(r['wet'] and h for r,h in zip(boundary,hit));dry_fail=sum(r['dry'] and not h for r,h in zip(boundary,hit))
# Ocean shoreline coverage on both sides of the original coastline constraints.
shore=[]
for p,q in zip(a.coast,a.coast[1:]):
 center=(p+q)/2;t=q-p;length=np.linalg.norm(t)
 if length<1e-6:continue
 normal=np.array([-t[1],t[0]])/length
 for distance in [.2,-.2,1.,-1.]:
  xy=center+normal*distance;inland=a.inside(xy,a.land);dry=inland and not any(a.inside(xy,h) for h in a.waters)
  shore.append({'p':[xy[0],10,-xy[1]],'dry':dry,'sea':not inland})
shore_ground=a.hits([r['p'] for r in shore],ground);shore_water=a.hits([r['p'] for r in shore],a.glb_triangles(ROOT/'assets/web/Course_Water.glb'))
shore_ground_fail=sum(r['dry'] and not h for r,h in zip(shore,shore_ground));shore_water_fail=sum(r['sea'] and not h for r,h in zip(shore,shore_water))
# Verify every added grass/palm full conservative root footprint, with nearest-road clearance.
before=json.loads((OUT/'terrain_repair_manifest_before.json').read_text());after=json.loads((OUT/'manifest.json').read_text());new=after['prop_instances'][len(before['prop_instances']):];route=np.array(after['route_points_m']);va=route[:-1,:2];delta=route[1:,:2]-va;den=np.sum(delta*delta,axis=1);dry_bad=[];road_bad=[];centers=[];minimum={'grass':float('inf'),'palm':float('inf')}
for idx,r in enumerate(new):
 p=np.array(r['location_m'][:2]);grass=r['asset']=='TropicalGrass';radius=(.75 if grass else 1.6)*r['scale'];ring=[p]+[p+radius*np.array([math.cos(i*math.pi/4),math.sin(i*math.pi/4)]) for i in range(8)]
 if not all(a.inside(q,a.land) and not any(a.inside(q,h) for h in a.waters) for q in ring):dry_bad.append(idx)
 t=np.clip(np.sum((p-va)*delta,axis=1)/den,0,1);distance=float(np.sqrt(np.min(np.sum((p-va-t[:,None]*delta)**2,axis=1))));minimum['grass' if grass else 'palm']=min(minimum['grass' if grass else 'palm'],distance)
 if distance<(4.95+.75*r['scale'] if grass else 9.2)-1e-4:road_bad.append(idx)
 centers.append([p[0],10,-p[1]])
center_hits=a.hits(centers,terrain)
oldruntime=json.loads((OUT/'terrain_repair_runtime_before.json').read_text());runtime=json.loads((ROOT/'assets/web/course_runtime.json').read_text())
baseline=json.loads((OUT/'terrain_repair_preservation_baseline.json').read_text())['sha256'];changed=[name for name,sha in baseline.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha];unexpected=[n for n in changed if not n.endswith('/Course_Terrain.glb')]
report={'terrain_triangles':len(terrain),'ground_triangles':len(ground),'lake_boundary_samples':len(boundary),'lake_interior_samples':sum(r['wet'] for r in boundary),'dry_boundary_samples':sum(r['dry'] for r in boundary),'ground_intrusions_in_lakes':int(lake_fail),'missing_dry_boundary_ground':int(dry_fail),'coast_boundary_samples':len(shore),'shore_dry_samples':sum(r['dry'] for r in shore),'shore_sea_samples':sum(r['sea'] for r in shore),'missing_dry_shore_ground':int(shore_ground_fail),'missing_sea_surface':int(shore_water_fail),'new_vegetation':len(new),'new_grass':sum(r['asset']=='TropicalGrass' for r in new),'new_palms':sum(r['asset'].startswith('CoconutPalm') for r in new),'new_vegetation_dry_footprint_failures':dry_bad,'new_vegetation_road_clearance_failures':road_bad,'new_vegetation_missing_ground':sum(not h for h in center_hits),'minimum_road_center_distance_m':minimum,'original_939_props_identical':before['prop_instances']==after['prop_instances'][:len(before['prop_instances'])],'native_route_identical':before['route_points_m']==after['route_points_m'],'native_checkpoints_identical':before['checkpoints_m']==after['checkpoints_m'],'runtime_route_identical':oldruntime['route_points']==runtime['route_points'],'runtime_checkpoints_identical':oldruntime['checkpoints']==runtime['checkpoints'],'runtime_original_props_identical':oldruntime['prop_instances']==runtime['prop_instances'][:len(oldruntime['prop_instances'])],'unchanged_mesh_hash_failures':unexpected,'changed_binary_files':changed,'terrain_sha256':hashlib.sha256((ROOT/'assets/web/Course_Terrain.glb').read_bytes()).hexdigest()}
report['pass']=not any([lake_fail,dry_fail,shore_ground_fail,shore_water_fail,dry_bad,road_bad,report['new_vegetation_missing_ground'],unexpected]) and all(report[k] for k in ['original_939_props_identical','native_route_identical','native_checkpoints_identical','runtime_route_identical','runtime_checkpoints_identical','runtime_original_props_identical'])
(OUT/'terrain_repair_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert report['pass'], 'Terrain repair validation failed'
