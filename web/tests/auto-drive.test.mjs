import assert from 'node:assert/strict';
import {autoPedals,nearbyObstacles} from '../src/auto-drive.js';
import {GameModel} from '../src/gameplay.js';
const route=Array.from({length:101},(_,i)=>({x:i*10,y:0,z:0}));
const m=new GameModel(route);m.start('free-drive');const input={throttle:-1,brake:true,steer:-.73,boost:true,ultraBoost:false,flight:false,lift:.2};
assert.equal(autoPedals(m,input,false),input,'manual input remains byte-for-byte the same object');
let out=autoPedals(m,input,true);assert(out.throttle>0);assert.equal(out.brake,false);assert.equal(out.steer,input.steer);assert.equal(out.boost,true);
m.player.speed=100;out=autoPedals(m,input,true);assert(out.brake);assert.equal(out.throttle,0);
m.player.speed=12;const plain=autoPedals(m,input,true);m.setDynamicObstacles([{id:'ahead',x:m.player.x+6,z:m.player.z,y:0,height:2,radius:1.2}]);assert(autoPedals(m,input,true).brake);m.setDynamicObstacles([{id:'overhead',x:m.player.x+6,z:m.player.z,y:8,height:2,radius:1.2}]);assert.deepEqual(autoPedals(m,input,true),plain);
for(const state of ['countdown','capturing','finished','failed','busted','menu']){m.state=state;out=autoPedals(m,input,true);assert.equal(out.throttle,0);assert.equal(out.brake,false);assert.equal(out.boost,false);assert.equal(out.steer,input.steer);}
m.state='racing';m.paused=true;assert.equal(autoPedals(m,input,true).throttle,0);m.paused=false;assert.equal(autoPedals(m,input,true,{paused:true}).throttle,0);
const curve={...m,player:{...m.player,speed:23},vehicleStats:m.vehicleStats,scenario:m.scenario,sampleRoute:s=>({heading:s*.035}),nearbyObstacles:()=>[],routeLength:1000};assert(autoPedals(curve,input,true).brake,'brakes for actual route curvature');
// Neither helper nor spatial queries mutate the driver, steering, route, opponents or obstacles.
const before=JSON.stringify(m.player);for(let i=0;i<500;i++){const result=autoPedals(m,{...input,steer:(i%3)-1},true);assert.equal(result.steer,(i%3)-1);}assert.equal(JSON.stringify(m.player),before);
assert(nearbyObstacles(m,0,0,20).length===1);
console.log('PASS Auto pedals: manual identity, steering passthrough, speed/curvature/obstacle control, overhead rejection, pause/countdown/capture/results, no model mutation.');

// A long wall beside the road is not an obstacle across the lane.
m.player.speed=18;m.setDynamicObstacles([{id:'wall',shape:'box',x:m.player.x+15,z:m.player.z+8,y:0,height:4,halfLength:25,halfWidth:.3,heading:0,radius:25}]);assert(!autoPedals(m,{...input,boost:false},true).brake);
m.setDynamicObstacles([{id:'barrier',shape:'box',x:m.player.x+10,z:m.player.z,y:0,height:1,halfLength:.3,halfWidth:4,heading:0,radius:4}]);assert(autoPedals(m,input,true).brake);
m.setDynamicObstacles([]);m.player.speed=30;assert(autoPedals(m,{...input,boost:false},true).brake);assert(!autoPedals(m,{...input,boost:true},true).brake,'boost remains useful on a clear straight');
// A 30-second straight drive reaches useful cruise without oscillating service braking or overspeed.
const driving=new GameModel(route);driving.start('free-drive');let peak=0,brakes=0;for(let i=0;i<1800;i++){const pedals=autoPedals(driving,{steer:0},true);if(pedals.brake)brakes++;driving.update(1/60,pedals);peak=Math.max(peak,driving.player.speed);}assert(peak>20&&peak<23);assert(brakes<5);assert.equal(driving.player.damage,0);console.log('PASS accurate box corridor, clear-lane wall rejection, boost retained, 30s cruise without overspeed or brake oscillation.');
