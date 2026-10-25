import {rotorAudioTargets} from './rotor-audio-targets.js';
/** Original procedural audio. No recordings, network requests, or licensed samples.
 * Levels are perceptual arcade mix controls, not Tesla motor/acoustic measurements.
 */
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,Number.isFinite(v)?v:0));
const finite=(v,fallback=0)=>Number.isFinite(v)?v:fallback;
const TAU=Math.PI*2;
// Original synthesis identities, not sampled/authentic manufacturer recordings.
const ELECTRIC=Object.freeze({wave:'sine',harmonicWave:'triangle',idle:62,slope:4.1,loadHz:18,ratio:2.01,harmonic:.23,whine:.11,filter:1100});
export const ENGINE_PROFILES=Object.freeze({
 red:ELECTRIC,silver:ELECTRIC,
 touring:Object.freeze({wave:'triangle',harmonicWave:'triangle',idle:45,slope:2.1,loadHz:31,ratio:3,harmonic:.24,whine:.018,filter:780}),
 vermilion:Object.freeze({wave:'triangle',harmonicWave:'sawtooth',idle:69,slope:2.8,loadHz:37,ratio:2.98,harmonic:.15,whine:.027,filter:1300}),
 bronze:Object.freeze({wave:'triangle',harmonicWave:'sawtooth',idle:39,slope:1.9,loadHz:27,ratio:2.02,harmonic:.23,whine:.035,filter:700}),
 verdant:Object.freeze({wave:'triangle',harmonicWave:'triangle',idle:64,slope:3.05,loadHz:33,ratio:4.01,harmonic:.14,whine:.022,filter:1150}),
 midnight:Object.freeze({wave:'triangle',harmonicWave:'sawtooth',idle:34,slope:1.75,loadHz:24,ratio:4.02,harmonic:.18,whine:.042,filter:680})
});
export function motorTargets(vehicleId,speed,load){
 const id=Object.hasOwn(ENGINE_PROFILES,vehicleId)?vehicleId:'red',p=ENGINE_PROFILES[id],s=clamp(Math.abs(finite(speed)),0,120),l=clamp(load);
 return {id,...p,base:p.idle+s*p.slope+l*p.loadHz,whineHz:520+s*12.8+l*150,filterHz:p.filter+s*24};
}

/** Perceptual contact strength from the simulation's actual impulse (N s).
 * This is an arcade sound mapping, not a calibrated acoustic/structural model.
 */
export function impactLevel(event={},mass=1450){
  if(Number.isFinite(event.impulse)&&event.impulse>=0){
    const deltaV=event.impulse/Math.max(100,finite(mass,1450));
    return clamp(.7*deltaV/18+.3*Math.max(0,finite(event.closingSpeed))/28,.04,1);
  }
  if(Number.isFinite(event.closingSpeed))return clamp(event.closingSpeed/25,.04,1);
  return clamp(event.intensity??.2,.04,1);
}
export function audioState(model={},time=0,{menu=false,paused=false,input={},coastAmount=1}={}){
  const p=model.player||{},speed=Math.abs(finite(p.speed)),running=model.state==='racing';
  const grounded=p.grounded!==false&&finite(p.altitude)<.08&&!p.flying;
  const throttle=finite(input.throttle);
  // Negative throttle brakes a forward-moving car, but drives the motor in reverse.
  const load=running?clamp(throttle<0&&finite(p.speed)<.5?-throttle:Math.max(0,throttle)):0;
  const braking=running&&(input.brake||finite(input.throttle)<0&&finite(p.speed)>1);
  const lateral=Math.abs(Math.tan(clamp(finite(p.steer),-.65,.65)))*speed*speed/2.7;
  const skid=running&&grounded?clamp((lateral-8)/18+Math.max(0,Math.abs(finite(p.lateralSpeed))-1.3)/7+(braking&&speed>9?.45:0))*clamp(speed/15):0;
  let nearest=null,distance=Infinity;
  if(running&&model.wanted)for(const cop of model.police||[]){
    if(cop.active===false||cop.siren===false)continue;
    const d=Math.hypot(finite(cop.x)-finite(p.x),finite(cop.z)-finite(p.z),finite(cop.y)-finite(p.y));
    if(d<distance){nearest=cop;distance=d;}
  }
  let pan=0;if(nearest){const dx=finite(nearest.x)-finite(p.x),dz=finite(nearest.z)-finite(p.z),heading=finite(p.heading);pan=clamp((-dx*Math.sin(heading)+dz*Math.cos(heading))/Math.max(distance,20),-.85,.85);}
  const siren=nearest&&distance<650?1/(1+(distance/72)**2):0;
  return {coastAmount:clamp(coastAmount),active:!menu&&!paused&&model.state!=='menu',running,speed,load,skid,braking,grounded,offRoad:!!p.offRoad,
    boost:running&&!!p.boosting&&!p.ultraBoosting,ultra:running&&!!p.ultraBoosting,thrust:running&&!!p.thrusting,airborne:!!p.flying,
    energy:clamp(p.energy),siren,distance,pan,time:finite(time),altitude:finite(p.altitude),vz:finite(p.vz)};
}

export class GameAudio {
  constructor({context=null,seed=267}={}){
    this._enabled=true;this.available=false;this.active=false;this.unlocked=false;this.error=null;
    this._seed=seed>>>0;this._loops=[];this._voices=new Set();this._lastEventId=0;this._model=null;
    this._lastState=null;this._lastCountdown=null;this._lastFlying=false;this._lastVz=0;this._lastDistance=Infinity;
    this._mix={};this._nextBird=9;this._lastUltra=false;this._lastUltraCue=-Infinity;this._ultraCues=0;this._lastImpact=null;this.disposed=false;
    this._paused=false;this._uiCueCount=0;this._lastUICue=null;this._airtimeCues=0;this._rotorTargets=[];
    const Context=globalThis.AudioContext||globalThis.webkitAudioContext;
    try{
      this.context=context||(Context?new Context({latencyHint:'interactive'}):null);
      this._ownsContext=!context;if(!this.context)return;
      this._build();this.available=true;
      this._contextStateHandler=()=>{if(this.context.state!=='running'){this._stopUI(true);this._silenceRotors(true);}this._syncUI();};
      this.context.addEventListener?.('statechange',this._contextStateHandler);
    }catch(error){this.error=String(error);this.available=false;}
  }
  get enabled(){return this._enabled;}
  set enabled(value){this._enabled=!!value;if(this.available&&!this.disposed){this._target(this.master.gain,this._enabled&&this.active?.62:0,.05);if(!this._enabled){this._stopUI();this._silenceRotors();}this._syncUI();}}
  get diagnostics(){return {airtimeRewardCues:this._airtimeCues,rotors:this._rotorTargets.map(t=>({...t})),engineProfile:this.engineProfile||'red',available:this.available,contextState:this.context?.state||'unavailable',unlocked:this.unlocked,enabled:this.enabled,active:this.active,oneShotVoices:this._voices.size,uiVoices:this._countUI(),uiCueCount:this._uiCueCount,lastUICue:this._lastUICue,lastEventId:this._lastEventId,ultraActivationCues:this._ultraCues,lastImpact:this._lastImpact?{...this._lastImpact}:null,mix:{...this._mix},error:this.error};}
  _random(){this._seed=(1664525*this._seed+1013904223)>>>0;return this._seed/4294967296;}
  _gain(value=0){const n=this.context.createGain();n.gain.value=value;return n;}
  _filter(type,hz,q=.7){const n=this.context.createBiquadFilter();n.type=type;n.frequency.value=hz;n.Q.value=q;return n;}
  _target(param,value,tau=.06){if(!param)return;const now=finite(this.context.currentTime);param.setTargetAtTime(finite(value),now,Math.max(.005,tau));}
  _noise(kind='white'){
    const ctx=this.context,buffer=ctx.createBuffer(2,Math.ceil(ctx.sampleRate*4),ctx.sampleRate);
    for(let channel=0;channel<2;channel++){const data=buffer.getChannelData(channel);let brown=0,b0=0,b1=0,b2=0;
      for(let i=0;i<data.length;i++){const white=this._random()*2-1;
        if(kind==='brown'){brown=(brown+.025*white)/1.025;data[i]=brown*4.1;}
        else if(kind==='pink'){b0=.99765*b0+white*.099046;b1=.963*b1+white*.2965164;b2=.57*b2+white*1.0526913;data[i]=(b0+b1+b2+white*.1848)*.055;}
        else data[i]=white*.7;
      }
      // Crossfade the loop seam without creating a discontinuity every four seconds.
      const seam=Math.min(512,Math.floor(data.length/4));for(let i=0;i<seam;i++){const t=(i+1)/seam;data[data.length-seam+i]=data[data.length-seam+i]*(1-t)+data[0]*t;}
    }return buffer;
  }
  _osc(type,hz,bus,gain=0){const osc=this.context.createOscillator(),amp=this._gain(gain);osc.type=type;osc.frequency.value=hz;osc.connect(amp).connect(bus);osc.start();this._loops.push(osc);return {osc,gain:amp};}
  _noiseLoop(buffer,bus,type,hz,q=.7){const source=this.context.createBufferSource(),filter=this._filter(type,hz,q),gain=this._gain();source.buffer=buffer;source.loop=true;source.connect(filter).connect(gain).connect(bus);source.start();this._loops.push(source);return {source,filter,gain};}
  _build(){
    const ctx=this.context;
    this.master=this._gain();this.compressor=ctx.createDynamicsCompressor();
    this.compressor.threshold.value=-10;this.compressor.knee.value=5;this.compressor.ratio.value=12;
    this.compressor.attack.value=.003;this.compressor.release.value=.18;
    this.compressor.connect(this.master).connect(ctx.destination);
    // Workshop confirmations bypass only the gameplay mute, never the user's mute.
    // Independent limiting + six UI voices maximum keeps menu audio bounded.
    this.uiBus=this._gain(1);this.uiCompressor=ctx.createDynamicsCompressor();this.uiMaster=this._gain();
    this.uiCompressor.threshold.value=-16;this.uiCompressor.knee.value=6;this.uiCompressor.ratio.value=8;
    this.uiCompressor.attack.value=.002;this.uiCompressor.release.value=.1;
    this.uiBus.connect(this.uiCompressor).connect(this.uiMaster).connect(ctx.destination);
    this.motorBus=this._filter('lowpass',1800,.7);this.motorBus.connect(this.compressor);
    this.roadBus=this._gain(1);this.roadBus.connect(this.compressor);
    this.fxBus=this._gain(1);this.fxBus.connect(this.compressor);
    this.ambienceBus=this._gain(1);this.ambienceBus.connect(this.compressor);
    this.sirenBus=typeof ctx.createStereoPanner==='function'?ctx.createStereoPanner():this._gain(1);this.sirenBus.connect(this.compressor);
    this.noise={white:this._noise('white'),pink:this._noise('pink'),brown:this._noise('brown')};
    this.motorFundamental=this._osc('sine',62,this.motorBus);
    this.motorHarmonic=this._osc('triangle',124,this.motorBus);
    this.motorWhine=this._osc('sine',600,this.motorBus);
    this.wind=this._noiseLoop(this.noise.pink,this.roadBus,'lowpass',1600);
    this.road=this._noiseLoop(this.noise.brown,this.roadBus,'bandpass',220,.75);
    this.skid=this._noiseLoop(this.noise.white,this.roadBus,'bandpass',1450,1.0);
    this.skidTone=this._osc('sine',760,this.roadBus);
    this.boost=this._noiseLoop(this.noise.pink,this.fxBus,'highpass',400,.6);
    this.ultraAir=this._noiseLoop(this.noise.pink,this.fxBus,'bandpass',1900,.55);
    this.ultraBody=this._noiseLoop(this.noise.brown,this.fxBus,'lowpass',650,.6);
    this.ultraTurbine=this._osc('triangle',190,this.fxBus);
    this.thruster=this._noiseLoop(this.noise.brown,this.fxBus,'lowpass',1100,.6);
    this.thrusterHiss=this._noiseLoop(this.noise.white,this.fxBus,'bandpass',2100,.65);
    this.surf=this._noiseLoop(this.noise.pink,this.ambienceBus,'lowpass',700);
    this.surfFoam=this._noiseLoop(this.noise.white,this.ambienceBus,'bandpass',2400,.5);
    this.sirenA=this._osc('sine',650,this.sirenBus);
    this.sirenB=this._osc('triangle',975,this.sirenBus);
    // Exactly two persistent actors, three sources each. No frame/event allocations.
    // One triangle drives both audible blade body and audio-rate wash modulation.
    this.rotorVoices=Array.from({length:2},()=>{
      const bus=this._gain(),pan=typeof ctx.createStereoPanner==='function'?ctx.createStereoPanner():this._gain(1);
      bus.connect(pan).connect(this.compressor);
      const rotor=this._osc('triangle',400*4/60,bus),turbine=this._osc('sine',1120,bus);
      const wash=this._noiseLoop(this.noise.pink,bus,'lowpass',1200,.65),modulation=this._gain();
      rotor.osc.connect(modulation);modulation.connect(wash.gain.gain);
      return {bus,pan,rotor,turbine,wash,modulation};
    });
  }
  _silenceRotors(hard=false){
    for(const voice of this.rotorVoices||[]){const gain=voice.bus.gain;if(hard){gain.cancelScheduledValues?.(this.context.currentTime);gain.setValueAtTime(0,this.context.currentTime);}else this._target(gain,0,.04);}
    this._rotorTargets=this._rotorTargets.map(t=>({...t,active:false,gain:0}));
  }
  _updateRotors(model,options){
    const targets=rotorAudioTargets(model||{},{...options,enabled:this.enabled,contextRunning:this.context.state==='running'});this._rotorTargets=targets;
    for(let i=0;i<2;i++){const target=targets[i],voice=this.rotorVoices[i];
      this._target(voice.bus.gain,target.gain,target.gain>0?.14:.04);if(voice.pan.pan)this._target(voice.pan.pan,target.pan,.1);
      this._target(voice.rotor.osc.frequency,target.bladePassHz,.14);this._target(voice.rotor.gain.gain,target.rotorGain,.12);
      this._target(voice.turbine.osc.frequency,target.turbineHz,.14);this._target(voice.turbine.gain.gain,target.turbineGain,.12);
      this._target(voice.wash.filter.frequency,target.washCutoffHz,.2);this._target(voice.wash.gain.gain,target.washGain,.12);this._target(voice.modulation.gain,target.modulationDepth,.12);
    }
  }
  async resume(){
    if(!this.available||this.disposed)return false;
    try{if(this.context.state!=='running'&&typeof this.context.resume==='function')await this.context.resume();this.unlocked=this.context.state==='running';if(this.unlocked)this.error=null;this._syncUI();return this.unlocked;}
    catch(error){this.error='Audio unlock pending: '+String(error);return false;}
  }
  _countUI(){let count=0;for(const voice of this._voices)if(voice.kind==='ui')count++;return count;}
  _syncUI(){if(this.available&&!this.disposed)this._target(this.uiMaster.gain,this.enabled&&!this._paused&&this.context.state==='running'?.5:0,.008);}
  _stopUI(immediate=false){
    const now=finite(this.context?.currentTime),hard=immediate||this.context?.state!=='running';
    for(const voice of this._voices){if(voice.kind!=='ui'||voice.stopping&&!hard)continue;voice.stopping=true;
      try{
        if(hard){voice.source.onended=null;voice.source.stop();voice.source.disconnect();for(const node of voice.chain)node.disconnect();this._voices.delete(voice);}
        else{const gain=voice.envelope.gain;if(typeof gain.cancelAndHoldAtTime==='function')gain.cancelAndHoldAtTime(now);else{const value=finite(gain.value);gain.cancelScheduledValues?.(now);gain.setValueAtTime(value,now);}gain.setTargetAtTime(.0001,now,.004);voice.source.stop(now+.025);}
      }catch{this._voices.delete(voice);}
    }
  }
  /** Call only AFTER a successful transaction, after gesture-driven resume().
   * Returns false rather than queueing on mute/pause/suspension or voice saturation.
   * This never changes the gameplay master or starts engine/ambient sound in menus.
   */
  playUI(kind){
    if(!['upgrade','unlock'].includes(kind)||!this.available||this.disposed||!this.enabled||this._paused||this.context.state!=='running')return false;
    if(this._countUI()>4||this._voices.size>10)return false;
    const now=this.context.currentTime,unlock=kind==='unlock';
    const notes=unlock?[[440,0,.1],[659.25,.11,.1],[880,.22,.1],[1318.51,.33,.3]]:[[659.25,0,.085],[830.61,.095,.085],[1108.73,.19,.21]];
    const end=notes[notes.length-1][1]+notes[notes.length-1][2]+.03;
    for(const [type,ratio,level] of [['sine',1,unlock?.105:.09],['triangle',2,unlock?.018:.014]]){
      const source=this.context.createOscillator(),gain=this._gain();source.type=type;source.frequency.value=notes[0][0]*ratio;gain.gain.setValueAtTime(0,now);
      for(const [hz,delay,duration]of notes){const t=now+delay;source.frequency.setValueAtTime(hz*ratio,t);gain.gain.setValueAtTime(.0001,t);gain.gain.linearRampToValueAtTime(level,t+.008);gain.gain.exponentialRampToValueAtTime(.0001,t+duration);}
      source.connect(gain).connect(this.uiBus);const voice={kind:'ui',source,chain:[gain],envelope:gain};this._voices.add(voice);
      source.onended=()=>{this._voices.delete(voice);source.disconnect();gain.disconnect();};source.start(now);source.stop(now+end);
    }
    this._uiCueCount++;this._lastUICue=kind;this._syncUI();return true;
  }
  _voice(source,chain,duration){
    if(this._voices.size>=12)return false;
    const voice={source,chain};this._voices.add(voice);
    source.onended=()=>{this._voices.delete(voice);for(const node of [source,...chain])try{node.disconnect();}catch{}};
    source.start(this.context.currentTime);source.stop(this.context.currentTime+duration);return true;
  }
  _tone(hz,duration=.18,level=.05,delay=0){
    if(this._voices.size>=12)return;const now=this.context.currentTime+delay,osc=this.context.createOscillator(),gain=this._gain();
    osc.type='sine';osc.frequency.value=hz;gain.gain.setValueAtTime(0,now);gain.gain.linearRampToValueAtTime(level,now+.008);gain.gain.exponentialRampToValueAtTime(.0001,now+duration);
    osc.connect(gain).connect(this.fxBus);const voice={source:osc,chain:[gain]};this._voices.add(voice);
    osc.onended=()=>{this._voices.delete(voice);osc.disconnect();gain.disconnect();};osc.start(now);osc.stop(now+duration+.02);
  }
  _impact(intensity=.3,landing=false){
    if(this._voices.size>8)return;const level=clamp(intensity,.06,1),now=this.context.currentTime;
    const noise=this.context.createBufferSource(),filter=this._filter('lowpass',landing?500:1600+3300*level,landing?.7:1),gain=this._gain();noise.buffer=this.noise.white;
    if(!landing){filter.frequency.setValueAtTime(1600+3300*level,now);filter.frequency.exponentialRampToValueAtTime(650+450*level,now+.24);}
    gain.gain.setValueAtTime(.001,now);gain.gain.linearRampToValueAtTime((landing?.17:.42)*level,now+.002);gain.gain.exponentialRampToValueAtTime(.0001,now+(landing?.18:.34));
    noise.connect(filter).connect(gain).connect(this.fxBus);this._voice(noise,[filter,gain],.36);
    const osc=this.context.createOscillator(),thud=this._gain();osc.type='sine';osc.frequency.setValueAtTime(landing?95:130,now);osc.frequency.exponentialRampToValueAtTime(38,now+.14);
    thud.gain.setValueAtTime(.001,now);thud.gain.linearRampToValueAtTime((landing?.19:.25)*level,now+.004);thud.gain.exponentialRampToValueAtTime(.0001,now+.22);
    osc.connect(thud).connect(this.fxBus);this._voice(osc,[thud],.24);
    // Brief damped bodywork partials only for a substantial collision, not every scrape.
    if(!landing&&level>.65){this._tone(367,.17,.024*level,.024);this._tone(641,.12,.017*level,.065);}
  }
  _ultraActivation(){
    const now=this.context.currentTime;if(now-this._lastUltraCue<.3||this._voices.size>8)return;
    this._lastUltraCue=now;this._ultraCues++;
    // A short electrical rise opens into pressure noise; not a sampled cinematic effect.
    const osc=this.context.createOscillator(),tone=this._gain();osc.type='sine';
    osc.frequency.setValueAtTime(145,now);osc.frequency.exponentialRampToValueAtTime(920,now+.16);osc.frequency.exponentialRampToValueAtTime(260,now+.38);
    tone.gain.setValueAtTime(.0001,now);tone.gain.linearRampToValueAtTime(.075,now+.07);tone.gain.exponentialRampToValueAtTime(.0001,now+.39);
    osc.connect(tone).connect(this.fxBus);this._voice(osc,[tone],.42);
    const source=this.context.createBufferSource(),filter=this._filter('bandpass',230,.65),gain=this._gain();source.buffer=this.noise.pink;
    filter.frequency.setValueAtTime(230,now);filter.frequency.exponentialRampToValueAtTime(3200,now+.18);filter.frequency.exponentialRampToValueAtTime(900,now+.42);
    gain.gain.setValueAtTime(.0001,now);gain.gain.linearRampToValueAtTime(.32,now+.15);gain.gain.exponentialRampToValueAtTime(.0001,now+.46);
    source.connect(filter).connect(gain).connect(this.fxBus);this._voice(source,[filter,gain],.49);
  }
  _events(model,canSound){
    let suppressFallback=false,ultraActivation=false;
    for(const event of model.events||[]){
      const id=finite(event.id);if(id<=this._lastEventId)continue;this._lastEventId=id;suppressFallback||=['landing','recovery','roadside-assist','water-contact','start'].includes(event.type);ultraActivation||=event.type==='ultra-start';if(!canSound)continue;
      if(event.type==='contact'||event.type==='obstacle-contact'){
        const level=impactLevel(event,model.player?.mass);this._lastImpact={eventId:id,level,impulse:Number.isFinite(event.impulse)?event.impulse:null,closingSpeed:Number.isFinite(event.closingSpeed)?event.closingSpeed:null};this._impact(level);
      }
      else if(event.type==='landing')this._impact(clamp(Number.isFinite(event.verticalSpeed)?event.verticalSpeed/12:event.intensity??.35,.1,1),true);
      else if(event.type==='ultra-start')this._ultraActivation();
      else if(event.type==='airtime-reward'&&!model.paused&&finite(event.actualEnergyAdded)>0&&this.context.state==='running'&&this._voices.size<=10){this._tone(1046.5,.10,.025);this._tone(1568,.15,.02,.055);this._airtimeCues++;}
      else if(event.type==='checkpoint'){this._tone(880,.12,.035);this._tone(1320,.16,.026,.08);}
      else if(event.type==='go'){this._tone(880,.25,.065);this._tone(1320,.3,.03);}
      else if(event.type==='escaped'||event.type==='finished'){[660,880,1100].forEach((hz,i)=>this._tone(hz,.3,.045,i*.11));}
      else if(event.type==='busted'||event.type==='failed'){this._tone(220,.3,.06);this._tone(164.8,.45,.05,.2);}
      else if(event.type==='water-contact')this._impact(.45,true);
    }return {suppressFallback,ultraActivation};
  }
  _clearVoices(includeUI=false){
    for(const voice of this._voices){if(!includeUI&&voice.kind==='ui')continue;voice.source.onended=null;try{voice.source.stop();voice.source.disconnect();for(const node of voice.chain)node.disconnect();}catch{}this._voices.delete(voice);}
  }
  update(model,time=0,options={}){
    if(!this.available||this.disposed)return;
    this._paused=!!options.paused;if(this._paused||this.context.state!=='running')this._stopUI();this._syncUI();this._updateRotors(model,options);
    if(!model?.player)return;
    const state=audioState(model,time,options),dt=clamp(options.dt??1/60,.001,.1);
    const eventsList=model.events||[],eventTail=eventsList[eventsList.length-1];
    // Explore can restart the same model directly into racing, without a countdown.
    const restarted=eventsList[0]?.type==='start'&&eventTail?.id<this._lastEventId;
    if(this._model!==model||restarted||(model.state==='countdown'&&this._lastState!=='countdown')){
      this._clearVoices();
      this._model=model;this._lastEventId=0;this._lastCountdown=null;this._lastFlying=false;this._lastDistance=Infinity;this._lastUltra=false;this._lastUltraCue=-Infinity;this._lastImpact=null;this._nextBird=state.time+9;
    }
    this.active=state.active;const canSound=state.active&&this.enabled;
    this._target(this.master.gain,canSound?.62:0,.05);
    const s=state.speed,travel=state.running?clamp(s/80):0,load=state.load;
    const motor=state.running?(.012+.045*load+.035*travel)*(state.airborne?.7:1):0;
    const tone=motorTargets(model.vehicleStats?.vehicleId,s,load);this.engineProfile=tone.id;
    if(this.motorFundamental.osc.type!==tone.wave)this.motorFundamental.osc.type=tone.wave;
    if(this.motorHarmonic.osc.type!==tone.harmonicWave)this.motorHarmonic.osc.type=tone.harmonicWave;
    this._target(this.motorFundamental.osc.frequency,tone.base,.055);this._target(this.motorFundamental.gain.gain,motor,.07);
    this._target(this.motorHarmonic.osc.frequency,tone.base*tone.ratio,.055);this._target(this.motorHarmonic.gain.gain,motor*tone.harmonic,.07);
    this._target(this.motorWhine.osc.frequency,tone.whineHz,.08);this._target(this.motorWhine.gain.gain,motor*tone.whine,.08);
    this._target(this.motorBus.frequency,tone.filterHz,.1);
    this._target(this.wind.gain.gain,.105*travel**1.7,.18);this._target(this.wind.filter.frequency,700+s*20,.2);
    this._target(this.road.gain.gain,state.grounded?travel*(state.offRoad?.2:.075):0,.1);this._target(this.road.filter.frequency,state.offRoad?145:230+s*2,.15);
    this._target(this.skid.gain.gain,state.skid*.075,.04);this._target(this.skid.filter.frequency,1250+state.skid*850,.08);
    this._target(this.skidTone.osc.frequency,720+state.skid*210+Math.sin(state.time*21)*12,.04);this._target(this.skidTone.gain.gain,state.skid*.012,.04);
    this._target(this.boost.gain.gain,state.boost?.045:0,.08);
    this._target(this.ultraAir.gain.gain,state.ultra?.2:0,state.ultra?.06:.15);this._target(this.ultraAir.filter.frequency,1500+s*14,.1);
    this._target(this.ultraBody.gain.gain,state.ultra?.13:0,.1);
    this._target(this.ultraTurbine.osc.frequency,190+s*3.5,.09);this._target(this.ultraTurbine.gain.gain,state.ultra?.023:0,.1);
    this._target(this.thruster.gain.gain,state.thrust?.22:0,.035);this._target(this.thrusterHiss.gain.gain,state.thrust?.035:0,.04);
    const swell=.62+.38*Math.sin(state.time*.23)**2;
    this._target(this.surf.gain.gain,.035*swell*state.coastAmount,.5);this._target(this.surfFoam.gain.gain,.012*swell*state.coastAmount,.5);
    const closing=Number.isFinite(this._lastDistance)&&Number.isFinite(state.distance)?clamp((this._lastDistance-state.distance)/dt,-80,80):0;
    this._lastDistance=state.distance;const doppler=clamp(343/(343-closing),.88,1.15),wail=670+Math.sin(state.time*TAU*.7)*270;
    this._target(this.sirenA.osc.frequency,wail*doppler,.035);this._target(this.sirenB.osc.frequency,wail*1.5*doppler,.035);
    this._target(this.sirenA.gain.gain,state.siren*.11,.14);this._target(this.sirenB.gain.gain,state.siren*.023,.14);
    if(this.sirenBus.pan)this._target(this.sirenBus.pan,state.pan,.16);
    const events=this._events(model,canSound);
    if(canSound&&state.ultra&&!this._lastUltra&&!events.ultraActivation)this._ultraActivation();
    this._lastUltra=state.ultra;
    if(canSound&&model.state==='countdown'){
      const n=Math.ceil(finite(model.countdown));if(n>0&&n!==this._lastCountdown){this._tone(440,.1,.045);this._lastCountdown=n;}
    }
    // Landing fallback for versions of the simulation that do not emit a landing event.
    if(canSound&&this._lastFlying&&!state.airborne&&!events.suppressFallback&&state.running)this._impact(clamp(Math.abs(this._lastVz)/12,.12,.7),true);
    this._lastFlying=state.airborne;this._lastVz=state.vz;
    if(canSound&&state.time>this._nextBird&&state.speed<15&&state.siren<.05){this._tone(1800,.09,.009);this._tone(2300,.11,.007,.11);this._nextBird=state.time+16+this._random()*13;}
    this._lastState=model.state;
    this._mix={motor,coast:state.coastAmount,wind:.105*travel**1.7,skid:state.skid,siren:state.siren,sirenDistance:Number.isFinite(state.distance)?state.distance:null,pan:state.pan,boost:state.boost?1:0,ultra:state.ultra?1:0,thrust:state.thrust?1:0,master:canSound?.62:0};
  }
  dispose(){
    if(this.disposed)return;this.disposed=true;this._silenceRotors(true);
    for(const source of this._loops)try{source.stop();source.disconnect();}catch{}
    this._clearVoices(true);for(const voice of this.rotorVoices||[])for(const node of [voice.bus,voice.pan,voice.rotor.gain,voice.turbine.gain,voice.wash.filter,voice.wash.gain,voice.modulation])try{node.disconnect();}catch{}
    try{this.master?.disconnect();this.uiMaster?.disconnect();this.uiBus?.disconnect();this.uiCompressor?.disconnect();}catch{}
    this.context?.removeEventListener?.('statechange',this._contextStateHandler);
    if(this._ownsContext&&this.context?.close)this.context.close().catch(()=>{});
  }
}
export default GameAudio;
