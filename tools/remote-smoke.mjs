/** Two independent AUTOMATED CLI clients. Not human, mobile, GPU or browser acceptance. */
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
const endpoint=new URL(process.argv[2]);
if(endpoint.username||endpoint.password||endpoint.pathname!=='/'||endpoint.search||endpoint.hash||!(endpoint.protocol==='https:'||endpoint.protocol==='http:'&&['127.0.0.1','localhost'].includes(endpoint.hostname)))throw new Error('Provide one exact HTTPS origin, or loopback fixture URL');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const clients=[];
function client(){const child=fork(new URL('../test/client-worker.mjs',import.meta.url),{stdio:['ignore','ignore','pipe','ipc']}),messages=[];child.on('message',m=>messages.push(m));child.stderr.on('data',()=>{});const result={child,messages,send:m=>child.send(m),mark:()=>messages.length,async wait(fn,from=0,ms=15000){const end=Date.now()+ms;while(Date.now()<end){const found=messages.slice(from).find(fn);if(found)return found;if(child.exitCode!==null)throw new Error('Test client exited');await pause(15);}throw new Error('Timed out waiting for expected remote state');}};clients.push(result);return result;}
const startedAt=new Date().toISOString();
try{
 const healthResponse=await fetch(`${endpoint.origin}/health`,{signal:AbortSignal.timeout(90_000)});assert.equal(healthResponse.status,200);const health=await healthResponse.json();
 const manifest=await(await fetch(`${endpoint.origin}/manifest`)).json();assert.equal(manifest.rules.maxPlayers,2);assert.equal(manifest.rules.stock,true);assert.equal(manifest.rules.contact,false);assert.equal(manifest.rules.payouts,false);
 const connect=async()=>{const peer=client();peer.send({type:'connect',url:endpoint.origin});await peer.wait(m=>m.type==='hello');return peer;};
 const a=await connect(),b=await connect();assert.notEqual(a.child.pid,b.child.pid);
 a.send({type:'create',name:'Automated acceptance A'});const aj=await a.wait(m=>m.type==='joined');b.send({type:'join',name:'Automated acceptance B',roomCode:aj.roomCode});const bj=await b.wait(m=>m.type==='joined');
 a.send({type:'send',value:{type:'ready',loaded:true}});b.send({type:'send',value:{type:'ready',loaded:true}});await a.wait(m=>m.type==='snapshot'&&m.players.length===2&&m.players.every(p=>p.ready));a.send({type:'send',value:{type:'start'}});
 const sa=await a.wait(m=>m.type==='snapshot'&&m.status==='racing'),sb=await b.wait(m=>m.type==='snapshot'&&m.status==='racing');assert.equal(sa.startTick,sb.startTick);assert.equal(sa.epoch,sb.epoch);
 a.send({type:'drive',mode:'follow'});b.send({type:'drive',mode:'follow'});
 const moved=await a.wait(m=>m.type==='snapshot'&&m.players.length===2&&m.players.every(p=>p.s>2215),0,15000);
 b.send({type:'drop'});await b.wait(m=>m.type==='socket-closed');await a.wait(m=>m.type==='snapshot'&&m.players.some(p=>p.id===bj.playerId&&!p.connected));
 const reconnected=await connect();reconnected.send({type:'reconnect',roomCode:aj.roomCode,playerId:bj.playerId,token:bj.reconnectToken});const rejoin=await reconnected.wait(m=>m.type==='joined');assert.equal(rejoin.playerId,bj.playerId);assert.notEqual(rejoin.reconnectToken,bj.reconnectToken);assert.equal(rejoin.reconnected,true);reconnected.send({type:'drive',mode:'follow'});
 const ra=await a.wait(m=>m.type==='snapshot'&&m.status==='results',0,200000),rb=await reconnected.wait(m=>m.type==='snapshot'&&m.status==='results');assert.deepEqual(ra.results,rb.results);assert(ra.results.every(p=>p.status==='finished'),'Both drivers must actually finish');
 const receipt={scope:`${endpoint.protocol==='https:'?'Remote HTTPS/WSS':'Local fixture'} automated CLI processes; not human/device/browser/GPU acceptance`,endpoint:endpoint.origin,startedAt,completedAt:new Date().toISOString(),health,clientPids:[a.child.pid,b.child.pid,reconnected.child.pid],protocolVersion:manifest.protocolVersion,physicsVersion:manifest.physicsVersion,trackHash:manifest.trackHash,sharedStartTick:sa.startTick,bothMovedAtElapsed:moved.elapsed,reconnectPreservedSeat:true,reconnectRotatedToken:true,identicalResults:true,results:ra.results};
 await writeFile(new URL('../docs/remote-smoke-receipt.json',import.meta.url),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt,null,2));
}finally{for(const c of clients){if(c.child.connected)c.send({type:'stop'});}await pause(100);for(const c of clients)if(c.child.exitCode===null)c.child.kill('SIGTERM');}
