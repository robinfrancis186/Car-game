/** Original curve markers. Visual guidance only; the existing road/rail collision is unchanged. */
import * as THREE from 'three';
import {sampleTeaTerrain} from './tea-placement.js';
const angle=v=>Math.atan2(Math.sin(v),Math.cos(v));
export function curveGuidePlacements(world,route){
 if(world.id!=='highlands')return [];
 const distances=[0];for(let i=1;i<route.length;i++)distances.push(distances[i-1]+Math.hypot(route[i].x-route[i-1].x,route[i].z-route[i-1].z));
 const sample=s=>{const i=Math.max(0,distances.findIndex(d=>d>=s)-1),a=route[i],b=route[i+1],t=(s-distances[i])/(distances[i+1]-distances[i]);return {x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t,heading:Math.atan2(b.z-a.z,b.x-a.x)};};
 const placements=[];
 for(let s=900;s<distances.at(-1)-30;s+=8){
  const turn=angle(sample(s+12).heading-sample(s-12).heading);
  if(Math.abs(turn)<.25||s-(placements.at(-1)?.s??-Infinity)<24)continue;
  const p=sample(s),direction=Math.sign(turn),offset=-direction*5.6,x=p.x-Math.sin(p.heading)*offset,z=p.z+Math.cos(p.heading)*offset;
  placements.push({s,x,z,y:sampleTeaTerrain(world.terrain_grid,x,z),heading:p.heading,direction,offset,turn});
 }
 return placements;
}
export function installCurveGuides(renderer){
 const placements=curveGuidePlacements(renderer.world,renderer.route);if(!placements.length)return {count:0,triangles:0,draws:0};
 const shape=new THREE.Shape();shape.moveTo(-.4,.28);for(const [x,y]of[[-.22,.28],[.06,0],[-.22,-.28],[-.4,-.28],[-.12,0]])shape.lineTo(x,y);shape.closePath();
 const arrow=new THREE.ShapeGeometry(shape),second=arrow.clone().translate(.42,0,0);
 const positions=[...arrow.attributes.position.array,...second.attributes.position.array],indices=[...arrow.index.array,...Array.from(second.index.array,v=>v+arrow.attributes.position.count)],chevrons=new THREE.BufferGeometry();
 chevrons.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));chevrons.setIndex(indices);chevrons.computeVertexNormals();arrow.dispose();second.dispose();
 const parts=[
  {name:'reflector boards',geometry:new THREE.BoxGeometry(1.15,.8,.06),color:'#202822',roughness:.8,y:1.65,z:0},
  {name:'steel posts',geometry:new THREE.BoxGeometry(.065,1.8,.065),color:'#747c75',roughness:.6,y:.9,z:0},
  {name:'direction chevrons',geometry:chevrons,color:'#edc64b',roughness:.55,y:1.65,z:.032}
 ];
 const temp=new THREE.Object3D(),rotation=new THREE.Quaternion();let triangles=0;
 for(const part of parts){
  const material=new THREE.MeshStandardMaterial({color:part.color,roughness:part.roughness,metalness:part.name==='steel posts'?.4:0,side:THREE.DoubleSide}),mesh=new THREE.InstancedMesh(part.geometry,material,placements.length);
  mesh.name='Highland curve '+part.name;mesh.castShadow=false;mesh.receiveShadow=true;
  placements.forEach((p,i)=>{rotation.setFromAxisAngle(THREE.Object3D.DEFAULT_UP,-p.heading-Math.PI/2);temp.position.set(p.x,p.y+part.y,p.z).add(new THREE.Vector3(0,0,part.z).applyQuaternion(rotation));temp.quaternion.copy(rotation);if(part.name==='direction chevrons'&&p.direction<0)temp.rotateY(Math.PI);temp.updateMatrix();mesh.setMatrixAt(i,temp.matrix);});
  mesh.instanceMatrix.needsUpdate=true;mesh.computeBoundingSphere();renderer.scene.add(mesh);
  // Scene-wide batches cost three draws and no per-frame placement/texture work.
  triangles+=(part.geometry.index?.count??part.geometry.attributes.position.count)/3*placements.length;
 }
 return {count:placements.length,triangles,draws:parts.length,placements};
}
