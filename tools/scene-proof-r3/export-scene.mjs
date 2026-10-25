/** Exports original runtime pavilion mesh geometry for an OFFLINE Blender lighting proof.
 * No browser launch, no reference bitmap, no web integration. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as THREE from '../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import {createCoastalShowroom} from '../../web/src/showroom-scene.js';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../web/public/assets');
globalThis.self=globalThis;globalThis.ProgressEvent=class{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
const loader=new GLTFLoader(),models={};
for(const name of ['CoconutPalm_A.glb','CoconutPalm_B.glb']){const b=await fs.readFile(path.join(root,name));models[name]=(await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const showroom=createCoastalShowroom(models);showroom.group.position.set(0,0,0);showroom.group.visible=true;showroom.group.updateMatrixWorld(true);
const meshes=[];let triangles=0;
showroom.group.traverse(o=>{if(!o.isMesh)return;const g=o.geometry,mats=(Array.isArray(o.material)?o.material:[o.material]);const p=g.getAttribute('position');const v=new THREE.Vector3();const vertices=[];for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);vertices.push(v.toArray());}const index=g.index?Array.from(g.index.array):Array.from({length:p.count},(_,i)=>i);triangles+=index.length/3;
meshes.push({name:o.name||mats[0].name||'Original pavilion geometry',vertices,index,groups:g.groups,materials:mats.map(m=>({name:m.name,color:m.color?.toArray()||[.1,.1,.1],roughness:m.roughness??.3,metalness:m.metalness??0,emission:m.emissive?.toArray()||[0,0,0],emissionIntensity:m.emissiveIntensity??0,shader:m.isShaderMaterial??false,basic:m.isMeshBasicMaterial??false,opacity:m.opacity??1}))});});
const data={scope:'Exact R3 runtime pavilion mesh geometry; Blender recreates shader materials/lighting separately. Not a browser screenshot.',meshes,triangles};await fs.writeFile(path.join(here,'pavilion-geometry.json'),JSON.stringify(data));console.log(JSON.stringify({meshes:meshes.length,triangles,bytes:JSON.stringify(data).length}));
showroom.dispose();
