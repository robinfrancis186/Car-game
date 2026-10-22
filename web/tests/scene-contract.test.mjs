// Actual GLTFLoader + Three scene-graph integration; this does NOT render WebGL.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
globalThis.document={baseURI:'http://localhost/'};
globalThis.window={};
globalThis.ProgressEvent=class ProgressEvent{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const {CoastRenderer,normalizeWorldData}=await import('../src/scene.js');
const {GameModel}=await import('../src/gameplay.js');
const root=new URL('../public/assets/',import.meta.url),loader=new GLTFLoader();
const load=async name=>{const b=await fs.readFile(new URL(name,root));return(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'' )).scene;};
const car=Object.create(CoastRenderer.prototype);
car.models=Object.fromEntries(await Promise.all(['car.glb','car_silver.glb','police_lightbar.glb'].map(async f=>[f,await load(f)])));
car.carInfo=JSON.parse(await fs.readFile(new URL('car_manifest.json',root)));
Object.assign(car,{scene:new THREE.Scene(),cars:[],waterShaders:[],windShaders:[],environmentChunks:[],clock:0,world:JSON.parse(await fs.readFile(new URL('course_runtime.json',root))),camera:new THREE.PerspectiveCamera(),sun:new THREE.DirectionalLight(),sky:new THREE.Object3D(),cameraMode:0,cameraReset:true,orbitYaw:0,orbitPitch:0,quality:'high',renderer:{render(){}}});
car.addCar('#b61920',false);for(const c of ['#fff','#fba','#abc'])car.addCar(c,false);car.addCar('#ddd',true);car.addCar('#222',true);car.makeEffects();
assert.equal(car.cars.length,6);assert.equal(car.cars[0].jets.length,4);
for(const c of car.cars){assert.equal(c.spin.filter(Boolean).length,4);assert.equal(c.steer.filter(Boolean).length,4);assert(c.body);}
const water=await load('Course_Water.glb');car.scene.add(water);car.scene.updateMatrixWorld(true);car.waterSurface=[];water.traverse(o=>{if(o.isMesh&&/Ocean/.test(o.material.name))car.waterSurface.push(o);});car.waterRay=new THREE.Raycaster();
assert(car.waterSurface.length>0);let waterProbes=0;for(const mesh of car.waterSurface){const positions=mesh.geometry.attributes.position;for(let i=0;i<positions.count;i+=37){const v=new THREE.Vector3().fromBufferAttribute(positions,i).applyMatrix4(mesh.matrixWorld);if(car.isWater(v.x+.001,v.z+.001))waterProbes++;}}assert(waterProbes>5,'Actual water mesh ray checks');assert.equal(car.isWater(100000,100000),false);
const rivals=car.cars.slice(1);car.setPlayerCar('silver');assert.equal(car.cars.length,6);assert.equal(car.cars[0].variant,'silver');assert.equal(car.cars[0].jets.length,6);assert(car.cars[0].wing);rivals.forEach((r,i)=>assert.equal(car.cars[i+1],r));
const world=normalizeWorldData(JSON.parse(await fs.readFile(new URL('course_runtime.json',root))));const route=world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]}));const game=new GameModel(route,{startS:2200,endS:3350});game.start('coast-sprint');
car.checkpointMarker=await load('CheckpointGate.glb');car.scene.add(car.checkpointMarker);car.update(game,1/60);assert.equal(car.checkpointMarker.position.x,game.checkpoints[1].x);assert.equal(car.checkpointMarker.visible,true);assert.equal(car.cars[4].group.visible,true,'Inactive roadside patrol remains visible');
game.player.steer=.25;game.player.wheelAngle=2;game.player.flying=true;game.player.thrusting=true;game.player.stuntRoll=Math.PI;game.player.bodyRoll=.08;game.player.bodyPitch=.04;game.player.suspension=.018;game.player.y=3;
car.update(game,1/60);assert.equal(car.cars[0].steer[0].rotation.y,-.25);assert.equal(car.cars[0].spin[0].rotation.z,-2);assert(car.cars[0].brakeLights.length>0);assert(car.cars[0].jets.filter(j=>j.down).every(j=>j.mesh.visible));assert(car.cars[0].jets.filter(j=>!j.down).every(j=>!j.mesh.visible));assert.equal(car.cars[0].wing.rotation.z,-.2);assert.equal(car.cars[0].group.position.y,3);assert.equal(car.cars[0].stunt.rotation.x,Math.PI);assert.equal(car.cars[0].chassis.position.y,.002);assert.equal(car.cars[0].chassis.rotation.x,.008);assert.equal(car.cars[0].chassis.rotation.z,.005);assert.equal(car.cars[0].wing.parent,car.cars[0].chassis);
assert(car.camera.position.toArray().every(Number.isFinite));
game.player.steer=.6;game.player.flipActive=true;game.player.stuntPhase='roll';car.update(game,1/60);assert.equal(car.cars[0].steer[0].rotation.y,-.4);assert(car.cars[0].jets.filter(j=>j.down&&j.side<0).every(j=>j.mesh.visible));assert(car.cars[0].jets.filter(j=>j.down&&j.side>0).every(j=>!j.mesh.visible));game.player.stuntPhase='counterthrust';car.update(game,1/60);assert(car.cars[0].jets.filter(j=>j.down&&j.side>0).every(j=>j.mesh.visible));assert(car.cars[0].jets.filter(j=>j.down&&j.side<0).every(j=>!j.mesh.visible));
game.player.flipActive=false;game.player.stuntRoll=0;game.player.stuntPhase=null;car.orbitYaw=1.8;car.cameraReset=true;car.update(game,1/60);car.camera.updateMatrixWorld(true);const screen=new THREE.Vector3(game.player.x,game.player.y+.65,game.player.z).project(car.camera);assert(Math.abs(screen.x)<.05,'Orbit must keep car centered');assert.equal(car.cars[0].contactShadow.visible,true);car.orbitYaw=0;
for(let i=0;i<3;i++){car.cycleCamera();car.update(game,1/60);assert(car.camera.position.toArray().every(Number.isFinite));}
car.setPlayerCar('red');assert.equal(car.cars[0].jets.length,4);game.player.flipActive=true;game.player.stuntRoll=Math.PI;game.player.stuntPhase='roll';game.player.altitude=3;game.player.offRoad=true;car.update(game,1/60,{menu:true,menuTime:5});assert(car.cars.slice(1).every(c=>!c.group.visible));assert(car.cars[0].jets.every(j=>!j.mesh.visible));assert.equal(car.cars[0].stunt.rotation.x,0);assert(Math.abs(car.cars[0].contactShadow.position.y-(game.sampleRoute(Math.min(car.world.garage_s??2550,game.routeLength)).y+.014))<1e-8);
const hot=new GameModel(route,{startS:2200,endS:4350}).start('hot-pursuit');car.update(hot,1/60);assert.equal(car.sirenGlow.intensity,2.5);car.update(hot,1/60,{menu:true});assert.equal(car.sirenGlow.intensity,0);hot.start('time-attack');car.update(hot,1/60);assert.equal(car.sirenGlow.intensity,0);
console.log('PASS: actual GLB parse, both car variants, wheel pivots/rotation signs, six-car indexing, police visibility, next-checkpoint placement, actual water-surface raycasts, thruster/wing animation, camera transforms, menu hide, car swaps. WebGL rendering NOT tested here.');

// Portrait framing uses the actual car graph, not a placeholder box.
car.camera.aspect=390/844;car.cameraReset=true;car.update(game,1/60,{menu:true,menuTime:0});car.camera.updateMatrixWorld(true);car.cars[0].group.updateMatrixWorld(true);
const heroBounds=new THREE.Box3().setFromObject(car.cars[0].group);for(const x of [heroBounds.min.x,heroBounds.max.x])for(const y of [heroBounds.min.y,heroBounds.max.y])for(const z of [heroBounds.min.z,heroBounds.max.z]){const p=new THREE.Vector3(x,y,z).project(car.camera);assert(Math.abs(p.x)<.95,'Portrait hero car should not be clipped horizontally');assert(Math.abs(p.y)<.95,'Portrait hero car should not be clipped vertically');}
console.log('PASS actual-car portrait garage frustum bounds at390×844 (scene graph only).');

if(world.version==='v8-kerala-infrastructure'){
 assert.equal(world.transit_routes.length,2,'Both transit routes must survive runtime normalization');assert.equal(world.districts.length,5,'All district labels must survive normalization');
 for(const config of world.transit_routes){const template=await load(config.asset+'.glb');assert(template.children.length>0,'Actual transit GLB must parse');}
 assert(world.elevated_corridors.length>0);assert.equal(Math.max(...world.route_points.map(p=>p[1])),10);
 console.log('PASS V8 metadata normalization, two actual transit GLBs, five districts and10m elevated profile.');
}

const clockBefore=car.clock;game.setPaused(true);car.vaporAge=.2;car.update(game,1/60);assert.equal(car.clock,clockBefore);assert.equal(car.vaporAge,.2);game.setPaused(false);car.update(game,1/60);assert(car.clock>clockBefore);console.log('PASS paused water/leaf animation and landing vapor clocks freeze; resume advances.');

// Original showroom is a real parsed asset; lighting and camera state restore.
car.hemisphere=new THREE.HemisphereLight();car.sun.intensity=3.1;car.hemisphere.intensity=2;
car.garageModel=await load('ServiceShowroomBay.glb');car.garageModel.position.set(10000,0,10000);car.scene.add(car.garageModel);car.garageLights=new THREE.Group();car.scene.add(car.garageLights);
car.setGarageMode(true);assert.equal(car.sun.intensity,.55);assert.equal(car.hemisphere.intensity,.9);
for(const aspect of [1180/757,390/844,844/390]){car.camera.aspect=aspect;car.cameraReset=true;car.update(game,1/60,{menu:true,menuTime:0});car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);assert(car.garageModel.visible&&car.garageLights.visible);assert.equal(car.cars[0].group.position.x,10000);const focus=car.cars[0].group.position.clone().add(new THREE.Vector3(0,.7,0)),ray=new THREE.Raycaster(car.camera.position,focus.clone().sub(car.camera.position).normalize(),0,focus.distanceTo(car.camera.position)-.25);assert.equal(ray.intersectObject(car.garageModel,true).length,0,'Open-front showroom camera reaches car without wall obstruction');}
car.setGarageMode(false);car.update(game,1/60,{menu:true});assert(!car.garageModel.visible&&!car.garageLights.visible);assert.equal(car.sun.intensity,3.1);assert.equal(car.hemisphere.intensity,2);assert.notEqual(car.cars[0].group.position.x,10000);
console.log('PASS actual showroom GLB, open-front camera center rays at three aspect ratios, isolated hero stage and lighting restoration. No rendered-image claim.');
