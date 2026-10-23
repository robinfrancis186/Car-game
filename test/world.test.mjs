import test from 'node:test';
import assert from 'node:assert/strict';
import {RaceWorld} from '../shared/world.mjs';
import {loadData} from '../server/data.mjs';
import {GameModel,buildCourseObstacles} from '../shared/gameplay.js';
import {worldPhysicsOptions} from '../shared/tracks.js';
const data=loadData(),slice={startS:2200,endS:2320};
test('one world, two independent driver contexts preserve stable V11.1 stock integration',()=>{
 const world=new RaceWorld(data,slice);world.add('A');world.add('B');const baseline=new GameModel(data.world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]})),{...slice,...worldPhysicsOptions(data.world),obstacles:[...buildCourseObstacles(data.world,data.furniture.colliders),...data.infrastructure.colliders],seed:267,upgrades:{},maxSteer:.57}).start('time-attack');baseline.state='racing';baseline.countdown=0;baseline.timeLimit=Infinity;baseline.timeRemaining=Infinity;
 for(let i=0;i<90;i++){const input={throttle:1,steer:0,boost:false};world.step(new Map([['A',input],['B',{brake:true}]]));baseline.update(1/60,input);assert.deepEqual(world.drivers.get('A').state.player,baseline.player);}
 assert(world.snapshot('A').s>world.snapshot('B').s);assert.equal(world.snapshot('B').speed,0);assert.equal(world.model.rivals.length,0);assert.equal(world.model.police.length,0);assert.equal(world.model.vehicleStats.topSpeedMps,68);
});
test('recovery preserves checkpoint, adds server penalty and cannot refill power',()=>{
 const world=new RaceWorld(data,slice);const d=world.add('A');d.state.nextCheckpoint=3;d.state.player.energy=.4;const previous=d.state.nextCheckpoint;world.step(new Map([['A',{recover:true}]]));const p=world.snapshot('A');assert.equal(p.nextCheckpoint,previous);assert.equal(p.penalties,5);assert(p.s<world.model.checkpoints[previous].s);assert(p.energy<.41);world.step(new Map([['A',{recover:true}]]));assert.equal(world.snapshot('A').penalties,5);
});
test('authored water recovers low off-road car; raised road support is not water recovery',()=>{
 const world=new RaceWorld(data,slice);const d=world.add('A');let point;
 for(const t of data.water.triangles){const x=(t[0]+t[3]+t[6])/3,z=(t[2]+t[5]+t[8])/3;if(world.model.projectToRoute(x,z).distance>15){point={x,z};break;}}
 assert(point);Object.assign(d.state.player,{...point,y:0,altitude:0,speed:0,velocityX:0,velocityZ:0});for(let i=0;i<14;i++)world.step(new Map());assert(d.state.events.some(e=>e.type==='water-contact'));assert.equal(d.state.penalties,5);assert.equal(d.state.nextCheckpoint,1);
 const high=new RaceWorld(data,{startS:2600,endS:2720});const hd=high.add('A');for(let i=0;i<60;i++)high.step(new Map());assert(hd.state.player.y>.5);assert(!hd.state.events.some(e=>e.type==='water-contact'));
});
