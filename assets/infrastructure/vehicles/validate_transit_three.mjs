import fs from 'node:fs';
import * as THREE from '../../../web/node_modules/three/build/three.module.js';
import {GLTFLoader} from '../../../web/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
globalThis.ProgressEvent ??= class {constructor(type,init={}){this.type=type;Object.assign(this,init)}};
const here=new URL('.',import.meta.url),project=new URL('../../../',here),results=[];
for(const [file,limit,rootName] of [['coast_metro_train',15000,'CoastMetroTrain'],['water_transit_ferry',12000,'WaterTransitFerry']]){
 const b=fs.readFileSync(new URL('assets/web/'+file+'.glb',project));
 const parsed=await new Promise((resolve,reject)=>new GLTFLoader().parse(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'',resolve,reject));
 const scene=parsed.scene;scene.updateMatrixWorld(true);const root=scene.getObjectByName(rootName);if(!root)throw Error('missing root');
 let tris=0,draws=0,finite=true,vertexColors=true,textureCount=0;
 scene.traverse(o=>{if(o.isMesh){tris+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;draws++;vertexColors&&=Boolean(o.geometry.attributes.color&&o.material.vertexColors);finite&&=[...o.geometry.attributes.position.array].every(Number.isFinite);if(o.material.map)textureCount++;}});
 const bounds=new THREE.Box3().setFromObject(root);const r={asset:file,result:'PASS',triangles:tris,draw_calls:draws,finite_vertices:finite,vertex_colors:vertexColors,texture_count:textureCount,bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()}};
 if(file==='coast_metro_train'){
  const cars=[0,1,2].map(i=>scene.getObjectByName('TrainCar_'+i));if(cars.some(c=>!c))throw Error('missing carriage pivot');
  const centers=cars.map(c=>c.getWorldPosition(new THREE.Vector3()).toArray());r.carriage_centers=centers;
  const unchanged=cars[1].matrixWorld.clone(),old=cars[0].matrixWorld.clone();cars[0].position.x+=2;cars[0].rotation.y=.22;scene.updateMatrixWorld(true);
  r.independent_carriage_motion=cars[1].matrixWorld.equals(unchanged)&&!cars[0].matrixWorld.equals(old);
  r.rear_cab_facing_negative_x=new THREE.Vector3(1,0,0).applyQuaternion(cars[2].quaternion).x<-.999;
  r.rail_contact_y=Math.abs(bounds.min.y)<1e-6;
  if(!r.independent_carriage_motion||!r.rear_cab_facing_negative_x||!r.rail_contact_y)r.result='FAIL';
 }else{r.sea_level_root_y=root.position.y;r.hull_submerged=bounds.min.y<-.9;r.upper_deck_and_mast=bounds.max.y>5;if(!r.hull_submerged||!r.upper_deck_and_mast)r.result='FAIL';}
 if(!finite||!vertexColors||textureCount||tris>limit||draws>9)r.result='FAIL';results.push(r);
}
fs.writeFileSync(new URL('three_validation.json',here),JSON.stringify({result:results.every(x=>x.result==='PASS')?'PASS':'FAIL',scope:'Actual Node Three GLTFLoader parsing, independent pivots, coordinates, vertex colors and geometry budgets. Not rendered browser gameplay.',assets:results},null,2));console.log(JSON.stringify(results,null,2));if(results.some(x=>x.result!=='PASS'))process.exit(1);
