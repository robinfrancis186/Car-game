import fs from 'node:fs';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
const scope=JSON.parse(fs.readFileSync(new URL('./polish-audio-scope.json',import.meta.url)));
assert.equal(scope.path,'web/src/audio.js','Only audio has an approved protected-file exception');
let behaviorsChecked=false;
export function assertProtectedWithAudioScope(path,originalHash,currentHash){
 if(path!=='web/src/audio.js'){assert.equal(currentHash,originalHash,path);return;}
 assert.equal(originalHash,scope.original_sha256,'Original protected audio baseline retained');
 assert.equal(currentHash,scope.candidate_sha256,'Audio must match the exact reviewed polish patch');
 if(behaviorsChecked)return;
 for(const file of ['audio.test.mjs','rotor-audio.test.mjs']){const result=spawnSync(process.execPath,[new URL('./'+file,import.meta.url).pathname],{encoding:'utf8'});assert.equal(result.status,0,`Audio scope behavioral check ${file}: ${result.stdout}\n${result.stderr}`);}
 behaviorsChecked=true;console.log('PASS explicitly reviewed audio scope: original baseline retained, exact candidate hash and audio/rotor behavioral suites');
}
