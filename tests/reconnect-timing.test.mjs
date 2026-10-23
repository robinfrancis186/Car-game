/** Deterministic protocol fixtures plus real scheduling. Never logs reconnect material. */
import test from'node:test';import assert from'node:assert/strict';import{RaceClient}from'../client/client.mjs';import{Socket,fakeFetch,hello,joined,fixture}from'./fixture.mjs';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function connected(t){let now=0;const c=new RaceClient({endpoint:{origin:'http://127.0.0.1:12345'},WebSocket:Socket,fetch:fakeFetch,now:()=>now}),events=[];c.on(e=>events.push(e));t.after(()=>c.close());await c.prepare();c.setLoaded(true);c.create('Timing test');const s=Socket.instances.at(-1);s.emit('message',hello);s.emit('message',joined);s.emit('message',fixture().snapshot);assert(c.connected);return{c,s,events,setNow:n=>now=n};}
test('old connected socket disconnect starts one backoff retry, not watchdog starvation',async t=>{
 const{c,s,events,setNow}=await connected(t);const before=Socket.instances.length;setNow(6000);s.close();await pause(1100);assert.equal(Socket.instances.length-before,1,'600ms retry must not be repeatedly cancelled by250ms watchdog');assert.equal(c.status,'reconnecting');
 const next=Socket.instances.at(-1);next.emit('message',hello);assert.equal(next.sent[0].type,'reconnect');next.emit('message',{...joined,reconnected:true,reconnectToken:'b'.repeat(32)});assert(c.connected);assert.equal(c.playerId,joined.playerId);assert(!JSON.stringify(events).includes('b'.repeat(32)));
});
test('5s handshake timeout retries once after600ms, retaining original20s overall deadline',async t=>{
 const{c,s,events,setNow}=await connected(t);s.close();await pause(650);const stalled=Socket.instances.at(-1),count=Socket.instances.length;assert.notEqual(stalled,s);setNow(6000);await pause(1100);assert.equal(stalled.readyState,3);assert.equal(Socket.instances.length-count,1,'timed-out handshake must leave retry backoff runnable');assert.equal(c.status,'reconnecting');
 setNow(20001);await pause(300);assert.equal(c.status,'error');assert(events.some(e=>e.code==='RECONNECT_EXPIRED'));assert.equal(c.playerId,null);const final=Socket.instances.length;await pause(650);assert.equal(Socket.instances.length,final,'deadline must not be extended by retries');
});
