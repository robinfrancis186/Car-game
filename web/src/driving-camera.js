import * as THREE from 'three';
/** Render-only follow state. Aim smoothing stays relative to the car, not behind it. */
export class DrivingCameraFilter{
 reset(){this.position=null;this.offset=null;this.fov=null;}
 update(anchor,desired,target,fov,dt,{reset=false,paused=false}={}){
  const offset=target.clone().sub(anchor),step=paused?0:Math.max(0,Math.min(.1,Number.isFinite(dt)?dt:0));
  if(reset||!this.position){this.position=desired.clone();this.offset=offset;this.fov=fov;}
  else if(step){this.position.lerp(desired,1-Math.exp(-6*step));this.offset.lerp(offset,1-Math.exp(-12*step));this.fov+=(fov-this.fov)*(1-Math.exp(-3*step));}
  return {position:this.position.clone(),target:anchor.clone().add(this.offset),fov:this.fov};
 }
}
