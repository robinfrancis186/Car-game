/** Executes the actual entry source with its real client/model/adapter and server
 * manifest. Only browser/GPU surfaces and network delivery are stubbed. This is
 * CPU regression coverage, NOT browser/GPU or public-internet acceptance. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import * as THREE from 'three';
import {GameModel} from '../game/gameplay.js';
import {RaceClient} from '../client/client.mjs';
import {OnlineRenderAdapter} from '../client/render-adapter.mjs';
import {endpointForPage} from '../client/endpoint.mjs';
import {EXPECTED} from '../client/manifest-pin.mjs';
import {NEUTRAL} from '../client/validation.mjs';
import {getManifest,loadData} from '../server/data.mjs';

const origin='https://kerala-roadster-multiplayer-alpha.onrender.com';
const manifest={...getManifest(),route:loadData().world.route_points};
const route=manifest.route.map(p=>({x:p[0],y:p[1],z:p[2]}));
const privateMarker='PRIVATE_TEST_TOKEN_MUST_NOT_APPEAR';

async function entry(t,options={}){
 const nodes=new Map(),clients=[],requests=[],logs=[];let frames=0,sockets=0,progress=()=>{};
 const node=id=>{
  if(!nodes.has(id))nodes.set(id,{id,textContent:'',hidden:false,disabled:true,value:'',style:{},classList:{remove(){},add(){}},focus(){},replaceChildren(){}});
  return nodes.get(id);
 };
 class Renderer{
  constructor(_canvas,{onProgress}){progress=label=>onProgress(0,label);if(options.rendererCreateError)throw options.rendererCreateError;this.route=options.route||route;}
  async load(){if(options.rendererLoadError)throw options.rendererLoadError;}
 }
 class Transport extends RaceClient{
  constructor(config){
   if(options.clientCreateError)throw options.clientCreateError;
   super({...config,fetch:async(url,init)=>{
    requests.push({url,cache:init.cache});
    if(options.fetchError)throw options.fetchError;
    return new Response(options.body??JSON.stringify(options.manifest||manifest),{status:options.status||200});
   },WebSocket:class{constructor(){sockets++;throw Error('No startup socket is allowed');}}});
   clients.push(this);
  }
 }
 t.after(()=>clients.forEach(c=>c.close()));
 let source=await readFile(process.env.STARTUP_BASELINE_ENTRY||new URL('../client/main.mjs',import.meta.url),'utf8');
 // Bind new startup exports only when the actual entry imports them. This also
 // lets the same regression reproduce the original entry before the fix.
 const startup=source.includes("'./startup-diagnostics.mjs'")||source.includes('"./startup-diagnostics.mjs"')
  ?await import('../client/startup-diagnostics.mjs'):{};
 source=source.replace(/import\s*(?:\*\s*as\s+\w+|\{[^}]*\})\s*from\s*['"][^'"]+['"];?/g,'');
 assert.match(source,/boot\(\);\s*$/,'actual entry must still invoke boot');
 source=source.replace(/boot\(\);\s*$/,'globalThis.testBoot=boot();');
 const window={},context=vm.createContext({
  ...startup,THREE,CoastRenderer:Renderer,GameModel,RaceClient:Transport,
  OnlineRenderAdapter,configureOnlineRenderer(){},endpointForPage,EXPECTED,NEUTRAL,
  validateWorldAssets:async()=>{if(options.integrityError)throw options.integrityError;},
  URL,location:new URL(origin),window,
  document:{getElementById:node,querySelectorAll:()=>[],addEventListener(){},hasFocus:()=>true,hidden:false},
  addEventListener(){},setInterval(){},requestAnimationFrame(){frames++;},
  sessionStorage:{getItem:()=>null,removeItem(){},setItem(){}},
  console:{error:(...args)=>logs.push(args),warn:(...args)=>logs.push(args),log:(...args)=>logs.push(args)},
 });
 vm.runInContext(source,context,{filename:'client/main.mjs'});
 await context.testBoot;
 return{node,clients,requests,logs,frames,sockets,progress,get diagnostics(){return window.__KERALA_ONLINE__.diagnostics;},get ready(){return window.__KERALA_ONLINE__.ready;}};
}

function failed(result,{stage,code,httpStatus}){
 assert.equal(result.ready,false);
 assert.equal(result.node('connection').textContent,'STARTUP FAILED');
 const startup=JSON.parse(JSON.stringify(result.diagnostics.startup));
 assert.equal(startup.status,'failed');
 assert.equal(startup.stage,stage);
 assert.deepEqual(startup.failure,{stage,code,...(httpStatus===undefined?{}:{httpStatus})});
 assert.match(result.node('loading').textContent,new RegExp(code));
 const visibleStage={'renderer-create':'graphics setup','renderer-load':'scene loading','asset-integrity':'asset verification','renderer-config':'scene setup','client-create':'network setup',manifest:'manifest',route:'route',adapter:'adapter',preview:'preview','session-restore':'session',ready:'ready'}[stage];
 assert.match(result.node('loading').textContent,new RegExp(visibleStage));
 assert.equal(result.node('loading').hidden,false);
 assert.doesNotMatch(result.node('notice').textContent,/Left room/);
 assert.equal(result.node('create').disabled,true);
 assert.equal(result.node('join').disabled,true);
 assert.equal(result.node('camera').disabled,true);
 assert.equal(result.node('quality').disabled,true);
 assert.equal(result.frames,0);
 assert.equal(result.sockets,0);
 const exposed=JSON.stringify({diagnostics:result.diagnostics,logs:result.logs,loading:result.node('loading').textContent,notice:result.node('notice').textContent});
 assert(!exposed.includes(privateMarker),'failure diagnostics must not disclose raw error messages');
}

test('actual entry with matching server manifest becomes ready without opening a race socket',async t=>{
 const r=await entry(t);
 assert.equal(r.ready,true);
 assert.equal(r.diagnostics.startup.status,'ready');
 assert.equal(r.diagnostics.startup.stage,'ready');
 assert.equal(r.diagnostics.startup.failure,null);
 assert.equal(r.node('connection').textContent,'AVAILABLE');
 assert.equal(r.node('loading').hidden,true);
 assert.equal(r.node('create').disabled,false);
 assert.equal(r.node('join').disabled,false);
 assert.equal(r.frames,1);
 assert.equal(r.sockets,0);
 assert.deepEqual(r.requests,[{url:origin+'/manifest',cache:'no-store'}]);
});

test('actual entry retains manifest timeout rather than overwriting it with Offline/Left room',async t=>{
 const r=await entry(t,{fetchError:new DOMException(privateMarker,'TimeoutError')});
 failed(r,{stage:'manifest',code:'TIMEOUT'});
 assert.equal(r.clients.length,1);
 assert.equal(r.clients[0].status,'offline','client cleanup must still run');
});

test('actual entry retains sanitized network and HTTP failures with controls disabled',async t=>{
 const network=await entry(t,{fetchError:new TypeError('Failed to fetch '+privateMarker)});
 failed(network,{stage:'manifest',code:'NETWORK_ERROR'});
 const http=await entry(t,{status:503,body:privateMarker});
 failed(http,{stage:'manifest',code:'CONNECTION_FAILED',httpStatus:503});
});

test('actual entry rejects malformed JSON and mismatching manifest route hash',async t=>{
 const invalid=await entry(t,{body:'{"private":"'+privateMarker});
 failed(invalid,{stage:'manifest',code:'INVALID_JSON'});
 const altered=structuredClone(manifest);altered.route[0][0]+=1;
 const mismatched=await entry(t,{manifest:altered});
 failed(mismatched,{stage:'manifest',code:'ROUTE_MISMATCH'});
});

test('actual entry rejects a renderer route that differs from the validated manifest',async t=>{
 const altered=route.map(p=>({...p}));altered[0].x+=1;
 failed(await entry(t,{route:altered}),{stage:'route',code:'ROUTE_MISMATCH'});
});

test('actual entry preserves renderer and asset-integrity failure phases before any client is created',async t=>{
 const renderer=await entry(t,{rendererLoadError:new Error(privateMarker)});
 failed(renderer,{stage:'renderer-load',code:'PREPARATION_ERROR'});
 assert.equal(renderer.clients.length,0);
 const assets=await entry(t,{integrityError:Object.assign(new Error('WORLD_ASSET_MISMATCH'),{httpStatus:429})});
 failed(assets,{stage:'asset-integrity',code:'WORLD_ASSET_MISMATCH',httpStatus:429});
 assert.equal(assets.clients.length,0);
});

test('late renderer progress cannot overwrite the retained startup failure',async t=>{
 const r=await entry(t,{integrityError:new Error('WORLD_ASSET_MISMATCH')});
 failed(r,{stage:'asset-integrity',code:'WORLD_ASSET_MISMATCH'});
 const failure=r.node('loading').textContent;
 r.progress('Preparing coast 32 / 32');
 assert.equal(r.node('loading').textContent,failure);
 assert.equal(r.diagnostics.startup.status,'failed');
});

test('client constructor failure is labeled network setup rather than renderer setup',async t=>{
 const r=await entry(t,{clientCreateError:new Error(privateMarker)});failed(r,{stage:'client-create',code:'PREPARATION_ERROR'});assert.equal(r.clients.length,0);
});
