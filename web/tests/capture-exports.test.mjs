import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as THREE from 'three';
import {captureAssets}from './capture-assets.mjs';
const manifest=JSON.parse(await fs.readFile(new URL('../public/assets/capture-lod-manifest.json',import.meta.url))),models=await captureAssets();
let waist=0,vertices=0;
for(const entry of manifest){
 const b=await fs.readFile(new URL('../public/assets/'+entry.file,import.meta.url)),n=b.readUInt32LE(12),json=JSON.parse(b.toString('utf8',20,20+n));assert.equal(b.length,b.readUInt32LE(8));
 const skin=json.materials.find(m=>m.name.startsWith('CC0 MakeHuman skin'));assert.deepEqual(skin.pbrMetallicRoughness.baseColorFactor,[.56,.37,.26,1]);assert(skin.pbrMetallicRoughness.baseColorTexture);assert.equal(entry.bones,53);
 const model=models[entry.file];model.updateMatrixWorld(true);model.traverse(mesh=>{if(!mesh.isSkinnedMesh)return;mesh.skeleton.update();const p=mesh.geometry.attributes.position,idx=mesh.geometry.attributes.skinIndex,w=mesh.geometry.attributes.skinWeight;
  for(let i=0;i<p.count;i++){vertices++;let sum=0,pelvis=0;for(let j=0;j<4;j++){const value=w.getComponent(i,j);assert(Number.isFinite(value)&&value>=0);sum+=value;if(mesh.skeleton.bones[idx.getComponent(i,j)].name==='pelvis')pelvis+=value;}assert(Math.abs(sum-1)<.00002,'normalized four-influence skin');if(/cotton|trouser/.test(mesh.material.name)){const point=mesh.localToWorld(mesh.applyBoneTransform(i,new THREE.Vector3().fromBufferAttribute(p,i)));if(point.y>.995&&point.y<1.02){assert(pelvis>.99999,'actual exported waist follows pelvis');waist++;}}}
 });
}
assert(waist>100);console.log(`PASS four exact-tint textured GLBs, 53-bone skins, ${vertices} normalized vertices and ${waist} independently sampled exported pelvis-only waist vertices.`);
