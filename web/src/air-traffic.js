import * as THREE from 'three';
const finite=(v,d=0)=>Number.isFinite(v)?v:d;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const AXIS_Y=new THREE.Vector3(0,1,0),AXIS_Z=new THREE.Vector3(0,0,1),AXIS_X=new THREE.Vector3(1,0,0),DOWN=new THREE.Vector3(0,-1,0);
const list=m=>Array.isArray(m)?m:[m];
/** Bounded presentation only. All positions, escalation, visibility and line of
 * sight belong to the deterministic model; this never changes pursuit rules. */
export class AirTrafficRenderer{
 constructor(scene,{civilian,police,blur}={}){
  this.scene=scene;this.actors=[];this.lastModel=null;
  for(const [kind,template] of [['civilian',civilian],['police',police]]){
   if(!template)continue;
   const group=new THREE.Group();group.name=`AirTraffic_${kind}`;const model=template.clone(true);group.add(model);group.visible=false;scene.add(group);
   const rotor=model.getObjectByName('MainRotor'),tail=model.getObjectByName('TailRotor'),yaw=model.getObjectByName('SearchlightYaw'),pitch=model.getObjectByName('SearchlightPitch'),socket=model.getObjectByName('SearchlightSocket');
   if(!rotor||!tail||!yaw||!pitch||!socket)throw new Error(`Helicopter ${kind} rig is incomplete`);
   const lamps=[];model.traverse(o=>{if(!o.isMesh)return;o.castShadow=false;o.receiveShadow=true;o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of list(o.material)){m.envMapIntensity=.75;if(m.emissive&&/navigation|beacon|optical lens/i.test(m.name))lamps.push({material:m,base:m.emissiveIntensity});}});
   const actor={kind,group,model,rotor,tail,yaw,pitch,socket,rotorBase:rotor.quaternion.clone(),tailBase:tail.quaternion.clone(),yawBase:yaw.quaternion.clone(),pitchBase:pitch.quaternion.clone(),lamps,angle:0,tailAngle:0,lastTime:null,blur:null};
   if(blur){actor.blur=blur.clone(true);actor.blur.traverse(o=>{if(o.isMesh){o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of list(o.material)){m.transparent=true;m.depthWrite=false;m.opacity=.13;m.side=THREE.DoubleSide;}}});group.add(actor.blur);actor.blur.visible=false;}
   this.actors.push(actor);
  }
  this.light=new THREE.SpotLight('#e5f0ff',0,180,.14,.8,1.35);this.light.castShadow=false;this.light.target=new THREE.Object3D();scene.add(this.light,this.light.target);
  const geometry=new THREE.CylinderGeometry(0,1,1,16,1,true).translate(0,-.5,0);
  this.beam=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color:'#c3ddf4',transparent:true,opacity:.045,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending}));this.beam.name='PoliceSearchlightAtmosphere';this.beam.visible=false;this.beam.frustumCulled=false;scene.add(this.beam);
  this.stats={visible:0,beam:false,triangles:0};
 }
 update(model,{menu=false,quality='high',night=false}={}){
  const newModel=this.lastModel!==model;this.lastModel=model;
  const running=!menu&&model?.state==='racing';const paused=!!model?.paused;const time=Math.max(0,finite(model?.timer));
  this.stats.visible=0;this.stats.beam=false;this.stats.triangles=0;this.light.intensity=0;this.beam.visible=false;
  for(const a of this.actors){
   const s=a.kind==='police'?model?.helicopter:model?.civilianHelicopter;
   a.group.visible=!!(running&&s?.visible&&s?.active!==false&&[s.x,s.y,s.z,s.heading].every(Number.isFinite));
   if(!a.group.visible){a.lastTime=null;a.angle=0;a.tailAngle=0;if(a.blur)a.blur.visible=false;continue;}
   this.stats.visible++;
   const actorTime=Math.max(0,finite(s.flightSeconds,time));const dt=paused||newModel||a.lastTime===null?0:clamp(actorTime-a.lastTime,0,.25);a.lastTime=actorTime;
   const rpm=clamp(finite(s.rotorRpm,390),0,650);a.angle=(a.angle+dt*rpm*Math.PI/30)%(Math.PI*2);a.tailAngle=(a.tailAngle+dt*rpm*5.2*Math.PI/30)%(Math.PI*2);
   a.group.position.set(s.x,s.y,s.z);a.group.quaternion.setFromAxisAngle(AXIS_Y,-s.heading).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Z,clamp(finite(s.pitch),-.3,.3))).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_X,clamp(finite(s.roll),-.35,.35)));
   a.rotor.quaternion.copy(a.rotorBase).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Y,a.angle));a.tail.quaternion.copy(a.tailBase).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Z,-a.tailAngle));
   if(a.blur)a.blur.visible=rpm>100&&quality==='high';
   a.group.traverseVisible(o=>{if(o.isMesh)this.stats.triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;});
   for(const lamp of a.lamps){const beacon=/beacon/i.test(lamp.material.name);lamp.material.emissiveIntensity=lamp.base*(beacon?(Math.sin(actorTime*8)>0?.9:.15):night?1:.5);}
   a.yaw.quaternion.copy(a.yawBase);a.pitch.quaternion.copy(a.pitchBase);a.group.updateMatrixWorld(true);
   if(a.kind!=='police'||!s.beamVisible||!s.beamTarget||![s.beamTarget.x,s.beamTarget.y,s.beamTarget.z].every(Number.isFinite))continue;
   const target=new THREE.Vector3(s.beamTarget.x,s.beamTarget.y,s.beamTarget.z);
   // Aim the physical pod first; two passes account for the lens moving with tilt.
   let lens=new THREE.Vector3(),local=new THREE.Vector3();
   for(let pass=0;pass<2;pass++){
    a.socket.getWorldPosition(lens);local.copy(target).sub(lens).applyQuaternion(a.group.quaternion.clone().invert());
    const bearing=Math.atan2(local.z,local.x),tilt=clamp(Math.atan2(Math.hypot(local.x,local.z),-local.y),0,.70);
    a.yaw.quaternion.copy(a.yawBase).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Y,-bearing));a.pitch.quaternion.copy(a.pitchBase).multiply(new THREE.Quaternion().setFromAxisAngle(AXIS_Z,tilt));a.group.updateMatrixWorld(true);
   }
   a.socket.getWorldPosition(lens);const direction=target.clone().sub(lens),distance=direction.length();if(distance<1||distance>170)continue;direction.normalize();
   // The model prefilter uses an approximate aircraft origin. The rendered pod
   // moves with yaw/pitch, so veto the exact optical ray too: no roof light leak.
   if(typeof model._airLineOfSight==='function'&&!model._airLineOfSight(lens,target))continue;
   const optic=DOWN.clone().applyQuaternion(a.socket.getWorldQuaternion(new THREE.Quaternion()));if(optic.angleTo(direction)>.025)continue; // No visually detached beam beyond pod articulation.
   const strength=clamp(finite(s.spotlightIntensity,1),0,1);this.light.position.copy(lens);this.light.target.position.copy(target);this.light.intensity=(night?230:120)*strength;
   this.beam.visible=strength>0;this.beam.position.copy(lens);this.beam.quaternion.setFromUnitVectors(DOWN,direction);const radius=Math.tan(.14)*distance;this.beam.scale.set(radius,distance,radius);this.beam.material.opacity=(night?.055:.025)*strength*(quality==='high'?1:.6);this.stats.beam=this.beam.visible;
  }
  if(this.stats.beam)this.stats.triangles+=32;
 }
 dispose(){for(const a of this.actors){this.scene.remove(a.group);a.group.traverse(o=>{if(o.isMesh)for(const m of list(o.material))m.dispose();});}this.scene.remove(this.light,this.light.target,this.beam);this.beam.geometry.dispose();this.beam.material.dispose();this.actors=[];}
}
