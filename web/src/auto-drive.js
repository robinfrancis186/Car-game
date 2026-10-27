/** Pedal assistance only. Never changes steering, position, damage or collision rules. */
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
 const p=model.player,speed=Math.abs(p.speed),q=model.sampleRoute(p.s);
 let curvature=0,last=q,previousDistance=0;
 for(const d of [12,28,48]){const next=model.sampleRoute(Math.min(model.routeLength,p.s+d));curvature=Math.max(curvature,Math.abs(angle(next.heading-last.heading))/Math.max(1,d-previousDistance));last=next;previousDistance=d;}
 const cruise=input.ultraBoost?model.vehicleStats.ultraBoostMaxSpeedMps:input.boost?model.vehicleStats.regularBoostMaxSpeedMps:Math.min(model.vehicleStats.topSpeedMps*.78,model.scenario.id==='free-drive'?22:29);
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
