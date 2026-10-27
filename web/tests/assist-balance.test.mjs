import assert from 'node:assert/strict';
import {GameModel,PURSUIT_REGROUP} from '../src/gameplay.js';
import {RoadAssistController,autoPedals} from '../src/auto-drive.js';
import {raceFeedback,pursuitLabel,regularBoostFeedback} from '../src/race-feedback.js';
const route=Array.from({length:501},(_,i)=>({x:i*10,y:.18,z:0})),make=(mode='free-drive')=>new GameModel(route).start(mode);
for(const hz of [30,60,120]){
 const m=make(),a=new RoadAssistController();m.player.speed=22;m.player.velocityX=22;m.setDynamicObstacles([{id:'moving',x:40,y:.18,z:m.player.z,radius:1.3,height:1.5,speed:30,velocityX:30,velocityZ:0}]);const i=a.update(m,{},true,{dt:1/hz});assert(!i.brake,'Pulling-away traffic is not a parked obstacle');assert(!a.trafficAhead);assert(!autoPedals(m,{throttle:0},true).brake);
 m.setDynamicObstacles([{id:'stopped',shape:'box',x:40,y:.18,z:0,heading:0,halfLength:1,halfWidth:4,radius:5,height:3}]);a.update(m,{},true,{dt:1/hz});assert(a.trafficAhead,'Warn about40m ahead at22m/s');assert(!a.blocked,'Warning precedes the near-stop state');assert.match(raceFeedback(m,{auto:true,trafficAhead:true}),/TRAFFIC AHEAD/);a.update(m,{},false);assert(!a.trafficAhead);
 const hot=make('hot-pursuit');hot.state='racing';hot.rivals[0].finished=true;hot.rivals[0].speed=30;const oldS=hot.rivals[0].s;hot._updateRivals(1/hz);assert(hot.rivals[0].speed>=24&&hot.rivals[0].s>oldS);assert(hot.rivals[0].s-oldS<=30/hz);hot.wanted=0;hot.rivals[0].speed=1;hot._updateRivals(1/hz);assert(hot.rivals[0].speed<1,'Clear-state original finish slowdown retained');
 const sprint=make('coast-sprint');sprint.rivals[0].finished=true;sprint.rivals[0].speed=30;sprint._updateRivals(1/hz);assert.equal(sprint.rivals[0].speed,30-10/hz);
}
const boost=make();boost.player.energy=.005;boost.update(1/60,{throttle:1,boost:true});assert(boost._boostLocked);assert.equal(regularBoostFeedback(boost,{boost:true}),'RELEASE BOOST TO REARM');boost.update(1/60,{throttle:1,boost:false});assert(!boost._boostLocked);assert.match(regularBoostFeedback(boost,{}),/RECHARGING/);boost.paused=true;assert.equal(regularBoostFeedback(boost,{}),'');boost.paused=false;boost.state='capturing';assert.equal(regularBoostFeedback(boost,{}),'');
const boxed=make('hot-pursuit');boxed.state='racing';boxed.arrestProgress=.2;const pose=JSON.stringify(boxed.player),time=boxed.timer;assert(!boxed.recover());assert.equal(JSON.stringify(boxed.player),pose);assert.equal(boxed.timer,time);assert.equal(boxed.arrestProgress,.2);assert.match(boxed.message,/RETURN BLOCKED/);
const recovered=make('hot-pursuit');recovered.state='racing';assert(recovered.recover());assert(Number.isFinite(recovered.pursuitRecoveryS));recovered._placeAI=()=>{};for(const c of recovered.police)Object.assign(c,{x:900,s:900,y:.18,z:0,speed:0});for(let i=0;i<120*9;i++)recovered._updatePolice(1/120);assert(!recovered.escaped);assert.equal(recovered.escapeTimer,0,'Teleport separation cannot manufacture an escape');const rejoin=recovered.pursuitRecoveryS+130;Object.assign(recovered.player,{s:rejoin,x:rejoin,speed:20});for(let i=0;i<120*8+2;i++)recovered._updatePolice(1/120);assert(recovered.escaped);assert.equal(recovered.wanted,0);
const finish=make('hot-pursuit');finish.state='racing';finish._allGatesPassed=true;finish.nextCheckpoint=finish.checkpoints.length;finish.escaped=true;finish.wanted=0;Object.assign(finish.player,{x:100,s:100});finish._updateRace({...finish.player},1/120);assert.equal(finish.state,'racing');assert.match(raceFeedback(finish),/RETURN TO THE SAFEHOUSE/);Object.assign(finish.player,{x:finish.endS-5,s:finish.endS-5});finish._updateRace({...finish.player},1/120);assert.equal(finish.state,'finished');
console.log('PASS relative traffic braking, early warning, safehouse traffic exit, boost rearm feedback, close-patrol recovery rejection, post-recovery escape travel and actual safehouse finish.');

const slope=Array.from({length:101},(_,i)=>({x:i*10,z:0,y:.18+i*.8}));const climbing=new GameModel(slope,{obstacles:[{id:'under-ramp-cap',shape:'box',x:30,z:0,y:1.2,height:.5,halfLength:1,halfWidth:3,heading:0,radius:4}]}).start('free-drive');climbing.player.speed=20;climbing.player.velocityX=20;const climbAssist=new RoadAssistController();assert(!climbAssist.update(climbing,{},true).brake,'Pier below future rising road must not cause phantom braking');climbing.setDynamicObstacles([{id:'real-barrier',shape:'box',x:30,z:0,y:2.5,height:2,halfLength:1,halfWidth:4,heading:0,radius:5}]);assert(climbAssist.update(climbing,{},true).brake,'Real barrier on rising road still requires braking');console.log('PASS future support height rejects under-road structure and preserves real elevated barrier braking.');

// The authored Hot Pursuit opening changes pace, never the contact/capture rules.
assert.deepEqual(PURSUIT_REGROUP,{start:32,end:52,speed:18});
for(const hz of [30,60,120]){
 for(const [time,opening] of [[31.99,false],[32,true],[51.99,true],[52,false]]){
  const g=make('hot-pursuit');g.state='racing';g.timer=time;g._placeAI=()=>{};
  Object.assign(g.player,{x:400,s:400,z:0,y:.18,speed:30});
  for(const c of g.police)Object.assign(c,{x:350,s:350,z:0,y:.18,speed:18});
  const before=g.police[0].s;g._updatePolice(1/hz);
  assert.equal(g.police[0].mode,opening?'regroup':'pursuit');
  assert(opening?g.police[0].speed<=18:g.police[0].speed>18);
  assert(g.police[0].s-before<=43/hz,'Pace changes cannot teleport units');
  assert.equal(pursuitLabel(g).startsWith('REGROUP'),opening);
  if(opening)assert.match(raceFeedback(g),/REGROUPING/);
 }
 const g=make('hot-pursuit');g.state='racing';g.timer=40;g._placeAI=()=>{};
 Object.assign(g.player,{x:100,s:100,z:0,y:.18,speed:0});
 for(const c of g.police)Object.assign(c,{x:98,s:98,z:0,y:.18,speed:0,active:true,visible:true});
 for(let i=0;i<5*hz&&g.state==='racing';i++)g._updatePolice(1/hz);
 assert.equal(g.state,'busted','Stopped capture remains possible during the opening');
 const sprint=make('coast-sprint');sprint.state='racing';sprint.timer=40;sprint._activatePolice();sprint._placeAI=()=>{};Object.assign(sprint.player,{x:400,s:400,speed:30});for(const c of sprint.police)Object.assign(c,{s:350,speed:18});sprint._updatePolice(1/hz);assert(sprint.police[0].speed>18,'Other scenarios retain original pace');
}
console.log('PASS advertised 32–52s Hot Pursuit-only opening, bounded pace, exact boundaries and stopped capture at 30/60/120 Hz.');
