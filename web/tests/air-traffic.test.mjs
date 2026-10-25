import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AirTrafficRenderer} from '../src/air-traffic.js';
const loader=new GLTFLoader();
async function glb(n){const b=await fs.readFile(new URL('../public/assets/'+n,import.meta.url));return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const scene=new THREE.Scene(),air=new AirTrafficRenderer(scene,{civilian:await glb('helicopter_civilian.glb'),police:await glb('helicopter_police.glb'),blur:await glb('helicopter_rotor_blur.glb')});
const actor=(x=0)=>({active:true,visible:true,x,y:36,z:0,heading:0,pitch:0,roll:0,rotorRpm:390,beamVisible:true,beamTarget:{x:x+12,y:1,z:4},spotlightIntensity:1});
const model={state:'racing',timer:20,paused:false,helicopter:actor(),civilianHelicopter:{...actor(40),beamVisible:false}};
air.update(model);assert.equal(air.stats.visible,2);assert(air.light.intensity>0);assert(air.beam.visible);
const police=air.actors.find(a=>a.kind==='police'),civil=air.actors.find(a=>a.kind==='civilian');
assert(police.group.position.toArray().every(Number.isFinite));
let optical=new THREE.Vector3(0,-1,0).applyQuaternion(police.socket.getWorldQuaternion(new THREE.Quaternion())),desired=new THREE.Vector3(12,1,4).sub(police.socket.getWorldPosition(new THREE.Vector3())).normalize();assert(optical.angleTo(desired)<.025,'Lens and projected searchlight target agree');
const body=police.model.getObjectByName('Airframe'),bodyQ=body.quaternion.clone(),q=police.rotor.quaternion.clone(),tail=police.tail.quaternion.clone();model.timer+=1/60;air.update(model);assert(q.angleTo(police.rotor.quaternion)>.05);assert(tail.angleTo(police.tail.quaternion)>.05);assert(bodyQ.angleTo(body.quaternion)<1e-8);
const pausedQ=police.rotor.quaternion.clone(),pausedTail=police.tail.quaternion.clone(),pos=police.group.position.clone();model.paused=true;for(let i=0;i<120;i++)air.update(model);assert(pausedQ.angleTo(police.rotor.quaternion)<1e-8);assert(pausedTail.angleTo(police.tail.quaternion)<1e-8);assert(pos.equals(police.group.position));
model.paused=false;model.helicopter.beamVisible=false;air.update(model);assert.equal(air.light.intensity,0);assert(!air.beam.visible);model.helicopter.beamVisible=true;
for(const heading of [-Math.PI,-1,0,.6,Math.PI])for(const pitch of [-.15,0,.15]){model.helicopter={...actor(),heading,pitch,roll:.1};air.update(model);assert(police.group.quaternion.toArray().every(Number.isFinite));if(air.beam.visible){optical=new THREE.Vector3(0,-1,0).applyQuaternion(police.socket.getWorldQuaternion(new THREE.Quaternion()));desired=new THREE.Vector3(12,1,4).sub(police.socket.getWorldPosition(new THREE.Vector3())).normalize();assert(optical.angleTo(desired)<.025);}}
model.helicopter={...actor(),beamTarget:{x:1000,y:0,z:0}};air.update(model);assert(!air.beam.visible);assert.equal(air.light.intensity,0,'Out-of-gimbal target cannot create detached beam');
model.helicopter=actor();let queriedLens=null,queriedTarget=null;model._airLineOfSight=(a,b)=>{queriedLens=a.clone();queriedTarget=b.clone();return false;};air.update(model);assert(!air.beam.visible&&air.light.intensity===0,'Actual socket ray obstruction vetoes approximate model visibility');assert(queriedLens.distanceTo(police.socket.getWorldPosition(new THREE.Vector3()))<1e-8);assert.deepEqual(queriedTarget.toArray(),[12,1,4]);delete model._airLineOfSight;air.update(model,{quality:'balanced'});assert(!police.blur.visible&&!civil.blur.visible);
for(const state of ['menu','countdown','finished','failed','busted']){model.state=state;air.update(model);assert.equal(air.stats.visible,0);assert(!air.beam.visible);assert.equal(air.light.intensity,0);}
model.state='racing';air.update(model,{menu:true});assert.equal(air.stats.visible,0);air.update(model);assert.equal(air.stats.visible,2);
// Each cloned material is isolated across actors and template roots; changing a beacon cannot recolor another actor.
const cm=new Set();civil.model.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])cm.add(m);});police.model.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])assert(!cm.has(m));});
air.dispose();assert.equal(air.actors.length,0);assert(!scene.children.includes(air.light));
console.log('PASS actual helicopter GLBs: independent rotor/body/socket transforms, optical aim, pause/hidden/result/reset, Lite blur budget, material isolation and disposal. No GPU rendering.');
