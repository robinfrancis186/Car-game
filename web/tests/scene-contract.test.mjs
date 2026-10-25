import {CAR_IDS,CAR_CATALOG} from '../src/garage.js';
// Actual GLTFLoader + Three scene-graph integration; this does NOT render WebGL.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
globalThis.document={baseURI:'http://localhost/'};
globalThis.window={};globalThis.self=globalThis;
// Header-only image shim for scene graph tests; not texture decode/GPU evidence.
globalThis.createImageBitmap??=async blob=>{const b=Buffer.from(await blob.arrayBuffer());assert.equal(b.toString('hex',0,8),'89504e470d0a1a0a');return{width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}};};
globalThis.ProgressEvent=class ProgressEvent{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const {CoastRenderer,normalizeWorldData}=await import('../src/scene.js');
const {GameModel}=await import('../src/gameplay.js');
const root=new URL('../public/assets/',import.meta.url),loader=new GLTFLoader();
const load=async name=>{const b=await fs.readFile(new URL(name,root));return(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'' )).scene;};
const car=Object.create(CoastRenderer.prototype);
car.models=Object.fromEntries(await Promise.all([...Object.values(CAR_CATALOG).map(v=>v.asset),'police_lightbar.glb','ArcadeBoostNozzle.glb'].map(async f=>[f,await load(f)])));
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
car.garageModel=await load('ServiceShowroomLoft.glb');car.garageModel.position.set(10000,0,10000);car.scene.add(car.garageModel);car.garageLights=new THREE.Group();car.scene.add(car.garageLights);
car.setGarageMode(true);assert.equal(car.sun.intensity,.55);assert.equal(car.hemisphere.intensity,.9);
for(const aspect of [1180/757,390/844,844/390]){car.camera.aspect=aspect;car.cameraReset=true;car.update(game,1/60,{menu:true,menuTime:0});car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);assert(car.garageModel.visible&&car.garageLights.visible);assert.equal(car.cars[0].group.position.x,10000);const focus=car.cars[0].group.position.clone().add(new THREE.Vector3(0,.7,0)),ray=new THREE.Raycaster(car.camera.position,focus.clone().sub(car.camera.position).normalize(),0,focus.distanceTo(car.camera.position)-.25);assert.equal(ray.intersectObject(car.garageModel,true).length,0,'Open-front showroom camera reaches car without wall obstruction');}
car.setGarageMode(false);car.update(game,1/60,{menu:true});assert(!car.garageModel.visible&&!car.garageLights.visible);assert.equal(car.sun.intensity,3.1);assert.equal(car.hemisphere.intensity,2);assert.notEqual(car.cars[0].group.position.x,10000);
console.log('PASS actual showroom GLB, open-front camera center rays at three aspect ratios, isolated hero stage and lighting restoration. No rendered-image claim.');

// 360 inspection rotates the display turntable, not the camera through walls.
// The gameplay model remains unchanged and the car stays inside its UI viewport.
const savedPlayer=JSON.stringify(game.player);car.setGarageMode(true);
for(const variant of CAR_IDS){car.setPlayerCar(variant);
for(const [w,h,bounds] of [[1180,757,{left:40,top:100,width:620,height:500}],[390,844,{left:20,top:80,width:350,height:250}],[320,568,{left:10,top:65,width:300,height:150}]]){
 car.canvas={getBoundingClientRect:()=>({left:0,top:0,width:w,height:h})};car.camera.aspect=w/h;car.setGarageViewBounds(bounds);
 for(let i=0;i<24;i++){car.orbitGarage(Math.PI/12,i%2?.02:-.02);car.update(game,1,{menu:true});car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);const b=new THREE.Box3().setFromObject(car.cars[0].body);for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new THREE.Vector3(x,y,z).project(car.camera),sx=(p.x+1)*w/2,sy=(1-p.y)*h/2;assert(sx>=bounds.left-1&&sx<=bounds.left+bounds.width+1&&sy>=bounds.top-1&&sy<=bounds.top+bounds.height+1,`360 car outside showcase ${w}x${h}: ${sx},${sy}`);}const center=car.cars[0].group.position.clone().add(new THREE.Vector3(0,.65,0)),ray=new THREE.Raycaster(car.camera.position,center.clone().sub(car.camera.position).normalize(),0,center.distanceTo(car.camera.position)-.3);assert.equal(ray.intersectObject(car.garageModel,true).length,0,'Turntable camera remains outside blocking walls');}
}
}
assert.equal(JSON.stringify(game.player),savedPlayer);car.orbitGarage(0,999);assert.equal(car.garagePitch,.4);car.orbitGarage(0,-999);assert.equal(car.garagePitch,.1);car.resetGarageView();assert.equal(car.garageYaw,0);assert.equal(car.garagePitch,.21);car.setGarageMode(false);car.update(game,1/60);assert(!car.camera.view?.enabled);assert.equal(car.orbitGarage(1,1),false);
console.log('PASS catalog-derived actual car/showroom 360 poses inside desktop/portrait/short-portrait viewport bounds; no showroom occlusion, model mutation or projection state leak. Scene graph only.');

car.setPlayerCar('touring');assert.equal(car.cars.length,6);assert.equal(car.cars[0].variant,'touring');assert.equal(car.cars[0].steer.filter(Boolean).length,4);assert.equal(car.cars[0].spin.filter(Boolean).length,4);assert(car.cars[0].boostFire);game.player.steer=.6;game.player.stuntRoll=0;game.player.flipActive=false;car.update(game,1/60);assert.equal(car.cars[0].steer[0].rotation.y,-.45);assert.equal(car.cars[0].jets.length,4);car.setPlayerCar('silver');car.setPlayerCar('red');assert.equal(car.cars.length,6);console.log('PASS actual touring car GLB, six-car indexing, independent wheel animation, validated .45rad steering limit, cosmetic flame attachment and variant swaps.');

// All three bonnet cameras must have a clear central forward view of the road.
car.setGarageMode(false);game.player.flying=false;game.player.flipActive=false;game.player.stuntRoll=0;game.player.bodyPitch=0;game.player.bodyRoll=0;game.player.suspension=0;for(const variant of CAR_IDS){car.setPlayerCar(variant);car.cameraMode=1;car.cameraReset=true;car.update(game,1/60);car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);const ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(0,0),car.camera);ray.far=10;assert.equal(ray.intersectObject(car.cars[0].body,true).length,0,variant+' bonnet center view must not be blocked by own hood');}console.log('PASS actual all-catalog-car bonnet center sightline clearance.');

// Actual runtime paint must preserve the Touring silver/blue interpretation.
// The shared paint slot may be recolored, but must not inherit Crimson's red.
for(const [variant,color] of CAR_IDS.map(id=>[id,CAR_CATALOG[id].displayColor.slice(1)])){
 car.setPlayerCar(variant);let paint=0,livery=0;car.cars[0].body.traverse(o=>{if(!o.isMesh)return;for(const m of Array.isArray(o.material)?o.material:[o.material]){if(m.name===car.carInfo.paint_material){paint++;assert.equal(m.color.getHexString(),color,variant+' runtime body paint');}if(m.name==='Azure Touring | cobalt geometric livery'){livery++;assert.equal(m.color.getHexString(),'1d4299','Touring blue livery must not be recolored');}}});assert(paint>0);if(variant==='touring')assert(livery>0);
}
console.log('PASS exact runtime red/silver/Touring paint colors and preserved Touring blue livery after real variant swaps.');

// Reconstructed Home uses a real isolated showroom car, framed to its DOM slot.
car.setGarageMode(false);car.cameraMode=0;const homeSaved=JSON.stringify(game.player);
for(const variant of CAR_IDS){car.setPlayerCar(variant);
 for(const [w,h,bounds] of [[1180,757,{left:425,top:136,width:708,height:439}],[390,844,{left:19.5,top:295.4,width:351,height:194.12}],[320,568,{left:16,top:198.8,width:288,height:130.64}]]){
  car.canvas={getBoundingClientRect:()=>({left:0,top:0,width:w,height:h})};car.camera.aspect=w/h;car.setHomeViewBounds(bounds);car.setHomeMode(true);car.update(game,2,{menu:true});car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);
  assert.equal(car.garageMode,false);assert(car.garageModel.visible);assert.equal(car.cars[0].group.position.x,10000);
  const box=new THREE.Box3().setFromObject(car.cars[0].body);for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){const q=new THREE.Vector3(x,y,z).project(car.camera),sx=(q.x+1)*w/2,sy=(1-q.y)*h/2;assert(sx>=bounds.left-1&&sx<=bounds.left+bounds.width+1&&sy>=bounds.top-1&&sy<=bounds.top+bounds.height+1,`Home framing ${variant} ${w}: ${sx},${sy}`);}
 }
}
assert.equal(JSON.stringify(game.player),homeSaved);car.setGarageMode(true);assert(!car.homeMode);assert(car.garageMode);car.setHomeMode(true);assert(!car.garageMode);car.setHomeMode(false);car.update(game,1/60);assert(!car.camera.view?.enabled);assert.equal(car.sun.intensity,3.1);assert.equal(car.hemisphere.intensity,2);assert(!car.garageModel.visible);
console.log('PASS Home actual-car scene framing at desktop/portrait/short portrait, mode exclusivity, lighting restore and no gameplay mutation. No pixel-render claim.');

// Every actual owned/purchasable model must register only rear emissive lamps.
for(const variant of CAR_IDS){car.setPlayerCar(variant);assert(car.cars[0].brakeLights.length>0,variant+' requires runtime brake lamps');if(variant==='midnight')assert(car.cars[0].brakeLights.every(m=>m.name==='Midnight rear vermilion lights'));}
console.log('PASS all catalogue rear brake lamps registered; Midnight running lamps/accents excluded.');

// V13 live installed finishes are per-car, persistent-input driven, and independent of boost/pause.
const otherMaterials=car.cars.slice(1).flatMap(v=>Object.values(v.upgradeVisuals).flat().map(b=>[b.material,b.material.color.getHexString(),b.material.roughness]));
let upgradePoses=0;
for(const variant of CAR_IDS){car.setPlayerCar(variant);const v=car.cars[0],pivots=v.steer.map(o=>o.position.clone());assert(v.upgradeVisuals.calipers.length>=4,variant+' four caliper finishes');
 for(let level=0;level<=3;level++){const upgrades={braking:level,handling:level,speed:level,acceleration:level,boost:level};car.setPlayerUpgrades(upgrades);car.update(game,0,{menu:true});const expected=['d63232','d63232','ff8b2f','9c65ff'][level];assert(v.upgradeVisuals.calipers.every(b=>b.material.color.getHexString()===expected));assert.equal(v.aeroTrimAngle,level*.012);pivots.forEach((p,i)=>assert(v.steer[i].position.equals(p)));if(v.wing)assert(Math.abs(v.wing.rotation.z+level*.012)<1e-8);upgradePoses++;}
 car.setPlayerUpgrades({});assert(v.upgradeVisuals.calipers.every(b=>b.material.color.getHexString()==='d63232'));
}
for(const[m,color,roughness]of otherMaterials){assert.equal(m.color.getHexString(),color);assert.equal(m.roughness,roughness);}
const pose={position:[100,50,200],target:[110,0,210],fov:57};assert(car.setCinematicCamera(pose));pose.position[0]=0;car.update(game,0);assert.deepEqual(car.camera.position.toArray(),[100,50,200]);assert.equal(car.camera.fov,57);assert(!car.setCinematicCamera({position:[NaN,0,0],target:[0,0,0],fov:60}));assert(car.setCinematicCamera(null));car.update(game,0);assert.notEqual(car.camera.position.x,100);
console.log(`PASS ${upgradePoses} actual seven-car installed brake/aero/finish states, no wheel pivot or rival material mutation; exact dt=0 cinematic pose and clean camera restoration. No WebGL claim.`);
const{createCinematicShot}=await import('../src/cinematic-camera.js');let cinematicBounds=0;
game.player.flying=false;game.player.altitude=0;game.player.flipActive=false;game.player.stuntRoll=0;game.player.bodyRoll=0;game.player.bodyPitch=0;
for(const variant of CAR_IDS){car.setPlayerCar(variant);for(const aspect of [1180/757,390/844,320/568,844/390]){car.camera.aspect=aspect;for(const kind of ['intro','finish']){const shot=createCinematicShot(kind,game);for(const fraction of [0,.25,.5,.75,1]){car.setCinematicCamera(shot.sample(shot.duration*fraction));car.update(game,0);car.scene.updateMatrixWorld(true);car.camera.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(car.cars[0].body);for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const p=new THREE.Vector3(x,y,z).project(car.camera);assert(Math.abs(p.x)<.96&&Math.abs(p.y)<.96&&p.z>-1&&p.z<1,`${variant} ${kind} cinematic framing`);}cinematicBounds++;}}}}
car.setCinematicCamera(null);console.log(`PASS ${cinematicBounds} actual seven-car intro/finish body bounds inside desktop/mobile camera frusta. Geometry, not rendered pixels.`);

for(const variant of CAR_IDS){car.setPlayerCar(variant);const v=car.cars[0],actual=[];v.boostFire.group.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])if(/nozzle/i.test(m.name)&&m.color)actual.push(m);});assert(actual.length>=2);assert(actual.every(m=>v.upgradeVisuals.nozzles.some(b=>b.material===m)));const before=actual.map(m=>m.color.getHexString());car.setPlayerUpgrades({boost:3});assert(actual.every((m,i)=>m.color.getHexString()!==before[i]));car.setPlayerUpgrades({});assert(actual.every((m,i)=>m.color.getHexString()===before[i]));}
console.log('PASS all7 actual attached boost-nozzle metals register after construction, visibly change atboost3 and restore without flame-color changes.');
