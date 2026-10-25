/** Graphics-loss fail-closed regression: actual controller/gameplay/storage + simulated DOM,
 * renderer and audio. It does NOT exercise a real WebGL context or establish GPU recovery.
 * Three 0.170.0 silently skips render after context loss; controller must stop blind driving.
 */
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {build} from 'esbuild';
import {PROFILE_KEY} from '../src/profile-storage.js';
const base=new URL('..',import.meta.url).pathname.replace(/\/$/,'');
const html=await fs.readFile(base+'/index.html','utf8');
const worlds={};for(const [id,file] of [['coast','course_runtime.json'],['highlands','course_runtime_highlands.json'],['surface-test','course_runtime_surface_test.json']]){const w=JSON.parse(await fs.readFile(base+'/public/assets/'+file));if(w.terrain_grid_file)w.terrain_grid=JSON.parse(await fs.readFile(base+'/public/assets/'+w.terrain_grid_file));worlds[id]=w;}
const fake=`export class CoastRenderer{constructor(_,options){this.onProgress=options.onProgress;this.requestedWorldFile=options.worldFile;this.quality='high';this.world=globalThis.__WORLD__;this.route=this.world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]}));this.scene={fog:{color:{set(){}},density:0}};this.sun={};this.hemisphere={};this.sky={material:{uniforms:{top:{value:{set(){}}},bottom:{value:{set(){}}}}}};this.renderer={info:{render:{calls:0,triangles:0}}};this.detailStats={enabled:true,instances:125,triangles:4321,draws:7,teaRadius:180,treeRadius:220};}async load(){if(globalThis.__LOAD_GATE__)await globalThis.__LOAD_GATE__;this.onProgress?.(.9,'LATE_ASSET_PROGRESS');}setPlayerCar(id){this.car=id;}setGarageMode(v){this.garage=v;}setHomeMode(v){this.home=v;}setHomeViewBounds(r){this.homeBounds=r;}orbitGarage(y,p){this.orbitCalls??=[];this.orbitCalls.push([y,p]);}resetGarageView(){this.resetCalls=(this.resetCalls||0)+1;}setGarageViewBounds(r){this.garageBounds=r;}lookAtLandmark(target){this.lookedAt=target;return !!target;}getLandmarkPosition(t){return this.liveLandmark||t.position;}setCinematicCamera(p){this.cinematicPose=p;this.poseCalls=(this.poseCalls||0)+1;return true;}setPlayerUpgrades(p){this.upgrades=p;}update(m,dt){this.updates??=[];this.updates.push(dt);}isWater(){return false;}cycleCamera(){return'CHASE';}setQuality(q){this.quality=q;}resize(){}}`;
const audioFake=`export class GameAudio{constructor(){this.enabled=true;this.calls=[];this.resumes=0;globalThis.__AUDIO__=this;}resume(){this.resumes++;return globalThis.__RESUME__?globalThis.__RESUME__():Promise.resolve(true);}playUI(k){if(!this.enabled)return false;this.calls.push(k);return true;}update(m,t,o){this.updates??=[];this.updates.push({...o});}get diagnostics(){return{contextState:'running',unlocked:true,active:false,enabled:this.enabled,mix:{}}}}`;
const bundled=await build({entryPoints:[base+'/src/main.js'],bundle:true,format:'iife',write:false,plugins:[{name:'renderer-stub',setup(b){b.onResolve({filter:/\.\/scene\.js$/},()=>({path:'renderer',namespace:'stub'}));b.onResolve({filter:/\.\/audio\.js$/},()=>({path:'audio',namespace:'stub'}));b.onLoad({filter:/.*/,namespace:'stub'},a=>({contents:a.path==='audio'?audioFake:fake,loader:'js'}));}}]});
let run=0;
async function harness({track='coast',storage=new Map(),deferLoad=false,systemReduced=false,worldOverride=null}={}){
 let releaseLoad,rejectLoad;const loadGate=deferLoad?new Promise((resolve,reject)=>{releaseLoad=resolve;rejectLoad=reject;}):null;const writes=[];
 const els=new Map(),all=[],events=new Map(),frames=[];let active=null,timestamp=1000;
 const style=()=>({setProperty(k,v){this[k]=v;}});
 class El{constructor(tag,attrs={}){this.tagName=tag.toUpperCase();this.id=attrs.id||'';this.hidden=Object.hasOwn(attrs,'hidden');this.dataset={};for(const[k,v]of Object.entries(attrs))if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=v;this.style=style();this.attributes=attrs;this.textContent='';this.children=[];this.listeners=new Map();this.width=240;this.height=240;const c=new Set((attrs.class||'').split(' '));this.classList={toggle:(k,v)=>{if(v??!c.has(k))c.add(k);else c.delete(k);},add:k=>c.add(k),remove:k=>c.delete(k),contains:k=>c.has(k)};}get value(){return this._value??'';}set value(v){const value=String(v);this._value=this.tagName==='SELECT'&&!(this.children||[]).some(o=>String(o.value)===value)?'':value;}addEventListener(n,f){this.listeners.set(n,[...(this.listeners.get(n)||[]),f]);}fire(n,e={}){for(const f of this.listeners.get(n)||[])f({target:this,preventDefault(){},pointerId:1,...e});}setAttribute(k,v){this.attributes[k]=v;}getAttribute(k){return this.attributes[k];}querySelector(){return this.label??=(new El('span'));}focus(){active=this;}blur(){active=null;}setPointerCapture(id){this.captured=id;}replaceChildren(){this.children=[];this.value='';}appendChild(e){this.children.push(e);if(this.value==='')this.value=String(e.value);}closest(){return /BUTTON|A|INPUT|SELECT|TEXTAREA/.test(this.tagName)?this:null;}getBoundingClientRect(){return this.rect||{left:600,top:80,width:600,height:this.hidden?0:400};}getContext(){return new Proxy({},{get:()=>()=>{}});}}
 for(const m of html.matchAll(/<([a-z][\w-]*)\b([^>]*)>/gi)){const attrs={};for(const a of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[a[1]]=a[2]??'';const el=new El(m[1],attrs);all.push(el);if(el.id)els.set(el.id,el);}
 const query=s=>{const m=s.match(/^\[data-([\w-]+)(?:=["']?([^"'\]]+)["']?)?\]$/);if(!m)return[];const key=m[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase());return all.filter(e=>Object.hasOwn(e.dataset,key)&&(m[2]===undefined||e.dataset[key]===m[2]));};
 const context={console,URL,URLSearchParams,Date,Math,performance,crypto:{randomUUID:()=>`test-${++run}`},__WORLD__:structuredClone(worldOverride||worlds[track]),__LOAD_GATE__:loadGate,location:{search:'?track='+track,href:'https://example.test/',reloadCount:0,reload(){this.reloadCount++;},assign(){}},localStorage:{getItem(k){return storage.has(k)?storage.get(k):null;},setItem(k,v){writes.push([k,String(v)]);storage.set(k,String(v));}},addEventListener:(n,f)=>events.set(n,f),matchMedia:q=>{const media={matches:q.includes('prefers-reduced-motion')?systemReduced:true,addEventListener:(n,f)=>events.set('motion:'+n,f)};if(q.includes('prefers-reduced-motion'))context.__MOTION__=media;return media;},requestAnimationFrame:f=>frames.push(f)};
 context.document={getElementById:id=>els.get(id)||all.find(e=>e.id===id),querySelectorAll:query,createElement:tag=>{const e=new El(tag);all.push(e);return e;},documentElement:{style:style()},body:new El('body'),hidden:false,addEventListener:(n,f)=>events.set('document:'+n,f),get activeElement(){return active;}};context.window=context;
 vm.createContext(context);vm.runInContext(bundled.outputFiles[0].text,context);await new Promise(r=>setTimeout(r,0));assert.equal(context.__MALABAR__.ready,!deferLoad);
 const tick=n=>{for(let i=0;i<n;i++){timestamp+=1000/60;frames.shift()?.(timestamp);}};const key=(code,on=true)=>events.get(on?'keydown':'keyup')?.({code,target:els.get('game-canvas'),repeat:false,preventDefault(){}});
 return{api:context.__MALABAR__,context,els,events,storage,writes,tick,key,click:id=>els.get(id).fire('click'),controls:query('[data-control]'),world:context.__WORLD__,releaseLoad,rejectLoad};
}

const straight={prop_instances:[],route_points:Array.from({length:451},(_,i)=>[i*10,.18,0]),event_slices:{'coast-sprint':{startS:0,endS:1150},'hot-pursuit':{startS:2200,endS:4350},'time-attack':{startS:165,endS:1265}},districts:[{name:'TEST COAST',start_s:0,end_s:4500}],explore_starts:[{name:'TEST COAST',s:0}],minimap_roads:[]};
const plain=v=>JSON.parse(JSON.stringify(v));
const raceState=h=>JSON.stringify(h.api.model?{timer:h.api.model.timer,countdown:h.api.model.countdown,player:h.api.model.player,coins:h.api.model.coinsCollected,state:h.api.model.state}:null);
const saveState=h=>JSON.stringify([...h.storage]);
const settle=()=>new Promise(resolve=>setTimeout(resolve,0));
function loss(h){let prevented=0;h.els.get('game-canvas').fire('webglcontextlost',{preventDefault(){prevented++;}});assert(prevented>0,'Loss handler permits browser context restoration rather than ignoring the event');}
function interrupted(h){
 assert.equal(h.api.ready,false,'The controller must not report ready after graphics loss');
 assert.equal(h.els.get('loading').hidden,false,'Loss must show an accessible graphics error instead of blind play');
 assert.match(h.els.get('loading-title').textContent,/graphics interrupted/i);
 assert.match(h.els.get('loading-label').textContent,/reload/i);
 assert.equal(h.els.get('loading-retry').hidden,false);
 assert.equal(h.els.get('home-ride').disabled,true);
 assert.equal(h.els.get('menu').inert,true,'Background page remains inert behind the error dialog');
 assert(h.controls.every(b=>!b.classList.contains('pressed')),'Held touch input is cleared');
}
function assertFrozenThroughRecoveryAttempts(h,label){
 const before=raceState(h),saved=saveState(h),writes=h.writes.length,model=h.api.model;
 const renders=h.api.renderer?.updates?.length||0;
 h.tick(120);
 h.events.get('focus')?.();h.context.document.hidden=false;h.events.get('document:visibilitychange')?.();
 h.els.get('game-canvas').fire('webglcontextrestored');
 h.els.get('game-canvas').fire('webglcontextrestored');
 h.api.pause(false,'regression resume attempt');h.api.start();
 for(const code of ['KeyW','KeyF','KeyR','Enter','Escape'])h.key(code);
 h.tick(240);loss(h);h.tick(60);
 interrupted(h);
 assert.equal(h.api.model,model,label+': the run is neither restarted nor replaced');
 assert.equal(raceState(h),before,label+': timer, countdown, player, coins and terminal state stay frozen');
 assert.equal(saveState(h),saved,label+': saved progression is byte-identical');
 assert.equal(h.writes.length,writes,label+': no hidden duplicate reward or save writes');
 assert.equal(h.api.renderer?.updates?.length||0,renders,label+': no render submission after loss');
 assert.equal(h.context.location.reloadCount,0,label+': restore must not silently reload');
 h.click('loading-retry');
 assert.equal(h.context.location.reloadCount,1,label+': explicit Reload is available');
 assert.equal(saveState(h),saved,label+': Reload handler does not reset saved progress');
 console.log('PASS graphics loss: '+label+'; frozen through repeated loss/restore/focus/input/resume/start, unchanged saves, explicit Reload.');
}
// Reproduce the former blind-driving path with held keyboard and touch throttle.
for(const track of ['coast','highlands']){
 const h=await harness({track});h.api.start();h.tick(200);h.key('KeyW');
 const throttle=h.controls.find(b=>b.dataset.control==='throttle');throttle.fire('pointerdown');h.tick(60);
 assert(h.api.model.player.speed>0);assert(throttle.classList.contains('pressed'));
 const before=raceState(h);loss(h);interrupted(h);
 assert.equal(raceState(h),before,'Loss does not move or reset the active car');
 assert.equal(h.api.model.paused,true,'Active model is paused immediately');
 assert.equal(h.api.snapshot().paused,true,'Controller pause agrees with model pause');
 const audio=h.context.__AUDIO__;assert(audio.enabled===false||audio.updates.at(-1)?.paused===true,'Race audio is silenced/paused at loss');
 assertFrozenThroughRecoveryAttempts(h,track+' held-throttle race');
}
for(const stage of ['countdown','already paused','Home']){
 const h=await harness();if(stage!=='Home'){h.api.start();if(stage==='already paused'){h.tick(200);h.api.pause(true);}}
 const before=raceState(h);loss(h);interrupted(h);assert.equal(raceState(h),before);
 if(stage!=='Home')assert.equal(h.api.model.paused,true);
 assertFrozenThroughRecoveryAttempts(h,stage);
}
// Late asynchronous asset completion must never clear a context-loss latch.
const loading=await harness({deferLoad:true}),loadingSaved=saveState(loading),loadingWrites=loading.writes.length;
loss(loading);interrupted(loading);loading.releaseLoad();await settle();await settle();
interrupted(loading);assert.equal(saveState(loading),loadingSaved);assert.equal(loading.writes.length,loadingWrites);
assertFrozenThroughRecoveryAttempts(loading,'pending asset load resolves after context loss');
// A late loader error and progress notifications must not replace the graphics message.
const rejected=await harness({deferLoad:true});loss(rejected);interrupted(rejected);
const graphicsMessage=rejected.els.get('loading-label').textContent;
rejected.api.renderer.onProgress(.95,'LATE_ASSET_PROGRESS');
assert.equal(rejected.els.get('loading-label').textContent,graphicsMessage);
rejected.rejectLoad(new Error('LATE_ASSET_FAILURE'));await settle();await settle();
assert.equal(rejected.els.get('loading-label').textContent,graphicsMessage);
interrupted(rejected);assertFrozenThroughRecoveryAttempts(rejected,'pending asset load rejects after context loss');
// Cinematic intro cannot finish itself into an unseen active race.
const intro=await harness({worldOverride:straight});intro.click('home-story');intro.click('story-start');
assert.equal(intro.api.snapshot().cinematic?.kind,'intro');const introRun=raceState(intro);
loss(intro);interrupted(intro);assert.equal(raceState(intro),introRun);assertFrozenThroughRecoveryAttempts(intro,'Story intro');
// Settle one canonical story result, then lose graphics during the finish shot.
const finish=await harness({worldOverride:straight});finish.click('home-story');finish.click('story-start');finish.click('cinematic-skip');
const m=finish.api.model,q=m.sampleRoute(m.endS);
Object.assign(m.player,{s:q.s,x:q.x,y:q.y,z:q.z,heading:q.heading,grounded:true,altitude:0,flying:false,flipActive:false});
vm.runInContext("__MALABAR__.model.state='finished';__MALABAR__.model.result={state:'finished',scenario:'time-attack',time:20,position:1,collectedCoins:5};",finish.context);
finish.tick(1);assert.equal(finish.api.snapshot().cinematic?.kind,'finish');
const profile=JSON.parse(finish.storage.get(PROFILE_KEY));assert.equal(profile.awardedRuns.length,1);assert(profile.credits>0);
loss(finish);interrupted(finish);assertFrozenThroughRecoveryAttempts(finish,'settled Story finish reward');
// The opt-in surface proof has its own StuntGameModel; use its actual shipped route/profile.
const surface=await harness({track:'surface-test'});surface.api.start();surface.key('KeyW');surface.tick(120);
assert.equal(surface.api.model.scenario.id,'free-drive');assert(surface.api.model.player.speed>0);
loss(surface);interrupted(surface);assert.equal(surface.api.model.paused,true);
assertFrozenThroughRecoveryAttempts(surface,'optional surface-test mode');
// Unsupported future saves are protected; Reload warns about session-only changes.
const futureRaw='{"schemaVersion":99,"valuable":"unknown future save"}';
const protectedSave=await harness({storage:new Map([[PROFILE_KEY,futureRaw]])});loss(protectedSave);interrupted(protectedSave);
assert.match(protectedSave.els.get('loading-label').textContent,/Session-only changes may be lost/);
assertFrozenThroughRecoveryAttempts(protectedSave,'protected unsupported save');
assert.equal(protectedSave.storage.get(PROFILE_KEY),futureRaw);
console.log('GRAPHICS_CONTEXT_CONTROLLER_PASS: 11 scenarios, actual controller/gameplay/storage with simulated context events; no real GPU loss/restore or browser rendering verdict.');
