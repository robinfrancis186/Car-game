/** Deterministic observational helicopter. Never changes arrest, damage or rewards. */
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),approach=(v,t,d)=>v<t?Math.min(t,v+d):Math.max(t,v-d),angle=v=>Math.atan2(Math.sin(v),Math.cos(v));
export class PoliceAirSupport {
 constructor(){this.reset();}
 reset(){this.clock=0;this.phaseTime=0;this.cooldown=0;this.lastKnown=null;this.state=Object.assign(this.state||{},{flightSeconds:0,pitch:0,roll:0,rotorRpm:0,verticalVelocity:0,active:false,visible:false,phase:'idle',x:0,y:0,z:0,heading:0,velocityX:0,velocityZ:0,beamVisible:false,beamTarget:{x:0,y:0,z:0},spotlightIntensity:0,highHeatSeconds:0,pursuitSeconds:0});return this.state;}
 stop(){this.reset();}
 recovery(){if(this.state.active){this.state.phase='search';this.phaseTime=0;this.state.beamVisible=false;this.state.spotlightIntensity=0;}}
 update(dt,{player,eligible=false,wanted=0,heat=0,arrestProgress=0,groundPoliceDistance=Infinity,floorAt=()=>0,lineOfSight=()=>true}){
  const h=this.state;this.clock+=dt;this.cooldown=Math.max(0,this.cooldown-dt);let event=null;
  const pursued=eligible&&wanted>0;
  h.pursuitSeconds=pursued?h.pursuitSeconds+dt:0;
  h.highHeatSeconds=pursued&&heat>=.76&&Math.abs(player.speed)>8&&arrestProgress<.2?h.highHeatSeconds+dt:0;
  if(!eligible){if(h.active)this.stop();return null;}
  if(!h.active&&this.cooldown===0&&h.pursuitSeconds>=30&&h.highHeatSeconds>=12&&groundPoliceDistance>12){
   h.x=player.x-Math.cos(player.heading)*240-Math.sin(player.heading)*110;h.z=player.z-Math.sin(player.heading)*240+Math.cos(player.heading)*110;h.y=Math.max(floorAt(h.x,h.z)+38,player.y+32);h.heading=player.heading;h.active=h.visible=true;h.phase='approach';this.phaseTime=0;this.lastKnown={x:player.x,y:player.y,z:player.z};event='air-support-dispatched';
  }
  if(!h.active)return event;this.phaseTime+=dt;h.flightSeconds+=dt;h.rotorRpm=420;
  const range=Math.hypot(player.x-h.x,player.z-h.z),canSee=wanted>0&&range<190&&lineOfSight({x:h.x,y:h.y-1,z:h.z},{x:player.x,y:player.y+.7,z:player.z});
  if(canSee){this.lastKnown={x:player.x,y:player.y,z:player.z};if(h.phase==='approach'||h.phase==='search'){h.phase='track';this.phaseTime=0;}}
  else if(h.phase==='track'||h.phase==='approach'&&!wanted){h.phase='search';this.phaseTime=0;}
  if(h.phase!=='withdraw'&&((h.phase==='search'&&this.phaseTime>8)||(h.phase==='approach'&&this.phaseTime>20)||range>650)){h.phase='withdraw';this.phaseTime=0;}
  let target;
  if(h.phase==='withdraw')target={x:h.x+Math.cos(h.heading)*180,z:h.z+Math.sin(h.heading)*180};
  else if(h.phase==='search'){const a=this.clock*.24;target={x:this.lastKnown.x+Math.cos(a)*65,z:this.lastKnown.z+Math.sin(a)*65};}
  else target={x:player.x-Math.cos(player.heading)*20-Math.sin(player.heading)*12,z:player.z-Math.sin(player.heading)*20+Math.cos(player.heading)*12};
  const dx=target.x-h.x,dz=target.z-h.z,len=Math.hypot(dx,dz),tracking=h.phase==='track'||h.phase==='approach',feedX=tracking?(Number.isFinite(player.velocityX)?player.velocityX:Math.cos(player.heading)*player.speed):0,feedZ=tracking?(Number.isFinite(player.velocityZ)?player.velocityZ:Math.sin(player.heading)*player.speed):0;
  const rawX=dx*1.2+feedX,rawZ=dz*1.2+feedZ,rawSpeed=Math.hypot(rawX,rawZ),limit=h.phase==='withdraw'?44:55,vx=rawSpeed?rawX*Math.min(1,limit/rawSpeed):0,vz=rawSpeed?rawZ*Math.min(1,limit/rawSpeed):0;
  h.velocityX+=(vx-h.velocityX)*(1-Math.exp(-1.6*dt));h.velocityZ+=(vz-h.velocityZ)*(1-Math.exp(-1.6*dt));
  const nextX=h.x+h.velocityX*dt,nextZ=h.z+h.velocityZ*dt,currentFloor=floorAt(h.x,h.z),nextFloor=floorAt(nextX,nextZ),lookFloor=floorAt(h.x+h.velocityX*2.5,h.z+h.velocityZ*2.5),desiredY=Math.max(currentFloor+38,nextFloor+38,lookFloor+38,player.y+24);
  const oldY=h.y;h.y=approach(h.y,desiredY,dt*(desiredY>h.y?9:5));h.verticalVelocity=(h.y-oldY)/dt;
  // Stop before entering a steep terrain/building edge until rotor clearance is
  // available; no horizontal teleport or snap through roofs to follow a player.
  if(h.y>=nextFloor+18){h.x=nextX;h.z=nextZ;}else{h.velocityX*=Math.exp(-6*dt);h.velocityZ*=Math.exp(-6*dt);}
  if(Math.hypot(h.velocityX,h.velocityZ)>.2)h.heading=angle(h.heading+clamp(angle(Math.atan2(h.velocityZ,h.velocityX)-h.heading),-dt*.8,dt*.8));
  h.pitch=-Math.min(.075,Math.hypot(h.velocityX,h.velocityZ)*.0014);h.roll=0;
  h.beamTarget=canSee?{x:player.x,y:player.y+.3,z:player.z}:{x:this.lastKnown.x,y:this.lastKnown.y+.3,z:this.lastKnown.z};
  const beamAngle=Math.atan2(Math.hypot(h.beamTarget.x-h.x,h.beamTarget.z-h.z),Math.max(.01,h.y-2-h.beamTarget.y));h.beamVisible=h.phase==='track'&&canSee&&beamAngle<=.62;h.spotlightIntensity=approach(h.spotlightIntensity,h.beamVisible?1:0,dt*3);
  if(h.phase==='withdraw'&&this.phaseTime>8){h.active=h.visible=h.beamVisible=false;h.phase='idle';h.spotlightIntensity=0;h.rotorRpm=0;h.highHeatSeconds=0;h.pursuitSeconds=0;this.cooldown=30;event='air-support-withdrawn';}
  return event;
 }
}

/** Sparse scenic pass, anchored once; never follows the player or affects police. */
export class CivilianAirTraffic {
 constructor(){this.reset();}
 reset(){this.clock=0;this.nextPass=12;this.path=null;this.state=Object.assign(this.state||{},{active:false,visible:false,phase:'idle',x:0,y:0,z:0,heading:0,pitch:0,roll:0,velocityX:0,velocityZ:0,verticalVelocity:0,rotorRpm:0,flightSeconds:0,beamVisible:false,beamTarget:{x:0,y:0,z:0},spotlightIntensity:0});return this.state;}
 stop(){this.reset();}
 update(dt,{eligible=false,player,anchor,floorAt=()=>0}){
  if(!eligible){if(this.state.active)this.stop();return null;}this.clock+=dt;const h=this.state;
  if(!h.active&&this.clock>=this.nextPass){const q=anchor(),a={x:q.x-q.nx*230+q.tx*150,z:q.z-q.nz*230+q.tz*150},b={x:q.x+q.nx*230+q.tx*150,z:q.z+q.nz*230+q.tz*150};let y=player.y+30;for(let i=0;i<=64;i++)y=Math.max(y,floorAt(a.x+(b.x-a.x)*i/64,a.z+(b.z-a.z)*i/64)+42);this.path={a,b,time:0,duration:460/28};Object.assign(h,{active:true,visible:true,phase:'crossing',x:a.x,y,z:a.z,heading:Math.atan2(b.z-a.z,b.x-a.x),rotorRpm:400,flightSeconds:0,velocityX:(b.x-a.x)/this.path.duration,velocityZ:(b.z-a.z)/this.path.duration});}
  if(!h.active)return null;this.path.time+=dt;h.flightSeconds+=dt;const t=Math.min(1,this.path.time/this.path.duration);h.x=this.path.a.x+(this.path.b.x-this.path.a.x)*t;h.z=this.path.a.z+(this.path.b.z-this.path.a.z)*t;h.pitch=-.025;
  if(t>=1){h.active=h.visible=false;h.phase='idle';h.rotorRpm=0;h.velocityX=h.velocityZ=0;this.nextPass=this.clock+90;this.path=null;}return null;
 }
}
