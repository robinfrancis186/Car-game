/** Synthetic controller for static previews only. It cannot validate CSS, native details,
 * keyboard default actions, WebGL, persisted results or actual race admission. */
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {CAR_CATALOG} from '../../web/src/garage.js';
import {SCENARIOS} from '../../web/src/gameplay.js';

export function smokePreview({html,source,css,main,worlds}){
 assert(html.includes('UI PREVIEW · ORIGINAL MODEL IMAGES · NO GAMEPLAY / NO 3D GARAGE'));
 assert(!html.includes('src="./src/main.js"'));assert(!html.includes('type="importmap"'));
 const ids=[...source.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length,'Unique game IDs');
 for(const id of ['settings-button','home-menu','garage-open','event-content','event-tabs','start-button','start-label','event-car-choices','event-car-label'])assert(!ids.includes(id),'Removed duplicate control absent: '+id);
 assert.equal(ids.filter(id=>id==='home-ride').length,1,'Exactly one Home launch');
 for(const id of ['home-race-setup','home-setup-summary','home-setup-label','district-start','home-ride'])assert(ids.includes(id),'Required single-Home control: '+id);
 assert(/<details\b[^>]*id="home-race-setup"/.test(source),'Setup uses native details');
 const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);assert.equal(scripts.length,1);
 const queries=['?view=hud&track=surface-test&notice=end','?view=help&track=surface-test','?view=home','?view=events','?view=setup','?view=owned','?view=shop',...Object.keys(CAR_CATALOG).flatMap(id=>['?view=workshop&car='+id,'?view=workshop&car='+id+'&coins='+CAR_CATALOG[id].price]),'?view=hud&mode=time-attack','?view=help&diagnostics=1','?view=pause','?view=result','?view=result-timeout','?view=result-busted','?view=result-failure','?view=loading','?view=error-webgl','?view=error-assets','?view=shop&owned=all','?view=workshop&upgrades=max','?view=workshop&upgrades=one&coins=580','?view=home&save=protected','?view=home&save=blocked','?view=story','?view=story&chapters=3&chapter=last-light','?view=cinematic-intro','?view=cinematic-finish','?view=result&story=1',...['coast','highlands'].flatMap(track=>SCENARIOS.flatMap(mode=>['home','setup'].map(view=>`?view=${view}&track=${track}&mode=${mode.id}`))),...SCENARIOS.map(mode=>`?view=setup&track=surface-test&mode=${mode.id}`),'?track=unknown&mode=unknown','?story=village-signal','?track=highlands&story=village-signal','?story=invalid',...Object.entries(worlds).flatMap(([track,world])=>world.explore_starts.map(d=>`?view=setup&track=${track}&mode=free-drive&start-${track}=${d.s}`))];
 for(const query of queries){
  const elements=[],byId=new Map(),events=new Map();let context;
  class Element{
   constructor(tag,attrs={}){this.tagName=tag;this.id=attrs.id||'';this.attrs=attrs;this.dataset={};for(const[k,v]of Object.entries(attrs))if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=v;this.hidden=Object.hasOwn(attrs,'hidden');this.open=Object.hasOwn(attrs,'open');this.style={setProperty(){}};this.classList={toggle(){},add(){},remove(){}};this.textContent='';this.width=240;this.height=240;this.children=[];this.value='';this.events={};}
   addEventListener(n,f){this.events[n]=f;}querySelector(){return this.label??=new Element('span');}setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}replaceChildren(){this.children=[];this.value='';}appendChild(e){this.children.push(e);if(!this.value)this.value=String(e.value);}getContext(){return new Proxy({},{get:()=>()=>{}});}getBoundingClientRect(){return{height:100,width:100,left:0,top:0,right:100,bottom:100};}focus(){context.document.activeElement=this;}blur(){if(context.document.activeElement===this)context.document.activeElement=null;}click(){if(!this.disabled)this.events.click?.({target:this});}
  }
  for(const m of source.matchAll(/<([a-z][\w-]*)\b([^>]*)>/gi)){const attrs={};for(const a of m[2].matchAll(/([\w-]+)(?:="([^"]*)")?/g))attrs[a[1]]=a[2]??'';const e=new Element(m[1],attrs);elements.push(e);if(e.id)byId.set(e.id,e);}
  const queryAll=s=>{const m=s.match(/^\[data-([\w-]+)(?:="([^"]+)")?\]$/);if(!m)return[];const k=m[1].replace(/-([a-z])/g,(_,c)=>c.toUpperCase());return elements.filter(e=>Object.hasOwn(e.dataset,k)&&(!m[2]||e.dataset[k]===m[2]));};
  const forbidden=()=>{throw Error('Preview must never access saves or change history');};
  context={console,URLSearchParams,location:{search:query},Math,Number,Set,Object,Array,matchMedia:()=>({matches:false}),addEventListener:(n,f)=>events.set(n,f),document:{getElementById:id=>byId.get(id)||elements.find(e=>e.id===id),querySelectorAll:queryAll,querySelector:s=>queryAll(s)[0],createElement:t=>{const e=new Element(t);elements.push(e);return e;},body:new Element('body'),documentElement:new Element('html')},localStorage:{getItem:forbidden,setItem:forbidden,removeItem:forbidden},history:{replaceState:forbidden,pushState:forbidden}};context.window=context;vm.createContext(context);vm.runInContext(scripts[0],context);
  const preview=context.__UI_PREVIEW__,params=new URLSearchParams(query),car=params.get('car'),get=id=>byId.get(id),click=id=>{assert.equal(typeof get(id)?.events.click,'function','Required preview action: '+id);get(id).click();},key=(code,{target=null,repeat=false}={})=>{let prevented=false;events.get('keydown')({code,target,repeat,preventDefault(){prevented=true;}});return prevented;};
  assert(preview);assert.equal(preview.metadata.revision,'R3.5-single-home');
  for(const [name,value]of Object.entries({html_sha256:source,css_sha256:css,main_sha256:main}))assert.equal(preview.metadata[name],createHash('sha256').update(value).digest('hex'));
  assert.deepEqual([...preview.metadata.catalog_ids],Object.keys(CAR_CATALOG));
  assert.equal(get('quality-button').getAttribute('aria-label'),'VISUALS HIGH · Interface preview only');
  assert.equal(get('loading').hidden,!/view=(loading|error-webgl|error-assets)/.test(query));
  for(const id of ['home-leaderboard','result-leaderboard']){assert.equal(get(id).disabled,true);assert.equal(get(id).getAttribute('aria-label'),'Leaderboard available in the game — interface preview only');}assert.equal(get('leaderboard-entry').hidden,true);
  if(car){const c=CAR_CATALOG[car];assert.equal(get('garage-car-name').textContent,c.name);assert.equal(get('garage-ownership').textContent,c.price?'LOCKED':'OWNED');if(c.price)assert.equal(get('garage-buy-car').disabled,Number(params.get('coins'))<c.price);}
  if(query.includes('diagnostics'))assert.equal(get('diagnostics-panel').hidden,false);
  if(query==='?view=shop&owned=all')assert(get('collection-scroll-hint').hidden);
  if(query==='?view=workshop&upgrades=one&coins=580')assert.equal(get('buy-speed').textContent,'20 more coins');
  if(preview.view==='home'){
   assert.equal(get('main-navigation').hidden,true,'Setup stays on Home, without a second dock/screen');assert.equal(get('home-leaderboard').hidden,false);
   assert.equal(get('home-race-setup').open,['events','setup'].includes(params.get('view')));
   const surface=params.get('track')==='surface-test',mode=surface?'free-drive':SCENARIOS.some(s=>s.id===params.get('mode'))?params.get('mode'):'coast-sprint';
   assert.equal(get('district-start-wrap').hidden,mode!=='free-drive');
   assert.equal(queryAll('[data-scenario]').find(b=>b.dataset.scenario===mode).getAttribute('aria-pressed'),'true');
   if(surface){assert(get('home-setup-label').textContent.includes('SOLO TEST'));for(const b of queryAll('[data-scenario]'))assert.equal(b.disabled,b.dataset.scenario!=='free-drive');}
   if(params.has('track')&&worlds[params.get('track')]){const t=params.get('track'),d=worlds[t].explore_starts.find(d=>d.s===Number(params.get('start-'+t)));if(params.has('start-'+t)&&d){assert.equal(get('district-start').value,String(d.s));assert(get('home-setup-label').textContent.includes(d.name));}}
  }
  if(query==='?view=pause'){click('help-audio-button');for(const id of ['audio-button','help-audio-button'])assert.equal(get(id).getAttribute('aria-pressed'),'false');click('audio-button');for(const id of ['audio-button','help-audio-button'])assert.equal(get(id).getAttribute('aria-pressed'),'true');}
  if(params.has('story')&&params.get('story')==='village-signal')assert.equal(preview.view,'story','Valid Story URL opens synthetic Story view, not quick play');
  if(query==='?view=home')for(let repeat=0;repeat<2;repeat++){
   click('home-garage');assert.equal(preview.view,'owned');click('garage-tab-garage');assert.equal(preview.view,'workshop');click('nav-garage');assert.equal(preview.view,'owned');
   click('nav-events');assert.equal(preview.view,'home');assert(get('home-race-setup').open);assert(get('main-navigation').hidden);
   const summary={closest:s=>s.includes('summary')?summary:null};for(const code of ['Enter','Space']){assert.equal(key(code,{target:summary}),false,'Let native summary default toggle, do not intercept/start');assert.equal(preview.view,'home');}
   key('Enter',{repeat:true});assert.equal(preview.view,'home','Repeated Enter never launches');
   click('help-button');assert.equal(preview.view,'help');click('help-close');assert.equal(preview.view,'home');assert(get('home-race-setup').open,'Help preserves expanded setup');
   assert.equal(key('Escape'),false);assert.equal(get('home-race-setup').open,true,'No invented Escape-to-collapse behavior');assert.equal(preview.view,'home');click('home-garage');click('nav-home');assert.equal(get('home-race-setup').open,true,'Returning Home preserves native disclosure state');get('home-race-setup').open=false;get('home-race-setup').events.toggle(); // Explicit fixture state, not a native default-action simulation.
   click('home-locations');assert(get('home-race-setup').open);assert.equal(get('district-start-wrap').hidden,false);assert.equal(preview.view,'maps');assert.equal(get('maps-panel').hidden,false);assert.equal(context.document.activeElement,get('maps-close'));click('home-ride');assert.equal(preview.view,'maps','Maps does not launch a run');click('maps-close');assert.equal(get('maps-panel').hidden,true);assert.equal(context.document.activeElement,get('home-locations'));
   const option=get('district-start').children.at(-1);get('district-start').value=String(option.value);get('district-start').events.change();assert(get('home-setup-label').textContent.includes(option.textContent));
   click('home-ride');assert.equal(preview.view,'hud','One Home Play directly enters synthetic HUD');assert.equal(get('home-race-setup').open,false);click('home-ride');assert.equal(preview.view,'hud','Hidden Play cannot re-enter menu flow');
   click('pause-button');assert.equal(preview.view,'pause');click('menu-button');assert.equal(preview.view,'home');
   key('Enter');assert.equal(preview.view,'hud','Unfocused Enter follows the sole Home launch');click('pause-button');click('menu-button');
  }
  console.log('PASS isolated exact-source preview boot:',query);
 }
 assert(css.includes('.collection-card img{width:100%;height:auto;'));
 for(const guard of ['home: duplicate launch/event screen remains','home: closed setup exposes','home: duplicate bottom navigation is visible','home: car caption overlaps actions','hud: speed overlaps ','header title/back/wallet/utilities overlap','touchTargetChecks','auditReachablePart(button,button.id,page)',"auditReachablePart(footer,'collection footer '+b.dataset.car,page,b)"])assert(html.includes(guard),'Required browser audit guard: '+guard);
 assert(!html.includes("$('start-button')"));assert(!html.includes('projectedCarBands'),'Obsolete roadside projection is not evidence for showroom layout');
 console.log(`PASS ${queries.length} static preview states; repeated Home/setup/Map/Help/Story navigation, exact source identity and no storage/history access. Native details/default keyboard, CSS, gameplay and GPU remain unverified here.`);
 return {queries:queries.length};
}
