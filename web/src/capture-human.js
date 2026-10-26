/** CC0 anatomical mesh, original garment and deterministic skeletal staging. */
import * as THREE from 'three';
import {clone} from 'three/addons/utils/SkeletonUtils.js';
const V=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
// Calibrated on deformed near/mobile skin, including both roadside orientations.
const GRIP={l:{palm:.0635,radius:.0512},r:{palm:.0692,radius:.0575}};
export class CaptureHuman{
 constructor(templates,name){
  this.root=new THREE.Group();this.root.name=name;this.lods={};
  for(const [lod,template]of Object.entries(templates)){
   if(!template)throw Error(`Missing skinned capture asset: ${name}/${lod}`);
   const model=clone(template),bones={},rest={};model.traverse(o=>{if(o.isBone)bones[o.name]=o;if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;}});this.root.add(model);this.root.updateMatrixWorld(true);
   for(const [n,b]of Object.entries(bones))rest[n]={position:b.position.clone(),quaternion:b.quaternion.clone(),worldQuaternion:b.getWorldQuaternion(new THREE.Quaternion())};
   const limbs={};for(const side of ['l','r'])for(const [kind,a,b,c]of [['arm','upperarm','lowerarm','hand'],['leg','thigh','calf','foot']]){
    const names=[a,b,c].map(n=>n+'_'+side);if(names.some(n=>!bones[n]))throw Error('Capture skeleton missing '+names);
    limbs[kind+'_'+side]={names,lengths:[bones[names[0]].getWorldPosition(V()).distanceTo(bones[names[1]].getWorldPosition(V())),bones[names[1]].getWorldPosition(V()).distanceTo(bones[names[2]].getWorldPosition(V()))]};
   }
   this.lods[lod]={model,bones,rest,limbs};model.visible=false;
  }
  this.useLOD('near');this.contactErrors=[];
 }
 useLOD(lod){if(this.lod===lod)return;this.lod=lod;this.rig=this.lods[lod];for(const [key,rig]of Object.entries(this.lods))rig.model.visible=key===lod;}
 point(x,y,z){return this.root.localToWorld(V(x,y,z));}
 joint(name){return this.rig.bones[name].getWorldPosition(V());}
 direction(name,child,target,blend=1){
  const bone=this.rig.bones[name],start=this.joint(name),from=this.joint(child).sub(start).normalize(),to=target.clone().sub(start).normalize();
  const q=new THREE.Quaternion().setFromUnitVectors(from,to).multiply(bone.getWorldQuaternion(new THREE.Quaternion()));
  bone.quaternion.slerp(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(q),blend);bone.updateWorldMatrix(false,true);
 }
 solve(kind,side,target,pole){
  const {names:[a,b,c],lengths:[l1,l2]}=this.rig.limbs[kind+'_'+side],h=this.joint(a),delta=target.clone().sub(h),requested=delta.length(),d=clamp(requested,Math.abs(l1-l2)+.0001,l1+l2-.0001),direction=delta.normalize();
  const along=(l1*l1-l2*l2+d*d)/(2*d),bend=pole.clone().sub(h);bend.addScaledVector(direction,-bend.dot(direction));if(bend.lengthSq()<1e-8)bend.set(1,0,0);bend.normalize();
  const elbow=h.clone().addScaledVector(direction,along).addScaledVector(bend,Math.sqrt(Math.max(0,l1*l1-along*along))),end=h.clone().addScaledVector(direction,d);
  this.direction(a,b,elbow);this.direction(b,c,end);return this.joint(c).distanceTo(target);
 }
 reach(side,target,blend=1){
  const goal=this.joint('hand_'+side).lerp(target,blend),error=this.solve('arm',side,goal,this.point(side==='l'?.65:-.65,1.15,-.15));
  // The palm follows its actual middle-finger axis; no assumed bone Euler axes.
  this.direction('hand_'+side,'middle_01_'+side,this.joint('hand_'+side).add(this.point(0,-.02,.12).sub(this.point(0,0,0))));
  return error;
 }
 orientHand(side,across,forward,blend){
  const bone=this.rig.bones['hand_'+side],x=this.joint('index_01_'+side).sub(this.joint('pinky_01_'+side)).normalize(),y=this.joint('middle_01_'+side).sub(this.joint('hand_'+side));y.addScaledVector(x,-y.dot(x)).normalize();
  const from=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x,y,x.clone().cross(y))),to=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(across,forward,across.clone().cross(forward)));
  const desired=to.multiply(from.invert()).multiply(bone.getWorldQuaternion(new THREE.Quaternion()));bone.quaternion.slerp(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(desired),blend);bone.updateWorldMatrix(false,true);
 }
 grasp(side,target,axis,blend){
  const outward=this.point(0,1.25,0).sub(target);outward.addScaledVector(axis,-outward.dot(axis)).normalize();
  const forward=axis.clone().cross(outward).normalize().multiplyScalar(side==='l'?1:-1),across=axis.clone().multiplyScalar(side==='l'?1:-1),palmLength=this.joint('hand_'+side).distanceTo(this.joint('middle_01_'+side));
  const palmTarget=target.clone().addScaledVector(outward,GRIP[side].palm+(1-blend)*.09),wristGoal=palmTarget.clone().addScaledVector(forward,-palmLength*.5);
  this.reach(side,wristGoal,blend);this.orientHand(side,across,forward,blend);
  for(let iteration=0;iteration<2;iteration++){const palm=this.joint('hand_'+side).lerp(this.joint('middle_01_'+side),.5),correction=palmTarget.clone().sub(palm).multiplyScalar(blend);this.reach(side,this.joint('hand_'+side).add(correction));this.orientHand(side,across,forward,blend);}
  const curl=blend*blend*(3-2*blend),radius=GRIP[side].radius+(1-blend)*.02;
  for(const finger of ['index','middle','ring','pinky','thumb']){
   const turn=finger==='thumb'?-1:1;
   for(let joint=1;joint<=3;joint++){
    const name=`${finger}_0${joint}_${side}`,child=joint<3?`${finger}_0${joint+1}_${side}`:null,start=this.joint(name),relative=start.clone().sub(target),axial=relative.dot(axis),center=target.clone().addScaledVector(axis,axial),radial=start.clone().sub(center),r0=radial.length(),length=child?start.distanceTo(this.joint(child)):.017;
    const angle=Math.atan2(radial.dot(forward),radial.dot(outward)),cosine=clamp((r0*r0+radius*radius-length*length)/(2*Math.max(.001,r0)*radius),-1,1),next=angle+turn*Math.acos(cosine),goal=center.addScaledVector(outward,Math.cos(next)*radius).addScaledVector(forward,Math.sin(next)*radius);
    if(child)this.direction(name,child,goal,curl);
    else{const bone=this.rig.bones[name],from=V(0,1,0).applyQuaternion(bone.getWorldQuaternion(new THREE.Quaternion())),to=goal.sub(start).normalize(),q=new THREE.Quaternion().setFromUnitVectors(from,to).multiply(bone.getWorldQuaternion(new THREE.Quaternion()));bone.quaternion.slerp(bone.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(q),curl);bone.updateWorldMatrix(false,true);}
   }
  }
  this.gripTargets??={};this.gripTargets[side]={center:target.clone(),axis:axis.clone(),radius:.022};
  return this.joint('hand_'+side).lerp(this.joint('middle_01_'+side),.5).distanceTo(palmTarget);
 }

 pose({seated=0,walk=0,time=0,surrender=0,secured=0}={}){
  for(const [n,b]of Object.entries(this.rig.bones)){b.position.copy(this.rig.rest[n].position);b.quaternion.copy(this.rig.rest[n].quaternion);}
  this.root.updateWorldMatrix(true,true);
  const root=this.rig.bones.Root,world=root.getWorldPosition(V());world.y-=.44*seated;root.position.copy(root.parent.worldToLocal(world));this.root.updateWorldMatrix(true,true);
  for(const [side,sign,phase]of [['l',1,0],['r',-1,Math.PI]]){
   const stride=Math.sin(time*7+phase)*walk;
   const ankle=this.point(sign*(.19-.02*seated),.075+Math.max(0,stride)*.05,.46*seated+stride*.16);
   if(seated||walk){this.solve('leg',side,ankle,this.point(sign*.15,.55,1));const foot=this.rig.bones['foot_'+side],q=this.root.getWorldQuaternion(new THREE.Quaternion()).multiply(this.rig.rest[foot.name].worldQuaternion);foot.quaternion.copy(foot.parent.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(q));foot.updateWorldMatrix(false,true);}
   const standing=V(sign*.275,.88+Math.max(0,stride)*.05,-stride*.10),sitting=V(sign*.22,.79,.28),raised=V(sign*.34,1.58,.04),cuffed=V(sign*.09,1.08,-.20);
   const wrist=standing.lerp(sitting,seated).lerp(raised,surrender).lerp(cuffed,secured);this.reach(side,this.root.localToWorld(wrist));
  }
  this.root.updateWorldMatrix(true,true);
 }
}
