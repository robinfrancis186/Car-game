/** Session-only render comparison and passive frame telemetry; no game/save state. */
const finite=(n,f)=>Number.isFinite(n)?n:f;
export const RENDER_RESOLUTIONS=Object.freeze(['auto','full','standard']);
export function renderPixelRatio(deviceRatio,quality='high',mode='auto'){
 const d=(Number.isFinite(deviceRatio)&&deviceRatio>0?deviceRatio:1),m=RENDER_RESOLUTIONS.includes(mode)?mode:'auto';
 return Math.min(d,m==='standard'?1:m==='full'?1.6:quality==='high'?1.6:1);
}
export function configureOpaqueSky(sky){
 // Opaque depth is established before expensive cloud shading. Transparent
 // glass/water still renders later in Three's separate transparent queue.
 if(!sky?.material||sky.material.transparent)throw new TypeError('Sky must remain opaque');
 sky.renderOrder=1000;sky.material.depthTest=true;sky.material.depthWrite=false;return sky;
}
export class RenderFrameWindow{
 constructor(seconds=5){this.seconds=Math.max(1,finite(seconds,5));this.reset();}
 reset(key=''){this.key=key;this.elapsed=0;this.rows=[];this.total=0;this.active=false;}
 sample(dt,{active=true,key=''}={}){
  if(!active||!Number.isFinite(dt)||dt<=0||dt>1){this.reset(key);return;}
  if(this.key!==key)this.reset(key);this.active=true;this.elapsed+=dt;this.rows.push(dt);this.total+=dt;
  while(this.rows.length>1&&this.total-this.rows[0]>=this.seconds){this.total-=this.rows.shift();}
  // Bound memory even on very high-refresh displays. Such windows remain
  // descriptive telemetry, not an exact hardware or capture-free benchmark.
  if(this.rows.length>2400){this.total-=this.rows.shift();}
 }
 snapshot(){const values=[...this.rows].sort((a,b)=>a-b),n=values.length,p=q=>n?values[Math.min(n-1,Math.floor((n-1)*q))]*1000:0;
  return {active:this.active,stable:this.active&&this.elapsed+1e-8>=this.seconds&&n>=20,warmupSeconds:Math.max(0,this.seconds-this.elapsed),windowSeconds:this.total,frames:n,fps:this.total?n/this.total:0,medianMs:p(.5),p95Ms:p(.95)};
 }
}
