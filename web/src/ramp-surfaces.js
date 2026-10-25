/** Explicit upright wedge support only. No wall/ceiling adhesion or loop physics. */
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function normalizeRamps(raw=[],routeLength=Infinity){
 const ids=new Set();return(Array.isArray(raw)?raw:[]).flatMap((r,i)=>{
  if(!r||![r.startS,r.lipS,r.rise].every(Number.isFinite)||r.startS<0||r.lipS>routeLength||r.lipS-r.startS<5||r.lipS-r.startS>150||r.rise<.5||r.rise>8||r.rise/(r.lipS-r.startS)>.35)return[];
  const id=typeof r.id==='string'&&r.id.length?r.id:'ramp-'+i;if(ids.has(id))return[];ids.add(id);
  return[{id,startS:r.startS,lipS:r.lipS,rise:r.rise,centerOffset:Number.isFinite(r.centerOffset)?clamp(r.centerOffset,-30,30):0,halfWidth:Number.isFinite(r.halfWidth)?clamp(r.halfWidth,1.5,8):3.6,minSpeed:Number.isFinite(r.minSpeed)?clamp(r.minSpeed,8,35):12,enabledScenarios:Array.isArray(r.enabledScenarios)?r.enabledScenarios.filter(s=>typeof s==='string'):null}];
 });
}
export function rampSupport(ramps,q,scenario){
 let result=null;for(const r of ramps){if(r.enabledScenarios&&!r.enabledScenarios.includes(scenario)||q.s<r.startS||q.s>r.lipS||Math.abs((q.offset??q.lane??0)-r.centerOffset)>r.halfWidth)continue;
  const rise=r.rise*(q.s-r.startS)/(r.lipS-r.startS),grade=(q.grade||0)+r.rise/(r.lipS-r.startS),surface={y:q.y+rise,grade,heading:q.heading,gradientX:grade*q.tx,gradientZ:grade*q.tz,layer:'road',rampId:r.id,ramp:r};if(!result||surface.y>result.y)result=surface;
 }return result;
}
export function rampLaunch(surface,after,velocityX,velocityZ,heading){
 if(!surface?.ramp||after.s<surface.ramp.lipS||Math.abs((after.offset??0)-surface.ramp.centerOffset)>surface.ramp.halfWidth-.25)return null;
 const along=velocityX*after.tx+velocityZ*after.tz;if(along<surface.ramp.minSpeed||Math.cos(heading-after.heading)<.7)return null;
 const verticalSpeed=Math.min(14,along*surface.grade);return verticalSpeed>1?{rampId:surface.rampId,verticalSpeed,alongSpeed:along}:null;
}
