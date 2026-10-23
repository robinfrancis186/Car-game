import {TIMING_POLICY as P} from '../shared/timing-policy.mjs';
const round=n=>Math.round(n*1000)/1000;
export const newInterruption=()=>({generation:0,phase:'active',count:0,totalMs:0,currentMs:0,beganAt:0,stableAt:0,completedMs:0});
export const interruptionView=s=>Object.fromEntries(['generation','phase','count','totalMs','currentMs'].map(k=>[k,s[k]]));
export function updateInterruption(s,now){
 if(s.phase!=='holding')return'active';
 const duration=Math.max(0,now-s.beganAt);s.currentMs=round(duration);s.totalMs=round(s.completedMs+duration);
 if(duration>P.maxInterruptionMs||s.count>P.maxInterruptions||s.totalMs>P.maxInterruptedMs){s.generation++;s.phase='active';s.currentMs=0;s.completedMs=s.totalMs;return'failed';}
 if(now-s.stableAt>=P.resyncStableMs){s.generation++;s.phase='active';s.currentMs=0;s.completedMs=s.totalMs;return'resumed';}
 return'holding';
}
export function beginInterruption(s,now,backlogMs){
 if(s.phase!=='holding'){s.generation++;s.count++;s.completedMs=s.totalMs;s.beganAt=now-backlogMs;s.phase='holding';}
 s.stableAt=now;
 return updateInterruption(s,now);
}
