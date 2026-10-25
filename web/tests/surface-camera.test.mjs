import assert from 'node:assert/strict';
import * as THREE from 'three';
import {SurfaceCameraRig,validSurfaceFrame,surfaceQuaternion} from '../src/surface-camera.js';
const frame=b=>({forward:[1,0,0],up:[0,Math.cos(b),-Math.sin(b)],right:[0,Math.sin(b),Math.cos(b)]});
for(let i=0;i<=360;i++){const f=frame(i*Math.PI/720);assert(validSurfaceFrame(f));assert(Math.abs(surfaceQuaternion(f).length()-1)<1e-12);}
assert(!validSurfaceFrame({forward:[1,0,0],up:[0,1,0],right:[0,0,-1]}));assert(!validSurfaceFrame({forward:[NaN,0,0],up:[0,1,0],right:[0,0,1]}));
const final=[];
for(const hz of [30,60,120]){const rig=new SurfaceCameraRig(),camera=new THREE.PerspectiveCamera();let previous=null,maxAngle=0,maxPosition=0;
 for(let i=0;i<=hz*12;i++){const t=i/hz,b=t<4?0:t<8?(t-4)*Math.PI/8:Math.PI/2,p={x:t*25,y:8,z:0,attached:true,surfaceFrame:frame(b)},shot=rig.update(p,1/hz,{reset:i===0});camera.position.copy(shot.position);camera.up.copy(shot.up);camera.lookAt(shot.target);assert([...shot.position.toArray(),...shot.target.toArray(),...camera.quaternion.toArray()].every(Number.isFinite));if(previous){maxAngle=Math.max(maxAngle,previous.q.angleTo(camera.quaternion));maxPosition=Math.max(maxPosition,previous.p.distanceTo(camera.position));}previous={q:camera.quaternion.clone(),p:camera.position.clone()};}
 assert(maxAngle<.06);assert(maxPosition<1.1);final.push(previous);const before={p:rig.position.toArray(),q:rig.orientation.toArray()};rig.update({x:300,y:8,z:0,attached:true,surfaceFrame:frame(Math.PI/2)},.1,{paused:true});assert.deepEqual(rig.position.toArray(),before.p);assert.deepEqual(rig.orientation.toArray(),before.q);
 for(const mode of [0,1,2]){rig.reset();const shot=rig.update({x:400,y:8,z:0,attached:true,surfaceFrame:frame(Math.PI/2)},0,{mode,projectSurface:point=>({inside:true,distance:-1,normal:[0,0,-1]})});assert(shot.position.toArray().every(Number.isFinite));assert(Math.abs(shot.up.y-Math.cos(Math.PI/2))<1e-12);}
}
// Exponential chase smoothing has a small sampling phase error, not an exact
// fixed-step physics assertion. Bound it rather than claim bit-identical cameras.
for(const v of final.slice(1)){assert(v.p.distanceTo(final[0].p)<.35);assert(v.q.angleTo(final[0].q)<.005);}
console.log('PASS surface-frame validation, finite 30/60/120 camera traversal, bounded continuity, pause and reset. Scene graph only; no GPU evidence.');
