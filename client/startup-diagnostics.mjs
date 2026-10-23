/** Bounded startup diagnostics: never expose raw exceptions, URLs, response bodies or session data. */
const stages=new Set(['renderer-create','renderer-load','asset-integrity','renderer-config','client-create','manifest','route','adapter','preview','session-restore','ready']);
const codes=new Set(['PROTOCOL_MISMATCH','PHYSICS_MISMATCH','TRACK_MISMATCH','ROUTE_MISMATCH','RACE_SLICE_MISMATCH','WORLD_ASSET_MISMATCH','RULES_MISMATCH','CONNECTION_FAILED','INVALID_ROUTE','ENDPOINT_NOT_APPROVED']);
const labels={'renderer-create':'graphics setup','renderer-load':'scene loading','asset-integrity':'asset verification','renderer-config':'online scene setup','client-create':'network setup',manifest:'server manifest',route:'route verification',adapter:'online scene setup',preview:'coast preview','session-restore':'session recovery',ready:'client setup'};
export function startupFailure(stage,error){
 const phase=stages.has(error?.startupStage)?error.startupStage:stages.has(stage)?stage:'ready';
 const code=codes.has(error?.message)?error.message:error?.name==='TimeoutError'||error?.name==='AbortError'?'TIMEOUT':error?.name==='SyntaxError'?'INVALID_JSON':/WebGL|graphics context/i.test(String(error?.message||''))?'WEBGL_UNAVAILABLE':error?.name==='TypeError'&&/fetch|network|load failed/i.test(String(error?.message||''))?'NETWORK_ERROR':'PREPARATION_ERROR';
 const failure={stage:phase,code};if(Number.isSafeInteger(error?.httpStatus)&&error.httpStatus>=100&&error.httpStatus<=599)failure.httpStatus=error.httpStatus;
 return Object.freeze(failure);
}
export function stageError(stage,error){
 const wrapped=new Error(error?.message||'PREPARATION_ERROR');wrapped.name=error?.name||'Error';wrapped.startupStage=stage;
 if(Number.isSafeInteger(error?.httpStatus))wrapped.httpStatus=error.httpStatus;
 return wrapped;
}
export function startupFailureText(failure){
 const code=failure.code+(failure.httpStatus?' / HTTP '+failure.httpStatus:'');
 return `${failure.code==='WEBGL_UNAVAILABLE'?'WebGL2 unavailable':'Client preparation failed'} at ${labels[failure.stage]} (${code}). No race has started. Reload to try again.`;
}
