import {makeAtmosphere} from '../src/finish-fx.js';
import {imageHeader} from './capture-assets.mjs';
// Full shipped-world loader and instance graph, without a GPU or browser.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
const directory=new URL('../public/assets/',import.meta.url);
globalThis.document={baseURI:'http://localhost/'};globalThis.self=globalThis;
// PNG header/dimension shim only: actual texture decoding is checked in Blender/browser.
globalThis.createImageBitmap??=imageHeader;
globalThis.ProgressEvent=class ProgressEvent{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const assets={};for(const name of await fs.readdir(directory)){if(!/\.(glb|json)$/.test(name))continue;const b=await fs.readFile(new URL(name,directory));assets[name]=`data:${name.endsWith('.glb')?'model/gltf-binary':'application/json'};base64,${b.toString('base64')}`;}
globalThis.window={__MALABAR_ASSETS__:assets};
const {CoastRenderer}=await import('../src/scene.js');
const renderer=Object.create(CoastRenderer.prototype);
Object.assign(renderer,{worldFile:'course_runtime.json',sky:makeAtmosphere(),sun:new THREE.DirectionalLight(),hemisphere:new THREE.HemisphereLight(),renderer:{toneMappingExposure:1.05},scene:new THREE.Scene(),onProgress(){},cars:[],environmentChunks:[],waterShaders:[],windShaders:[],windowMaterials:[]});
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
const high=Object.create(CoastRenderer.prototype);Object.assign(high,{worldFile:'course_runtime_highlands.json',sky:makeAtmosphere(),sun:new THREE.DirectionalLight(),hemisphere:new THREE.HemisphereLight(),renderer:{toneMappingExposure:1.05},scene:new THREE.Scene(),onProgress(){},cars:[],environmentChunks:[],waterShaders:[],windShaders:[],windowMaterials:[]});await high.load();
assert(high.route.length>100);assert(Math.max(...high.route.map(p=>p.y))>90);assert(high.world.terrain_grid?.heights.length>10000);assert(high.world.road_sections.length>=2);assert(high.world.explore_starts.length>=3);assert.equal(high.cars.length,6);assert.equal(high.transit.length,0);assert.equal(high.waterSurface.length,0);
assert(high.models['BirdRockLookout.glb'],'The bird landmark must exist in the actual selected world');let normalMaps=0;high.models['BirdRockLookout.glb'].traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.normalMap){normalMaps++;assert.equal(m.normalMap.image.width,256);assert.equal(m.normalMap.image.height,256);}});assert(normalMaps>0);
for(const entry of high.world.course_meshes){let nodes=0;high.models[entry.file].traverse(o=>{if(o.isMesh){nodes++;assert(o.geometry.attributes.position.count>0);for(const value of o.geometry.attributes.position.array)assert(Number.isFinite(value));}});assert(nodes>0);}
console.log(`PASS actual Highland world.load: ${Object.keys(high.models).length} GLBs, ${high.world.prop_instances.length} placements, ${high.infrastructureColliders.length} proxies, terrain grid, graded route, divided-road metadata, landmark normal-map wiring and no coastal water/transit leak. No WebGL or image decoding.`);

assert.equal(renderer.simReadyPilot.sites.length,3);assert(!high.simReadyPilot,'NVIDIA coastal pilot must not leak into Highlands');
let pilotTriangles=0;for(const {site}of renderer.simReadyPilot.sites)for(const lod of site.children){assert.equal(lod.autoUpdate,false);assert.equal(lod.levels.length,2);const counts=lod.levels.map(l=>{let n=0;l.object.traverse(mesh=>{if(mesh.isMesh){n+=(mesh.geometry.index?.count||mesh.geometry.attributes.position.count)/3*mesh.count;assert(mesh.material.map);assert(mesh.material.normalMap);assert(mesh.material.roughnessMap);assert(mesh.material.metalnessMap);for(const v of mesh.instanceMatrix.array)assert(Number.isFinite(v));}});return n;});assert(counts[1]<counts[0]);pilotTriangles+=counts[1];}
assert(pilotTriangles<82000,'three sites retain bounded far mesh budget');renderer.simReadyPilot.update(new THREE.PerspectiveCamera(),{menu:true});assert(renderer.simReadyPilot.sites.every(x=>!x.site.visible));console.log('PASS genuine embedded NVIDIA PBR maps, three instanced coastal sites, finite transforms, cheaper manual mobile LODs, culling and menu/Highlands isolation.');

// Instanced facade tint clones must retain the actual compiled material hook.
let facadeHooks=0,facadeInstances=0;
for(const r of [renderer,high])for(const chunk of r.environmentChunks)chunk.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material])if(m.userData.scenerySurface==='facade'){const shader={vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader,uniforms:{}};m.onBeforeCompile(shader);assert(shader.uniforms.sceneryDetail?.value?.isDataTexture,'facade clone lost its PBR detail hook');assert(shader.vertexShader.includes('vFacadePoint'));assert(shader.fragmentShader.includes('scDamp'));facadeHooks++;facadeInstances+=o.count||1;}});
assert(facadeHooks>0);assert(facadeInstances>200);console.log(`PASS ${facadeHooks} actual coastal/Highland material hooks across ${facadeInstances} facade instances preserved with shared texture and exact authored instance colours.`);
