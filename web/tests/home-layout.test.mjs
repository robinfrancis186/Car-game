/** Exact-source structure and arithmetic, not browser pixels or GPU acceptance. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const css=readFileSync(new URL('../src/style.css',import.meta.url),'utf8');
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const block=css.slice(css.indexOf('/* R3.5 one showroom Home flow.'));
const compact=block.replace(/\s+/g,'');
let passed=0;const test=(name,fn)=>{fn();passed++;console.log('PASS',name);};
const nearly=(a,b)=>assert(Math.abs(a-b)<1e-6,`${a} != ${b}`);
test('native setup is inside Home and precedes the sole Play outside its scroll body',()=>{
 const home=html.slice(html.indexOf('<section id="home-content"'),html.indexOf('<section id="garage-panel"'));
 assert.match(home,/<details id="home-race-setup" class="home-race-setup">/);assert.match(home,/<summary id="home-setup-summary">/);
 const detailsEnd=home.indexOf('</details>'),play=home.indexOf('id="home-ride"');assert(detailsEnd>0&&play>detailsEnd);assert.equal((home.match(/id="home-ride"/g)||[]).length,1);
 for(const id of ['start-button','event-content','event-tabs','event-car-choices'])assert(!html.includes(`id="${id}"`),id);
});
test('unreachable outdoor Events positioning is removed, not just hidden',()=>{
 for(const selector of ['#event-content','#event-tabs','.events-view','.brand-lockup','.event-vehicle-picker'])assert(!css.includes(selector),selector);
 assert(css.includes('.track-choice'));assert(css.includes('.scenario-tab'));assert(css.includes('.district-start'));
});
test('native summary is a keyboard-focusable44px pointer target within pointer-disabled scene',()=>{
 assert(compact.includes('.home-race-setup>summary{height:44px;min-height:var(--control-target);'));
 assert.match(block,/\.home-race-setup>summary\{[^}]*pointer-events:auto;touch-action:manipulation;/);
 assert(css.includes('summary:focus-visible'));assert(!html.match(/<summary[^>]*tabindex="-1"/));
});
test('drawer content scrolls independently and uses existing secondary tokens',()=>{
 assert(compact.includes('height:var(--home-setup-body-height,44px);min-height:0;overflow-y:auto;overflow-x:hidden;'));
 assert(compact.includes('overscroll-behavior:contain;touch-action:pan-y;scrollbar-width:thin;scroll-padding:8px;'));
 assert(compact.includes('background:var(--control-secondary-bg);color:var(--control-secondary-color);'));
 assert(!/position:fixed|z-index:/.test(block),'no new full-screen overlay');
});
test('closed responsive grids reserve setup plus all original action rows',()=>{
 for(const rows of ['46px72px64px52px','46px56px52px44px','46px52px48px44px'])assert(compact.includes('grid-template-rows:'+rows),rows);
 for(const selector of ['.home-setup-body.track-choice','.home-mode-picker.scenario-tab','.home-setup-body.district-startselect'])assert(compact.includes(selector+'{min-height:44px')||compact.includes(selector+'{min-width:0;min-height:44px'),selector);
});
test('expanded viewport formulas bind drawer body to available action-column height',()=>{
 for(const declaration of ['--home-setup-body-height:max(52px,calc(57dvh-276px-var(--safe-bottom)))','--home-setup-body-height:max(52px,calc(57dvh-240px-var(--safe-bottom)))','--home-setup-body-height:clamp(52px,calc(100dvh-506px-var(--safe-bottom)),164px)','top:min(114px,calc(100dvh-266px-var(--safe-bottom)))'])assert(compact.includes(declaration),declaration);
});
test('1222x619 collapsed summary clears existing large wordmark and preserves Play position',()=>{
 const width=1222,height=619,gap=8,oldRows=[72,64,52],newRows=[46,...oldRows];
 const oldTop=height*.86-oldRows.reduce((a,b)=>a+b)-2*gap,newTop=height*.86-newRows.reduce((a,b)=>a+b)-3*gap;
 const titleFont=Math.min(120,Math.max(64,width*.075));
 const brandBottom=height*.18+titleFont*.94+5+15*1.45+22+9*1.45;
 nearly(newTop,274.34);nearly(brandBottom,259.371);assert(newTop-brandBottom>14);nearly(newTop+46+gap,oldTop);
});
function landscape(height,safe=0){
 const short=height<=520,compact=height<=700;
 const gap=short?6:8,rows=short?[44,44,44]:compact?[56,52,44]:[72,64,52];
 const top=short?Math.min(114,height-266-safe):Math.min(height*.43,height-(compact?292:328)-safe),bottom=18+safe;
 const area=height-top-bottom,details=area-rows.reduce((a,b)=>a+b)-3*gap;
 const body=short?Math.max(52,height-Math.min(114,height-266-safe)-214-safe):Math.max(52,height*.57-(compact?240:276)-safe);
 return {top,bottom,area,details,body,rows};
}
test('expanded desktop and short landscape keep full44px body and every action above bottom inset',()=>{
 for(const [w,h] of [[1222,619],[1706,922],[1024,768],[844,390],[667,375],[568,320]])for(const safe of [0,34]){
  const b=landscape(h,safe);assert(b.top>=0);if(h>350)assert(b.top>=58);assert(b.details>=98-1e-9);assert(b.body>=52);nearly(b.details-46,b.body);assert(b.rows.every(n=>n>=44));nearly(b.top+b.area,h-b.bottom);
 }
});
function portrait(width,height,safe=0,open=false){
 const small=height<=650,gap=small?6:8,padding=(small?26:34)+safe;
 const title=Math.min(small?64:82,Math.max(small?54:60,width*(small?.175:.18)));
 const brand=(small?7:17)+title*.94+(small?5:7)+(small?9:10)*1.45+(small?0:12+8*1.45);
 const actions=open?Math.max(268,Math.min(380,height-290-safe)):216;
 const body=open?Math.max(52,Math.min(164,height-506-safe)):0;
 return {actions,body,hero:height-padding-4*gap-44-brand-44-actions};
}
test('390x844 and320x568 preserve nonzero showroom car band when drawer opens',()=>{
 for(const [w,h] of [[390,844],[320,568]])for(const safe of [0,34])for(const open of [false,true]){
  const b=portrait(w,h,safe,open);assert(b.hero>44,`${w}x${h} safe${safe} open${open}: car band${b.hero}`);
  if(open){assert(b.body>=52);nearly(b.actions,46+b.body+56+52+44+18);}
 }
 nearly(portrait(320,568,0,true).hero,74.31);nearly(portrait(320,568,34,true).hero,50.31);
});
test('expanded short landscape hides no action and keeps showroom instead of overlapping wordmarks',()=>{
 assert.match(block,/\.home-view:has\(\.home-race-setup\[open\]\) \.home-brand\{visibility:hidden\}/);
 assert.match(block,/@media\(orientation:landscape\) and \(max-height:350px\)\{[\s\S]*\.home-view:has\(\.home-race-setup\[open\]\) \.home-masthead\{visibility:hidden\}/);
 assert(!/\.home-(?:ride|secondary|shortcuts|car-view|masthead)[^{]*\{[^}]*display:none/.test(block));
});
console.log(`Home integration layout: ${passed} passed, 0 failed — source/math only; native review pending`);
