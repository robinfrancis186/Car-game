import assert from 'node:assert/strict';
import * as THREE from 'three';
import {TransitPath,shuttleState,ScenicTransit} from '../src/transit.js';
const path=new TransitPath([[0,13,0],[100,13,0],[200,18,50]]);
assert.equal(path.sample(0).position.y,13);assert.equal(path.sample(path.length).position.y,18);assert(path.sample(150).pitch>0);assert.throws(()=>new TransitPath([[0,0,0],[0,0,0]]));
const length=1000,speed=15,dwell=8,margin=31,travel=1.5*(length-2*margin)/speed,period=2*(travel+dwell);
assert.equal(shuttleState(0,length,speed,dwell,margin).moving,false);assert.equal(shuttleState(dwell,length,speed,dwell,margin).velocityMps,0);
assert(Math.abs(shuttleState(dwell+travel/2,length,speed,dwell,margin).velocityMps-speed)<1e-8);
assert.equal(shuttleState(dwell+travel+.1,length,speed,dwell,margin).moving,false);
assert.equal(shuttleState(period,length,speed,dwell,margin).distance,margin);
let previous=shuttleState(0,length,speed,dwell,margin);for(let i=1;i<period*120;i++){const next=shuttleState(i/120,length,speed,dwell,margin);assert(Math.abs(next.distance-previous.distance)<=speed/120+.0001);assert(next.distance>=margin&&next.distance<=length-margin);previous=next;}
const template=new THREE.Group();for(const [i,x] of [19.4,0,-19.4].entries()){const car=new THREE.Group();car.name='TrainCar_'+i;car.position.x=x;car.add(new THREE.Mesh(new THREE.BoxGeometry(18,3,2.9),new THREE.MeshStandardMaterial()));template.add(car);}
const transit=new ScenicTransit(template,{id:'metro',asset:'CoastMetroTrain',type:'metro',points:[[0,13,0],[100,13,0],[200,13,60]],speed_mps:15},new THREE.Scene());transit.update(20,1/60);assert.equal(transit.carriages.length,3);assert.equal(transit.colliderProxies.length,3);for(const p of transit.colliderProxies){assert.equal(p.shape,'capsule');assert.equal(p.y,13);assert(Object.values(p).filter(x=>typeof x==='number').every(Number.isFinite));}
assert(transit.carriages[0].pivot.position.x>transit.carriages[2].pivot.position.x);
const ferry=new ScenicTransit(new THREE.Group(),{id:'ferry',asset:'CoastWaterFerry',points:[[0,.015,0],[500,.015,20]],speed_mps:5},new THREE.Scene());for(let i=0;i<1000;i++){ferry.update(i/60,1/60);assert(ferry.group.position.toArray().every(Number.isFinite));assert(Math.abs(ferry.group.rotation.x)<.006);}
console.log('PASS transit path grades, continuous smooth shuttle/dwells, peak-speed bound, three independent carriage pivots, finite capsule proxies and restrained ferry bob. Scene-graph tests, not WebGL.');

// Pause freezes visual smoothing as well as the absolute shuttle clock.
const heldTime=24.75;ferry.update(heldTime,1/60);const frozen=ferry.group.matrix.clone();ferry.group.updateMatrix();const before=ferry.group.matrix.clone();for(let i=0;i<120;i++)ferry.update(heldTime,0);ferry.group.updateMatrix();assert.deepEqual(ferry.group.matrix.elements,before.elements);
// Collision velocity follows track movement, not the smoothed body heading.
const turnFerry=new ScenicTransit(new THREE.Group(),{id:'turn-ferry',asset:'ferry',type:'ferry',points:[[0,0,0],[100,0,0],[100,0,100]],speed_mps:12},new THREE.Scene());
turnFerry.update(20.25,1/120);const motion=turnFerry.state, tangent=turnFerry.path.sample(motion.distance),proxy=turnFerry.colliderProxies[0];assert(Math.abs(proxy.velocityX-Math.cos(tangent.heading)*motion.velocityMps)<1e-9);assert(Math.abs(proxy.velocityZ-Math.sin(tangent.heading)*motion.velocityMps)<1e-9);
console.log('PASS transit pause freezes rotation and collision velocity follows actual path tangent.');
