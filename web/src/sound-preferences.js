/** Independent sound settings; never reads or writes garage, Story or rewards. */
export const SOUND_KEY='malabar-sound-v1';
const valid=x=>x&&x.version===1&&typeof x.enabled==='boolean'&&Number.isFinite(x.volume)&&x.volume>=0&&x.volume<=1;
export function createSoundPreferences(getStorage=()=>globalThis.localStorage){
 let value={version:1,enabled:true,volume:1},storage,expected=null,writable=false,warning='';
 const stop=message=>{writable=false;warning=message;return false;};
 try{storage=getStorage();expected=storage.getItem(SOUND_KEY);if(expected!==null){const saved=JSON.parse(expected);if(!valid(saved))throw Error('unsupported');value={...saved};}writable=true;}catch{stop('Sound settings unavailable or unsupported · session only');}
 return {get value(){return {...value};},get warning(){return warning;},save(next){
  if(!valid(next))return false;value={version:1,enabled:next.enabled,volume:next.volume};if(!writable)return false;
  try{if(storage.getItem(SOUND_KEY)!==expected)return stop('Sound settings changed in another tab · session only');const raw=JSON.stringify(value);storage.setItem(SOUND_KEY,raw);if(storage.getItem(SOUND_KEY)!==raw)return stop('Sound settings changed in another tab · session only');expected=raw;return true;}catch{return stop('Sound settings unavailable · session only');}
 }};
}
