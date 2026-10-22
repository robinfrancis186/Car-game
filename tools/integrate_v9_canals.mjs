/** Place authored v9 canopy/shikaras and a richer harbor onto verified v8 ground/water.
 * Does not edit original OSM route, road, terrain or water geometry. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const THREE=await import(ROOT+'/web/node_modules/three/build/three.module.js');
const {GLTFLoader}=await import(ROOT+'/web/node_modules/three/examples/jsm/loaders/GLTFLoader.js');
const {GameModel,buildCourseObstacles}=await import(ROOT+'/web/src/gameplay.js');
globalThis.ProgressEvent=class{constructor(type,fields){Object.assign(this,fields);}};
const json=async p=>JSON.parse(await fs.readFile(path.join(ROOT,p),'utf8'));
const world=await json('assets/course/coastal_v8_base_runtime.json'),collision=await json('assets/course/coastal_v8_base_colliders.json');
const furniture=await json('web/public/assets/furniture_colliders.json');
const treeManifest=await json('assets/landscape_reference_kit/CanalRainTree_manifest.json'),shikaraManifest=await json('assets/landscape_reference_kit/CanalShikara_manifest.json');
const model=new GameModel(world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]})));
const geo=await json('references/route/kappil_osm_environment.geojson'),sourceRoute=await json('references/route/kappil_route_local_meters.json');const[lon0,lat0]=sourceRoute.origin_wgs84_lon_lat,earth=6371000;const lakes=geo.features.filter(f=>f.properties.natural==='water'&&f.geometry.type==='Polygon').map(f=>f.geometry.coordinates[0].map(p=>[(p[0]-lon0)*Math.PI/180*earth*Math.cos(lat0*Math.PI/180),-(p[1]-lat0)*Math.PI/180*earth]));
function inLake(x,z){return lakes.some(poly=>{let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>z)!==(b[1]>z)&&x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])inside=!inside;}return inside;});}

const loader=new GLTFLoader(),loaded={};
async function load(name){if(loaded[name])return loaded[name];const b=await fs.readFile(path.join(ROOT,'web/public/assets',name+'.glb'));const g=(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;g.updateMatrixWorld(true);return loaded[name]=g;}
const water=await load('Course_Water'),terrain=await load('Course_Terrain');const waterMeshes=[],terrainMeshes=[];
water.traverse(o=>{if(o.isMesh&&/water|ocean/i.test(o.material.name))waterMeshes.push(o);});terrain.traverse(o=>{if(o.isMesh)terrainMeshes.push(o);});
const ray=new THREE.Raycaster();let waterRays=0,groundRays=0;
function waterAt(x,z){waterRays++;ray.set(new THREE.Vector3(x,100,z),new THREE.Vector3(0,-1,0));const a=ray.intersectObjects(waterMeshes,true);return a.length?a[0].point.y:null;}
function groundAt(x,z){groundRays++;ray.set(new THREE.Vector3(x,100,z),new THREE.Vector3(0,-1,0));const a=ray.intersectObjects(terrainMeshes,true);return a.length?a[0].point.y:null;}
const solids=[...buildCourseObstacles(world,furniture.colliders),...collision.colliders],added=[],addedColliders=[];
function nearSolid(x,z,margin){return [...solids,...addedColliders].some(o=>{if(o.shape==='box'){const co=Math.cos(o.heading||0),si=Math.sin(o.heading||0),dx=x-o.x,dz=z-o.z;return Math.abs(dx*co+dz*si)<o.halfLength+margin&&Math.abs(-dx*si+dz*co)<o.halfWidth+margin;}if(o.shape==='capsule'){const dx=(o.endX??o.x)-o.x,dz=(o.endZ??o.z)-o.z,t=Math.max(0,Math.min(1,((x-o.x)*dx+(z-o.z)*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-o.x-dx*t,z-o.z-dz*t)<o.radius+margin;}return Math.hypot(x-o.x,z-o.z)<o.radius+margin;});}
function localWorld(pos,heading,x,z){const co=Math.cos(heading),si=Math.sin(heading);return [pos[0]+x*co-z*si,pos[2]+x*si+z*co];}
function boxProxy(id,pos,heading,center,half,kind){const [x,z]=localWorld(pos,heading,center[0],center[2]);return{id,kind,shape:'box',x,z,y:pos[1]+center[1]-half[1],height:half[1]*2,heading,halfLength:half[0],halfWidth:half[2],radius:Math.hypot(half[0],half[2])};}
function authoredProxies(manifest,id,pos,heading,scale=1){return manifest.collision_proxies.map((proxy,i)=>{if(proxy.type==='obb')return boxProxy(id+'-'+i,pos,heading,proxy.center_local_m.map(v=>v*scale),proxy.half_extents_m.map(v=>v*scale),manifest.asset==='CanalRainTree'?'tree_root':'moored_shikara');const a=proxy.a_local_m.map(v=>v*scale),b=proxy.b_local_m.map(v=>v*scale),r=proxy.radius_m*scale,[x,z]=localWorld(pos,heading,a[0],a[2]),[endX,endZ]=localWorld(pos,heading,b[0],b[2]),bottom=Math.min(a[1],b[1])-r;return{id:id+'-'+i,kind:'tree_trunk',shape:'capsule',x,z,endX,endZ,radius:r,y:pos[1]+bottom,height:Math.max(a[1],b[1])+r-bottom};});}
function add(asset,pos,heading,scale,district){const p={asset,position:pos,yaw_rad:-heading,scale,district};added.push(p);return p;}
// Long crowns arch over the roadside and shallow water, rather than putting trunks in the race lane.
let treeIndex=0;for(const [start,end] of [[2350,2470],[3020,3180]])for(let s=start;s<=end;s+=12)for(const side of [-1,1]){
 const q=model.sampleRoute(s);let done=false;
 for(const offset of [10.5,14,18,22,27]){const x=q.x+q.nx*side*offset,z=q.z+q.nz*side*offset,y=groundAt(x,z);if(y===null||waterAt(x,z)!==null||nearSolid(x,z,1.7))continue;
  const scale=.91+(treeIndex%4)*.035,heading=q.heading+(side>0?-Math.PI/2:Math.PI/2),p=add('CanalRainTree',[x,y,z],heading,scale,'canal_garden');
  addedColliders.push(...authoredProxies(treeManifest,'v9-canopy-trunk-'+treeIndex,p.position,heading,scale));treeIndex++;done=true;break;
 }
}
// Extra bank trees follow the inland lake edge; seaside trees are not a substitute for a backwater canopy.
let bankTrees=0;for(const [start,end] of [[2355,2465],[3020,3175]])for(let s=start;s<=end;s+=16){const q=model.sampleRoute(s);for(const side of [-1,1]){let shore=null;for(let off=8;off<120;off+=2){if(inLake(q.x+q.nx*side*off,q.z+q.nz*side*off)){shore=off;break;}}if(shore===null)continue;for(const inset of [7,10,13]){const off=shore-inset;if(off<7)continue;const x=q.x+q.nx*side*off,z=q.z+q.nz*side*off,y=groundAt(x,z);if(y===null||waterAt(x,z)!==null||nearSolid(x,z,1.7))continue;const scale=.96,heading=q.heading+(side>0?Math.PI/2:-Math.PI/2);add('CanalRainTree',[x,y,z],heading,scale,'canal_garden');addedColliders.push(...authoredProxies(treeManifest,'v9-canopy-trunk-'+treeIndex++,[x,y,z],heading,scale));bankTrees++;break;}}}
// Wet-footprint checks sample an actual GLB below-water outline, not only its center.
async function hullPoints(asset){const g=await load(asset),pts=[];g.traverse(o=>{if(!o.isMesh)return;const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++){const p=new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);if(p.y<.05)pts.push([p.x,p.z]);}});const seen=new Set();return pts.filter(p=>{const k=p.map(v=>v.toFixed(2)).join(',');if(seen.has(k))return false;seen.add(k);return true;});}
function fullyWet(pos,heading,outline){return outline.every(p=>{const [x,z]=localWorld(pos,heading,...p);return inLake(x,z)&&waterAt(x,z)!==null;});}
const shikaraOutline=await hullPoints('CanalShikara'),boatPlacements=[];
for(const s of [2365,2392,2420,2450,3025,3055,3085,3120]){const q=model.sampleRoute(s);for(const side of [-1,1]){let found=false;for(let offset=23;offset<=110;offset+=3){const pos=[q.x+q.nx*side*offset,.015,q.z+q.nz*side*offset],heading=q.heading+(s%2?.16:-.12);if(nearSolid(pos[0],pos[2],5)||!fullyWet(pos,heading,shikaraOutline))continue;add('CanalShikara',pos,heading,1,'canal_garden');addedColliders.push(...authoredProxies(shikaraManifest,'v9-shikara-'+boatPlacements.length,pos,heading));boatPlacements.push({pos,heading});found=true;break;}if(found)break;}}
const ferry=world.transit_routes.find(t=>t.type==='ferry'),start=ferry.points[0],end=ferry.points.at(-1),fh=Math.atan2(end[2]-start[2],end[0]-start[0]);const ferryOutline=await hullPoints('water_transit_ferry');const ferries=[];
for(const along of [26,60,100]){if(ferries.length>=2)break;for(const side of [-1,1]){let found=false;for(const offset of [23,30,38,46]){const [x,z]=localWorld(start,fh,along,side*offset),pos=[x,.015,z];if(nearSolid(x,z,13)||!fullyWet(pos,fh,ferryOutline))continue;add('water_transit_ferry',pos,fh,1,'backwater_harbor');addedColliders.push(boxProxy('v9-moored-ferry-'+ferries.length,pos,fh,[-.0775,1.935,0],[11.9275,3.055,4.21],'moored_ferry'));ferries.push({pos,heading:fh});found=true;break;}if(found)break;}}
// Map the actual authored side-street centerlines; do not invent a fake street texture.
const streetModel=await load('SideStreetSegment'),streetBounds=new THREE.Box3().setFromObject(streetModel),mini=[];
for(const p of world.prop_instances)if(p.asset==='SideStreetSegment'){const heading=-p.yaw_rad;mini.push([streetBounds.min.x,streetBounds.max.x].map(x=>{const [wx,wz]=localWorld(p.position,heading,x*p.scale,0);return [wx,p.position[1]+.05,wz];}));}
world.prop_instances.push(...added);collision.colliders.push(...addedColliders);world.minimap_roads=mini;world.garage_s=1500;world.version='v9-canals-and-highlands';world.world={...world.world,version:world.version,minimap_roads:mini,garage_s:world.garage_s,total_prop_instances:world.prop_instances.length};
// Menu discovery waypoints supplement geographically continuous district names.
world.explore_starts=[{name:'Coastal Villages',s:0},{name:'Metro Market / Station',s:2000},{name:'Canal Garden / Shikaras',s:2380},{name:'Skyline Flyover',s:2530},{name:'Water Transit / Harbor',s:3050},{name:'Harbour Avenue',s:4000}];world.world.explore_starts=world.explore_starts;
const report={scope:'Actual original GLB ground/water ray placement, not browser rendering',counts:{rainTrees:treeIndex,lakeBankTrees:bankTrees,shikaras:boatPlacements.length,mooredFerries:ferries.length,minimapSideStreets:mini.length,allProps:world.prop_instances.length,allInfrastructure:collision.colliders.length},queries:{groundRays,waterRays},shikaras:boatPlacements,ferries,treeCollision:'Two authored primary-trunk capsules plus root OBB; crown foliage is non-solid visual wind; capsule vertical ranges are conservative arcade extrusions',footprintPolicy:'Every unique actual below-water GLB vertex must lie inside original inland OSM lake polygons AND hit the actual water mesh at placement; no shikaras placed in the Arabian Sea'};
if(treeIndex<12||boatPlacements.length<5||ferries.length<2)throw new Error('Insufficient actual canal/harbor placements: '+JSON.stringify(report.counts));
for(const dir of ['web/public/assets','assets/web']){await fs.writeFile(path.join(ROOT,dir,'course_runtime.json'),JSON.stringify(world));await fs.writeFile(path.join(ROOT,dir,'infrastructure_colliders.json'),JSON.stringify(collision));}
await fs.mkdir(path.join(ROOT,'tests/v9'),{recursive:true});await fs.writeFile(path.join(ROOT,'tests/v9/canal_integration.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
