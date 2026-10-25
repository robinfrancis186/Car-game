import assert from 'node:assert/strict';
import {createLeaderboard,createLeaderboardCandidate,normalizeLeaderboardName,leaderboardCategoryKey,rankLeaderboard,validateLeaderboard,addLeaderboardResult,LEADERBOARD_LIMIT} from '../src/leaderboard.js';
import {GameModel} from '../src/gameplay.js';
let passed=0;
const test=(name,fn)=>{fn();passed++;console.log('PASS',name);};
const input=(overrides={})=>({runId:'race-1',trackId:'coast',scenarioId:'time-attack',startS:0,endS:5000,timeSeconds:71.2345,state:'finished',...overrides});
const candidate=(overrides={})=>createLeaderboardCandidate(input(overrides));
const clone=value=>JSON.parse(JSON.stringify(value));

test('candidate snapshots actual course and rounds result time to milliseconds',()=>{
 const source=input(),c=createLeaderboardCandidate(source);assert.equal(c.timeMs,71235);assert.equal(c.startS,0);assert.equal(c.endS,5000);assert.equal(c.storyChapterId,null);assert(Object.isFrozen(c));source.timeSeconds=1;assert.equal(c.timeMs,71235);assert(!('name' in c));
});
test('Explore, experimental surface, failed and interrupted states never qualify',()=>{
 for(const state of ['racing','countdown','failed','aborted','crashed','menu',undefined])assert.equal(candidate({state}),null);
 assert.equal(candidate({scenarioId:'free-drive'}),null);assert.equal(candidate({experimentalSurface:true}),null);assert.equal(candidate({trackId:'surface-test'}),null);
});
test('invalid times and malformed result inputs are rejected without coercion',()=>{
 for(const timeSeconds of [0,-1,NaN,Infinity,-Infinity,'10',null,86400.01])assert.equal(candidate({timeSeconds}),null);
 for(const value of [null,undefined,false,1,[],{}])assert.equal(createLeaderboardCandidate(value),null);
 assert.equal(candidate({timeSeconds:.00001}).timeMs,1);
});
test('unknown tracks modes and invalid route endpoints are rejected',()=>{
 for(const change of [{trackId:'unknown'},{scenarioId:'unknown'},{startS:-1},{startS:NaN},{startS:'0'},{endS:0},{endS:Infinity},{endS:10000001}])assert.equal(candidate(change),null);
});
test('run IDs require explicit bounded collision-resistant controller identifiers',()=>{
 for(const runId of ['',null,'spaces invalid','../bad','a'.repeat(129)])assert.equal(candidate({runId}),null);
 assert(candidate({runId:'race:2026-10-24_1.2'}));
});
test('Story requires known chapter track and scenario but uses actual route bounds',()=>{
 assert(candidate({storyChapterId:'village-signal',startS:165,endS:1265}));
 assert.equal(candidate({storyChapterId:'missing'}),null);assert.equal(candidate({storyChapterId:'village-signal',trackId:'highlands'}),null);assert.equal(candidate({storyChapterId:'harbor-line'}),null);
 const adjusted=candidate({storyChapterId:'village-signal',startS:165,endS:1200});assert(adjusted);assert.equal(adjusted.endS,1200);
});
test('names are trimmed Unicode NFC and limited by codepoints rather than UTF16 units',()=>{
 assert.equal(normalizeLeaderboardName('  Racer  '),'Racer');assert.equal(normalizeLeaderboardName('Cafe\u0301'),'Café');
 assert.equal(normalizeLeaderboardName('കേരളം'),'കേരളം');assert.equal(normalizeLeaderboardName('😀'.repeat(24)),'😀'.repeat(24));assert.equal(normalizeLeaderboardName('😀'.repeat(25)),null);assert.equal(normalizeLeaderboardName('👩‍🚀'),'👩‍🚀');
});
test('empty nonstring invisible and control character names are rejected',()=>{
 for(const name of ['', '   ',null,{},42,'\tRacer','Racer\n','a\0b','a\u202eb','a\u200bb','\u200d','\ud800','\u0301'])assert.equal(normalizeLeaderboardName(name),null);
});
test('markup-looking names stay inert plain strings',()=>{
 const name='<b>Racer</b>',r=addLeaderboardResult(createLeaderboard(),name,candidate());assert.equal(r.entry.name,name);assert.equal(JSON.parse(JSON.stringify(r.entry)).name,name);
});
test('no record exists before explicit add and adding does not mutate inputs',()=>{
 const board=createLeaderboard(),c=candidate(),result=addLeaderboardResult(board,'  Ada  ',c);assert.equal(board.entries.length,0);assert.equal(result.entry.name,'Ada');assert.equal(result.board.entries.length,1);assert.equal(result.rank,1);assert.equal(result.duplicate,false);assert(!('name' in c));
});
test('invalid names or forged candidate fields cannot add records',()=>{
 const board=createLeaderboard();assert.equal(addLeaderboardResult(board,'',candidate()).reason,'invalid-name');
 for(const value of [null,{...candidate(),categoryKey:'wrong'},{...candidate(),timeMs:0},{...candidate(),extra:true}])assert.equal(addLeaderboardResult(board,'Ada',value).reason,'invalid-result');
 assert.equal(board.entries.length,0);
});
test('repeated clicks never duplicate rename or change the saved run',()=>{
 const first=addLeaderboardResult(createLeaderboard(),'Ada',candidate());const duplicate=addLeaderboardResult(first.board,'Bob',candidate({timeSeconds:5}));assert.equal(duplicate.ok,true);assert.equal(duplicate.duplicate,true);assert.equal(duplicate.reason,'already-saved');assert.equal(duplicate.board.entries.length,1);assert.equal(duplicate.entry.name,'Ada');assert.equal(duplicate.entry.timeMs,71235);
 assert.equal(addLeaderboardResult(first.board,'',candidate()).duplicate,true);
});
test('ties have equal rank with stable lexical run ID order and correct next rank',()=>{
 let board=createLeaderboard();for(const [runId,timeSeconds] of [['z',10],['a',10],['b',12],['c',9]])board=addLeaderboardResult(board,runId,candidate({runId,timeSeconds})).board;
 const ranked=rankLeaderboard(board.entries,candidate());assert.deepEqual(ranked.map(r=>[r.runId,r.rank]),[['c',1],['a',2],['z',2],['b',4]]);ranked[0].name='changed';assert.equal(board.entries.find(r=>r.runId==='c').name,'c');
});
test('track mode exact actual route and Story chapter never share category',()=>{
 const cases=[{}, {trackId:'highlands'}, {scenarioId:'coast-sprint'}, {startS:.000001}, {endS:4999.999999}, {storyChapterId:'village-signal'}];
 const rows=cases.map((value,index)=>({...candidate({...value,runId:'mode-'+index}),name:'Racer'}));assert.equal(new Set(rows.map(r=>r.categoryKey)).size,cases.length);
 for(const row of rows){const ranked=rankLeaderboard(rows,row);assert.equal(ranked.length,1);assert.equal(ranked[0].runId,row.runId);assert.equal(ranked[0].rank,1);assert.equal(leaderboardCategoryKey(row),row.categoryKey);}
 assert(rankLeaderboard(rows).every(row=>row.rank===1),'unfiltered ranking must still rank within categories');
});
test('strict versioned decoder rejects corruption without mutating input',()=>{
 const valid=addLeaderboardResult(createLeaderboard(),'Ada',candidate()).board;assert.deepEqual(validateLeaderboard(valid),valid);
 const invalid=[null,{},[],{...valid,schemaVersion:2},{...valid,extra:true},{...valid,entries:[...valid.entries,...valid.entries]}, {...valid,entries:[{...valid.entries[0],name:' Ada '}]},{...valid,entries:[{...valid.entries[0],categoryKey:'wrong'}]}];
 for(const value of invalid)assert.throws(()=>validateLeaderboard(value));const decoded=validateLeaderboard(valid);decoded.entries[0].name='Bob';assert.equal(valid.entries[0].name,'Ada');
});
test('bounded capacity retains all saved IDs and refuses silent eviction',()=>{
 let board=createLeaderboard();for(let i=0;i<LEADERBOARD_LIMIT;i++)board=addLeaderboardResult(board,'Racer',candidate({runId:'run-'+i})).board;
 const before=clone(board),full=addLeaderboardResult(board,'New',candidate({runId:'run-overflow'}));assert.equal(full.ok,false);assert.equal(full.reason,'capacity');assert.deepEqual(full.board,before);assert.equal(addLeaderboardResult(board,'Again',candidate({runId:'run-0'})).duplicate,true);
});
test('a race finished through actual simulation supplies an eligible immutable candidate',()=>{
 const model=new GameModel(Array.from({length:5},(_,i)=>({x:i*50,z:0,y:.18}))).start('time-attack');
 for(let i=0;i<4000&&model.state!=='finished'&&model.state!=='failed';i++)model.update(1/120,{throttle:1});
 assert.equal(model.state,'finished');assert.equal(model.result.state,'finished');assert(model._allGatesPassed);
 const c=candidate({runId:'simulation-finish',scenarioId:model.result.scenario,startS:model.startS,endS:model.endS,timeSeconds:model.result.time,state:model.state});assert(c);assert.equal(c.timeMs,Math.round(model.result.time*1000));assert.equal(c.endS,200);
});
console.log(`Leaderboard: ${passed} passed, 0 failed`);
