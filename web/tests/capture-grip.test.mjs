import assert from 'node:assert/strict';
import * as THREE from 'three';
import {captureAssets,captureTemplates}from './capture-assets.mjs';
import {PoliceCaptureScene}from '../src/police-capture-scene.js';
import {CaptureGameModel}from '../src/police-capture.js';
const V=()=>new THREE.Vector3(),models=await captureAssets();
function samples(actor,side){const out=[];actor.rig.model.traverse(mesh=>{if(!mesh.isSkinnedMesh||!mesh.material.name.includes('skin'))return;mesh.skeleton.update();const p=mesh.geometry.attributes.position,idx=mesh.geometry.attributes.skinIndex,w=mesh.geometry.attributes.skinWeight,cache=new Map();for(let i=0;i<p.count;i++){let influence=0,best=0,part;for(let j=0;j<4;j++){const name=mesh.skeleton.bones[idx.getComponent(i,j)].name;if(name.endsWith('_'+side)&&/^(hand|index|middle|ring|pinky|thumb)/.test(name)){influence+=w.getComponent(i,j);if(w.getComponent(i,j)>best){best=w.getComponent(i,j);part=name;}}}if(influence>.4){const v=mesh.applyBoneTransform(i,V().fromBufferAttribute(p,i));mesh.localToWorld(v);v.part=part;out.push(v);cache.set(i,v);}}
 const indices=mesh.geometry.index;for(let i=0;i<indices.count;i+=3){const a=cache.get(indices.getX(i)),b=cache.get(indices.getX(i+1)),c=cache.get(indices.getX(i+2));if(a&&b&&c)out.push(a.clone().lerp(b,.5),b.clone().lerp(c,.5),c.clone().lerp(a,.5),a.clone().add(b).add(c).multiplyScalar(1/3));}});return out;}

let poses=0,minimum=Infinity,surfaceCases=0,contactRange=[];
for(const side of [-1,1]){
 const visual=new PoliceCaptureScene(new THREE.Scene(),captureTemplates(models)),m=new CaptureGameModel(Array.from({length:151},(_,i)=>({x:i*10,y:.18,z:0}))).start('hot-pursuit');m.state='racing';Object.assign(m.police[0],{x:m.player.x-5,z:m.player.z+side*2,y:m.player.y,speed:0});m._end('busted','BUSTED');
 function driverTriangles(){const triangles=[];const centers=['l','r'].map(s=>visual.driver.joint('hand_'+s));visual.driver.rig.model.traverse(mesh=>{if(!mesh.isSkinnedMesh||!mesh.material.name.includes('skin'))return;mesh.skeleton.update();const p=mesh.geometry.attributes.position,index=mesh.geometry.index,cache=new Map();const vertex=i=>{if(!cache.has(i))cache.set(i,mesh.localToWorld(mesh.applyBoneTransform(i,V().fromBufferAttribute(p,i))));return cache.get(i);};for(let i=0;i<index.count;i+=3){const a=vertex(index.getX(i)),b=vertex(index.getX(i+1)),c=vertex(index.getX(i+2));if(!centers.some(center=>Math.min(a.distanceTo(center),b.distanceTo(center),c.distanceTo(center))<.19))continue;const tri=new THREE.Triangle(a,b,c);tri.normal=tri.getNormal(V());triangles.push(tri);}});return triangles;}
 for(const quality of ['high','balanced'])for(let i=0;i<55;i++){
  const t=5.2+i*.05;m.capture.elapsed=t;visual.update(m,{quality});visual.group.updateMatrixWorld(true);poses++;
  const checkSurface=[5.8,5.95,6.1,6.25,6.4,6.55,6.7].some(v=>Math.abs(t-v)<1e-7),triangles=checkSurface?driverTriangles():[];
  for(const hand of ['l','r']){
   const target=visual.officers[0].gripTargets[hand],points=samples(visual.officers[0],hand);
   if(checkSurface){let minimumSkin=Infinity;const closest=V(),delta=V();for(const p of points){if(p.distanceTo(target.center)>.18)continue;let nearest=Infinity,sign=1;for(const tri of triangles){tri.closestPointToPoint(p,closest);const distance=p.distanceToSquared(closest);if(distance<nearest){nearest=distance;sign=delta.subVectors(p,closest).dot(tri.normal)<0?-1:1;}}minimumSkin=Math.min(minimumSkin,Math.sqrt(nearest)*sign);}assert(minimumSkin>=0,`sampled officer hand penetrates actual driver skin ${side}/${quality}/${t}/${hand}: ${minimumSkin}`);if(t>=6.7-1e-7){assert(minimumSkin<.006,`visible contact must remain within 6mm of actual skin: ${side}/${quality}/${t}/${hand}: ${minimumSkin}`);contactRange.push(minimumSkin);}surfaceCases++;}
   for(const p of points){const delta=p.clone().sub(target.center),axial=delta.dot(target.axis);if(axial<-.045||axial>.03)continue;const clearance=delta.addScaledVector(target.axis,-axial).length()-target.radius;minimum=Math.min(minimum,clearance);assert(clearance>.001,`skinned hand enters wrist staging cylinder: ${side}/${quality}/${t}/${hand}/${clearance}`);}
  }
  if(t>=6.7)for(const error of visual.diagnostics.contactErrors)assert(error<.002,'palm reaches wrist surface target');
 }
 visual.dispose();
}
console.log(`PASS ${poses} near/mobile grip poses, both staging sides; skin vertices/triangle samples clear wrist proxy by ${(minimum*1000).toFixed(2)}mm minimum. ${surfaceCases} actual deformed driver-skin comparisons passed; final proximity ${Math.min(...contactRange).toFixed(4)}–${Math.max(...contactRange).toFixed(4)}m. Samples, not continuous all-surface physics.`);
