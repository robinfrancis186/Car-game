/** Bounded local CPU evidence, not a provider capacity or real-time guarantee. */
import {performance} from 'node:perf_hooks';
import {RaceWorld} from '../shared/world.mjs';
import {loadData} from '../server/data.mjs';
import {warmRuntime} from '../server/warmup.mjs';
import {newInterruption,beginInterruption,updateInterruption} from '../server/interruption.mjs';
const round=n=>Math.round(n*1000)/1000,data=loadData(),startup=await warmRuntime(data),world=new RaceWorld(data),ids=['cpu-a','cpu-b'];
for(const id of ids)world.add(id);
const cpu=process.cpuUsage(),began=performance.now();let maxStepMs=0;
for(let tick=0;tick<600;tick++){
 const start=performance.now(),inputs=new Map();
 for(const id of ids){const p=world.snapshot(id),q=world.model.sampleRoute(p.s+7),error=Math.atan2(Math.sin(q.heading-p.heading),Math.cos(q.heading-p.heading));inputs.set(id,{throttle:p.speed<13?1:0,steer:Math.max(-1,Math.min(1,error*2)),brake:p.speed>15,boost:false,recover:false});}
 world.step(inputs);if(tick%3===0)JSON.stringify(ids.map(id=>world.snapshot(id)));maxStepMs=Math.max(maxStepMs,performance.now()-start);
}
const used=process.cpuUsage(cpu),cpuMs=(used.user+used.system)/1000,wallMs=performance.now()-began,s=newInterruption();beginInterruption(s,1000,484);
const holdCpu=process.cpuUsage(),holdWall=performance.now();for(let i=0;i<100000;i++)updateInterruption(s,1000+(i%400));const holdUsed=process.cpuUsage(holdCpu);
console.log(JSON.stringify({scope:'Single bounded local sample. Same V11.1 physics, 2 stock drivers, 600 fixed steps/10 simulated seconds, 20Hz serialization; no sockets, GPU, host quota or provider timing emulation. Hold cost excludes serialization.',startup,simulation:{steps:600,drivers:2,cpuMs:round(cpuMs),wallMs:round(wallMs),cpuMsPerSimulatedSecond:round(cpuMs/10),maxStepMs:round(maxStepMs)},holdingPolicy:{checks:100000,cpuMs:round((holdUsed.user+holdUsed.system)/1000),wallMs:round(performance.now()-holdWall),worldSteps:0},providerConstraint:'Observed Render Free CPU limit 0.15 core; roughly 150 CPU-ms per wall-second available on average. This workspace measurement does not establish provider capacity. Bounded interruption may recover isolated stalls but sustained quota starvation still ends honestly.'},null,2));
