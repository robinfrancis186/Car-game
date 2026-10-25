/** Optional SOLO façade. The ordinary GameModel module, save and economy are untouched. */
import {GameModel,SCENARIOS} from './gameplay.js';
import {SurfaceDrive} from './surface-drive.js';
import {normalizeRibbonProfile,sampleRibbon,projectRibbon} from './surface-ribbon.js';
export class StuntGameModel extends GameModel{
 constructor(routeOrProfile,options={}){
  const raw=Array.isArray(routeOrProfile)?options.surfaceProfile:routeOrProfile,profile=normalizeRibbonProfile(raw),route=[{x:0,y:profile.baseY,z:0},{x:profile.length,y:profile.baseY,z:0}];
  super(route,{vehicleId:options.vehicleId,upgrades:options.upgrades,maxSteer:options.maxSteer,airTraffic:false,ramps:[]});
  this.ribbonProfile=profile;this.isSurfaceTest=true;this.surfaceDrive=new SurfaceDrive(profile,options);this._adopt();this.state='menu';
 }
 _adopt(){
  this.player=this.surfaceDrive.player;this.vehicleStats=this.surfaceDrive.vehicleStats;this.scenario=Object.freeze({...SCENARIOS.find(s=>s.id==='free-drive'),name:'Surface Test',title:'SOLO SURFACE PROOF',goal:'Maintain 29 km/h on the wall; steer locally; R returns to flat road. No rewards.'});this.rivals=[];this.police=[];this.coins=[];this.coinsCollected=0;this.collectedCoinIds=new Set();this.checkpoints=[];this.totalCheckpoints=0;this.nextCheckpoint=0;this.position=1;this.wanted=this.heat=this.arrestProgress=0;this.escaped=false;this.pursuit='clear';this.result=null;this.timeLimit=this.timeRemaining=Infinity;this.penalties=0;this.recoveryWarning=null;this.recoveryCooldown=0;this.automaticRecoveries=0;this.recoveries=0;this.timer=0;this.countdown=0;this.events=[];this._eventSequence=0;this.message='SURFACE TEST / SOLO / NO REWARDS';this.messageUntil=4;this.paused=false;this.wrongWay=false;this.airtime={active:false,eligible:false,seconds:0,energyAwarded:0,lastReward:null};this.helicopter={active:false,visible:false,phase:'idle'};this.civilianHelicopter={active:false,visible:false,phase:'idle'};this._sync();
 }
 _sync(){this.timer=this.surfaceDrive.time;this.recoveries=this.surfaceDrive.recoveries;this.damage=this.player.damage;this.surfaceBank=this.player.bankAngle;const endpoint=this.player.velocityX>1&&this.player.x>this.ribbonProfile.length-70?'end':this.player.velocityX<-1&&this.player.x<70?'start':null;this.recoveryWarning=endpoint?{reason:'route-end',endpoint,warningOnly:true}:null;this.progress=Math.max(0,Math.min(1,this.player.s/this.ribbonProfile.length));this.distanceRemaining=Math.max(0,this.ribbonProfile.length-this.player.s);for(const e of this.surfaceDrive.consumeEvents()){const {id,type,text,time,...details}=e;this._emit(type,text,details);}}
 start(id='free-drive'){if(id!=='free-drive')throw new RangeError('The surface proof supports free-drive only; no race or rewards');this.surfaceDrive.reset();this._surfaceEventSequence=0;this._adopt();this.state='racing';this._emit('start','SURFACE TEST / MAINTAIN 29 KM/H ON WALL');return this;}
 update(dt,input={}){if(this.paused||this.state!=='racing')return this;this.surfaceDrive.update(dt,input);this._sync();return this;}
 setPaused(value){this.paused=!!value;this.surfaceDrive?.setPaused(value);return this;}
 recover(){if(this.paused||this.state!=='racing')return false;const ok=this.surfaceDrive.recover('manual');if(ok)this._sync();return ok;}
 setDynamicObstacles(){return this;}
 surfaceSample(s,l=0){return sampleRibbon(this.ribbonProfile,s,l);}
 surfaceProject(point){return projectRibbon(this.ribbonProfile,point);}
 sampleTerrain(){return {y:0,gradientX:0,gradientZ:0,grade:0,heading:0,inside:true,layer:'terrain'};}
 projectToRoute(x,z,hintS=null){
  // During super construction ribbonProfile is not assigned yet. The flat center
  // line remains the public minimap/progress route; full 3D queries use surfaceProject.
  return super.projectToRoute(x,z,hintS);
 }
}
