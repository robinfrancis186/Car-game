import assert from 'node:assert/strict';
import * as THREE from 'three';
import {CaptureGameModel,CAPTURE_DURATION,capturePhase,sampleCapturePath,captureWalkPath,captureSegmentBlocked} from '../src/police-capture.js';
import {PoliceCaptureScene} from '../src/police-capture-scene.js';
import {refineCarPaint,refineFacade} from '../src/capture-materials.js';
import {awardResult,resetProfile} from '../src/garage.js';
import {createLeaderboardCandidate} from '../src/leaderboard.js';
const route=Array.from({length:151},(_,i)=>({x:i*10,y:.18,z:0}));
const advance=(m,seconds,input={})=>{for(let i=0;i<Math.ceil(seconds*120);i++)m.update(1/120,input);return m;};
const make=()=>advance(new CaptureGameModel(route).start('hot-pursuit'),3.1);
const m=make();m.rivals=[];
Object.assign(m.police[0],{x:m.player.x-5,z:m.player.z+2,s:m.player.s-5,y:m.player.y,speed:0});
m.arrestProgress=.9999;m.update(1/120,{brake:true});
assert.equal(m.state,'capturing','real boxed-in police detection enters capture');assert.equal(m.result,null);assert.equal(m.capture.officers.length,2);
const frozen=JSON.stringify([m.player,...m.police]),timer=m.timer,first=m.capture;
assert.equal(m.recover(),false);m._end('busted','duplicate');m._end('failed','duplicate');assert.equal(m.capture,first);
m.setPaused(true);advance(m,2,{throttle:1,boost:true,flight:true});assert.equal(m.capture.elapsed,0);assert.equal(m.timer,timer);
m.setPaused(false);advance(m,2,{throttle:1,steer:1,boost:true,flight:true,flip:true});assert.equal(JSON.stringify([m.player,...m.police]),frozen);assert.equal(m.timer,timer);assert.equal(m.capture.phase,'approach');
assert.equal(createLeaderboardCandidate({state:m.state,scenarioId:'hot-pursuit'}),null);
advance(m,CAPTURE_DURATION);assert.equal(m.state,'busted');assert.equal(m.result.state,'busted');assert.equal(m.result.time,timer);assert.equal(m.events.filter(e=>e.type==='busted').length,1);assert.equal(m.events.filter(e=>e.type==='capture-start').length,1);assert.equal(awardResult(resetProfile(),m.result,'capture-test').reward,0);
const result=m.result;advance(m,5);assert.equal(m.result,result);assert.equal(m.events.filter(e=>e.type==='busted').length,1);
m.restart();assert.equal(m.capture,null);assert.equal(m.state,'countdown');
console.log('PASS real police trigger, blocked driving/recovery/repeated terminal triggers, pause, one caught result, frozen race time, no reward or leaderboard eligibility, clean replay.');
for(const heading of [0,Math.PI/2,Math.PI,-Math.PI/2])for(const door of [-1,1]){
 const cars=[{x:0,z:0,heading},{x:6.5,z:2,heading:0}],start={x:-Math.cos(heading)*.15-Math.sin(heading)*door*1.65,z:-Math.sin(heading)*.15+Math.cos(heading)*door*1.65},goal={x:5.95,z:4.2};
 const path=captureWalkPath(start,goal,cars),boxes=cars.map(car=>({car,halfLength:2.9,halfWidth:1.4}));
 for(let i=1;i<path.length;i++)assert(!captureSegmentBlocked(path[i-1],path[i],boxes),'officer path must avoid both cars, including opposite-facing patrols');
}
console.log('PASS vehicle-clear officer paths from both doors at four patrol headings.');
for(const scenario of ['coast-sprint','time-attack','free-drive']){const q=new CaptureGameModel(route).start(scenario);assert.equal(q.capture,null);assert.equal(q.scenario.id,scenario);}
const scene=new THREE.Scene(),visual=new PoliceCaptureScene(scene);const game=make();Object.assign(game.police[0],{x:game.player.x-5,z:game.player.z+2,y:game.player.y,speed:0});game._end('busted','BUSTED');
for(const aspect of [1440/900,390/844,320/568]){
 for(const elapsed of [.7,2.8,4.7,6.7,7.6]){
  game.capture.elapsed=elapsed;visual.update(game);assert(visual.group.visible);assert.equal(visual.officers.filter(o=>o.root.visible).length,2);assert.equal(visual.driver.root.visible,elapsed>3.3);
  const pose=visual.camera(game.capture,aspect),camera=new THREE.PerspectiveCamera(pose.fov,aspect,.1,1000);camera.position.fromArray(pose.position);camera.lookAt(new THREE.Vector3(...pose.target));camera.updateMatrixWorld(true);visual.group.updateMatrixWorld(true);
  visual.group.traverse(o=>{if(o.isMesh){assert(o.geometry.attributes.position.array.every(Number.isFinite));assert(o.matrixWorld.elements.every(Number.isFinite));}});
  for(const actor of visual.officers){const p=actor.root.position.clone();p.y+=.9;p.project(camera);assert(Math.abs(p.x)<.95&&Math.abs(p.y)<.95,`officers remain in frame: aspect=${aspect}, t=${elapsed}, point=${p.toArray()}`);}
  assert.equal(visual.cuffs.visible,elapsed>=6.35);
  if(elapsed>=6.7){visual.group.updateMatrixWorld(true);const cuff=visual.driver.root.localToWorld(new THREE.Vector3(0,.99,-.27));for(const arm of visual.officers[0].arms){const hand=arm.elbow.children.at(-1).getWorldPosition(new THREE.Vector3());assert(hand.distanceTo(cuff)<.07,'arresting officer visibly reaches the secured wrists');}}
 }
}
const count=visual.group.children.length;game._end('busted','repeat');visual.update(game);assert.equal(visual.group.children.length,count);
visual.update(game,{menu:true});assert(!visual.group.visible);game.restart();visual.update(game);assert(!visual.group.visible);visual.dispose();assert(!scene.children.length);
for(const t of [-1,0,.2,1,2])assert(Object.values(sampleCapturePath([{x:0,y:.18,z:0},{x:4,y:.6,z:5}],t)).every(Number.isFinite));
assert.equal(capturePhase(0),'exit');assert.equal(capturePhase(3),'approach');assert.equal(capturePhase(6),'secure');assert.equal(capturePhase(8),'complete');
const paint=new THREE.MeshStandardMaterial({color:'#b61920'});paint.name='test-paint';const refined=refineCarPaint(paint,'test-paint');assert(refined.isMeshPhysicalMaterial);assert.equal(refined.color.getHexString(),'b61920');assert.equal(refined.clearcoat,.72);assert.equal(refineCarPaint(paint,'other'),paint);
const facade=new THREE.MeshStandardMaterial();facade.name='Warm_Lime_Plaster';assert(refineFacade(facade));assert(!refineFacade(facade));const shader={vertexShader:'#include <begin_vertex>',fragmentShader:'#include <color_fragment>'};facade.onBeforeCompile(shader);assert(shader.fragmentShader.includes('fwidth'));assert(shader.vertexShader.includes('vFacadePoint'));
console.log('PASS two articulated officers, visible driver/cuffs and door staging, finite poses, desktop/portrait framing, pooled actors, menu/replay cleanup and bounded paint/facade materials (scene graph; not pixel rendering).');
