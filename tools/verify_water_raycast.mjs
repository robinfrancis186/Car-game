/** Optional source-parity check. Uses the existing frozen V10 Three installation.
 * Run from alpha: node tools/verify_water_raycast.mjs ../kerala_racing_v10/web
 * Not part of the dependency-light server or npm test. CPU raycast only.
 */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { createWaterQuery } from '../shared/water.js';
const root=resolve(process.argv[2]||'../kerala_racing_v10/web');
const THREE=await import(pathToFileURL(root+'/node_modules/three/build/three.module.js'));
const {GLTFLoader}=await import(pathToFileURL(root+'/node_modules/three/examples/jsm/loaders/GLTFLoader.js'));
const b=await readFile(root+'/public/assets/Course_Water.glb');
const scene=(await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength), '')).scene;
scene.updateMatrixWorld(true);
const meshes=[];
scene.traverse(o=>{if(o.isMesh&&[o.material].flat().some(m=>/ocean|water/i.test(m.name)))meshes.push(o)});
const data=JSON.parse(await readFile(new URL('../data/water.json',import.meta.url)));
assert.equal(createHash('sha256').update(b).digest('hex'),data.sourceSha256,'Source GLB must match exported water data');
const water=createWaterQuery(data),ray=new THREE.Raycaster();let samples=0,mismatches=0,seed=31969;
const rand=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};
const check=(x,z)=>{ray.set(new THREE.Vector3(x,30,z),new THREE.Vector3(0,-1,0));const expected=ray.intersectObjects(meshes,false).length>0; samples++;if(expected!==water(x,z))mismatches++;};
for(const t of data.triangles)check((t[0]+t[3]+t[6])/3,(t[2]+t[5]+t[8])/3);
for(let i=0;i<20000;i++)check(-7000+11000*rand(),-7000+10000*rand());
const evidence={comparison:'Three 0.170.0 CPU Raycaster vs headless authored water query',sourceSha256:data.sourceSha256,waterTriangles:data.triangles.length,centroidSamples:data.triangles.length,seededRandomSamples:20000,randomSeed:31969,samples,mismatches,meshCount:meshes.length,gpu:false,internetMultiplayer:false};
console.log(JSON.stringify(evidence));
await writeFile(new URL('../docs/water_validation.json',import.meta.url),JSON.stringify(evidence,null,2)+'\n');
assert.equal(mismatches,0,'Headless water query must match frozen renderer CPU raycast');
