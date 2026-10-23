import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {GameModel,buildCourseObstacles} from '../shared/gameplay.js';
import {worldPhysicsOptions} from '../shared/tracks.js';
import {RaceWorld} from '../shared/world.mjs';
import {getManifest} from '../server/data.mjs';
import {EXPECTED} from '../client/manifest-pin.mjs';
import {data,route} from './parity-fixture.mjs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url));
const sha=b=>createHash('sha256').update(b).digest('hex');

test('exact stable V11.1 engine anchors, shared world bytes, stock stats and protocol pins',()=>{
 const anchors={'gameplay.js':'f1464350b943632dffeb321b50632e3524e03f356018c5005392de1fda89620f','garage.js':'4337626adb45efa08238e2f52896269d8e8303baf4aaacf28f499bb25d646386','tracks.js':'ac0a8659be0d96f209a44ad5d93671d57c75a7200d53f4d357de57ba57f49d6f'};
 for(const[f,h]of Object.entries(anchors)){assert.equal(sha(read('shared/'+f)),h);assert.deepEqual(read('game/'+f),read('shared/'+f));}
 for(const f of ['course_runtime.json','furniture_colliders.json','infrastructure_colliders.json','coastal_map_data.json'])assert.deepEqual(read('public/assets/'+f),read('data/'+f));
 const manifest=getManifest();for(const k of ['protocolVersion','physicsVersion','trackHash','rules','raceSlice'])assert.deepEqual(manifest[k],EXPECTED[k]);assert.equal(manifest.protocolVersion,2);assert.equal(sha(Buffer.from(JSON.stringify(data.world.route_points))),EXPECTED.routeHash);
 const w=new RaceWorld(data);assert.equal(w.model.obstacles.length,buildCourseObstacles(data.world,data.furniture.colliders).length+data.infrastructure.colliders.length);assert.equal(w.model.vehicleStats.vehicleId,'red');assert.equal(w.model.vehicleStats.topSpeedMps,68);assert.equal(w.model.maxSteer,.57);assert.deepEqual(w.model.upgrades,{speed:0,acceleration:0,handling:0,boost:0});
});

test('each complete mutable driver context matches its own independent stable V11.1 GameModel',()=>{
 const w=new RaceWorld(data),baselines=new Map();
 for(const id of ['A','B']){
  w.add(id);const b=new GameModel(route,{startS:2200,endS:3350,...worldPhysicsOptions(data.world),obstacles:[...buildCourseObstacles(data.world,data.furniture.colliders),...data.infrastructure.colliders],seed:267,vehicleId:'red',upgrades:{},maxSteer:.57}).start('time-attack');
  b.state='racing';b.countdown=0;b.timeLimit=Infinity;b.timeRemaining=Infinity;b.coins=[];b.coinsCollected=0;b.collectedCoinIds=new Set();b.rivals=[];b.police=[];baselines.set(id,b);
 }
 for(let tick=0;tick<180;tick++){
  const inputs=new Map([['A',{throttle:tick<100?1:-1,steer:Math.sin(tick/25)*.1,boost:tick>30&&tick<40,recover:tick===110}],['B',{throttle:tick%60<40?1:0,steer:-.12,brake:tick%60>=40,recover:tick===80}]]);
  w.step(inputs);
  for(const[id,b]of baselines){const input=inputs.get(id);if(input.recover)b.recover();b.update(1/60,{...input,flight:false,ultraBoost:false,flip:false,lift:0});const state=w.drivers.get(id).state;assert.deepEqual(state,Object.fromEntries(Object.keys(state).map(k=>[k,b[k]])),`full mutable state ${id} tick ${tick}`);}
 }
 const a=w.drivers.get('A').state,b=w.drivers.get('B').state;
 for(const key of ['player','events','coins','collectedCoinIds'])assert.notEqual(a[key],b[key],`independent ${key}`);
 assert.equal(a.coins.length+b.coins.length,0);assert.equal(a.coinsCollected+b.coinsCollected,0);assert.equal(a.rivals.length+b.rivals.length+a.police.length+b.police.length,0);
});

test('joint stock authority reverses from road, shoulder and deep grass across ±15% grades',()=>{
 for(const grade of [-.15,0,.15])for(const z of [0,5.4,20]){
  const synthetic={world:{route_points:[[0,.18,0],[1000,1000*grade+.18,0]],terrain_grid:{origin:[0,-100],step:[100,100],count:[11,3],heights:Array.from({length:33},(_,i)=>i%11*100*grade),diagonal:'sw-ne'},prop_instances:[]},furniture:{colliders:[]},infrastructure:{colliders:[]},water:{schemaVersion:1,rayOriginY:30,triangles:[]}};
  const w=new RaceWorld(synthetic,{startS:0,endS:1000}),d=w.add('A'),y=300*grade+(z?0:.18);
  Object.assign(d.state.player,{x:300,z,y,groundY:y,heading:0,s:300,grounded:true,onRoadDeck:!z,altitude:0,speed:0,velocityX:0,velocityZ:0});
  for(let i=0;i<240;i++)w.step(new Map([['A',{throttle:-1}]]));
  assert(d.state.player.x<298,`${grade}/${z}: reverse must overcome rolling loss`);assert(d.state.player.speed<-.5);assert.equal(d.state.automaticRecoveries,0);assert.equal(d.state.player.damage,0);
 }
});

test('blocked water recovery uses independent server-clock retry and cannot invent a success',()=>{
 const w=new RaceWorld(data),d=w.add('A');let point;
 for(const t of data.water.triangles){const x=(t[0]+t[3]+t[6])/3,z=(t[2]+t[5]+t[8])/3;if(w.model.projectToRoute(x,z).distance>15){point={x,z};break;}}
 assert(point);Object.assign(d.state.player,{...point,y:0,altitude:0,speed:0,velocityX:0,velocityZ:0});
 // Keep physics time frozen to isolate the wrapper's bounded retry clock. Actual
 // blocked-placement/recovery physics is covered by the stable baseline suite.
 let attempts=0;w.model.recover=()=>{attempts++;return false;};w.model.update=()=>{};
 for(let i=0;i<180;i++)w.step(new Map());
 assert.equal(attempts,3);assert.equal(d.state.timer,0);assert.equal(d.state.recoveries,0);assert.equal(d.state.penalties,0);assert(!d.state.events.some(e=>e.type==='water-contact'));
});
