# Architecture and protocol constraints

Public ingress/one-room restrictions supersede the original local-only hosting notes; see `HOSTING.md` and the root README. Core physics and race protocol remain the same.

## Authority

`server/service.mjs` owns every room, monotonic clock, 60 Hz ticks and finish list. The clock uses `performance.now()`; clients cannot provide elapsed simulation time. Catch-up is bounded to 250 ms; a larger stall ends active races unranked with `server-overload`, rather than accepting a silently wrong clock. Snapshot interval is every third tick.

`shared/world.mjs` owns one immutable authored world and one `GameModel`, with a map of complete mutable driver contexts. Each car is stepped sequentially with the unchanged V10 120 Hz integration. Context separation covers steering, velocities, locks, accumulators, recovery/collision cooldowns, events, checkpoints, penalties and result. Room elapsed time is common; recovery adds five seconds only to that racer's scored time. No player contact exists; **do not extend this adapter to car-contact racing without implementing joint interaction resolution**. Scenic traffic proxies are deliberately absent, not trusted from rendering.

Static options and stock upgrade stats cannot be supplied by clients. Both cars begin at the same authored spawn and can overlap. Water query uses authored triangles and original low-height / altitude / hinted route-distance gates at roughly 0.2 s cadence. The recovery path remains the last validated checkpoint, with no gate advancement or charge refill. The baseline Explore and terrain behavior remains unchanged in the copied core; online mode is race-only.

## Wire messages

WebSocket: `ws://127.0.0.1:PORT/room` locally only. Server emits `hello` with `{protocolVersion, physicsVersion, trackHash, tickRate, snapshotRate, rules}`. `/manifest` supplies the same plus route geometry.

- `create`: `type,name,protocolVersion,physicsVersion,trackHash`
- `join`: those same fields plus `roomCode`
- `reconnect`: `type,roomCode,playerId,token,protocolVersion,physicsVersion,trackHash`
- `ready`: `{type:'ready',loaded:true}`
- `start` / `rematch`: `{type:'start'}` / `{type:'rematch'}`; host permission required.
- `input`: `{type:'input',epoch,seq,clientTick,controls:{throttle,steer,brake,boost,recover}}`

All fields are exact: extra keys are rejected. Throttle/steer must be finite numbers within [-1,1], buttons booleans. Sequence is a positive safe integer <=2^31−1; only monotonically increasing values within 4096 of last accepted sequence are accepted. Epoch changes on rematch. Referenced server tick must be within [-120,+6] of current tick. Input ack is last accepted sequence, not client truth about elapsed frames. Latest input replaces previous; no unbounded input queue. After 15 ticks without accepted input, throttle/boost are zero and brake is true. Recover is rising-edge triggered, never a client-supplied destination.

`joined` privately returns `playerId`, `roomCode`, `reconnectToken`, `epoch`, `lastSeq`. Tokens rotate on successful reconnect and are not broadcast. `snapshot` carries room status/tick/startTick/elapsed/host, all visible car states and input ack/readiness/connectivity, plus shared results when terminal. `error` carries a code, no sensitive payload. No protocol supports currency, purchases, user profiles or direct state edits.

## Bounds and lifecycle

Two players per room. Public mode permits one room and six concurrent transport clients; local mode retains eight rooms and 32 clients. Maximum data message is 2048 bytes, 90 messages/connection/second, and outgoing buffer 128 KiB. Public mode additionally bounds global HTTP/upgrade/message/create rates, ping/pong control frames, connection lifetime and TCP sockets. Public Host and Origin must match the exact Render HTTPS origin; absent or null Origin is rejected. Local mode permits loopback Host/Origin and no-Origin CLI clients. Origin checks are browser safeguards, not authentication; a non-browser client can forge them. Heartbeat every 5 s; unauthenticated connections are retired after a bounded handshake window. Rooms expire after 15 min waiting or 60 s after results. Reconnect window is 20 s, clock continues; expired unfinished seats become DNF. Lobby host transfers to a connected seat; server authority never migrates to players.

These are local alpha safeguards, **not** complete internet authentication or DoS protection. Private random 96-bit invite codes grant access; no account identity is established. Browser reconnect uses sessionStorage, so anyone who can run same-origin scripts can impersonate that seat. Hosting changes require review.

## Tests and interpretation

Network test forks a genuine server process and independently connected Node clients. The test-only route follower submits controls via WebSocket; it never sends positions or directly changes server state. Both independently receive movement/start/results. Unit tests may place a car in hazardous fixtures directly, but those are not claimed as network driving. Test reconnect expiry is shortened; production-default 20 s timing is a configuration value, not a measured separate-network trial. No public browser/device session or GPU has been accepted.
