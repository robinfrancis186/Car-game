import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
const source=readFileSync(new URL('../src/gameplay.js',import.meta.url),'utf8');
const {GameModel,SCENARIOS,__testing,buildCourseObstacles}=await import('../src/gameplay.js');
const {TRACKS,eventSlice,routeLength,worldPhysicsOptions}=await import('../src/tracks.js');
const line=Array.from({length:101},(_,i)=>({x:i*50,z:0,y:.18}));
const advance=(m,seconds,input={},hz=60)=>{for(let i=0;i<Math.ceil(seconds*hz);i++)m.update(1/hz,input);return m;};
const ready=(id='coast-sprint',route=line)=>advance(new GameModel(route).start(id),3.1);
let count=0,failures=0;const metrics={generatedAt:new Date().toISOString(),scope:'Pure-JS simulation; not browser or real-device acceptance',steering:[],collisions:[],wallScrapes:[],routes:[],tests:[]};
const test=(name,fn)=>{try{fn();count++;metrics.tests.push({name,status:'pass'});console.log('PASS',name);}catch(error){failures++;metrics.tests.push({name,status:'fail',error:error.message});console.error('FAIL',name,error.message);}};
metrics.exploreDepartures=[];
function testExploreDepartures(trackId,world,route,obstacles){
 for(const destination of world.explore_starts||[])for(const [variant,maxSteer] of [['red',.57],['silver',.4]])test('actual UI Explore departure stays clear for3 seconds: '+trackId+' / '+destination.name+' / '+variant,()=>{
  const selectedS=destination.s??destination.start_s??destination.startS??destination.start??0,slice=eventSlice(TRACKS[trackId],world,'free-drive',routeLength(route),selectedS);
  const m=new GameModel(route,{...slice,...worldPhysicsOptions(world),obstacles,seed:267,maxSteer}).start('free-drive'),p=m.player,spawnS=p.s,heading=p.heading,q=m.sampleRoute(spawnS);assert.equal(spawnS,slice.startS+8);assert.equal(heading,q.heading);assert.equal(p.y,q.y);
  for(const o of m.obstacles){const bottom=o.y??.18,top=bottom+(o.height??1.2);if(p.y+1.2>bottom&&p.y<top)assert(m._obstacleContact(o).depth<=.003,'initial overlap with '+o.id);}
  let minPavementMargin=Infinity,maxLateral=0;
  for(let i=0;i<360;i++){m.update(1/120,{throttle:1,steer:0});const center=m.projectToRoute(p.x,p.z,p.s);maxLateral=Math.max(maxLateral,center.distance);
   for(const sign of [-1,1]){const cap=m.projectToRoute(p.x+Math.cos(p.heading)*1.25*sign,p.z+Math.sin(p.heading)*1.25*sign,p.s),zone=m._roadZone(cap);minPavementMargin=Math.min(minPavementMargin,zone.halfWidth-zone.distance-.98);}
   assert(!p.offRoad&&p.grounded&&p.altitude===0,'departure must remain on supported asphalt');assert.equal(p.damage,0);assert(center.distance<4.3,'must not enable the main water-recovery guard');
  }
  assert(minPavementMargin>=.03,'whole capsule must remain on pavement, margin='+minPavementMargin);assert(p.speed>27,'must accelerate freely, not remain pinned');assert.equal(m.recoveries,0);assert.equal(m.penalties,0);assert.equal(m.events.filter(e=>['contact','obstacle-contact','water-contact'].includes(e.type)).length,0);assert(Math.abs(__testing.angle(p.heading-heading))<1e-10,'no hidden launch steering');
  metrics.exploreDepartures.push({track:trackId,destination:destination.name,variant,selectedS,spawnS,heading,seconds:3,finalS:p.s,speedMps:p.speed,damage:p.damage,minPavementMarginMetres:minPavementMargin,maxLateralMetres:maxLateral});
 });
}
test('rejects invalid and zero-length route',()=>{assert.throws(()=>new GameModel([]));assert.throws(()=>new GameModel([{x:0,z:0},{x:NaN,z:1}]));assert.throws(()=>new GameModel([{x:0,z:0},{x:0,z:0}]));});
test('scenario definitions and countdown transition',()=>{assert.equal(SCENARIOS.length,4);const m=new GameModel(line);assert.equal(m.state,'menu');m.start('coast-sprint');assert.equal(m.state,'countdown');advance(m,3.1);assert.equal(m.state,'racing');assert.equal(m.rivals.length,3);assert.equal(m.police.length,2);});
test('route sampling and projection use metres and signed offset',()=>{const m=new GameModel(line);assert.equal(m.sampleRoute(55).x,55);assert.equal(m.sampleRoute(-10).x,-10);const p=m.projectToRoute(55,2);assert.equal(p.s,55);assert.equal(p.offset,2);assert.equal(p.distance,2);});
test('forward acceleration rolls wheels and remains bounded',()=>{const m=ready('time-attack');advance(m,8,{throttle:1});assert(m.player.speed>50);assert(m.player.speed<=68.1);assert(m.player.x>200);assert.notEqual(m.player.wheelAngle,0);assert(m.progress>0);});
test('braking reaches stop without reversing',()=>{const m=ready('time-attack');advance(m,5,{throttle:1});advance(m,5,{brake:true});assert.equal(m.player.speed,0);});
test('reverse control brakes then reverses',()=>{const m=ready('time-attack');advance(m,2,{throttle:1});advance(m,6,{throttle:-1});assert(m.player.speed<0);assert(m.player.speed>=-10);});
test('positive steering turns toward positive Z',()=>{const m=ready('time-attack');advance(m,1,{throttle:1});const z=m.player.z;advance(m,.4,{throttle:1,steer:1});assert(m.player.heading>0);assert(m.player.z>z);});
test('fixed-step simulation invariant at 30/60/120Hz',()=>{const a=ready('time-attack'),b=ready('time-attack'),c=ready('time-attack');advance(a,5,{throttle:1},30);advance(b,5,{throttle:1},60);advance(c,5,{throttle:1},120);assert(Math.abs(a.player.x-b.player.x)<1e-7);assert(Math.abs(a.player.x-c.player.x)<1e-7);assert(Math.abs(a.timer-c.timer)<1e-7);});
test('pause prevents time, movement, charge changes',()=>{const m=ready('time-attack');advance(m,1,{throttle:1});const p={...m.player},t=m.timer;m.setPaused(true);advance(m,20,{throttle:1});assert.equal(m.timer,t);assert.equal(m.player.x,p.x);m.setPaused(false);advance(m,1,{throttle:1});assert(m.player.x>p.x);});
test('paused recovery cannot teleport or add a penalty',()=>{const m=ready('time-attack');advance(m,2,{throttle:1});m.setPaused(true);const t=m.timer,x=m.player.x;assert.equal(m.recover(),false);assert.equal(m.timer,t);assert.equal(m.player.x,x);});
test('recovery synchronizes remaining time and progress before the next frame',()=>{const m=ready('time-attack');advance(m,2,{throttle:1});m.recover();m.setPaused(true);assert.equal(m.timeRemaining,m.timeLimit-m.timer);assert.equal(m.distanceRemaining,m.endS-m.player.s);assert.equal(m.progress,(m.player.s-m.startS)/m.length);m.setPaused(false);m.timer=m.timeLimit-2;m.recover();assert.equal(m.state,'failed');assert.equal(m.timeRemaining,0);});
test('offroad reduces speed and recovery costs five seconds',()=>{const m=ready('time-attack');m.player.z=15;advance(m,10,{throttle:1});assert(m.player.speed<=21.1);const t=m.timer;assert(m.recover());assert.equal(m.timer,t+5);assert.equal(m.penalties,5);assert.equal(m.player.speed,0);assert(Math.abs(m.player.z+1.65)<.01);});
test('grounded wheels follow authored road, shoulder and terrain elevations',()=>{const m=ready('time-attack');for(const [z,y] of [[0,.18],[4,.12],[6,-.04]]){Object.assign(m.player,{z,speed:0,altitude:0,vz:0});advance(m,1/60);assert(Math.abs(m.player.y-y)<1e-8,`${z}: expected${y}, got${m.player.y}`);}});
test('flight rises, caps altitude, consumes energy, lands',()=>{const m=ready('time-attack');advance(m,3,{flight:true});assert(m.player.altitude>1);assert(m.player.altitude<=7.5);assert(m.player.energy<1);advance(m,8,{});assert.equal(m.player.altitude,0);assert.equal(m.player.y,.18);});
test('kickflip requires clearance, speed and a landing energy reserve',()=>{
 for(const [altitude,speed,energy] of [[0,20,1],[3,0,1],[3,20,.29]]){const m=ready('time-attack');Object.assign(m.player,{altitude,speed,energy,y:altitude+.18});advance(m,1/120,{flip:true});assert(!m.player.flipActive);assert(m.events.some(e=>e.type==='flip-unavailable'));}
 const m=ready('time-attack');Object.assign(m.player,{altitude:3,y:3.18,speed:20,energy:.30});advance(m,1/120,{flip:true,flight:true});assert(m.player.flipActive);assert(Math.abs(m.player.energy-.08)<1e-10);
});
test('kickflip completes one longitudinal revolution and does not repeat while held',()=>{
 const m=ready('time-attack');Object.assign(m.player,{altitude:3,y:3.18,speed:20});let maxRoll=0;const phases=new Set();
 for(let i=0;i<390;i++){m.update(1/120,{flip:true,flight:true,throttle:.3});maxRoll=Math.max(maxRoll,m.player.stuntRoll);if(m.player.stuntPhase)phases.add(m.player.stuntPhase);assert(m.player.altitude>=2.8);assert(Number.isFinite(m.player.stuntRoll));}
 assert(maxRoll>Math.PI*1.99);assert.equal(m.player.stuntRoll,0);assert(!m.player.flipActive);assert.deepEqual([...phases],['lift','roll','counterthrust','level']);assert.equal(m.events.filter(e=>e.type==='flip-start').length,1);assert.equal(m.events.filter(e=>e.type==='flip-complete').length,1);assert(m.player.energy>.70);
});
test('paused kickflip freezes and recovery clears its pose',()=>{
 const m=ready('time-attack');Object.assign(m.player,{altitude:3,y:3.18,speed:20});advance(m,.8,{flip:true});assert(m.player.stuntRoll>0);const roll=m.player.stuntRoll,alt=m.player.altitude;m.setPaused(true);advance(m,5,{flip:true});assert.equal(m.player.stuntRoll,roll);assert.equal(m.player.altitude,alt);m.setPaused(false);assert(m.recover());assert(!m.player.flipActive);assert.equal(m.player.stuntRoll,0);assert.equal(m.player.altitude,0);
});
test('landing assist brakes descent and touchdown fires once',()=>{
 const m=ready('time-attack');Object.assign(m.player,{altitude:1.7,y:1.88,vz:-7});advance(m,.1);assert(m.player.landingAssist);assert(m.player.vz>-4.5);advance(m,2);assert.equal(m.player.altitude,0);assert.equal(m.player.damage,0);assert.equal(m.events.filter(e=>e.type==='landing').length,1);assert(m.events.find(e=>e.type==='landing').verticalSpeed<6);
});
test('unassisted hard landing is finite and damages the car',()=>{
 const m=ready('time-attack');Object.assign(m.player,{altitude:.1,y:.28,vz:-12,energy:0});advance(m,1/60);assert.equal(m.player.altitude,0);assert(m.player.damage>0);assert.equal(m.events.filter(e=>e.type==='landing').length,1);
});
test('silver steering cap obeys the validated wheel-arch envelope',()=>{
 const m=advance(new GameModel(line,{maxSteer:.4}).start('time-attack'),3.1);advance(m,2,{steer:1});assert(m.player.steer<=.4&&m.player.steer>.39);advance(m,2,{steer:-1});assert(m.player.steer>=-.4&&m.player.steer<-.39);
});
test('boost is faster and energy remains in bounds',()=>{const a=ready('time-attack'),b=ready('time-attack');advance(a,4,{throttle:1});advance(b,4,{throttle:1,boost:true});assert(b.player.x>a.player.x);assert(b.player.energy>=0&&b.player.energy<=1);});
test('depleted boost does not pulse while held and re-arms after release',()=>{const m=ready('time-attack');advance(m,6,{throttle:1,boost:true});assert(!m.player.boosting);assert(m._boostLocked);advance(m,1,{throttle:1});assert(!m._boostLocked);advance(m,.1,{throttle:1,boost:true});assert(m.player.boosting);});
test('finish cannot be skipped by teleporting past checkpoints',()=>{const m=ready('time-attack');m.player.x=4990;m.player.s=4990;advance(m,.2,{throttle:1});assert.equal(m.state,'racing');assert.equal(m.nextCheckpoint,1);});
test('all sequential checkpoints finish and restart resets',()=>{const m=ready('time-attack',Array.from({length:21},(_,i)=>({x:i*10,z:0})));advance(m,12,{throttle:1});assert.equal(m.state,'finished');assert.equal(m.nextCheckpoint,m.checkpoints.length);assert(m.result.time>0);m.restart();assert.equal(m.state,'countdown');assert.equal(m.timer,0);assert.equal(m.player.damage,0);});
test('time attack has no police and time expires',()=>{const m=ready('time-attack',line.slice(0,5));assert.equal(m.police.length,0);advance(m,45);assert.equal(m.state,'failed');assert.equal(m.result.title,'TIME EXPIRED');});
test('hot pursuit begins wanted and can catch stationary player',()=>{const m=ready('hot-pursuit');assert(m.wanted>0);advance(m,18);assert.equal(m.state,'busted');assert.equal(m.arrestProgress,1);});
test('continuous police motion never teleports to catch player',()=>{const m=ready('hot-pursuit');for(let i=0;i<1200&&m.state==='racing';i++){const old=m.police.map(p=>({x:p.x,z:p.z}));m.update(1/120,{throttle:1});m.police.forEach((p,k)=>assert(Math.hypot(p.x-old[k].x,p.z-old[k].z)<.6));}});
test('fast player can break pursuit fairly',()=>{const m=ready('hot-pursuit');m.rivals=[];advance(m,25,{throttle:1,boost:true});assert(m.escaped);assert.equal(m.wanted,0);assert.equal(m.arrestProgress,0);});
test('coastal patrol detects nearby speeding racer, not countdown',()=>{const m=ready('coast-sprint');m.timer=m._detectionAfter+1;const cop=m.police[0];m.player.x=cop.x-35;m.player.z=cop.z;m.player.s=cop.s-35;m.player.speed=20;advance(m,.1,{throttle:1});assert(m.wanted>0);assert(m.events.some(e=>e.type==='detected'));});
test('invalid controls and randomized inputs stay finite',()=>{const m=ready('time-attack');m.update(NaN,{throttle:NaN});m.update(-1,{});m.update(.01,null);m.update(.01,'invalid');let seed=7;const r=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};for(let i=0;i<12000&&m.state==='racing';i++){m.update(1/120,{throttle:r()*4-2,steer:r()*4-2,brake:r()>.95,boost:r()>.7,flight:r()>.8,flip:r()>.97,lift:r()*2-1});assert(Object.values(m.player).filter(v=>typeof v==='number').every(Number.isFinite));assert(m.player.energy>=0&&m.player.energy<=1);assert(m.player.damage>=0&&m.player.damage<=1);}});
test('swept checkpoint helper detects high-speed crossing',()=>{assert(__testing.segmentNear(-20,0,20,0,0,0,1));assert(!__testing.segmentNear(-20,5,20,5,0,0,1));});
test('head-on relative velocity causes more damage than same-speed contact',()=>{const a=ready(),b=ready();for(const [m,head] of [[a,0],[b,Math.PI]]){m.player.speed=20;const v=m.rivals[0];Object.assign(v,{x:m.player.x+2.5,z:m.player.z,y:m.player.y,speed:20,heading:head});m._vehicleContacts(1/120);}assert(b.player.damage>a.player.damage*5);});
test('static roadside obstacle resolves contact, damages once and allows reversing',()=>{
 const m=advance(new GameModel(line,{obstacles:[{x:35,z:-1.65,radius:.35}]}).start('time-attack'),3.1);
 advance(m,4,{throttle:1});assert(m.player.x<34);assert(m.player.damage>0&&m.player.damage<.5);assert(m.player.speed<3);
 assert(m.events.some(e=>e.type==='obstacle-contact'));const x=m.player.x;advance(m,2,{throttle:-1});assert(m.player.x<x-5);
});
test('exact-center obstacle contact is finite and cooldown prevents instant destruction',()=>{
 const m=advance(new GameModel(line,{obstacles:[{x:20,z:0,radius:4},{x:NaN,z:0,radius:2}]}).start('time-attack'),3.1);
 assert.equal(m.obstacles.length,1);m.player.x=20;m.player.z=0;m.player.speed=0;m._obstacleContacts(1/120);
 assert(Number.isFinite(m.player.x)&&Number.isFinite(m.player.z));assert.equal(m.player.damage,0);m.player.x=20;m.player.z=0;m.player.speed=20;m._obstacleContacts(1/120);
 assert(Number.isFinite(m.player.x)&&Number.isFinite(m.player.z));assert(Math.hypot(m.player.x-20,m.player.z)>0);assert(Math.hypot(m.player.x-20,m.player.z)<2,'deep overlap correction must be bounded, not teleport');assert(m.player.damage<.3);advance(m,.3,{throttle:-1});assert(Math.hypot(m.player.x-20,m.player.z)>5);
});
test('arcade lift clears ground-only roadside colliders',()=>{
 const m=advance(new GameModel(line,{obstacles:[{x:20,z:-1.65,radius:1}]}).start('time-attack'),3.1);
 m.player.x=16;m.player.speed=30;m.player.altitude=2;m.player.y=2.18;advance(m,.4,{throttle:1,flight:true});assert(m.player.x>23);assert.equal(m.player.damage,0);
});
test('flight collides with tall obstacles but clears their tops',()=>{
 const m=ready('time-attack');m.obstacles=[{id:'house',x:20,z:-1.65,radius:2,y:0,height:4.7}];m._obstacleGrid=new Map([['0,-1',m.obstacles]]);
 Object.assign(m.player,{x:18,z:-1.65,y:2.18,altitude:2,speed:20});m._obstacleContacts(1/120);assert(m.player.damage>0,'Flight must not ignore tall walls');
 Object.assign(m.player,{x:18,z:-1.65,y:5.5,altitude:5.32,speed:20});const damage=m.player.damage;m._obstacleContacts(1/120);assert.equal(m.player.x,18);assert.equal(m.player.damage,damage);
});
test('elevated gate crossbars allow ground travel but block intersecting flight',()=>{
 const m=ready('time-attack');m.obstacles=[{id:'beam',x:20,z:-1.65,radius:.3,y:4.8,height:.6}];m._obstacleGrid=new Map([['0,-1',m.obstacles]]);
 Object.assign(m.player,{x:19,z:-1.65,y:.18,altitude:0,speed:20});m._obstacleContacts(1/120);assert.equal(m.player.x,19);assert.equal(m.player.damage,0);
 Object.assign(m.player,{x:19,z:-1.65,y:4.2,altitude:4.02,speed:20});m._obstacleContacts(1/120);assert(m.player.damage>0);
});
test('visual suspension state is finite and reacts to acceleration and steering',()=>{
 const m=ready('time-attack');advance(m,1,{throttle:1});assert(m.player.bodyPitch>0);advance(m,.4,{throttle:1,steer:1});assert(m.player.bodyRoll<0);
 assert(Number.isFinite(m.player.suspension));assert(Math.abs(m.player.bodyPitch)<=.055);assert(Math.abs(m.player.bodyRoll)<=.08);
});
test('high-speed steering is progressive rather than saturated at small inputs',()=>{
 for(const speed of [15,35,55]){const values=[];for(const steer of [.1,.3,1]){const m=ready('time-attack');m.player.speed=speed;advance(m,.3,{steer});values.push(Math.abs(m.player.yawRate));metrics.steering.push({speedMps:speed,input:steer,durationSeconds:.3,yawRateRadPerSec:m.player.yawRate,headingDegrees:m.player.heading*180/Math.PI,lateralMetres:m.player.z+1.65});assert(Math.abs(m.player.steer)<=__testing.steeringEnvelope(m.player.speed,.57)+.002);}
 assert(values[0]<values[1]*.6);assert(values[1]<values[2]*.8);}
});
test('steering rack travel is rate-limited and a short high-speed tap is restrained',()=>{
 const m=ready('time-attack');m.player.speed=35;let rack=0;
 for(let i=0;i<18;i++){m.update(1/120,{steer:1});assert(Math.abs(m.player.steerInput-rack)<=2.7/120+1e-10);rack=m.player.steerInput;}
 assert(Math.abs(m.player.heading)<Math.PI/180);assert(Math.abs(m.player.z+1.65)<.08);
 advance(m,1,{steer:0});assert(Math.abs(m.player.steer)<.00001);assert(Math.abs(m.player.yawRate)<.002);
});
test('turning and braking remain frame-rate invariant at30/60/120Hz',()=>{
 const results=[];for(const hz of [30,60,120]){const m=ready('time-attack');advance(m,3,{throttle:1},hz);advance(m,.5,{throttle:.4,steer:.6},hz);advance(m,1,{brake:true,steer:-.2},hz);results.push(m.player);}
 for(const p of results.slice(1))for(const k of ['x','z','speed','heading','velocityX','velocityZ'])assert(Math.abs(p[k]-results[0][k])<1e-8,k);
});
test('head-on impulses conserve linear momentum and dissipate kinetic energy',()=>{
 for(const speed of [15,35,55]){const m=ready(),a=m.player,b=m.rivals[0];m.rivals=[b];m.police=[];Object.assign(b,{x:a.x+4.35,z:a.z,heading:Math.PI,speed});a.speed=speed;
 const momentum=(a.mass-b.mass)*speed,energy=.5*(a.mass+b.mass)*speed*speed;m._vehicleContacts(1/120);
 const va=m._bodyVelocity(a),vb=m._bodyVelocity(b);assert(Math.abs(a.mass*va.x+b.mass*vb.x-momentum)<1e-6);assert(.5*a.mass*(va.x**2+va.z**2)+.5*b.mass*(vb.x**2+vb.z**2)<=energy*1.001);assert(a.speed<0&&b.speed<0);assert(a.damage>0&&a.damage<=.48);metrics.collisions.push({kind:'head-on',entrySpeedMps:speed,playerExitSpeedMps:a.speed,otherExitSpeedMps:b.speed,damage:a.damage,linearMomentumError:a.mass*va.x+b.mass*vb.x-momentum,energyRetained:(.5*a.mass*(va.x**2+va.z**2)+.5*b.mass*(vb.x**2+vb.z**2))/energy});}
});
test('rear-end impact transfers momentum instead of arbitrarily stopping both cars',()=>{
 for(const speed of [15,35,55]){const m=ready(),a=m.player,b=m.rivals[0],lead=speed*.45;m.rivals=[b];m.police=[];Object.assign(b,{x:a.x+4.35,z:a.z,heading:0,speed:lead});a.speed=speed;const before=a.mass*speed+b.mass*lead;m._vehicleContacts(1/120);assert(a.speed>lead&&a.speed<speed);assert(b.speed>lead);assert(a.damage>=0&&a.damage<=.48);assert(Math.abs(a.mass*a.speed+b.mass*b.speed-before)<1e-6);metrics.collisions.push({kind:'rear-end',entrySpeedMps:speed,leadEntrySpeedMps:lead,playerExitSpeedMps:a.speed,otherExitSpeedMps:b.speed,damage:a.damage});}
});
test('sideswipe retains forward travel and has much less damage than head-on contact',()=>{
 for(const speed of [15,35,55]){const m=ready(),a=m.player,b=m.rivals[0];m.rivals=[b];m.police=[];Object.assign(b,{x:a.x,z:a.z+1.9,heading:0,speed:speed-5});Object.assign(a,{speed,velocityX:speed,velocityZ:3,lateralSpeed:3});m._vehicleContacts(1/120);assert(a.speed>speed*.94);assert(a.velocityZ<3);assert(a.damage<.01);metrics.collisions.push({kind:'sideswipe',entrySpeedMps:speed,playerExitSpeedMps:a.speed,otherExitSpeedMps:b.speed,lateralExitSpeedMps:a.velocityZ,damage:a.damage});}
});
test('resting overlap is corrected without repeated damage or a teleport',()=>{
 const m=ready(),a=m.player,b=m.rivals[0];m.rivals=[b];m.police=[];Object.assign(b,{x:a.x+4.2,z:a.z,heading:0,speed:0});const x=a.x;for(let i=0;i<120;i++){m.timer+=1/120;m._vehicleContacts(1/120);}assert.equal(a.damage,0);assert(Math.abs(a.x-x)<.2);
});
for(const speed of [15,35,55])test(`continuous barrier scrape at${speed}m/s slides instead of pinning`,()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'wall',x:-50,z:3.2,endX:500,endZ:3.2,radius:.15,y:0,height:2}]}).start('time-attack'),3.1);Object.assign(m.player,{speed,z:1.6,heading:.1});const x=m.player.x;advance(m,2,{throttle:.3});assert(m.player.x-x>speed*1.6);assert(m.player.speed>speed*.72);assert(m.player.damage<.03);assert(m.events.filter(e=>e.type==='obstacle-contact').length<=2);
 metrics.wallScrapes.push({entrySpeedMps:speed,durationSeconds:2,retainedSpeedMps:m.player.speed,travelMetres:m.player.x-x,damage:m.player.damage,impactEvents:m.events.filter(e=>e.type==='obstacle-contact').length});const z=m.player.z;advance(m,.6,{throttle:.3,steer:-.5});assert(m.player.z<z);assert(m.player.speed>5);
});
test('thin-post swept collision cannot tunnel at88m/s',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'post',x:30,z:-1.65,radius:.02,y:0,height:2}]}).start('time-attack'),3.1);m.player.speed=88;advance(m,.25);assert(m.player.x<28);assert(m.player.speed<1);assert(m.events.some(e=>e.type==='obstacle-contact'));
});
test('oriented box wall permits reverse escape from a stopped frontal crash',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'box',shape:'box',x:24,z:0,radius:8,halfLength:2,halfWidth:8,heading:0,y:0,height:4}]}).start('time-attack'),3.1);advance(m,3,{throttle:1});const x=m.player.x;assert(x<20);advance(m,2,{throttle:-1});assert(m.player.x<x-6);assert(m.player.speed<-5);
});
test('large rotated OBB collider indexes its distant ends',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'station',shape:'box',x:80,z:0,radius:45,halfLength:44,halfWidth:3,heading:0,y:0,height:4}]}).start('time-attack'),3.1);Object.assign(m.player,{x:35,z:0,heading:0,speed:20});m._obstacleContacts(1/120);assert(m.player.damage>0);assert(m.player.velocityX<=0);
 const o={id:'rotated',shape:'box',x:0,z:0,radius:5,halfLength:4,halfWidth:1,heading:Math.PI/4};const c=m._obstacleContact(o,{x:3,z:3,heading:Math.PI/4});assert(c.depth>0);assert(Number.isFinite(c.nx)&&Number.isFinite(c.nz));
});
test('collision results are invariant at30/60/120Hz',()=>{
 const out=[];for(const hz of [30,60,120]){const m=advance(new GameModel(line,{obstacles:[{id:'wall',x:-50,z:3,endX:300,endZ:3,radius:.15,y:0,height:2}]}).start('time-attack'),3.1);Object.assign(m.player,{speed:35,z:1.6,heading:.1});advance(m,2,{throttle:.3},hz);out.push(m.player);}
 for(const p of out.slice(1))for(const k of ['x','z','speed','heading','damage'])assert(Math.abs(p[k]-out[0][k])<1e-8,k);
});
test('moving dynamic collider uses relative velocity and can be removed',()=>{
 const m=ready('time-attack');m.setDynamicObstacles([{id:'train',shape:'box',x:m.player.x+2,z:m.player.z,radius:4,halfLength:1,halfWidth:3,heading:0,y:0,height:4,velocityX:-10,velocityZ:0}]);m._obstacleContacts(1/120);assert(m.player.velocityX<0);assert(m.player.damage>0);m.setDynamicObstacles([]);assert.equal(m._dynamicObstacles.length,0);
});
test('OBB roof landing resolves vertically and remains supported without sideways ejection',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'roof',shape:'box',x:30,z:0,radius:20,halfLength:20,halfWidth:8,heading:0,y:0,height:5}]}).start('time-attack'),3.1);Object.assign(m.player,{x:30,z:0,y:9,groundY:.18,altitude:8.82,grounded:false,onRoadDeck:false,vz:-3,speed:0,velocityX:0,velocityZ:0,flightCeiling:16});advance(m,3);assert(Math.abs(m.player.y-5)<1e-8);assert.equal(m.player.groundY,5);assert(m.player.grounded);assert(Math.abs(m.player.x-30)<.001);assert(Math.abs(m.player.z)<.001);assert.equal(m.player.damage,0);advance(m,1);assert.equal(m.player.y,5);
});
test('rising flight hits a box underside vertically instead of teleporting sideways',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'overhead',shape:'box',x:30,z:0,radius:20,halfLength:20,halfWidth:8,heading:0,y:5,height:.6}]}).start('time-attack'),3.1);Object.assign(m.player,{x:30,z:0,y:3.7,groundY:.18,altitude:3.52,grounded:false,onRoadDeck:false,vz:5,speed:0,velocityX:0,velocityZ:0,flightCeiling:10});advance(m,.2,{flight:true,lift:1});assert(m.player.y+1.2<=5);assert(Math.abs(m.player.x-30)<.001);assert(Math.abs(m.player.z)<.001);assert(m.events.some(e=>e.text==='OVERHEAD CONTACT'));
});
test('Kerala house proxy uses transformed authored bounds rather than a large circle',()=>{
 const [o]=buildCourseObstacles({prop_instances:[{asset:'KeralaHouse',position:[10,0,20],yaw_rad:Math.PI/2,scale:2}]});assert.equal(o.shape,'box');assert(Math.abs(o.x-11.095962)<1e-6);assert(Math.abs(o.z-19.903702)<1e-6);assert(Math.abs(o.halfLength-9.243702)<1e-6);assert.equal(o.heading,-Math.PI/2);
});
test('legacy straight bridge bead chains become exact continuous capsules only',()=>{
 const beads=Array.from({length:8},(_,i)=>({id:'furniture-Bridge_Rail.001-'+i,x:10+i*.65,z:4,y:.375,height:.15,radius:.12}));
 const modern={id:'furniture-Bridge_Rail-0',x:0,z:-4,endX:20,endZ:-4,y:.375,height:.15,radius:.12};
 const out=buildCourseObstacles({prop_instances:[]},[...beads,modern]);assert.equal(out.length,2);assert(out.includes(modern));const rail=out.find(o=>o.legacyRailSamples);assert.equal(rail.x,beads[0].x);assert.equal(rail.endX,beads.at(-1).x);assert.equal(rail.endZ,4);for(const k of ['radius','y','height'])assert.equal(rail[k],beads[0][k]);
 const curved=beads.map((o,i)=>({...o,z:o.z+(i===3?.2:0)}));assert.equal(buildCourseObstacles({prop_instances:[]},curved).length,8);
 const mismatch=beads.map((o,i)=>({...o,y:o.y+(i===3?.1:0)}));assert.equal(buildCourseObstacles({prop_instances:[]},mismatch).length,8);
 const missing=beads.filter((_,i)=>i!==3);assert.equal(buildCourseObstacles({prop_instances:[]},missing).length,7);
});
const raisedY=s=>{const smooth=t=>t*t*(3-2*t);return .18+9.82*(s<100?0:s<200?smooth((s-100)/100):s<350?1:s<450?1-smooth((s-350)/100):0);};
const graded=Array.from({length:701},(_,i)=>({x:i,z:0,y:raisedY(i)}));
const deckSection={startS:100,endS:450,halfWidth:4.42,railHeight:1.1,railThickness:.3,deckHalfWidth:4.8,deckThickness:.55,deckTopBelowRoad:.10};
const gradedReady=(startS=0)=>advance(new GameModel(graded,{startS,endS:700,elevatedCorridors:[deckSection]}).start('time-attack'),3.1);
test('grade sampling preserves horizontal distances and reports ascent/descent pitch',()=>{
 const m=gradedReady();assert.equal(m.routeLength,700);assert(m.sampleRoute(150).roadPitch>.14);assert(m.sampleRoute(400).roadPitch<-.14);assert.equal(m.sampleRoute(275).y,10);assert.equal(m.projectToRoute(275,2).s,275);
});
test('grounded car climbs and descends flyover without vertical teleportation',()=>{
 const m=gradedReady();let maxY=0,maxStep=0,previous=m.player.y;for(let i=0;i<120*40&&m.state==='racing';i++){m.update(1/120,{throttle:.55});maxY=Math.max(maxY,m.player.y);maxStep=Math.max(maxStep,Math.abs(m.player.y-previous));previous=m.player.y;assert(Math.abs(m.player.y-m.sampleRoute(m.player.s).y)<.015);assert(m.player.grounded);}
 assert.equal(m.state,'finished');assert(maxY>=10);assert(maxStep<.12);assert.equal(m.player.altitude,0);
});
test('uphill gravity modestly reduces acceleration and the brake holds a grade',()=>{
 const up=Array.from({length:101},(_,i)=>({x:i*10,z:0,y:.18+i*.5}));const a=ready('time-attack'),b=ready('time-attack',up);advance(a,2,{throttle:1});advance(b,2,{throttle:1});assert(b.player.speed<a.player.speed);assert(a.player.speed-b.player.speed<2);advance(b,3,{brake:true});assert(Math.abs(b.player.speed)<.001);
});
test('AI and recovery use elevated surface and road pitch',()=>{
 const m=advance(new GameModel(graded,{startS:130,endS:700,elevatedCorridors:[deckSection]}).start('coast-sprint'),3.1);advance(m,1,{throttle:1});for(const v of [...m.rivals,...m.police]){assert(Math.abs(v.y-(m.terrainGrid&&(v.s<0||v.s>m.routeLength)?m.sampleTerrain(v.x,v.z).y:m.sampleRoute(v.s).y))<1e-8);assert(Math.abs(v.roadPitch-m.sampleRoute(v.s).roadPitch)<1e-8);}
 m.nextCheckpoint=m.checkpoints.findIndex(q=>q.s>260);m.player.y=0;assert(m.recover());assert(m.player.y>8);assert.equal(m.player.groundY,m.player.y);assert(m.player.grounded);assert.equal(m.player.altitude,0);
});
test('a side impact cannot push AI through the elevated physical rail',()=>{
 const m=advance(new GameModel(graded,{startS:220,endS:700,elevatedCorridors:[deckSection]}).start('hot-pursuit'),3.1),v=m.police[0];Object.assign(v,{x:270,z:2.4,s:270,lane:2.4,targetLane:2.4,heading:0,speed:10,y:10});Object.assign(m.player,{x:270,z:-.1,y:10,heading:Math.PI/2,speed:30,velocityX:0,velocityZ:30});const contact=m._carContact(v);assert(contact);m._resolveContact(v,contact,v.id);let outer=0;for(let i=0;i<120;i++){m._placeAI(v,1/120);outer=Math.max(outer,Math.abs(v.lane)+.98+1.25*Math.abs(Math.sin(v.heading)));}assert(outer<=4.42-.15);assert(v.lateralVelocity<.01);
});
test('ground flyover edge blocks departure but a lifted car falls toward flatland',()=>{
 const m=gradedReady(240);Object.assign(m.player,{z:3.15,speed:15,heading:Math.PI/2,velocityX:0,velocityZ:15});advance(m,.5,{throttle:.2});assert(Math.abs(m.player.z)<4.42);assert(m.player.y>9.9);
 Object.assign(m.player,{x:260,z:5.4,y:12,altitude:2,grounded:false,onRoadDeck:false,vz:0,speed:0,velocityX:0,velocityZ:0,flightCeiling:17.5,energy:1});const oldY=m.player.y;m.update(1/120,{});assert(m.player.y>oldY-.01&&m.player.y<=oldY);assert.equal(m.player.groundY,-.04);advance(m,4,{});assert(Math.abs(m.player.y+.04)<1e-8);assert(m.player.grounded);assert.equal(m.player.groundPitch,0);
});
test('underpass does not snap to flyover or pass its checkpoint',()=>{
 const m=gradedReady(180);const gate=m.checkpoints.find(q=>q.s>220&&q.s<350);assert(gate);m.nextCheckpoint=m.checkpoints.indexOf(gate);Object.assign(m.player,{x:gate.x,z:0,y:-.04,s:gate.s,speed:0,altitude:0,groundY:-.04,grounded:true,onRoadDeck:false,velocityX:0,velocityZ:0});const index=m.nextCheckpoint;advance(m,.1);assert.equal(m.nextCheckpoint,index);assert(Math.abs(m.player.y+.04)<1e-8);assert.equal(m.player.groundY,-.04);
});
test('flyover underside blocks rising flight and denies a flip without clearance',()=>{
 const m=gradedReady(240);Object.assign(m.player,{x:260,z:0,y:8,groundY:-.04,altitude:8.04,grounded:false,onRoadDeck:false,vz:5,speed:0,energy:1,flightCeiling:20});advance(m,.2,{flight:true,lift:1});assert(m.player.y+1.2<=9.3501);assert(m.events.some(e=>e.type==='obstacle-contact'));
 Object.assign(m.player,{x:260,z:0,y:7.4,groundY:-.04,altitude:7.44,grounded:false,onRoadDeck:false,vz:0,speed:20});m.update(1/120,{flip:true});assert(!m.player.flipActive);
});
test('ground normal is normalized and independent of car heading on a slope',()=>{
 const m=gradedReady(140);Object.assign(m.player,{heading:Math.PI/2,speed:0});advance(m,.05);const p=m.player,q=m.projectToRoute(p.x,p.z,p.s);assert(Math.abs(Math.hypot(p.groundNormalX,p.groundNormalY,p.groundNormalZ)-1)<1e-10);assert(Math.abs(p.groundNormalX+q.grade*p.groundNormalY)<1e-10);assert(Math.abs(p.roadPitch)<.001);assert(p.groundPitch>.1);assert(Math.abs(p.roadRoll)>.1);
});
test('flip preflight rejects a low roof without moving the car vertically',()=>{
 const m=advance(new GameModel(line,{obstacles:[{id:'ceiling',shape:'box',x:30,z:0,radius:20,halfLength:20,halfWidth:8,heading:0,y:5,height:.6}]}).start('time-attack'),3.1);Object.assign(m.player,{x:30,z:0,y:3.3,groundY:.18,altitude:3.12,grounded:false,onRoadDeck:false,vz:0,speed:20,velocityX:20,velocityZ:0});m.update(1/120,{flip:true});assert(!m.player.flipActive);assert(Math.abs(m.player.y-3.3)<.01);
});
test('police cannot arrest a stopped car from the deck above',()=>{
 const m=advance(new GameModel(graded,{startS:240,endS:700,elevatedCorridors:[deckSection]}).start('hot-pursuit'),3.1);m.rivals=[];Object.assign(m.player,{x:280,z:0,y:-.04,s:280,altitude:0,groundY:-.04,grounded:true,onRoadDeck:false,speed:0});for(const v of m.police){v.s=280;v.speed=0;v.x=280;v.z=0;v.y=10;}advance(m,6);assert.equal(m.state,'racing');assert.equal(m.arrestProgress,0);assert(Math.abs(m.player.y+.04)<1e-8);
});

// V9 terrain and open-drive contracts, independent of the forthcoming authored track.
const gridFor=(fn,{origin=[-100,-100],step=[10,10],count=[81,41]}={})=>({origin,step,count,diagonal:'sw-ne',heights:Array.from({length:count[0]*count[1]},(_,i)=>fn(origin[0]+i%count[0]*step[0],origin[1]+Math.floor(i/count[0])*step[1]))});
const hillGrid=gridFor((x,z)=>20+x*.08+z*.03),hillRoute=Array.from({length:601},(_,i)=>({x:i,z:0,y:20.18+i*.08}));
const hillOptions={terrainGrid:hillGrid,roadSections:[{startS:0,endS:600,halfWidth:3.6,shoulderHalfWidth:4.6,shoulderDrop:.06}]};
test('terrain grid triangle interpolation is exact, not bilinear',()=>{
 const g=__testing.normalizeTerrainGrid({origin:[0,0],step:[2,4],count:[2,2],diagonal:'sw-ne',heights:[0,0,0,10]});
 for(const [x,z,y] of [[1,2,5],[1.5,1,2.5],[.5,3,2.5],[2,4,10]]){const t=__testing.sampleTerrainGrid(g,x,z);assert(Math.abs(t.y-y)<1e-12);assert(t.inside);}
 assert.throws(()=>new GameModel(line,{terrainGrid:{...g,heights:[0]}}));assert.throws(()=>new GameModel(line,{terrainGrid:{...g,diagonal:'opposite'}}));assert(!__testing.sampleTerrainGrid(g,-1,0).inside);
});
test('AI outside heightfield-route endpoints uses real terrain and restores asphalt support on entry',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('hot-pursuit'),v=m.police[0];assert(v.s<0);assert(Math.abs(v.y-m.sampleTerrain(v.x,v.z).y)<1e-10);assert(!v.onRoadDeck&&v.offRoad);
 for(const s of [-.01,0,300,600,600.01,620]){v.s=s;m._placeAI(v,1/120);const outside=s<0||s>m.routeLength,t=m.sampleTerrain(v.x,v.z);assert(Math.abs(v.y-(outside?t.y:m.sampleRoute(s).y))<1e-10);assert.equal(v.onRoadDeck,!outside);assert.equal(v.offRoad,outside);if(outside){const n=Math.hypot(1,t.gradientX,t.gradientZ);assert(Math.abs(v.groundNormalX+t.gradientX/n)<1e-10);assert(Math.abs(v.groundNormalZ+t.gradientZ/n)<1e-10);assert(Math.abs(v.roadPitch-Math.atan(t.gradientX*Math.cos(v.heading)+t.gradientZ*Math.sin(v.heading)))<1e-10);}}
 const legacy=new GameModel(hillRoute).start('hot-pursuit');assert.equal(legacy.police[0].y,legacy.sampleRoute(legacy.police[0].s).y,'legacy no-grid behavior remains unchanged');
});
test('ordinary hill-road elevation never creates a phantom flyover',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('free-drive');assert.equal(m._deckAt(m.sampleRoute(200)),null);
 Object.assign(m.player,{x:200,z:20,y:36.6,s:200,grounded:true,onRoadDeck:false,groundY:36.6,altitude:0,speed:0});advance(m,.05,{brake:true});assert(Math.abs(m.player.groundY-36.6)<1e-5);assert(Math.abs(m.player.y-36.6)<1e-5);assert(m.player.offRoad);assert.equal(m.player.grounded,true);
 const expected=Math.hypot(1,.08,.03);assert(Math.abs(m.player.groundNormalX+.08/expected)<1e-8);assert(Math.abs(m.player.groundNormalZ+.03/expected)<1e-8);assert(Math.abs(m.player.groundNormalY-1/expected)<1e-8);
});
test('offroad hill driving stays on the actual triangle ground, not road height',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('free-drive');Object.assign(m.player,{x:100,z:25,y:28.75,s:100,heading:0,grounded:true,onRoadDeck:false,groundY:28.75,altitude:0,speed:12});let biggest=0;
 for(let i=0;i<240;i++){const y=m.player.y;m.update(1/120,{throttle:.4});biggest=Math.max(biggest,Math.abs(m.player.y-y));const t=m.sampleTerrain(m.player.x,m.player.z);assert(Math.abs(m.player.y-t.y)<1e-8);assert(m.player.grounded);}assert(biggest<.03);assert(m.player.y>28.75);
});
test('hill flight falls onto terrain while high world altitude is not a lift ceiling',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('free-drive');Object.assign(m.player,{x:400,z:30,y:57,groundY:52.9,altitude:4.1,s:400,grounded:false,onRoadDeck:false,speed:0,vz:-2,flightCeiling:65});advance(m,4,{});assert(Math.abs(m.player.y-m.sampleTerrain(m.player.x,m.player.z).y)<.001);assert.equal(m.player.altitude,0);
 m.recover();advance(m,.02,{});const base=m.player.y;advance(m,1,{flight:true});assert(m.player.y>base+.5);assert(m.player.y<base+7.6);assert(m.player.y>50);
});
test('road widths support both divided-highway carriageways but not the median',()=>{
 const road=Array.from({length:101},(_,i)=>({x:i*5,z:0,y:20.18})),grid=gridFor(()=>20),section={startS:0,endS:500,halfWidth:5.25,shoulderHalfWidth:6.5,driveableStrips:[{centerOffset:0,halfWidth:5.25,shoulderHalfWidth:6.5},{centerOffset:14,halfWidth:5.25,shoulderHalfWidth:6.5}]};
 const m=new GameModel(road,{terrainGrid:grid,roadSections:[section],obstacles:[{id:'median',x:0,z:7,endX:500,endZ:7,radius:.45,y:20,height:.8}]}).start('free-drive');
 for(const z of [0,4.8,14,18.8]){Object.assign(m.player,{x:100,z,y:20.18,s:100,grounded:true,onRoadDeck:true,altitude:0,speed:0});advance(m,.02,{brake:true});assert(!m.player.offRoad);assert(Math.abs(m.player.y-20.18)<1e-8);}
 Object.assign(m.player,{x:100,z:5,y:20.18,s:100,heading:Math.PI/2,speed:12,velocityX:0,velocityZ:12});advance(m,.6,{throttle:.2});assert(m.player.z<6);assert(m.player.speed<5);
 for(const v of [...new GameModel(road,{terrainGrid:grid,roadSections:[section]}).start('coast-sprint').rivals])assert(Math.abs(v.lane)<5.25-.98);
});
test('hinted hairpin projection cannot jump onto a nearby later parallel segment',()=>{
 const route=[...Array.from({length:101},(_,i)=>({x:i,z:0,y:0})),...Array.from({length:11},(_,i)=>({x:100+5*Math.sin(i*Math.PI/10),z:5-5*Math.cos(i*Math.PI/10),y:0})),...Array.from({length:101},(_,i)=>({x:100-i,z:10,y:0}))];const m=new GameModel(route);
 const local=m.projectToRoute(40,8,40),global=m.projectToRoute(40,8);assert(Math.abs(local.s-40)<.01);assert(global.s>160);assert(local.distance>global.distance);
});
test('another hairpin branch supplies road support without jumping race progress',()=>{
 const route=[...Array.from({length:101},(_,i)=>({x:i,z:0,y:.18})),{x:105,z:5,y:2.68},...Array.from({length:101},(_,i)=>({x:100-i,z:10,y:5.18}))],grid=gridFor((x,z)=>z*.5);
 const m=new GameModel(route,{terrainGrid:grid,roadSections:[{startS:0,endS:300,halfWidth:3.6,shoulderHalfWidth:4.6}]}).start('free-drive');Object.assign(m.player,{x:40,z:10,y:5.18,s:40,groundY:5.18,grounded:true,onRoadDeck:true,speed:0,heading:Math.PI});advance(m,.02,{brake:true});assert(m.player.s<60);assert(Math.abs(m.player.y-5.18)<1e-8);assert(!m.player.offRoad);
});
test('divided highway race gates cannot be scored from the opposing carriageway',()=>{
 const road=[{x:0,z:0,y:20.18},{x:500,z:0,y:20.18}],m=new GameModel(road,{roadSections:[{startS:0,endS:500,halfWidth:5.25,driveableStrips:[{centerOffset:0,halfWidth:5.25},{centerOffset:14,halfWidth:5.25}]}]}).start('time-attack');advance(m,4,{brake:true});const index=m.nextCheckpoint,g=m.checkpoints[index];Object.assign(m.player,{x:g.x+20,z:8.9,y:g.y,s:g.s});m._updateRace({x:g.x-20,z:8.9,y:g.y},1/60);assert.equal(m.nextCheckpoint,index,'other carriageway must not count');Object.assign(m.player,{z:4});m._updateRace({x:g.x-20,z:4,y:g.y},1/60);assert.equal(m.nextCheckpoint,index+1,'race carriageway must count');
});
test('Explore starts immediately, has no pursuit or gate terminal, and recovers locally',()=>{
 const m=new GameModel(hillRoute,{...hillOptions,startS:350}).start('free-drive');assert.equal(m.state,'racing');assert.equal(m.countdown,0);assert.equal(m.rivals.length,0);assert.equal(m.police.length,0);assert.equal(m.totalCheckpoints,0);assert.equal(m.timeLimit,Infinity);assert(m.progress>.5);
 Object.assign(m.player,{x:500,z:80,s:500,y:62.4,groundY:62.4,altitude:0,grounded:true,onRoadDeck:false,speed:0});advance(m,5,{brake:true});assert.equal(m.recoveries,0);const timer=m.timer;m.player.damage=.3;assert(m.recover());assert(Math.abs(m.player.s-500)<.01);assert.equal(m.timer,timer);assert.equal(m.penalties,0);assert.equal(m.player.damage,0);assert(Math.abs(m.player.y-60.18)<.01);
 Object.assign(m.player,{x:600,z:0,s:600,y:68.18});advance(m,.05,{brake:true});assert.equal(m.state,'racing');assert.equal(m.progress,1);assert.equal(m.distanceRemaining,0);assert.equal(m.nextCheckpoint,0);assert.equal(m.wanted,0);
});
test('a disabled Explore car receives local roadside recovery instead of ending exploration',()=>{
 const m=new GameModel(hillRoute,{...hillOptions,startS:350}).start('free-drive');m.player.damage=1;advance(m,1/60,{});assert.equal(m.state,'racing');assert.equal(m.result,null);assert.equal(m.player.damage,0);assert.equal(m.recoveries,1);assert.equal(m.penalties,0);assert(m.player.s>350);assert(m.events.some(e=>e.type==='roadside-assist'));assert(m.recover());
});
test('driving past the road endpoint uses real hill ground instead of extending an invisible road',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('free-drive');Object.assign(m.player,{x:650,z:0,s:600,y:72,groundY:72,altitude:0,grounded:true,onRoadDeck:false,speed:0});advance(m,.05,{brake:true});assert(m.player.offRoad);assert(Math.abs(m.player.y-72)<1e-8);assert.equal(m.player.groundY,72);assert.equal(m.progress,1);assert.equal(m.state,'racing');
});
test('Explore permits the terrain margin but recovers after leaving authored world bounds',()=>{
 const m=new GameModel(hillRoute,hillOptions).start('free-drive');Object.assign(m.player,{x:150,z:350,y:41,groundY:41,s:150,altitude:0,grounded:true,onRoadDeck:false,speed:0});advance(m,2,{brake:true});assert.equal(m.recoveries,0);Object.assign(m.player,{z:450});advance(m,2,{brake:true});assert.equal(m.recoveries,1);assert(m.player.z<4);assert.equal(m.penalties,0);
});

const course=JSON.parse(readFileSync(new URL('../public/assets/course_runtime.json',import.meta.url),'utf8'));
const actualRoute=course.route_points.map(p=>({x:p[0],y:p[1],z:p[2]}));
const furniture=JSON.parse(readFileSync(new URL('../public/assets/furniture_colliders.json',import.meta.url),'utf8'));
const infrastructureURL=course.collision_file?new URL('../public/assets/'+course.collision_file,import.meta.url):null;
const infrastructure=infrastructureURL&&existsSync(infrastructureURL)?JSON.parse(readFileSync(infrastructureURL,'utf8')):{colliders:[]};
const actualObstacles=buildCourseObstacles(course,[...furniture.colliders,...infrastructure.colliders]);
assert(actualObstacles.length>400,'Actual authored furniture and props included');
metrics.geometry={routePoints:actualRoute.length,minY:Math.min(...actualRoute.map(p=>p.y)),maxY:Math.max(...actualRoute.map(p=>p.y)),elevatedCorridors:(course.elevated_corridors||[]).length,infrastructureColliders:infrastructure.colliders.length,totalStaticColliders:actualObstacles.length};
metrics.sha256={gameplay:createHash('sha256').update(source).digest('hex'),course:createHash('sha256').update(readFileSync(new URL('../public/assets/course_runtime.json',import.meta.url))).digest('hex'),furniture:createHash('sha256').update(readFileSync(new URL('../public/assets/furniture_colliders.json',import.meta.url))).digest('hex'),infrastructure:infrastructureURL&&existsSync(infrastructureURL)?createHash('sha256').update(readFileSync(infrastructureURL)).digest('hex'):null};
metrics.geometry.newElevatedExportValidated=metrics.geometry.maxY>5&&metrics.geometry.elevatedCorridors>0&&metrics.geometry.infrastructureColliders>0;
testExploreDepartures('coast',course,actualRoute,actualObstacles);
for(const [scenario,startS,endS,base,maxSteer,variant] of [['coast-sprint',2200,3350,38],['hot-pursuit',2200,4350,68],['time-attack',0,4539,38]].flatMap(v=>[[...v,.57,'red'],[...v,.4,'silver']])){
 test('actual smoothed Kappil route is drivable and winnable: '+scenario+' / '+variant,()=>{
  const m=new GameModel(actualRoute,{startS,endS,maxSteer,obstacles:actualObstacles,elevatedCorridors:course.elevated_corridors||[]}).start(scenario);let detected=false,maxOff=0,lane=-1.65,laneGoal=-1.65,laneLock=0,peakY=m.player.y,maxVerticalStep=0,maxPitch=0,maxPlanarStep=0,maxProgressStep=0,maxAIGroundError=0;
  for(let i=0;i<120*280&&['countdown','racing'].includes(m.state);i++){
   const p=m.player,look=Math.max(10,Math.abs(p.speed)*.60),ahead=m.sampleRoute(p.s+look);
   let target=m._curveSpeed(p.s,base);const lead=m.rivals.filter(v=>v.s>p.s&&v.s-p.s<38&&Math.abs(v.lane-laneGoal)<1.95).sort((a,b)=>a.s-b.s)[0];
   if(lead){const other=laneGoal<0?1.65:-1.65;if(m.timer>laneLock&&!m.rivals.some(v=>Math.abs(v.s-p.s)<13&&Math.abs(v.lane-other)<1.95)){laneGoal=other;laneLock=m.timer+3.5;}else target=Math.min(target,Math.max(8,lead.speed-2));}
   lane+=Math.max(-1.1/120,Math.min(1.1/120,laneGoal-lane));
   const traffic=m.rivals.find(v=>v.s>p.s&&v.s-p.s<26&&Math.abs(v.lane-p.lane)<1.95);if(traffic)target=Math.min(target,Math.max(5,traffic.speed+(traffic.s-p.s-11)*.7));
   const err=__testing.angle(Math.atan2(ahead.z+ahead.nz*lane-p.z,ahead.x+ahead.nx*lane-p.x)-p.heading);
   const ratio=Math.atan(2.7*2*Math.sin(err)/look)/__testing.steeringEnvelope(p.speed,maxSteer);
   const steer=Math.sign(ratio)*Math.pow(Math.min(1,Math.abs(ratio)),1/1.35);
   assert(Number.isFinite(steer)&&Math.abs(steer)<=1.000001&&Number.isFinite(target),'test controller inputs must be finite');const previousY=p.y,previousX=p.x,previousZ=p.z,previousS=p.s;m.update(1/120,{throttle:p.speed<target?1:-.2,steer,brake:p.speed>target+3,boost:target>48});maxPlanarStep=Math.max(maxPlanarStep,Math.hypot(p.x-previousX,p.z-previousZ));maxProgressStep=Math.max(maxProgressStep,Math.abs(p.s-previousS));for(const v of [...m.rivals,...m.police]){assert([v.x,v.y,v.z,v.speed,v.heading].every(Number.isFinite));maxAIGroundError=Math.max(maxAIGroundError,Math.abs(v.y-(m.terrainGrid&&(v.s<0||v.s>m.routeLength)?m.sampleTerrain(v.x,v.z).y:m.sampleRoute(v.s).y)));}peakY=Math.max(peakY,p.y);maxVerticalStep=Math.max(maxVerticalStep,Math.abs(p.y-previousY));maxPitch=Math.max(maxPitch,Math.abs(p.groundPitch));
   maxOff=Math.max(maxOff,m.projectToRoute(p.x,p.z,p.s).distance);detected||=m.wanted>0;
  }
  assert.equal(m.state,'finished',`${scenario}: ${m.message}, damage ${m.damage}, progress ${m.progress}`);
  assert(maxPlanarStep<1.5&&maxProgressStep<1.5,'controller-driven run must not teleport at hairpins');assert(maxAIGroundError<.1,'AI must follow the actual road grade');assert(maxOff<3.6,'automated test driver should remain on paved road');assert.equal(m.nextCheckpoint,m.checkpoints.length);assert(maxVerticalStep<.2,'grounded driving must not teleport vertically');if(metrics.geometry.newElevatedExportValidated)assert(peakY>9.9,'driver must actually traverse elevated deck');
  if(scenario==='coast-sprint')assert(detected,'coastal race should trigger police detection');
  if(scenario==='hot-pursuit'){assert(m.escaped);assert.equal(m.wanted,0);}
  if(scenario==='time-attack')assert(!detected);
  metrics.routes.push({scenario,variant,lengthMetres:m.length,state:m.state,timeSeconds:m.timer,damage:m.damage,maxLateralMetres:maxOff,escaped:m.escaped,policeDetected:detected,maxRoadY:Math.max(...actualRoute.map(p=>p.y)),maxPlayerY:peakY,maxVerticalStepMetres:maxVerticalStep,maxGroundPitchRadians:maxPitch,maxPlanarStepMetres:maxPlanarStep,maxProgressStepMetres:maxProgressStep,maxAIGroundErrorMetres:maxAIGroundError,finiteControllerInputs:true});
  console.log(`  ${m.length.toFixed(0)} m / ${m.timer.toFixed(2)} s / damage ${(m.damage*100).toFixed(0)}% / maximum lateral offset ${maxOff.toFixed(2)} m`);
 });
}

for(const [name,startS] of [['Village',0],['Metro',2000],['Canal Garden',2380],['Flyover',2530],['Water Harbor',3050],['Harbour Avenue',3950]])test('Explore Coastal start and recovery are safe: '+name,()=>{
 const m=new GameModel(actualRoute,{startS,obstacles:actualObstacles,elevatedCorridors:course.elevated_corridors||[]}).start('free-drive'),q=m.sampleRoute(m.player.s),x=m.player.x,z=m.player.z;advance(m,.1,{brake:true});assert.equal(m.state,'racing');assert.equal(m.damage,0);assert(Math.hypot(m.player.x-x,m.player.z-z)<.02,'district spawn must not begin inside a static obstacle');assert(Math.abs(m.player.y-q.y)<.02);assert.equal(m.totalCheckpoints,0);
 Object.assign(m.player,{x:q.x+q.nx*12,z:q.z+q.nz*12,y:-.04,groundY:-.04,altitude:0,grounded:true,onRoadDeck:false});const nearest=m.projectToRoute(m.player.x,m.player.z).s;assert(m.recover());assert(Math.abs(m.player.s-nearest)<1e-8);assert(Math.abs(m.player.y-m.sampleRoute(m.player.s).y)<1e-8);assert.equal(m.penalties,0);
});

// Exact second-track acceptance is deliberately pending until final runtime,
// heightfield and physical proxies exist; a planning-only route is not accepted.
const highlandURL=new URL('../public/assets/course_runtime_highlands.json',import.meta.url);
metrics.highlands={status:'pending final export',routes:[],districts:[]};
if(existsSync(highlandURL)){
 const highlands=JSON.parse(readFileSync(highlandURL,'utf8')),assetJSON=name=>JSON.parse(readFileSync(new URL('../public/assets/'+name,import.meta.url),'utf8'));
 const highlandRoute=highlands.route_points.map(p=>({x:p[0],y:p[1],z:p[2]})),heightfield=highlands.terrain_grid||(highlands.terrain_grid_file?assetJSON(highlands.terrain_grid_file):null);
 const proxies=highlands.collision_file?assetJSON(highlands.collision_file).colliders:[],furn=highlands.furniture_file?assetJSON(highlands.furniture_file).colliders:[];
 const highlandObstacles=buildCourseObstacles(highlands,[...proxies,...furn]),highlandOptions={terrainGrid:heightfield,roadSections:highlands.road_sections,elevatedCorridors:highlands.elevated_corridors||[],obstacles:highlandObstacles};
 metrics.highlands={status:'actual runtime loaded',routePoints:highlandRoute.length,staticColliders:highlandObstacles.length,terrainVertices:heightfield?.heights?.length||0,routes:[],districts:[],sha256:{runtime:createHash('sha256').update(readFileSync(highlandURL)).digest('hex'),terrain:createHash('sha256').update(JSON.stringify(heightfield)).digest('hex'),colliders:createHash('sha256').update(JSON.stringify([...proxies,...furn])).digest('hex')}};
 testExploreDepartures('highlands',highlands,highlandRoute,highlandObstacles);
 test('actual Highland pursuit police rest on terrain before the highway starts',()=>{
  const m=new GameModel(highlandRoute,{...highlandOptions,startS:0}).start('hot-pursuit');metrics.highlands.offRouteAISpawns=m.police.map(v=>({id:v.id,s:v.s,y:v.y,terrainY:m.sampleTerrain(v.x,v.z).y}));
  for(const v of m.police){assert(v.s<0);assert.equal(v.y,m.sampleTerrain(v.x,v.z).y);assert.equal(v.groundY,v.y);assert(!v.onRoadDeck);assert(Math.abs(v.y-m.sampleRoute(v.s).y)>.17,'fixture must expose the original18cm extrapolated-asphalt hover');}
  advance(m,3.1,{brake:true});for(const v of m.police)if(v.s<0)assert.equal(v.y,m.sampleTerrain(v.x,v.z).y);
 });
 test('actual Highland grid supports its hill road with no implicit elevated deck',()=>{
  assert(heightfield&&heightfield.heights.length>1000);assert(highlandObstacles.length>20,'physical authored median/buildings/trees required');assert.equal(highlandOptions.elevatedCorridors.length,0);
  const m=new GameModel(highlandRoute,highlandOptions);let maxError=0;
  for(let i=0;i<highlandRoute.length;i+=7){const p=highlandRoute[i],terrain=m.sampleTerrain(p.x,p.z);assert(terrain.inside);maxError=Math.max(maxError,Math.abs(p.y-terrain.y-.18));assert.equal(m._deckAt(m.projectToRoute(p.x,p.z)),null);}
  assert(maxError<.015,'road is fitted to exact triangle terrain +18cm');metrics.highlands.maxRoadTerrainErrorMetres=maxError;
 });
for(const [scenario,startS,endS,base,maxSteer,variant] of Object.entries(highlands.event_slices).filter(([id])=>id!=='free-drive').map(([id,v])=>[id,v.startS,v.endS,id==='hot-pursuit'?68:38]).flatMap(v=>[[...v,.57,'red'],[...v,.4,'silver']])){
 test('actual authored Highland route is drivable and winnable: '+scenario+' / '+variant,()=>{
  const m=new GameModel(highlandRoute,{...highlandOptions,startS,endS,maxSteer}).start(scenario);let detected=false,maxOff=0,lane=-1.65,laneGoal=-1.65,laneLock=0,peakY=m.player.y,maxVerticalStep=0,maxPitch=0,maxPlanarStep=0,maxProgressStep=0,maxAIGroundError=0;
  for(let i=0;i<120*280&&['countdown','racing'].includes(m.state);i++){
   const p=m.player,look=Math.max(10,Math.abs(p.speed)*.60),ahead=m.sampleRoute(p.s+look);
   let target=m._curveSpeed(p.s,base);const lead=m.rivals.filter(v=>v.s>p.s&&v.s-p.s<38&&Math.abs(v.lane-laneGoal)<1.95).sort((a,b)=>a.s-b.s)[0];
   if(lead){const other=laneGoal<0?1.65:-1.65;if(m.timer>laneLock&&!m.rivals.some(v=>Math.abs(v.s-p.s)<13&&Math.abs(v.lane-other)<1.95)){laneGoal=other;laneLock=m.timer+3.5;}else target=Math.min(target,Math.max(8,lead.speed-2));}
   lane+=Math.max(-1.1/120,Math.min(1.1/120,laneGoal-lane));
   const traffic=m.rivals.find(v=>v.s>p.s&&v.s-p.s<26&&Math.abs(v.lane-p.lane)<1.95);if(traffic)target=Math.min(target,Math.max(5,traffic.speed+(traffic.s-p.s-11)*.7));
   const err=__testing.angle(Math.atan2(ahead.z+ahead.nz*lane-p.z,ahead.x+ahead.nx*lane-p.x)-p.heading);
   const ratio=Math.atan(2.7*2*Math.sin(err)/look)/__testing.steeringEnvelope(p.speed,maxSteer);
   const steer=Math.sign(ratio)*Math.pow(Math.min(1,Math.abs(ratio)),1/1.35);
   assert(Number.isFinite(steer)&&Math.abs(steer)<=1.000001&&Number.isFinite(target),'test controller inputs must be finite');const previousY=p.y,previousX=p.x,previousZ=p.z,previousS=p.s;m.update(1/120,{throttle:p.speed<target?1:-.2,steer,brake:p.speed>target+3,boost:target>48});maxPlanarStep=Math.max(maxPlanarStep,Math.hypot(p.x-previousX,p.z-previousZ));maxProgressStep=Math.max(maxProgressStep,Math.abs(p.s-previousS));for(const v of [...m.rivals,...m.police]){assert([v.x,v.y,v.z,v.speed,v.heading].every(Number.isFinite));maxAIGroundError=Math.max(maxAIGroundError,Math.abs(v.y-(m.terrainGrid&&(v.s<0||v.s>m.routeLength)?m.sampleTerrain(v.x,v.z).y:m.sampleRoute(v.s).y)));}peakY=Math.max(peakY,p.y);maxVerticalStep=Math.max(maxVerticalStep,Math.abs(p.y-previousY));maxPitch=Math.max(maxPitch,Math.abs(p.groundPitch));
   maxOff=Math.max(maxOff,m.projectToRoute(p.x,p.z,p.s).distance);detected||=m.wanted>0;
  }
  assert.equal(m.state,'finished',`${scenario}: ${m.message}, damage ${m.damage}, progress ${m.progress}`);
  assert(maxPlanarStep<1.5&&maxProgressStep<1.5,'controller-driven run must not teleport at hairpins');assert(maxAIGroundError<.1,'AI must follow the actual road grade');assert(maxOff<3.6,'automated test driver should remain on paved road');assert.equal(m.nextCheckpoint,m.checkpoints.length);assert(maxVerticalStep<.2,'grounded driving must not teleport vertically');assert(peakY>30,'driver must actually climb the authored tea hills');
  if(scenario==='coast-sprint')assert(detected,'coastal race should trigger police detection');
  if(scenario==='hot-pursuit'){assert(m.escaped);assert.equal(m.wanted,0);}
  if(scenario==='time-attack')assert(!detected);
  metrics.highlands.routes.push({scenario,variant,lengthMetres:m.length,state:m.state,timeSeconds:m.timer,damage:m.damage,maxLateralMetres:maxOff,escaped:m.escaped,policeDetected:detected,maxRoadY:Math.max(...highlandRoute.map(p=>p.y)),maxPlayerY:peakY,maxVerticalStepMetres:maxVerticalStep,maxGroundPitchRadians:maxPitch,maxPlanarStepMetres:maxPlanarStep,maxProgressStepMetres:maxProgressStep,maxAIGroundErrorMetres:maxAIGroundError,finiteControllerInputs:true});
  console.log(`  ${m.length.toFixed(0)} m / ${m.timer.toFixed(2)} s / damage ${(m.damage*100).toFixed(0)}% / maximum lateral offset ${maxOff.toFixed(2)} m`);
 });
}

 for(const district of highlands.districts||[])test('Explore safely enters and recovers in Highland district '+district.name,()=>{
  const m=new GameModel(highlandRoute,{...highlandOptions,startS:district.start_s,endS:undefined}).start('free-drive'),q=m.sampleRoute(m.player.s),initialS=m.player.s;
  advance(m,.1,{brake:true});assert.equal(m.state,'racing');assert.equal(m.rivals.length,0);assert.equal(m.police.length,0);assert.equal(m.damage,0);assert(Math.abs(m.player.y-q.y)<.02);
  const x=q.x+q.nx*15,z=q.z+q.nz*15,terrain=m.sampleTerrain(x,z);Object.assign(m.player,{x,z,y:terrain.y,groundY:terrain.y,altitude:0,grounded:true,onRoadDeck:false,speed:0});const nearest=m.projectToRoute(m.player.x,m.player.z).s;assert(m.recover());assert(Math.abs(m.player.s-nearest)<1e-8);assert(Math.abs(m.player.y-m.sampleRoute(m.player.s).y)<1e-8);assert.equal(m.penalties,0);assert.equal(m.state,'racing');metrics.highlands.districts.push({name:district.name,startS:initialS,recoveredS:m.player.s,y:m.player.y});
 });
 test('actual Highland median separates highway traffic while opposite lanes support exploration',()=>{
  const m=new GameModel(highlandRoute,{...highlandOptions,startS:100}).start('free-drive'),q=m.sampleRoute(100);
  Object.assign(m.player,{x:q.x+q.nx*4.4,z:q.z+q.nz*4.4,s:q.s,y:q.y,heading:q.heading+Math.PI/2,speed:12,velocityX:q.nx*12,velocityZ:q.nz*12});advance(m,.6,{throttle:.2});assert(m.projectToRoute(m.player.x,m.player.z,100).offset<6.5);assert(m.player.speed<5);
  Object.assign(m.player,{x:q.x+q.nx*14,z:q.z+q.nz*14,s:q.s,y:q.y,heading:q.heading,speed:0,velocityX:0,velocityZ:0,altitude:0,grounded:true,onRoadDeck:true});advance(m,.05,{brake:true});assert(!m.player.offRoad);assert(Math.abs(m.player.y-q.y)<.01);
 });
 test('actual Highland offroad altitude and normal match terrain away from the paved route',()=>{
  const m=new GameModel(highlandRoute,{...highlandOptions,startS:1900}).start('free-drive'),q=m.sampleRoute(1950),x=q.x+q.nx*25,z=q.z+q.nz*25,t=m.sampleTerrain(x,z);Object.assign(m.player,{x,z,s:q.s,y:t.y,groundY:t.y,altitude:0,grounded:true,onRoadDeck:false,speed:0});advance(m,.02,{brake:true});const n=Math.hypot(1,t.gradientX,t.gradientZ);assert(m.player.offRoad);assert(Math.abs(m.player.y-t.y)<.001);assert(Math.abs(m.player.groundNormalX+t.gradientX/n)<1e-8);assert(Math.abs(m.player.groundNormalZ+t.gradientZ/n)<1e-8);assert(Math.abs(m.player.y-q.y)>.05,'sample must distinguish terrain from route plane');
 });
 test('actual Highland flight lands on varied hillside terrain, not route height or sea level',()=>{
  let checked=0,maxError=0,maxSlope=0;
  for(const s of [940,1410,1880,2350,2820,3290])for(const offset of [-80,-35,35,80]){
   const m=new GameModel(highlandRoute,highlandOptions).start('free-drive'),q=m.sampleRoute(s),x=q.x+q.nx*offset,z=q.z+q.nz*offset,t=m.sampleTerrain(x,z);
   if(m.projectToRoute(x,z).distance<12||highlandObstacles.some(o=>Math.hypot(o.x-x,o.z-z)<o.radius+4))continue;
   Object.assign(m.player,{x,z,s,y:t.y+4,groundY:t.y,altitude:4,grounded:false,onRoadDeck:false,speed:0,velocityX:0,velocityZ:0,vz:-2,flightCeiling:t.y+12});advance(m,3,{brake:true});const landed=m.sampleTerrain(m.player.x,m.player.z),error=Math.abs(m.player.y-landed.y);
   assert(m.player.grounded&&m.player.altitude===0);assert(error<1e-6);assert([m.player.y,m.player.roadPitch,m.player.roadRoll,m.player.groundNormalX,m.player.groundNormalY,m.player.groundNormalZ].every(Number.isFinite));maxError=Math.max(maxError,error);maxSlope=Math.max(maxSlope,landed.grade);checked++;
  }
  assert(checked>=12,'enough actual clear hillside samples required');metrics.highlands.offroadLandings={samples:checked,maxErrorMetres:maxError,maxGrade:maxSlope};
 });
 metrics.highlands.status='actual exported geometry tested';
}else console.log('PENDING exact Highland runtime/grid/colliders export; plan-only simulations are not final acceptance.');
metrics.passed=count;metrics.failed=failures;writeFileSync(new URL('./physics_metrics.json',import.meta.url),JSON.stringify(metrics,null,2)+'\n');
if(failures)process.exitCode=1;
console.log(`\n${count} gameplay tests passed, ${failures} failed. Scope: pure-JS simulation, not browser/visual QA.`);
