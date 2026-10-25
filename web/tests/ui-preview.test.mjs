/** Static preview contract only; no real browser or race proof. */
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {smokePreview} from '../../tools/ui-review-r3-1/preview-smoke-harness.mjs';
const html=await fs.readFile(new URL('../../dist/ui-preview.html',import.meta.url),'utf8');
for(const alias of ['v16-1-ui-preview.html','v17-ui-preview.html'])assert.equal(await fs.readFile(new URL('../../dist/'+alias,import.meta.url),'utf8'),html,'Static-host named alias is byte-identical');
const [source,css,main]=await Promise.all(['index.html','src/style.css','src/main.js'].map(p=>fs.readFile(new URL('../'+p,import.meta.url),'utf8')));
const worlds={};for(const [id,file]of [['coast','course_runtime.json'],['highlands','course_runtime_highlands.json']])worlds[id]=JSON.parse(await fs.readFile(new URL('../public/assets/'+file,import.meta.url)));
smokePreview({html,source,css,main,worlds});
console.log('UI_PREVIEW_R3_5_SINGLE_HOME_PASS — synthetic DOM only.');
