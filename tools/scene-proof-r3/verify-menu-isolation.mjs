/** Graph/state-only checks. This does not create WebGL or claim pixel acceptance. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from '../../web/node_modules/three/build/three.module.js';
globalThis.document={baseURI:'http://localhost/'};
const {CoastRenderer}=await import('../../web/src/scene.js');
const {createCoastalShowroom,createShowroomReflectionScene}=await import('../../web/src/showroom-scene.js');
const r=Object.create(CoastRenderer.prototype);
Object.assign(r,{scene:new THREE.Scene(),sun:new THREE.DirectionalLight('#ffddb1',3.1),hemisphere:new THREE.HemisphereLight('#e7f0ef','#485438',2),renderer:{toneMappingExposure:1.05},showroomEnvironment:{id:'menu'},coastalEnvironment:{id:'game'}});
const state=()=>({sun:r.sun.intensity,hemisphere:r.hemisphere.intensity,sunColor:r.sun.color.toArray(),skyColor:r.hemisphere.color.toArray(),groundColor:r.hemisphere.groundColor.toArray(),exposure:r.renderer.toneMappingExposure});
const initial=state();
for(let i=0;i<12;i++){r.setHomeMode(true);assert.equal(r.scene.environment,r.showroomEnvironment);assert.equal(r.renderer.toneMappingExposure,.92);r.setGarageMode(true);assert.equal(r.homeMode,false);r.setHomeMode(true);assert.equal(r.garageMode,false);r.setHomeMode(false);assert.equal(r.scene.environment,r.coastalEnvironment);assert.deepEqual(state(),initial);}
let triangles=0,meshes=0;const s=createCoastalShowroom({});
s.group.traverse(o=>{if(o.isMesh){meshes++;const p=o.geometry.getAttribute('position');assert(p.array.every(Number.isFinite));triangles+=(o.geometry.index?.count||p.count)/3;assert(o.material);}});assert(triangles<20000);s.update(1);s.dispose();
const meshesByMaterial=[];s.group.traverse(o=>{if(o.isMesh)meshesByMaterial.push(o);});const ocean=meshesByMaterial.find(o=>o.material.name==='R3 sunset ocean'),sky=meshesByMaterial.find(o=>o.material.name==='Showroom sunset sky');assert(ocean&&sky);assert(ocean.geometry.parameters.width>=sky.geometry.parameters.radius*2);assert(ocean.geometry.parameters.height>=sky.geometry.parameters.radius*2);assert.equal(ocean.position.x,0);assert.equal(ocean.position.z,0);
const env=createShowroomReflectionScene();assert.equal(env.children.length,5);env.traverse(o=>{if(o.isMesh){assert(o.geometry.attributes.position.array.every(Number.isFinite));o.geometry.dispose();o.material.dispose();}});
const result={result:'PASS',scope:'Graph/state only, not GPU',modeTransitions:48,lightColorIntensityExposureRestored:true,reflectionEnvironmentRestored:true,proceduralMeshesExcludingLoadedPalms:meshes,proceduralTrianglesExcludingLoadedPalms:triangles,finiteVertices:true,oceanCoversFullSkyCrossSection:true,noWebGL:true};await fs.writeFile(new URL('./menu-isolation-results.json',import.meta.url),JSON.stringify(result,null,2)+'\n');console.log(result);
