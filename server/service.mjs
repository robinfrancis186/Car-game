import http from 'node:http';
import {loadStaticAssets,readStaticAllowlist} from './static-assets.mjs';
import {randomBytes,randomUUID,timingSafeEqual} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {WebSocketServer,WebSocket} from 'ws';
import {RaceWorld} from '../shared/world.mjs';
import {loadData,getManifest} from './data.mjs';
import {ingress,bucket} from './ingress.mjs';
import {NEUTRAL,exact,validControls,versionError,JOIN_KEYS,validName} from '../shared/protocol.mjs';
const validRoomCode=value=>typeof value==='string'&&/^[A-Za-z0-9_-]{16}$/.test(value);
const token=()=>randomBytes(24).toString('base64url');
const matchToken=(a,b)=>typeof b==='string'&&/^[A-Za-z0-9_-]{32}$/.test(b)&&timingSafeEqual(Buffer.from(a),Buffer.from(b));
export async function createService(options={}){
 const config={port:0,countdownTicks:180,reconnectMs:20000,inputTimeoutTicks:15,raceLimitTicks:60*180,roomIdleMs:15*60_000,resultRetentionMs:60_000,...options};
 const policy=ingress(options);let closing=false;
 // Aggregate diagnostics only: no seat, room, input, token or address data.
 let diagnosticAt=performance.now(),diagnosticCpu=process.cpuUsage(),lastOverloadLog=-Infinity;
 const packageRoot=new URL('../',import.meta.url);const publicAssets=await loadStaticAssets(packageRoot,await readStaticAllowlist(packageRoot));
 const manifest=getManifest(options.raceSlice),data=loadData(),rooms=new Map(),metrics={ticks:0,maxTickMs:0,invalidMessages:0,overloads:0,connections:0};let lastWall=performance.now(),accumulator=0;
 const httpServer=http.createServer({maxHeaderSize:8192,headersTimeout:10000,requestTimeout:10000,keepAliveTimeout:5000},(req,res)=>{
  const host=req.headers.host;
  if(!policy.validHost(host,httpServer.address()?.port)){res.writeHead(403);return res.end('Host denied');}
  if(closing){res.writeHead(503);return res.end('Service restarting');}
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Cross-Origin-Resource-Policy','same-origin');
  res.setHeader('Permissions-Policy','camera=(), microphone=(), geolocation=()');
  if(policy.publicMode)res.setHeader('Strict-Transport-Security','max-age=31536000');
  const socketOrigin=policy.publicMode?policy.origin.replace(/^https:/,'wss:'):'ws://'+host;
  res.setHeader('Content-Security-Policy',`default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data: blob:; connect-src 'self' ${socketOrigin}; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`);
  if(req.method!=='GET'||req.headers['transfer-encoding']||Number(req.headers['content-length']||0)!==0){res.writeHead(405,{Connection:'close'});return res.end();}
  if(req.url==='/health'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify(policy.publicMode?{status:'experimental-alpha',capacity:2,persistent:false}:{status:'local-alpha',rooms:rooms.size,...metrics}));}
  if(policy.publicMode&&!policy.httpBudget()){res.writeHead(429,{'Retry-After':'1'});return res.end('Try again later');}
  if(req.url==='/manifest'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify({...manifest,route:data.world.route_points}));}
  if(req.url==='/robots.txt'){res.setHeader('Content-Type','text/plain');return res.end('User-agent: *\nDisallow: /\n');}
  if(publicAssets.serve(req,res))return;res.writeHead(404);res.end();
 });
 httpServer.maxConnections=40;httpServer.maxRequestsPerSocket=60;httpServer.setTimeout(15000);
 httpServer.on('clientError',(_error,socket)=>socket.destroy());
 const wss=new WebSocketServer({noServer:true,maxPayload:2048,perMessageDeflate:false,autoPong:false});
 httpServer.on('upgrade',(req,socket,head)=>{
  const port=httpServer.address()?.port;
  if(closing||req.method!=='GET'||req.url!=='/room'||!policy.validHost(req.headers.host,port)||!policy.validOrigin(req.headers.origin,port)||wss.clients.size>=policy.maxClients||policy.publicMode&&!policy.upgradeBudget()){socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');return;}
  wss.handleUpgrade(req,socket,head,ws=>{socket.setTimeout(0);wss.emit('connection',ws,req);});
 });
 const send=(ws,msg)=>{if(ws?.readyState!==WebSocket.OPEN)return;if(ws.bufferedAmount>128*1024){ws.terminate();return;}ws.send(JSON.stringify(msg));};
 const fail=(ws,code)=>{metrics.invalidMessages++;send(ws,{type:'error',code});if(++ws.context.invalidCount>=20)ws.close(1008,'Invalid messages');};
 const repairHost=room=>{if(room.status==='waiting'&&!room.seats.get(room.hostId)?.ws)room.hostId=[...room.seats.values()].find(seat=>seat.ws)?.id||[...room.seats.keys()][0]||null;};
 const summary=room=>({type:'snapshot',roomCode:room.code,epoch:room.epoch,status:room.status,tick:room.tick,startTick:room.startTick,elapsed:room.world.ticks/60,hostId:room.hostId,players:[...room.seats.values()].map(s=>({...room.world.snapshot(s.id),name:s.name,connected:!!s.ws,ready:s.ready,ack:s.lastSeq,inputStale:room.tick-s.lastInputTick>config.inputTimeoutTicks,dnf:s.dnf})),results:room.results});
 const broadcast=room=>{const m=summary(room);for(const s of room.seats.values())send(s.ws,m);};
 const endRoom=room=>{room.status='results';room.endedAt=performance.now();room.results=[...room.seats.values()].map(s=>{const p=room.world.snapshot(s.id);return {playerId:s.id,name:s.name,status:s.dnf?'dnf':p.state==='finished'?'finished':'dnf',reason:s.dnf|| (p.state==='finished'?null:p.state==='failed'?'vehicle-disabled':'race-timeout'),time:p.state==='finished'?p.result.time:null,penalties:p.penalties,checkpoints:p.nextCheckpoint-1};}).sort((a,b)=>(a.time??Infinity)-(b.time??Infinity)||a.playerId.localeCompare(b.playerId));let rank=0;room.results.forEach((r,i)=>{r.rank=r.status==='finished'?++rank:null;});broadcast(room);};
 wss.on('connection',ws=>{
  metrics.connections++;ws.context={room:null,seat:null,windowStart:performance.now(),count:0,joinedAt:performance.now(),invalidCount:0,controlBudget:bucket(8,2)};ws.alive=true;
  const controlFrame=(data,ping)=>{if(ws.readyState!==WebSocket.OPEN)return;if(!ws.context.controlBudget()||policy.publicMode&&!policy.messageBudget()){ws.close(1008,'Control frame limit');return;}if(ws.bufferedAmount>128*1024){ws.terminate();return;}if(ping)ws.pong(data);else ws.alive=true;};
  ws.on('ping',data=>controlFrame(data,true));ws.on('pong',data=>controlFrame(data,false));ws.on('error',()=>{});send(ws,{type:'hello',...manifest});
  ws.on('message',(raw,binary)=>{
   if(ws.readyState!==WebSocket.OPEN||closing)return;
   if(policy.publicMode&&!policy.messageBudget()){ws.close(1013,'Server busy');return;}
   const c=ws.context,now=performance.now();if(now-c.windowStart>=1000){c.windowStart=now;c.count=0;}if(++c.count>90){fail(ws,'RATE_LIMIT');ws.close(1008,'Rate limit');return;}
   if(binary)return fail(ws,'TEXT_REQUIRED');let m;try{m=JSON.parse(raw.toString());}catch{return fail(ws,'MALFORMED_JSON');}if(!m||typeof m!=='object'||Array.isArray(m))return fail(ws,'INVALID_MESSAGE');
   if(['create','join','reconnect'].includes(m.type)){
    if(c.room)return fail(ws,'ALREADY_JOINED');const error=versionError(m,manifest);if(error)return fail(ws,error);
    if(m.type==='reconnect'){
     if(!exact(m,['type','roomCode','playerId','token','protocolVersion','physicsVersion','trackHash'])||!validRoomCode(m.roomCode)||typeof m.playerId!=='string'||!/^[0-9a-f-]{36}$/.test(m.playerId))return fail(ws,'INVALID_RECONNECT');
     const room=rooms.get(m.roomCode),seat=room?.seats.get(m.playerId);
     if(!seat||seat.ws||seat.dnf||!seat.disconnectAt||now-seat.disconnectAt>config.reconnectMs||!matchToken(seat.token,m.token))return fail(ws,'RECONNECT_DENIED');
     seat.ws=ws;seat.token=token();seat.disconnectAt=null;seat.controls=NEUTRAL;seat.lastInputTick=-Infinity;c.room=room;c.seat=seat;repairHost(room);
     send(ws,{type:'joined',roomCode:room.code,playerId:seat.id,reconnectToken:seat.token,reconnected:true,epoch:room.epoch,lastSeq:seat.lastSeq});broadcast(room);return;
    }
    if(!exact(m,m.type==='create'?JOIN_KEYS:[...JOIN_KEYS,'roomCode'])||!validName(m.name)||(m.type==='join'&&!validRoomCode(m.roomCode)))return fail(ws,'INVALID_JOIN');
    let room;
    if(m.type==='create'){
     if(rooms.size>=policy.maxRooms)return fail(ws,'CAPACITY');if(policy.publicMode&&!policy.createBudget())return fail(ws,'RATE_LIMIT');const code=randomBytes(12).toString('base64url');
     room={code,epoch:randomUUID(),status:'waiting',seats:new Map(),world:new RaceWorld(data,config.raceSlice),tick:0,startTick:null,hostId:null,createdAt:now,endedAt:null,results:null};rooms.set(code,room);
    }else{room=rooms.get(m.roomCode);if(!room)return fail(ws,'ROOM_NOT_FOUND');if(room.status!=='waiting')return fail(ws,'RACE_ALREADY_STARTED');if(room.seats.size>=2)return fail(ws,'ROOM_FULL');}
    const id=randomUUID(),seat={id,name:m.name,ws,token:token(),ready:false,lastSeq:0,lastInputTick:-Infinity,controls:NEUTRAL,disconnectAt:null,dnf:null};room.seats.set(id,seat);room.world.add(id);if(!room.hostId)room.hostId=id;repairHost(room);c.room=room;c.seat=seat;
    send(ws,{type:'joined',roomCode:room.code,playerId:id,reconnectToken:seat.token,reconnected:false,epoch:room.epoch,lastSeq:0});broadcast(room);return;
   }
   const room=c.room,seat=c.seat;if(!room||!seat)return fail(ws,'JOIN_REQUIRED');
   if(m.type==='ready'){
    if(!exact(m,['type','loaded'])||m.loaded!==true||room.status!=='waiting')return fail(ws,'INVALID_READY');if(!seat.ready){seat.ready=true;broadcast(room);}return;
   }
   if(m.type==='start'){
    if(!exact(m,['type'])||seat.id!==room.hostId)return fail(ws,'HOST_REQUIRED');
    if(room.status!=='waiting'||room.seats.size!==2||[...room.seats.values()].some(s=>!s.ready||!s.ws))return fail(ws,'NOT_READY');
    room.status='countdown';room.startTick=room.tick+config.countdownTicks;broadcast(room);return;
   }
   if(m.type==='input'){
    if(!exact(m,['type','epoch','seq','clientTick','controls'])||!validControls(m.controls)||!Number.isSafeInteger(m.seq)||m.seq<1||m.seq>2147483647||!Number.isSafeInteger(m.clientTick))return fail(ws,'INVALID_INPUT');
    if(m.epoch!==room.epoch)return fail(ws,'EPOCH_MISMATCH');if(!['countdown','racing'].includes(room.status)||seat.dnf)return fail(ws,'NOT_RACING');
    if(m.seq<=seat.lastSeq)return fail(ws,'STALE_SEQUENCE');if(m.seq>seat.lastSeq+4096)return fail(ws,'SEQUENCE_GAP');
    if(m.clientTick<room.tick-120)return fail(ws,'STALE_INPUT');if(m.clientTick>room.tick+6)return fail(ws,'FUTURE_INPUT');
    seat.lastSeq=m.seq;seat.lastInputTick=room.tick;seat.controls=m.controls;return;
   }
   if(m.type==='rematch'){
    if(!exact(m,['type'])||seat.id!==room.hostId)return fail(ws,'HOST_REQUIRED');if(room.status!=='results'||[...room.seats.values()].some(s=>!s.ws))return fail(ws,'INVALID_REMATCH');
    room.epoch=randomUUID();room.world=new RaceWorld(data,config.raceSlice);room.status='waiting';room.startTick=null;room.results=null;room.endedAt=null;room.createdAt=now;
    for(const s of room.seats.values()){room.world.add(s.id);s.ready=false;s.lastSeq=0;s.lastInputTick=-Infinity;s.controls=NEUTRAL;s.dnf=null;}broadcast(room);return;
   }
   fail(ws,'UNKNOWN_MESSAGE');
  });
  ws.on('close',()=>{const {room,seat}=ws.context;if(!room||!seat||seat.ws!==ws)return;seat.ws=null;seat.controls=NEUTRAL;seat.disconnectAt=performance.now();if(room.status==='waiting'){seat.ready=false;repairHost(room);}broadcast(room);});
 });
 function step(){const began=performance.now();metrics.ticks++;for(const [code,room] of rooms){room.tick++;
  for(const seat of room.seats.values())if(!seat.ws&&seat.disconnectAt&&began-seat.disconnectAt>config.reconnectMs&&!seat.dnf){
   if(room.status==='waiting'){room.seats.delete(seat.id);room.world.drivers.delete(seat.id);repairHost(room);}else if(!['finished','failed'].includes(room.world.snapshot(seat.id).state))seat.dnf='disconnect-timeout';
  }
  if(!room.seats.size||(room.status==='waiting'&&began-room.createdAt>config.roomIdleMs)||(room.status==='results'&&began-room.endedAt>config.resultRetentionMs)){
   for(const seat of room.seats.values()){send(seat.ws,{type:'closed',reason:'room-expired'});seat.ws?.close(1000,'Room expired');}rooms.delete(code);continue;
  }
  if(room.status==='countdown'&&room.tick>=room.startTick)room.status='racing';
  if(room.status==='racing'){
   const inputs=new Map([...room.seats.values()].map(s=>[s.id,!s.ws||s.dnf||room.tick-s.lastInputTick>config.inputTimeoutTicks?NEUTRAL:s.controls]));
   room.world.step(inputs);
   if(room.world.ticks>=config.raceLimitTicks||[...room.seats.values()].every(s=>s.dnf||['finished','failed'].includes(room.world.snapshot(s.id).state)))endRoom(room);
  }
  if(room.tick%3===0)broadcast(room);
 }metrics.lastTickMs=performance.now()-began;metrics.maxTickMs=Math.max(metrics.maxTickMs,metrics.lastTickMs);}
 const timer=setInterval(()=>{const now=performance.now(),delta=now-lastWall;lastWall=now;accumulator+=delta;
  if(accumulator>250){metrics.overloads++;
   const activeRaces=[...rooms.values()].filter(room=>['countdown','racing'].includes(room.status)).length;
   if(policy.publicMode&&activeRaces&&now-lastOverloadLog>=60000){const cpu=process.cpuUsage(diagnosticCpu),round=n=>Math.round(n*1000)/1000;lastOverloadLog=now;console.warn(JSON.stringify({event:'runtime-overload',loopDeltaMs:round(delta),backlogMs:round(accumulator),lastStepMs:round(metrics.lastTickMs||0),maxStepMs:round(metrics.maxTickMs),sampleWindowMs:round(now-diagnosticAt),cpuUserMs:round(cpu.user/1000),cpuSystemMs:round(cpu.system/1000),activeRaces,guardMs:250}));}
   for(const room of rooms.values())if(['countdown','racing'].includes(room.status)){for(const s of room.seats.values())s.dnf||='server-overload';endRoom(room);}accumulator=0;return;}
  while(accumulator>=1000/60){accumulator-=1000/60;step();}
  if(now-diagnosticAt>=1000){diagnosticAt=now;diagnosticCpu=process.cpuUsage();}
 },4);
 const heartbeat=setInterval(()=>{for(const ws of wss.clients){if(!ws.context.room&&performance.now()-ws.context.joinedAt>10000||policy.publicMode&&performance.now()-ws.context.joinedAt>20*60_000||!ws.alive){ws.terminate();continue;}ws.alive=false;ws.ping();}},5000);
 await new Promise((resolve,reject)=>{httpServer.once('error',reject);httpServer.listen(config.port,policy.host,()=>{httpServer.removeListener('error',reject);resolve();});}).catch(error=>{clearInterval(timer);clearInterval(heartbeat);wss.close();throw error;});
 return {port:httpServer.address().port,manifest,rooms,metrics,async close(){if(closing)return;closing=true;clearInterval(timer);clearInterval(heartbeat);for(const ws of wss.clients){send(ws,{type:'closed',reason:'server-restart'});ws.close(1012,'Service restart');}const force=setTimeout(()=>{for(const ws of wss.clients)ws.terminate();httpServer.closeAllConnections();},500);await new Promise(resolve=>wss.close(resolve));await new Promise(resolve=>httpServer.close(resolve));clearTimeout(force);rooms.clear();}};
}
