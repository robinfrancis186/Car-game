import test from 'node:test';import assert from 'node:assert/strict';
import{startupFailure,stageError,startupFailureText}from'../client/startup-diagnostics.mjs';
test('startup diagnostics expose only fixed phase/code and a bounded HTTP status',()=>{
 const secret='private-session-token-and-user-data';
 for(const error of[new Error(secret),Object.assign(new Error(secret),{startupStage:secret,httpStatus:secret}),null]){
  const d=startupFailure('manifest',error);assert.deepEqual(d,{stage:'manifest',code:'PREPARATION_ERROR'});assert(!JSON.stringify(d).includes(secret));assert(!startupFailureText(d).includes(secret));
 }
 const known=Object.assign(new Error('CONNECTION_FAILED'),{httpStatus:503});assert.deepEqual(startupFailure('manifest',known),{stage:'manifest',code:'CONNECTION_FAILED',httpStatus:503});
 for(const httpStatus of[0,99,600,Infinity,200.5,'503'])assert.equal(startupFailure('manifest',Object.assign(new Error('CONNECTION_FAILED'),{httpStatus})).httpStatus,undefined);
 assert.deepEqual(startupFailure('ready',stageError('manifest',known)),{stage:'manifest',code:'CONNECTION_FAILED',httpStatus:503});
 assert.equal(startupFailure('manifest',Object.assign(new Error(secret),{name:'TimeoutError'})).code,'TIMEOUT');
 assert.equal(startupFailure('manifest',new SyntaxError(secret)).code,'INVALID_JSON');
 assert.equal(startupFailure('manifest',new TypeError('Failed to fetch '+secret)).code,'NETWORK_ERROR');
 assert.equal(startupFailure('renderer-create',new Error('Error creating WebGL context.')).code,'WEBGL_UNAVAILABLE');
 assert.equal(startupFailure('manifest',new Error('ROUTE_MISMATCH')).code,'ROUTE_MISMATCH');
 assert(Object.isFrozen(startupFailure('manifest',known)));
});
