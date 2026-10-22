/** Actual Three GLTFLoader node-contract validation. No WebGL/browser render claimed.
 * Optional args: input.glb output.json. Defaults to this silver variant.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as THREE from '../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
const here=path.dirname(fileURLToPath(import.meta.url));
const input=process.argv[2]||path.join(here,'car_silver.glb');
const output=process.argv[3]||path.join(here,'car_silver_three_validation.json');
const b=await fs.readFile(input);
const gltf=await new Promise((ok,bad)=>new GLTFLoader().parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'',ok,bad));
const scene=gltf.scene;scene.updateMatrixWorld(true);const tests=[];
for(const key of ['Front_Left','Front_Right','Rear_Left','Rear_Right']){
 const st=scene.getObjectByName('Steer_'+key),sp=scene.getObjectByName('Spin_'+key),cal=scene.getObjectByName('Caliper_'+key);
 const wheel=scene.getObjectByName('Wheel_'+key);let mesh;wheel.traverse(o=>{if(o.isMesh&&(!mesh||o.material.name==='Tire rubber'))mesh=o;});
 const pos=mesh.geometry.getAttribute('position');let i=0;for(let j=1;j<pos.count;j++)if(pos.getX(j)>pos.getX(i))i=j;
 const local=new THREE.Vector3().fromBufferAttribute(pos,i);const before=local.clone().applyMatrix4(mesh.matrixWorld),cp=cal.matrixWorld.clone();
 sp.rotation.z=-.7;scene.updateMatrixWorld(true);const after=local.clone().applyMatrix4(mesh.matrixWorld);const calDelta=Math.max(...cal.matrixWorld.elements.map((v,i)=>Math.abs(v-cp.elements[i])));
 sp.rotation.z=0;scene.updateMatrixWorld(true);const s0=local.clone().applyMatrix4(mesh.matrixWorld);st.rotation.y=.4;scene.updateMatrixWorld(true);const s1=local.clone().applyMatrix4(mesh.matrixWorld);
 tests.push({wheel:key,spin_displacement_m:before.distanceTo(after),caliper_matrix_delta:calDelta,steer_displacement_m:s0.distanceTo(s1)});
 st.rotation.y=0;scene.updateMatrixWorld(true);
}
const wing=scene.getObjectByName('AeroWing');const hinge=scene.getObjectByName('AeroWing_Hinge');let wingMove=null;
if(wing&&hinge){
 let wm;wing.traverse(o=>{if(o.isMesh)wm=o;});const wp=new THREE.Vector3().fromBufferAttribute(wm.geometry.getAttribute('position'),0),w0=wp.clone().applyMatrix4(wm.matrixWorld);
 hinge.rotation.z=-.18;scene.updateMatrixWorld(true);wingMove=w0.distanceTo(wp.clone().applyMatrix4(wm.matrixWorld));hinge.rotation.z=0;scene.updateMatrixWorld(true);
}
const bounds=new THREE.Box3().setFromObject(scene),size=bounds.getSize(new THREE.Vector3());let paint=false,meshes=0;scene.traverse(o=>{if(o.isMesh){meshes++;if((Array.isArray(o.material)?o.material:[o.material]).some(m=>m.name==='Crimson multi-coat | original fan concept'))paint=true;}});
const result={result:tests.every(t=>t.spin_displacement_m>.1&&t.steer_displacement_m>.05&&t.caliper_matrix_delta<1e-9)&&(wingMove===null||wingMove>.005)&&paint?'PASS':'FAIL',loader:'Three.js 0.170.0 GLTFLoader (Node asset parse; not a browser render)',wheel_tests:tests,wing_displacement_m:wingMove,paint_material_found:paint,mesh_objects:meshes,bounds_three:size.toArray(),bytes:b.length};
await fs.writeFile(output,JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
if(result.result!=='PASS')process.exitCode=1;
