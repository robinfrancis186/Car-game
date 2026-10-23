import test from'node:test';import assert from'node:assert/strict';import{readFile}from'node:fs/promises';import WebSocket from'ws';import{warmRuntime,WARMUP_STEPS}from'../server/warmup.mjs';import{loadData}from'../server/data.mjs';import{RaceWorld}from'../shared/world.mjs';import{createService}from'../server/service.mjs';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
test('bounded startup warmup yields and discards state; fresh live stock cars remain identical',async()=>{
 const data=loadData(),baseline=new RaceWorld(data);baseline.add('live');const before=baseline.snapshot('live');let yielded=false;setImmediate(()=>{yielded=true;});const receipt=await warmRuntime(data);
 assert(yielded);assert.equal(receipt.steps,WARMUP_STEPS);assert.equal(receipt.drivers,2);assert.equal(receipt.event,'runtime-warmup-complete');assert(receipt.wallMs>0&&receipt.cpuMs>0);assert(receipt.wallMs<30000);
 const fresh=new RaceWorld(data);fresh.add('live');assert.equal(fresh.ticks,0);assert.deepEqual(fresh.snapshot('live'),before);assert.equal(fresh.drivers.size,1);assert.equal(fresh.model.coins.length,0);
 const entry=await readFile(new URL('../server/index.mjs',import.meta.url),'utf8');assert(entry.indexOf('await warmRuntime(loadData())')<entry.indexOf('await createService(options)'));
});
test('250ms overload fail-safe still ends both seats honestly; diagnostic is aggregate-only and bounded',async()=>{
 const publicOrigin='https://kerala-runtime-fixture.onrender.com',app=await createService({publicOrigin,countdownTicks:6}),peers=[],logged=[],oldWarn=console.warn;console.warn=s=>logged.push(JSON.parse(s));
 async function peer(){const ws=new WebSocket(`ws://127.0.0.1:${app.port}/room`,{headers:{host:new URL(publicOrigin).host,origin:publicOrigin}}),messages=[];peers.push(ws);ws.on('message',b=>messages.push(JSON.parse(b)));await new Promise((r,j)=>{ws.once('open',r);ws.once('error',j);});return{send:m=>ws.send(JSON.stringify(m)),async until(fn){for(let i=0;i<500;i++){const m=messages.find(fn);if(m)return m;await wait(5);}throw Error('RUNTIME_TEST_TIMEOUT');}};}
 try{
  const a=await peer(),b=await peer(),versions=Object.fromEntries(['protocolVersion','physicsVersion','trackHash'].map(k=>[k,app.manifest[k]]));a.send({type:'create',name:'Timing A',...versions});const join=await a.until(m=>m.type==='joined');b.send({type:'join',name:'Timing B',roomCode:join.roomCode,...versions});await b.until(m=>m.type==='joined');a.send({type:'ready',loaded:true});b.send({type:'ready',loaded:true});await a.until(m=>m.type==='snapshot'&&m.players.length===2&&m.players.every(p=>p.ready));a.send({type:'start'});await a.until(m=>m.type==='snapshot'&&m.status==='racing');
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,290);
  const result=await a.until(m=>m.type==='snapshot'&&m.status==='results');assert(result.results.every(r=>r.status==='dnf'&&r.reason==='server-overload'));assert(result.results.every(r=>r.time===null));
  assert.equal(logged.length,1);assert.equal(logged[0].guardMs,250);assert(logged[0].loopDeltaMs>250);assert.equal(logged[0].activeRaces,1);assert.deepEqual(Object.keys(logged[0]).sort(),['event','loopDeltaMs','backlogMs','lastStepMs','maxStepMs','sampleWindowMs','cpuUserMs','cpuSystemMs','activeRaces','guardMs'].sort());assert(!JSON.stringify(logged).includes(join.roomCode));assert(!JSON.stringify(logged).includes(join.reconnectToken));
  const source=await readFile(new URL('../server/service.mjs',import.meta.url),'utf8');assert(source.includes('now-lastOverloadLog>=60000'));assert(!source.match(/connect-src[^;]+blob:/));assert(!source.match(/connect-src[^;]+data:/));
 }finally{console.warn=oldWarn;for(const ws of peers)ws.terminate();await app.close();}
});
