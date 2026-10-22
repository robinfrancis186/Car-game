import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import WebSocket from 'ws';
import {createService} from '../server/service.mjs';
import {bucket,ingress,renderOptions} from '../server/ingress.mjs';
const origin='https://kerala-alpha-fixture.onrender.com',host=new URL(origin).host;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function request(port,path,headers={}){return new Promise((resolve,reject)=>{const req=http.get({hostname:'127.0.0.1',port,path,headers:{host,...headers}},res=>{let body='';res.on('data',b=>body+=b);res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,body}));});req.on('error',reject);});}
async function peer(port,headers={host,origin}){const ws=new WebSocket(`ws://127.0.0.1:${port}/room`,{headers}),messages=[];ws.on('message',b=>messages.push(JSON.parse(b)));await new Promise((r,j)=>{ws.once('open',r);ws.once('error',j);});return {ws,messages,send:m=>ws.send(JSON.stringify(m)),async wait(fn){for(let i=0;i<300;i++){const m=messages.find(fn);if(m)return m;await delay(10);}throw new Error('Expected message not received');}};}
const create=(app,name)=>({type:'create',name,protocolVersion:app.manifest.protocolVersion,physicsVersion:app.manifest.physicsVersion,trackHash:app.manifest.trackHash});
test('public startup fails closed; Render owns port and exact HTTPS hostname',()=>{
 assert.deepEqual(renderOptions({}),{port:8787});
 assert.throws(()=>renderOptions({PUBLIC_ALPHA:'true',PORT:'10000'}),/Render-provided/);
 assert.throws(()=>renderOptions({PUBLIC_ALPHA:'true',RENDER:'true',PORT:'10000',RENDER_EXTERNAL_HOSTNAME:'evil.example'}),/Render-provided/);
 assert.throws(()=>renderOptions({PUBLIC_ALPHA:'true',RENDER:'true',PORT:'18012',RENDER_EXTERNAL_HOSTNAME:host}),/Render-provided/);
 assert.deepEqual(renderOptions({PUBLIC_ALPHA:'true',RENDER:'true',PORT:'10000',RENDER_EXTERNAL_HOSTNAME:host}),{port:10000,publicOrigin:origin});
 for(const value of ['http://example.com','https://example.com/path','https://a:b@example.com','https://example.com/','https://example.com:8443'])assert.throws(()=>ingress({publicOrigin:value}));
 const policy=ingress({publicOrigin:origin});assert.equal(policy.host,'0.0.0.0');assert.equal(policy.maxRooms,1);assert.equal(policy.maxClients,6);
 assert.equal(policy.validOrigin(undefined),false);assert.equal(policy.validOrigin('null'),false);assert.equal(policy.validOrigin(origin),true);
});
test('token buckets bound repeated requests and recover without growing an address map',()=>{
 let now=0;const consume=bucket(2,1,()=>now);assert(consume());assert(consume());assert(!consume());now=999;assert(!consume());now=1000;assert(consume());assert(!consume());now=10_000;assert(consume());assert(consume());assert(!consume());
});
test('public ingress: exact host/origin, one two-seat room, strict inputs, private health, graceful restart',async()=>{
 const app=await createService({publicOrigin:origin,countdownTicks:12}),peers=[];
 try{
  const health=await request(app.port,'/health');assert.equal(health.status,200);assert.deepEqual(JSON.parse(health.body),{status:'experimental-alpha',capacity:2,persistent:false});
  assert.equal(health.headers['strict-transport-security'],'max-age=31536000');assert.equal(health.headers['referrer-policy'],'no-referrer');
  assert.equal((await request(app.port,'/health',{host:'evil.example'})).status,403);
  for(const path of ['/server/service.mjs','/.env','/?token=secret','/room?token=secret'])assert.equal((await request(app.port,path)).status,404);
  for(const headers of [{host},{host,origin:'null'},{host,origin:'https://evil.example'},{host:'evil.example',origin}])await assert.rejects(()=>peer(app.port,headers),/403/);
  const a=await peer(app.port),b=await peer(app.port),c=await peer(app.port);peers.push(a,b,c);
  a.send({...create(app,'Driver A'),coins:1000});await a.wait(m=>m.code==='INVALID_JOIN');a.send(create(app,'Driver A'));const joined=await a.wait(m=>m.type==='joined');
  b.send(create(app,'Driver B'));await b.wait(m=>m.code==='CAPACITY');b.send({...create(app,'Driver B'),type:'join',roomCode:joined.roomCode});await b.wait(m=>m.type==='joined');
  c.send({...create(app,'Driver C'),type:'join',roomCode:joined.roomCode});await c.wait(m=>m.code==='ROOM_FULL');c.send({...create(app,'Driver C'),type:'join',roomCode:{bad:'code'}});await c.wait(m=>m.code==='INVALID_JOIN');
  a.send({type:'ready',loaded:true});b.send({type:'ready',loaded:true});await a.wait(m=>m.type==='snapshot'&&m.players.every(p=>p.ready));a.send({type:'start'});
  const sa=await a.wait(m=>m.type==='snapshot'&&m.status==='racing'),sb=await b.wait(m=>m.type==='snapshot'&&m.status==='racing');assert.equal(sa.startTick,sb.startTick);assert.equal(sa.epoch,sb.epoch);
  const closeCodes=peers.map(p=>new Promise(r=>p.ws.once('close',r)));await app.close();assert.deepEqual(await Promise.all(closeCodes),[1012,1012,1012]);assert.equal(app.rooms.size,0);
 }finally{for(const p of peers)p.ws.terminate();await app.close();}
});
test('public websocket connection quota, malformed-message limit and HTTP rate cap',async()=>{
 const app=await createService({publicOrigin:origin}),peers=[];
 try{
  for(let i=0;i<6;i++)peers.push(await peer(app.port));await assert.rejects(()=>peer(app.port),/403/);
  const closed=new Promise(r=>peers[0].ws.once('close',r));for(let i=0;i<21;i++)peers[0].ws.send('{');assert.equal(await closed,1008);
  let limited=false;for(let i=0;i<150;i++)if((await request(app.port,'/robots.txt')).status===429){limited=true;break;}assert(limited);
  assert.equal((await request(app.port,'/health')).status,200,'health remains cheap and available under request quota');
 }finally{for(const p of peers)p.ws.terminate();await app.close();}
});

test('control-frame floods cannot bypass budgets or auto-pong without backpressure checks',async()=>{
 const app=await createService({publicOrigin:origin}),peers=[];
 try{
  for(const method of ['ping','pong']){
   const p=await peer(app.port);peers.push(p);let pongCount=0;p.ws.on('pong',()=>pongCount++);
   const closed=new Promise(r=>p.ws.once('close',r));for(let i=0;i<1000;i++)p.ws[method]('probe');
   assert.equal(await closed,1008);assert(pongCount<=8,'server bounds reflected pong count');
  }
 }finally{for(const p of peers)p.ws.terminate();await app.close();}
});

test('waiting host repairs after two disconnects, reconnect and expired-seat removal',async()=>{
 const app=await createService({publicOrigin:origin,reconnectMs:250,countdownTicks:12}),peers=[];
 try{
  const a=await peer(app.port),b=await peer(app.port);peers.push(a,b);a.send(create(app,'A'));const aj=await a.wait(m=>m.type==='joined');
  b.send({...create(app,'B'),type:'join',roomCode:aj.roomCode});await b.wait(m=>m.type==='joined');
  a.ws.terminate();await delay(20);b.ws.terminate();await delay(20);
  const resumed=await peer(app.port);peers.push(resumed);resumed.send({type:'reconnect',roomCode:aj.roomCode,playerId:aj.playerId,token:aj.reconnectToken,protocolVersion:app.manifest.protocolVersion,physicsVersion:app.manifest.physicsVersion,trackHash:app.manifest.trackHash});await resumed.wait(m=>m.type==='joined');
  await delay(300);const c=await peer(app.port);peers.push(c);c.send({...create(app,'C'),type:'join',roomCode:aj.roomCode});await c.wait(m=>m.type==='joined');
  resumed.send({type:'ready',loaded:true});c.send({type:'ready',loaded:true});const state=await resumed.wait(m=>m.type==='snapshot'&&m.players.length===2&&m.players.every(p=>p.ready));assert.equal(state.hostId,aj.playerId);
  resumed.send({type:'start'});await resumed.wait(m=>m.type==='snapshot'&&m.status==='racing');
 }finally{for(const p of peers)p.ws.terminate();await app.close();}
});
