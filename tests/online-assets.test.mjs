/** Actual renderer load enumeration, with network/GLTF completion stopped before GPU work. */
import test from 'node:test';import assert from 'node:assert/strict';import{readFile,readdir}from'node:fs/promises';import{GLTFLoader}from'three/addons/loaders/GLTFLoader.js';
globalThis.document={baseURI:'http://localhost/'};globalThis.window={};
const {CoastRenderer}=await import('../game/scene.js'),assets=new URL('../public/assets/',import.meta.url);
test('online skips unused coin texture; all remaining selected GLBs have no image fetch dependency; solo default preserved',async()=>{
 const originalFetch=globalThis.fetch,originalLoad=GLTFLoader.prototype.loadAsync,requested=[];
 globalThis.fetch=async url=>({json:async()=>JSON.parse(await readFile(new URL(new URL(url).pathname.split('/').at(-1),assets)))});
 GLTFLoader.prototype.loadAsync=async url=>{requested.push(new URL(url).pathname.split('/').at(-1));throw Error('TEST_STOP_BEFORE_GPU');};
 try{
  const renderer=Object.create(CoastRenderer.prototype);Object.assign(renderer,{worldFile:'course_runtime.json',collectiblesEnabled:false,onProgress(){}});
  await assert.rejects(()=>renderer.load(),/TEST_STOP_BEFORE_GPU/);assert(requested.length>25);assert(!requested.includes('ArcadeCoin.glb'));
  for(const name of requested){const b=await readFile(new URL(name,assets)),json=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());assert.equal((json.images||[]).length,0,name);}
  const all=[];for(const name of await readdir(assets)){if(!name.endsWith('.glb'))continue;const b=await readFile(new URL(name,assets)),json=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());if(json.images?.length)all.push(name);}assert.deepEqual(all,['ArcadeCoin.glb']);
  requested.length=0;renderer.collectiblesEnabled=true;await assert.rejects(()=>renderer.load(),/TEST_STOP_BEFORE_GPU/);assert(requested.includes('ArcadeCoin.glb'));
  const source=await readFile(new URL('../game/scene.js',import.meta.url),'utf8');assert(source.includes("worldFile='course_runtime.json',collectibles=true"));assert(source.includes('this.collectibles=this.collectiblesEnabled?new RaceCollectibles'));
  const entry=await readFile(new URL('../client/main.mjs',import.meta.url),'utf8');assert(entry.includes("worldFile:'course_runtime.json',collectibles:false"));
 }finally{globalThis.fetch=originalFetch;GLTFLoader.prototype.loadAsync=originalLoad;}
});
