import assert from 'node:assert/strict';import fs from 'node:fs/promises';import {createHash}from'node:crypto';
const baseline=JSON.parse(await fs.readFile(new URL('./v15-protected-baseline.json',import.meta.url))),root=new URL('../../',import.meta.url);
for(const [path,hash]of Object.entries(baseline.protected)){const b=await fs.readFile(new URL(path,root));assert.equal(createHash('sha256').update(b).digest('hex'),hash,path+' must remain unchanged');}
for(const file of ['garage.js','profile-storage.js','story.js','story-store.js','cinematic-camera.js','style.css','upgrade-visuals.js','boost-fire.js'])assert(baseline.protected['web/src/'+file]);
console.log(`PASS V15 scope: ${Object.keys(baseline.protected).length} frozen V14.1 files exact, including all save/economy/ownership/story/cinematic/UI-style and existing car/world geometry assets.`);
