import test from 'node:test';
import assert from 'node:assert/strict';
import WebSocket from 'ws';
import http from 'node:http';
import {createService} from '../server/service.mjs';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function peer(port,options={}){const ws=new WebSocket(`ws://127.0.0.1:${port}/room`,options),messages=[];ws.on('message',b=>messages.push(JSON.parse(b)));await new Promise((r,j)=>{ws.on('open',r);ws.on('error',j);});return {ws,messages,send:x=>ws.send(JSON.stringify(x)),async wait(fn){const end=Date.now()+3000;while(Date.now()<end){const m=messages.find(fn);if(m)return m;await pause(10);}throw Error('Missing expected message: '+JSON.stringify(messages));}};}
const join=(manifest,name='A')=>({type:'create',name,protocolVersion:manifest.protocolVersion,physicsVersion:manifest.physicsVersion,trackHash:manifest.trackHash});
test('transport is loopback-only; origin/host gates and bounded payload/rate/unauthenticated input',async()=>{
 await assert.rejects(()=>createService({host:'0.0.0.0'}),/only binds/);const app=await createService(),peers=[];try{
  const p=await peer(app.port);peers.push(p);p.send({type:'input'});await p.wait(m=>m.code==='JOIN_REQUIRED');
  assert.equal(await new Promise((resolve,reject)=>{const request=http.get({hostname:'127.0.0.1',port:app.port,path:'/health',headers:{host:'evil.example'}},res=>{res.resume();resolve(res.statusCode);});request.on('error',reject);}),403);
  await assert.rejects(()=>peer(app.port,{origin:'https://evil.example'}),/403/);
  const large=await peer(app.port);peers.push(large);const largeClosed=new Promise(r=>large.ws.on('close',code=>r(code)));large.ws.send('a'.repeat(4096));assert.equal(await largeClosed,1009);
  const rate=await peer(app.port);peers.push(rate);const rateClosed=new Promise(r=>rate.ws.on('close',code=>r(code)));for(let i=0;i<100;i++)rate.send({type:'invalid'});assert.equal(await rateClosed,1008);
  p.send({...join(app.manifest),upgrades:{speed:3}});await p.wait(m=>m.code==='INVALID_JOIN');p.send(join(app.manifest));const membership=await p.wait(m=>m.type==='joined');
  const bad=await peer(app.port);peers.push(bad);p.ws.terminate();await pause(30);
  bad.send({type:'reconnect',roomCode:membership.roomCode,playerId:membership.playerId,token:'é'.repeat(32),protocolVersion:app.manifest.protocolVersion,physicsVersion:app.manifest.physicsVersion,trackHash:app.manifest.trackHash});await bad.wait(m=>m.code==='RECONNECT_DENIED');assert.equal((await fetch(`http://127.0.0.1:${app.port}/health`)).status,200);
  assert.equal((await fetch(`http://127.0.0.1:${app.port}/map-data`)).status,200);
 }finally{for(const p of peers)p.ws.terminate();await app.close();}
});
