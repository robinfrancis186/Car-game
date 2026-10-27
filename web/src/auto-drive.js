/** Original input assistance. Neither mode changes physical state or collision rules. */
const angle=a=>Math.atan2(Math.sin(a),Math.cos(a));
// Read the model's existing collision index; never change its contents or physics.
export function nearbyObstacles(model,x,z,radius=32){
 const found=new Set(model._dynamicObstacles||[]);radius=Math.max(0,Math.min(80,radius));
 for(let gx=Math.floor((x-radius)/32);gx<=Math.floor((x+radius)/32);gx++)for(let gz=Math.floor((z-radius)/32);gz<=Math.floor((z+radius)/32);gz++)for(const o of model._obstacleGrid?.get(gx+','+gz)||[])found.add(o);
 return [...found];
}

// Distance to the forward driving corridor. Use actual box extents rather than
// their broad-phase radius, so a long roadside wall cannot stop a clear lane.
function forwardGap(p,o,look){
 const fx=Math.cos(p.heading),fz=Math.sin(p.heading),dx=p.x-o.x,dz=p.z-o.z;
 if(o.shape!=='box'&&Number.isFinite(o.endX)&&Number.isFinite(o.endZ)){
  const length=Math.hypot(o.endX-o.x,o.endZ-o.z);if(length>.001)return forwardGap(p,{...o,shape:'box',x:(o.x+o.endX)/2,z:(o.z+o.endZ)/2,heading:Math.atan2(o.endZ-o.z,o.endX-o.x),halfLength:length/2+o.radius,halfWidth:o.radius},look);
 }
 if(o.shape==='box'){
  const c=Math.cos(o.heading||0),s=Math.sin(o.heading||0);let enter=0,leave=look;
  for(const [origin,direction,extent]of [[dx*c+dz*s,fx*c+fz*s,(o.halfLength??1)+1.05],[-dx*s+dz*c,-fx*s+fz*c,(o.halfWidth??1)+1.05]]){
   if(Math.abs(direction)<1e-8){if(Math.abs(origin)>extent)return Infinity;}
   else{let a=(-extent-origin)/direction,b=(extent-origin)/direction;if(a>b)[a,b]=[b,a];enter=Math.max(enter,a);leave=Math.min(leave,b);}
  }
  return leave>=enter?Math.max(0,enter-3):Infinity;
 }
 const ahead=-dx*fx-dz*fz,lateral=Math.abs(dx*fz-dz*fx),radius=(o.radius??1.3)+1.05;
 if(ahead<=0||lateral>=radius)return Infinity;
 const entry=ahead-Math.sqrt(radius*radius-lateral*lateral);return entry<look?Math.max(0,entry-3):Infinity;
}
export function autoPedals(model,input,enabled,{paused=false}={}){
 if(!enabled)return input;
 if(paused||model.paused||model.state!=='racing')return {...input,throttle:0,brake:false,boost:false,ultraBoost:false};
 if(input.brake)return {...input,throttle:0,brake:true};
 const p=model.player,speed=Math.abs(p.speed),q=model.sampleRoute(p.s);
 let curvature=0,last=q,previousDistance=0;
 for(const d of [12,28,48]){const next=model.sampleRoute(Math.min(model.routeLength,p.s+d));curvature=Math.max(curvature,Math.abs(angle(next.heading-last.heading))/Math.max(1,d-previousDistance));last=next;previousDistance=d;}
 const cruise=input.ultraBoost||p.ultraBoosting?model.vehicleStats.ultraBoostMaxSpeedMps:input.boost?model.vehicleStats.regularBoostMaxSpeedMps:Math.min(model.vehicleStats.topSpeedMps*.78,model.scenario.id==='free-drive'?22:29);
 let target=Math.min(cruise,Math.sqrt(5.5/Math.max(.001,curvature)));
 // A driver must still steer back onto the road; assistance does not recover or turn the car.
 const headingError=Math.abs(angle(p.heading-q.heading));
 if(p.offRoad||headingError>.7)target=Math.min(target,8);
 const brakeRate=Math.max(8,model.vehicleStats.brakeDecelerationMps2*.65),look=Math.min(65,12+speed*2);
 const nearby=nearbyObstacles(model,p.x,p.z,look);
 for(const o of [...nearby,...(model.rivals||[]),...(model.police||[])]){
  if(o.visible===false||o.active===false||o===p)continue;
  const bottom=o.y??0,top=bottom+(o.height??1.5);if(bottom>p.y+1.7||top<p.y+.1)continue;
  const gap=forwardGap(p,o,look);if(Number.isFinite(gap))target=Math.min(target,Math.sqrt(2*brakeRate*gap));
 }
 const brake=speed>target+1.2;
 return {...input,throttle:brake?0:Math.max(0,Math.min(1,(target-speed)/3)),brake};
}

const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const approach=(x,y,d)=>x<y?Math.min(y,x+d):Math.max(y,x-d);
const neutral=input=>({...input,throttle:0,steer:0,brake:false,boost:false,ultraBoost:false,flight:false,flip:false,lift:0});
// Invert the existing rack envelope/shape; the unchanged model still owns tire
// grip, yaw relaxation, collisions and the physical steering response.
function steeringInput(wheel,speed,model){
 const smooth=x=>x*x*(3-2*x),park=smooth(clamp(speed/10,0,1)),road=smooth(clamp((speed-3)/15,0,1));
 const grip=model.player.offRoad&&model.player.altitude<.5?8.5:14.5*model.vehicleStats.gripMultiplier;
 const envelope=Math.min(model.maxSteer*(1-.28*park),Math.atan(2.7*grip*(1-.28*road)/(speed*speed+16)));
 return Math.sign(wheel)*Math.pow(clamp(Math.abs(wheel)/Math.max(.001,envelope),0,1),1/1.35);
}
function laneOffset(model,q,lane){
 const section=(model.roadSections||[]).find(s=>q.s>=s.startS&&q.s<=s.endS),strips=section?.driveableStrips||[{centerOffset:0,halfWidth:section?.halfWidth??3.6}];
 // Follow an existing carriageway; never choose a junction or cross its median.
 const strip=strips.reduce((a,b)=>Math.abs(q.offset-(b.centerOffset||0))<Math.abs(q.offset-(a.centerOffset||0))?b:a),center=strip.centerOffset||0;
 const halfWidth=strip.halfWidth??3.6,base=Math.abs(center)<halfWidth-1.4?0:center;
 const spacing=Math.min(1.5,Math.max(0,halfWidth-1.4));return base+lane*spacing;
}
/** Original bounded road-following input assist, not a teleport or route AI. */
export class RoadAssistController{
 constructor(){this.reset();}
 reset(){this._lane=0;this._clearMotion();return this;}
 _clearMotion(){this._model=null;this._offset=null;this._braking=false;this._brakeTime=0;this._direction=1;this._recoveries=null;this._mode=null;}
 get lane(){return this._lane;}
 setLane(lane){if(lane===-1||lane===0||lane===1)this._lane=lane;return this._lane;}
 chooseLane(direction=1){if(direction===-1||direction===1)this._lane=clamp(this._lane+direction,-1,1);return this._lane;}
 update(model,rawInput,enabled,{dt=1/60,paused=false,mode='road'}={}){
  if(!enabled){this._clearMotion();return rawInput;}
  if(paused||model.paused||model.state!=='racing'||model.isSurfaceTest){this._clearMotion();return neutral(rawInput);}
  if(mode==='pedals'){this._clearMotion();return autoPedals(model,rawInput,true);}
  const p=model.player,speed=Math.abs(p.speed),q=model.projectToRoute(p.x,p.z,p.s);dt=clamp(Number.isFinite(dt)?dt:0,0,.1);
  if(this._model!==model||this._recoveries!==model.recoveries||this._mode!==mode){this._offset=q.offset;this._braking=false;this._brakeTime=0;this._direction=model.scenario.id==='free-drive'&&Math.cos(p.heading-q.heading)<0?-1:1;}
  this._model=model;this._recoveries=model.recoveries;this._mode=mode;
  const direction=this._direction,desiredOffset=laneOffset(model,q,this._lane*direction);this._offset=approach(this._offset,desiredOffset,dt*1.4);
  const look=clamp(5+speed*.55,6,18),ahead=model.sampleRoute(clamp(q.s+direction*look,0,model.routeLength));
  const targetX=ahead.x+ahead.nx*this._offset,targetZ=ahead.z+ahead.nz*this._offset,dx=targetX-p.x,dz=targetZ-p.z,distance=Math.max(2,Math.hypot(dx,dz));
  const error=angle(Math.atan2(dz,dx)-p.heading),wheel=Math.atan(2*2.7*Math.sin(error)/distance),steer=steeringInput(wheel,speed,model);
  const boosted=rawInput.ultraBoost||p.ultraBoosting?model.vehicleStats.ultraBoostMaxSpeedMps:rawInput.boost?model.vehicleStats.regularBoostMaxSpeedMps:Math.min(model.vehicleStats.topSpeedMps*.78,model.scenario.id==='free-drive'?22:26);
  let target=boosted;const comfortBrake=4;let previous=model.sampleRoute(clamp(q.s-direction*2,0,model.routeLength));
  for(let d=2;d<=64;d+=4){const at=model.sampleRoute(clamp(q.s+direction*d,0,model.routeLength)),curvature=Math.abs(angle(at.heading-previous.heading))/4;if(curvature>.0005)target=Math.min(target,Math.sqrt(3.5/curvature+2*comfortBrake*Math.max(0,d-7)));previous=at;}
  const laneError=Math.abs(q.offset-desiredOffset);if(laneError>5)target=Math.min(target,4);else if(laneError>3)target=Math.min(target,6);else if(Math.abs(error)>.5)target=Math.min(target,8);
  if(model.scenario.id==='free-drive'){const remaining=direction>0?model.routeLength-q.s:q.s;target=Math.min(target,Math.sqrt(2*comfortBrake*Math.max(0,remaining-5)));}
  const obstacleLook=Math.min(80,14+speed*2.5);let gap=Infinity;
  for(const o of [...nearbyObstacles(model,p.x,p.z,obstacleLook),...(model.rivals||[]),...(model.police||[])]){if(o.visible===false||o.active===false||o===p)continue;const bottom=o.y??0,top=bottom+(o.height??1.5);if(bottom>p.y+1.7||top<p.y+.1)continue;gap=Math.min(gap,forwardGap(p,o,obstacleLook));}
  if(Number.isFinite(gap))target=Math.min(target,Math.sqrt(2*comfortBrake*gap));
  if(rawInput.brake){this._braking=true;this._brakeTime=0;return {...rawInput,steer,throttle:0,brake:true};}
  this._brakeTime+=dt;const hold=target<.2&&speed<2;
  if(hold||speed>target+1.2)this._braking=true;
  else if(this._brakeTime>.12&&speed<target-.3){this._braking=false;this._brakeTime=0;}
  const throttle=this._braking?0:clamp((target-speed)*.6+.03+speed*speed*.00165/11.7,0,1);
  return {...rawInput,steer,throttle,brake:this._braking};
 }
}
