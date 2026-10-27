import {PURSUIT_REGROUP} from './gameplay.js';
/** Read-only race guidance. No timers, controls, rewards or world state are changed. */
export function raceFeedback(model,{auto=false,blocked=false,trafficAhead=false,touch=false}={}){
 if(model.state==='countdown')return auto?'AUTO DRIVE · CHOOSE A LINE · BRAKE / BOOST':touch?'HOLD GO · TAP LEFT / RIGHT · BRAKE TO SLOW':'W / ↑ GO · A / D STEER · SPACE BRAKE · T AUTO';
 if(model.state!=='racing')return '';
 if(auto&&model.scenario.id==='hot-pursuit'&&model.wanted&&model.routeLength-model.player.s<45)return 'ROAD ENDS · SWITCH TO MANUAL TO TURN BACK';
 if(model.wanted&&Number.isFinite(model.pursuitRecoveryS))return `RECOVERY · DRIVE ${Math.max(0,Math.ceil(130-Math.abs(model.player.s-model.pursuitRecoveryS)))} M BEFORE ESCAPING`;
 if(model.scenario.id==='hot-pursuit'&&model.escaped&&!model.wanted&&model._allGatesPassed&&model.player.s<model.endS-11)return 'PATROL LOST · RETURN TO THE SAFEHOUSE';
 if(auto&&trafficAhead&&!blocked)return 'TRAFFIC AHEAD · CHOOSE A CLEAR LINE / BRAKE';
 if(auto&&blocked)return 'AUTO BRAKING · CHOOSE A CLEAR LINE OR SWITCH TO MANUAL';
 if(model.scenario.id==='hot-pursuit'&&model._allGatesPassed&&model.wanted)return 'SAFEHOUSE LOCKED · BREAK CONTACT FOR 8 SECONDS';
 if(model.wanted&&model.scenario.id==='hot-pursuit'&&model.timer>=PURSUIT_REGROUP.start&&model.timer<PURSUIT_REGROUP.end)return 'PATROL REGROUPING · BOOST ON A CLEAR STRAIGHT';
 if(model.wanted&&model.pursuit==='evading')return `BREAKING CONTACT · ${Math.max(0,8-model.escapeTimer).toFixed(1)} S TO ESCAPE`;
 if(model.wanted&&model.police.some(c=>c.active&&c.mode==='pressure'))return 'INTERCEPTOR CLOSING · CHANGE LINE / USE BOOST';
 return '';
}
export function pursuitLabel(model){
 if(model.arrestProgress>.05)return `BOXED IN  ${Math.round(model.arrestProgress*100)}%`;
 if(model.wanted&&model.pursuit==='evading')return `EVADING  ${Math.max(0,8-model.escapeTimer).toFixed(1)} S`;
 if(model.wanted&&model.scenario.id==='hot-pursuit'&&model.timer>=PURSUIT_REGROUP.start&&model.timer<PURSUIT_REGROUP.end)return `REGROUP  ${Math.ceil(PURSUIT_REGROUP.end-model.timer)} S`;
 if(model.wanted)return `${model.helicopter?.active?'AIR SUPPORT':'PURSUIT'}  ${'▰'.repeat(model.wanted)}`;
 return model.escaped?'ESCAPED':model.scenario.id==='free-drive'?'EXPLORE / NO PURSUIT':'PATROL WATCH';
}

/** Regular boost rearm is deliberately explicit; Ultra retains its own gauge/status. */
export function regularBoostFeedback(model,input={}){
 if(model.state!=='racing'||model.paused||model.player.ultraBoosting)return '';
 if(model._boostLocked)return 'RELEASE BOOST TO REARM';
 if(input.boost&&model.player.energy<.2)return 'BOOST LOW · RELEASE TO RECHARGE';
 if(!input.boost&&model.player.energy<.7)return `BOOST RECHARGING ${Math.round(model.player.energy*100)}%`;
 return '';
}
