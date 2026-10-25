import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {createCinematicShot,validCinematicPose} from '../src/cinematic-camera.js';
import {GameModel,buildCourseObstacles} from '../src/gameplay.js';
import {worldPhysicsOptions} from '../src/tracks.js';
const dir=new URL('../public/assets/',import.meta.url),json=n=>JSON.parse(fs.readFileSync(new URL(n,dir))),raw=json('course_runtime.json'),world={...raw,...raw.world};
const obstacles=buildCourseObstacles(world,[...json(world.furniture_file||'furniture_colliders.json').colliders,...json(world.collision_file).colliders]),route=world.route_points.map(([x,y,z])=>({x,y,z}));
let samples=0;
for(const startS of [165,1265,2200,3350,4350])for(const kind of ['intro','finish']){
 const model=new GameModel(route,{...worldPhysicsOptions(world),obstacles,startS,endS:Math.min(startS+100,4500)}).start('time-attack');const before=JSON.stringify(model.player),timer=model.timer,shot=createCinematicShot(kind,model);let prior;
 for(let i=0;i<=240;i++){const pose=shot.sample(shot.duration*i/240);assert(validCinematicPose(pose));if(prior)assert(Math.hypot(...pose.position.map((v,j)=>v-prior[j]))<.5,'No discontinuous camera travel');prior=pose.position;assert(pose.position[1]>model.sampleTerrain(pose.position[0],pose.position[2]).y+(kind==='finish'?2.49:5.9));
 for(const aspect of [1180/757,390/844,320/568,844/390]){const c=new THREE.PerspectiveCamera(pose.fov,aspect,.12,6500);c.position.fromArray(pose.position);c.lookAt(new THREE.Vector3(...pose.target));c.updateMatrixWorld(true);const point=new THREE.Vector3(model.player.x,model.player.y+.75,model.player.z).project(c);assert(Math.abs(point.x)<1e-8&&Math.abs(point.y)<1e-8);assert(point.z>-1&&point.z<1);}
 samples++;
 }assert.equal(JSON.stringify(model.player),before);assert.equal(model.timer,timer);assert.deepEqual(shot.sample(-10),shot.sample(0));assert.deepEqual(shot.sample(999),shot.sample(shot.duration));
}
for(const pose of [null,{}, {position:[0,1,2],target:[0,1,2],fov:60},{position:[0,1,2],target:[3,4,5],fov:NaN}])assert(!validCinematicPose(pose));
console.log(`PASS ${samples} finite continuous actual-route cinematic poses ×4 aspects, target centering/terrain clearance, duration clamps, model/time immutability. No WebGL rendering.`);
const{isCanonicalFinish}=await import('../src/cinematic-camera.js');
const model=new GameModel(route,{startS:165,endS:1265}).start('time-attack'),q=model.sampleRoute(1265);Object.assign(model.player,q,{grounded:true,altitude:0,flying:false,flipActive:false,s:1265});assert(isCanonicalFinish(model));
for(const mutation of [{s:1300},{y:q.y+.1},{y:NaN},{altitude:1},{flying:true},{flipActive:true},{grounded:false},{heading:q.heading+.3},{x:q.x-Math.sin(q.heading)*3.1,z:q.z+Math.cos(q.heading)*3.1}]){const previous={...model.player};Object.assign(model.player,mutation);assert(!isCanonicalFinish(model));model.player=previous;}
console.log('PASS delayed/offroad/airborne/flipping/reverse-facing finish results bypass camera rather than assuming arbitrary world clearance.');

const beforeEnd=model.sampleRoute(model.endS-11);Object.assign(model.player,beforeEnd,{s:model.endS-11,x:beforeEnd.x-Math.sin(beforeEnd.heading)*1.9,z:beforeEnd.z+Math.cos(beforeEnd.heading)*1.9,grounded:true,altitude:0,flying:false,flipActive:false});assert(!isCanonicalFinish(model));console.log("PASS road-height and pre-end circular gate boundary admission guards.");
