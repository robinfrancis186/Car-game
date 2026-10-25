import assert from 'node:assert/strict';
import {TRACKS,SURFACE_TEST_TRACK,trackFromSearch,eventSlice,routeLength,worldPhysicsOptions} from '../src/tracks.js';
assert.equal(trackFromSearch('').id,'coast');assert.equal(trackFromSearch('?track=highlands').file,'course_runtime_highlands.json');assert.equal(trackFromSearch('?track=bogus').id,'coast');for(const key of ['constructor','toString','__proto__'])assert.equal(trackFromSearch('?track='+key).id,'coast');
const route=[{x:0,y:0,z:0},{x:30,y:20,z:40}];assert.equal(routeLength(route),50,'Course distance remains horizontal, like model s');
let e=eventSlice(TRACKS.coast,{},'coast-sprint',4539.75);assert.equal(e.startS,2200);assert.equal(e.endS,3350);assert.equal(e.distance,'1.15 KM');
e=eventSlice(TRACKS.highlands,{},'coast-sprint',3700);assert.equal(e.startS,0);assert.equal(e.endS,3700);
e=eventSlice(TRACKS.highlands,{event_slices:{'coast-sprint':{startS:800,endS:3000}}},'coast-sprint',3700);assert.equal(e.distance,'2.20 KM');
e=eventSlice(TRACKS.coast,{},'free-drive',4539,3050);assert.equal(e.startS,3050);assert.equal(e.endS,4539);assert.equal(e.distance,'OPEN COURSE');
e=eventSlice(TRACKS.highlands,{},'free-drive',3700,9999);assert.equal(e.startS,3670);
const grid={origin:[0,0],step:[1,1],count:[2,2],heights:[0,1,2,3]};const opts=worldPhysicsOptions({terrain_grid:grid,road_sections:[{startS:0,endS:100,halfWidth:5.25}],terrain_y:8});assert.equal(opts.terrainGrid,grid);assert.equal(opts.terrainY,8);assert.equal(opts.roadSections.length,1);assert.deepEqual(opts.elevatedCorridors,[]);
console.log('PASS track catalogue, URL fallback, event ranges, district starts, horizontal distance and world/physics metadata forwarding.');

assert.deepEqual(Object.keys(TRACKS),['coast','highlands'],'Optional solo proof never enters normal race catalogue');assert.equal(trackFromSearch('?track=surface-test'),SURFACE_TEST_TRACK);const proof=eventSlice(SURFACE_TEST_TRACK,{},'coast-sprint',900,50);assert.equal(proof.startS,50);assert.equal(proof.risk,'NO RACE / NO COIN REWARDS');console.log('PASS explicit optional surface URL and no normal catalogue expansion');
