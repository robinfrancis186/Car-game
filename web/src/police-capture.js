/** Original non-graphic capture staging. Normal driving/reward rules stay in GameModel. */
import {GameModel} from './gameplay.js';
export const CAPTURE_DURATION=8;
const clamp=t=>Math.max(0,Math.min(1,t));
export const captureEase=t=>{t=clamp(t);return t*t*(3-2*t);};
const local=(car,x,z)=>({x:car.x+Math.cos(car.heading)*x-Math.sin(car.heading)*z,z:car.z+Math.sin(car.heading)*x+Math.cos(car.heading)*z});
const snapshot=v=>({...v});
export function capturePhase(elapsed){return elapsed<1.4?'exit':elapsed<4.8?'approach':elapsed<6.8?'secure':'complete';}
// Small visibility graph around the two stopped cars; never walk through a hood.
const carBox=car=>({car,halfLength:2.9,halfWidth:1.4});
const relative=(p,car)=>({x:(p.x-car.x)*Math.cos(car.heading)+(p.z-car.z)*Math.sin(car.heading),z:-(p.x-car.x)*Math.sin(car.heading)+(p.z-car.z)*Math.cos(car.heading)});
export function captureSegmentBlocked(a,b,boxes){
 return boxes.some(({car,halfLength,halfWidth})=>{
  const p=relative(a,car),q=relative(b,car);let near=0,far=1;
  for(const [key,extent]of [['x',halfLength],['z',halfWidth]]){
   const d=q[key]-p[key];if(Math.abs(d)<1e-8){if(Math.abs(p[key])>=extent)return false;continue;}
   const u=(-extent-p[key])/d,v=(extent-p[key])/d;near=Math.max(near,Math.min(u,v));far=Math.min(far,Math.max(u,v));if(near>=far)return false;
  }
  return far>1e-6&&near<1-1e-6;
 });
}
export function captureWalkPath(start,goal,cars){
 const boxes=cars.map(carBox),corners=boxes.flatMap(({car,halfLength,halfWidth})=>[-1,1].flatMap(x=>[-1,1].map(z=>local(car,x*(halfLength+.12),z*(halfWidth+.12)))));
 const nodes=[start,goal,...corners.filter(p=>!boxes.some(({car,halfLength,halfWidth})=>{const q=relative(p,car);return Math.abs(q.x)<halfLength&&Math.abs(q.z)<halfWidth;}))];
 const cost=nodes.map(()=>Infinity),previous=nodes.map(()=>-1),visited=new Set();cost[0]=0;
 while(visited.size<nodes.length){let next=-1;for(let i=0;i<nodes.length;i++)if(!visited.has(i)&&(next<0||cost[i]<cost[next]))next=i;if(next<0||!Number.isFinite(cost[next]))break;if(next===1){const path=[];for(let i=1;i!==-1;i=previous[i])path.unshift(nodes[i]);return path;}visited.add(next);
  for(let i=0;i<nodes.length;i++)if(!visited.has(i)&&!captureSegmentBlocked(nodes[next],nodes[i],boxes)){const d=cost[next]+Math.hypot(nodes[i].x-nodes[next].x,nodes[i].z-nodes[next].z);if(d<cost[i]){cost[i]=d;previous[i]=next;}}
 }
 // shortcut: static scenery has no pedestrian navmesh. A blocked staging site
 // remains a review limitation until authored walkable arrest areas are added.
 return [start,goal];
}
function stageCapture(model){
 const player=snapshot(model.player),patrol=model.police.filter(c=>c.visible!==false&&Math.abs(c.y-player.y)<1.5).sort((a,b)=>Math.hypot(a.x-player.x,a.z-player.z)-Math.hypot(b.x-player.x,b.z-player.z))[0];
 if(!patrol)return null;
 const cop=snapshot(patrol),side=(-(cop.x-player.x)*Math.sin(player.heading)+(cop.z-player.z)*Math.cos(player.heading))>=0?1:-1;
 const ground=point=>{const q=model.projectToRoute(point.x,point.z,player.s);return {...point,y:model._surfaceAt(q,player.y,player.onRoadDeck).y};};
 const suspect=ground(local(player,-.55,side*1.65));
 const officers=[-1,1].map((door,i)=>{
  const start=ground(local(cop,-.15,door*.65)),exit=ground(local(cop,-.15,door*1.65));
  const goal=local(player,i===0?-.55:.9,side*(i===0?2.2:2.1));
  const path=captureWalkPath(exit,goal,[cop,player]).map(ground);
  return {door,start,path};
 });
 return {elapsed:0,duration:CAPTURE_DURATION,phase:'exit',patrolId:cop.id,player,cop,side,suspect,officers,vehicles:[model.player,...model.rivals,...model.police].map(snapshot)};
}
export function sampleCapturePath(points,t){
 const lengths=points.slice(1).map((p,i)=>Math.hypot(p.x-points[i].x,p.z-points[i].z)),total=lengths.reduce((a,b)=>a+b,0);
 let remaining=clamp(t)*total;
 for(let i=0;i<lengths.length;i++){
  if(remaining<=lengths[i]||i===lengths.length-1){const a=points[i],b=points[i+1],u=lengths[i]>1e-8?remaining/lengths[i]:1;return {x:a.x+(b.x-a.x)*u,y:a.y+(b.y-a.y)*u,z:a.z+(b.z-a.z)*u,heading:Math.atan2(b.x-a.x,b.z-a.z)};}
  remaining-=lengths[i];
 }
 return {...points[0],heading:0};
}
export class CaptureGameModel extends GameModel{
 _initialize(){super._initialize();this.capture=null;this._captureTitle=null;}
 _end(state,title){
  if(state==='busted'&&this.state==='racing'){
   const capture=stageCapture(this);if(!capture)return super._end(state,title);
   this.capture=capture;this._captureTitle=title;this.state='capturing';this.pursuit='captured';
   this._airtime.cancel('capture');this._policeAir.stop();this._civilianAir.stop();this._stopUltra('capture');this._clearRecoveryWarning();
   this._freezeCapture();this._emit('capture-start','PATROL / DRIVER, STEP OUT');return;
  }
  if(this.state!=='capturing')super._end(state,title);
 }
 _freezeCapture(){
  const vehicles=[this.player,...this.rivals,...this.police];
  for(const v of vehicles){const pose=this.capture.vehicles.find(p=>p.id===v.id);if(pose)Object.assign(v,pose,{speed:0,velocityX:0,velocityZ:0,lateralSpeed:0,lateralVelocity:0,yawRate:0,steer:0,boosting:false,ultraBoosting:false,ultraRemaining:0,flying:false,thrusting:false,impactShake:0});}
 }
 _step(dt,input){super._step(dt,input);if(this.state==='capturing')this._freezeCapture();}
 update(dt,input={}){
  if(this.state!=='capturing')return super.update(dt,input);
  if(this.paused||!Number.isFinite(dt)||dt<=0)return this;
  const c=this.capture;c.elapsed=Math.min(c.duration,c.elapsed+Math.min(dt,.25));c.phase=capturePhase(c.elapsed);
  if(c.elapsed>=c.duration){
   // Settle through the existing single terminal/reward path, without a driving step.
   this.state='racing';super._end('busted',this._captureTitle);
  }
  return this;
 }
}
