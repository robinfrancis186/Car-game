/** Device-local race records. No wallet, story, network, or name collection side effects. */
import {getStoryChapter} from './story.js';

export const LEADERBOARD_LIMIT = 200;
export const LEADERBOARD_NAME_LIMIT = 24;
const tracks = new Set(['coast','highlands']);
const modes = new Set(['time-attack','coast-sprint','hot-pursuit']);
const runIdValid = id => typeof id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(id);
const object = value => !!value && typeof value==='object' && !Array.isArray(value);
const clone = value => JSON.parse(JSON.stringify(value));
const candidateFields = ['runId','trackId','scenarioId','startS','endS','timeMs','storyChapterId','categoryKey'];

/** Names are plain text, not markup. Render the returned string with textContent. */
export function normalizeLeaderboardName(raw){
 if(typeof raw!=='string')return null;
 // Reject controls (including bidi overrides), invalid surrogates, and invisible
 // format characters. ZWJ is retained for ordinary joined emoji names.
 if(/[\p{C}\u2028\u2029]/u.test(raw.replace(/\u200d/g,'')))return null;
 const name=raw.normalize('NFC').trim();
 if(!name || [...name].length>LEADERBOARD_NAME_LIMIT || !/[\p{L}\p{N}\p{P}\p{S}]/u.test(name))return null;
 return name;
}

/** Exact actual route endpoints intentionally partition even small course edits. */
export function leaderboardCategoryKey(value){
 return JSON.stringify([value.trackId,value.scenarioId,value.startS,value.endS,value.storyChapterId??null]);
}

function routeValid(value){
 if(!tracks.has(value.trackId)||!modes.has(value.scenarioId)||!Number.isFinite(value.startS)||!Number.isFinite(value.endS)||value.startS<0||value.endS<=value.startS||value.endS>1e7)return false;
 if(value.storyChapterId!==null){
  const chapter=getStoryChapter(value.storyChapterId);
  if(!chapter||chapter.track!==value.trackId||chapter.scenario!==value.scenarioId)return false;
 }
 return true;
}

/** Call only from the controller's actual, uninterrupted GameModel finish path.
 * The time is the model result time, never a form field or a preview result.
 * Explore, aborted/failed sessions, and the experimental surface course cannot qualify.
 */
export function createLeaderboardCandidate(input={}){
 if(!object(input))return null;
 const {runId,trackId,scenarioId,startS,endS,timeSeconds,state,storyChapterId=null,experimentalSurface=false}=input;
 if(state!=='finished'||experimentalSurface||!runIdValid(runId)||!Number.isFinite(timeSeconds)||timeSeconds<=0||timeSeconds>86400)return null;
 const value={runId,trackId,scenarioId,startS,endS,timeMs:Math.max(1,Math.round(timeSeconds*1000)),storyChapterId};
 if(!routeValid(value))return null;
 value.categoryKey=leaderboardCategoryKey(value);
 return Object.freeze(value);
}

function checkedCandidate(value){
 if(!object(value)||Object.keys(value).length!==candidateFields.length||candidateFields.some(key=>!Object.hasOwn(value,key))||!runIdValid(value.runId)||!routeValid(value)||!Number.isSafeInteger(value.timeMs)||value.timeMs<1||value.timeMs>86400000||value.categoryKey!==leaderboardCategoryKey(value))throw new Error('invalid-leaderboard-result');
 return clone(value);
}

export const createLeaderboard = () => ({schemaVersion:1,entries:[]});

/** Strict decoder. A malformed or future-version file must not be overwritten. */
export function validateLeaderboard(value){
 if(!object(value)||value.schemaVersion!==1||Object.keys(value).length!==2||!Array.isArray(value.entries)||value.entries.length>LEADERBOARD_LIMIT)throw new Error('invalid-leaderboard');
 const ids=new Set(),entries=[];
 for(const row of value.entries){
  if(!object(row)||Object.keys(row).length!==candidateFields.length+1||!Object.hasOwn(row,'name')||normalizeLeaderboardName(row.name)!==row.name||ids.has(row.runId))throw new Error('invalid-leaderboard');
  const {name,...candidate}=row;
  entries.push({...checkedCandidate(candidate),name});ids.add(row.runId);
 }
 return {schemaVersion:1,entries};
}

/** Competition ranking: equal displayed milliseconds share rank (1, 1, 3).
 * Run IDs are a deterministic, locale-independent display order for ties.
 */
export function rankLeaderboard(entries,category){
 const key=typeof category==='string'?category:category?leaderboardCategoryKey(category):null;
 // With no selected category, return independently ranked groups, never a
 // misleading global time rank across different routes or game modes.
 if(key===null)return [...new Set(entries.map(row=>row.categoryKey))].sort().flatMap(group=>rankLeaderboard(entries,group));
 const rows=entries.filter(row=>row.categoryKey===key).map(clone).sort((a,b)=>a.timeMs-b.timeMs||(a.runId<b.runId?-1:a.runId>b.runId?1:0));
 let rank=0;
 return rows.map((row,index)=>{if(index===0||row.timeMs!==rows[index-1].timeMs)rank=index+1;return {...row,rank};});
}

/** Pure append, invoked only by the player's explicit Save button. */
export function addLeaderboardResult(board,name,candidate){
 const current=validateLeaderboard(board);
 let checked;try{checked=checkedCandidate(candidate);}catch{return {ok:false,reason:'invalid-result',board:current};}
 // A repeated click can neither rename nor alter a previously saved run.
 const prior=current.entries.find(row=>row.runId===checked.runId);
 if(prior)return {ok:true,reason:'already-saved',duplicate:true,board:current,entry:clone(prior),rank:rankLeaderboard(current.entries,prior).find(row=>row.runId===prior.runId).rank};
 const normalized=normalizeLeaderboardName(name);
 if(normalized===null)return {ok:false,reason:'invalid-name',board:current};
 if(current.entries.length>=LEADERBOARD_LIMIT)return {ok:false,reason:'capacity',board:current};
 const entry={...checked,name:normalized};current.entries.push(entry);
 return {ok:true,reason:'saved',duplicate:false,board:current,entry:clone(entry),rank:rankLeaderboard(current.entries,entry).find(row=>row.runId===entry.runId).rank};
}
