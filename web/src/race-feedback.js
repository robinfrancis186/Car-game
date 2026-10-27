/** Read-only race guidance. No timers, controls, rewards or world state are changed. */
export function raceFeedback(model,{auto=false,blocked=false,touch=false}={}){
 if(model.state==='countdown')return auto?'AUTO DRIVE · CHOOSE A LINE · BRAKE / BOOST':touch?'HOLD GO · TAP LEFT / RIGHT · BRAKE TO SLOW':'W / ↑ GO · A / D STEER · SPACE BRAKE · T AUTO';
 if(model.state!=='racing')return '';
 if(auto&&blocked)return 'AUTO BRAKING · CHOOSE A CLEAR LINE OR SWITCH TO MANUAL';
 if(model.scenario.id==='hot-pursuit'&&model._allGatesPassed&&model.wanted)return 'SAFEHOUSE LOCKED · BREAK CONTACT FOR 8 SECONDS';
 if(model.wanted&&model.pursuit==='evading')return `BREAKING CONTACT · ${Math.max(0,8-model.escapeTimer).toFixed(1)} S TO ESCAPE`;
 if(model.wanted&&model.police.some(c=>c.active&&c.mode==='pressure'))return 'INTERCEPTOR CLOSING · CHANGE LINE / USE BOOST';
 return '';
}
export function pursuitLabel(model){
 if(model.arrestProgress>.05)return `BOXED IN  ${Math.round(model.arrestProgress*100)}%`;
 if(model.wanted&&model.pursuit==='evading')return `EVADING  ${Math.max(0,8-model.escapeTimer).toFixed(1)} S`;
 if(model.wanted)return `${model.helicopter?.active?'AIR SUPPORT':'PURSUIT'}  ${'▰'.repeat(model.wanted)}`;
 return model.escaped?'ESCAPED':model.scenario.id==='free-drive'?'EXPLORE / NO PURSUIT':'PATROL WATCH';
}
