import assert from 'node:assert/strict';
import {raceFeedback,pursuitLabel} from '../src/race-feedback.js';
import {GameModel} from '../src/gameplay.js';
import {RoadAssistController} from '../src/auto-drive.js';
const route=Array.from({length:501},(_,i)=>({x:i*10,y:.18,z:0}));
const m=new GameModel(route).start('hot-pursuit');
assert.match(raceFeedback(m),/W.*SPACE.*AUTO/);assert.match(raceFeedback(m,{touch:true}),/HOLD GO/);assert.match(raceFeedback(m,{auto:true}),/CHOOSE A LINE/);
m.state='racing';assert.equal(raceFeedback(m), '');
m.escapeTimer=3.25;m.pursuit='evading';assert.equal(pursuitLabel(m),'EVADING  4.8 S');assert.match(raceFeedback(m),/4.8 S TO ESCAPE/);
m._allGatesPassed=true;assert.match(raceFeedback(m),/SAFEHOUSE LOCKED/);m.arrestProgress=.8;assert.equal(pursuitLabel(m),'BOXED IN  80%');
assert.match(raceFeedback(m,{auto:true,blocked:true}),/AUTO BRAKING.*CLEAR LINE/);m.state='busted';assert.equal(raceFeedback(m,{auto:true,blocked:true}),'');
// Second-unit tactics are deterministic, bounded input to the original path follower.
for(const hz of [30,60,120]){const g=new GameModel(route).start('hot-pursuit');g.state='racing';Object.assign(g.player,{x:300,s:300,z:0,y:.18,speed:25,lane:0});for(const [t,mode]of [[4,'pursuit'],[10,'pressure'],[18,'regroup'],[28,'pursuit']]){g.timer=t;g._updatePolice(1/hz);assert.equal(g.police[0].mode,'pursuit');assert.equal(g.police[1].mode,mode);assert(Math.abs(g.police[1].targetLane)<=2.4);assert(g.police[1].speed<=43);}g.timer=18;g.player.speed=0;g._updatePolice(1/hz);assert.equal(g.police[1].mode,'pursuit','No regroup immunity when stopped');}
// The braking notice tracks a real physical obstacle, clears on removal/pause/manual.
const a=new RoadAssistController(),g=new GameModel(route,{obstacles:[{id:'wall',shape:'box',x:30,z:0,y:0,height:3,heading:0,halfLength:1,halfWidth:4,radius:5}]}).start('free-drive');
for(let n=0;n<1200;n++)g.update(1/60,a.update(g,{},true,{dt:1/60}));assert(a.blocked);assert(g.player.speed<.1);assert.equal(g.damage,0);g.paused=true;a.update(g,{},true);assert.equal(a.blocked,false);g.paused=false;a.update(g,{},false);assert.equal(a.blocked,false);
console.log('PASS countdown/escape/safehouse/blocked feedback and deterministic second-unit pacing at 30/60/120Hz; stopped capture retained.');
