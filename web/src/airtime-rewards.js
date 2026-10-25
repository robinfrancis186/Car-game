/** Original bounded boost-only reward. Not a reproduced third-party formula. */
export class AirtimeRewards {
 constructor(){this.reset();}
 reset(){this.used=new Set();this.lastAwardTime=-Infinity;this.sequence=0;this.episode=null;this.state={active:false,seconds:0,rampId:null,eligible:false,reason:null,lastReward:null,energyAwarded:0};return this.state;}
 cancel(reason='reset'){if(this.episode)this.invalidate(reason);this.episode=null;this.state.active=false;this.state.seconds=0;this.state.rampId=null;this.state.eligible=false;}
 invalidate(reason){if(this.episode){this.episode.reason||=reason;this.state.eligible=false;this.state.reason=this.episode.reason;}}
 begin({rampId,player,time}){
  const reason=this.used.has(rampId)?'ramp-already-rewarded':time-this.lastAwardTime<10?'cooldown':this.state.energyAwarded>=.30-1e-9?'run-cap':null;
  this.episode={id:++this.sequence,rampId,time,x:player.x,y:player.y,z:player.z,damage:player.damage,lastX:player.x,lastY:player.y,lastZ:player.z,seconds:0,distance:0,reason};
  Object.assign(this.state,{active:true,seconds:0,rampId,eligible:!reason,reason});
 }
 update(dt,{player,input={},time,contact=false,landingSpeed=null}){
  const e=this.episode;if(!e)return null;
  const dx=player.x-e.lastX,dz=player.z-e.lastZ,dy=player.y-e.lastY,travel=Math.hypot(dx,dz);e.lastX=player.x;e.lastY=player.y;e.lastZ=player.z;
  if(travel>2.5||Math.abs(dy)>1.5)this.invalidate('discontinuity');
  if(input.flight||input.flip||player.flipActive)this.invalidate('manual-flight');
  if(contact||player.damage>e.damage+.00001)this.invalidate('contact');
  e.seconds+=dt;e.distance+=travel;this.state.seconds=e.seconds;
  if(e.seconds>8||e.distance>450)this.invalidate('episode-limit');
  if(!player.grounded)return null;
  const straightDistance=Math.hypot(player.x-e.x,player.z-e.z);
  if(e.seconds<.65||straightDistance<12)this.invalidate('too-short');
  if(!player.onRoadDeck||Math.abs(player.lateralSpeed)>5||!Number.isFinite(landingSpeed)||landingSpeed>6)this.invalidate('unclean-landing');
  const result={episodeId:e.id,rampId:e.rampId,airtimeSeconds:e.seconds,distanceMetres:straightDistance,energyAward:0,actualEnergyAdded:0,reason:e.reason};
  if(!e.reason){result.energyAward=Math.max(0,Math.min(.12,.04*e.seconds,.30-this.state.energyAwarded));result.actualEnergyAdded=Math.min(result.energyAward,Math.max(0,1-player.energy));player.energy=Math.min(1,player.energy+result.actualEnergyAdded);this.state.energyAwarded+=result.actualEnergyAdded;this.lastAwardTime=time;this.used.add(e.rampId);}
  this.episode=null;Object.assign(this.state,{active:false,eligible:false,reason:result.reason,lastReward:result});return result;
 }
}
