/** Manual, authoritative-snapshot UI. No local simulation, prediction or bots. */
const $=id=>document.getElementById(id);
const STORAGE_KEY='kerala-public-alpha-session-v1';
const COLORS=['#ecc17b','#7fd2d8'];
const keys=new Set();
let manifest=null,ws=null,session=null,snapshot=null,latestAt=0,sequence=0,epoch=null;
let pendingAction=null,intentionalClose=false,retryTimer=null,reconnectDeadline=0,recoverEdge=false,noticeCode='';
const text=(id,value)=>{$(id).textContent=String(value);};
const notify=message=>text('notice',message);
const now=()=>performance.now();
const isConnected=()=>ws?.readyState===WebSocket.OPEN&&!!session;
const send=message=>{if(ws?.readyState===WebSocket.OPEN)ws.send(JSON.stringify(message));};
const credentials=()=>({protocolVersion:manifest.protocolVersion,physicsVersion:manifest.physicsVersion,trackHash:manifest.trackHash});
const formatTime=seconds=>`${String(Math.floor(seconds/60)).padStart(2,'0')}:${(seconds%60).toFixed(2).padStart(5,'0')}`;
function setConnection(label,live=false){text('connection-state',label);$('connection-dot').classList.toggle('live',live);}
function storeSession(){try{if(session)sessionStorage.setItem(STORAGE_KEY,JSON.stringify(session));else sessionStorage.removeItem(STORAGE_KEY);}catch{notify('Session storage is unavailable. A page reload cannot restore this seat.');}}
function loadSession(){try{const s=JSON.parse(sessionStorage.getItem(STORAGE_KEY)||'null');return s&&typeof s.roomCode==='string'&&typeof s.playerId==='string'&&typeof s.token==='string'?s:null;}catch{return null;}}
function clearControls(){keys.clear();recoverEdge=false;}
function controls(){const focused=!document.hidden&&document.hasFocus();return {throttle:focused?Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')):0,steer:focused?Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft')):0,brake:!focused||keys.has('Space'),boost:focused&&(keys.has('ShiftLeft')||keys.has('ShiftRight')),recover:focused&&recoverEdge};}
function sendInput(){if(!isConnected()||!snapshot||!['countdown','racing'].includes(snapshot.status))return;const own=snapshot.players.find(p=>p.id===session.playerId);if(own?.dnf)return;send({type:'input',epoch,seq:++sequence,clientTick:snapshot.tick,controls:controls()});recoverEdge=false;}
function setBusy(busy){$('create').disabled=busy||!manifest;$('join').disabled=busy||!manifest;}
function connect(action){
  clearTimeout(retryTimer);pendingAction=action;intentionalClose=false;setBusy(true);setConnection(action.type==='reconnect'?'Reconnecting':'Connecting');
  const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/room`);ws=socket;
  socket.addEventListener('message',event=>{
    if(socket!==ws)return;
    let message;try{message=JSON.parse(event.data);}catch{notify('Invalid server message; reconnecting.');socket.close();return;}
    if(message.type==='hello'){
      if(['protocolVersion','physicsVersion','trackHash'].some(k=>message[k]!==manifest[k])){intentionalClose=true;socket.close();setConnection('Build mismatch');notify('Client/server track or physics mismatch. Reload the page before joining.');setBusy(false);return;}
      send({...pendingAction,...credentials()});
    }else if(message.type==='joined'){
      session={roomCode:message.roomCode,playerId:message.playerId,token:message.reconnectToken};storeSession();epoch=message.epoch;sequence=message.lastSeq||0;reconnectDeadline=0;pendingAction=null;noticeCode='';
      text('room-code',message.roomCode);$('entry').hidden=true;$('room').hidden=false;setConnection('Connected',true);notify(message.reconnected?'Reconnected to the same server-owned seat.':'Share the room code with the second driver. Both drivers must click Ready.');
    }else if(message.type==='snapshot'){
      if(!session||message.roomCode!==session.roomCode)return;
      if(epoch!==message.epoch){epoch=message.epoch;sequence=0;clearControls();noticeCode='';notify('New race. Both drivers need to click Ready again.');}
      snapshot=message;latestAt=now();updateRoom();
    }else if(message.type==='closed'){
      intentionalClose=true;notify(`Room closed: ${message.reason}.`);session=null;storeSession();socket.close();showEntry();
    }else if(message.type==='error'){
      const labels={NOT_READY:'Both drivers must be connected and ready.',ROOM_NOT_FOUND:'That room code was not found.',ROOM_FULL:'This room already has two drivers.',RACE_ALREADY_STARTED:'This race has started. Join a new private room instead.',INVALID_JOIN:'Use a name of 1–24 characters without angle brackets.',HOST_REQUIRED:'Only the current lobby host can do that.',RATE_LIMIT:'Too many messages. The connection was closed.',RECONNECT_DENIED:'Reconnection has not been accepted. Retrying within the 20-second window.'};
      if(message.code!==noticeCode){notify(labels[message.code]||`Server rejected message: ${message.code}`);noticeCode=message.code;}
      if(pendingAction?.type==='reconnect'){socket.close();return;}
      if(!session){intentionalClose=true;socket.close();setBusy(false);setConnection('Not connected');}
    }
  });
  socket.addEventListener('close',()=>{
    if(socket!==ws)return;clearControls();setConnection('Disconnected');updateRoom();
    if(intentionalClose)return;
    if(session){
      if(!reconnectDeadline)reconnectDeadline=now()+20000;
      if(now()<reconnectDeadline){setConnection('Reconnecting');notify('Connection lost. Reconnecting for up to 20 seconds; the race continues.');retryTimer=setTimeout(()=>connect({type:'reconnect',roomCode:session.roomCode,playerId:session.playerId,token:session.token}),600);}
      else{notify('The 20-second reconnect window ended. This seat cannot be restored; the server may record DNF.');session=null;storeSession();showEntry();}
    }else{setBusy(false);notify('Could not connect. The free server may be waking or restarting. Wait about a minute, then try again.');}
  });
  socket.addEventListener('error',()=>{});
}
function showEntry(){clearTimeout(retryTimer);clearControls();snapshot=null;latestAt=0;epoch=null;sequence=0;$('entry').hidden=false;$('room').hidden=true;setBusy(false);text('race-state','Coastal test course');text('snapshot-status','Waiting for a private room');text('race-clock','00:00.00');text('checkpoint','— / —');text('speed','— KM/H');text('penalties','0.0 S');}
function leave(){intentionalClose=true;clearTimeout(retryTimer);session=null;storeSession();ws?.close(1000,'Left room');ws=null;showEntry();setConnection('Not connected');notify('Left the room. Any active race continues on the server.');}
function updateRoom(){
  if(!snapshot||!session)return;const own=snapshot.players.find(p=>p.id===session.playerId),host=snapshot.hostId===session.playerId,connected=isConnected();
  const rows=snapshot.players.map((p,i)=>{const row=document.createElement('div');row.className='driver';const swatch=document.createElement('span');swatch.className='swatch';swatch.style.background=COLORS[i%COLORS.length];const info=document.createElement('div');const name=document.createElement('div');name.className='driver-name';name.textContent=p.name+(p.id===session.playerId?' · you':'');const sub=document.createElement('div');sub.className='driver-sub';sub.textContent=(p.id===snapshot.hostId?'Lobby host':'Driver')+' · '+(p.connected?'connected':'seat reserved');info.append(name,sub);const state=document.createElement('span');state.className='driver-state';state.textContent=p.dnf?'DNF':snapshot.status==='waiting'?(p.ready?'READY':'not ready'):p.state==='finished'?'FINISHED':p.inputStale?'safe brake':'DRIVING';row.append(swatch,info,state);return row;});
  $('players').replaceChildren(...rows);$('ready').hidden=snapshot.status!=='waiting';$('ready').disabled=!connected||!!own?.ready;text('ready',own?.ready?'Ready ✓':'Ready');$('start').hidden=!host||snapshot.status!=='waiting';$('start').disabled=!connected||snapshot.players.length!==2||snapshot.players.some(p=>!p.ready||!p.connected);
  text('race-state',{waiting:'Waiting for drivers',countdown:'Shared start countdown',racing:'Race in progress',results:'Race results'}[snapshot.status]||snapshot.status);text('snapshot-status',`Server tick ${snapshot.tick} · ${manifest.snapshotRate} snapshots/s · no prediction`);text('race-clock',formatTime(snapshot.elapsed||0));
  if(own){text('speed',`${Math.max(0,Math.round(own.speed*3.6))} KM/H`);text('checkpoint',`${Math.min(own.nextCheckpoint-1,own.totalCheckpoints)} / ${own.totalCheckpoints}`);text('penalties',`${own.penalties.toFixed(1)} S`);}
  $('results').hidden=snapshot.status!=='results';$('rematch').hidden=!host;$('rematch').disabled=!connected||snapshot.players.some(p=>!p.connected);
  if(snapshot.results){$('result-list').replaceChildren(...snapshot.results.map(r=>{const li=document.createElement('li');const title=document.createElement('div');title.className='result-title';title.textContent=`${r.rank?`${r.rank}. `:''}${r.name} · ${r.status==='finished'?formatTime(r.time):'DNF'}`;const detail=document.createElement('div');detail.textContent=`${r.checkpoints} checkpoints · ${r.penalties.toFixed(1)}s penalties${r.reason?' · '+r.reason:''}`;li.append(title,detail);return li;}));}
}
function validName(){const name=$('driver-name').value.trim();if(!name||name.length>24||/[\x00-\x1f\x7f<>]/.test(name)){notify('Enter a name of 1–24 characters without angle brackets.');return null;}return name;}
$('create-form').addEventListener('submit',event=>{event.preventDefault();const name=validName();if(name&&manifest)connect({type:'create',name});});
$('join-form').addEventListener('submit',event=>{event.preventDefault();const name=validName(),roomCode=$('join-code').value.trim();if(name&&roomCode&&manifest)connect({type:'join',name,roomCode});});
$('ready').addEventListener('click',()=>{send({type:'ready',loaded:true});$('map').focus();});
$('start').addEventListener('click',()=>{send({type:'start'});$('map').focus();});
$('rematch').addEventListener('click',()=>send({type:'rematch'}));$('leave').addEventListener('click',leave);
const keyCodes=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space','ShiftLeft','ShiftRight','KeyR']);
addEventListener('keydown',event=>{if(!keyCodes.has(event.code)||/^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)||!session)return;event.preventDefault();if(event.code==='KeyR'&&!event.repeat)recoverEdge=true;keys.add(event.code);});
addEventListener('keyup',event=>{keys.delete(event.code);if(keyCodes.has(event.code)&&!/^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName)&&session)event.preventDefault();});
addEventListener('blur',()=>{clearControls();sendInput();});document.addEventListener('visibilitychange',()=>{if(document.hidden){clearControls();sendInput();}});
$('map').addEventListener('pointerdown',()=>{$('map').focus();});
setInterval(sendInput,1000/30);

const canvas=$('map'),ctx=canvas.getContext('2d');
function draw(){
  const bounds=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2),w=bounds.width,h=bounds.height;
  if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#14262b';ctx.fillRect(0,0,w,h);
  const own=snapshot?.players.find(p=>p.id===session?.playerId),route=manifest?.route||[];
  const anchor=own?{x:own.x,z:own.z}:route.length?{x:route[Math.floor(route.length*.52)][0],z:route[Math.floor(route.length*.52)][2]}:{x:0,z:0};
  const scale=Math.min(w,h)/200,map=(x,z)=>[w/2+(x-anchor.x)*scale,h/2+(z-anchor.z)*scale];
  ctx.strokeStyle='#20363d';ctx.lineWidth=1;for(let x=Math.floor((anchor.x-w/2/scale)/20)*20;x<anchor.x+w/2/scale;x+=20){const p=map(x,0);ctx.beginPath();ctx.moveTo(p[0],0);ctx.lineTo(p[0],h);ctx.stroke();}for(let z=Math.floor((anchor.z-h/2/scale)/20)*20;z<anchor.z+h/2/scale;z+=20){const p=map(0,z);ctx.beginPath();ctx.moveTo(0,p[1]);ctx.lineTo(w,p[1]);ctx.stroke();}
  if(route.length){ctx.lineJoin='round';ctx.lineCap='round';const path=()=>{ctx.beginPath();route.forEach((p,i)=>{const[x,y]=map(p[0],p[2]);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});};path();ctx.lineWidth=Math.max(10,8*scale);ctx.strokeStyle='#4b6268';ctx.stroke();path();ctx.lineWidth=Math.max(6,6.6*scale);ctx.strokeStyle='#253a42';ctx.stroke();path();ctx.setLineDash([5,7]);ctx.lineWidth=1;ctx.strokeStyle='#8b9790';ctx.stroke();ctx.setLineDash([]);}
  for(const [i,p] of (snapshot?.players||[]).entries()){
    const[x,y]=map(p.x,p.z),color=COLORS[i%COLORS.length];ctx.save();ctx.globalAlpha=p.connected?1:.45;ctx.translate(x,y);ctx.rotate(p.heading);ctx.fillStyle=color;ctx.strokeStyle='#0d1c21';ctx.lineWidth=2;ctx.beginPath();ctx.roundRect(-7,-4,14,8,2);ctx.fill();ctx.stroke();ctx.fillStyle='#14262b';ctx.fillRect(1,-2.5,2.5,5);ctx.restore();
    ctx.strokeStyle=color;ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,11+i*4,0,Math.PI*2);ctx.stroke();ctx.font='600 11px system-ui';ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(`${p.name}${p.id===session?.playerId?' (you)':''}`,x,y-(22+i*15));
  }
  const age=latestAt?now()-latestAt:0;text('snapshot-age',latestAt?`${Math.round(age)} MS`:'— MS');let overlay='Create or join a room to drive';
  if(snapshot){overlay=!isConnected()?'Connection lost · server clock continues':age>500?'Snapshots delayed · authoritative markers frozen':snapshot.status==='waiting'?`Waiting · ${snapshot.players.filter(p=>p.ready).length} / 2 drivers ready`:snapshot.status==='countdown'?`START IN ${Math.max(0,(snapshot.startTick-snapshot.tick)/60).toFixed(1)}s`:snapshot.status==='results'?'Race complete · server result in lobby':own?.state==='finished'?'Finished · waiting for other driver':own?.dnf?'DNF · race continues':own?.inputStale?'Controls stale · server safe brake':'';}
  $('map-overlay').hidden=!overlay;text('map-overlay',overlay);requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
try{const response=await fetch('/manifest',{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);manifest=await response.json();if(!Array.isArray(manifest.route)||manifest.route.length<2)throw new Error('Missing route');setConnection('Ready locally');setBusy(false);session=loadSession();if(session){$('entry').hidden=true;$('room').hidden=false;text('room-code',session.roomCode);reconnectDeadline=now()+20000;connect({type:'reconnect',roomCode:session.roomCode,playerId:session.playerId,token:session.token});}}catch(error){setConnection('Load failed');notify(`Could not load the local track: ${error.message}.`);}
