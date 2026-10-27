/**
 * MALABAR — deterministic arcade racing model, independent of Three/DOM.
 * Units: metres, seconds, radians. Three world: +Y up; heading 0 = +X,
 * heading +PI/2 = +Z. Render a +X-forward car with rotation.y = -heading.
 * Original game mechanics, not a Tesla engineering/production simulation.
 *
 * API: new GameModel(route, {startS, endS, seed, obstacles, elevatedCorridors,
 * terrainGrid, roadSections, upgrades, vehicleId}).start(scenarioId)
 * update(elapsedSeconds, {throttle, steer, brake, boost, ultraBoost, flight, lift}).
 * Throttle/steer/lift are -1..1; the other controls are booleans.
 * Obstacles support circles, capsules and oriented boxes with world Y/height.
 * setDynamicObstacles replaces low-count moving proxies; route s stays planar.
 * y is absolute wheel-contact height; groundY is the actual support surface.
 * Vehicles use rate-limited bicycle steering and damped lateral momentum.
 * Ground support samples authored heightfield triangles exactly. Height-aware
 * contacts remain 2.5D capsule/impulse approximations, not general mesh rigid-body
 * collision, physical rollovers, or engineering aerodynamics.
 * bodyRoll/bodyPitch/suspension are cosmetic radians/radians/metres.
 */
import {sanitizeUpgrades,getUpgradeStats} from './garage.js';
import {normalizeRamps,rampSupport,rampLaunch} from './ramp-surfaces.js';
import {AirtimeRewards} from './airtime-rewards.js';
import {PoliceAirSupport,CivilianAirTraffic} from './police-air-support.js';
export const SCENARIOS = Object.freeze([
  Object.freeze({id:'coast-sprint',name:'Coast Sprint',title:'COAST SPRINT',tag:'RACE / PURSUIT',description:'Three rivals. One coastal road. Patrols watch the bridge.',rivals:3,police:2,lighting:'golden',goal:'Finish ahead of the pack. Outrun patrols if they spot the race.',difficulty:'STREET'}),
  Object.freeze({id:'hot-pursuit',name:'Hot Pursuit',title:'HOT PURSUIT',tag:'ESCAPE / SURVIVE',description:'They already know your car. Break contact and reach the safehouse.',rivals:2,police:2,lighting:'blue',goal:'Lose the patrol for eight seconds, then reach the finish.',difficulty:'WANTED'}),
  Object.freeze({id:'time-attack',name:'Midnight Run',title:'MIDNIGHT RUN',tag:'TIME ATTACK',description:'An empty coast and a ticking clock. Every corner counts.',rivals:0,police:0,lighting:'night',goal:'Reach the end before the clock runs out. Recoveries cost five seconds.',difficulty:'PRECISION'}),
  Object.freeze({id:'free-drive',name:'Explore',title:'EXPLORE',tag:'OPEN ROAD / DISCOVER',description:'Choose a district and take the road at your own pace.',rivals:0,police:0,lighting:'golden',goal:'Explore freely. Recovery returns you to the nearest route position.',difficulty:'FREE DRIVE'})
]);
const PI=Math.PI,TAU=PI*2,FIXED=1/120;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const finite=(v,fallback=0)=>Number.isFinite(Number(v))?Number(v):fallback;
const lerp=(a,b,t)=>a+(b-a)*t;
const angle=(a)=>Math.atan2(Math.sin(a),Math.cos(a));
const approach=(v,t,d)=>v<t?Math.min(t,v+d):Math.max(t,v-d);
const sq=(x)=>x*x;
const deckDepth=(d)=>Math.max(0,finite(d.deckThickness,.65))+Math.max(0,finite(d.deckTopBelowRoad,0));
const distance=(a,b)=>Math.hypot(a.x-b.x,a.z-b.z);
const segmentNear=(ax,az,bx,bz,gx,gz,r)=>{
 const dx=bx-ax,dz=bz-az,den=dx*dx+dz*dz;
 const t=den>1e-12?clamp(((gx-ax)*dx+(gz-az)*dz)/den,0,1):0;
 return sq(ax+dx*t-gx)+sq(az+dz*t-gz)<=r*r;
};
const inputSafe=(value={})=>{const i=value&&typeof value==='object'?value:{};return {throttle:clamp(finite(i.throttle),-1,1),steer:clamp(finite(i.steer),-1,1),lift:clamp(finite(i.lift),-1,1),brake:!!i.brake,boost:!!i.boost,ultraBoost:!!i.ultraBoost,flight:!!i.flight,flip:!!i.flip};};


// Closest points between two finite 2D segments (including parallel/zero-length).
const closestSegments=(a,b,c,d)=>{
 const ux=b.x-a.x,uz=b.z-a.z,vx=d.x-c.x,vz=d.z-c.z,wx=a.x-c.x,wz=a.z-c.z;
 const aa=ux*ux+uz*uz,bb=ux*vx+uz*vz,cc=vx*vx+vz*vz,dd=ux*wx+uz*wz,ee=vx*wx+vz*wz,den=aa*cc-bb*bb;
 let t=aa<1e-12?0:den>1e-12?clamp((bb*ee-cc*dd)/den,0,1):0;
 if(cc<1e-12)t=aa>1e-12?clamp(-dd/aa,0,1):0;
 let q=cc<1e-12?0:(bb*t+ee)/cc;
 if(q<0){q=0;t=aa>1e-12?clamp(-dd/aa,0,1):0;}
 else if(q>1){q=1;t=aa>1e-12?clamp((bb-dd)/aa,0,1):0;}
 const pa={x:a.x+t*ux,z:a.z+t*uz},pb={x:c.x+q*vx,z:c.z+q*vz};
 return {a:pa,b:pb,distance:Math.hypot(pa.x-pb.x,pa.z-pb.z)};
};
const carSegment=p=>{const x=Math.cos(p.heading)*1.25,z=Math.sin(p.heading)*1.25;return [{x:p.x-x,z:p.z-z},{x:p.x+x,z:p.z+z}];};
// Comfort envelope is separate from available tire grip: binary arrow keys must
// not command the full lateral grip limit on every long press. Keep parking
// authority, blend road-speed authority continuously, never snap to road heading.
const steeringEnvelope=(speed,maxSteer=.57,grip=14.5)=>{
 const smooth=v=>v*v*(3-2*v),park=smooth(clamp(Math.abs(speed)/10,0,1)),road=smooth(clamp((Math.abs(speed)-3)/15,0,1));
 return Math.min(maxSteer*(1-.28*park),Math.atan(2.7*grip*(1-.28*road)/(speed*speed+16)));
};
const normalizeTerrainGrid=g=>{
 if(!g)return null;const origin=g.origin,step=g.step||[g.cell_size_m,g.cell_size_m],count=g.count||[g.columns,g.rows];
 if(!Array.isArray(origin)||!origin.every(Number.isFinite)||origin.length!==2||!Array.isArray(step)||step.length!==2||!step.every(v=>Number.isFinite(v)&&v>0)||!Array.isArray(count)||count.length!==2||!count.every(v=>Number.isInteger(v)&&v>=2)||!Array.isArray(g.heights)||g.heights.length!==count[0]*count[1]||!g.heights.every(Number.isFinite))throw new TypeError('Invalid terrain grid: finite origin/step, integer count and row-major heights required');
 if(g.diagonal&&!['sw-ne','v00-v11','00-11'].includes(g.diagonal))throw new TypeError('Terrain grid must use the v00-v11 diagonal');
 return {origin:[...origin],step:[...step],count:[...count],heights:g.heights,diagonal:'v00-v11'};
};
const sampleTerrainGrid=(g,x,z)=>{
 const [nx,nz]=g.count,[dx,dz]=g.step,ux=(x-g.origin[0])/dx,vz=(z-g.origin[1])/dz,inside=ux>=0&&vz>=0&&ux<=nx-1&&vz<=nz-1;
 const ix=clamp(Math.floor(ux),0,nx-2),iz=clamp(Math.floor(vz),0,nz-2),u=clamp(ux-ix,0,1),v=clamp(vz-iz,0,1),i=iz*nx+ix;
 const a=g.heights[i],b=g.heights[i+1],c=g.heights[i+nx],d=g.heights[i+nx+1];let y,gx,gz;
 if(v<=u){y=a+(b-a)*u+(d-b)*v;gx=(b-a)/dx;gz=(d-b)/dz;}
 else{y=a+(d-c)*u+(c-a)*v;gx=(d-c)/dx;gz=(c-a)/dz;}
 if(ux<0||ux>nx-1)gx=0;if(vz<0||vz>nz-1)gz=0;
 return {y,gradientX:gx,gradientZ:gz,grade:Math.hypot(gx,gz),heading:Math.atan2(gz,gx),inside,outsideDistance:Math.hypot(Math.max(0,-ux,ux-(nx-1))*dx,Math.max(0,-vz,vz-(nz-1))*dz),layer:'terrain'};
};
const obstacleBounds=o=>o.shape==='box'?{minX:o.x-o.radius,maxX:o.x+o.radius,minZ:o.z-o.radius,maxZ:o.z+o.radius}:{minX:Math.min(o.x,o.endX??o.x)-o.radius,maxX:Math.max(o.x,o.endX??o.x)+o.radius,minZ:Math.min(o.z,o.endZ??o.z)-o.radius,maxZ:Math.max(o.z,o.endZ??o.z)+o.radius};
const obstacleCovers=(o,x,z,margin=0)=>{
 if(o.shape==='box'){const c=Math.cos(finite(o.heading)),s=Math.sin(finite(o.heading)),dx=x-o.x,dz=z-o.z;return Math.abs(dx*c+dz*s)<=finite(o.halfLength,1)+margin&&Math.abs(-dx*s+dz*c)<=finite(o.halfWidth,1)+margin;}
 const dx=finite(o.endX,o.x)-o.x,dz=finite(o.endZ,o.z)-o.z,len=dx*dx+dz*dz,t=len?clamp(((x-o.x)*dx+(z-o.z)*dz)/len,0,1):0;return Math.hypot(x-o.x-dx*t,z-o.z-dz*t)<=o.radius+margin;
};


export class GameModel {
 constructor(route,options={}) {
  if(!Array.isArray(route)||route.length<2)throw new TypeError('GameModel needs at least two finite route points');
  this.route=[];
  for(const p of route){
   if(!p||!Number.isFinite(p.x)||!Number.isFinite(p.z))throw new TypeError('Route coordinates must be finite {x,z} metres');
   const q={x:p.x,z:p.z,y:Number.isFinite(p.y)?p.y:.18};
   if(!this.route.length||distance(q,this.route[this.route.length-1])>.0001)this.route.push(q);
  }
  if(this.route.length<2)throw new RangeError('Route has no nonzero segment');
  this.segments=[];let sum=0;
  for(let i=0;i<this.route.length-1;i++){
   const a=this.route[i],b=this.route[i+1],len=distance(a,b),tx=(b.x-a.x)/len,tz=(b.z-a.z)/len;
   this.segments.push({a,b,length:len,s:sum,tx,tz,heading:Math.atan2(tz,tx),grade:(b.y-a.y)/len,roadPitch:Math.atan2(b.y-a.y,len),index:i});sum+=len;
  }
  this.routeLength=sum;this.airTraffic=options.airTraffic===true;this.ramps=normalizeRamps(options.ramps,sum);
  this.startS=clamp(finite(options.startS),0,Math.max(0,sum-25));
  this.endS=clamp(finite(options.endS,sum),Math.min(sum,this.startS+20),sum);
  this.length=this.endS-this.startS;
  this.terrainY=finite(options.terrainY,-.04);this.terrainGrid=normalizeTerrainGrid(options.terrainGrid||options.terrainHeightfield);this.roadSections=Array.isArray(options.roadSections||options.roadWidthSegments)?(options.roadSections||options.roadWidthSegments):[];this.elevatedCorridors=Array.isArray(options.elevatedCorridors)?options.elevatedCorridors:[];
  this.seed=(options.seed??1337)>>>0;this._randomState=this.seed;
  this.upgrades=sanitizeUpgrades(options.upgrades);this.vehicleStats=getUpgradeStats(this.upgrades,options.vehicleId);
  this.roadHalfWidth=3.6;this.maxSteer=clamp(finite(options.maxSteer,this.vehicleStats.maxSteer),.2,.65);this.scenario=SCENARIOS[0];this.state='menu';this.paused=false;
  this.obstacles=(Array.isArray(options.obstacles)?options.obstacles:[]).filter(o=>o&&Number.isFinite(o.x)&&Number.isFinite(o.z)&&Number.isFinite(o.radius)&&o.radius>0).map((o,i)=>({...o,id:o.id??'obstacle-'+i,radius:o.shape==='box'?Math.hypot(finite(o.halfLength,1),finite(o.halfWidth,1)):Math.min(120,o.radius)}));
  this._dynamicObstacles=[];this._obstacleGrid=new Map();
  for(const o of this.obstacles){const b=obstacleBounds(o);for(let gx=Math.floor(b.minX/32);gx<=Math.floor(b.maxX/32);gx++)for(let gz=Math.floor(b.minZ/32);gz<=Math.floor(b.maxZ/32);gz++){const key=gx+','+gz;if(!this._obstacleGrid.has(key))this._obstacleGrid.set(key,[]);this._obstacleGrid.get(key).push(o);}}
  this.events=[];this.message='Choose an event';this._eventSequence=0;
  this._buildCheckpoints();this._initialize();this.state='menu';
 }
 _random(){this._randomState=(1664525*this._randomState+1013904223)>>>0;return this._randomState/4294967296;}
 _buildCheckpoints(){
  this.checkpoints=[this.sampleRoute(this.startS)];
  const spacing=Math.min(125,Math.max(25,this.length/10));
  for(let s=this.startS+spacing;s<this.endS-10;s+=spacing)this.checkpoints.push(this.sampleRoute(s));
  this.checkpoints.push(this.sampleRoute(this.endS));for(const q of this.checkpoints){const surface=rampSupport(this.ramps,q,this.scenario.id);if(surface){q.y=surface.y;q.grade=surface.grade;q.roadPitch=Math.atan(surface.grade);}}this.totalCheckpoints=this.checkpoints.length-1;
 }
 sampleRoute(s){
  s=finite(s);let lo=0,hi=this.segments.length-1;
  while(lo<hi){const mid=(lo+hi)>>1;if(this.segments[mid].s+this.segments[mid].length<s)lo=mid+1;else hi=mid;}
  const seg=this.segments[lo],t=(s-seg.s)/seg.length;
  return {x:lerp(seg.a.x,seg.b.x,t),z:lerp(seg.a.z,seg.b.z,t),y:lerp(seg.a.y,seg.b.y,clamp(t,0,1)),heading:seg.heading,grade:seg.grade,roadPitch:seg.roadPitch,tx:seg.tx,tz:seg.tz,nx:-seg.tz,nz:seg.tx,s,index:lo};
 }
 projectToRoute(x,z,hintS=null){
  x=finite(x);z=finite(z);let from=0,to=this.segments.length-1;
  if(Number.isFinite(hintS)){
   const anchor=this.sampleRoute(hintS),reach=Math.max(10,Math.hypot(x-anchor.x,z-anchor.z)*2+3);from=this.sampleRoute(hintS-reach).index;to=this.sampleRoute(hintS+reach).index;
  }
  const search=(start,end)=>{
   let best=null;
   for(let i=start;i<=end;i++){
    const seg=this.segments[i],dx=x-seg.a.x,dz=z-seg.a.z;
    const t=clamp((dx*seg.tx+dz*seg.tz)/seg.length,0,1);
    const px=seg.a.x+seg.tx*seg.length*t,pz=seg.a.z+seg.tz*seg.length*t;
    const dd=sq(x-px)+sq(z-pz);
    if(best===null||dd<best.distanceSq)best={x:px,z:pz,worldX:x,worldZ:z,y:lerp(seg.a.y,seg.b.y,t),s:seg.s+seg.length*t,heading:seg.heading,grade:seg.grade,roadPitch:seg.roadPitch,tx:seg.tx,tz:seg.tz,nx:-seg.tz,nz:seg.tx,offset:(x-px)*(-seg.tz)+(z-pz)*seg.tx,distance:Math.sqrt(dd),distanceSq:dd,index:i};
   }
   return best;
  };
  let best=search(from,to);
  // With a progress hint, stay on the locally reachable branch of a hairpin.
  // Unhinted calls remain a global nearest-road query for placement/terrain QA.
  return best;
 }
 _vehicle(id,s,lane,color){
  const p=this.sampleRoute(s),bounds=this._aiRoadBounds(p,p.heading);if(bounds)lane=clamp(lane,bounds.min,bounds.max);
  const v={id,x:p.x+p.nx*lane,z:p.z+p.nz*lane,y:p.y,heading:p.heading,s,roadPitch:p.roadPitch,roadRoll:0,groundPitch:p.roadPitch,groundHeading:p.heading,groundNormalX:-p.grade*p.tx/Math.hypot(1,p.grade),groundNormalY:1/Math.hypot(1,p.grade),groundNormalZ:-p.grade*p.tz/Math.hypot(1,p.grade),groundY:p.y,grounded:true,onRoadDeck:true,flightCeiling:p.y+7.5,speed:0,steer:0,steerInput:0,yawRate:0,collisionYaw:0,velocityX:0,velocityZ:0,lateralSpeed:0,lateralVelocity:0,impactShake:0,mass:id==='player'?this.vehicleStats.mass:1550,wheelAngle:0,energy:1,ultraCharge:1,ultraCooldown:0,ultraRemaining:0,ultraBoosting:false,damage:0,lane,targetLane:lane,color,active:true,visible:true,finished:false,finishTime:null,altitude:0,vz:0,offRoad:false,boosting:false,flying:false,thrusting:false,flipActive:false,flipTime:0,stuntRoll:0,stuntPhase:null,landingAssist:false,bodyRoll:0,bodyPitch:0,suspension:0};
  if(id!=='player')this._supportOffRouteAI(v);const ramp=rampSupport(this.ramps,{...p,offset:lane},this.scenario.id);if(ramp)this._setRampGround(v,ramp);if(this.ramps.length&&id!=='player')v._rampPreviousS=s;return v;
 }
 _initialize(){
  this._randomState=this.seed;this._accumulator=0;this._flightLocked=false;this._boostLocked=false;this.recoveryWarning=null;this.recoveryCooldown=0;this.automaticRecoveries=0;this._recoveryReason=null;this._recoveryElapsed=0;this._stuckAnchor=null;this._lastSolidContactAt=-Infinity;this._lastAnyContactAt=-Infinity;this._damageAssistRetryAt=0;this._ultraLocked=false;this._ultraSpeedCarry=false;this._flipLocked=false;this._collisionCooldowns=new Map();
  this._airtime=new AirtimeRewards();this.airtime=this._airtime.state;this._policeAir=new PoliceAirSupport();this.helicopter=this._policeAir.state;this._civilianAir=new CivilianAirTraffic();this.civilianHelicopter=this._civilianAir.state;
  this.player=this._vehicle('player',this.startS+8,-1.65,'#b82632');this.player.name='YOU';
  const rivalNames=['NILA','RAHUL','DEV'];const colors=['#e2bb52','#499cbd','#e6e7dc'];
  this.rivals=Array.from({length:this.scenario.rivals},(_,i)=>{
   const v=this._vehicle('rival-'+i,this.startS+20+i*12,i%2?1.55:-1.55,colors[i]);v.name=rivalNames[i];v.skill=31+i*1.8;v.phase=this._random()*TAU;return v;
  });
  this._detectionAfter=Math.min(30,this.length/55);
  const detectionS=this.startS+Math.min(this.length*.72,Math.max(this.length*.27,this._detectionAfter*28+80));
  this.police=Array.from({length:this.scenario.police},(_,i)=>{
   const hot=this.scenario.id==='hot-pursuit';const s=hot?this.startS-25-i*24:detectionS+i*46;
   const v=this._vehicle('patrol-'+i,s,hot?(i%2?1.4:-1.4):(i%2?4.55:-4.55),'#d5dad5');v.name=i?'INTERCEPTOR':'PATROL';v.active=hot;v.siren=hot;v.mode=hot?'pursuit':'patrol';v.visible=true;v.patrolS=s;v.searchTimer=0;return v;
  });
  this.timer=0;this.countdown=this.scenario.id==='free-drive'?0:3;this.progress=this.scenario.id==='free-drive'?this.player.s/this.routeLength:0;this.position=1+this.rivals.length;this.nextCheckpoint=this.scenario.id==='free-drive'?0:1;this.totalCheckpoints=this.scenario.id==='free-drive'?0:this.checkpoints.length-1;
  this.distanceRemaining=this.scenario.id==='free-drive'?this.routeLength-this.player.s:this.length;this.penalties=0;this.recoveries=0;this.damage=0;
  this.wanted=this.scenario.id==='hot-pursuit'?2:0;this.heat=this.wanted?.45:0;this.arrestProgress=0;
  this.escapeTimer=0;this.escaped=false;this.pursuit=this.wanted?'pursuit':'clear';this.policeDistance=Infinity;
  this._detectionAfter=Math.min(30,this.length/55);this._offRoadTime=0;this._allGatesPassed=false;this._terminalAnnounced=false;
  this.timeLimit=this.scenario.id==='time-attack'?Math.max(35,this.length/22+25):Infinity;
  this.timeRemaining=this.timeLimit;this.result=null;this.wrongWay=false;this.paused=false;
  this.coinsCollected=0;this.collectedCoinIds=new Set();this.coins=[];
  if(this.scenario.id!=='free-drive')for(let group=this.startS+80;group<=this.endS-40&&this.coins.length<120;group+=180)for(let n=0;n<3&&group+n*8<=this.endS-40&&this.coins.length<120;n++){
   const q=this.sampleRoute(group+n*8),section=this._roadSection(q.s),strips=section?.driveableStrips||[{centerOffset:0,halfWidth:section?.halfWidth??3.6}],strip=strips.reduce((a,b)=>Math.abs(finite(b.centerOffset))<Math.abs(finite(a.centerOffset))?b:a),lane=finite(strip.centerOffset)+clamp(-1.65,-finite(strip.halfWidth,3.6)+1,finite(strip.halfWidth,3.6)-1);
   const support=rampSupport(this.ramps,{...q,offset:lane},this.scenario.id);this.coins.push({id:'coin-'+this.coins.length,s:q.s,x:q.x+q.nx*lane,y:(support?.y??q.y)+.65,z:q.z+q.nz*lane,value:5,collected:false});
  }
  this.events=[];this.message='READY';this.messageUntil=0;this._eventSequence=0;
 }
 start(id='coast-sprint'){
  const scenario=SCENARIOS.find(s=>s.id===id);
  if(!scenario)throw new RangeError('Unknown scenario: '+id);
  this.scenario=scenario;this._buildCheckpoints();this._initialize();this.state=id==='free-drive'?'racing':'countdown';this._emit('start',scenario.name);return this;
 }
 restart(){return this.start(this.scenario.id);}
 reset(){return this.restart();}
 setPaused(value){this.paused=!!value;this._accumulator=0;return this;}
 _emit(type,text,data={}){
  const e={id:++this._eventSequence,type,text,time:this.timer,...data};this.events.push(e);if(this.events.length>30)this.events.shift();
  this.message=text;this.messageUntil=this.timer+4;return e;
 }
 consumeEvents(){const e=this.events.slice();this.events.length=0;return e;}
 _recoveryPose(baseS,{reverse=false}={}){
  // Search behind the eligible position; never skip a gate to find empty asphalt.
  // Check the full car capsule against pavement, solid proxies and nearby cars.
  for(const back of [0,5,10,18,28,42,60])for(const lane of (reverse?[1.65,-1.65,0]:[-1.65,1.65,0])){
   const q=this.sampleRoute(clamp(baseS-back,Math.min(3,this.routeLength/3),this.routeLength-3));
   const ramp=rampSupport(this.ramps,{...q,offset:lane},this.scenario.id);if(ramp){q.y=ramp.y;q.grade=ramp.grade;q.roadPitch=Math.atan(ramp.grade);}
   const pose={...q,x:q.x+q.nx*lane,z:q.z+q.nz*lane,lane,heading:angle(q.heading+(reverse?PI:0)),groundHeading:q.heading,groundPitch:q.roadPitch,roadPitch:reverse?-q.roadPitch:q.roadPitch,flipActive:false};
   if(carSegment(pose).some(point=>{const zone=this._roadZone(this.projectToRoute(point.x,point.z,q.s));return zone.distance+.98>zone.halfWidth-.025;}))continue;
   const gx=Math.floor(pose.x/32),gz=Math.floor(pose.z/32),near=[...this._dynamicObstacles],seen=new Set();
   for(let x=gx-1;x<=gx+1;x++)for(let z=gz-1;z<=gz+1;z++)near.push(...(this._obstacleGrid.get(x+','+z)||[]));
   let blocked=false;
   for(const o of near){if(seen.has(o.id))continue;seen.add(o.id);const bottom=finite(o.y,.18),top=bottom+finite(o.height,1.2);if(pose.y+1.2>bottom&&pose.y<top&&this._obstacleContact(o,pose).depth>-.12){blocked=true;break;}}
   if(blocked)continue;
   if([...this.rivals,...this.police].some(v=>v.visible&&pose.y+1.2>v.y&&pose.y<v.y+1.2&&closestSegments(...carSegment(pose),...carSegment(v)).distance<2.26))continue;
   return pose;
  }
  return null;
 }
 _clearRecoveryWarning(){this.recoveryWarning=null;this._recoveryReason=null;this._recoveryElapsed=0;}
 _updateAutoRecovery(dt,input){
  this.recoveryCooldown=Math.max(0,this.recoveryCooldown-dt);
  const p=this.player;
  // An intentional flight/flip must never be mistaken for leaving the road.
  // Ground-only world-boundary recovery also waits for a real touchdown.
  if(this.state!=='racing'||this.recoveryCooldown>0||!p.grounded||p.altitude>.15||p.flying||p.flipActive||input.flight||p.damage>=1){this._clearRecoveryWarning();this._stuckAnchor=null;return;}
  const local=this.projectToRoute(p.x,p.z,p.s),localZone=this._roadZone(local),nearest=localZone.distance<=localZone.shoulderHalfWidth+8?local:this.projectToRoute(p.x,p.z),zone=this._roadZone(nearest),beyond=Math.max(0,zone.distance-zone.shoulderHalfWidth),free=this.scenario.id==='free-drive';
  const boxed=this.wanted&&this.police.some(v=>v.active&&Math.abs(v.y-p.y)<1.5&&this._patrolSeesPlayer(v,12));
  if(boxed||this.arrestProgress>.05){this._clearRecoveryWarning();this._stuckAnchor=null;return;}
  const outside=this.terrainGrid&&this.sampleTerrain(p.x,p.z).outsideDistance>100;
  const wantsMotion=Math.abs(input.throttle)>.35&&!input.brake;
  const impeded=this.timer-this._lastSolidContactAt<.3||beyond>.5;
  const slow=Math.hypot(p.velocityX,p.velocityZ)<1.0;
  let stuck=false;
  if(wantsMotion&&impeded&&slow){if(!this._stuckAnchor||distance(p,this._stuckAnchor)>.75)this._stuckAnchor={x:p.x,z:p.z,time:this.timer};stuck=this.timer-this._stuckAnchor.time>1.5;}
  else this._stuckAnchor=null;
  const first=this.sampleRoute(0),last=this.sampleRoute(this.routeLength);
  const pastStart=-((p.x-first.x)*first.tx+(p.z-first.z)*first.tz),pastEnd=(p.x-last.x)*last.tx+(p.z-last.z)*last.tz;
  const outwardEnd=p.velocityX*last.tx+p.velocityZ*last.tz,outwardStart=-(p.velocityX*first.tx+p.velocityZ*first.tz);
  const endpoint=free&&((nearest.s<1&&pastStart>8&&outwardStart>-.8)?'start':(nearest.s>this.routeLength-1&&pastEnd>8&&outwardEnd>-.8)?'end':null);
  const approaching=free&&((nearest.s<45&&Math.cos(p.heading-first.heading)<-.35)?'start':(nearest.s>this.routeLength-45&&Math.cos(p.heading-last.heading)>.35)?'end':null);
  const far=beyond>(free?60:25),reason=outside?'world-boundary':endpoint?'route-end':far?'far-offroad':stuck?'stuck':null;
  if(!reason&&approaching){
   if(this._recoveryReason!=='approach-'+approaching)this._emit('recovery-warning','ROAD ENDS AHEAD / TURN BACK',{reason:'route-end',endpoint:approaching,warningOnly:true});
   this._recoveryReason='approach-'+approaching;this._recoveryElapsed=0;this.recoveryWarning={reason:'route-end',endpoint:approaching,warningOnly:true,secondsRemaining:null,distanceMetres:approaching==='end'?Math.max(0,this.routeLength-nearest.s):Math.max(0,nearest.s)};return;
  }
  if(!reason){this._clearRecoveryWarning();return;}
  const grace=outside||endpoint?2:reason==='stuck'?2.5:free?5:3;
  if(reason!==this._recoveryReason){this._recoveryReason=reason;this._recoveryElapsed=0;this._emit('recovery-warning',reason==='stuck'?'STUCK / ROADSIDE ASSIST SOON':endpoint?'ROAD ENDS / RETURNING TO FACE BACK':'RETURN TO THE ROAD / AUTO RETURN SOON',{reason});}
  this._recoveryElapsed+=dt;this.recoveryWarning={reason,endpoint,warningOnly:false,secondsRemaining:Math.max(0,grace-this._recoveryElapsed),distanceMetres:zone.distance};
  if(this._recoveryElapsed>=grace-1e-8){if(!this.recover({automatic:true,reason})){this.recoveryCooldown=2;this._clearRecoveryWarning();}}
 }
 recover({automatic=false,reason='manual'}={}){
  if(this.paused||!['racing','countdown'].includes(this.state))return false;
  const free=this.scenario.id==='free-drive',gate=this.checkpoints[clamp(this.nextCheckpoint-1,0,this.checkpoints.length-2)];
  const nearest=free?this.projectToRoute(this.player.x,this.player.z):null;
  const travelReverse=free&&Math.cos(this.player.heading-nearest.heading)<0;
  const first=free?this.sampleRoute(0):null,last=free?this.sampleRoute(this.routeLength):null;
  const beyondEnd=free&&((this.player.x-last.x)*last.tx+(this.player.z-last.z)*last.tz)>0;
  const beyondStart=free&&((this.player.x-first.x)*first.tx+(this.player.z-first.z)*first.tz)<0;
  const fromEnd=free&&nearest.s>this.routeLength-6&&(beyondEnd||!travelReverse),fromStart=free&&nearest.s<6&&(beyondStart||travelReverse);
  const reverse=fromEnd?true:fromStart?false:travelReverse;
  const baseS=free?(fromEnd?this.routeLength-14:fromStart?14:clamp(nearest.s,0,this.routeLength-5)):Math.min(gate.s+4,this.endS-5);
  const p=this._recoveryPose(baseS,{reverse});
  if(!p){this._emit('recovery-blocked','RETURN BLOCKED / BRAKE OR REVERSE',{automatic,reason});return false;}
  this._airtime.cancel('recovery');this._policeAir.recovery();this._stopUltra('recovery');this._ultraSpeedCarry=false;
  Object.assign(this.player,{x:p.x,z:p.z,y:p.y,heading:p.heading,s:p.s,roadPitch:p.roadPitch,roadRoll:0,groundPitch:p.groundPitch??p.roadPitch,groundHeading:p.groundHeading??p.heading,groundNormalX:-p.grade*p.tx/Math.hypot(1,p.grade),groundNormalY:1/Math.hypot(1,p.grade),groundNormalZ:-p.grade*p.tz/Math.hypot(1,p.grade),groundY:p.y,grounded:true,onRoadDeck:true,flightCeiling:p.y+7.5,speed:0,steer:0,steerInput:0,yawRate:0,collisionYaw:0,velocityX:0,velocityZ:0,lateralSpeed:0,lane:p.lane,altitude:0,vz:0,offRoad:false,boosting:false,flying:false,thrusting:false,flipActive:false,flipTime:0,stuntRoll:0,stuntPhase:null,landingAssist:false,bodyRoll:0,bodyPitch:0,suspension:0});
  this._offRoadTime=0;this._flightLocked=true;this.arrestProgress=0;this.recoveryCooldown=6;this._clearRecoveryWarning();this._stuckAnchor=null;if(automatic)this.automaticRecoveries++;
  if(this.state==='racing'){this.recoveries++;if(free){this.player.damage=0;this.damage=0;this._emit('recovery',automatic?'ROADSIDE ASSIST / BACK ON THE ROAD':'BACK ON THE ROAD / REPAIRED',{automatic,reason});}else{this.timer+=5;this.penalties+=5;this._emit('recovery',automatic?'AUTO RETURN / +5 SEC':'BACK ON THE ROAD  +5 SEC',{automatic,reason});}}
  this.timeRemaining=Math.max(0,this.timeLimit-this.timer);this.progress=clamp(free?p.s/this.routeLength:(p.s-this.startS)/this.length,0,1);this.distanceRemaining=Math.max(0,(free?this.routeLength:this.endS)-p.s);this.position=1+this.rivals.filter(v=>v.finished||v.s>p.s).length;this.wrongWay=false;
  if(this.state==='racing'&&this.timeRemaining<=0)this._end('failed','TIME EXPIRED');
  return true;
 }
 update(dt,input={}){
  if(this.paused||!['racing','countdown'].includes(this.state))return this;
  dt=finite(dt);if(dt<=0)return this;
  this._accumulator+=Math.min(dt,.25);
  const controls=inputSafe(input);
  while(this._accumulator+1e-10>=FIXED){
   this._accumulator-=FIXED;this._step(FIXED,controls);
   if(!['racing','countdown'].includes(this.state)){this._accumulator=0;break;}
  }
  return this;
 }
 _step(dt,input){
  if(this.state==='countdown'){
   this.countdown=Math.max(0,this.countdown-dt);
   if(this.countdown<=1e-6){this.countdown=0;this.state='racing';this._emit('go','GO / THE COAST IS YOURS');}
   return;
  }
  this.timer+=dt;this.timeRemaining=Math.max(0,this.timeLimit-this.timer);
  const old={x:this.player.x,z:this.player.z,y:this.player.y,heading:this.player.heading,height:this.player.flipActive?3:1.2,flipActive:this.player.flipActive,grounded:this.player.grounded,altitude:this.player.altitude,s:this.player.s};
  const eventStart=this._eventSequence;
  this._drivePlayer(dt,input);this._updateRivals(dt);this._updatePolice(dt);this._vehicleContacts(dt);this._obstacleContacts(dt,old);this._deckContacts();this._rampContacts(old);
  this._updateAirtime(dt,input,eventStart);this._updateAirTraffic(dt);
  this._updateCoins(old);this._updateRace(old,dt);this._updateAutoRecovery(dt,input);
  if(this.player.damage>=1&&this.state==='racing'){
   if(this.scenario.id==='free-drive'){
    if(this.timer>=this._damageAssistRetryAt){if(this.recover())this._emit('roadside-assist','ROADSIDE ASSIST / REPAIRED');else this._damageAssistRetryAt=this.timer+2;}
   }else this._end('failed','VEHICLE DISABLED');
  }
  if(this.timeRemaining<=0&&this.state==='racing')this._end('failed','TIME EXPIRED');
 }
 _stopUltra(reason='depleted'){
  const p=this.player;if(!p.ultraBoosting)return;
  p.ultraBoosting=false;p.ultraRemaining=0;p.ultraCooldown=this.vehicleStats.ultraCooldownSeconds;
  this._emit('ultra-ended','ULTRA / COOLING',{reason});
 }
 _updateUltra(dt,input,deepOffroad){
  const p=this.player,stats=this.vehicleStats;
  const blocked=p.flipActive?'flip':input.brake?'brake':input.throttle<=.15?'throttle':deepOffroad?'terrain':null;
  if(p.ultraBoosting){p.ultraRemaining=Math.max(0,p.ultraRemaining-dt);if(blocked||p.ultraRemaining<1e-8)this._stopUltra(blocked||'depleted');}
  else if(p.ultraCooldown>0)p.ultraCooldown=Math.max(0,p.ultraCooldown-dt);
  else p.ultraCharge=clamp(p.ultraCharge+stats.ultraRechargePerSecond*dt,0,1);
  if(!input.ultraBoost)this._ultraLocked=false;
  if(input.ultraBoost&&!this._ultraLocked){
   this._ultraLocked=true;
   const reason=blocked||(p.ultraBoosting?'active':p.ultraCooldown>1e-8?'cooldown':p.ultraCharge<1-1e-8?'charging':null);
   if(reason)this._emit('ultra-unavailable','ULTRA NOT READY / '+reason.toUpperCase(),{reason});
   else{p.ultraBoosting=true;p.ultraCharge=0;p.ultraRemaining=stats.ultraDuration;this._ultraSpeedCarry=true;this._emit('ultra-start','ULTRA / FULL DISCHARGE',{duration:stats.ultraDuration});}
  }
 }
 _drivePlayer(dt,input){
  const p=this.player,projection=this.projectToRoute(p.x,p.z,p.s);
  p.s=projection.s;const roadZone=this._roadZone(this._supportProjection(projection));p.offRoad=roadZone.distance>roadZone.halfWidth+.45;
  let deepOffroad=roadZone.distance>roadZone.halfWidth+3.4;
  const wasGrounded=p.grounded&&p.altitude<.01;
  const surfaceBefore=this._surfaceAt(projection,p.y,wasGrounded&&p.onRoadDeck);
  const ground=surfaceBefore.y;
  if(surfaceBefore.rampId){p.offRoad=false;deepOffroad=false;}
  this._bodyVelocity(p);
  const speedAbs=Math.abs(p.speed),previousSpeed=p.speed,previousAltitude=p.altitude;
  if(!input.flip)this._flipLocked=false;
  if(input.flip&&!this._flipLocked){this._flipLocked=true;if(p.y-ground>=2.8&&speedAbs>6&&p.energy>=.30&&!p.flipActive&&this._flipHasClearance(projection)){p.energy-=.22;p.flipActive=true;p.flipTime=0;this._emit('flip-start','CONTROLLED KICKFLIP');}else if(!p.flipActive)this._emit('flip-unavailable','FLIP NEEDS 3 M ALTITUDE / SPEED / ENERGY');}
  if(p.flipActive){p.flipTime+=dt;const u=clamp((p.flipTime-.25)/2.5,0,1);p.stuntRoll=TAU*(u*u*(3-2*u));p.stuntPhase=p.flipTime<.25?'lift':u<.5?'roll':u<1?'counterthrust':'level';if(p.flipTime>=3.2){p.flipActive=false;p.stuntRoll=0;p.stuntPhase=null;this._emit('flip-complete','LEVEL / READY TO LAND');}}
  if(!input.flight)this._flightLocked=false;
  // The flip's 22% charge prepays its authored assist; keep at least the entry reserve for landing.
  const flyingThrust=input.flight&&!p.flipActive&&!this._flightLocked&&p.energy>.01;p.thrusting=flyingThrust;
  if(input.flight&&p.energy<=.01)this._flightLocked=true;
  if(!input.boost)this._boostLocked=false;
  if(input.boost&&p.energy<=.02)this._boostLocked=true;
  this._updateUltra(dt,input,deepOffroad);
  p.boosting=input.boost&&!p.ultraBoosting&&!p.flipActive&&!this._boostLocked&&input.throttle>.15&&!input.brake&&p.energy>.02&&!deepOffroad;
  const energyUse=(flyingThrust?.14:0)+(p.boosting?.24/this.vehicleStats.boostEfficiency:0);
  p.energy=clamp(p.energy+dt*(energyUse?-energyUse:p.flipActive?0:.095*this.vehicleStats.boostRechargeMultiplier),0,1);
  // Rack travel is rate-limited in normalized space. The speed envelope is derived
  // from tire grip, so a 10% input remains 10%-ish curvature, not instant full yaw.
  const shaped=Math.sign(input.steer)*Math.pow(Math.abs(input.steer),1.35);
  p.steerInput=approach(p.steerInput,shaped,dt*(p.steerInput*shaped<0||Math.abs(shaped)<Math.abs(p.steerInput)?6.5:2.7));
  const grip=p.offRoad&&p.altitude<.5?8.5:14.5*this.vehicleStats.gripMultiplier;
  p.steer=p.steerInput*steeringEnvelope(speedAbs,this.maxSteer,grip);
  let acceleration=input.throttle*(input.throttle>=0?11.7*this.vehicleStats.accelerationMultiplier:5.8)*(p.ultraBoosting?2.1:p.boosting?1.5:1);
  if(input.throttle<0&&p.speed>.5)acceleration=-21;
  if(input.throttle>0&&p.speed<-.5)acceleration=19;
  if(input.brake)acceleration=0;
  if(p.offRoad&&p.altitude<.5){
   // A low reverse crawl gear must overcome the 3.2 m/s² rough-ground rolling
   // loss: the old deep-grass factor made full reverse weaker than drag and
   // pinned an otherwise free car at rest. Preserve forward traction, braking
   // from forward speed, airborne motion and lateral grip unchanged.
   const terrainScale=deepOffroad?.38:.65,reverseCrawl=wasGrounded&&input.throttle<0&&p.speed<=.5&&!input.brake;
   acceleration*=reverseCrawl?Math.max(terrainScale,.85):terrainScale;
  }
  if(wasGrounded)acceleration-=9.81*.85*Math.sin(Math.atan(surfaceBefore.gradientX*Math.cos(p.heading)+surfaceBefore.gradientZ*Math.sin(p.heading)));
  const drag=.00165*p.speed*Math.abs(p.speed);
  let longitudinal=p.speed+(acceleration-drag)*dt;
  longitudinal=approach(longitudinal,0,dt*(input.brake?(wasGrounded?this.vehicleStats.brakeDecelerationMps2:24):(p.offRoad&&p.altitude<.5?3.2:.32)));
  const maxSpeed=deepOffroad&&p.altitude<.5?21:(p.ultraBoosting?this.vehicleStats.ultraBoostMaxSpeedMps:p.boosting?this.vehicleStats.regularBoostMaxSpeedMps:this.vehicleStats.topSpeedMps);
  if(longitudinal>maxSpeed)longitudinal=Math.max(maxSpeed,longitudinal-14*dt);
  const normalHardLimit=88*this.vehicleStats.topSpeedMps/68;
  if(!p.ultraBoosting&&p.speed<=normalHardLimit)this._ultraSpeedCarry=false;
  longitudinal=clamp(longitudinal,-10,this._ultraSpeedCarry?this.vehicleStats.ultraBoostMaxSpeedMps+5:normalHardLimit);
  const desiredYaw=longitudinal/2.7*Math.tan(p.steer)*(p.flipActive?.2:p.altitude>.45?.72:1);
  p.yawRate=lerp(p.yawRate,desiredYaw,1-Math.exp(-(shaped*p.yawRate<=0?14:10)*dt));
  p.collisionYaw*=Math.exp(-3.7*dt);p.impactShake*=Math.exp(-5*dt);
  const yaw=p.yawRate+p.collisionYaw,previousHeading=p.heading;
  p.heading=angle(p.heading+yaw*dt);
  // Existing world momentum is retained through yaw, then tire grip damps slip.
  const lateral=(-Math.sin(previousHeading)*p.velocityX+Math.cos(previousHeading)*p.velocityZ);
  const vx=Math.cos(previousHeading)*longitudinal-Math.sin(previousHeading)*lateral;
  const vz=Math.sin(previousHeading)*longitudinal+Math.cos(previousHeading)*lateral;
  const fx=Math.cos(p.heading),fz=Math.sin(p.heading);
  // Tire relaxation is faster near zero slip, but its per-step correction is
  // bounded by available lateral acceleration so impact momentum is not erased.
  const forward=vx*fx+vz*fz,rawSlip=-vx*fz+vz*fx,slipDecay=1-Math.exp(-(p.altitude>.45?.45:p.offRoad?6:12.5*this.vehicleStats.gripMultiplier)*dt),sideDelta=rawSlip*slipDecay,slip=rawSlip-(p.altitude>.45?sideDelta:clamp(sideDelta,-grip*dt,grip*dt));
  p.velocityX=fx*forward-fz*slip;p.velocityZ=fz*forward+fx*slip;p.speed=forward;p.lateralSpeed=slip;
  p.x+=p.velocityX*dt;p.z+=p.velocityZ*dt;
  this._deckContacts();
  const afterGround=this.projectToRoute(p.x,p.z,p.s);
  const surface=this._surfaceAt(afterGround,p.y,wasGrounded&&p.onRoadDeck&&surfaceBefore.layer==='road',wasGrounded?surfaceBefore.rampId:null);
  const floor=surface.y,oldY=p.y;
  const launch=wasGrounded&&!input.flight&&!input.flip&&!p.flipActive?rampLaunch(surfaceBefore,afterGround,p.velocityX,p.velocityZ,p.heading):null;
  if(launch){p.vz=launch.verticalSpeed;p.flightCeiling=p.y+launch.verticalSpeed*launch.verticalSpeed/(2*9.81)+1;this._airtime.begin({rampId:launch.rampId,player:p,time:this.timer});this._emit('ramp-launch','RAMP / BALLISTIC AIR',launch);}

  p.landingAssist=false;
  const followGround=wasGrounded&&!launch&&!flyingThrust&&!p.flipActive&&Math.abs(floor-p.y)<.65;
  if(followGround){p.y=floor;p.vz=0;p.grounded=true;p.onRoadDeck=surface.layer==='road';}
  else{
   if(wasGrounded&&flyingThrust){p.flightCeiling=p.y+7.5;p.vz=Math.max(p.vz,surfaceBefore.grade*p.speed*Math.cos(p.heading-projection.heading));}
   if(p.flipActive){p.vz=lerp(p.vz,p.stuntPhase==='lift'?2.8:0,1-Math.exp(-8*dt));p.thrusting=true;}
   else if(flyingThrust){const targetVz=1.8+input.lift*4;p.vz=lerp(p.vz,targetVz,1-Math.exp(-3*dt));}
   else p.vz-=9.81*dt;
   const clearance=Math.max(0,p.y-floor);
   if(!p.flipActive&&!flyingThrust&&clearance>0&&clearance<1.8&&p.vz<-2&&p.energy>.03){p.vz=lerp(p.vz,-1.4,1-Math.exp(-10*dt));p.energy=Math.max(0,p.energy-dt*.045);p.thrusting=true;p.landingAssist=true;}
   const impactSpeed=Math.max(0,-p.vz);let nextY=p.y+p.vz*dt;
   const deck=this._deckAt(afterGround),roof=p.flipActive?3:1.2;
   if(deck&&surface.layer==='terrain'&&afterGround.distance<(deck.deckHalfWidth??4.8)){
    const underside=afterGround.y-deckDepth(deck);
    if(oldY+roof<=underside+.05&&nextY+roof>underside){const impact=Math.max(0,p.vz);nextY=underside-roof;p.vz=-p.vz*.08;p.damage=clamp(p.damage+sq(Math.max(0,impact-2))/1800,0,1);this._emit('obstacle-contact','FLYOVER UNDERSIDE',{x:p.x,y:underside,z:p.z,intensity:clamp(impact/12,0,1)});if(p.flipActive){p.flipActive=false;p.stuntRoll=0;p.stuntPhase=null;}}
   }
   if(nextY>=p.flightCeiling&&p.vz>0){nextY=Math.max(oldY,p.flightCeiling);p.vz=0;}
   if(nextY<=floor&&(oldY>=floor-.65||surface.layer==='terrain'||surface.layer==='road'&&!this._deckAt(afterGround))){
    p.y=floor;p.vz=0;p.grounded=true;p.onRoadDeck=surface.layer==='road';
    if(previousAltitude>.001||oldY-floor>.01||this.airtime.active){const hard=impactSpeed>6;p.damage=clamp(p.damage+(hard?(impactSpeed-6)*.015:0),0,1);this._emit('landing',hard?'HARD LANDING':'TOUCHDOWN',{intensity:clamp(impactSpeed/12,.1,1),verticalSpeed:impactSpeed,x:p.x,y:floor,z:p.z});}
   }else{p.y=nextY;p.grounded=false;p.onRoadDeck=false;}
  }
  p.groundY=floor;p.groundPitch=Math.atan(surface.grade);p.groundHeading=surface.heading;const norm=Math.hypot(1,surface.gradientX,surface.gradientZ);p.groundNormalX=-surface.gradientX/norm;p.groundNormalY=1/norm;p.groundNormalZ=-surface.gradientZ/norm;p.altitude=Math.max(0,p.y-floor);p.flying=p.altitude>.08;
  const slopePitch=Math.atan(surface.gradientX*Math.cos(p.heading)+surface.gradientZ*Math.sin(p.heading));
  p.roadPitch=p.grounded?slopePitch:lerp(p.roadPitch,0,1-Math.exp(-4*dt));p.roadRoll=p.grounded?Math.atan(surface.gradientX*Math.sin(p.heading)-surface.gradientZ*Math.cos(p.heading)):lerp(p.roadRoll,0,1-Math.exp(-4*dt));
  p.wheelAngle=angle(p.wheelAngle+p.speed*dt/.366);
  p.bodyRoll=lerp(p.bodyRoll,clamp(-yaw*p.speed*.0045,-.08,.08),1-Math.exp(-8*dt));
  p.bodyPitch=lerp(p.bodyPitch,clamp((p.speed-previousSpeed)/dt*.003,-.055,.04),1-Math.exp(-7*dt));
  p.suspension=p.altitude>.05?0:Math.sin(this.timer*(p.offRoad?28:18))*Math.min(p.offRoad?.018:.006,Math.abs(p.speed)*.0004);
  const after=this.projectToRoute(p.x,p.z,p.s);p.s=after.s;p.lane=after.offset;
  this.wrongWay=p.speed>3&&Math.abs(angle(p.heading-after.heading))>PI*.6;
 }
 _setRampGround(v,surface){
  const norm=Math.hypot(1,surface.gradientX,surface.gradientZ);v.y=v.groundY=surface.y;v.grounded=true;v.onRoadDeck=surface.layer==='road';v.offRoad=surface.layer!=='road';v.altitude=0;v.vz=0;v.flying=false;v.groundHeading=surface.heading;v.groundPitch=Math.atan(surface.grade);v.roadPitch=Math.atan(surface.gradientX*Math.cos(v.heading)+surface.gradientZ*Math.sin(v.heading));v.groundNormalX=-surface.gradientX/norm;v.groundNormalY=1/norm;v.groundNormalZ=-surface.gradientZ/norm;v.flightCeiling=v.y+7.5;
 }
 _applyAIRamp(v,dt,{oldY,oldS,wasAirborne}){
  if(!wasAirborne&&!this.ramps.some(r=>v.s>=r.startS-1&&v.s<=r.lipS+.5))return;
  const q=this.sampleRoute(v.s),old=this.sampleRoute(oldS),before=rampSupport(this.ramps,{...old,offset:v.lane},this.scenario.id),surface=this._surfaceAt({...q,offset:v.lane,worldX:v.x,worldZ:v.z,distance:Math.abs(v.lane),distanceSq:v.lane*v.lane},oldY,!wasAirborne,before&&oldY>=before.y-.12?before.rampId:null),launch=!wasAirborne?rampLaunch(before,{...q,offset:v.lane},Math.cos(v.heading)*v.speed,Math.sin(v.heading)*v.speed,v.heading):null;
  if(launch)v.vz=launch.verticalSpeed;
  if(wasAirborne||launch||oldY>surface.y+.65){v.vz-=9.81*dt;const y=oldY+v.vz*dt;if(y>surface.y){v.y=y;v.groundY=surface.y;v.grounded=false;v.onRoadDeck=false;v.altitude=y-surface.y;v._rampAirborne=true;v.flying=true;v.roadPitch=lerp(v.roadPitch,0,1-Math.exp(-4*dt));return;}}
  v._rampAirborne=false;this._setRampGround(v,surface);
 }
 _rampContacts(old){
  if(!this.ramps.length)return;
  const p=this.player,oldQ=this.projectToRoute(old.x,old.z,old.s),supported=rampSupport(this.ramps,oldQ,this.scenario.id);
  // Cars already on the wedge may leave its lip/edge. An approaching car below
  // the deck meets the actual vertical face, not an invisible convex ramp hull.
  for(const r of this.ramps){
   if(r.enabledScenarios&&!r.enabledScenarios.includes(this.scenario.id)||p.s<r.startS-5||p.s>r.lipS+5||supported?.rampId===r.id&&old.y>=supported.y-.12)continue;
   const walls=[],count=Math.ceil((r.lipS-r.startS)/3),point=(s,side)=>{const q=this.sampleRoute(s),offset=r.centerOffset+side*r.halfWidth;return {x:q.x+q.nx*offset,z:q.z+q.nz*offset,y:q.y,top:q.y+r.rise*(s-r.startS)/(r.lipS-r.startS)};};
   for(const side of [-1,1])for(let i=0;i<count;i++)walls.push([point(r.startS+(r.lipS-r.startS)*i/count,side),point(r.startS+(r.lipS-r.startS)*(i+1)/count,side)]);
   walls.push([point(r.lipS,-1),point(r.lipS,1)]);
   for(let pass=0;pass<3;pass++)for(const [a,b] of walls){
    const [ca,cb]=carSegment(p),hit=closestSegments(ca,cb,a,b),depth=.98-hit.distance;if(depth<=0)continue;
    const lengthSq=sq(b.x-a.x)+sq(b.z-a.z),t=lengthSq?clamp(((hit.b.x-a.x)*(b.x-a.x)+(hit.b.z-a.z)*(b.z-a.z))/lengthSq,0,1):0,top=lerp(a.top,b.top,t),bottom=lerp(a.y,b.y,t);
    if(p.y>=top-.12||p.y+(p.flipActive?3:1.2)<bottom)continue;
    let nx=(hit.a.x-hit.b.x)/(hit.distance||1),nz=(hit.a.z-hit.b.z)/(hit.distance||1);
    if(hit.distance<1e-8){const d=Math.hypot(b.x-a.x,b.z-a.z)||1;nx=-(b.z-a.z)/d;nz=(b.x-a.x)/d;const side=(old.x-hit.b.x)*nx+(old.z-hit.b.z)*nz;if(side<0){nx=-nx;nz=-nz;}}
    this._resolveContact(null,{nx,nz,depth,cx:hit.b.x,cz:hit.b.z},'ramp-wall-'+r.id);
   }
  }
 }
 _updateAirtime(dt,input,eventStart){
  if(!this.airtime.active)return;
  const recent=this.events.filter(e=>e.id>eventStart),landing=recent.find(e=>e.type==='landing');
  const result=this._airtime.update(dt,{player:this.player,input,time:this.timer,contact:this._lastAnyContactAt===this.timer||recent.some(e=>e.type==='contact'||e.type==='obstacle-contact'),landingSpeed:landing?.verticalSpeed??null});
  if(result&&!result.reason)this._emit('airtime-reward',result.actualEnergyAdded>0?(result.actualEnergyAdded<.005?'BIG AIR / <1% BOOST ADDED':'BIG AIR / +'+Math.round(result.actualEnergyAdded*100)+'% BOOST'):'BIG AIR / BOOST FULL',result);
 }
 _airGroundAt(x,z,margin=9.2){
  let ground=this.sampleTerrain(x,z).y;
  const q=this.projectToRoute(x,z,this.player.s),zone=this._roadZone(q);if(zone.distance<=zone.shoulderHalfWidth+margin)ground=Math.max(ground,q.y);
  const ramp=rampSupport(this.ramps,q,this.scenario.id);if(ramp)ground=Math.max(ground,ramp.y);
  const minX=Math.floor((x-margin)/32),maxX=Math.floor((x+margin)/32),minZ=Math.floor((z-margin)/32),maxZ=Math.floor((z+margin)/32),seen=new Set(),near=[...this._dynamicObstacles];
  for(let gx=minX;gx<=maxX;gx++)for(let gz=minZ;gz<=maxZ;gz++)near.push(...(this._obstacleGrid.get(gx+','+gz)||[]));
  for(const o of near){if(seen.has(o.id))continue;seen.add(o.id);if(obstacleCovers(o,x,z,margin))ground=Math.max(ground,finite(o.y,.18)+finite(o.height,1.2));}
  return ground;
 }
 _airDeckOccluded(a,b){
  const dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z;
  for(const deck of this.elevatedCorridors){
   const first=this.sampleRoute(deck.startS).index,last=this.sampleRoute(deck.endS).index;
   for(let i=first;i<=last;i++){
    const seg=this.segments[i],u=(a.x-seg.a.x)*seg.tx+(a.z-seg.a.z)*seg.tz,du=dx*seg.tx+dz*seg.tz,w=-(a.x-seg.a.x)*seg.tz+(a.z-seg.a.z)*seg.tx,dw=-dx*seg.tz+dz*seg.tx;
    const relativeY=a.y-seg.a.y-seg.grade*u,relativeDY=dy-seg.grade*du,half=deck.deckHalfWidth??4.8;
    let enter=0,leave=1;for(const [origin,direction,lo,hi] of [[u,du,Math.max(0,deck.startS-seg.s),Math.min(seg.length,deck.endS-seg.s)],[w,dw,-half,half],[relativeY,relativeDY,-deckDepth(deck),-finite(deck.deckTopBelowRoad)]]){
     if(Math.abs(direction)<1e-10){if(origin<lo||origin>hi){leave=-1;break;}}else{let t0=(lo-origin)/direction,t1=(hi-origin)/direction;if(t0>t1)[t0,t1]=[t1,t0];enter=Math.max(enter,t0);leave=Math.min(leave,t1);}
    }
    if(leave>=enter&&leave>.00001&&enter<.99999)return true;
   }
  }return false;
 }
 _airLineOfSight(a,b,checkOverhead=true){
  // A roof/deck directly above the target blocks the beam even though it is not
  // the car's current support floor (e.g. driving beneath a flyover).
  if((checkOverhead&&this._airGroundAt(b.x,b.z,0)>b.y+.2)||this._airDeckOccluded(a,b))return false;
  const dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z,steps=Math.min(100,Math.max(2,Math.ceil(Math.hypot(dx,dz)/4)));
  for(let i=1;i<steps;i++){const t=i/steps;if(this.sampleTerrain(a.x+dx*t,a.z+dz*t).y>a.y+dy*t-.2)return false;}
  const minX=Math.floor(Math.min(a.x,b.x)/32),maxX=Math.floor(Math.max(a.x,b.x)/32),minZ=Math.floor(Math.min(a.z,b.z)/32),maxZ=Math.floor(Math.max(a.z,b.z)/32),seen=new Set(),near=[...this._dynamicObstacles];
  for(let gx=minX;gx<=maxX;gx++)for(let gz=minZ;gz<=maxZ;gz++)near.push(...(this._obstacleGrid.get(gx+','+gz)||[]));
  for(const o of near){if(seen.has(o.id))continue;seen.add(o.id);const bounds=obstacleBounds(o),c=Math.cos(finite(o.heading)),s=Math.sin(finite(o.heading)),axes=o.shape==='box'?[[((a.x-o.x)*c+(a.z-o.z)*s),dx*c+dz*s,-finite(o.halfLength,1),finite(o.halfLength,1)],[(-(a.x-o.x)*s+(a.z-o.z)*c),-dx*s+dz*c,-finite(o.halfWidth,1),finite(o.halfWidth,1)]]:[[a.x,dx,bounds.minX,bounds.maxX],[a.z,dz,bounds.minZ,bounds.maxZ]];let enter=0,leave=1;for(const [origin,direction,lo,hi] of [...axes,[a.y,dy,finite(o.y,.18),finite(o.y,.18)+finite(o.height,1.2)]]){if(Math.abs(direction)<1e-10){if(origin<lo||origin>hi){leave=-1;break;}}else{let t0=(lo-origin)/direction,t1=(hi-origin)/direction;if(t0>t1)[t0,t1]=[t1,t0];enter=Math.max(enter,t0);leave=Math.min(leave,t1);}}
   if(leave>=enter&&leave>.01&&enter<.99)return false;
  }return true;
 }
 _updateAirTraffic(dt){
  const active=this.airTraffic&&this.state==='racing',floorAt=(x,z)=>this._airGroundAt(x,z),event=this._policeAir.update(dt,{eligible:active&&this.police.length>0,player:this.player,wanted:this.wanted,heat:this.heat,arrestProgress:this.arrestProgress,groundPoliceDistance:this.policeDistance,floorAt,lineOfSight:(a,b)=>this._airLineOfSight(a,b)});
  this._civilianAir.update(dt,{eligible:active&&this.scenario.id!=='free-drive',player:this.player,floorAt,anchor:()=>this.sampleRoute(clamp(this.player.s+clamp(Math.abs(this.player.speed)*8,100,600),0,this.routeLength))});
  if(event)this._emit(event,event==='air-support-dispatched'?'AIR SUPPORT / SEARCHLIGHT INBOUND':'AIR SUPPORT / WITHDRAWING');
 }
 _curveSpeed(s,base,cornerGrip=9.5){
  let limit=base;
  for(let ahead=0;ahead<=56;ahead+=7){const a=this.sampleRoute(s+ahead-3.5),b=this.sampleRoute(s+ahead+3.5),curvature=Math.abs(angle(b.heading-a.heading))/7;
   if(curvature>.0001)limit=Math.min(limit,Math.sqrt(cornerGrip/curvature+20*ahead));
  }
  return clamp(limit,8,base);
 }
 _supportOffRouteAI(v){
  // The route's height is extrapolated only for route sampling, not a phantom
  // asphalt deck beneath AI that start before, or coast beyond, its endpoints.
  // Preserve legacy no-heightfield courses and all on-route AI placement.
  if(!this.terrainGrid||v.s>=0&&v.s<=this.routeLength)return;
  const t=this.sampleTerrain(v.x,v.z),norm=Math.hypot(1,t.gradientX,t.gradientZ);
  v.y=v.groundY=t.y;v.groundPitch=Math.atan(t.grade);v.groundHeading=t.heading;
  v.groundNormalX=-t.gradientX/norm;v.groundNormalY=1/norm;v.groundNormalZ=-t.gradientZ/norm;
  v.roadPitch=Math.atan(t.gradientX*Math.cos(v.heading)+t.gradientZ*Math.sin(v.heading));
  v.roadRoll=Math.atan(t.gradientX*Math.sin(v.heading)-t.gradientZ*Math.cos(v.heading));
  v.onRoadDeck=false;v.offRoad=true;v.flightCeiling=t.y+7.5;
 }
 _placeAI(v,dt){
  const oldX=v.x,oldZ=v.z,oldY=v.y,oldLane=v.lane,oldS=v._rampPreviousS??v.s,wasAirborne=!!v._rampAirborne;const p=this.sampleRoute(v.s);
  v.lane=clamp(lerp(v.lane,v.targetLane,1-Math.exp(-2.1*dt))+v.lateralVelocity*dt,-4.6,4.6);v.lateralVelocity*=Math.exp(-4*dt);this._constrainAIDeck(v,p);
  // AI path followers may not merge through a raised wedge's vertical side.
  // Keep a full capsule outside until the lip is behind them or they are above it.
  for(const r of this.ramps){
   if(r.enabledScenarios&&!r.enabledScenarios.includes(this.scenario.id)||v.s<r.startS||v.s>r.lipS)continue;
   const oldQ=this.sampleRoute(oldS),oldSupport=rampSupport([r],{...oldQ,offset:oldLane},this.scenario.id),top=p.y+r.rise*(v.s-r.startS)/(r.lipS-r.startS);
   if(oldSupport&&oldY>=oldSupport.y-.12||oldY>=top-.12)continue;
   const side=Math.sign(oldLane-r.centerOffset)||1,extent=.98+1.25*Math.abs(Math.sin(v.heading-p.heading))+.02,limit=r.centerOffset+side*(r.halfWidth+extent);
   if(side*(v.lane-limit)<0){v.lane=limit;if(side*v.lateralVelocity<0)v.lateralVelocity=0;}
  }
  v.x=p.x+p.nx*v.lane;v.z=p.z+p.nz*v.lane;v.y=p.y;v.groundY=p.y;v.roadPitch=p.roadPitch;v.groundPitch=p.roadPitch;v.groundHeading=p.heading;v.groundNormalX=-p.grade*p.tx/Math.hypot(1,p.grade);v.groundNormalY=1/Math.hypot(1,p.grade);v.groundNormalZ=-p.grade*p.tz/Math.hypot(1,p.grade);v.roadRoll=0;v.grounded=true;v.onRoadDeck=true;v.offRoad=false;
  const desired=p.heading;const diff=angle(desired-v.heading);
  v.heading=angle(v.heading+clamp(diff,-2.5*dt,2.5*dt));
  v.steer=clamp(diff*.8,-.35,.35);v.wheelAngle=angle(v.wheelAngle+v.speed*dt/.366);
  v.movement=Math.hypot(v.x-oldX,v.z-oldZ);v.velocityX=(v.x-oldX)/dt;v.velocityZ=(v.z-oldZ)/dt;this._supportOffRouteAI(v);if(this.ramps.length)this._applyAIRamp(v,dt,{oldY,oldS,wasAirborne});if(this.ramps.length)v._rampPreviousS=v.s;
 }
 _updateRivals(dt){
  for(let i=0;i<this.rivals.length;i++){
   const v=this.rivals[i];if(v.finished){v.speed=approach(v.speed,0,10*dt);v.s+=v.speed*dt;this._placeAI(v,dt);continue;}
   let target=this._curveSpeed(v.s,v.skill+Math.sin(this.timer*.22+v.phase)*1.3);
   const lead=v.s-this.player.s;target+=clamp(-lead*.015,-3,3);
   const closest=[this.player,...this.rivals.filter(r=>r!==v)].find(o=>o.s>v.s&&o.s-v.s<18&&Math.abs(o.lane-v.lane)<1.7);
   if(closest){
    const otherLane=v.lane<0?1.5:-1.5;
    const occupied=[this.player,...this.rivals.filter(r=>r!==v)].some(o=>Math.abs(o.s-v.s)<11&&Math.abs(o.lane-otherLane)<1.8);
    if(!occupied)v.targetLane=otherLane;else target=Math.min(target,Math.max(9,closest.speed-2));
   }
   v.speed=approach(v.speed,Math.max(8,target),dt*(v.speed<target?7.5:13));v.speed-=9.81*.7*Math.sin(v.roadPitch)*dt;v.s+=v.speed*dt;
   this._placeAI(v,dt);
   if(v.s>=this.endS){v.finished=true;v.finishTime=this.timer;this._emit('rival-finish',v.name+' REACHED THE FINISH',{rival:v.id});}
  }
 }
 _activatePolice(){
  if(this.wanted||!this.police.length)return;
  this.wanted=1;this.heat=.25;this.escapeTimer=0;this.pursuit='pursuit';
  for(const cop of this.police){cop.active=true;cop.siren=true;cop.mode='pursuit';}
  this._emit('detected','PATROL SPOTTED THE RACE / BREAK CONTACT');
 }
 _patrolSeesPlayer(cop,range){
  const player=this.player;
  if(cop.visible===false||Math.hypot(cop.x-player.x,cop.z-player.z,cop.y-player.y)>=range)return false;
  // Reuse the existing terrain, solid-prop and deck occlusion at car eye height.
  return this._airLineOfSight({x:cop.x,y:cop.y+1.1,z:cop.z},{x:player.x,y:player.y+1.1,z:player.z},false);
 }
 _updatePolice(dt){
  const player=this.player;
  if(!this.police.length){this.policeDistance=Infinity;return;}
  if(!this.wanted){
   const canDetect=this.timer>=this._detectionAfter&&player.speed>11;
   const inSight=canDetect&&player.altitude<5&&this.police.some(c=>this._patrolSeesPlayer(c,90));
   if(canDetect&&inSight&&(!this.escaped||this.scenario.id==='coast-sprint'))this._activatePolice();
  }
  for(let i=0;i<this.police.length;i++){
   const cop=this.police[i];
   if(cop.active&&this.wanted){
    const gap=player.s-cop.s;
    // The second unit alternates a signalled closing run with room to regroup.
    // Keep stopped-car capture and the lead unit unchanged; never spawn/warp a unit.
    const cycle=this.timer%24,pressure=i===1&&player.speed>8&&cycle>=8&&cycle<16;
    const regroup=i===1&&player.speed>8&&cycle>=16;
    cop.mode=pressure?'pressure':regroup?'regroup':'pursuit';
    const follow=5.1+i*6.2+(regroup?14:0);
    let target;
    if(gap>20)target=Math.min(43,Math.max(25,player.speed+8+i*1.5));
    else if(gap>follow)target=Math.min(35,Math.max(0,player.speed)+(gap-follow)*1.3);
    else if(gap<-8)target=Math.max(0,Math.min(18,player.speed*.45));
    else target=Math.max(0,player.speed-3);
    if(gap>follow)target=Math.min(target,Math.max(0,player.speed)+Math.sqrt(24*(gap-follow)));
    if(regroup&&gap<40)target=Math.min(target,Math.max(0,player.speed-2));
    target=Math.min(target,this._curveSpeed(cop.s,43,7.6));
    cop.speed=approach(cop.speed,target,dt*(cop.speed<target?8:17));
    cop.targetLane=gap<0?(player.lane<0?2.25:-2.25):clamp(player.lane+(i?(pressure?1.6:regroup?-1.6:.8):-.6),-2.4,2.4);
    cop.s+=cop.speed*dt;
   }else{
    cop.speed=approach(cop.speed,0,12*dt);cop.s+=cop.speed*dt;
    cop.siren=false;cop.active=false;
   }
   this._placeAI(cop,dt);
  }
  this.policeDistance=Math.min(...this.police.map(c=>Math.hypot(c.x-player.x,c.z-player.z,c.y-player.y)));
  if(this.wanted){
   const contact=this.policeDistance<105&&player.altitude<6;
   this.heat=clamp(this.heat+dt*(contact?.016:-.009),.12,1);
   this.wanted=this.heat>.76?3:this.heat>.42?2:1;
   const separated=this.policeDistance>130||(this.escapeTimer>0&&this.policeDistance>110);
   if(separated){
    this.escapeTimer+=dt;this.pursuit='evading';
    if(this.escapeTimer>=8){
     this.escaped=true;this.wanted=0;this.heat=0;this.escapeTimer=0;this.arrestProgress=0;this.pursuit='clear';
     for(const cop of this.police){cop.active=false;cop.siren=false;cop.mode='searching';}
     this._emit('escaped','PURSUIT EVADED / THE COAST IS CLEAR');
    }
   }else{this.escapeTimer=0;this.pursuit='pursuit';}
   const boxed=Math.abs(player.speed)<5&&player.altitude<1.2&&this.police.some(c=>c.active&&Math.abs(c.y-player.y)<1.5&&this._patrolSeesPlayer(c,8.2));
   this.arrestProgress=clamp(this.arrestProgress+dt*(boxed?.245:-.48),0,1);
   if(this.arrestProgress>=1)this._end('busted','BUSTED / PATROL HAS YOUR CAR');
  }else this.arrestProgress=Math.max(0,this.arrestProgress-dt);
 }
 _deckAt(q){
  const section=this.elevatedCorridors.find(c=>q.s>=c.startS&&q.s<=c.endS);
  if(section)return section;
  return null;
 }
 sampleTerrain(x,z){return this.terrainGrid?sampleTerrainGrid(this.terrainGrid,x,z):{y:this.terrainY,gradientX:0,gradientZ:0,grade:0,heading:0,inside:true,layer:'terrain'};}
 _roadSection(s){return this.roadSections.find(c=>s>=finite(c.startS)&&s<=finite(c.endS,this.routeLength))||null;}
 _roadZone(q){
  const section=this._roadSection(q.s),strips=section?.driveableStrips||[{centerOffset:0,halfWidth:section?.halfWidth??3.6,shoulderHalfWidth:section?.shoulderHalfWidth??4.6}];let best=null;
  for(const strip of strips){const d=Math.sqrt(sq(finite(q.offset)-finite(strip.centerOffset))+Math.max(0,finite(q.distanceSq)-sq(finite(q.offset)))),zone={...strip,section,distance:d,halfWidth:finite(strip.halfWidth,section?.halfWidth??3.6),shoulderHalfWidth:finite(strip.shoulderHalfWidth,section?.shoulderHalfWidth??4.6)};if(!best||d-zone.halfWidth<best.distance-best.halfWidth)best=zone;}
  return best;
 }
 _supportProjection(q){
  if(!this.terrainGrid||this._roadZone(q).distance<=this._roadZone(q).shoulderHalfWidth)return q;
  const x=q.worldX??q.x+q.nx*finite(q.offset),z=q.worldZ??q.z+q.nz*finite(q.offset),near=this.projectToRoute(x,z),zone=this._roadZone(near);
  // Physical support may be a different earth-supported branch; race progress
  // still uses its continuous hinted projection and ordered checkpoints.
  return !this._deckAt(near)&&zone.distance<=zone.shoulderHalfWidth?near:q;
 }
 _surfaceAt(q,worldY,followingRoad=false,previousRampId=null){
  q=this._supportProjection(q);const deck=this._deckAt(q),x=q.worldX??q.x+q.nx*(q.offset||0),z=q.worldZ??q.z+q.nz*(q.offset||0),terrain=this.sampleTerrain(x,z),zone=this._roadZone(q);
  let surface,roadY=q.y-.06*clamp((q.distance-3.55)/.15,0,1);
  if(deck)surface=q.distance<=(deck.deckHalfWidth??4.8)&&(followingRoad||worldY>=roadY-.45)?{y:roadY,grade:q.grade,heading:q.heading,gradientX:q.grade*q.tx,gradientZ:q.grade*q.tz,layer:'road'}:terrain;
  else if(this.terrainGrid||zone.section){
   const shoulderDrop=finite(zone.shoulderDrop,finite(zone.section?.shoulderDrop,.06));roadY=q.y-shoulderDrop*clamp((zone.distance-zone.halfWidth)/Math.max(.01,zone.shoulderHalfWidth-zone.halfWidth),0,1);
   surface=zone.distance<=zone.shoulderHalfWidth?{y:roadY,grade:q.grade,heading:q.heading,gradientX:q.grade*q.tx,gradientZ:q.grade*q.tz,layer:'road'}:terrain;
  }else surface={y:roadY-.16*clamp((q.distance-4.5)/.3,0,1),grade:q.distance<4.5?q.grade:0,heading:q.heading,gradientX:q.distance<4.5?q.grade*q.tx:0,gradientZ:q.distance<4.5?q.grade*q.tz:0,layer:q.distance<4.5?'road':'terrain'};
  const ramp=rampSupport(this.ramps,q,this.scenario.id);if(ramp&&(worldY>=ramp.y-.12||followingRoad&&previousRampId===ramp.rampId))surface=ramp;
  // Flat-top OBB proxies are solid roofs/decks, not sideways ejection volumes.
  const gx=Math.floor(x/32),gz=Math.floor(z/32),seen=new Set(),nearby=[...(this._obstacleGrid.get(gx+','+gz)||[]),...this._dynamicObstacles];
  for(const o of nearby){if(o.shape!=='box'||o.support===false||seen.has(o.id))continue;seen.add(o.id);const top=finite(o.y,.18)+finite(o.height,1.2);if(top<=surface.y||worldY<top-.20)continue;
   const h=finite(o.heading),co=Math.cos(h),si=Math.sin(h),dx=x-o.x,dz=z-o.z,lx=dx*co+dz*si,lz=-dx*si+dz*co;
   if(Math.abs(lx)<=finite(o.halfLength,1)&&Math.abs(lz)<=finite(o.halfWidth,1))surface={y:top,grade:0,heading:q.heading,gradientX:0,gradientZ:0,layer:'solid-top',obstacle:o.id};
  }
  return surface;
 }
 _deckContacts(){
  const p=this.player;
  for(let pass=0;pass<3;pass++){
   const q=this.projectToRoute(p.x,p.z,p.s),d=this._deckAt(q);if(!d)break;
   if(p.y+(p.flipActive?3:1.2)<q.y-deckDepth(d)||p.y-(p.flipActive?1.8:0)>q.y+(d.railHeight??1.1))break;
   const underside=q.y-deckDepth(d),roof=p.flipActive?3:1.2;
   if(q.distance<(d.deckHalfWidth??4.8)&&p.y<q.y-.45&&p.y+roof>underside&&Math.abs(q.grade)>.01){const direction=Math.sign(q.grade);this._resolveContact(null,{nx:q.tx*direction,nz:q.tz*direction,depth:(p.y+roof-underside)/Math.abs(q.grade),cx:p.x-q.tx*direction*2,cz:p.z-q.tz*direction*2},'deck-ramp-'+d.startS);continue;}
   const side=Math.sign(q.offset)||1,extent=(p.flipActive?1.65:.98)+1.25*Math.abs(Math.sin(p.heading-q.heading)),half=d.halfWidth??4.42,thick=(d.railThickness??.3)/2;
   const gap=Math.abs(q.distance-half),depth=extent+thick-gap;if(depth<=0)break;
   const outward=q.distance>=half?1:-1,nx=q.nx*side*outward,nz=q.nz*side*outward;
   this._resolveContact(null,{nx,nz,depth,cx:q.x+q.nx*side*half,cz:q.z+q.nz*side*half},'deck-edge-'+d.startS+'-'+side);
  }
 }
 _flipHasClearance(q){
  const p=this.player,deck=this._deckAt(q);if(deck&&q.distance<4.8&&p.y<q.y-.45&&p.y+3>q.y-deckDepth(deck))return false;
  const gx=Math.floor(p.x/32),gz=Math.floor(p.z/32),near=[...this._dynamicObstacles],seen=new Set();
  for(let x=gx-1;x<=gx+1;x++)for(let z=gz-1;z<=gz+1;z++)near.push(...(this._obstacleGrid.get(x+','+z)||[]));
  for(const o of near){if(seen.has(o.id))continue;seen.add(o.id);const bottom=finite(o.y,.18),top=bottom+finite(o.height,1.2);if(p.y-1.8<top&&p.y+3>bottom&&this._obstacleContact(o,{...p,flipActive:true}).depth>0)return false;}
  for(const v of [...this.rivals,...this.police])if(v.visible&&p.y-1.8<v.y+1.2&&p.y+3>v.y&&distance(p,v)<4.5)return false;
  return true;
 }
 _bodyVelocity(v){
  const fx=Math.cos(v.heading),fz=Math.sin(v.heading);
  if(v!==this.player)return {x:fx*v.speed-fz*(v.lateralVelocity||0),z:fz*v.speed+fx*(v.lateralVelocity||0)};
  const projected=v.velocityX*fx+v.velocityZ*fz;
  // This also permits deterministic test/debug placement through the public speed field.
  if(Math.abs(projected-v.speed)>.001){v.velocityX=fx*v.speed-fz*(v.lateralSpeed||0);v.velocityZ=fz*v.speed+fx*(v.lateralSpeed||0);}
  return {x:v.velocityX,z:v.velocityZ};
 }
 _setBodyVelocity(v,x,z){
  const fx=Math.cos(v.heading),fz=Math.sin(v.heading);v.velocityX=x;v.velocityZ=z;
  v.speed=clamp(x*fx+z*fz,-35,95);v.lateralSpeed=-x*fz+z*fx;
  if(v!==this.player)v.lateralVelocity=clamp(v.lateralSpeed,-12,12);
 }
 _aiRoadBounds(q,heading=q.heading){
  const d=this._deckAt(q),section=this._roadSection(q.s);if(!d&&!section)return null;
  const extent=.98+1.25*Math.abs(Math.sin(heading-q.heading))+.02;
  if(d){const limit=Math.max(.5,(d.halfWidth??4.42)-(d.railThickness??.3)/2-extent);return {min:-limit,max:limit};}
  const strips=section.driveableStrips||[{centerOffset:0,halfWidth:finite(section.halfWidth,3.6)}],strip=[...strips].sort((a,b)=>Math.abs(finite(a.centerOffset))-Math.abs(finite(b.centerOffset)))[0],center=finite(strip.centerOffset),limit=Math.max(.5,finite(strip.halfWidth,3.6)-extent);
  return {min:center-limit,max:center+limit};
 }
 _constrainAIDeck(v,q){
  const bounds=this._aiRoadBounds(q,v.heading);if(!bounds)return;
  v.lane=clamp(v.lane,bounds.min,bounds.max);v.targetLane=clamp(v.targetLane,bounds.min,bounds.max);
  if(v.lane<=bounds.min+.001&&v.lateralVelocity<0||v.lane>=bounds.max-.001&&v.lateralVelocity>0)v.lateralVelocity=0;
 }
 _translateBody(v,x,z){
  v.x+=x;v.z+=z;
  if(v!==this.player){const q=this.projectToRoute(v.x,v.z,v.s);v.s=q.s;v.lane=q.offset;this._constrainAIDeck(v,q);v.x=q.x+q.nx*v.lane;v.z=q.z+q.nz*v.lane;}
 }
 _resolveContact(other,contact,key){
  const a=this.player,b=other,invA=1/a.mass,invB=b?1/b.mass:0,total=invA+invB;
  const {nx,nz,depth,cx,cz}=contact;
  if(depth>=-.001){this._lastAnyContactAt=this.timer;if(!b)this._lastSolidContactAt=this.timer;}
  if(depth>0){const correction=Math.min(.38,Math.max(0,depth-.003)*.78);this._translateBody(a,nx*correction*invA/total,nz*correction*invA/total);if(b)this._translateBody(b,-nx*correction*invB/total,-nz*correction*invB/total);}
  const va=this._bodyVelocity(a),vb=b?this._bodyVelocity(b):{x:finite(contact.velocityX),z:finite(contact.velocityZ)};
  const closing=-((va.x-vb.x)*nx+(va.z-vb.z)*nz);if(closing<=.02)return;
  const impulse=(1.10)*closing/total,tx=-nz,tz=nx;
  const tangential=(va.x-vb.x)*tx+(va.z-vb.z)*tz;
  const friction=clamp(-tangential/total,-impulse*.22,impulse*.22);
  const ix=nx*impulse+tx*friction,iz=nz*impulse+tz*friction;
  this._setBodyVelocity(a,va.x+ix*invA,va.z+iz*invA);
  if(b){this._setBodyVelocity(b,vb.x-ix*invB,vb.z-iz*invB);this._constrainAIDeck(b,this.sampleRoute(b.s));}
  const torque=((cx-a.x)*iz-(cz-a.z)*ix)/(a.mass*1.95);
  a.collisionYaw=clamp(a.collisionYaw+torque*.13,-1.15,1.15);
  if(closing>2&&this.timer>=(this._collisionCooldowns.get(key)||0)){
   const severity=clamp(sq(closing-2)/1800*(b?.7:1),0,.48);
   a.damage=clamp(a.damage+severity,0,1);a.impactShake=Math.max(a.impactShake,clamp(closing/28,0,1));
   this._collisionCooldowns.set(key,this.timer+.35);
   this._emit(b?'contact':'obstacle-contact',b?(b.id.startsWith('patrol')?'PATROL CONTACT':'BODYWORK CONTACT'):'ROADSIDE CONTACT',{x:cx,y:a.y+.45,z:cz,intensity:clamp(closing/25,0,1),closingSpeed:closing,impulse,normalX:nx,normalZ:nz,other:key});
  }
 }
 _carContact(v){
  const a=this.player,aa=carSegment(a),bb=carSegment(v),q=closestSegments(...aa,...bb),carRadius=a.flipActive?1.65:.98,radius=carRadius+.98;
  if(q.distance>=radius)return null;
  const dx=q.a.x-q.b.x,dz=q.a.z-q.b.z,center=Math.hypot(a.x-v.x,a.z-v.z);
  const nx=q.distance>1e-7?dx/q.distance:center>1e-7?(a.x-v.x)/center:-Math.cos(a.heading);
  const nz=q.distance>1e-7?dz/q.distance:center>1e-7?(a.z-v.z)/center:-Math.sin(a.heading);
  return {nx,nz,depth:radius-q.distance,cx:q.a.x-nx*carRadius,cz:q.a.z-nz*carRadius};
 }
 _vehicleContacts(dt){
  for(let pass=0;pass<3;pass++)for(const v of [...this.rivals,...this.police]){
   if(!v.visible||this.player.y+(this.player.flipActive?-1.8:0)>v.y+1.2||this.player.y+(this.player.flipActive?3:1.2)<v.y)continue;
   const contact=this._carContact(v);if(contact)this._resolveContact(v,contact,v.id);
  }
  this.damage=this.player.damage;
 }
 _obstacleContact(o,pose=this.player){
  const segment=carSegment(pose),carRadius=pose.flipActive?1.65:.98;
  if(o.shape==='box'){
   const h=finite(o.heading),co=Math.cos(h),si=Math.sin(h),hl=Math.max(.01,finite(o.halfLength,1)),hw=Math.max(.01,finite(o.halfWidth,1));
   const local=p=>({x:(p.x-o.x)*co+(p.z-o.z)*si,z:-(p.x-o.x)*si+(p.z-o.z)*co}),a=local(segment[0]),b=local(segment[1]);
   const corners=[{x:-hl,z:-hw},{x:hl,z:-hw},{x:hl,z:hw},{x:-hl,z:hw}];
   let q=null;for(let i=0;i<4;i++){const t=closestSegments(a,b,corners[i],corners[(i+1)%4]);if(!q||t.distance<q.distance)q=t;}
   const center=local(pose),inside=Math.abs(center.x)<hl&&Math.abs(center.z)<hw;
   let nx,nz,depth,cx,cz;
   if(inside){const dx=hl-Math.abs(center.x),dz=hw-Math.abs(center.z);nx=dx<dz?(Math.sign(center.x)||1):0;nz=dx<dz?0:(Math.sign(center.z)||1);depth=carRadius+Math.min(dx,dz);cx=center.x+nx*Math.min(dx,dz);cz=center.z+nz*Math.min(dx,dz);}
   else{const sideX=Math.abs(center.x)-hl,sideZ=Math.abs(center.z)-hw;nx=q.distance>1e-7?(q.a.x-q.b.x)/q.distance:sideX>sideZ?(Math.sign(center.x)||1):0;nz=q.distance>1e-7?(q.a.z-q.b.z)/q.distance:sideX>sideZ?0:(Math.sign(center.z)||1);depth=carRadius-q.distance;cx=q.b.x;cz=q.b.z;}
   return {nx:nx*co-nz*si,nz:nx*si+nz*co,depth,cx:o.x+cx*co-cz*si,cz:o.z+cx*si+cz*co};
  }
  const q=closestSegments(...segment,{x:o.x,z:o.z},{x:o.endX??o.x,z:o.endZ??o.z});
  const odx=(o.endX??o.x)-o.x,odz=(o.endZ??o.z)-o.z,olen=Math.hypot(odx,odz),side=Math.sign((pose.x-o.x)*(-odz)+(pose.z-o.z)*odx)||1;
  const center=Math.hypot(pose.x-o.x,pose.z-o.z),nx=q.distance>1e-7?(q.a.x-q.b.x)/q.distance:olen>1e-7?-odz/olen*side:center>1e-7?(pose.x-o.x)/center:-Math.cos(pose.heading),nz=q.distance>1e-7?(q.a.z-q.b.z)/q.distance:olen>1e-7?odx/olen*side:center>1e-7?(pose.z-o.z)/center:-Math.sin(pose.heading);
  return {nx,nz,depth:carRadius+o.radius-q.distance,cx:q.a.x-nx*carRadius,cz:q.a.z-nz*carRadius};
 }
 setDynamicObstacles(obstacles=[]){this._dynamicObstacles=(Array.isArray(obstacles)?obstacles:[]).filter(o=>o&&Number.isFinite(o.x)&&Number.isFinite(o.z)&&Number.isFinite(o.radius)&&o.radius>0).slice(0,256).map((o,i)=>({...o,id:o.id??'dynamic-'+i}));return this;}
 _obstacleContacts(dt,old=null){
  const p=this.player;if(!this.obstacles.length&&!this._dynamicObstacles.length)return;
  const bx=Math.floor(p.x/32),bz=Math.floor(p.z/32),seen=new Set(),near=[];
  for(let gx=bx-1;gx<=bx+1;gx++)for(let gz=bz-1;gz<=bz+1;gz++)for(const o of this._obstacleGrid.get(gx+','+gz)||[]){
   if(seen.has(o.id))continue;seen.add(o.id);const bottom=Number.isFinite(o.y)?o.y:.18,top=bottom+(Number.isFinite(o.height)?o.height:1.2);
   if(p.y+(p.flipActive?-1.8:0)>=top-.001||p.y+(p.flipActive?3:1.2)<bottom)continue;near.push(o);
  }
  for(const o of this._dynamicObstacles){const b=obstacleBounds(o),bottom=finite(o.y,.18),top=bottom+finite(o.height,1.2);if(p.x+3>=b.minX&&p.x-3<=b.maxX&&p.z+3>=b.minZ&&p.z-3<=b.maxZ&&p.y+(p.flipActive?-1.8:0)<=top&&p.y+(p.flipActive?3:1.2)>=bottom)near.push(o);}
  if(old)for(let i=near.length-1;i>=0;i--){const o=near[i],bottom=finite(o.y,.18),roof=p.flipActive?3:1.2;
   if(bottom-p.groundY>roof+.02&&old.y+(old.height??1.2)<=bottom+.02&&p.y+roof>=bottom&&this._obstacleContact(o).depth>0){const impact=Math.max(0,p.vz);p.y=Math.max(p.groundY,bottom-roof-.002);p.vz=-impact*.08;p.altitude=Math.max(0,p.y-p.groundY);p.flying=p.altitude>.08;p.grounded=p.altitude<.001;const key='underside-'+o.id;if(impact>.5&&this.timer>=(this._collisionCooldowns.get(key)||0)){p.damage=clamp(p.damage+sq(Math.max(0,impact-2))/1800,0,1);this._collisionCooldowns.set(key,this.timer+.35);this._emit('obstacle-contact','OVERHEAD CONTACT',{x:p.x,y:bottom,z:p.z,intensity:clamp(impact/12,0,1)});}if(p.flipActive){p.flipActive=false;p.stuntRoll=0;p.stuntPhase=null;}near.splice(i,1);}
  }
  // Conservative advancement of the moving capsule catches thin posts and rails
  // before penetration; fixed 120Hz substeps bound the remaining contact error.
  if(old){const movement=Math.hypot(p.x-old.x,p.z-old.z),rotation=Math.abs(angle(p.heading-old.heading)),bound=movement+rotation*1.25;let earliest=1,hit=null;
   if(bound>1e-8)for(const o of near){let t=0;if(this._obstacleContact(o,old).depth>0)continue;
    for(let i=0;i<24&&t<=earliest;i++){const pose={x:lerp(old.x,p.x,t),z:lerp(old.z,p.z,t),heading:old.heading+angle(p.heading-old.heading)*t,flipActive:p.flipActive};const c=this._obstacleContact(o,pose);
     if(c.depth>=-.0005){earliest=t;hit={o,c};break;}t+=Math.max(.00001,-c.depth/bound*.9);
    }
   }
   if(hit){p.x=lerp(old.x,p.x,earliest);p.z=lerp(old.z,p.z,earliest);this._resolveContact(null,{...hit.c,velocityX:hit.o.velocityX,velocityZ:hit.o.velocityZ},'static-'+hit.o.id);const left=dt*(1-earliest);p.x+=p.velocityX*left;p.z+=p.velocityZ*left;}
  }
  for(let pass=0;pass<4;pass++)for(const o of near){const c=this._obstacleContact(o);if(c.depth>0)this._resolveContact(null,{...c,velocityX:o.velocityX,velocityZ:o.velocityZ},'static-'+o.id);}
  this.damage=p.damage;
 }
 _updateCoins(old){
  const p=this.player;
  // Only normal, grounded travel can sweep a pickup. Recovery does not call this
  // routine; the run ledger survives all returns and pays only after race finish.
  if(this.state!=='racing'||this.scenario.id==='free-drive'||!old.grounded||!p.grounded||old.altitude>.15||p.altitude>.15||p.flipActive||p.flying||distance(old,p)>2||Math.abs(p.s-old.s)>4)return;
  const zone=this._roadZone(this.projectToRoute(p.x,p.z,p.s));if(zone.distance>zone.halfWidth+.1)return;
  for(const coin of this.coins){
   if(coin.collected||Math.abs(coin.s-p.s)>5||Math.abs(p.y-(coin.y-.65))>.4||!this._checkpointCarriageway(this.sampleRoute(coin.s),old))continue;
   if(segmentNear(old.x,old.z,p.x,p.z,coin.x,coin.z,1.85)){
    coin.collected=true;this.collectedCoinIds.add(coin.id);this.coinsCollected+=coin.value;
    this._emit('coin-collected','+'+coin.value+' COINS / BANK ON FINISH',{coinId:coin.id,value:coin.value,total:this.coinsCollected,x:coin.x,y:coin.y,z:coin.z});
   }
  }
 }
 _checkpointCarriageway(gate,old){
  const section=this._roadSection(gate.s);if(!section)return true;
  const strips=section.driveableStrips||[{centerOffset:0,halfWidth:section.halfWidth??3.6}],raceStrip=strips.reduce((a,b)=>Math.abs(finite(b.centerOffset))<Math.abs(finite(a.centerOffset))?b:a);
  const p=this.player,dx=p.x-old.x,dz=p.z-old.z,len=dx*dx+dz*dz,t=len>1e-12?clamp(((gate.x-old.x)*dx+(gate.z-old.z)*dz)/len,0,1):0;
  const lateral=(old.x+dx*t-gate.x)*gate.nx+(old.z+dz*t-gate.z)*gate.nz;
  // Adjacent divided carriageways remain explorable, but do not score the race
  // gate. A small tire-edge allowance is not enough to reach the other lanes.
  return Math.abs(lateral-finite(raceStrip.centerOffset))<=finite(raceStrip.halfWidth,section.halfWidth??3.6)+.55;
 }
 _updateRace(old,dt){
  if(this.state!=='racing')return;
  const player=this.player;if(this.scenario.id==='free-drive'){this.progress=clamp(player.s/this.routeLength,0,1);this.distanceRemaining=Math.max(0,this.routeLength-player.s);this.position=1;return;}const gate=this.checkpoints[this.nextCheckpoint];
  if(gate&&this._checkpointCarriageway(gate,old)&&player.y>=gate.y-.55&&player.y<=gate.y+8&&segmentNear(old.x,old.z,player.x,player.z,gate.x,gate.z,11)){
   this.nextCheckpoint++;this._emit('checkpoint','CHECKPOINT '+Math.min(this.nextCheckpoint-1,this.totalCheckpoints)+' / '+this.totalCheckpoints);
   if(this.nextCheckpoint>=this.checkpoints.length)this._allGatesPassed=true;
  }
  this.progress=clamp((player.s-this.startS)/this.length,0,1);
  this.distanceRemaining=Math.max(0,this.endS-player.s);
  this.position=1+this.rivals.filter(v=>v.finished||v.s>player.s).length;
  if(this._allGatesPassed){
   if(this.scenario.id!=='hot-pursuit'||this.escaped&&!this.wanted)this._end('finished',this.position===1?'COAST CONQUERED':'FINISH LINE');
   else if(!this._terminalAnnounced){this._terminalAnnounced=true;this._emit('finish-locked','SAFEHOUSE REACHED / SHAKE THE PURSUIT');}
  }
 }
 _end(state,title){
  if(this.state!=='racing')return;
  if(state==='finished'){this.progress=1;this.distanceRemaining=0;}
  this._airtime.cancel('event-ended');this._policeAir.stop();this._civilianAir.stop();this._stopUltra('event-ended');this.state=state;this.result={state,title,time:this.timer,position:this.position,totalCars:1+this.rivals.length,penalties:this.penalties,damage:this.player.damage,escaped:this.escaped,scenario:this.scenario.id,collectedCoins:this.coinsCollected};
  this._emit(state,title);
 }
}

export const __testing=Object.freeze({angle,segmentNear,inputSafe,FIXED,steeringEnvelope,closestSegments,normalizeTerrainGrid,sampleTerrainGrid});

export function buildCourseObstacles(world,furniture=[]){
 const props=world.prop_instances.filter(p=>/CoconutPalm|KeralaHouse|FishingBoat|SeaWallRock/.test(p.asset)).map((p,i)=>{
  const scale=p.scale,id='prop-'+i;
  if(p.asset==='KeralaHouse'){
   // Authored local GLTF bounds, including roof overhang; no oversized circle.
   const x=.048149*scale,z=.547981*scale,co=Math.cos(p.yaw_rad),si=Math.sin(p.yaw_rad),halfLength=4.621851*scale,halfWidth=3.936682*scale;
   return {id,shape:'box',x:p.position[0]+co*x+si*z,z:p.position[2]-si*x+co*z,y:p.position[1],height:4.699863*scale,halfLength,halfWidth,heading:-p.yaw_rad,radius:Math.hypot(halfLength,halfWidth)};
  }
  return {id,x:p.position[0],z:p.position[2],y:p.position[1],height:(p.asset.includes('Palm')?8.5:p.asset==='FishingBoat'?1.4:1.1)*scale,radius:(p.asset.includes('Palm')?.32:p.asset==='FishingBoat'?3.2:1.2)*scale};
 });
 // Legacy Blender export represented each straight Bridge_Rail with a row of
 // tiny circles. Collapse only complete, collinear, matching rail IDs: the old
 // visual mesh stays unchanged while contacts use its continuous rail surface.
 const groups=new Map();
 for(const o of furniture){const match=/^(furniture-Bridge_Rail(?:\.\d+)?)-(\d+)$/.exec(o.id||'');if(!match||o.shape||Number.isFinite(o.endX)||Number.isFinite(o.endZ))continue;const key=match[1];if(!groups.has(key))groups.set(key,[]);groups.get(key).push({o,index:Number(match[2])});}
 const replaced=new Set(),rails=[];
 for(const [id,entries] of groups){
  entries.sort((a,b)=>a.index-b.index);if(entries.length<2)continue;
  const a=entries[0].o,b=entries.at(-1).o,dx=b.x-a.x,dz=b.z-a.z,den=dx*dx+dz*dz;if(den<.01)continue;
  let previous=-Infinity;const compatible=entries.every(({o,index},i)=>{
   const t=((o.x-a.x)*dx+(o.z-a.z)*dz)/den,off=Math.hypot(o.x-a.x-dx*t,o.z-a.z-dz*t);
   const okay=(i===0||index===entries[i-1].index+1)&&t>previous&&off<.03&&Math.abs(o.radius-a.radius)<1e-6&&Math.abs(finite(o.y,.18)-finite(a.y,.18))<1e-5&&Math.abs(finite(o.height,1.2)-finite(a.height,1.2))<1e-5;previous=t;return okay;
  });
  if(!compatible)continue;
  entries.forEach(({o})=>replaced.add(o));rails.push({...a,id:id+'-capsule',endX:b.x,endZ:b.z,legacyRailSamples:entries.length});
 }
 return [...props,...furniture.filter(o=>!replaced.has(o)),...rails];
}
