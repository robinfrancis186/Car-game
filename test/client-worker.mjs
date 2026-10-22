/** Automated NETWORK TEST DRIVER, not an AI opponent offered to players. */
import WebSocket from 'ws';
let ws,manifest,joined,snapshot,seq=0,driver=null,controls=null,timer;
const send=m=>ws?.readyState===WebSocket.OPEN&&ws.send(JSON.stringify(m));
const controlsMessage=c=>({type:'input',seq:++seq,epoch:snapshot?.epoch,clientTick:snapshot?.tick??0,controls:c});
const angle=x=>Math.atan2(Math.sin(x),Math.cos(x));
process.on('message',async m=>{
 if(m.type==='connect'){
  const endpoint=new URL(m.url||`http://127.0.0.1:${m.port}`);
  if(endpoint.username||endpoint.password||endpoint.pathname!=='/'||endpoint.search||endpoint.hash||!(endpoint.protocol==='https:'||endpoint.protocol==='http:'&&['127.0.0.1','localhost'].includes(endpoint.hostname)))throw new Error('Invalid test endpoint');
  manifest=await(await fetch(`${endpoint.origin}/manifest`)).json();ws=new WebSocket(`${endpoint.protocol==='https:'?'wss':'ws'}://${endpoint.host}/room`,{origin:endpoint.origin});
  ws.on('open',()=>process.send({type:'open',pid:process.pid}));ws.on('error',e=>process.send({type:'socket-error',message:e.message}));ws.on('close',()=>process.send({type:'socket-closed'}));
  ws.on('message',b=>{const x=JSON.parse(b);if(x.type==='hello')manifest={...manifest,...x};if(x.type==='joined'){joined=x;seq=x.lastSeq;}if(x.type==='snapshot'){snapshot=x;if(x.epoch!==joined?.epoch&&joined){joined.epoch=x.epoch;seq=0;}}process.send(x);});
 }else if(m.type==='create'||m.type==='join'||m.type==='reconnect')send({...m,protocolVersion:manifest.protocolVersion,physicsVersion:manifest.physicsVersion,trackHash:manifest.trackHash});
 else if(m.type==='raw')ws.send(m.value);
 else if(m.type==='send')send(m.value);
 else if(m.type==='input')send(controlsMessage(m.controls));
 else if(m.type==='drive'){
  driver=m.mode;controls=m.controls;clearInterval(timer);timer=setInterval(()=>{
   if(!snapshot||!['racing','countdown'].includes(snapshot.status))return;
   const p=snapshot.players.find(p=>p.id===joined?.playerId);if(!p)return;
   if(driver==='follow'){
    const route=manifest.route;let s=0,target=route.at(-1);for(let i=1;i<route.length;i++){s+=Math.hypot(route[i][0]-route[i-1][0],route[i][2]-route[i-1][2]);if(s>p.s+7){target=route[i];break;}}
    const error=angle(Math.atan2(target[2]-p.z,target[0]-p.x)-p.heading);
    send(controlsMessage({throttle:p.speed<13?1:0,steer:Math.max(-1,Math.min(1,error*2)),brake:p.speed>15,boost:false,recover:false}));
   }else if(controls)send(controlsMessage(controls));
  },1000/30);
 }else if(m.type==='stop-drive'){clearInterval(timer);driver=null;controls=null;}
 else if(m.type==='drop'){clearInterval(timer);ws.terminate();}
 else if(m.type==='stop'){clearInterval(timer);ws?.terminate();process.exit(0);}
});
