/** Original finite analytic ribbon. +X forward, +Y up, +Z right. No ceiling/loop. */
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const vec={add:(a,b)=>a.map((x,i)=>x+b[i]),sub:(a,b)=>a.map((x,i)=>x-b[i]),scale:(a,s)=>a.map(x=>x*s),dot:(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],length:a=>Math.hypot(...a),normalize:a=>{const n=Math.hypot(...a);return n>1e-12?a.map(x=>x/n):[1,0,0];}};
export function normalizeRibbonProfile(raw){
 if(!raw||raw.schemaVersion!==1||raw.interpolation!=='quintic-smoothstep'||raw.sign!=='positive-right-rises'||!Number.isFinite(raw.length)||raw.length<100||raw.length>10000||!Number.isFinite(raw.baseY)||raw.baseY<7||raw.baseY>1000||!Number.isFinite(raw.halfWidth)||raw.halfWidth<3||raw.halfWidth>30||raw.halfWidth>raw.baseY-1||!Array.isArray(raw.bankKnots)||raw.bankKnots.length<2)throw new TypeError('Invalid finite ribbon profile');
 const knots=raw.bankKnots.map(k=>{if(!k||!Number.isFinite(k.s)||!Number.isFinite(k.degrees)||k.degrees<0||k.degrees>90)throw new TypeError('Ribbon supports 0–90 degree banking only');return Object.freeze({s:k.s,degrees:k.degrees});});
 if(knots[0].s!==0||knots.at(-1).s!==raw.length||knots[0].degrees!==0||knots.at(-1).degrees!==0||knots.some((k,i)=>i&&k.s<=knots[i-1].s))throw new RangeError('Ribbon knots must span its finite length with flat endpoints');
 return Object.freeze({schemaVersion:1,id:String(raw.id||'surface-proof'),label:String(raw.label||'SOLO SURFACE PROOF'),length:raw.length,baseY:raw.baseY,halfWidth:raw.halfWidth,bankKnots:Object.freeze(knots),interpolation:raw.interpolation,sign:raw.sign});
}
export function bankAt(profile,s){
 const k=profile.bankKnots;s=clamp(Number.isFinite(s)?s:0,0,profile.length);let i=1;while(i<k.length-1&&s>k[i].s)i++;
 const a=k[i-1],b=k[i],length=b.s-a.s,t=clamp((s-a.s)/length,0,1),delta=(b.degrees-a.degrees)*Math.PI/180;
 return {beta:a.degrees*Math.PI/180+delta*(6*t**5-15*t**4+10*t**3),betaPrime:delta*(30*t**4-60*t**3+30*t**2)/length,betaSecond:delta*(120*t**3-180*t**2+60*t)/(length*length)};
}
export function sampleRibbon(profile,s,l=0){
 if(!Number.isFinite(s)||!Number.isFinite(l))throw new TypeError('Finite surface coordinates required');
 const requestedS=s;s=clamp(s,0,profile.length);const {beta,betaPrime,betaSecond}=bankAt(profile,s),sin=Math.sin(beta),cos=Math.cos(beta),ds=[1,l*cos*betaPrime,-l*sin*betaPrime],dl=[0,sin,cos],metric=Math.hypot(...ds),forward=vec.scale(ds,1/metric),right=dl,up=vec.normalize(vec.cross(right,forward));
 return {s,l,requestedS,insideRange:requestedS>=0&&requestedS<=profile.length&&Math.abs(l)<=profile.halfWidth,position:[s,profile.baseY+l*sin,l*cos],forward,up,right,ds,dl,dss:[0,l*(cos*betaSecond-sin*betaPrime*betaPrime),-l*(sin*betaSecond+cos*betaPrime*betaPrime)],dsl:[0,cos*betaPrime,-sin*betaPrime],metric,beta,betaPrime,betaSecond};
}
export function projectRibbon(profile,point){
 if(!Array.isArray(point)||point.length!==3||!point.every(Number.isFinite))throw new TypeError('Finite world point required');
 let s=clamp(point[0],0,profile.length),bank=bankAt(profile,s),l=(point[1]-profile.baseY)*Math.sin(bank.beta)+point[2]*Math.cos(bank.beta),sample;
 for(let n=0;n<8;n++){sample=sampleRibbon(profile,s,l);const error=vec.sub(point,sample.position),ds=vec.dot(error,sample.forward)/sample.metric,dl=vec.dot(error,sample.right);s=clamp(s+ds,0,profile.length);l+=dl;if(Math.abs(ds)+Math.abs(dl)<1e-10)break;}
 sample=sampleRibbon(profile,s,l);const delta=vec.sub(point,sample.position);return {...sample,insideRange:point[0]>=0&&point[0]<=profile.length&&Math.abs(l)<=profile.halfWidth,signedDistance:vec.dot(delta,sample.up),distance:vec.length(delta),delta};
}
export function vehicleFrame(sample,yaw=0){const c=Math.cos(yaw),s=Math.sin(yaw);return {forward:vec.add(vec.scale(sample.forward,c),vec.scale(sample.right,s)),up:[...sample.up],right:vec.add(vec.scale(sample.right,c),vec.scale(sample.forward,-s))};}
