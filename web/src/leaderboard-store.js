/** Isolated namespace: never reads, writes, migrates, or deletes other game saves. */
import {createLeaderboard,validateLeaderboard,addLeaderboardResult} from './leaderboard.js';
export const LEADERBOARD_KEY='malabar-leaderboard-v1';
const notices={
 unavailable:'Leaderboard storage unavailable · new records last this session only',
 unreadable:'Saved leaderboard unreadable or unsupported · protected; new records last this session only',
 conflict:'Leaderboard changed in another tab · saved data protected; new records last this session only'
};

export function createLeaderboardStore(getStorage=()=>globalThis.localStorage){
 let storage,board=createLeaderboard(),expected=null,writable=false,warning='';
 const stop=kind=>{writable=false;warning=notices[kind];};
 try{
  storage=getStorage();expected=storage.getItem(LEADERBOARD_KEY);
  if(expected!==null){
   try{board=validateLeaderboard(JSON.parse(expected));}
   catch{stop('unreadable');return api();}
  }
  writable=true;
 }catch{stop('unavailable');}

 function save(name,candidate){
  const result=addLeaderboardResult(board,name,candidate);
  if(!result.ok)return {ok:false,reason:result.reason,persistent:writable,duplicate:false};
  board=result.board;
  if(!result.duplicate&&writable){
   try{
    // Optimistic compare protects data changed by another tab before this save.
    if(storage.getItem(LEADERBOARD_KEY)!==expected)stop('conflict');
    else{
     const raw=JSON.stringify(board);storage.setItem(LEADERBOARD_KEY,raw);
     if(storage.getItem(LEADERBOARD_KEY)!==raw)stop('conflict');
     else{expected=raw;warning='';}
    }
   }catch{stop('unavailable');}
  }
  return {ok:true,reason:result.reason,entry:result.entry,rank:result.rank,duplicate:result.duplicate,persistent:writable};
 }
 function api(){return {
  get entries(){return validateLeaderboard(board).entries;},
  get warning(){return warning;},
  get persistent(){return writable;},
  save
 };}
 return api();
}
