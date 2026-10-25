/** Original arcade helicopter audio targets, not measured H135/manufacturer acoustics.
 * Coordinates and velocity components are metres / metres per second; +Y is up.
 * The four-blade, ~400 RPM pulse is an authored visual/sound convention only.
 */
const finite=(n,fallback=0)=>Number.isFinite(n)?n:fallback;
const clamp=(n,lo,hi)=>Math.max(lo,Math.min(hi,finite(n)));
const PROFILES=Object.freeze({
 police:Object.freeze({rpm:400,gain:.95,turbine:1120}),
 civilian:Object.freeze({rpm:404,gain:.78,turbine:1210})
});
const positionValid=p=>p&&['x','y','z'].every(k=>Number.isFinite(p[k]));
/** Pure and history-free: restarts/teleports cannot create a distance-derivative spike. */
export function rotorActorTarget(actor,listener,{kind='police',audible=true}={}){
 kind=typeof kind==='string'&&Object.hasOwn(PROFILES,kind)?kind:'police';const profile=PROFILES[kind];
 const valid=positionValid(actor)&&positionValid(listener),dx=valid?actor.x-listener.x:0,dy=valid?actor.y-listener.y:0,dz=valid?actor.z-listener.z:0;
 const rawDistance=valid?Math.hypot(dx,dy,dz):0,finiteDistance=Number.isFinite(rawDistance),distance=finiteDistance?rawDistance:0,heading=finite(listener?.heading);
 const active=!!(audible&&valid&&finiteDistance&&actor.active===true&&actor.visible!==false&&!['idle','inactive','hidden'].includes(actor.phase));
 const vx=finite(listener?.velocityX)-finite(actor?.velocityX),vy=finite(listener?.velocityY,finite(listener?.vz))-finite(actor?.verticalVelocity,finite(actor?.velocityY)),vz=finite(listener?.velocityZ)-finite(actor?.velocityZ);
 const closingSpeed=distance>1?clamp((vx*dx+vy*dy+vz*dz)/distance,-45,45):0;
 const doppler=clamp(343/(343-closingSpeed),.92,1.08);
 // Inverse-square-style rolloff plus smooth disappearance before the 900m cap.
 const tail=clamp((900-distance)/350,0,1),fade=tail*tail*(3-2*tail);
 const attenuation=active&&distance<900?fade/(1+(distance/95)**2):0;
 const rpm=clamp(finite(actor?.rotorRpm,profile.rpm),300,480);
 const speed=clamp(Math.hypot(finite(actor?.velocityX),finite(actor?.verticalVelocity,finite(actor?.velocityY)),finite(actor?.velocityZ))/60,0,1);
 return {kind,active:active&&attenuation>0,distance,gain:attenuation*profile.gain,
   pan:distance>1?clamp((-dx*Math.sin(heading)+dz*Math.cos(heading))/distance,-.85,.85):0,
   closingSpeed,doppler,bladePassHz:rpm*4/60*doppler,turbineHz:profile.turbine*doppler,
   rotorGain:.033+.006*speed,turbineGain:.006,washGain:.115+.02*speed,modulationDepth:(.115+.02*speed)*.65,
   washCutoffHz:clamp(1850-distance*1.4,350,1850)};
}
/** Two fixed slots only. Model pause and caller pause both suppress audio. */
export function rotorAudioTargets(model={},options={}){
 model=model&&typeof model==='object'?model:{};options=options&&typeof options==='object'?options:{};
 const audible=options.enabled!==false&&options.contextRunning!==false&&!options.menu&&!options.paused&&!model.paused&&model.state==='racing';
 return [rotorActorTarget(model.helicopter,model.player,{kind:'police',audible}),rotorActorTarget(model.civilianHelicopter,model.player,{kind:'civilian',audible})];
}
