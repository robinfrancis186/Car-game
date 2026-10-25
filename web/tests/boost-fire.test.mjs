import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {ArcadeBoostFire,BOOST_FIRE_MOUNTS,BOOST_FIRE_COLORS} from '../src/boost-fire.js';
globalThis.ProgressEvent=class{constructor(t,f){Object.assign(this,f)}};
const bytes=await fs.readFile(new URL('../public/assets/ArcadeBoostNozzle.glb',import.meta.url));
const template=(await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')).scene;
const root=new T.Group(),stunt=new T.Group(),chassis=new T.Group();root.add(stunt);stunt.add(chassis);const fire=new ArcadeBoostFire(chassis,template);
assert.equal(fire.emitters.length,2);assert.equal(fire.emitters.reduce((n,e)=>n+e.flames.length,0),2);
assert(fire.emitters.every(e=>!e.flames[0].visible));
for(let i=0;i<60;i++)fire.update({boosting:true,speed:35},1/60);
assert(fire.strength>.99);assert.equal(fire.mode,'regular');assert.equal(fire.light.color.getHexString(),'ff5308');assert(fire.light.intensity>2);
for(const e of fire.emitters){assert(e.flames[0].visible);assert.equal(e.material.uniforms.outerColor.value.getHexString(),'ff5308');const rootX=e.flames[0].position.x-.08*e.flames[0].scale.x;assert(Math.abs(rootX+.08)<1e-7,'Flame root remains at the nozzle opening when length scales');}
fire.update({ultraBoosting:true,speed:97},1/60);assert.equal(fire.mode,'ultra');assert.equal(fire.light.color.getHexString(),'7120ff');assert(fire.emitters[0].flames[0].scale.x>1.5);
root.updateMatrixWorld(true);let lowest=Infinity;for(const e of fire.emitters)for(const f of e.flames){const a=f.geometry.attributes.position;for(let i=0;i<a.count;i++)lowest=Math.min(lowest,new T.Vector3().fromBufferAttribute(a,i).applyMatrix4(f.matrixWorld).y);}assert(lowest>.02,`Flat-ground ultra cards remain above pavement: ${lowest}`);
for(const heading of [0,1.3,-2.1])for(const roll of [0,Math.PI/2,Math.PI])for(const pitch of [-.15,.12]){root.position.set(12,6,-9);root.rotation.set(0,-heading,pitch);stunt.rotation.x=roll;chassis.rotation.set(.008,0,.005);root.updateMatrixWorld(true);for(let i=0;i<2;i++){const e=fire.emitters[i],expected=new T.Vector3(...BOOST_FIRE_MOUNTS[i]).applyMatrix4(chassis.matrixWorld),actual=e.mount.getWorldPosition(new T.Vector3());assert(expected.distanceTo(actual)<1e-10,'Mount follows yaw, grade, flip and chassis pose');const dir=new T.Vector3(-1,0,0).transformDirection(e.mount.matrixWorld),basis=new T.Vector3(-Math.cos(Math.PI/60),-Math.sin(Math.PI/60),0).transformDirection(chassis.matrixWorld);assert(dir.distanceTo(basis)<1e-10);}}
const pausedClock=fire.clock;fire.update({ultraBoosting:true},.1,{paused:true});assert.equal(fire.clock,pausedClock);assert.equal(fire.strength,0);assert.equal(fire.light.intensity,0);assert(fire.emitters.every(e=>!e.flames[0].visible));
fire.update({boosting:true},.1);assert(fire.strength>.9);for(let i=0;i<30;i++)fire.update({},1/60);assert.equal(fire.strength,0);assert.equal(fire.light.intensity,0);
for(const options of [{menu:true},{active:false}]){fire.update({boosting:true},.1);fire.update({boosting:true},.1,options);assert.equal(fire.strength,0);}
fire.update({ultraBoosting:true},.1);fire.reset();assert.equal(fire.strength,0);assert.deepEqual(BOOST_FIRE_COLORS.ultra,['#7120ff','#d554ff','#f4dcff']);
const materials=[...fire.materials];let disposed=0;materials.forEach(m=>m.addEventListener('dispose',()=>disposed++));fire.dispose();fire.dispose();assert.equal(disposed,materials.length);assert.equal(chassis.children.length,0);assert.equal(fire.emitters.length,0);
console.log(`PASS actual Blender boost GLB, two mounts, orange/violet mode, UV root anchoring, car-local yaw/grade/flip, ultra ground clearance ${lowest.toFixed(3)}m, pause/menu/end/reset/fade and dispose. Shader GPU compilation is a separate browser test.`);
