import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../../',import.meta.url),baseline=JSON.parse(await fs.readFile(new URL('./v16-protected-baseline.json',import.meta.url)));
assert.equal(Object.keys(baseline.protected).length,127,'Complete frozen V15 protected inventory is required');
for(const [path,hash]of Object.entries(baseline.protected))assert.equal(createHash('sha256').update(await fs.readFile(new URL(path,root))).digest('hex'),hash,path+' must retain frozen V15 behavior/asset bytes');
console.log(`PASS V16 scope: ${Object.keys(baseline.protected).length} V15 runtime files exact, including normal physics, saves, economy, story, audio and existing assets.`);
