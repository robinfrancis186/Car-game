import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {GameModel} from '../src/gameplay.js';
const normalizeWorldData=data=>({...data,...data.world});
import {worldPhysicsOptions} from '../src/tracks.js';
const root=new URL('../public/assets/',import.meta.url),loader=new GLTFLoader();let rays=0,maxError=0;
for(const name of ['course_runtime.json','course_runtime_highlands.json']){
 const raw=JSON.parse(await fs.readFile(new URL(name,root))),world=normalizeWorldData(raw);
 assert.deepEqual(raw.ramps,raw.world.ramps,'Both schema copies match actual normalization');assert.equal(raw.air_traffic,raw.world.air_traffic);assert.equal(world.ramps.length,1);
 const frozenRouteHashes={"course_runtime.json": "4d40a75bc75bcccc77235faccee247b5e360449857760963030e03cca1563dac", "course_runtime_highlands.json": "78c9671546e887afd21f3e81ff6c78d01d8cf8e27dd9f1e35fbe939494f4aa0c"};
 assert.equal(createHash('sha256').update(JSON.stringify(world.route_points)).digest('hex'),frozenRouteHashes[name],'Existing route elevations/positions untouched');
 const model=new GameModel(world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]})),worldPhysicsOptions(world));
 const r=world.ramps[0],file=name.includes('highlands')?'Highland_AirtimeRamp.glb':'Coast_AirtimeRamp.glb',b=await fs.readFile(new URL(file,root));const asset=(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;asset.updateMatrixWorld(true);
 const surfaces=[];let triangles=0;asset.traverse(o=>{if(!o.isMesh)return;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;assert(o.geometry.attributes.position.array.every(Number.isFinite));if(/asphalt/i.test(o.material.name))surfaces.push(o);});assert(triangles<500);assert.equal(surfaces.length,1);
 const ray=new THREE.Raycaster();for(let s=r.startS+.05;s<r.lipS;s+=.19)for(const offset of [-r.halfWidth+.05,-r.halfWidth*.5,0,r.halfWidth*.5,r.halfWidth-.05]){
  const q=model.sampleRoute(s),x=q.x+q.nx*offset,z=q.z+q.nz*offset,y=q.y+r.rise*(s-r.startS)/(r.lipS-r.startS);ray.set(new THREE.Vector3(x,y+10,z),new THREE.Vector3(0,-1,0));const hit=ray.intersectObjects(surfaces)[0];assert(hit,`${name} surface gap at ${s}/${offset}`);const err=Math.abs(hit.point.y-y);maxError=Math.max(maxError,err);assert(err<.0015,`Surface/model difference ${err}`);assert(hit.face.normal.clone().transformDirection(hit.object.matrixWorld).y>.8,'Top faces upward');rays++;
 }
 assert(world.course_meshes.some(e=>e.file===file),'Ramp GLB actually loaded by world');
}
console.log(`PASS ramp actual GLB/support geometry: ${rays} road-footprint rays, max error ${maxError}m; unchanged base routes, root/nested metadata coherent, bounded mesh budget. No WebGL rendering.`);
