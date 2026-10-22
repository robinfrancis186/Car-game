// Full shipped-world loader and instance graph, without a GPU or browser.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
const directory=new URL('../public/assets/',import.meta.url);
globalThis.document={baseURI:'http://localhost/'};globalThis.self=globalThis;
// PNG header/dimension shim only: actual texture decoding is checked in Blender/browser.
globalThis.createImageBitmap??=async(blob)=>{const b=Buffer.from(await blob.arrayBuffer());assert.equal(b.toString('hex',0,8),'89504e470d0a1a0a');return {width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}};};
globalThis.ProgressEvent=class ProgressEvent{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const assets={};for(const name of await fs.readdir(directory)){if(!/\.(glb|json)$/.test(name))continue;const b=await fs.readFile(new URL(name,directory));assets[name]=`data:${name.endsWith('.glb')?'model/gltf-binary':'application/json'};base64,${b.toString('base64')}`;}
globalThis.window={__MALABAR_ASSETS__:assets};
const {CoastRenderer}=await import('../src/scene.js');
const renderer=Object.create(CoastRenderer.prototype);
Object.assign(renderer,{scene:new THREE.Scene(),onProgress(){},cars:[],environmentChunks:[],waterShaders:[],windShaders:[],windowMaterials:[]});
await renderer.load();
assert(['v8-kerala-infrastructure','v9-canals-and-highlands'].includes(renderer.world.version));
assert.equal(renderer.world.districts.length,5);assert.equal(renderer.transit.length,2);assert.equal(renderer.cars.length,6);assert(renderer.infrastructureColliders.length>=450);assert.equal(renderer.world.elevated_corridors.length,1);
let instances=0,meshes=0,tinted=0;const palette=new Set();
for(const chunk of renderer.environmentChunks){assert(chunk.userData.center.toArray().every(Number.isFinite));chunk.traverse(o=>{if(!o.isInstancedMesh)return;meshes++;instances+=o.count;for(const value of o.instanceMatrix.array)assert(Number.isFinite(value));if(o.instanceColor){tinted+=o.count;for(let i=0;i<o.instanceColor.count;i++){const c=new THREE.Color().fromBufferAttribute(o.instanceColor,i);palette.add(c.getHexString());}}});}
assert(instances>renderer.world.prop_instances.length);assert(tinted>200);assert(palette.size>=4,'Authored neighborhood facade/accent variation must survive instancing');
for(const vehicle of renderer.transit){vehicle.update(14,1/60);assert(vehicle.colliderProxies.length>0);for(const o of vehicle.colliderProxies)for(const [key,value] of Object.entries(o))if(typeof value==='number')assert(Number.isFinite(value),key);}
assert.equal(renderer.transit.find(t=>t.kind==='metro').carriages.length,3);assert.equal(renderer.transit.find(t=>t.kind==='ferry').colliderProxies[0].shape,'box');
console.log(`PASS full actual world.load: ${Object.keys(renderer.models).length} GLBs, ${renderer.world.prop_instances.length} placements, ${meshes} spatial/material instance batches, ${palette.size} facade/accent colors, ${renderer.infrastructureColliders.length} infrastructure proxies, two moving transit rigs. No WebGL rendering.`);

assert(assets['course_runtime_highlands.json'],'The selectable Highland course must actually ship, not silently skip acceptance.');
const high=Object.create(CoastRenderer.prototype);Object.assign(high,{worldFile:'course_runtime_highlands.json',scene:new THREE.Scene(),onProgress(){},cars:[],environmentChunks:[],waterShaders:[],windShaders:[],windowMaterials:[]});await high.load();
assert(high.route.length>100);assert(Math.max(...high.route.map(p=>p.y))>90);assert(high.world.terrain_grid?.heights.length>10000);assert(high.world.road_sections.length>=2);assert(high.world.explore_starts.length>=3);assert.equal(high.cars.length,6);assert.equal(high.transit.length,0);assert.equal(high.waterSurface.length,0);
assert(high.models['BirdRockLookout.glb'],'The bird landmark must exist in the actual selected world');let normalMaps=0;high.models['BirdRockLookout.glb'].traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.normalMap){normalMaps++;assert.equal(m.normalMap.image.width,256);assert.equal(m.normalMap.image.height,256);}});assert(normalMaps>0);
for(const entry of high.world.course_meshes){let nodes=0;high.models[entry.file].traverse(o=>{if(o.isMesh){nodes++;assert(o.geometry.attributes.position.count>0);for(const value of o.geometry.attributes.position.array)assert(Number.isFinite(value));}});assert(nodes>0);}
console.log(`PASS actual Highland world.load: ${Object.keys(high.models).length} GLBs, ${high.world.prop_instances.length} placements, ${high.infrastructureColliders.length} proxies, terrain grid, graded route, divided-road metadata, landmark normal-map wiring and no coastal water/transit leak. No WebGL or image decoding.`);
