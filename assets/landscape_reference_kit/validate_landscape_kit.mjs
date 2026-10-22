import fs from 'node:fs';
import crypto from 'node:crypto';
import * as THREE from '../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
globalThis.self??=globalThis;
// Node lacks image bitmap decoding. Actual PNG pixels are decoded and rendered by Blender roundtrip.
// This shim validates PNG dimensions while GLTFLoader builds the real texture/material objects.
globalThis.createImageBitmap??=async(blob)=>{const b=Buffer.from(await blob.arrayBuffer());if(b.toString('hex',0,8)!=='89504e470d0a1a0a')throw Error('Expected PNG');return {width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}}};
globalThis.ProgressEvent??=class{constructor(t,i={}){this.type=t;Object.assign(this,i)}};
const here=new URL('.',import.meta.url),project=new URL('../../',here),results=[];
for(const asset of ['BirdRockLookout','CanalShikara','CanalRainTree']){
 const b=fs.readFileSync(new URL('assets/web/'+asset+'.glb',project));const manifest=JSON.parse(fs.readFileSync(new URL(asset+'_manifest.json',here)));
 const gltf=await new Promise((r,j)=>new GLTFLoader().parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'',r,j));const root=gltf.scene.getObjectByName(asset);if(!root)throw Error('Root missing: '+asset);gltf.scene.updateMatrixWorld(true);
 let triangles=0,draws=0,finite=true,colors=true,textures=0,normalTextures=0,leafMin=Infinity,leafMax=-Infinity;const materials=new Set();
 root.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position;triangles+=(o.geometry.index?.count??p.count)/3;draws++;finite&&=[...p.array].every(Number.isFinite);colors&&=!!(o.geometry.attributes.color&&o.material.vertexColors);textures+=!!o.material.map;normalTextures+=!!o.material.normalMap;materials.add(o.material.name);
 if(/leaf/i.test(o.material.name)){const v=new THREE.Vector3();for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);leafMin=Math.min(leafMin,v.y);leafMax=Math.max(leafMax,v.y);}}
 });
 const box=new THREE.Box3().setFromObject(root);const matchesBounds=box.min.toArray().every((v,i)=>Math.abs(v-manifest.bounds_local_m.min[i])<1e-4)&&box.max.toArray().every((v,i)=>Math.abs(v-manifest.bounds_local_m.max[i])<1e-4);const hash=crypto.createHash('sha256').update(b).digest('hex');
 const result={asset,result:'PASS',sha256:hash,triangles,draw_calls:draws,bytes:b.byteLength,finite_vertices:finite,vertex_colors:colors,albedo_texture_count:textures,normal_texture_count:normalTextures,materials:[...materials],root_position:root.position.toArray(),root_scale:root.scale.toArray(),bounds:{min:box.min.toArray(),max:box.max.toArray()},manifest_bounds_match:matchesBounds,manifest_hash_match:hash===manifest.sha256};
 if(asset==='BirdRockLookout'){
  result.original_stone_normal_present=normalTextures===1;if(normalTextures!==1)result.result='FAIL';
  const proxy=manifest.collision_proxies.find(p=>p.type==='obb'&&p.part.includes('rocky'));let misses=0,count=0;
  root.traverse(o=>{if(!o.isMesh||!/_Rock$/.test(o.material.name))return;const p=o.geometry.attributes.position,v=new THREE.Vector3();for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);count++;if(v.toArray().some((c,j)=>Math.abs(c-proxy.center_local_m[j])>proxy.half_extents_m[j]+1e-5))misses++;}});
  result.rock_proxy_tested_vertices=count;result.rock_proxy_missed_vertices=misses;if(!count||misses)result.result='FAIL';
 }
 if(asset==='CanalShikara'){
  const p=manifest.collision_proxies[0];result.boat_proxy_contains_bounds=box.min.toArray().every((v,i)=>v>=p.center_local_m[i]-p.half_extents_m[i]-1e-5)&&box.max.toArray().every((v,i)=>v<=p.center_local_m[i]+p.half_extents_m[i]+1e-5);if(!result.boat_proxy_contains_bounds)result.result='FAIL';
 }
 if(asset==='CanalRainTree'){result.leaf_height_m=[leafMin,leafMax];result.canopy_clearance_ge_6m=leafMin>=6;result.wind_material_detected=materials.has('RainTree_Leaf');}
 if(asset==='CanalShikara'){result.waterline_root=root.position.y===0;result.submerged_hull=box.min.y<-.45;}
 if(!finite||!colors||textures||!matchesBounds||hash!==manifest.sha256||triangles>20000||draws>6||b.byteLength>1200000||(asset==='CanalRainTree'&&(!result.canopy_clearance_ge_6m||!result.wind_material_detected))||(asset==='CanalShikara'&&!result.submerged_hull))result.result='FAIL';results.push(result);
}
const out={result:results.every(r=>r.result==='PASS')?'PASS':'FAIL',scope:'Actual exported GLBs parsed with Three GLTFLoader. Geometry bounds/root/material/wind-height/budget assertions, not rendered browser gameplay or artistic likeness scoring. Node texture shim checks PNG dimensions/material wiring; actual normal-map pixels decoded by Blender GLB reimport/render.',assets:results};fs.writeFileSync(new URL('three_validation.json',here),JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));if(out.result!=='PASS')process.exit(1);
