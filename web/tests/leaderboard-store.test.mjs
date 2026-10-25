import assert from 'node:assert/strict';
import {createLeaderboardCandidate,createLeaderboard} from '../src/leaderboard.js';
import {createLeaderboardStore,LEADERBOARD_KEY} from '../src/leaderboard-store.js';
let passed=0;
const test=(name,fn)=>{fn();passed++;console.log('PASS',name);};
const candidate=(runId='run-1')=>createLeaderboardCandidate({runId,trackId:'coast',scenarioId:'time-attack',startS:0,endS:5000,timeSeconds:45.123,state:'finished'});
function memory(initial={}){
 const data=new Map(Object.entries(initial)),reads=[],writes=[],deletes=[];
 return {data,reads,writes,deletes,getItem(k){reads.push(k);return data.get(k)??null;},setItem(k,v){writes.push([k,v]);data.set(k,v);},removeItem(k){deletes.push(k);data.delete(k);}};
}
test('fresh storage reads only own key and never eagerly writes or saves a name',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);assert.equal(s.persistent,true);assert.equal(s.warning,'');assert.deepEqual(s.entries,[]);assert.deepEqual(m.reads,[LEADERBOARD_KEY]);assert.deepEqual(m.writes,[]);assert.deepEqual(m.deletes,[]);
});
test('explicit save persists trimmed name and result exactly then reloads',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m),saved=s.save(' Ada ',candidate());assert(saved.ok);assert(saved.persistent);assert.equal(saved.entry.name,'Ada');assert.equal(saved.rank,1);assert.equal(m.writes.length,1);
 const loaded=createLeaderboardStore(()=>m);assert.deepEqual(loaded.entries,s.entries);assert.equal(loaded.warning,'');assert.equal(m.writes.length,1);
});
test('invalid form input never writes or registers a result',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);assert.equal(s.save('',candidate()).ok,false);assert.equal(s.save('Ada',null).ok,false);assert.deepEqual(s.entries,[]);assert.deepEqual(m.writes,[]);
});
test('duplicate clicks and renamed duplicate save cannot write twice',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);s.save('Ada',candidate());const r=s.save('Bob',candidate());assert.equal(r.duplicate,true);assert.equal(r.entry.name,'Ada');assert.equal(m.writes.length,1);assert.equal(s.entries.length,1);
});
test('entry getter and returned save result cannot mutate internal state',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m),r=s.save('Ada',candidate());r.entry.name='Wrong';const rows=s.entries;rows[0].timeMs=1;rows.push({});assert.equal(s.entries[0].name,'Ada');assert.equal(s.entries[0].timeMs,45123);assert.equal(s.entries.length,1);
});
test('garage story and unknown namespaces are never read written or deleted',()=>{
 const m=memory({'malabar-profile-v12':'wallet-385-silver','malabar-story-v13':'story','other':'secret'}),s=createLeaderboardStore(()=>m);s.save('Ada',candidate());assert(m.reads.every(k=>k===LEADERBOARD_KEY));assert(m.writes.every(([k])=>k===LEADERBOARD_KEY));assert.deepEqual(m.deletes,[]);assert.equal(m.data.get('malabar-profile-v12'),'wallet-385-silver');assert.equal(m.data.get('malabar-story-v13'),'story');assert.equal(m.data.get('other'),'secret');
});
test('malformed and future-version bytes are preserved with session-only save',()=>{
 for(const raw of ['{bad',JSON.stringify({schemaVersion:2,entries:[]}),JSON.stringify({schemaVersion:1,entries:[{}]}),'null']){
  const m=memory({[LEADERBOARD_KEY]:raw}),s=createLeaderboardStore(()=>m);assert.equal(s.persistent,false);assert.match(s.warning,/protected/);const r=s.save('Ada',candidate());assert.equal(r.ok,true);assert.equal(r.persistent,false);assert.equal(s.entries.length,1);assert.equal(m.data.get(LEADERBOARD_KEY),raw);assert.deepEqual(m.writes,[]);
 }
});
test('blocked storage accessor is nonfatal and stays session-only',()=>{
 const s=createLeaderboardStore(()=>{throw new Error('SecurityError');});assert.equal(s.persistent,false);assert.match(s.warning,/session only/);assert(s.save('Ada',candidate()).ok);assert.equal(s.entries.length,1);
});
test('blocked read never attempts a write and still accepts explicit session records',()=>{
 let writes=0;const s=createLeaderboardStore(()=>({getItem(){throw new Error('denied');},setItem(){writes++;}}));assert(s.save('Ada',candidate()).ok);assert.equal(writes,0);assert.equal(s.persistent,false);
});
test('quota failure preserves prior durable bytes and retains new record only in session',()=>{
 const raw=JSON.stringify(createLeaderboard()),m=memory({[LEADERBOARD_KEY]:raw});m.setItem=()=>{throw new Error('QuotaExceededError');};const s=createLeaderboardStore(()=>m),r=s.save('Ada',candidate());assert(r.ok);assert.equal(r.persistent,false);assert.equal(s.entries.length,1);assert.equal(m.data.get(LEADERBOARD_KEY),raw);assert.match(s.warning,/session only/);
});
test('access error after startup preserves prior bytes and stops future writes',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);m.getItem=()=>{throw new Error('blocked');};assert(s.save('Ada',candidate()).ok);assert(s.save('Bob',candidate('run-2')).ok);assert.equal(s.persistent,false);assert.equal(m.writes.length,0);assert.equal(s.entries.length,2);
});
test('stale tab does not overwrite another tab records',()=>{
 const m=memory(),first=createLeaderboardStore(()=>m),stale=createLeaderboardStore(()=>m);first.save('Ada',candidate());const bytes=m.data.get(LEADERBOARD_KEY),r=stale.save('Bob',candidate('run-2'));assert(r.ok);assert.equal(r.persistent,false);assert.match(stale.warning,/another tab/);assert.equal(m.data.get(LEADERBOARD_KEY),bytes);assert.equal(m.writes.length,1);assert.equal(stale.entries[0].name,'Bob');
});
test('readback conflict stops retries without overwriting concurrent bytes',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m),other='another tab write';m.setItem=(key,value)=>{m.writes.push([key,value]);m.data.set(key,other);};const r=s.save('Ada',candidate());assert(r.ok);assert.equal(r.persistent,false);assert.match(s.warning,/another tab/);assert.equal(m.data.get(LEADERBOARD_KEY),other);s.save('Bob',candidate('run-2'));assert.equal(m.writes.length,1);
});
test('deletion by another tab is a conflict rather than an implicit reset',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);s.save('Ada',candidate());m.data.delete(LEADERBOARD_KEY);s.save('Bob',candidate('run-2'));assert.equal(m.data.has(LEADERBOARD_KEY),false);assert.match(s.warning,/another tab/);assert.equal(s.entries.length,2);
});
test('duplicate remains deduped after reload and after storage failure',()=>{
 const m=memory(),s=createLeaderboardStore(()=>m);s.save('Ada',candidate());const loaded=createLeaderboardStore(()=>m);assert.equal(loaded.save('Bob',candidate()).duplicate,true);assert.equal(m.writes.length,1);
 const session=createLeaderboardStore(()=>{throw new Error('blocked');});session.save('Ada',candidate());assert.equal(session.save('Bob',candidate()).duplicate,true);assert.equal(session.entries.length,1);
});
console.log(`Leaderboard storage: ${passed} passed, 0 failed`);
