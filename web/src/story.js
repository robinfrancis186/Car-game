/** Original, device-local three-event Coast story. No wallet or race-physics writes. */
const chapter = value => Object.freeze(value);
export const STORY_CHAPTERS = Object.freeze([
 chapter({id:'village-signal',number:1,title:'Village Signal',track:'coast',scenario:'time-attack',startS:165,endS:1265,
  intro:'A signal from the villages. One clear run.',
  briefing:'The coast crew is gathering before dusk. Carry the route signal from the village to the next meeting point.',
  objective:'Pass every checkpoint and finish before the clock expires.',
  completion:'The route is confirmed. The harbor crew is waiting for your next run.',
  shortObjective:'FINISH BEFORE TIME RUNS OUT'}),
 chapter({id:'harbor-line',number:2,title:'Harbor Line',track:'coast',scenario:'coast-sprint',startS:2200,endS:3350,
  intro:'Follow the harbor line. Bring the crew through.',
  briefing:'Three local drivers know the harbor approach. Keep your line through the flyover and bring the crew to the waterfront.',
  objective:'Complete the rival race through every checkpoint. Any finishing position qualifies.',
  completion:'You made the harbor run. Patrols are closing the road behind the crew.',
  shortObjective:'FINISH THE RIVAL RACE'}),
 chapter({id:'last-light',number:3,title:'Last Light',track:'coast',scenario:'hot-pursuit',startS:2200,endS:4350,
  intro:'Last light on the coast. Lose the patrol.',
  briefing:'One final run remains before the coast goes quiet. Reach the meeting point and lose the patrol without abandoning the car.',
  objective:'Pass every checkpoint, escape the patrol, and reach the safehouse.',
  completion:'The crew is together and the coast is clear. Replay any chapter or return to the open road.',
  shortObjective:'FINISH AND ESCAPE THE PATROL'})
]);
export const STORY_IDS = Object.freeze(STORY_CHAPTERS.map(c=>c.id));
const own = (object,key) => Object.prototype.hasOwnProperty.call(object,key);
const plain = value => !!value && typeof value==='object' && !Array.isArray(value) && [Object.prototype,null].includes(Object.getPrototypeOf(value));
const runIdValid = id => typeof id==='string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(id);
const clone = value => JSON.parse(JSON.stringify(value));
export const createStoryProgress = () => ({schemaVersion:1,completions:[],reducedMotion:false});
export const getStoryChapter = id => STORY_CHAPTERS.find(c=>c.id===id) || null;
/** Strict decoder: unsupported/corrupt progress is protected, never silently rewritten. */
export function validateStoryProgress(value){
 if(!plain(value)||value.schemaVersion!==1||typeof value.reducedMotion!=='boolean'||!Array.isArray(value.completions)||value.completions.length>3||Object.keys(value).some(k=>!['schemaVersion','completions','reducedMotion'].includes(k)))throw new Error('invalid-story-progress');
 const ids=new Set();
 for(let i=0;i<value.completions.length;i++){
  const row=value.completions[i];
  if(!plain(row)||Object.keys(row).some(k=>!['chapterId','runId','time','position'].includes(k))||row.chapterId!==STORY_IDS[i]||!runIdValid(row.runId)||ids.has(row.runId)||!Number.isFinite(row.time)||row.time<=0||row.time>86400||!Number.isInteger(row.position)||row.position<1||row.position>(STORY_CHAPTERS[i].scenario==='time-attack'?1:4))throw new Error('invalid-story-progress');
  ids.add(row.runId);
 }
 return clone(value);
}
const valid = progress => {try{return validateStoryProgress(progress);}catch{return null;}};
export function isChapterCompleted(progress,id){const p=valid(progress);return !!p && p.completions.some(c=>c.chapterId===id);}
export function isChapterUnlocked(progress,id){const p=valid(progress),index=STORY_IDS.indexOf(id);return !!p && index>=0 && index<=p.completions.length;}
export function nextStoryChapter(progress){const p=valid(progress);return p?STORY_CHAPTERS[p.completions.length]||null:null;}
/** The controller retains this context only for a selected story event, never a quick race. */
export function beginStoryRun(progress,chapterId,runId,trackId='coast'){
 const p=valid(progress),entry=getStoryChapter(chapterId);
 if(!p)return {ok:false,reason:'invalid-progress'};
 if(!entry)return {ok:false,reason:'unknown-chapter'};
 if(trackId!=='coast')return {ok:false,reason:'wrong-track'};
 if(!runIdValid(runId))return {ok:false,reason:'invalid-run-id'};
 if(!isChapterUnlocked(p,chapterId))return {ok:false,reason:'chapter-locked'};
 if(p.completions.some(c=>c.runId===runId))return {ok:false,reason:'run-id-reused'};
 const {scenario,startS,endS}=entry;
 return {ok:true,chapter:entry,run:Object.freeze({chapterId,runId,trackId:'coast',scenario,startS,endS})};
}
function contextValid(run,entry){return plain(run)&&entry&&run.trackId==='coast'&&runIdValid(run.runId)&&['scenario','startS','endS'].every(k=>own(run,k)&&run[k]===entry[k]);}
/** Result inspection is deliberately independent of coins: awardResult remains their only award path. */
export function storyResultQualifies(chapterId,result){
 const entry=getStoryChapter(chapterId);
 return !!entry && plain(result)&&result.state==='finished'&&result.scenario===entry.scenario&&Number.isFinite(result.time)&&result.time>0&&result.time<=86400&&Number.isInteger(result.position)&&result.position>=1&&result.position<=(entry.scenario==='time-attack'?1:4)&&(entry.scenario!=='hot-pursuit'||result.escaped===true);
}
export function completeStoryRun(progress,run,result){
 const p=valid(progress),entry=getStoryChapter(run?.chapterId);
 const reject=reason=>({ok:false,progress:progress,reason,newlyCompleted:false,nextChapter:nextStoryChapter(progress)});
 if(!p)return reject('invalid-progress');
 if(!contextValid(run,entry))return reject('invalid-run-context');
 if(!isChapterUnlocked(p,entry.id))return reject('chapter-locked');
 if(!storyResultQualifies(entry.id,result))return reject('objective-not-met');
 const used=p.completions.find(c=>c.runId===run.runId);
 if(used&&used.chapterId!==entry.id)return reject('run-id-reused');
 if(isChapterCompleted(p,entry.id))return {ok:true,progress:p,reason:used?'already-recorded':'replay',newlyCompleted:false,nextChapter:nextStoryChapter(p)};
 p.completions.push({chapterId:entry.id,runId:run.runId,time:result.time,position:result.position});
 return {ok:true,progress:p,reason:'chapter-completed',newlyCompleted:true,nextChapter:nextStoryChapter(p)};
}
