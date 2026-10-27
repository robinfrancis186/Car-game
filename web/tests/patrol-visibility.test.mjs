import assert from 'node:assert/strict';
import {GameModel} from '../src/gameplay.js';
const route=Array.from({length:151},(_,i)=>({x:i*10,y:.18,z:0}));
const wall={id:'solid-roadside-wall',shape:'box',x:105,z:0,y:0,height:3,halfLength:.4,halfWidth:4,radius:4.1,heading:0};
function ready(scenario='coast-sprint',obstacles=[]){
 const m=new GameModel(route,{obstacles}).start(scenario);m.state='racing';m.timer=40;m.rivals=[];
 Object.assign(m.player,{x:100,y:.18,z:0,s:100,speed:20,altitude:0,lane:0});
 m.police=[m.police[0]];Object.assign(m.police[0],{x:110,y:.18,z:0,s:110,speed:0,lane:0});
 m._placeAI=()=>{};return m;
}
let failed=0,passed=0;
function test(name,f){try{f();console.log('PASS '+name);passed++;}catch(e){failed++;console.error('FAIL '+name+': '+e.message);}}
test('unobstructed visible patrol still detects speeding racer',()=>{const m=ready();m._updatePolice(1/120);assert(m.wanted>0);});
test('patrol cannot detect through a solid roadside wall',()=>{const m=ready('coast-sprint',[wall]);m._updatePolice(1/120);assert.equal(m.wanted,0);});
test('hidden patrol cannot detect a racer',()=>{const m=ready();m.police[0].visible=false;m._updatePolice(1/120);assert.equal(m.wanted,0);});
test('shared cover above both cars does not hide an unobstructed ground sightline',()=>{const m=ready('coast-sprint',[{...wall,x:105,y:5,height:1,halfLength:20}]);m._updatePolice(1/120);assert(m.wanted>0);});
test('deck slab between patrol and player blocks detection',()=>{const high=route.map(p=>({...p,y:8})),m=new GameModel(high,{elevatedCorridors:[{startS:0,endS:1500,deckHalfWidth:4.8,deckThickness:.55,deckTopBelowRoad:.1}]}).start('coast-sprint');m.state='racing';m.timer=40;m.rivals=[];m.police=[m.police[0]];Object.assign(m.player,{x:100,z:0,y:8,s:100,speed:20,altitude:0});Object.assign(m.police[0],{x:110,z:0,y:.18,s:110,speed:0});m._placeAI=()=>{};m._updatePolice(1/120);assert.equal(m.wanted,0);});
for(const hz of [30,60,120]){
 test(`solid wall prevents false boxing at ${hz} Hz`,()=>{const m=ready('hot-pursuit',[{...wall,x:103}]);Object.assign(m.player,{speed:0});Object.assign(m.police[0],{x:106,s:106});m.arrestProgress=.5;m._updatePolice(1/hz);assert(m.arrestProgress<.5);});
 test(`visible nearby patrol builds arrest at ${hz} Hz`,()=>{const m=ready('hot-pursuit');m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});m._updatePolice(1/hz);assert(m.arrestProgress>0);});
}
test('hidden patrol cannot build arrest progress',()=>{const m=ready('hot-pursuit');m.player.speed=0;Object.assign(m.police[0],{x:106,s:106,visible:false});m._updatePolice(1/120);assert.equal(m.arrestProgress,0);});

test('occlusion does not cancel an existing chase or grant a distance escape',()=>{const m=ready('hot-pursuit',[wall]);for(let i=0;i<9*120;i++)m._updatePolice(1/120);assert(m.wanted>0);assert(!m.escaped);assert.equal(m.escapeTimer,0);assert(m.police[0].active);});
test('capture resumes after the player leaves cover',()=>{const m=ready('hot-pursuit',[{...wall,x:103}]);m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});for(let i=0;i<120;i++)m._updatePolice(1/120);assert.equal(m.arrestProgress,0);m.player.z=m.police[0].z=5;for(let i=0;i<5*120&&m.state==='racing';i++)m._updatePolice(1/120);assert.equal(m.state,'busted');});
test('low kerb does not act as full-height hiding cover',()=>{const m=ready('hot-pursuit',[{...wall,x:103,height:.25}]);m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});m._updatePolice(1/120);assert(m.arrestProgress>0);});
test('terrain ridge between cars blocks ground detection',()=>{const m=ready();m.terrainGrid={origin:[100,-5],step:[5,5],count:[3,3],heights:[0,3,0,0,3,0,0,3,0]};m._updatePolice(1/120);assert.equal(m.wanted,0);});
test('cars on separate levels cannot start an arrest',()=>{const m=ready('hot-pursuit');m.player.speed=0;Object.assign(m.police[0],{x:106,s:106,y:4});m._updatePolice(1/120);assert.equal(m.arrestProgress,0);});
test('overhead deck above both ground cars does not prevent arrest',()=>{const m=ready('hot-pursuit',[{...wall,x:103,y:5,height:1,halfLength:20}]);m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});m._updatePolice(1/120);assert(m.arrestProgress>0);});
test('out-of-range, countdown grace and slow clear-state players skip occlusion work',()=>{for(const kind of ['far','grace','slow']){const m=ready();if(kind==='far')m.police[0].x=1000;if(kind==='grace')m.timer=0;if(kind==='slow')m.player.speed=0;let calls=0;m._airLineOfSight=()=>{calls++;return true;};m._updatePolice(1/120);assert.equal(calls,0,kind);assert.equal(m.wanted,0);}});
test('paused model performs no patrol sight checks',()=>{const m=ready('hot-pursuit');let calls=0;m._airLineOfSight=()=>{calls++;return true;};m.setPaused(true);m.update(1/30,{throttle:1});assert.equal(calls,0);});
test('occluded patrol does not suppress a genuine stuck recovery warning',()=>{const m=ready('hot-pursuit',[{...wall,x:103}]);m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});m._lastSolidContactAt=m.timer;m._stuckAnchor={x:100,z:0,time:35};m._updateAutoRecovery(1/120,{throttle:1,brake:false});assert.equal(m.recoveryWarning?.reason,'stuck');});
test('visible patrol still prevents recovery from bypassing capture',()=>{const m=ready('hot-pursuit');m.player.speed=0;Object.assign(m.police[0],{x:106,s:106});m._lastSolidContactAt=m.timer;m._stuckAnchor={x:100,z:0,time:35};m._updateAutoRecovery(1/120,{throttle:1,brake:false});assert.equal(m.recoveryWarning,null);});

console.log(JSON.stringify({passed,failed}));process.exitCode=failed?1:0;
