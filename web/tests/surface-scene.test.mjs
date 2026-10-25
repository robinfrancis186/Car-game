// Actual shipped GLBs, analytic contact model and renderer scene graph; no GPU.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
import {StuntGameModel} from '../src/stunt-model.js';
import {CAR_IDS} from '../src/garage.js';
globalThis.document={baseURI:'http://localhost/'};globalThis.self=globalThis;
globalThis.createImageBitmap??=async blob=>{const b=Buffer.from(await blob.arrayBuffer());assert.equal(b.toString('hex',0,8),'89504e470d0a1a0a');return{width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}};};
globalThis.ProgressEvent=class{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const directory=new URL('../public/assets/',import.meta.url),assets={};
for(const n of await fs.readdir(directory)){if(!/\.(glb|json)$/.test(n))continue;const b=await fs.readFile(new URL(n,directory));assets[n]=`data:${n.endsWith('.glb')?'model/gltf-binary':'application/json'};base64,${b.toString('base64')}`;}
globalThis.window={__MALABAR_ASSETS__:assets};
const {CoastRenderer}=await import('../src/scene.js');const r=Object.create(CoastRenderer.prototype);
Object.assign(r,{worldFile:'course_runtime_surface_test.json',scene:new THREE.Scene(),onProgress(){},cars:[],environmentChunks:[],waterShaders:[],windShaders:[],windowMaterials:[],clock:0,worldTime:0,camera:new THREE.PerspectiveCamera(65,390/844,.1,6500),sun:new THREE.DirectionalLight(),sky:new THREE.Object3D(),cameraMode:0,cameraReset:true,orbitYaw:0,orbitPitch:.12,quality:'balanced',renderer:{render(){}}});await r.load();assert.equal(r.infrastructureColliders.length,68,'Actual renderer loads exact authored structure proxies');
assert.equal(r.world.id,'surface-test');assert(r.route.length>100);assert.equal(r.transit.length,0);assert.equal(r.airTraffic,undefined);assert.equal(r.waterSurface.length,0);assert(r.models['SurfaceTest_Road.glb']);
let poses=0,rays=0,maxWheelSurfaceError=0;const ray=new THREE.Raycaster(),road=r.models['SurfaceTest_Road.glb'];
for(const id of CAR_IDS){r.setPlayerCar(id);const m=new StuntGameModel(r.route,{surfaceProfile:r.world.surface_profile,vehicleId:id}).start('free-drive');
 for(const s of [50,180,220,260,300,340,400,500,580,620,680,720,800])for(const mode of [0,1,2]){
  m.surfaceDrive.reset({s,speed:30});m._sync();r.cameraMode=mode;r.cameraReset=true;r.update(m,0);r.scene.updateMatrixWorld(true);r.camera.updateMatrixWorld(true);const p=m.player,v=r.cars[0],up=new THREE.Vector3(...p.surfaceFrame.up),actualUp=new THREE.Vector3(0,1,0).applyQuaternion(v.group.quaternion);assert(actualUp.distanceTo(up)<1e-10);assert(r.cars.slice(1).every(c=>!c.group.visible));assert(v.contactShadow.visible);assert(v.contactShadow.position.distanceTo(new THREE.Vector3(...p.supportPoint).addScaledVector(new THREE.Vector3(...p.supportNormal),.014))<1e-9);assert(r.camera.up.distanceTo(up)<1e-9);assert(r.camera.quaternion.toArray().every(Number.isFinite));
  for(const wheel of v.spin){const center=new THREE.Vector3();wheel.getWorldPosition(center);ray.set(center.clone().addScaledVector(up,.5),up.clone().negate());const hit=ray.intersectObject(road,true)[0];assert(hit,'Actual tire center must cast onto authored deck');let lowest=Infinity;wheel.traverse(o=>{if(!o.isMesh)return;const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++){const point=new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);lowest=Math.min(lowest,point.clone().sub(hit.point).dot(up));}});maxWheelSurfaceError=Math.max(maxWheelSurfaceError,Math.abs(lowest));assert(Math.abs(lowest)<.075,`${id} s${s} wheel-plane error ${lowest}`);rays++;}
  poses++;
 }
 m.surfaceDrive.reset({s:420,speed:30});m._sync();r.cameraMode=0;r.cameraReset=true;r.update(m,0);assert(Math.abs(r.camera.up.z)>.999);r.update(m,0,{menu:true,menuTime:0});assert(r.camera.up.distanceTo(new THREE.Vector3(0,1,0))<1e-12);assert(r.cars[0].group.quaternion.angleTo(new THREE.Quaternion())<1e-8,'Menu must not inherit the wall pose');
}
const report={result:'PASS',scope:'Actual GLB scene/model contact and camera transforms; no GPU/textures/native steering evidence',poses,rays,maxWheelSurfaceErrorMetres:maxWheelSurfaceError};await fs.mkdir(new URL('../../tests/v16/',import.meta.url),{recursive:true});await fs.writeFile(new URL('../../tests/v16/surface_scene_metrics.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(report);
