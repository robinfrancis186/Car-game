import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {assertProtectedWithAudioScope} from './polish-audio-scope.mjs';
const scope=JSON.parse(fs.readFileSync(new URL('./polish-gameplay-scope.json',import.meta.url))),hash=b=>createHash('sha256').update(b).digest('hex');
assert.equal(scope.path,'web/src/gameplay.js');
assert.deepEqual(scope.changed_methods,['_updateAutoRecovery','_airLineOfSight','_updatePolice']);
assert.deepEqual(scope.added_methods,['_patrolSeesPlayer']);
let behaviorsChecked=false;
export function assertProtectedWithPolishScope(path,originalHash,currentHash){
 if(path!=='web/src/gameplay.js')return assertProtectedWithAudioScope(path,originalHash,currentHash);
 assert.equal(originalHash,scope.original_sha256,'Original protected gameplay baseline retained');
 assert.equal(currentHash,scope.candidate_sha256,'Gameplay must match the exact Stage2 occlusion patch');
 if(behaviorsChecked)return;
 const source=fs.readFileSync(new URL('../src/gameplay.js',import.meta.url),'utf8'),matches=[...source.matchAll(/^ ([A-Za-z_]\w*)\(/gm)],methods=new Map(matches.map((m,i)=>[m[1],source.slice(m.index,matches[i+1]?.index??source.indexOf('\n}\n',m.index))]));
 assert.equal(Object.keys(scope.unchanged_method_sha256).length,58,'All 58 other gameplay methods remain protected');
 for(const [name,expected]of Object.entries(scope.unchanged_method_sha256))assert.equal(hash(methods.get(name)),expected,'Unchanged gameplay method '+name);
 for(const name of ['patrol-visibility.test.mjs','police-capture.test.mjs']){const result=spawnSync(process.execPath,[new URL('./'+name,import.meta.url).pathname],{encoding:'utf8'});assert.equal(result.status,0,`Gameplay scope behavior ${name}: ${result.stdout}\n${result.stderr}`);}
 behaviorsChecked=true;console.log('PASS exact reviewed patrol patch, original gameplay baseline, unchanged driving/race/reward methods and patrol/capture behavior');
}
