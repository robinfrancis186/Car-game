/** Source/cascade contract and dock geometry arithmetic. Not browser pixel acceptance. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {transformSync} from 'esbuild';
const css=readFileSync(new URL('../src/style.css',import.meta.url),'utf8');
const normalized=css.replace(/\s+/g,'');
let passed=0;
const test=(name,fn)=>{fn();passed++;console.log('PASS',name);};
const roles=css.slice(css.indexOf('/* Shared control roles,'));
const token=name=>{const values=[...css.matchAll(new RegExp(`--${name}:([^;}]*)`,'g'))];assert.equal(values.length,1,`one definition of ${name}`);return values[0][1].trim();};
test('stylesheet parses without CSS syntax warnings',()=>{
 const parsed=transformSync(css,{loader:'css'});assert.deepEqual(parsed.warnings,[]);assert(parsed.code.length>0);
});
test('one reference-derived primary gradient and one secondary gradient family',()=>{
 assert.equal(token('control-primary-bg'),'linear-gradient(110deg,#ff9b51,#ff8a49)');assert.match(token('control-primary-hover-bg'),/^linear-gradient/);
 assert.match(token('control-secondary-bg'),/^linear-gradient/);assert.match(token('control-secondary-hover-bg'),/^linear-gradient/);
 for(const name of ['primary-border','primary-color','secondary-border','secondary-color','selected-bg','selected-border','selected-shadow','disabled-bg','disabled-color','disabled-border'])token('control-'+name);
 assert.equal(token('control-radius'),'8px');assert.equal(token('control-target'),'44px');
});
test('generic Play Story Pause and Results primary use the same role as Home',()=>{
 assert.match(css,/\.primary-button\{background:var\(--control-primary-bg\);color:var\(--control-primary-color\);border-color:var\(--control-primary-border\)/);
 assert.match(css,/\.home-primary\{background:var\(--control-primary-bg\);border-color:var\(--control-primary-border\)/);
 assert(!css.includes('.primary-button{background:var(--orange)'));assert(!/\.result-card \.primary-button\{/.test(css),'Results must not define a separate primary palette');
 assert.match(roles,/\.primary-button,\.home-primary\{border-radius:var\(--control-radius\)\}/);
});
test('secondary selectors cover existing menus utilities Story and Workshop',()=>{
 const group=roles.match(/:is\(([^\n]+)\)\{\n background:var\(--control-secondary-bg\);border-color:var\(--control-secondary-border\)/)?.[1];assert(group);
 for(const selector of ['.text-button','.utility-button','.garage-save button','.home-tile:not(.home-primary)','.track-choice','.car-choice','.scenario-tab','.story-chapter','.close-button','.garage-back','.garage-orbit-reset','.garage-tabs button','.upgrade-row>button','.collection-filters button','.collection-action'])assert(group.includes(selector),selector);
});
test('selection hover focus and disabled states are shared roles rather than screen palettes',()=>{
 assert(roles.includes('background:var(--control-secondary-hover-bg)'));assert(roles.includes('background:var(--control-selected-bg)'));assert(roles.includes('box-shadow:var(--control-selected-shadow)'));
 assert(roles.includes('background:var(--control-disabled-bg)'));assert(roles.includes('color:var(--control-disabled-color)'));assert(roles.includes('box-shadow:none;cursor:not-allowed'));
 assert(css.includes('outline:2px solid var(--control-focus)'));assert(css.includes('.primary-button:hover:not(:disabled){background:var(--control-primary-hover-bg)}'));
});
test('leaderboard no longer has a bespoke Home row or flat input theme',()=>{
 assert(!css.includes('.home-leaderboard'));assert(!css.includes('#settings-button'));assert(!css.includes('#10242bdb'));
 const input=css.match(/\.leaderboard-entry input\{([^}]*)\}/)?.[1];assert(input?.includes('background:var(--control-secondary-bg)'));assert(input.includes('border-radius:var(--control-radius)'));assert(input.includes('min-height:44px'));
 assert(!/\.leaderboard-entry-controls \.primary-button\{[^}]*background:/.test(css));
});
test('generic modal Story shell and leaderboard inherit the reference panel palette',()=>{
 assert.equal(token('panel-bg'),'linear-gradient(145deg,#172a35f2,#07131bf5)');
 for(const selector of ['.modal-panel','.story-shell']){const body=css.match(new RegExp(selector.replaceAll('.','\\.')+'\\{([^}]*)\\}'))?.[1];assert(body?.includes('background:var(--panel-bg)'),selector);assert(body.includes('border:1px solid var(--panel-border)'));}
});
test('44px minimum survives portrait landscape and Home utility overrides',()=>{
 assert(roles.includes(':is(.home-view,.garage-view) .utilities .utility-button{min-width:var(--control-target);min-height:var(--control-target)}'));
 assert(roles.includes('.collection-filters button){min-height:var(--control-target)}'));
 assert(normalized.includes('.home-view.home-shortcuts.home-tile{min-height:44px;'));
});
test('confirmed driving HUD containment remains unchanged',()=>{
 assert.match(css,/\.vehicle-bars\{[^}]*width:232px;max-width:100%;/);
});

const dock=css.slice(css.indexOf('/* Dock-aware scroll bounds:'),css.indexOf('/* R3.5 one showroom Home flow.'));
const compact=dock.replace(/\s+/g,'');
test('both scroll panels use the exact dock metrics rather than independent percentages',()=>{
 assert(compact.includes('.main-navigation{height:var(--dock-height);bottom:var(--dock-bottom)}'));
 assert(compact.includes('.garage-view#garage-inspection,.garage-view.garage-collection-panel{bottom:calc(var(--dock-height)+var(--dock-bottom)+var(--dock-gap));overflow-y:auto;overscroll-behavior:contain;scroll-padding-bottom:var(--dock-gap);}'));
 assert(!/display:none|visibility:hidden|z-index:/.test(dock),'fix must reserve and scroll content, not hide or layer over it');
});
test('dock variables preserve existing desktop and compact viewport dimensions',()=>{
 assert(compact.includes(':root{--dock-height:61px;--dock-bottom:calc(2.5vh+var(--safe-bottom));--dock-gap:12px}'));
 assert(compact.includes('@media(orientation:portrait){:root{--dock-height:58px;--dock-bottom:calc(16px+var(--safe-bottom))}}'));
 assert(compact.includes('@media(orientation:portrait)and(max-height:650px){:root{--dock-height:53px;--dock-bottom:calc(14px+var(--safe-bottom))}}'));
 assert(compact.includes('@media(orientation:landscape)and(max-height:520px){:root{--dock-height:45px;--dock-bottom:calc(13px+var(--safe-bottom))}}'));
});
// Arithmetic mirrors only the explicitly asserted CSS metrics above. It does
// not substitute for browser bounding-box / clipping checks after deployment.
function bounds(width,height,safe=0){
 let dockHeight=61,bottom=height*.025+safe;
 if(height>=width){dockHeight=height<=650?53:58;bottom=(height<=650?14:16)+safe;}
 else if(height<=520){dockHeight=45;bottom=13+safe;}
 return {dockTop:height-bottom-dockHeight,contentBottom:height-bottom-dockHeight-12};
}
test('real 1222x619 evidence is reproduced mathematically then cleared by 12px',()=>{
 const measured=bounds(1222,619);assert(Math.abs(measured.dockTop-542.525)<1e-9);
 assert(619*(1-.115)>measured.dockTop,'old collection11.5% inset overlaps measured dock');assert(619*(1-.12)>measured.dockTop,'old inspection12% inset overlaps measured dock');
 assert(Math.abs(measured.contentBottom-530.525)<1e-9);assert.equal(measured.dockTop-measured.contentBottom,12);
});
test('desktop phone compact portrait and landscape keep 12px dock clearance including safe areas',()=>{
 for(const [w,h] of [[1706,922],[1222,619],[1024,768],[390,844],[320,568],[844,390],[667,375]])for(const safe of [0,34]){const b=bounds(w,h,safe);assert.equal(b.dockTop-b.contentBottom,12);assert(b.contentBottom>0);}
});
console.log(`UI theme/source and dock math: ${passed} passed, 0 failed (browser pixels not tested)`);
