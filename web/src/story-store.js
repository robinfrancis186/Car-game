/** Separate story namespace: no garage reads, writes, deletes, migration, or coin awards. */
import {createStoryProgress,validateStoryProgress} from './story.js';
export const STORY_KEY='malabar-story-v13';
const notices={unavailable:'Story storage unavailable · progress lasts this session only',unreadable:'Saved story unreadable or unsupported · protected; session only',conflict:'Story changed in another tab · reload to use it; session only'};
export function createStoryStore(getStorage=()=>globalThis.localStorage){
 let storage,progress=createStoryProgress(),expected=null,writable=false,warning='';
 const stop=kind=>{writable=false;warning=notices[kind];return false;};
 try{
  storage=getStorage();expected=storage.getItem(STORY_KEY);
  if(expected!==null){try{progress=validateStoryProgress(JSON.parse(expected));}catch{stop('unreadable');return api();}}
  writable=true;
 }catch{stop('unavailable');}
 function save(next){
  let checked;try{checked=validateStoryProgress(next);}catch{return false;}
  // Reject stale/rollback calls even within one tab; only immutable prefix extension is legal.
  if(checked.completions.length<progress.completions.length||progress.completions.some((row,i)=>JSON.stringify(row)!==JSON.stringify(checked.completions[i])))return false;
  progress=checked;
  if(!writable)return false;
  try{
   if(storage.getItem(STORY_KEY)!==expected)return stop('conflict');
   const raw=JSON.stringify(checked);storage.setItem(STORY_KEY,raw);
   if(storage.getItem(STORY_KEY)!==raw)return stop('conflict');
   expected=raw;warning='';return true;
  }catch{return stop('unavailable');}
 }
 function api(){return {get progress(){return validateStoryProgress(progress);},get warning(){return warning;},get persistent(){return writable;},save};}
 return api();
}
