// Offline signal rendering of the actual V10 module. NOT a browser audio capture.
// Setup: npm install --prefix /tmp/kerala-audio-tools web-audio-engine@0.13.4 --ignore-scripts
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {GameAudio} from '../src/audio.js';
const require=createRequire(import.meta.url);
const {RenderingAudioContext}=require(process.env.AUDIO_ENGINE||'/tmp/kerala-audio-tools/node_modules/web-audio-engine');
const context=new RenderingAudioContext({sampleRate:44100,numberOfChannels:2,blockSize:128});
const audio=new GameAudio({context,seed:267});assert(audio.available,audio.error);
const model={state:'menu',player:{mass:1450,x:0,z:0,y:.18,heading:0,speed:0,steer:0,energy:1,altitude:0,flying:false,thrusting:false,offRoad:false},police:[],wanted:0,events:[],countdown:3};
const event=(type,data={})=>model.events.push({id:model.events.length+1,type,...data});
const stageEnds=[1.5,4.5,8,11,14,16,19,22,25,26,28,30,32,34,37,39];
let lastStage=-1,maxVoices=0;
for(let frame=0;frame<39*60;frame++){
 const t=frame/60,p=model.player,stage=stageEnds.findIndex(end=>t<end);
 if(stage!==lastStage){
  if(stage===2)event('go');
  if([4,11,14].includes(stage))event('ultra-start');
  if(stage===9)event('landing',{verticalSpeed:7.8,intensity:.65});
  lastStage=stage;
 }
 if(frame===16*60)event('contact',{impulse:1450*2,closingSpeed:3,intensity:1});
 if(frame===17*60)event('obstacle-contact',{impulse:1450*9,closingSpeed:14,intensity:.01});
 if(frame===18*60)event('contact',{impulse:1450*24,closingSpeed:28,intensity:.01});
 if(stage===14&&frame%15===0)event('contact',{impulse:50000,closingSpeed:38,intensity:1});
 model.state=stage===0?'menu':stage===1?'countdown':'racing';model.countdown=Math.max(0,4.5-t);
 p.speed=stage<2?0:stage===2?(t-4.5)*18:stage===3||stage===4?72:stage===5?45:stage===6?14:stage===7?50:stage===8?42:stage===9?22:[11,12,14].includes(stage)?85:stage===13?15:0;
 p.steer=stage===5?.22:stage===14?.35:0;p.lateralSpeed=stage===5?4:stage===14?8:0;
 p.offRoad=stage===5&&t>15||stage===14;p.boosting=stage===3||stage===14;p.ultraBoosting=[4,11,12,14].includes(stage);
 p.thrusting=stage===8||stage===14;p.flying=stage===8;p.altitude=stage===8?2:0;p.vz=stage===8?-7.8:0;
 model.wanted=stage===7||stage===14?2:0;model.police=stage===7?[{x:-20,z:90-(t-19)*60,y:.18,active:true,siren:true}]:stage===14?[{x:2,z:2,y:.18,active:true,siren:true}]:[];
 audio.enabled=stage!==11;
 audio.update(model,t,{menu:stage===0,paused:stage===10||stage===15,input:{throttle:stage>=2?.9:0,brake:stage===5||stage===14},dt:1/60});
 maxVoices=Math.max(maxVoices,audio.diagnostics.oneShotVoices);
 context.processTo((frame+1)/60);
}
const data=context.exportAsAudioData();
const windows=[['menu silence',0,1.4],['countdown',1.5,4.5],['EV acceleration',4.5,8],['regular boost steady',8.5,10.8],['ultra activation',11,11.5],['ultra steady',11.5,13.8],['braking/skid/offroad',14,16],['soft impulse contact',16,16.35],['medium impulse contact',17,17.35],['hard impulse contact',18,18.35],['siren passes left/right',19,22],['thruster',22,25],['landing',25,26],['paused silence after fade',26.6,27.9],['muted ultra after fade',28.6,29.9],['resume ultra without replay',30,32],['coast',32,34],['simultaneous stress mix',34,37],['final paused silence',37.6,38.9]];
const source=await fs.readFile(new URL('../src/audio.js',import.meta.url));
const report={type:'software rendering of actual V10 procedural module with scripted state; not browser capture; not auditory review',sourceSha256:createHash('sha256').update(source).digest('hex'),engine:'web-audio-engine 0.13.4 (MIT)',compressor:'This software engine passes unimplemented DynamicsCompressor through unchanged. Measurements therefore validate pre-compressor headroom, not native browser compression.',sampleRate:data.sampleRate,channels:data.channelData.length,duration:data.length/data.sampleRate,maxOneShotVoices:maxVoices,ultraActivationCues:audio.diagnostics.ultraActivationCues,segments:[]};
let peak=0,nonfinite=0,clipped=0,sum=0,squares=0,n=0;
for(const channel of data.channelData)for(const sample of channel){if(!Number.isFinite(sample))nonfinite++;peak=Math.max(peak,Math.abs(sample));if(Math.abs(sample)>=1)clipped++;sum+=sample;squares+=sample*sample;n++;}
Object.assign(report,{peak,peakDbFS:20*Math.log10(peak),rms:Math.sqrt(squares/n),dcMean:sum/n,nonfinite,clipped});
for(const [name,a,b]of windows){let ss=0,nn=0,pp=0;for(const channel of data.channelData)for(let i=Math.floor(a*data.sampleRate);i<Math.min(channel.length,b*data.sampleRate);i++){ss+=channel[i]**2;pp=Math.max(pp,Math.abs(channel[i]));nn++;}const rms=Math.sqrt(ss/nn);report.segments.push({name,start:a,end:b,rms,dbFS:rms?20*Math.log10(rms):null,peak:pp});}
const metric=name=>report.segments.find(s=>s.name===name);
report.ultraToRegularSteadyRms=metric('ultra steady').rms/metric('regular boost steady').rms;
report.hardToSoftContactPeak=metric('hard impulse contact').peak/metric('soft impulse contact').peak;
assert.equal(nonfinite,0);assert.equal(clipped,0);assert(peak<.8,'pre-compressor peak headroom');assert(Math.abs(report.dcMean)<.005);assert(maxVoices<=12);assert.equal(report.ultraActivationCues,2,'muted ultra start must not replay on resume');
for(const name of ['menu silence','paused silence after fade','muted ultra after fade','final paused silence'])assert(metric(name).rms<1e-5,name);
assert(metric('EV acceleration').rms>.001);assert(report.ultraToRegularSteadyRms>1.05,'ultra has a distinct higher-energy sustained mix');assert(report.hardToSoftContactPeak>1.5,'actual high impulse produces stronger transient');
const out=new URL('../../assets/audio/',import.meta.url);await fs.mkdir(out,{recursive:true});
await fs.writeFile(new URL('malabar_v10_ultra_crash_NOT_GAMEPLAY.wav',out),Buffer.from(await context.encodeAudioData(data,{bitDepth:16})));
await fs.writeFile(new URL('v10_audio_signal_validation.json',out),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));audio.dispose();
