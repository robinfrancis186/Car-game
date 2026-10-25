import * as THREE from 'three';

/** Visuals for the headless model's run ledger; never awards currency itself. */
export class RaceCollectibles{
 constructor(scene,template){
  if(!template?.isObject3D)throw new Error('Original Blender ArcadeCoin.glb is required.');
  this.group=new THREE.Group();this.group.name='RaceCoinPickups';scene.add(this.group);this.meshes=[];this.temp=new THREE.Object3D();this.clock=0;this.visibleCoins=0;
  template.updateMatrixWorld(true);template.traverse(o=>{if(!o.isMesh)return;const mesh=new THREE.InstancedMesh(o.geometry,o.material,120);mesh.count=0;mesh.castShadow=false;mesh.receiveShadow=false;mesh.frustumCulled=false;this.group.add(mesh);this.meshes.push({mesh,local:o.matrixWorld.clone()});});
 }
 update(model,dt,{menu=false}={}){
  if(!menu&&!model.paused)this.clock+=Math.max(0,Math.min(.1,Number.isFinite(dt)?dt:0));
  this.group.visible=!menu&&['racing','countdown'].includes(model.state)&&model.scenario.id!=='free-drive';
  const visible=this.group.visible?(model.coins||[]).filter(c=>!c.collected&&[c.x,c.y,c.z].every(Number.isFinite)&&Math.hypot(c.x-model.player.x,c.z-model.player.z)<180).slice(0,120):[];
  for(const entry of this.meshes){entry.mesh.count=visible.length;visible.forEach((c,i)=>{this.temp.position.set(c.x,c.y+.055*Math.sin(this.clock*2.4+c.s*.11),c.z);this.temp.rotation.set(0,this.clock*1.7+c.s*.03,0);this.temp.scale.setScalar(1);this.temp.updateMatrix();entry.mesh.setMatrixAt(i,this.temp.matrix.clone().multiply(entry.local));});entry.mesh.instanceMatrix.needsUpdate=true;}
  this.visibleCoins=visible.length;
 }
}
