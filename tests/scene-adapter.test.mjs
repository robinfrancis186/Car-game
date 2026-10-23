/** Actual GLTFLoader + Three scene graph. NOT browser/WebGL/GPU acceptance. */
import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';
import * as THREE from 'three';import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OnlineRenderAdapter,configureOnlineRenderer} from '../client/render-adapter.mjs';
import {authoritativeFixture,route,IDs} from './parity-fixture.mjs';
globalThis.document={baseURI:'http://localhost/'};globalThis.window={};globalThis.ProgressEvent=class{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const {CoastRenderer}=await import('../game/scene.js'),root=new URL('../public/assets/',import.meta.url),loader=new GLTFLoader();
const load=async name=>{const b=await fs.readFile(new URL(name,root));return(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;};
test('actual Three renderer consumes authoritative two-seat poses, wheel/ground/camera/checkpoint contract without duplicates',async()=>{
 const r=Object.create(CoastRenderer.prototype);
 r.models=Object.fromEntries(await Promise.all(['car.glb','car_silver.glb','car_touring.glb','police_lightbar.glb','ArcadeBoostNozzle.glb'].map(async f=>[f,await load(f)])));r.carInfo=JSON.parse(await fs.readFile(new URL('car_manifest.json',root)));
 let renders=0;Object.assign(r,{scene:new THREE.Scene(),cars:[],waterShaders:[],windShaders:[],environmentChunks:[],clock:0,world:JSON.parse(await fs.readFile(new URL('course_runtime.json',root))),camera:new THREE.PerspectiveCamera(),sun:new THREE.DirectionalLight(),sky:new THREE.Object3D(),cameraMode:0,cameraReset:true,orbitYaw:0,orbitPitch:0,quality:'high',renderer:{render(){renders++;}}});
 r.addCar('#b61920',false);for(const c of ['#fff','#fba','#abc'])r.addCar(c,false);r.addCar('#ddd',true);r.addCar('#222',true);r.makeEffects();r.checkpointMarker=await load('CheckpointGate.glb');r.scene.add(r.checkpointMarker);configureOnlineRenderer(r);
 const adapter=new OnlineRenderAdapter(route),{snapshot:s}=authoritativeFixture();s.players[0].steer=.2;s.players[0].speed=10;s.players[1].x+=3;s.players[1].groundNormalX=.15;s.players[1].groundNormalY=Math.sqrt(1-.15**2);assert(adapter.accept(s,IDs[0],0));
 for(let i=0;i<20;i++){
  const m=adapter.frame(i*16,1/60);r.update(m,1/60);assert.equal(r.cars.length,6);assert.equal(r.cars.filter(c=>c.group.visible).length,2);assert.equal(r.cars[0].group.position.x,m.player.x);assert.equal(r.cars[1].group.position.x,m.rivals[0].x);assert(r.camera.position.toArray().every(Number.isFinite));assert.equal(r.checkpointMarker.position.x,m.checkpoints[m.nextCheckpoint].x);
  assert.equal(m.rivals[0].id,IDs[1]);assert(m.rivals[0].onlineHuman);assert.equal(m.police.length,0);assert.equal(m.coins.length,0);assert.equal(m.paused,false);assert.throws(()=>m.update(.01,{}),/FORBIDDEN/);assert.throws(()=>m.recover(),/FORBIDDEN/);
 }
 assert.equal(renders,20);assert.equal(r.cars[0].steer[0].rotation.y,-.2);assert.notEqual(r.cars[0].spin[0].rotation.z,0);assert.notEqual(r.cars[1].group.quaternion.z,0);assert(r.cars.slice(2).every(c=>!c.group.visible));assert.equal(r.transit.length,0);assert.equal(r.dynamicObstacles.length,0);assert.equal(r.cars[0].variant,'red');
});

test('every coast renderer dependency is in exact public allowlist; car manifest excludes source/reference notes',async()=>{
 const raw=JSON.parse(await fs.readFile(new URL('course_runtime.json',root))),w={...raw,...raw.world},props=[...new Set(w.prop_instances.map(p=>p.asset))];
 const files=[...w.course_meshes.map(p=>p.file),...props.map(n=>n+'.glb'),'car.glb','car_silver.glb','car_touring.glb','police_lightbar.glb','CheckpointGate.glb','ServiceShowroomBay.glb','ArcadeBoostNozzle.glb','ArcadeCoin.glb','car_manifest.json',w.furniture_file||'furniture_colliders.json',w.collision_file,...(props.includes('CanalRainTree')?['CanalRainTreeFar.glb']:[]),...(w.transit_routes||[]).map(r=>r.asset+'.glb')].filter(Boolean);
 const allow=JSON.parse(await fs.readFile(new URL('../public-manifest.json',import.meta.url))).files;for(const name of files)assert(allow.some(f=>f.path==='assets/'+name),'missing renderer dependency '+name);
 assert.deepEqual(Object.keys(JSON.parse(await fs.readFile(new URL('car_manifest.json',root)))).sort(),['paint_material','spin_nodes','steer_nodes']);
});
