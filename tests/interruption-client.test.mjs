import test from'node:test';
import assert from'node:assert/strict';
import{readFileSync}from'node:fs';
import{RaceClient}from'../client/client.mjs';
import{OnlineRenderAdapter}from'../client/render-adapter.mjs';
import{NEUTRAL,POSE,validSnapshot}from'../client/validation.mjs';
import{fixture,IDs,joined,hello,Socket,fakeFetch,memoryStorage,route}from'./fixture.mjs';
const initial=()=>fixture().snapshot;
const hold=(s,{count=1,totalMs=300,currentMs=300}={})=>({...structuredClone(s),interruption:{generation:2*count-1,count,phase:'holding',totalMs,currentMs}});
const active=(s,totalMs=s.interruption.totalMs)=>({...structuredClone(s),interruption:{...s.interruption,generation:2*s.interruption.count,phase:'active',totalMs,currentMs:0}});
const results=s=>({...active(s),status:'results',results:s.players.map((p,i)=>({playerId:p.id,name:p.name,status:'dnf',reason:'server-interrupted',time:null,penalties:p.penalties,checkpoints:p.nextCheckpoint-1,rank:null}))});
const rematch=s=>{const n={...initial(),epoch:'22222222-2222-2222-2222-222222222222',status:'waiting',startTick:null,elapsed:0,tick:0};n.players.forEach(p=>{p.ready=false;p.ack=0;});return n;};
async function connected(t,options={}){const client=new RaceClient({endpoint:{origin:'http://127.0.0.1:12345'},WebSocket:Socket,fetch:fakeFetch,now:()=>0,...options});t.after(()=>client.close());await client.prepare();client.setLoaded(true);client.create('Interruption test');const socket=Socket.instances.at(-1);socket.emit('message',hello);socket.emit('message',joined);socket.emit('message',initial());assert(client.connected);assert(client.snapshot);return{client,socket};}

test('interruption metadata is mandatory, exact, finite and semantically bounded',()=>{
 const s=initial();assert(validSnapshot(s));const missing=structuredClone(s);delete missing.interruption;assert.equal(validSnapshot(missing),false);
 for(const patch of[{generation:-1},{generation:.5},{count:1},{phase:'paused'},{phase:'holding'},{totalMs:-1},{totalMs:Infinity},{currentMs:1},{extra:true}])assert.equal(validSnapshot({...s,interruption:{...s.interruption,...patch}}),false,JSON.stringify(patch));
 const held=hold(s);assert(validSnapshot(held));for(const patch of[{currentMs:301},{generation:0,count:0},{phase:'active'},{totalMs:NaN}])assert.equal(validSnapshot({...held,interruption:{...held.interruption,...patch}}),false);
 assert.equal(validSnapshot({...results(held),interruption:held.interruption}),false,'results cannot still claim a resync hold');
});

test('hold clears controls, sends nothing, freezes accepted state, resumes with current generation',async t=>{
 const{client:c,socket:s}=await connected(t),events=[];c.on(e=>events.push(e));assert(c.input({...NEUTRAL,throttle:1,brake:false}));assert.equal(s.sent.at(-1).generation,0);
 const h=hold(c.snapshot);s.emit('message',h);assert.equal(events.filter(e=>e.type==='neutralize').length,1);const seq=c.sequence,sent=s.sent.length;assert.equal(c.input({...NEUTRAL,throttle:1}),false);c.neutralize();assert.equal(c.sequence,seq);assert.equal(s.sent.length,sent);
 const later=hold(h,{currentMs:450,totalMs:450});s.emit('message',later);assert.deepEqual(c.snapshot.players,h.players);assert.equal(c.snapshot.tick,h.tick);assert.equal(c.snapshot.elapsed,h.elapsed);
 for(const patch of[{tick:h.tick+1},{elapsed:h.elapsed+.01},{players:h.players.map((p,i)=>i?p:{...p,x:p.x+1})}]){s.emit('message',{...structuredClone(later),...patch});assert.deepEqual(c.snapshot,later);}
 const before=events.filter(e=>e.type==='neutralize').length;s.emit('message',active(later,800));assert.equal(events.filter(e=>e.type==='neutralize').length,before+1);assert(c.input({...NEUTRAL}));assert.equal(s.sent.at(-1).generation,2);assert.equal(s.sent.at(-1).seq,seq+1);
 const missed=active(hold(c.snapshot,{count:2,totalMs:1600,currentMs:800}));s.emit('message',missed);assert.equal(events.filter(e=>e.type==='neutralize').length,before+2);assert(c.input({...NEUTRAL}));assert.equal(s.sent.at(-1).generation,4);
});

test('regressive generation, totals, current hold and stale phase cannot overwrite latest snapshot',async t=>{
 const{client:c,socket:s}=await connected(t);s.emit('message',hold(c.snapshot,{count:2,totalMs:1400,currentMs:400}));const good=c.snapshot;
 for(const interruption of[{generation:1,count:1,phase:'holding',totalMs:1500,currentMs:500},{...good.interruption,totalMs:1399},{...good.interruption,currentMs:399}]){s.emit('message',{...structuredClone(good),interruption});assert.equal(c.snapshot,good);}
 s.emit('message',active(good,1800));const resumed=c.snapshot;s.emit('message',hold(resumed,{count:2,totalMs:1800,currentMs:800}));assert.equal(c.snapshot,resumed);assert.equal(c.rejectedSnapshots,4);
});

test('resync-required clears controls and suppresses old-generation input until next authoritative state (including same-generation error ordering)',async t=>{
 const{client:c,socket:s}=await connected(t),events=[];c.on(e=>events.push(e));s.emit('message',{type:'error',code:'RESYNC_REQUIRED'});assert(events.some(e=>e.type==='neutralize'));assert(events.some(e=>e.code==='RESYNC_REQUIRED'));assert.equal(c.input({...NEUTRAL}),false);s.emit('message',initial());assert(c.input({...NEUTRAL}),'same-generation snapshot after a delayed stale-input notice must unblock');s.emit('message',{type:'error',code:'RESYNC_REQUIRED'});assert.equal(c.input({...NEUTRAL}),false);s.emit('message',active(hold(c.snapshot),800));assert(c.input({...NEUTRAL}));assert.equal(s.sent.at(-1).generation,2);
});

test('only legitimate rematch resets interruption history and retired race state stays rejected',async t=>{
 const{client:c,socket:s}=await connected(t);s.emit('message',hold(c.snapshot));const held=c.snapshot,n=rematch();s.emit('message',n);assert.equal(c.snapshot,held);
 s.emit('message',results(held));const finished=c.snapshot;const badReset={...n,interruption:{generation:2,count:1,phase:'active',totalMs:300,currentMs:0}};s.emit('message',badReset);assert.equal(c.snapshot,finished);s.emit('message',n);assert.equal(c.snapshot.epoch,n.epoch);assert.equal(c.snapshot.interruption.generation,0);s.emit('message',held);assert.equal(c.snapshot.epoch,n.epoch);
});

test('reconnect joined cannot bypass active-race epoch and interruption validation',async t=>{
 const{client:c,socket:s}=await connected(t);s.emit('message',hold(c.snapshot));s.close();await new Promise(resolve=>setTimeout(resolve,650));const next=Socket.instances.at(-1);next.emit('message',hello);next.emit('message',{...joined,reconnected:true,epoch:rematch().epoch,reconnectToken:'b'.repeat(32)});assert.equal(c.status,'error');assert.equal(c.snapshot,null);
});

test('results reconnect preserves interruption evidence until valid rematch snapshot arrives',async t=>{
 const{client:c,socket:s}=await connected(t);s.emit('message',results(hold(c.snapshot)));const finished=c.snapshot;s.close();await new Promise(resolve=>setTimeout(resolve,650));const next=Socket.instances.at(-1);next.emit('message',hello);next.emit('message',{...joined,reconnected:true,epoch:rematch().epoch,reconnectToken:'b'.repeat(32)});assert(c.connected);assert.equal(c.snapshot,finished);assert.equal(c.epoch,finished.epoch);next.emit('message',rematch());assert.equal(c.snapshot.interruption.generation,0);assert.equal(c.epoch,rematch().epoch);
});

test('render adapter snaps on hold/resume, freezes wheels and both exact authoritative poses without extrapolation',()=>{
 const a=new OnlineRenderAdapter(route),s=initial();s.players.forEach(p=>{p.speed=10;p.velocityX=10;});assert(a.accept(s,IDs[0],0));const latest=structuredClone(s);latest.tick+=6;latest.elapsed+=.1;latest.players.forEach(p=>p.x+=2);assert(a.accept(latest,IDs[0],100));assert(a.frame(150).player.x<latest.players[0].x);
 const h=hold(latest);assert(a.accept(h,IDs[0],160));assert.equal(a.buffer.length,1);const m=a.frame(170),wheels=[m.player.wheelAngle,m.rivals[0].wheelAngle];for(const car of[m.player,...m.rivals])for(const key of POSE)assert.equal(car[key],h.players.find(p=>p.id===car.id)[key],key);
 const frozen=a.frame(1200,.1);assert.deepEqual([frozen.player.wheelAngle,frozen.rivals[0].wheelAngle],wheels);assert.equal(frozen.timer,h.players[0].time);assert.equal(frozen.network.interruption.phase,'holding');assert.equal(frozen.police.length,0);assert.equal(frozen.coins.length,0);assert.equal(frozen.paused,false);assert.equal(frozen.setPaused(true),false);assert.throws(()=>frozen.update(.1,NEUTRAL),/FORBIDDEN/);assert.throws(()=>frozen.recover(),/FORBIDDEN/);
 const drift=hold(h,{totalMs:450,currentMs:450});drift.players[1].z+=1;assert.equal(a.accept(drift,IDs[0],1250),false);const resumed=active(h,800);assert(a.accept(resumed,IDs[0],1300));assert.equal(a.buffer.length,1);assert.equal(a.frame(1300).player.x,resumed.players[0].x);assert.equal(a.accept(h,IDs[0],1310),false);assert.equal(a.accept(s,IDs[0],1400),false);assert.equal(a.accept(rematch(),IDs[0],1500),false);assert(a.accept(results(resumed),IDs[0],1600));assert(a.accept(rematch(),IDs[0],1700));assert.equal(a.accept(h,IDs[0],1800),false);assert.equal(a.frame(1800).network.interruption.count,0);
});

test('interruption UI distinguishes host freeze from player pause and cannot access solo saves',async t=>{
 const storage=memoryStorage(),saved='{"coins":9182,"cars":["seven-car-solo"]}';storage.values.set('kerala-profile-v12',saved);const{client:c,socket:s}=await connected(t,{storage});s.emit('message',hold(c.snapshot));s.emit('message',active(c.snapshot,800));s.emit('message',results(c.snapshot));s.emit('message',rematch());c.leave();assert.equal(storage.values.get('kerala-profile-v12'),saved);assert(storage.writes.every(k=>k.startsWith('kerala-online-session-v2:')));
 const main=readFileSync(new URL('../client/main.mjs',import.meta.url),'utf8'),html=readFileSync(new URL('../public/online.html',import.meta.url),'utf8');assert.match(main,/Server interrupted — both cars and race clock frozen/);assert.match(main,/Server resynced — press controls again/);assert.match(main,/server-confirmed/);assert.match(main,/excluded from race time/);assert.match(main,/holding'\|\|e\.repeat\)return/);assert.match(html,/id="interruption-banner" role="status" aria-live="polite"/);assert.match(html,/No player pause/);assert.doesNotMatch(html,/Online never pauses/);for(const file of['client/main.mjs','client/client.mjs','client/render-adapter.mjs'])assert.doesNotMatch(readFileSync(new URL('../'+file,import.meta.url),'utf8'),/localStorage|saveProfile|loadProfile|awardCoins|buyCar/);
});
