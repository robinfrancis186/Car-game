/** Local-only authority tests. Stalls are injected into this test process, never via a server endpoint. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {performance} from 'node:perf_hooks';
import WebSocket from 'ws';
import {createService} from '../server/service.mjs';
import {NEUTRAL} from '../shared/protocol.mjs';
import {TIMING_POLICY} from '../shared/timing-policy.mjs';
import {newInterruption, interruptionView, beginInterruption, updateInterruption} from '../server/interruption.mjs';

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const stall = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const driving = {...NEUTRAL, throttle: 1, brake: false};
const versionFields = manifest => Object.fromEntries(['protocolVersion', 'physicsVersion', 'trackHash'].map(key => [key, manifest[key]]));

async function fixture(t, options = {}) {
  const app = await createService({countdownTicks: 3, ...options});
  const peers = [];
  t.after(async () => {
    for (const p of peers) p.ws.terminate();
    await app.close();
  });
  async function peer() {
    const ws = new WebSocket(`ws://127.0.0.1:${app.port}/room`);
    const messages = [], arrival = new WeakMap();
    ws.on('message', bytes => {
      const message = JSON.parse(bytes);
      arrival.set(message, performance.now());
      messages.push(message);
    });
    await new Promise((resolve, reject) => {
      ws.once('open', resolve);
      ws.once('error', reject);
    });
    const p = {
      ws, messages, arrival, mark: () => messages.length,
      send: message => ws.send(JSON.stringify(message)),
      async wait(predicate, from = 0, timeoutMs = 3500) {
        const end = performance.now() + timeoutMs;
        while (performance.now() < end) {
          const message = messages.slice(from).find(predicate);
          if (message) return message;
          await sleep(5);
        }
        throw new Error('Missing interruption-test message: ' + JSON.stringify(messages.slice(-2), (key, value) => /token/i.test(key) ? '[REDACTED]' : value));
      },
    };
    peers.push(p);
    await p.wait(m => m.type === 'hello');
    return p;
  }
  const a = await peer(), b = await peer(), versions = versionFields(app.manifest);
  a.send({type: 'create', name: 'Timing A', ...versions});
  const aj = await a.wait(m => m.type === 'joined');
  b.send({type: 'join', name: 'Timing B', roomCode: aj.roomCode, ...versions});
  const bj = await b.wait(m => m.type === 'joined');
  const room = app.rooms.get(aj.roomCode);
  async function start(until = 'racing') {
    const mark = a.mark();
    a.send({type: 'ready', loaded: true});
    b.send({type: 'ready', loaded: true});
    await a.wait(m => m.type === 'snapshot' && m.players.length === 2 && m.players.every(p => p.ready), mark);
    a.send({type: 'start'});
    return a.wait(m => m.type === 'snapshot' && m.status === until, mark);
  }
  return {app, a, b, aj, bj, room, peer, versions, start};
}

function capture(room) {
  // Normalize exactly as the wire does (notably -0 -> 0), and detach event arrays.
  return JSON.parse(JSON.stringify({tick: room.tick, elapsed: room.world.ticks / 60, players: [...room.seats.keys()].map(id => room.world.snapshot(id))}));
}
function assertFrozen(message, before) {
  assert.equal(message.tick, before.tick, 'room tick is not advanced during a hold');
  assert.equal(message.elapsed, before.elapsed, 'race clock is not advanced during a hold');
  assert.deepEqual(message.players.map(player => Object.fromEntries(Object.keys(before.players.find(p => p.id === player.id)).map(key => [key, player[key]]))), before.players, 'all authoritative world fields remain committed, not caught up');
}
function assertMetadata(message) {
  const value = message.interruption;
  assert.deepEqual(Object.keys(value).sort(), ['generation', 'phase', 'count', 'totalMs', 'currentMs'].sort());
  assert(Number.isSafeInteger(value.generation) && value.generation >= 0);
  assert(Number.isSafeInteger(value.count) && value.count >= 0);
  assert(['active', 'holding'].includes(value.phase));
  assert(Number.isFinite(value.totalMs) && value.totalMs >= 0);
  assert(Number.isFinite(value.currentMs) && value.currentMs >= 0);
  if (value.phase === 'active') { assert.equal(value.currentMs, 0); assert.equal(value.generation, value.count * 2); }
  else assert.equal(value.generation, value.count * 2 - 1);
}
function input(room, seq, controls = NEUTRAL, generation = room.interruption.generation) {
  return {type: 'input', epoch: room.epoch, generation, seq, clientTick: room.tick, controls};
}
async function resultsMatch(a, b, fromA, fromB) {
  const ra = await a.wait(m => m.type === 'snapshot' && m.status === 'results', fromA);
  const rb = await b.wait(m => m.type === 'snapshot' && m.status === 'results', fromB);
  assert.deepEqual(ra.results, rb.results, 'both real WebSocket clients see identical server-authored results');
  return ra;
}
async function recoveredStall(f, ms, event) {
  const mark = f.a.mark();
  stall(ms);
  const holding = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', mark);
  assert.equal(holding.interruption.generation, event * 2 - 1);
  const resumed = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'active' && m.interruption.generation === event * 2, mark);
  assert.equal(resumed.status, 'racing');
  return resumed;
}

// Every assertion is against protocol 3 and live service state; no production stall controls are introduced.
test('protocol 3: two clients observe a genuine frozen world, stable recovery, neutral controls and generation fencing', {timeout: 7000}, async t => {
  const f = await fixture(t), {app, a, b, aj, room} = f;
  assert.equal(app.manifest.protocolVersion, 3);
  const waiting = await a.wait(m => m.type === 'snapshot' && m.players.length === 2);
  assert.deepEqual(waiting.interruption, {generation: 0, phase: 'active', count: 0, totalMs: 0, currentMs: 0});
  const initial = await f.start();
  a.send(input(room, 1, driving, 0));
  await a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === aj.playerId)?.ack === 1);
  const before = capture(room), am = a.mark(), bm = b.mark();
  stall(480);
  const unblockedAt = performance.now();
  const heldA = await a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', am);
  const heldB = await b.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', bm);
  assertFrozen(heldA, before); assertFrozen(heldB, before);
  assert.equal(heldA.interruption.generation, 1); assert.equal(heldA.interruption.count, 1);
  assert(heldA.interruption.currentMs >= 480, 'initial lost wall time is charged to the hold');
  assert.deepEqual(room.seats.get(aj.playerId).controls, NEUTRAL, 'pre-stall throttle is cleared immediately');
  let mark = a.mark(); a.send(input(room, 2, driving, 0));
  assert.equal((await a.wait(m => m.type === 'error', mark)).code, 'RESYNC_REQUIRED');
  const queuedDuringHold = input(room, 2, driving, 1);
  mark = a.mark(); a.send(queuedDuringHold);
  await sleep(50);
  assert.equal(room.seats.get(aj.playerId).lastSeq, 1, 'current-generation controls sent while held are discarded, not acknowledged');
  assert(!a.messages.slice(mark).some(m => m.type === 'error'), 'ordinary hold traffic does not spend invalid-message allowance');
  const laterMark = a.mark();
  const stillHeld = await a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding' && m.interruption.currentMs >= heldA.interruption.currentMs + 100, laterMark);
  assertFrozen(stillHeld, before);
  const resumed = await a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'active' && m.interruption.generation === 2, am);
  const resumedB = await b.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'active' && m.interruption.generation === 2, bm);
  assert.equal(resumedB.tick, resumed.tick); assert.equal(resumedB.elapsed, resumed.elapsed);
  assert.deepEqual(resumedB.interruption, resumed.interruption, 'both peers resume from one authoritative hold decision');
  assert(a.arrival.get(resumed) - unblockedAt >= 480, 'no early resume before the 500ms stable window');
  assert(resumed.elapsed - before.elapsed < .12, 'discarded backlog is never simulated after resume');
  assert(resumed.interruption.totalMs >= 960, 'aggregate includes lost gap plus actual stable hold');
  assert.equal(resumed.interruption.currentMs, 0);
  assert.deepEqual(room.seats.get(aj.playerId).controls, NEUTRAL, 'resume does not resurrect pre-hold or held inputs');
  mark = a.mark(); a.send(queuedDuringHold);
  assert.equal((await a.wait(m => m.type === 'error', mark)).code, 'RESYNC_REQUIRED', 'queued commands created during hold are fenced after resume');
  mark = a.mark(); a.send(input(room, 2, driving, 0));
  await sleep(30);
  assert.equal(room.seats.get(aj.playerId).lastSeq, 1, 'old-generation controls remain rejected after resume');
  assert(!a.messages.slice(mark).some(m => m.type === 'error'), 'resynchronization notice is bounded to once per generation');
  mark = a.mark(); a.send(input(room, 2, driving, 2));
  const accepted = await a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === aj.playerId)?.ack === 2, mark);
  assert(accepted.elapsed > before.elapsed, 'race clock resumes only through new fixed simulation steps');
  const progressedB = await b.wait(m => m.type === 'snapshot' && m.tick === accepted.tick, bm);
  assert.equal(progressedB.elapsed, accepted.elapsed, 'both peers observe the resumed authoritative clock');
  assert.equal(accepted.epoch, initial.epoch);
  let lastTotal = 0;
  for (const message of a.messages.filter(m => m.type === 'snapshot')) {
    assertMetadata(message);
    assert(message.interruption.totalMs >= lastTotal, 'reported interruption aggregate never decreases');
    lastTotal = message.interruption.totalMs;
  }
});

test('old and malformed clients cannot create a hold, omit generation, or spoof interruption state', {timeout: 4000}, async t => {
  const f = await fixture(t), {a, room, peer, versions} = f;
  const old = await peer();
  old.send({type: 'create', name: 'Protocol 2', ...versions, protocolVersion: 2});
  assert.equal((await old.wait(m => m.type === 'error')).code, 'PROTOCOL_MISMATCH');
  await f.start();
  const malformed = [
    {type: 'pause'}, {type: 'hold'}, {type: 'resume'}, {type: 'interruption', generation: 1, phase: 'holding'},
    {...input(room, 1), generation: undefined}, {...input(room, 1), generation: -1},
    {...input(room, 1), generation: .5}, {...input(room, 1), generation: '0'},
    {...input(room, 1), generation: Number.MAX_SAFE_INTEGER + 1},
    {...input(room, 1), interruption: {phase: 'active'}},
  ];
  for (const message of malformed) {
    const mark = a.mark(); a.send(message);
    const error = await a.wait(m => m.type === 'error', mark);
    assert.equal(error.code, message.type === 'input' ? 'INVALID_INPUT' : 'UNKNOWN_MESSAGE');
  }
  const mark = a.mark(); a.send(input(room, 1, NEUTRAL, 1));
  assert.equal((await a.wait(m => m.type === 'error', mark)).code, 'FUTURE_GENERATION');
  assert.equal(room.interruption.generation, 0);
  assert.equal(room.interruption.count, 0);
  assert.equal(room.interruption.phase, 'active');
  assert.equal((await fetch(`http://127.0.0.1:${f.app.port}/__test__/stall`)).status, 404);
});

test('countdown shares the same frozen tick and stable-wall recovery policy', {timeout: 4000}, async t => {
  const f = await fixture(t, {countdownTicks: 90});
  const countdown = await f.start('countdown'), before = capture(f.room), mark = f.a.mark();
  stall(310);
  const holding = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', mark);
  assert.equal(holding.status, 'countdown'); assert.equal(holding.startTick, countdown.startTick);
  assertFrozen(holding, before);
  const resumed = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'active' && m.interruption.generation === 2, mark);
  assert.equal(resumed.status, 'countdown'); assert.equal(resumed.elapsed, 0);
  assert.equal(resumed.startTick, countdown.startTick);
});

test('a real CPU-blocking gap during hold restarts the stable window without consuming another event', {timeout: 4000}, async t => {
  const f = await fixture(t); await f.start();
  const before = capture(f.room), mark = f.a.mark(); stall(300);
  await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', mark);
  await sleep(120);
  const cpuStarted = performance.now();
  // Deliberately consume CPU in this isolated test process; there is no remote trigger.
  let work = 0;
  while (performance.now() - cpuStarted < 310) work = Math.sqrt(work + 1);
  assert(work > 0);
  const cpuEnded = performance.now();
  const held = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding' && m.interruption.currentMs > 700, mark);
  assertFrozen(held, before);
  assert.equal(held.interruption.count, 1); assert.equal(held.interruption.generation, 1);
  const resumed = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'active' && m.interruption.generation === 2, mark);
  assert(f.a.arrival.get(resumed) - cpuEnded >= 480, 'recovery waits for stability after the latest gap, not the first one');
  assert.equal(resumed.interruption.count, 1);
  assert(resumed.interruption.totalMs >= 1200 && resumed.interruption.totalMs < 2000);
});

test('three recovered interruptions are allowed; the fourth gives both unfinished seats an honest matching DNF', {timeout: 6000}, async t => {
  const f = await fixture(t); await f.start();
  for (let generation = 1; generation <= 3; generation++) {
    const resumed = await recoveredStall(f, 300, generation);
    assert.equal(resumed.interruption.count, generation);
    assert(resumed.interruption.totalMs < 5000);
  }
  const am = f.a.mark(), bm = f.b.mark(); stall(300);
  const result = await resultsMatch(f.a, f.b, am, bm);
  assert(result.results.every(r => r.status === 'dnf' && r.reason === 'server-interrupted' && r.time === null && r.rank === null));
  assert.equal(result.interruption.count, 4);
  assert.equal(result.interruption.generation, 8);
});

test('exact interruption budgets and repeated gaps are deterministic, version-pinned server policy', () => {
  assert.deepEqual(TIMING_POLICY, {serverInterruption: 'bounded-v1', stallDetectMs: 250, resyncStableMs: 500, maxInterruptionMs: 2000, maxInterruptions: 3, maxInterruptedMs: 5000});
  const repeated = newInterruption();
  assert.equal(beginInterruption(repeated, 300, 300), 'holding');
  assert.equal(updateInterruption(repeated, 799), 'holding');
  assert.equal(beginInterruption(repeated, 1000, 301), 'holding');
  assert.equal(repeated.generation, 1); assert.equal(repeated.count, 1);
  assert.equal(updateInterruption(repeated, 1499), 'holding', 'another server gap resets the stable recovery window');
  assert.equal(updateInterruption(repeated, 1500), 'resumed');
  assert.deepEqual(interruptionView(repeated), {generation: 2, phase: 'active', count: 1, totalMs: 1500, currentMs: 0});

  const individual = newInterruption();
  assert.equal(beginInterruption(individual, 1500, 1500), 'holding');
  assert.equal(updateInterruption(individual, 1999.9), 'holding');
  assert.equal(updateInterruption(individual, 2000), 'resumed', 'exact 2s cap is allowed');
  const exceeded = newInterruption();
  assert.equal(beginInterruption(exceeded, 2000.1, 2000.1), 'failed');
  assert.equal(exceeded.totalMs, 2000.1); assert.equal(exceeded.currentMs, 0);

  const aggregate = newInterruption();
  for (const now of [1300, 3100]) {
    assert.equal(beginInterruption(aggregate, now, 1300), 'holding');
    assert.equal(updateInterruption(aggregate, now + 500), 'resumed');
  }
  assert.equal(aggregate.totalMs, 3600);
  assert.equal(beginInterruption(aggregate, 4900, 1300), 'holding');
  assert.equal(updateInterruption(aggregate, 5000), 'holding', 'exact aggregate cap is allowed, but stable window is still required');
  assert.equal(updateInterruption(aggregate, 5000.1), 'failed');
  assert.equal(aggregate.count, 3); assert.equal(aggregate.totalMs, 5000.1);
  assert.equal(aggregate.phase, 'active'); assert.equal(aggregate.currentMs, 0);
});

// This is a real stock-physics finish through WebSocket input, not an injected finished state.
test('the 2s interruption budget preserves an already completed driver while the unfinished driver receives server-interrupted DNF', {timeout: 9000}, async t => {
  const f = await fixture(t, {raceSlice: {startS: 2200, endS: 2220}}); await f.start();
  let seq = 0;
  const timer = setInterval(() => {
    if (f.room.status === 'racing') f.a.send(input(f.room, ++seq, driving));
  }, 40);
  t.after(() => clearInterval(timer));
  const finished = await f.a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === f.aj.playerId)?.state === 'finished', 0, 5500);
  clearInterval(timer);
  const completed = finished.players.find(p => p.id === f.aj.playerId);
  assert.equal(finished.status, 'racing');
  assert.equal(finished.players.find(p => p.id === f.bj.playerId).state, 'racing');
  const am = f.a.mark(), bm = f.b.mark(); stall(1750);
  const held = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', am);
  assert.equal(held.status, 'racing');
  assert(held.interruption.currentMs >= 1750 && held.interruption.currentMs < 2000);
  // The lost gap itself fits, but there is not enough budget for 500ms stable recovery.
  const result = await resultsMatch(f.a, f.b, am, bm);
  assert.equal(result.elapsed, held.elapsed, 'budget failure during hold does not advance the world');
  const winner = result.results.find(r => r.playerId === f.aj.playerId), dnf = result.results.find(r => r.playerId === f.bj.playerId);
  assert.equal(winner.status, 'finished'); assert.equal(winner.reason, null);
  assert.equal(winner.time, completed.result.time); assert.equal(winner.rank, 1);
  assert.equal(dnf.status, 'dnf'); assert.equal(dnf.reason, 'server-interrupted'); assert.equal(dnf.time, null);
  assert(result.interruption.totalMs >= 2000 && result.interruption.totalMs < 2200, 'lost gap plus hold is charged, and cap failure is prompt');
  const rematchMark = f.a.mark(); f.a.send({type: 'rematch'});
  const reset = await f.a.wait(m => m.type === 'snapshot' && m.status === 'waiting', rematchMark);
  assert.notEqual(reset.epoch, result.epoch);
  assert.deepEqual(reset.interruption, {generation: 0, phase: 'active', count: 0, totalMs: 0, currentMs: 0});
});

test('disconnect and token-rotating rejoin during a hold preserve its frozen world and generation', {timeout: 4000}, async t => {
  const f = await fixture(t); await f.start();
  const mark = f.a.mark(); f.b.ws.terminate();
  await f.a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === f.bj.playerId)?.connected === false, mark);
  const before = capture(f.room), heldMark = f.a.mark(); stall(320);
  await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', heldMark);
  const rejoined = await f.peer();
  rejoined.send({type: 'reconnect', roomCode: f.aj.roomCode, playerId: f.bj.playerId, token: f.bj.reconnectToken, ...f.versions});
  const joined = await rejoined.wait(m => m.type === 'joined');
  assert.equal(joined.reconnected, true); assert.notEqual(joined.reconnectToken, f.bj.reconnectToken);
  const snapshot = await rejoined.wait(m => m.type === 'snapshot');
  assert.equal(snapshot.interruption.phase, 'holding'); assert.equal(snapshot.interruption.generation, 1);
  assertFrozen(snapshot, before);
});

test('reconnect expiry remains wall-clock based even while simulation is held', {timeout: 4000}, async t => {
  // Same timer path with a short fixture window keeps the test bounded; production default remains 20s.
  const f = await fixture(t, {reconnectMs: 250}); await f.start();
  const mark = f.a.mark(); f.b.ws.terminate();
  await f.a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === f.bj.playerId)?.connected === false, mark);
  const heldMark = f.a.mark(); stall(350);
  const held = await f.a.wait(m => m.type === 'snapshot' && m.interruption?.phase === 'holding', heldMark);
  const outsider = await f.peer();
  outsider.send({type: 'reconnect', roomCode: f.aj.roomCode, playerId: f.bj.playerId, token: f.bj.reconnectToken, ...f.versions});
  assert.equal((await outsider.wait(m => m.type === 'error')).code, 'RECONNECT_DENIED');
  const expired = await f.a.wait(m => m.type === 'snapshot' && m.players.find(p => p.id === f.bj.playerId)?.dnf === 'disconnect-timeout', heldMark);
  assert.equal(expired.interruption.phase, 'holding', 'disconnect expiry housekeeping is not suspended with physics');
  assert.equal(expired.elapsed, held.elapsed);
});
