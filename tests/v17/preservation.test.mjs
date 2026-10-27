import {assertProtectedWithPolishScope} from '../../web/tests/polish-preservation-scope.mjs';
/** Bound reference-UI work against the frozen live V16.1 runtime manifest. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const release=JSON.parse(await fs.readFile(path.join(root,'tests/release/V16_1_RELEASE.json')));
const protectedBaseline=JSON.parse(await fs.readFile(path.join(root,'web/tests/v16-1-protected-baseline.json')));
const permittedChanged=new Set(['web/index.html','web/src/style.css','web/src/main.js','web/src/scene.js','web/src/audio.js','web/src/gameplay.js']);
const privateReferenceHashes=new Set(['78186c597582de327dee7a4f25b1884765dac262fccfe32289c85c07c37eed3b','82421f0f9de3a5cda88e7ff4f0574f3736cd4331476e7742630b6abafc3b7c97','c9165be11338a88e5aa90be971dfb7734c1502ac4a8d382f70f6bbd04a63ff5d','e8498e0070256a7dcedc110f2c8118e16c2649d246015a1ed378524112d0ef1d']);
const hash=b=>createHash('sha256').update(b).digest('hex');
const changed=[],unchanged=[],inventory=[];
for(const file of release.runtime_files){const current=hash(await fs.readFile(path.join(root,file.path)));(current===file.sha256?unchanged:changed).push(file.path);if(current!==file.sha256)assert(permittedChanged.has(file.path),`Unexpected protected V16.1 runtime change: ${file.path}`);}
assert.equal(Object.keys(protectedBaseline).length,138);
for(const [rel,expected]of Object.entries(protectedBaseline))assertProtectedWithPolishScope(rel,expected,hash(await fs.readFile(path.join(root,rel))));
async function walk(dir){for(const entry of await fs.readdir(path.join(root,dir),{withFileTypes:true})){const rel=dir+'/'+entry.name;if(entry.isDirectory())await walk(rel);else{const bytes=await fs.readFile(path.join(root,rel));const sha256=hash(bytes);assert(!privateReferenceHashes.has(sha256),`Private visual reference copied into runtime: ${rel}`);inventory.push({path:rel,bytes:bytes.length,sha256});}}}
for(const dir of ['web/src','web/public'])await walk(dir);const index=await fs.readFile(path.join(root,'web/index.html'));inventory.push({path:'web/index.html',bytes:index.length,sha256:hash(index)});inventory.sort((a,b)=>a.path.localeCompare(b.path));
const report={created:new Date().toISOString(),base:release.runtime_tree_sha256,protectedFiles:138,protectedByteIdentical:false,protectedByteIdenticalCount:136,approvedAudioScope:'web/tests/polish-audio-scope.json',approvedGameplayScope:'web/tests/polish-gameplay-scope.json',oldRuntimeCount:release.runtime_files.length,changed,unchanged:unchanged.length,addedRuntime:inventory.map(x=>x.path).filter(p=>!release.runtime_files.some(x=>x.path===p)),privateReferenceOriginalsAbsentFromRuntime:true,runtimeTree:hash(inventory.map(x=>`${x.path}\0${x.sha256}\n`).join('')),inventory};
await fs.writeFile(path.join(root,'tests/v17/preservation-report.json'),JSON.stringify(report,null,2));
console.log(`PASS 136 exact protected files plus authorized audio/gameplay scopes and ${unchanged.length}/${release.runtime_files.length} frozen V16.1 runtime files unchanged; permitted UI/scene changes: ${changed.join(', ')||'(none yet)'}`);
console.log('PASS private original reference image hashes absent from runtime. This does not prove derivatives, archive exclusions, rendered fidelity or native FPS.');
