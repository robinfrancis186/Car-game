/** Width-contract regression, not a rendered browser/GPU test.
 * Parses the actual relevant CSS cascade and anchors the prepatch result to
 * measured Mac Chrome bounds at 1222 x 619 (DPR 2).
 */
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {transform} from 'esbuild';

const css=await fs.readFile(process.argv[2]||new URL('../src/style.css',import.meta.url),'utf8');
await transform(css,{loader:'css',logLevel:'silent'});
function rules(text,media=[],result=[]){
 text=text.replace(/\/\*[\s\S]*?\*\//g,'');let at=0;
 while(at<text.length){const start=text.indexOf('{',at);if(start<0)break;const selector=text.slice(at,start).trim();let end=start+1,depth=1;for(;end<text.length&&depth;end++){if(text[end]==='{')depth++;if(text[end]==='}')depth--;}assert.equal(depth,0,'Balanced CSS blocks');const body=text.slice(start+1,end-1);if(selector.startsWith('@media'))rules(body,[...media,selector.slice(6).trim()],result);else if(!selector.startsWith('@'))result.push({selectors:selector.split(',').map(s=>s.trim()),media,values:Object.fromEntries(body.split(';').map(s=>s.split(':')).filter(p=>p.length>=2).map(([k,...v])=>[k.trim(),v.join(':').trim()]))});at=end;}
 return result;
}
const all=rules(css);
function matches(query,v){return query.split(/\s+and\s+/).every(part=>{const m=part.trim().match(/^\(([^:]+):\s*([^)]*)\)$/);assert(m,'Supported width-contract media query: '+part);const [,key,value]=m;const n=parseFloat(value);if(key==='max-width')return v.w<=n;if(key==='min-width')return v.w>=n;if(key==='max-height')return v.h<=n;if(key==='min-height')return v.h>=n;if(key==='orientation')return value===(v.w>v.h?'landscape':'portrait');if(key==='pointer')return value===v.pointer;throw Error('Unexpected relevant media query: '+query);});}
function style(selector,v){const out={};for(const r of all)if(r.selectors.includes(selector)&&r.media.every(q=>matches(q,v)))Object.assign(out,r.values);return out;}
const px=v=>{assert.match(v,/^-?\d+(?:\.\d+)?px$/);return Number.parseFloat(v);};
function measure(v,patched=true){const parent=style('.speed-cluster',v),child=style('.vehicle-bars',v),width=px(parent.width),x=parent.left&&parent.left!=='auto'?px(parent.left):v.w-px(parent.right)-width;assert.equal(child['max-width'],'100%','Bars must never exceed their responsive parent');const barsWidth=patched?Math.min(px(child.width),width):px(child.width);return{cluster:{x,width,right:x+width},bars:{x:x+Math.max(0,width-barsWidth),width:barsWidth,right:x+Math.max(0,width-barsWidth)+barsWidth}};}
const mac={w:1222,h:619,pointer:'fine'};
assert.deepEqual(measure(mac,false),{cluster:{x:1029,width:170,right:1199},bars:{x:1029,width:232,right:1261}},'Prepatch CSS reproduces measured Mac geometry');
assert.deepEqual(measure(mac),{cluster:{x:1029,width:170,right:1199},bars:{x:1029,width:170,right:1199}},'Patch removes 39px viewport overflow by sizing, not clipping');
let cases=0;
for(const [w,h] of [[320,568],[390,844],[430,932],[568,320],[700,500],[844,390],[900,650],[1024,600],[1100,650],[1101,650],[1222,619],[1222,650],[1222,651],[1440,722],[1920,650],[1920,1080]])for(const pointer of ['fine','coarse']){const r=measure({w,h,pointer});assert(r.bars.x>=r.cluster.x-.01);assert(r.bars.right<=r.cluster.right+.01);assert(r.bars.x>=0&&r.bars.right<=w);cases++;}
for(const r of all.filter(r=>r.selectors.includes('.vehicle-bars')))assert(!['hidden','clip'].includes(r.values.overflow),'Do not hide bars to disguise overflow');
console.log(`PASS HUD width contract: ${cases} CSS breakpoint/pointer cases; exact Mac prepatch 39px overflow reproduced and capped to parent. Source cascade/math only, not rendered acceptance.`);
