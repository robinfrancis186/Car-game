/** Original scenic transit motion: distance-parametrized track, station dwells,
 * independent carriage tangents and a restrained ferry turn/bob. No network or
 * traffic simulation. Geometry is authored separately in Blender. */
import * as THREE from 'three';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const mix=(a,b,t)=>a+(b-a)*t;
const smooth=t=>t*t*(3-2*t);
const angle=a=>Math.atan2(Math.sin(a),Math.cos(a));
export class TransitPath {
 constructor(points){
  if(!Array.isArray(points)||points.length<2)throw new Error('Transit path needs two points');
  this.points=points.map(p=>new THREE.Vector3(...p));this.segments=[];this.length=0;
  for(let i=0;i<this.points.length-1;i++){const a=this.points[i],b=this.points[i+1],length=a.distanceTo(b);if(length<.0001)continue;this.segments.push({a,b,length,s:this.length});this.length+=length;}
  if(!this.length||!this.points.every(p=>p.toArray().every(Number.isFinite)))throw new Error('Transit path must be finite and nonzero');
 }
 sample(distance){
  const s=clamp(distance,0,this.length);let segment=this.segments[this.segments.length-1];
  for(const p of this.segments)if(s<=p.s+p.length){segment=p;break;}
  const t=clamp((s-segment.s)/segment.length,0,1),position=segment.a.clone().lerp(segment.b,t),delta=segment.b.clone().sub(segment.a);
  return {position,heading:Math.atan2(delta.z,delta.x),pitch:Math.atan2(delta.y,Math.hypot(delta.x,delta.z)),distance:s};
 }
}
/** Endpoint dwells are explicit; train body orientation stays bidirectional. */
export function shuttleState(time,length,speed=12,dwell=8,margin=0){
 speed=Math.max(.1,Number.isFinite(speed)?speed:12);dwell=Math.max(.1,Number.isFinite(dwell)?dwell:8);
 const a=clamp(margin,0,length*.45),b=length-a,travel=1.5*(b-a)/speed,period=2*(travel+dwell);
 const t=((time%period)+period)%period;
 const moving=(q,direction)=>({distance:direction>0?mix(a,b,smooth(q)):mix(b,a,smooth(q)),direction,moving:true,velocityMps:(b-a)*6*q*(1-q)/travel*direction,dwellProgress:0});
 if(t<dwell)return {distance:a,direction:1,moving:false,velocityMps:0,dwellProgress:t/dwell,endpoint:'start'};
 if(t<dwell+travel)return moving((t-dwell)/travel,1);
 if(t<2*dwell+travel)return {distance:b,direction:-1,moving:false,velocityMps:0,dwellProgress:(t-dwell-travel)/dwell,endpoint:'end'};
 return moving((t-2*dwell-travel)/travel,-1);
}
export class ScenicTransit {
 constructor(template,config,scene){
  this.config=config;this.path=new TransitPath(config.points);this.kind=config.type||(/metro|train/i.test(config.asset)?'metro':'ferry');this.group=template.clone(true);this.group.name=config.id;
  this.group.traverse(o=>{if(o.isMesh){o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();o.castShadow=true;o.receiveShadow=true;}});
  this.carriages=[];if(this.kind==='metro'){
   this.group.updateMatrixWorld(true);
   for(const name of ['TrainCar_0','TrainCar_1','TrainCar_2']){const pivot=this.group.getObjectByName(name);if(pivot){const offset=new THREE.Vector3();pivot.getWorldPosition(offset);this.group.attach(pivot);this.carriages.push({pivot,offset:offset.x,baseRotation:pivot.quaternion.clone()});}}
  }
  this.margin=this.kind==='metro'?Math.max(31,config.end_margin_m||0):Math.max(3,config.end_margin_m||0);
  this.heading=0;this.initialized=false;this.state=null;this.colliderProxies=[];scene.add(this.group);
  // Original lightweight visual wake, not a fluid simulation. It stays on the
  // water plane instead of inheriting the cabin's cosmetic bob.
  if(this.kind==='ferry'){
   const vertices=[],colors=[],indices=[];
   for(const side of [-1,1])for(let i=0;i<=12;i++){const t=i/12;for(const width of [-1,0,1]){vertices.push(-11.8-t*24,0,side*(3.08+t*5)+width*(.18+t*.9));colors.push(.65,.83,.81,width===0?Math.sin(Math.PI*t)*.8:0);}if(i<12){const a=(side<0?0:39)+i*3;for(let j=0;j<2;j++)indices.push(a+j,a+j+3,a+j+1,a+j+1,a+j+3,a+j+4);}}
   const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,4));geometry.setIndex(indices);geometry.computeVertexNormals();
   this.wake=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:0,depthWrite:false,side:THREE.DoubleSide}));this.wake.name=config.id+'_visual_wake';this.wake.renderOrder=1;scene.add(this.wake);
  }
 }
 update(time,dt,{night=false,viewer=null}={}){
  const cfg=this.config,state=shuttleState(time+(cfg.phase_seconds||0),this.path.length,cfg.speed_mps||12,cfg.dwell_seconds||8,this.margin),sample=this.path.sample(state.distance);
  this.state=state;this.group.visible=!viewer||viewer.distanceTo(sample.position)<950;
  if(this.kind==='metro'&&this.carriages.length){
   this.group.position.set(0,0,0);this.group.rotation.set(0,0,0);
   for(const car of this.carriages){const p=this.path.sample(state.distance+car.offset);car.pivot.position.copy(p.position);car.pivot.quaternion.setFromEuler(new THREE.Euler(0,-p.heading,p.pitch)).multiply(car.baseRotation);}
  }else{
   let desired=sample.heading+(state.direction<0?Math.PI:0);
   if(this.kind==='ferry'&&!state.moving){const startHeading=sample.heading+(state.endpoint==='start'?Math.PI:0),endHeading=sample.heading+(state.endpoint==='end'?Math.PI:0);desired=startHeading+angle(endHeading-startHeading)*smooth(state.dwellProgress);}
   this.heading=this.initialized?this.heading+angle(desired-this.heading)*(1-Math.exp(-dt*1.5)):desired;this.initialized=true;
   this.group.position.copy(sample.position);this.group.rotation.set(0,-this.heading,sample.pitch);
   if(this.kind==='ferry'){this.group.position.y+=Math.sin(time*.7)*.035;this.group.rotation.x=Math.sin(time*.55)*.005;}
  }
  if(this.wake){this.wake.visible=this.group.visible&&Math.abs(state.velocityMps)>.2;this.wake.position.set(sample.position.x,sample.position.y+.025,sample.position.z);this.wake.rotation.y=-this.heading;this.wake.material.opacity=Math.min(.26,Math.abs(state.velocityMps)*.045);}
  this.group.traverse(o=>{if(o.isMesh)for(const material of Array.isArray(o.material)?o.material:[o.material])if(/lamp|light|window|glaz/i.test(material.name)&&material.emissive)material.emissiveIntensity=night?.7:.12;});
  // Low-count vertical proxies used by the arcade collision model, not mesh physics.
  const centers=this.carriages.length?this.carriages.map(c=>{const tangent=this.path.sample(state.distance+c.offset);return {p:c.pivot.position,h:tangent.heading,vh:tangent.heading,vp:tangent.pitch,half:8.3,r:1.5,height:cfg.collider_height_m||4.22};}): [{p:this.group.position,h:this.heading,vh:sample.heading,vp:sample.pitch,half:8,r:3.2,height:cfg.collider_height_m||4.6}];
  this.colliderProxies=[];for(let c=0;c<centers.length;c++){const v=centers[c];this.colliderProxies.push({id:`${cfg.id}-${c}`,shape:'capsule',x:v.p.x-Math.cos(v.h)*v.half,z:v.p.z-Math.sin(v.h)*v.half,endX:v.p.x+Math.cos(v.h)*v.half,endZ:v.p.z+Math.sin(v.h)*v.half,y:v.p.y,radius:v.r,height:v.height,velocityX:Math.cos(v.vh)*Math.cos(v.vp)*state.velocityMps,velocityZ:Math.sin(v.vh)*Math.cos(v.vp)*state.velocityMps});}
  if(this.kind==='ferry'){
   // Squared twin-bow ferry: OBB follows the hull footprint. Decorative mast
   // tips remain non-solid; flat roof support is a deliberate arcade proxy.
   const h=this.heading,offset=-.0775,halfLength=11.9275,halfWidth=4.21;
   this.colliderProxies=[{id:cfg.id+'-hull',shape:'box',x:this.group.position.x+Math.cos(h)*offset,z:this.group.position.z+Math.sin(h)*offset,y:this.group.position.y-1.12,halfLength,halfWidth,radius:Math.hypot(halfLength,halfWidth),heading:h,height:cfg.collider_height_m||6.11,velocityX:Math.cos(sample.heading)*Math.cos(sample.pitch)*state.velocityMps,velocityZ:Math.sin(sample.heading)*Math.cos(sample.pitch)*state.velocityMps}];
  }
  return state;
 }
}
