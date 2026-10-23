import test from 'node:test';
import assert from 'node:assert/strict';
import {APPROVED_PRODUCTION_ORIGINS} from '../client/deployment.mjs';
import {validateEndpoint,endpointForPage} from '../client/endpoint.mjs';
import {RaceClient} from '../client/client.mjs';
import {Socket,fakeFetch,EXPECTED} from './fixture.mjs';
const origin='https://kerala-roadster-multiplayer-alpha.onrender.com';
test('activation approves exactly the verified HTTPS origin and ignores endpoint-query injection',()=>{
 assert.deepEqual(APPROVED_PRODUCTION_ORIGINS,[origin]);
 assert.equal(validateEndpoint({origin}).origin,origin);
 assert.equal(endpointForPage({origin,search:'?endpoint=https://attacker.example'}).origin,origin);
 for(const value of ['http://kerala-roadster-multiplayer-alpha.onrender.com',origin+'/',origin+':443',origin+':8443',origin+'/room',origin+'?endpoint=x',origin+'#x','https://user:pass@kerala-roadster-multiplayer-alpha.onrender.com','https://kerala-roadster-multiplayer-alpha.onrender.com.attacker.example','https://other.onrender.com','wss://kerala-roadster-multiplayer-alpha.onrender.com'])assert.throws(()=>validateEndpoint({origin:value}),/ENDPOINT_NOT_APPROVED/);
 assert.equal(endpointForPage({origin:'https://attacker.example',search:'?endpoint='+encodeURIComponent(origin)}),null);
});
test('actual production transport derives only exact approved same-origin WSS and preserves protocol pins',async t=>{
 const calls=[],c=new RaceClient({endpoint:{origin},WebSocket:Socket,fetch:async(url,options)=>{calls.push({url,options});return fakeFetch();}});t.after(()=>c.close());
 await c.prepare();c.setLoaded(true);c.create('Activation check');
 assert.equal(calls[0].url,origin+'/manifest');
 assert.equal(Socket.instances.at(-1).url,'wss://kerala-roadster-multiplayer-alpha.onrender.com/room');
 assert.equal(c.expected.protocolVersion,2);
 assert.equal(c.expected.physicsVersion,'v11.1-stock-noncontact-rebuild2-dc74ca61a9d4fc50');
 assert.equal(c.expected.trackHash,'1b3bdbf06de3bb91414b00f6e62b524c4141c34febbd5e0b2bc9adf9f844720d');
 assert.deepEqual(c.expected,EXPECTED);
});
