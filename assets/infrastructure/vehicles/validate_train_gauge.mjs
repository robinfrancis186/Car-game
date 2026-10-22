import fs from 'node:fs';
import * as THREE from '../../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import {createHash} from 'node:crypto';
globalThis.ProgressEvent??=class{constructor(t,v={}){this.type=t;Object.assign(this,v)}};
const here=new URL('.',import.meta.url),project=new URL('../../../',here);
async function load(relative){const b=fs.readFileSync(new URL(relative,project));const g=await new Promise((ok,no)=>new GLTFLoader().parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'',ok,no));g.scene.updateMatrixWorld(true);return {scene:g.scene,hash:createHash('sha256').update(b).digest('hex')}}
function points(scene){const p=[];scene.traverse(o=>{if(o.isMesh){const a=o.geometry.attributes.position;for(let i=0;i<a.count;i++)p.push(new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld));}});return p}
const train=await load('assets/web/coast_metro_train.glb'),rail=await load('assets/web/MetroViaductSpan.glb'),old=await load('assets/infrastructure/vehicles/history_gauge/coast_metro_train_before_gauge_fix.glb');
const tp=points(train.scene),rp=points(rail.scene),op=points(old.scene),q=n=>Math.round(n*1e4)/1e4;
const rails=[-1,1].map(side=>{const vs=rp.filter(p=>Math.abs(p.y)<1e-5&&Math.sign(p.z)===side&&Math.abs(p.z)>.6&&Math.abs(p.z)<.9);if(!vs.length)throw Error('No measured rail tops');return {side,min_z:Math.min(...vs.map(p=>p.z)),max_z:Math.max(...vs.map(p=>p.z)),top_y_range:[Math.min(...vs.map(p=>p.y)),Math.max(...vs.map(p=>p.y))]};});
const bands=new Map;
for(const p of tp.filter(p=>Math.abs(p.y)<1e-5&&Math.abs(p.z)<1.1)){const side=Math.sign(p.z),key=q(p.x)+'|'+side;if(!bands.has(key))bands.set(key,{x:q(p.x),side,min_z:Infinity,max_z:-Infinity,min_y:Infinity,max_y:-Infinity});const b=bands.get(key);b.min_z=Math.min(b.min_z,p.z);b.max_z=Math.max(b.max_z,p.z);b.min_y=Math.min(b.min_y,p.y);b.max_y=Math.max(b.max_y,p.y)}
const wheelChecks=[...bands.values()].map(b=>{const r=rails.find(r=>r.side===b.side),center=(b.min_z+b.max_z)/2,overlap=Math.max(0,Math.min(b.max_z,r.max_z)-Math.max(b.min_z,r.min_z));return {...b,center_z:center,overlap_m:overlap,full_rail_width_supported:b.min_z<=r.min_z+1e-5&&b.max_z>=r.max_z-1e-5,center_matches_standard_gauge:Math.abs(Math.abs(center)-.7175)<1e-5}});
const geomSignature=ps=>JSON.stringify([...new Set(ps.filter(p=>p.y>.80001).map(p=>[q(p.x),q(p.y),q(p.z)].join(',')))].sort());
const bodyUnchanged=geomSignature(tp)===geomSignature(op),pivotsUnchanged=[0,1,2].every(i=>{const a=train.scene.getObjectByName('TrainCar_'+i),b=old.scene.getObjectByName('TrainCar_'+i);return a.position.distanceTo(b.position)<1e-7&&a.quaternion.angleTo(b.quaternion)<1e-7});
const result={result:'PASS',scope:'Actual exported train and viaduct GLB vertices. Contact widths at Y=0; no moving-curved-track dynamic contact simulation.',train_sha256:train.hash,viaduct_sha256:rail.hash,gauge_m:1.435,measured_rail_tops:rails,wheel_contact_bands:wheelChecks,wheel_count:wheelChecks.length,all_wheels_fully_overlap_rail_top:wheelChecks.every(x=>x.full_rail_width_supported&&x.center_matches_standard_gauge),minimum_lateral_overlap_m:Math.min(...wheelChecks.map(x=>x.overlap_m)),body_geometry_above_wheels_unchanged:bodyUnchanged,carriage_pivots_and_rear_base_yaw_unchanged:pivotsUnchanged};
if(wheelChecks.length!==24||!result.all_wheels_fully_overlap_rail_top||!bodyUnchanged||!pivotsUnchanged)result.result='FAIL';
fs.writeFileSync(new URL('train_gauge_validation.json',here),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,wheel_contact_bands:wheelChecks.slice(0,2)},null,2));if(result.result!=='PASS')process.exit(1);
