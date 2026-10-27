import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {curveGuidePlacements,installCurveGuides} from '../src/curve-guides.js';
import {sampleTeaTerrain} from '../src/tea-placement.js';
import {GameModel} from '../src/gameplay.js';
const load=file=>{const d=JSON.parse(fs.readFileSync(new URL('../public/assets/'+file,import.meta.url)));return {...d,...d.world};};
const world=load('course_runtime_highlands.json'),route=world.route_points.map(([x,y,z])=>({x,y,z})),model=new GameModel(route),before=JSON.stringify(world);
const guides=curveGuidePlacements(world,route);assert.equal(guides.length,23);assert.deepEqual(curveGuidePlacements(world,route),guides);
assert(guides.some(p=>p.direction===1)&&guides.some(p=>p.direction===-1));
for(let i=0;i<guides.length;i++){
 const p=guides[i],q=model.sampleRoute(p.s),near=model.projectToRoute(p.x,p.z,p.s);
 assert(p.s>900&&p.s<model.routeLength-30);if(i)assert(p.s-guides[i-1].s>=24);
 assert(Math.abs(near.offset)>5.4,'marker must stay behind the guardrail, clear of the shoulder');
 assert.equal(Math.sign(near.offset),-p.direction,'guide belongs outside its turn');assert.equal(Math.sign(p.turn),p.direction,'arrow must point into the actual bend');
 assert(Math.abs(p.y-sampleTeaTerrain(world.terrain_grid,p.x,p.z))<1e-12);assert(Math.abs(p.x-q.x-Math.sin(q.heading)*p.direction*5.6)<1e-8);assert(Object.values(p).every(Number.isFinite));
}
for(const f of ['course_runtime.json','course_runtime_surface_test.json']){const other=load(f);assert.deepEqual(curveGuidePlacements(other,other.route_points.map(([x,y,z])=>({x,y,z}))),[]);}
const renderer={world,route,scene:new THREE.Scene(),environmentChunks:[]},stats=installCurveGuides(renderer);assert.equal(stats.count,23);assert.equal(stats.draws,3);assert.equal(stats.triangles,736);assert.equal(renderer.scene.children.length,3);assert.equal(renderer.environmentChunks.length,0);
for(const mesh of renderer.scene.children){assert(mesh.isInstancedMesh);assert.equal(mesh.count,23);assert.equal(mesh.castShadow,false);assert(mesh.receiveShadow);assert(mesh.boundingSphere.radius>0);const matrix=new THREE.Matrix4();for(let i=0;i<mesh.count;i++){mesh.getMatrixAt(i,matrix);assert(matrix.elements.every(Number.isFinite));assert(Math.abs(matrix.determinant()-1)<1e-5,'instanced transforms must not use unsupported negative scaling');}}
const panel=renderer.scene.children.find(m=>m.name.endsWith('reflector boards')),arrows=renderer.scene.children.find(m=>m.name.endsWith('direction chevrons')),matrix=new THREE.Matrix4();
for(let i=0;i<guides.length;i++){
 const p=guides[i],towardsApproach=new THREE.Vector3(-Math.cos(p.heading),0,-Math.sin(p.heading));panel.getMatrixAt(i,matrix);assert(new THREE.Vector3(0,0,1).transformDirection(matrix).dot(towardsApproach)>.999999);
 arrows.getMatrixAt(i,matrix);const right=new THREE.Vector3(-Math.sin(p.heading),0,Math.cos(p.heading));assert(new THREE.Vector3(1,0,0).transformDirection(matrix).dot(right)*p.direction>.999999);
}
assert.equal(JSON.stringify(world),before,'visual installation cannot mutate world physics/navigation data');
console.log('PASS 23 terrain-supported original curve markers: correct outside placement, signed arrows, road clearance, deterministic three-batch/736-triangle budget, positive instance transforms and unchanged other worlds. Scene graph only.');
