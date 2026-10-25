/** Camera for the explicitly opt-in surface test. Normal race cameras do not use it. */
import * as THREE from 'three';

const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function validSurfaceFrame(frame){
 if(!frame||!['forward','up','right'].every(k=>Array.isArray(frame[k])&&frame[k].length===3&&frame[k].every(Number.isFinite)))return false;
 const [f,u,r]=['forward','up','right'].map(k=>new THREE.Vector3(...frame[k]));
 return [f,u,r].every(v=>Math.abs(v.lengthSq()-1)<.002)&&Math.abs(f.dot(u))<.002&&Math.abs(f.dot(r))<.002&&Math.abs(u.dot(r))<.002&&new THREE.Vector3().crossVectors(f,u).dot(r)>.998;
}
export function surfaceQuaternion(frame){
 if(!validSurfaceFrame(frame))return null;
 return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(...['forward','up','right'].map(k=>new THREE.Vector3(...frame[k]))));
}

export class SurfaceCameraRig{
 constructor(){this.position=new THREE.Vector3();this.orientation=new THREE.Quaternion();this.ready=false;}
 reset(){this.ready=false;}
 update(state,dt,{mode=0,orbitYaw=0,orbitPitch=.12,reset=false,paused=false,projectSurface=null}={}){
  const basis=surfaceQuaternion(state.surfaceFrame);if(!basis)return null;
  const step=paused?0:clamp(Number(dt)||0,0,.1),snap=reset||!this.ready;
  if(snap)this.orientation.copy(basis);else this.orientation.slerp(basis,1-Math.exp(-step*8));
  const forward=new THREE.Vector3(1,0,0).applyQuaternion(basis),up=new THREE.Vector3(0,1,0).applyQuaternion(basis),right=new THREE.Vector3(0,0,1).applyQuaternion(basis);
  const pos=new THREE.Vector3(state.x,state.y,state.z),lookUp=new THREE.Vector3(0,1,0).applyQuaternion(this.orientation);
  let desired,target;
  if(mode===1){desired=pos.clone().addScaledVector(forward,1.18).addScaledVector(up,1.08);target=pos.clone().addScaledVector(forward,35).addScaledVector(up,.9);}
  else{const back=forward.clone().multiplyScalar(Math.cos(orbitYaw)).addScaledVector(right,Math.sin(orbitYaw));desired=pos.clone().addScaledVector(back,mode===2?-11.5:-8.2).addScaledVector(up,mode===2?5:3.3+clamp(orbitPitch,-.3,1.1));target=pos.clone().addScaledVector(forward,3.4*Math.max(0,1-Math.abs(orbitYaw)/.8)).addScaledVector(up,.8);}
  if(snap||mode===1)this.position.copy(desired);else this.position.lerp(desired,1-Math.exp(-step*7));
  // Keep the chase camera on the visible side of the actual ribbon, not merely
  // above world Y. This is local clearance, not universal scene collision avoidance.
  if(state.attached&&mode!==1&&projectSurface){const q=projectSurface(this.position.toArray());if(q&&q.inside&&Array.isArray(q.normal)&&q.normal.every(Number.isFinite)&&Number.isFinite(q.distance)&&q.distance<1.15)this.position.addScaledVector(new THREE.Vector3(...q.normal),1.15-q.distance);}
  this.position.y=Math.max(this.position.y,1.1);this.ready=true;
  return{position:this.position.clone(),target,up:lookUp,mode};
 }
}
