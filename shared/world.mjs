/** One static world + independent driver contexts; deliberately NO car contact or moving traffic. */
import {GameModel, buildCourseObstacles} from './gameplay.js';
import {worldPhysicsOptions} from './tracks.js';
import {createWaterQuery} from './water.js';
const STATIC = new Set(['route','segments','routeLength','startS','endS','length','terrainY','terrainGrid','roadSections','elevatedCorridors','seed','upgrades','vehicleStats','roadHalfWidth','maxSteer','obstacles','_dynamicObstacles','_obstacleGrid','checkpoints']);
export class RaceWorld {
 constructor(data, slice={startS:2200,endS:3350}) {
  this.data=data; this.isWater=createWaterQuery(data.water); this.drivers=new Map(); this.ticks=0;
  this.model=new GameModel(data.world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]})),{...slice,...worldPhysicsOptions(data.world),obstacles:[...buildCourseObstacles(data.world,data.furniture.colliders),...data.infrastructure.colliders],seed:267,upgrades:{},maxSteer:.57});
 }
 capture(){return Object.fromEntries(Object.entries(this.model).filter(([k])=>!STATIC.has(k)));}
 add(id){this.model.start('time-attack');this.model.state='racing';this.model.countdown=0;this.model.timeLimit=Infinity;this.model.timeRemaining=Infinity;const d={id,state:this.capture(),waterCheck:0,lastRecover:false};this.drivers.set(id,d);return d;}
 step(inputs) {
  this.ticks++;
  for(const [id,d] of this.drivers){
   Object.assign(this.model,d.state);
   if(this.model.state==='racing'){
    const input=inputs.get(id)||{};
    if(input.recover&&!d.lastRecover)this.model.recover();
    d.lastRecover=!!input.recover;
    this.model.update(1/60,{...input,flight:false,ultraBoost:false,flip:false,lift:0});
    d.waterCheck+=1/60;
    if(this.model.state==='racing'&&d.waterCheck>.2){d.waterCheck=0;const p=this.model.player;
     if(p.y<.5&&p.altitude<.3&&this.model.projectToRoute(p.x,p.z,p.s).distance>4.3&&this.isWater(p.x,p.z)){
      this.model.recover();this.model._emit('water-contact','WATER CONTACT / RECOVERED +5 S');
     }
    }
   }
   d.state=this.capture();
  }
 }
 snapshot(id){const d=this.drivers.get(id),s=d.state,p=s.player;return {id,x:p.x,y:p.y,z:p.z,s:p.s,heading:p.heading,speed:p.speed,velocityX:p.velocityX,velocityZ:p.velocityZ,steer:p.steer,energy:p.energy,damage:p.damage,offRoad:p.offRoad,grounded:p.grounded,state:s.state,nextCheckpoint:s.nextCheckpoint,totalCheckpoints:s.totalCheckpoints,penalties:s.penalties,recoveries:s.recoveries,time:s.timer,result:s.result,events:s.events.slice(-6)};}
}
