/** Startup only. Exercise and discard real stock physics before accepting any rooms.
 * This does not advance live clocks, relax overload limits or predict player results.
 */
import {performance} from 'node:perf_hooks';
import {setImmediate as yieldLoop} from 'node:timers/promises';
import {RaceWorld} from '../shared/world.mjs';
export const WARMUP_STEPS=600;
export async function warmRuntime(data){
 const began=performance.now(),cpu=process.cpuUsage(),world=new RaceWorld(data),ids=['warmup-a','warmup-b'];
 for(const id of ids)world.add(id);
 let maxBatchMs=0;
 for(let offset=0;offset<WARMUP_STEPS;offset+=12){
  const batch=performance.now();
  for(let i=offset;i<Math.min(offset+12,WARMUP_STEPS);i++){
   const inputs=new Map();
   for(const id of ids){const p=world.snapshot(id),q=world.model.sampleRoute(p.s+7),error=Math.atan2(Math.sin(q.heading-p.heading),Math.cos(q.heading-p.heading));inputs.set(id,{throttle:p.speed<13?1:0,steer:Math.max(-1,Math.min(1,error*2)),brake:p.speed>15,boost:false,recover:false});}
   world.step(inputs);
   if(i%3===0)JSON.stringify(ids.map(id=>world.snapshot(id)));
  }
  maxBatchMs=Math.max(maxBatchMs,performance.now()-batch);
  if(performance.now()-began>30000)throw Error('RUNTIME_WARMUP_TIMEOUT');
  await yieldLoop();
 }
 const used=process.cpuUsage(cpu),round=n=>Math.round(n*1000)/1000;
 return Object.freeze({event:'runtime-warmup-complete',steps:WARMUP_STEPS,drivers:ids.length,wallMs:round(performance.now()-began),cpuMs:round((used.user+used.system)/1000),maxBatchMs:round(maxBatchMs)});
}
