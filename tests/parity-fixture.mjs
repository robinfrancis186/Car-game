import {RaceWorld} from '../shared/world.mjs';
import {loadData} from '../server/data.mjs';
export const IDs=['12345678-1234-1234-1234-123456789012','12345678-1234-1234-1234-123456789013'];
export const data=loadData(),route=data.world.route_points.map(p=>({x:p[0],y:p[1],z:p[2]}));
export function authoritativeFixture(){
 const world=new RaceWorld(data);IDs.forEach(id=>world.add(id));
 return{world,snapshot:{type:'snapshot',roomCode:'abcdefghijklmnop',epoch:'11111111-1111-1111-1111-111111111111',status:'racing',tick:100,startTick:60,elapsed:40/60,hostId:IDs[0],players:IDs.map((id,i)=>({...world.snapshot(id),name:'Driver '+(i+1),connected:true,ready:true,ack:0,inputStale:false,dnf:null})),results:null}};
}
