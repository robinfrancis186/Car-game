/** Manual diagnostic client. No bot, prediction, 3D renderer, or browser acceptance. */
import WebSocket from 'ws';
import readline from 'node:readline';
const args=process.argv.slice(2),value=(flag,fallback)=>{const i=args.indexOf(flag);return i>=0?args[i+1]:fallback;};
const port=Number(value('--port','8787')),name=value('--name','Driver'),roomCode=value('--join',null);
if(!Number.isInteger(port)||port<1||port>65535)throw new Error('Invalid port');
const endpoint=new URL(value('--url',`http://127.0.0.1:${port}`));
if(endpoint.username||endpoint.password||endpoint.pathname!=='/'||endpoint.search||endpoint.hash||!(endpoint.protocol==='https:'||endpoint.protocol==='http:'&&['127.0.0.1','localhost'].includes(endpoint.hostname)))throw new Error('Use an exact HTTPS origin, or loopback HTTP for local tests');
const response=await fetch(`${endpoint.origin}/manifest`);if(!response.ok)throw new Error(`Service unavailable: ${response.status}`);
const manifest=await response.json();
const ws=new WebSocket(`${endpoint.protocol==='https:'?'wss':'ws'}://${endpoint.host}/room`,{origin:endpoint.origin});let joined,snapshot,seq=0,lastPrint=-1,epoch;
let controls={throttle:0,steer:0,brake:true,boost:false,recover:false};
const send=m=>ws.readyState===WebSocket.OPEN&&ws.send(JSON.stringify(m));
ws.on('message',b=>{const m=JSON.parse(b);
 if(m.type==='hello')send({type:roomCode?'join':'create',name,...(roomCode?{roomCode}:{}),protocolVersion:manifest.protocolVersion,physicsVersion:manifest.physicsVersion,trackHash:manifest.trackHash});
 else if(m.type==='joined'){joined=m;seq=m.lastSeq;epoch=m.epoch;console.log(`Joined as ${name}. PRIVATE INVITE: ${m.roomCode}`);}
 else if(m.type==='snapshot'){snapshot=m;if(epoch!==m.epoch){epoch=m.epoch;seq=0;}const seconds=Math.floor(m.elapsed);if(seconds!==lastPrint||m.status==='results'){lastPrint=seconds;console.log(`${m.status} ${m.elapsed.toFixed(1)}s | ${m.players.map(p=>`${p.name}: ${p.s.toFixed(1)}m ${p.speed.toFixed(1)}m/s ${p.connected?'connected':'disconnected'}`).join(' | ')}`);if(m.results)console.log(m.results);}}
 else if(m.type==='error')console.error(m.code);
});
ws.on('error',e=>console.error(e.message));ws.on('close',()=>{clearInterval(timer);rl.close();});
const timer=setInterval(()=>{if(snapshot&&['countdown','racing'].includes(snapshot.status))send({type:'input',epoch:snapshot.epoch,seq:++seq,clientTick:snapshot.tick,controls});},1000/30);
const rl=readline.createInterface({input:process.stdin,output:process.stdout});
console.log('EXPERIMENTAL MANUAL CLIENT. Commands: ready, start, w (throttle), s (reverse), a/d (steer), center, brake, coast, boost, recover, rematch, quit. Commands persist. Online clock never pauses.');
rl.on('line',line=>{switch(line.trim()){
 case 'ready':send({type:'ready',loaded:true});break;case 'start':case 'rematch':send({type:line.trim()});break;
 case 'w':controls={...controls,throttle:1,brake:false};break;case 's':controls={...controls,throttle:-1,brake:false};break;
 case 'a':controls.steer=-1;break;case 'd':controls.steer=1;break;case 'center':controls.steer=0;break;
 case 'brake':controls={throttle:0,steer:0,brake:true,boost:false,recover:false};break;case 'coast':controls={throttle:0,steer:0,brake:false,boost:false,recover:false};break;
 case 'boost':controls.boost=!controls.boost;break;case 'recover':controls.recover=true;setTimeout(()=>controls.recover=false,100);break;
 case 'quit':ws.close();break;default:console.log('Unknown command');
}});
