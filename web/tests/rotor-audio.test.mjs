import assert from 'node:assert/strict';
import {rotorActorTarget,rotorAudioTargets} from '../src/rotor-audio-targets.js';
import {GameAudio} from '../src/audio.js';
import {GameModel} from '../src/gameplay.js';
import {PoliceAirSupport} from '../src/police-air-support.js';
class Param{constructor(v=0){this.value=v;this.events=[];}setTargetAtTime(v,t,tau){assert(Number.isFinite(v)&&Number.isFinite(t)&&tau>0);this.value=v;this.events.push(['target',v,t,tau]);}setValueAtTime(v,t){assert(Number.isFinite(v)&&Number.isFinite(t));this.value=v;this.events.push(['set',v,t]);}linearRampToValueAtTime(v,t){this.setValueAtTime(v,t);}exponentialRampToValueAtTime(v,t){assert(v>0);this.setValueAtTime(v,t);}cancelScheduledValues(t){this.events.push(['cancel',t]);}}
class Node{constructor(ctx){this.ctx=ctx;this.connections=[];for(const p of ['gain','frequency','Q','pan','threshold','knee','ratio','attack','release'])this[p]=new Param();}connect(n){this.connections.push(n);return n;}disconnect(){this.connections=[];this.disconnected=true;}start(t=0){this.started=t;}stop(t=this.ctx.currentTime){this.stopped=t;}}
class Context{constructor(){this.sampleRate=1000;this.currentTime=0;this.state='suspended';this.nodes=[];this.listeners=new Map();this.destination=new Node(this);}node(){const n=new Node(this);this.nodes.push(n);return n;}createGain(){return this.node();}createBiquadFilter(){return this.node();}createOscillator(){return this.node();}createBufferSource(){return this.node();}createStereoPanner(){return this.node();}createDynamicsCompressor(){return this.node();}createBuffer(ch,n,rate){const arrays=Array.from({length:ch},()=>new Float32Array(n));return{sampleRate:rate,length:n,getChannelData:c=>arrays[c]};}addEventListener(name,fn){if(!this.listeners.has(name))this.listeners.set(name,new Set());this.listeners.get(name).add(fn);}removeEventListener(name,fn){this.listeners.get(name)?.delete(fn);}changeState(state){this.state=state;for(const fn of this.listeners.get('statechange')||[])fn();}resume(){this.changeState('running');return Promise.resolve();}close(){this.changeState('closed');return Promise.resolve();}advance(t){this.currentTime+=t;for(const n of this.nodes)if(n.stopped!==undefined&&n.stopped<=this.currentTime&&n.onended){const f=n.onended;n.onended=null;f();}}}
const actor=(extra={})=>({active:true,visible:true,phase:'track',x:40,y:38,z:30,velocityX:0,velocityZ:0,verticalVelocity:0,rotorRpm:420,...extra});
const player=(extra={})=>({x:0,y:0,z:0,heading:0,speed:20,velocityX:0,velocityZ:0,vz:0,energy:.4,altitude:0,steer:0,...extra});
const model=()=>({state:'racing',timer:0,paused:false,player:player(),helicopter:actor(),civilianHelicopter:actor({phase:'crossing',x:-50,z:-50}),events:[],police:[],wanted:0});
let count=0;async function test(name,fn){await fn();count++;console.log('PASS',name);}
await test('true3D range attenuates equal horizontal and vertical separation equally',()=>{
 const p=player(),horizontal=rotorActorTarget(actor({x:100,y:0,z:0}),p),vertical=rotorActorTarget(actor({x:0,y:100,z:0}),p),near=rotorActorTarget(actor({x:0,y:20,z:0}),p);
 assert.equal(horizontal.distance,100);assert.equal(vertical.distance,100);assert.equal(horizontal.gain,vertical.gain);assert(near.gain>vertical.gain);assert.equal(vertical.pan,0);
});
await test('relative stereo pan follows listener heading and attenuates directly overhead',()=>{
 assert(rotorActorTarget(actor({x:0,y:30,z:100}),player()).pan>0);assert(rotorActorTarget(actor({x:0,y:30,z:-100}),player()).pan<0);
 assert(rotorActorTarget(actor({x:100,y:30,z:0}),player({heading:Math.PI/2})).pan<0);assert.equal(rotorActorTarget(actor({x:0,y:80,z:0}),player()).pan,0);
});
await test('distance rolloff is bounded smooth and fully silent by900m',()=>{
 const gains=[0,20,95,300,550,700,899,900,1200].map(x=>rotorActorTarget(actor({x,y:0,z:0}),player()).gain);
 assert(gains.every(g=>g>=0&&g<=.95));for(let i=1;i<gains.length;i++)assert(gains[i]<=gains[i-1]);assert.equal(gains.at(-1),0);assert(gains[6]<1e-6);assert.equal(gains[7],0);
});
await test('relative-velocity Doppler includes vertical motion and stays within8percent',()=>{
 const towards=rotorActorTarget(actor({x:100,y:0,z:0,velocityX:-30}),player()),away=rotorActorTarget(actor({x:100,y:0,z:0,velocityX:30}),player());assert(towards.doppler>1);assert(away.doppler<1);
 assert.equal(rotorActorTarget(actor({velocityX:20,velocityZ:10}),player({velocityX:20,velocityZ:10})).doppler,1);
 assert(rotorActorTarget(actor({x:0,y:60,z:0,verticalVelocity:-20}),player()).doppler>1);assert(rotorActorTarget(actor({x:0,y:60,z:0}),player({vz:10})).doppler>1);
 for(const velocityX of [-1e8,1e8]){const t=rotorActorTarget(actor({velocityX}),player());assert(t.doppler>=.92&&t.doppler<=1.08);}
});
await test('blade pulse follows bounded authored rotorRPM rather than an authenticity claim',()=>{
 const a=actor({rotorRpm:420}),p=player(),t=rotorActorTarget(a,p);assert.equal(t.bladePassHz,28);assert(t.modulationDepth<t.washGain);
 assert.equal(rotorActorTarget({...a,rotorRpm:Infinity},p).bladePassHz,400*4/60);assert.equal(rotorActorTarget({...a,rotorRpm:999999},p).bladePassHz,32);
});
await test('actor phases are audible only when actually active and positioned',()=>{
 for(const phase of ['approach','track','search','withdraw','crossing'])assert(rotorActorTarget(actor({phase}),player()).gain>0);
 for(const change of [{active:false},{visible:false},{phase:'idle'},{x:NaN},{y:Infinity}])assert.equal(rotorActorTarget(actor(change),player()).gain,0);
 assert.equal(rotorActorTarget(undefined,player()).gain,0);assert.equal(rotorActorTarget(actor(),undefined).gain,0);
});
await test('at most two model slots and every inactive lifecycle state has zero gain',()=>{
 const m=model();m.extraHelicopters=Array.from({length:100},()=>actor());assert.equal(rotorAudioTargets(m).length,2);
 for(const options of [{menu:true},{paused:true},{enabled:false},{contextRunning:false}])assert(rotorAudioTargets(m,options).every(t=>t.gain===0));
 for(const state of ['menu','countdown','finished','failed','busted'])assert(rotorAudioTargets({...m,state}).every(t=>t.gain===0));assert(rotorAudioTargets({...m,paused:true}).every(t=>t.gain===0));
});
await test('pure targets tolerate malformed positions velocities and inherited kind names',()=>{
 const m=model(),before=JSON.stringify(m);rotorAudioTargets(m);assert.equal(JSON.stringify(m),before);
 for(const value of [NaN,Infinity,-Infinity,1e308,-1e308]){const t=rotorActorTarget(actor({x:value,velocityX:value,verticalVelocity:value,rotorRpm:value}),player({x:-value,vz:value}),{kind:'__proto__'});for(const v of Object.values(t))if(typeof v==='number')assert(Number.isFinite(v));assert(t.gain>=0&&t.gain<=.95);assert(t.modulationDepth<t.washGain);}
});
await test('two persistent actor graphs add only6sources and20nodes with no frame leaks',async()=>{
 const c=new Context(),a=new GameAudio({context:c});await a.resume();const nodes=c.nodes.length,loops=[...a._loops],m=model();assert.equal(a.rotorVoices.length,2);assert.equal(loops.length,23);assert.equal(new Set(a.rotorVoices.flatMap(v=>[v.bus,v.pan,v.rotor.osc,v.rotor.gain,v.turbine.osc,v.turbine.gain,v.wash.source,v.wash.filter,v.wash.gain,v.modulation])).size,20);
 for(let i=0;i<300;i++){m.helicopter.x=40+i*.1;m.civilianHelicopter.z=-50+i*.1;a.update(m,i/60);assert.equal(c.nodes.length,nodes);assert.deepEqual(a._loops,loops);assert.equal(a._voices.size,0);}assert(a.diagnostics.rotors.every(t=>t.gain>0));a.dispose();
});
await test('audio-rate chop modulation is bounded positive and routed into wash gain only',async()=>{
 const a=new GameAudio({context:new Context()});await a.resume();a.update(model(),0);
 for(const v of a.rotorVoices){assert(v.rotor.osc.connections.includes(v.modulation));assert.deepEqual(v.modulation.connections,[v.wash.gain.gain]);assert(v.modulation.gain.value<v.wash.gain.gain.value);assert.deepEqual(v.bus.connections,[v.pan]);assert.deepEqual(v.pan.connections,[a.compressor]);assert(v.rotor.gain.gain.value<.04);assert(v.turbine.gain.gain.value<=.006);}a.dispose();
});
await test('rotors are silent before unlock and after pause menu or mute',async()=>{
 const c=new Context(),a=new GameAudio({context:c}),m=model();a.update(m,0);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));await a.resume();a.update(m,.1);assert(a.rotorVoices.every(v=>v.bus.gain.value>0));
 a.update(m,.2,{paused:true});assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.update(m,.3,{menu:true});assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.update(m,.4);a.enabled=false;assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.enabled=true;assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.update(m,.5);assert(a.rotorVoices.every(v=>v.bus.gain.value>0));a.dispose();
});
await test('pause without a frame or model still silences helicopter buses',async()=>{
 const a=new GameAudio({context:new Context()});await a.resume();a.update(model(),0);a.update(null,.1,{paused:true});assert(a.rotorVoices.every(v=>v.bus.gain.value===0));assert(a.diagnostics.rotors.every(t=>t.gain===0));a.dispose();
});
await test('context interruption hard-clears bus automation and resume requires fresh targets',async()=>{
 const c=new Context(),a=new GameAudio({context:c}),m=model();await a.resume();a.update(m,0);c.changeState('interrupted');assert(a.rotorVoices.every(v=>v.bus.gain.value===0));assert(a.rotorVoices.every(v=>v.bus.gain.events.some(e=>e[0]==='cancel')));await a.resume();assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.update(m,.1);assert(a.rotorVoices.every(v=>v.bus.gain.value>0));a.dispose();
});
await test('withdrawal restart missing actors and giant teleports cannot leave stale audio',async()=>{
 const a=new GameAudio({context:new Context()}),m=model();await a.resume();a.update(m,0);m.helicopter.active=false;m.civilianHelicopter.active=false;a.update(m,.1);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.update({...model(),helicopter:null,civilianHelicopter:null},.2);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));m.helicopter=actor({x:1e8});a.update(m,.3);assert.equal(a.rotorVoices[0].bus.gain.value,0);assert.equal(a.diagnostics.rotors[0].doppler,1);a.dispose();
});
await test('fallback without StereoPanner remains bounded and dispose disconnects every rotor branch',async()=>{
 const c=new Context();c.createStereoPanner=undefined;const a=new GameAudio({context:c});assert(a.available);await a.resume();a.update(model(),0);const voices=a.rotorVoices;a.dispose();a.dispose();for(const v of voices)for(const n of [v.bus,v.pan,v.rotor.osc,v.rotor.gain,v.turbine.osc,v.turbine.gain,v.wash.source,v.wash.filter,v.wash.gain,v.modulation])assert(n.disconnected);assert.equal(c.listeners.get('statechange').size,0);a.update(model(),1);
});
await test('airtime reward cue fires once only for actual positive boost transfer',async()=>{
 const c=new Context(),a=new GameAudio({context:c}),m=model();await a.resume();m.events=[{id:1,type:'airtime-reward',energyAward:.12,actualEnergyAdded:0}];a.update(m,0);assert.equal(a._voices.size,0);assert.equal(a.diagnostics.airtimeRewardCues,0);
 m.events.push({id:2,type:'airtime-reward',energyAward:.12,actualEnergyAdded:.04});a.update(m,.1);assert.equal(a._voices.size,2);assert.equal(a.diagnostics.airtimeRewardCues,1);a.update(m,.2);assert.equal(a._voices.size,2);assert.equal(a.diagnostics.airtimeRewardCues,1);c.advance(1);assert.equal(a._voices.size,0);a.dispose();
});
await test('airtime cue consumes paused muted suspended and malformed payouts without replay',async()=>{
 for(const mode of ['pause','model-pause','menu','mute','suspend','malformed']){const c=new Context(),a=new GameAudio({context:c}),m=model();await a.resume();a.update(m,0);if(mode==='mute')a.enabled=false;if(mode==='model-pause')m.paused=true;if(mode==='suspend')c.changeState('suspended');m.events=[{id:1,type:'airtime-reward',actualEnergyAdded:mode==='malformed'?NaN:.1}];a.update(m,.1,{paused:mode==='pause',menu:mode==='menu'});assert.equal(a.diagnostics.airtimeRewardCues,0);assert.equal(a._voices.size,0);a.enabled=true;m.paused=false;await a.resume();a.update(m,.2);assert.equal(a._voices.size,0);a.dispose();}
});
await test('airtime event bursts retain existing12voice ceiling and restart clears tails',async()=>{
 const c=new Context(),a=new GameAudio({context:c}),m=model();await a.resume();m.events=Array.from({length:40},(_,i)=>({id:i+1,type:'airtime-reward',actualEnergyAdded:.1}));a.update(m,0);assert.equal(a._voices.size,12);assert.equal(a.diagnostics.airtimeRewardCues,6);const old=[...a._voices];a.update(model(),.1);assert.equal(a._voices.size,0);assert(old.every(v=>v.source.disconnected));a.dispose();
});
await test('actual GameModel civilian pass drives audio and freezes correctly across pause and restart',async()=>{
 const c=new Context(),a=new GameAudio({context:c}),game=new GameModel([{x:0,z:0,y:.18},{x:3000,z:0,y:.18}],{airTraffic:true}).start('time-attack');await a.resume();
 const step=seconds=>{for(let i=0;i<seconds*60;i++){game.update(1/60,{});a.update(game,c.currentTime,{paused:game.paused,dt:1/60});c.advance(1/60);}};
 step(16);assert(game.civilianHelicopter.active);assert(!game.helicopter.active);assert(a.diagnostics.rotors[1].gain>0);assert.equal(a.diagnostics.rotors[0].gain,0);assert.equal(a.diagnostics.rotors[1].bladePassHz/ a.diagnostics.rotors[1].doppler,game.civilianHelicopter.rotorRpm*4/60);
 const before=JSON.stringify(game.civilianHelicopter),clock=game.timer;game.setPaused(true);step(1);assert.equal(JSON.stringify(game.civilianHelicopter),before);assert.equal(game.timer,clock);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));game.setPaused(false);step(.1);assert(a.diagnostics.rotors[1].gain>0);
 game.restart();step(1/60);assert(!game.civilianHelicopter.active);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));assert.equal(a._loops.length,23);a.dispose();
});
await test('actual PoliceAirSupport actor state maps to rotor targets and stop removes it',async()=>{
 const controller=new PoliceAirSupport(),c=new Context(),a=new GameAudio({context:c}),m=model();await a.resume();m.civilianHelicopter=null;m.helicopter=controller.state;m.player.speed=20;
 for(let i=0;i<31*60;i++)controller.update(1/60,{player:m.player,eligible:true,wanted:3,heat:.9,groundPoliceDistance:100,floorAt:()=>0,lineOfSight:()=>true});
 assert(m.helicopter.active);assert(Number.isFinite(m.helicopter.verticalVelocity));a.update(m,31);assert(a.diagnostics.rotors[0].gain>0);assert.equal(a.diagnostics.rotors[1].gain,0);controller.stop();a.update(m,31.1);assert(a.rotorVoices.every(v=>v.bus.gain.value===0));a.dispose();
});

await test('actual physical ramp landing emits one cue for its measured positive transfer',async()=>{
 for(const energy of [.2,1]){const c=new Context(),a=new GameAudio({context:c}),game=new GameModel([{x:0,z:0,y:.18},{x:5000,z:0,y:.18}],{ramps:[{id:'audio-ramp',startS:100,lipS:130,rise:3,halfWidth:3.6}]}).start('free-drive');game.player.energy=energy;await a.resume();
 for(let i=0;i<8*60;i++){game.update(1/60,{throttle:1});a.update(game,c.currentTime,{input:{throttle:1},dt:1/60});c.advance(1/60);}
 const events=game.events.filter(e=>e.type==='airtime-reward');assert.equal(events.length,1);assert(game.events.some(e=>e.type==='ramp-launch'));assert(game.player.grounded);assert.equal(game.player.damage,0);const paid=events[0].actualEnergyAdded>0;assert(paid);assert.equal(a.diagnostics.airtimeRewardCues,1);if(energy===1)assert(events[0].actualEnergyAdded<.001,'Landing assist can spend a tiny amount before refill; this is not an exact zero payout');a.update(game,8.1);assert.equal(a.diagnostics.airtimeRewardCues,1);a.dispose();}
});

console.log(`\n${count} rotor/airtime audio tests passed. Pure targets + stub Web Audio; no listening/browser verification.`);
