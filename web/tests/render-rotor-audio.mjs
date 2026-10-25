// Optional actual-synthesis signal check. Synthesized test, NOT gameplay/listening.
// Dependency kept outside the game: web-audio-engine@0.13.4 (MIT).
// npm install --prefix /tmp/kerala-audio-tools web-audio-engine@0.13.4 --ignore-scripts
// node tests/render-rotor-audio.mjs [--wav] writes only /tmp artifacts.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {GameAudio} from '../src/audio.js';
const require=createRequire(import.meta.url),{RenderingAudioContext}=require(process.env.AUDIO_ENGINE||'/tmp/kerala-audio-tools/node_modules/web-audio-engine');
const rate=22050;
const runningFacade=raw=>new Proxy(raw,{get(t,k){if(k==='state')return 'running';const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});
const actor=(extra={})=>({active:true,visible:true,phase:'crossing',x:0,y:55,z:-180,velocityX:0,velocityZ:60,verticalVelocity:0,rotorRpm:420,...extra});
const model=()=>({state:'racing',timer:0,player:{mass:1450,x:0,z:0,y:0,heading:0,speed:0,velocityX:0,velocityZ:0,vz:0,steer:0,energy:.5,altitude:0,flying:false,thrusting:false,offRoad:false},helicopter:actor(),civilianHelicopter:actor({active:false}),events:[],wanted:0,police:[]});
const metric=(data,a=0,b=data.length/rate)=>{let peak=0,sq=0,n=0,nonfinite=0,clipped=0,dc=0;const channelRms=[];for(const c of data.channelData){let ch=0,k=0;for(let i=Math.floor(a*rate);i<Math.min(c.length,Math.floor(b*rate));i++){const v=c[i];peak=Math.max(peak,Math.abs(v));sq+=v*v;ch+=v*v;dc+=v;k++;n++;clipped+=Number(Math.abs(v)>=1);nonfinite+=Number(!Number.isFinite(v));}channelRms.push(Math.sqrt(ch/k));}return {peak,peakDbFS:peak?20*Math.log10(peak):null,rms:Math.sqrt(sq/n),channelRms,dc:dc/n,nonfinite,clipped};};
const raw=new RenderingAudioContext({sampleRate:rate,numberOfChannels:2,blockSize:128}),audio=new GameAudio({context:runningFacade(raw)});let game=model();
for(let frame=0;frame<13*60;frame++){
 const t=frame/60;if(frame===690)game=model();game.timer=t;
 game.helicopter.z=-180+Math.max(0,t-.5)*60;
 if(t>=9.5){game.helicopter=actor({x:0,y:35,z:-20,velocityZ:0});game.civilianHelicopter=actor({x:0,y:35,z:20,velocityZ:0});}
 audio.enabled=!(t>=10.5&&t<11.5);
 audio.update(game,t,{menu:t<.5||t>=8.5&&t<9.5,paused:t>=7.5&&t<8.5,dt:1/60});
 // Isolate rotor branch for directional/level tests; original game buses untouched in runtime.
 audio.motorFundamental.gain.gain.value=0;audio.motorHarmonic.gain.gain.value=0;audio.motorWhine.gain.gain.value=0;
 audio.roadBus.gain.value=0;audio.fxBus.gain.value=0;audio.ambienceBus.gain.value=0;
 if(frame===750)audio.dispose();raw.processTo((frame+1)/60);
}
const data=raw.exportAsAudioData(),overall=metric(data),windows=[['initial menu',0,.45],['left approach',1,2.5],['overhead',3.2,3.8],['right departure',4.5,6],['pause after fade',8.1,8.4],['menu after fade',8.8,9.3],['two nearby actors',9.8,10.4],['mute after fade',11.1,11.4],['restart',11.8,12.4],['disposed',12.6,12.9]],segments=windows.map(([name,a,b])=>({name,...metric(data,a,b)}));
const segment=name=>segments.find(s=>s.name===name);
assert.equal(overall.nonfinite,0);assert.equal(overall.clipped,0);assert(overall.peak<.2);assert(Math.abs(overall.dc)<.001);
assert(segment('left approach').channelRms[0]>segment('left approach').channelRms[1]*1.8);assert(segment('right departure').channelRms[1]>segment('right departure').channelRms[0]*1.8);
for(const name of ['initial menu','pause after fade','menu after fade','mute after fade','disposed'])assert(segment(name).rms<1e-5,name);
assert(segment('overhead').rms>.002);assert(segment('two nearby actors').rms>.002);assert(segment('restart').rms>.002);
const stressRaw=new RenderingAudioContext({sampleRate:rate,numberOfChannels:2,blockSize:128}),stressAudio=new GameAudio({context:runningFacade(stressRaw)}),stressGame=model();let maxVoices=0;
Object.assign(stressGame.player,{speed:85,steer:.35,lateralSpeed:8,ultraBoosting:true,thrusting:true,offRoad:true});stressGame.wanted=3;stressGame.police=[{active:true,siren:true,x:2,y:0,z:2}];stressGame.helicopter=actor({x:0,y:0,z:0,velocityZ:0});stressGame.civilianHelicopter=actor({x:0,y:0,z:0,velocityZ:0});
for(let frame=0;frame<4*60;frame++){if(frame%15===0){stressGame.events.push({id:stressGame.events.length+1,type:'contact',impulse:50000,closingSpeed:38});stressGame.events.push({id:stressGame.events.length+1,type:'airtime-reward',actualEnergyAdded:.04});}stressAudio.update(stressGame,frame/60,{input:{throttle:1,brake:true},dt:1/60});maxVoices=Math.max(maxVoices,stressAudio._voices.size);stressRaw.processTo((frame+1)/60);}
const stress=metric(stressRaw.exportAsAudioData());assert.equal(stress.clipped,0);assert.equal(stress.nonfinite,0);assert(stress.peak<.85);assert(maxVoices<=12);stressAudio.dispose();
const hashes={};for(const name of ['audio.js','rotor-audio-targets.js'])hashes[name]=createHash('sha256').update(await fs.readFile(new URL('../src/'+name,import.meta.url))).digest('hex');
const report={scope:'Actual original synthesis software-rendered in scripted states, not gameplay, not native browser autoplay/performance or listening verification',engine:'web-audio-engine 0.13.4 MIT; DynamicsCompressor is pass-through, so measurements are pre-compressor',runningContext:'Test facade reports running; this does not test gesture unlock',sampleRate:rate,hashes,addedNodes:20,addedContinuousSources:6,maximumActors:2,overall,segments,stress,maxOneShotVoices:maxVoices};
const output='/tmp/kerala-v15-rotor-audio-signal.json';await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');
if(process.argv.includes('--wav'))await fs.writeFile('/tmp/kerala-v15-rotor-SYNTHESIZED_NOT_GAMEPLAY.wav',Buffer.from(await raw.encodeAudioData(data,{bitDepth:16})));
console.log(JSON.stringify({overall,segments,stress,maxOneShotVoices:maxVoices,output},null,2));
