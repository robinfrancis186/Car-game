import * as THREE from 'three';
/** Visual-only licensed pilot. No new collision, reward or navigation behavior. */
export class SimReadyPilot{
 constructor(renderer){
  this.sites=[];
  const route=renderer.route;
  const at=s=>{let total=0;for(let i=1;i<route.length;i++){const a=route[i-1],b=route[i],d=Math.hypot(b.x-a.x,b.z-a.z);if(total+d>=s){const t=(s-total)/d;return {x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t,heading:Math.atan2(b.z-a.z,b.x-a.x)};}total+=d;}return route.at(-1);};
  for(const start of [180,3192,4050]){
   const q=at(start),site=new THREE.Group();site.name='NVIDIA SimReady roadside pilot';
   const center=new THREE.Vector3(q.x,q.y-.18,q.z),placements={Fence:[],Crate:[]};
   for(let i=0;i<4;i++)placements.Fence.push({along:(i-1.5)*1.23,side:7.5,yaw:q.heading});
   for(let i=0;i<3;i++)placements.Crate.push({along:(i-1)*.65,side:9,yaw:q.heading+.18*i});
   for(const kind of ['Fence','Crate']){
    const lod=new THREE.LOD();lod.autoUpdate=false;
    for(const [level,distance]of [['Near',0],['Far',40]]){
     const model=renderer.models['SimReady'+kind+level+'.glb'],group=new THREE.Group();model.updateMatrixWorld(true);
     model.traverse(o=>{if(!o.isMesh)return;const mesh=new THREE.InstancedMesh(o.geometry,o.material,placements[kind].length);mesh.castShadow=mesh.receiveShadow=true;
      const temp=new THREE.Object3D();placements[kind].forEach((p,i)=>{temp.position.set(Math.cos(q.heading)*p.along-Math.sin(q.heading)*p.side,0,Math.sin(q.heading)*p.along+Math.cos(q.heading)*p.side);temp.rotation.y=-p.yaw;temp.updateMatrix();mesh.setMatrixAt(i,temp.matrix.clone().multiply(o.matrixWorld));});group.add(mesh);});
     lod.addLevel(group,distance);
    }
    site.add(lod);
   }
   site.position.copy(center);renderer.scene.add(site);this.sites.push({site,center});
  }
 }
 update(camera,{menu=false,quality='high'}={}){for(const {site,center} of this.sites){site.visible=!menu&&camera.position.distanceTo(center)<(quality==='high'?150:100);if(site.visible)for(const lod of site.children){if(quality==='high')lod.update(camera);else{lod.levels[0].object.visible=false;lod.levels[1].object.visible=true;}}}}
}
