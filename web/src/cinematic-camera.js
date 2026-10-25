/** Original short drone-style shots. Pure snapshots: never advances or mutates the race. */
const finite=(v,f=0)=>Number.isFinite(v)?v:f;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const smooth=t=>t*t*t*(10+t*(-15+6*t));
export function validCinematicPose(p){return !!p&&['position','target'].every(k=>Array.isArray(p[k])&&p[k].length===3&&p[k].every(Number.isFinite))&&Number.isFinite(p.fov)&&p.fov>=35&&p.fov<=85&&Math.hypot(...p.position.map((v,i)=>v-p.target[i]))>.5;}
export function createCinematicShot(kind,model,{duration=kind==='finish'?3:4}={}){
 if(!['intro','finish'].includes(kind)||!model?.player)throw new TypeError('A supported shot and race model are required');
 const p=model.player,origin=[finite(p.x),finite(p.y,.18),finite(p.z)],heading=finite(p.heading),forward=[Math.cos(heading),Math.sin(heading)],right=[-forward[1],forward[0]];
 const target=[origin[0],origin[1]+.75,origin[2]],terrain=model.sampleTerrain?.(origin[0],origin[2]);
 let minimumY=Math.max(origin[1]+10,finite(terrain?.y)+10);
 // Respect authored building/rail volumes near the shot, not only flat ground.
 for(const o of model.obstacles||[])if(Math.hypot(o.x-origin[0],o.z-origin[2])<35+finite(o.radius))minimumY=Math.max(minimumY,finite(o.y)+finite(o.height)+3);
 const length=clamp(finite(duration,kind==='finish'?3:4),1,6);
 return Object.freeze({kind,duration:length,sample(elapsed){
  const t=smooth(clamp(finite(elapsed)/length,0,1)),finish=kind==='finish';
  const back=finish?8+4*t:22-12*t,side=finish?0:10-6*t,height=finish?origin[1]+2.6+1.4*t:minimumY+9-7*t;
  const x=origin[0]-forward[0]*back+right[0]*side,z=origin[2]-forward[1]*back+right[1]*side;
  const localGround=model.sampleTerrain?.(x,z),y=Math.max(height,finite(localGround?.y)+(finish?2.5:6));
  return {position:[x,y,z],target:[...target],fov:finish?57+4*t:64-7*t};
 }});
}
// Finish shots are not a general free-camera collision system. Only a narrow,
// grounded finish corridor is eligible; delayed escapes elsewhere show results.
export function isCanonicalFinish(model){
 const p=model?.player;if(!p||!['x','y','z','heading'].every(k=>Number.isFinite(p[k]))||!Number.isFinite(model.endS)||typeof model.sampleRoute!=='function'||!Number.isFinite(p.s)||(p.s<model.endS-11||p.s>model.endS+20)||p.grounded!==true||finite(p.altitude)>.08||p.flipActive||p.flying)return false;
 const q=model.sampleRoute(p.s),end=model.sampleRoute(model.endS);if(!Number.isFinite(q.y)||Math.abs(p.y-q.y)>.08||(p.s<model.endS&&Math.hypot(p.x-end.x,p.z-end.z)>11))return false;
 const heading=finite(q.heading),dx=p.x-q.x,dz=p.z-q.z,offset=-Math.sin(heading)*dx+Math.cos(heading)*dz,delta=Math.atan2(Math.sin(p.heading-heading),Math.cos(p.heading-heading));
 return Number.isFinite(offset)&&Math.abs(offset)<=1.9&&Number.isFinite(delta)&&Math.abs(delta)<=.15;
}
