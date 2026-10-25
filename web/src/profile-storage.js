/** V13 storage boundary; migrate V12 once without exposing new braking levels to old tabs. No legacy writes/deletes; exact backup is write-once. */
import {createProfile,validateProfile,CAR_IDS,UPGRADE_CATALOG} from './garage.js';
export const PROFILE_KEY='malabar-garage-v13';
export const LEGACY_PROFILE_KEY='malabar-garage-v12';
export const OLDEST_PROFILE_KEY='malabar-garage-v1';
export const LEGACY_BACKUP_KEY='malabar-garage-v13-legacy-backup';
const unavailable='Storage unavailable · changes last this session only';
const unreadable='Saved data unreadable or unsupported · protected; session only';
const conflict='Save changed in another tab · reload to use it; session only';
const object=v=>!!v&&typeof v==='object'&&!Array.isArray(v);
function decode(raw,legacy=false){
 const p=JSON.parse(raw);
 if(!object(p)||(!legacy&&p.schemaVersion!==2)||(p.schemaVersion!==undefined&&![1,2].includes(p.schemaVersion))||!Number.isInteger(p.credits)||p.credits<0||p.credits>999999)throw Error(unreadable);
 if(p.cars!==undefined){if(!object(p.cars))throw Error(unreadable);for(const[id,levels]of Object.entries(p.cars)){if(!CAR_IDS.includes(id)||!object(levels))throw Error(unreadable);for(const[key,v]of Object.entries(levels))if(!Object.hasOwn(UPGRADE_CATALOG,key)||!Number.isInteger(v)||v<0||v>3)throw Error(unreadable);}}
 if(p.ownedCars!==undefined&&(!Array.isArray(p.ownedCars)||p.ownedCars.some(id=>!CAR_IDS.includes(id))))throw Error(unreadable);
 if(p.selectedCar!==undefined&&(!CAR_IDS.includes(p.selectedCar)||!['red','silver',...(p.ownedCars||[])].includes(p.selectedCar)))throw Error(unreadable);
 if(p.awardedRuns!==undefined&&(!Array.isArray(p.awardedRuns)||p.awardedRuns.some(id=>typeof id!=='string'||!(/^[A-Za-z0-9_.:-]{1,128}$/).test(id))))throw Error(unreadable);
 return validateProfile(p);
}
export function createProfileStore(getStorage=()=>globalThis.localStorage){
 let storage,profile=createProfile(),warning='',writable=false,expected=null;
 const stop=message=>{writable=false;warning=message;return false;};
 const save=next=>{if(!writable)return false;try{const serialized=JSON.stringify(decode(JSON.stringify(next)));if(storage.getItem(PROFILE_KEY)!==expected)return stop(conflict);storage.setItem(PROFILE_KEY,serialized);if(storage.getItem(PROFILE_KEY)!==serialized)return stop(conflict);expected=serialized;profile=JSON.parse(serialized);warning='';return true;}catch(error){return stop(error?.message===unreadable?unreadable:unavailable);}};
 try{storage=getStorage();const current=storage.getItem(PROFILE_KEY);if(current!==null){profile=decode(current);expected=current;writable=true;}else{const backup=storage.getItem(LEGACY_BACKUP_KEY),raw=backup!==null?backup:(storage.getItem(LEGACY_PROFILE_KEY)??storage.getItem(OLDEST_PROFILE_KEY));if(raw!==null){profile=decode(raw,true);if(backup===null){if(storage.getItem(LEGACY_BACKUP_KEY)!==null)throw Error(conflict);storage.setItem(LEGACY_BACKUP_KEY,raw);if(storage.getItem(LEGACY_BACKUP_KEY)!==raw)throw Error(conflict);}}writable=true;save(profile);}}
 catch(error){stop([unreadable,conflict].includes(error?.message)?error.message:error instanceof SyntaxError?unreadable:unavailable);}
 return{get profile(){return profile;},get warning(){return warning;},get persistent(){return writable;},save};
}
