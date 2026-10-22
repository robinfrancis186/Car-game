/** Original deterministic V10 tea-detail placement. Pure JS, no imports or global state. */
const teaHash=x=>{x^=x>>>16;x=Math.imul(x,0x7feb352d);x^=x>>>15;x=Math.imul(x,0x846ca68b);return(x^(x>>>16))>>>0;};
const teaUnit=x=>teaHash(x)/4294967296;
export function sampleTeaTerrain(grid,x,z){
 const [nx,nz]=grid.count,[dx,dz]=grid.step,[x0,z0]=grid.origin;
 let u=(x-x0)/dx,v=(z-z0)/dz;const i=Math.max(0,Math.min(nx-2,Math.floor(u))),j=Math.max(0,Math.min(nz-2,Math.floor(v)));
 u=Math.max(0,Math.min(1,u-i));v=Math.max(0,Math.min(1,v-j));const a=grid.heights[j*nx+i],b=grid.heights[j*nx+i+1],c=grid.heights[(j+1)*nx+i],d=grid.heights[(j+1)*nx+i+1];
 return v<=u?a+(b-a)*u+(d-b)*v:a+(d-c)*u+(c-a)*v;
}
export function buildTeaPlacementIndex(manifest,cellSize=32){
 const segments=[],cells=new Map();
 for(const run of manifest.runs)for(let i=0;i<run.points.length-1;i++){
  const a=run.points[i],b=run.points[i+1],d0=run.distances_m[i],d1=run.distances_m[i+1];if(d1-d0<1e-6)continue;
  const index=segments.length;segments.push({row_id:run.row_id,run_id:run.id,a,b,d0,d1});
  for(let ix=Math.floor((Math.min(a[0],b[0])-1)/cellSize);ix<=Math.floor((Math.max(a[0],b[0])+1)/cellSize);ix++)for(let iz=Math.floor((Math.min(a[2],b[2])-1)/cellSize);iz<=Math.floor((Math.max(a[2],b[2])+1)/cellSize);iz++){
   const key=ix+','+iz;if(!cells.has(key))cells.set(key,[]);cells.get(key).push(index);
  }
 }
 return {segments,cells,cellSize};
}
export function selectTeaDetailPlacements(manifest,terrainGrid,{center,radius=85,maxInstances=1250,index}={}){
 if(!center||!terrainGrid)throw new Error('Exact terrain grid and a Three-space center are required.');
 index=index||buildTeaPlacementIndex(manifest);const {segments,cells,cellSize}=index,p=manifest.scatter,candidates=new Set(),out=[];
 for(let ix=Math.floor((center[0]-radius-1)/cellSize);ix<=Math.floor((center[0]+radius+1)/cellSize);ix++)for(let iz=Math.floor((center[2]-radius-1)/cellSize);iz<=Math.floor((center[2]+radius+1)/cellSize);iz++)for(const id of cells.get(ix+','+iz)||[])candidates.add(id);
 for(const id of candidates){
  const seg=segments[id],{a,b,d0,d1,row_id}=seg,dx=b[0]-a[0],dz=b[2]-a[2],len=Math.hypot(dx,dz),nx=-dz/len,nz=dx/len;
  const phase=teaUnit(row_id+manifest.scatter.seed)*p.pitch_m;
  for(let band=0;band<p.lateral_offsets_m.length;band++){
   const origin=phase+band*p.band_stagger_m;let k=Math.ceil((d0-origin-1e-8)/p.pitch_m);
   for(let distance=origin+k*p.pitch_m;distance<d1-1e-8;k++,distance=origin+k*p.pitch_m){
    const f=(distance-d0)/(d1-d0);if(f< -1e-7)continue;
    const seed=teaHash(Math.imul(row_id+1,0x9e3779b1)^Math.imul(k+100000,0x85ebca77)^Math.imul(band+1,0xc2b2ae3d)^p.seed);
    const lateral=p.lateral_offsets_m[band]+(teaUnit(seed+1)-.5)*p.lateral_jitter_m;
    const x=a[0]+dx*f+nx*lateral,z=a[2]+dz*f+nz*lateral,distance2=(x-center[0])**2+(z-center[2])**2;if(distance2>radius*radius)continue;
    out.push({id:`${row_id}:${band}:${k}`,row_id,position:[x,sampleTeaTerrain(terrainGrid,x,z),z],yaw_rad:-Math.atan2(dz,dx)+(teaUnit(seed+2)-.5)*p.yaw_jitter_rad,scale:p.scale_range[0]+teaUnit(seed+3)*(p.scale_range[1]-p.scale_range[0]),distance_m:Math.sqrt(distance2)});
   }
  }
 }
 out.sort((a,b)=>a.distance_m-b.distance_m||(a.id<b.id?-1:a.id>b.id?1:0));const total=out.length,placements=out.slice(0,maxInstances);
 // All nearer candidates are included. A conservative two-metre buffer prevents edge holes.
 const completeRadius=total>maxInstances?(placements.at(-1)?.distance_m||0):radius;
 let routeDistance=Infinity;const route=manifest.route_reference_xz||[];
 for(let i=0;i<route.length-1;i++){const a=route[i],b=route[i+1],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((center[0]-a[0])*dx+(center[2]-a[1])*dz)/(dx*dx+dz*dz)));routeDistance=Math.min(routeDistance,Math.hypot(center[0]-a[0]-t*dx,center[2]-a[1]-t*dz));}
 const covered=Math.min(completeRadius-2,manifest.near_route_clip_m-routeDistance-(manifest.fade_route_margin_m||12));
 return {placements,total_candidates:total,coverage_radius_m:Math.max(0,covered),route_distance_m:routeDistance,selected_triangles:placements.length*160};
}
