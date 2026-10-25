// Actual exported road/wheel geometry + actual runtime metadata. No GPU or human-input claim.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import {GameModel,buildCourseObstacles} from '../../web/src/gameplay.js';
import {CAR_IDS,CAR_CATALOG} from '../../web/src/garage.js';
import {TRACKS,eventSlice,routeLength,worldPhysicsOptions} from '../../web/src/tracks.js';
globalThis.document={baseURI:'http://localhost/'};globalThis.window={};
const {normalizeWorldData}=await import('../../web/src/scene.js');
const assets=new URL('../../web/public/assets/',import.meta.url),loadJSON=f=>JSON.parse(fs.readFileSync(new URL(f,assets))),loader=new GLTFLoader(),hash=f=>createHash('sha256').update(fs.readFileSync(new URL(f,assets))).digest('hex');
async function load(f){const b=fs.readFileSync(new URL(f,assets));const g=(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;g.updateMatrixWorld(true);return g;}
const report={scope:'Reconstructed seven-car source/GLB geometry regression, not browser acceptance',created:new Date().toISOString(),cases:[],hashes:{},capsuleRays:0,wheelRays:0};
const wheels={};for(const id of CAR_IDS){const g=await load(CAR_CATALOG[id].asset);report.hashes[CAR_CATALOG[id].asset]=hash(CAR_CATALOG[id].asset);wheels[id]=[];for(const key of ['Front_Left','Front_Right','Rear_Left','Rear_Right']){const node=g.getObjectByName('Wheel_'+key);assert(node,id+' missing wheel');const bb=new THREE.Box3().setFromObject(node);for(const z of [bb.min.z,bb.max.z])wheels[id].push([node.getWorldPosition(new THREE.Vector3()).x,z]);}}
const ray=new THREE.Raycaster(),down=new THREE.Vector3(0,-1,0),origin=new THREE.Vector3();
for(const track of Object.values(TRACKS)){
 const raw=loadJSON(track.file),w=normalizeWorldData(raw);if(raw.world?.explore_starts)assert.deepEqual(raw.explore_starts,raw.world.explore_starts,'Root/nested starts must not disagree');
 report.hashes[track.file]=hash(track.file);const roadFiles=w.course_meshes.filter(c=>/Road/i.test(c.name)).map(c=>c.file);assert(roadFiles.length);const road=[];for(const f of roadFiles){const g=await load(f);g.traverse(o=>{if(o.isMesh&&/asphalt|road surface|highway pavement/i.test(o.material.name))road.push(o);});report.hashes[f]=hash(f);}assert(road.length,'Actual asphalt material selection');
 const furniture=loadJSON(w.furniture_file||'furniture_colliders.json').colliders,infra=loadJSON(w.collision_file).colliders,obstacles=buildCourseObstacles(w,[...furniture,...infra]),route=w.route_points.map(p=>({x:p[0],y:p[1],z:p[2]}));
 for(const dest of w.explore_starts)for(const id of CAR_IDS)for(const upgraded of [false,true]){
  const slice=eventSlice(track,w,'free-drive',routeLength(route),dest.s),m=new GameModel(route,{...worldPhysicsOptions(w),...slice,obstacles,vehicleId:id,upgrades:upgraded?{speed:3,acceleration:3,handling:3,boost:3}:{}}).start('free-drive');let minMargin=Infinity,maxError=0;
  for(let n=0;n<=360;n++){
   if(n)m.update(1/120,{throttle:1});const p=m.player;if(n%3!==0&&n!==360)continue;
   const points=[];for(const end of [-1,1])for(let a=0;a<8;a++){const t=a*Math.PI/4;points.push([end*1.25+Math.cos(t)*.98,Math.sin(t)*.98,'capsule']);}for(const v of wheels[id])points.push([...v,'wheel']);
   for(const [lx,lz,type]of points){const x=p.x+Math.cos(p.heading)*lx-Math.sin(p.heading)*lz,z=p.z+Math.sin(p.heading)*lx+Math.cos(p.heading)*lz,q=m.projectToRoute(x,z,p.s);ray.set(origin.set(x,p.y+5,z),down);ray.far=12;const hits=ray.intersectObjects(road,false).filter(h=>h.face?.normal.y>0);assert(hits.length,`${track.id}/${dest.name}/${id}/${upgraded?'max':'stock'} ${type} off asphalt at ${(n/120).toFixed(3)}s`);maxError=Math.max(maxError,Math.abs(hits[0].point.y-q.y));minMargin=Math.min(minMargin,m._roadZone(q).halfWidth-q.distance);report[type==='wheel'?'wheelRays':'capsuleRays']++;}
  }
  assert.equal(m.damage,0);assert.equal(m.automaticRecoveries,0);assert(!m.player.offRoad);assert(maxError<.04,'Road/model surface alignment');report.cases.push({track:track.id,destination:dest.name,s:dest.s,car:id,upgraded,minMargin,maxError});
 }
}
fs.writeFileSync(new URL('./explore_asphalt_metrics.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(`PASS ${report.cases.length} stock/max actual-runtime departures; ${report.capsuleRays} capsule and ${report.wheelRays} exported-wheel asphalt rays; no damage/off-road/auto-return. No browser claim.`);
