# Harbour Wall Run: bounded V16 solo surface proof

Canonical geometry: `surface_profile.json`, SHA256 `ab19f552d0dca7bec8aa93b8c03773d9fa42fd4f81dbbc0176e98d5a563e6698`.

- Length: 900 m; base Y: 8 m; half-width: 6 m.
- Flat 0–160 m, quintic bank 160–360 m, 90° wall 360–540 m, quintic return 540–740 m, flat 740–900 m.
- Positive road-right rises. Mesh spacing is advisory; exported geometry error is measured separately.
- No ceiling, tube, loop or inverted driving is claimed.

## Shared geometry and queries

`normalizeRibbonProfile(raw)` validates and deep-freezes the analytic profile.
`sampleRibbon(profile,s,l)` returns position, ds/dl/dss/dsl, true orthonormal forward/up/right, metric, beta/betaPrime/betaSecond and insideRange. Sampling beyond either finite endpoint clamps the returned surface point and marks insideRange false; no extended driving floor exists.

```js
S(s,l) = [s, 8+l*sin(beta), l*cos(beta)]
ds = [1, l*cos(beta)*betaPrime, -l*sin(beta)*betaPrime]
dl = [0, sin(beta), cos(beta)]
up = normalize(dl × ds)
```

Unlike animated body roll, the normal includes its longitudinal X component away from the centreline. `projectRibbon(profile,[x,y,z])` iteratively projects to the analytic contact frame and reports signedDistance. Physics uses this shared surface. Artist mesh QA establishes the discrepancy from its triangulated approximation.

## SurfaceDrive

```js
new SurfaceDrive(profile, {vehicleId, upgrades, maxSteer, startS:30, obstacles:[]})
```

Public methods: `update(elapsed,input)`, `reset({s,l,yaw,speed})`, `recover(reason)`, `setPaused(bool)`, `consumeEvents()`.

- Fixed 120 Hz accumulator; throttle, steering and brake are the only accepted controls.
- World tangent momentum, eased local steering, gravity projected into the actual forward/lateral frame, bounded lateral grip, drag and existing car-specific motor/grip/brake modifiers are used. Top speed is bounded at 80 m/s for this proof.
- Explicit arcade adhesion is required: nominal wall traction assist 12 m/s², maximum 30 m/s². This is a game rule, not a claim about real cars adhering to walls.
- At bank >60°, maintain at least 8 m/s (about 29 km/h). Remaining slower for 0.7 s releases contact. Exceeding adhesion capacity or driving a conservative tire footprint past a finite edge also releases it. Half-track is 1.15 m and half-wheelbase 1.4 m, projected with steering yaw. The same whole-footprint admission applies to recontact.
- Release retains world tangent velocity, then applies world gravity. There is no airborne steering or thrust. Frame leveling toward world-up is allowed only when the conservative body envelope clears the finite contact plane; otherwise it retains its released orientation, without adhesion or position attachment. An unsupported body-plane crossing causes a truthful `body-clearance` safe return. A partial-footprint edge release that would penetrate the still-underlapping road similarly uses `edge-clearance` return, not a pretend rigid-body rollover.
- Recontact requires an in-bounds front-side crossing, approach speed and adequate wall speed. Normal impact velocity is removed; a hard landing can add bounded damage. No energy, coins or race result is awarded.
- Lost contact, reaching ground or a bounded 5 s airborne interval triggers a visible safe return to a previously visited **exactly flat** area. End return faces inward; start return faces forward. Advance endpoint warnings appear within 70 m while moving outward. Manual R returns to flat supported road and clears transient motion/damage.
- Paused update changes nothing; paused recovery returns false. Recovery preserves elapsed time, increments its count and retains the fixed-step remainder. Reset starts a new transient solo session. No storage is read or written.

### Static structure safety, not full scenery dynamics

The optional `obstacles` array accepts finite, positive `shape:'box'` proxies: `{id,x,z,y,height,halfLength,halfWidth,heading}`. Heading is radians around world Y, local X points `(cos(heading),0,sin(heading))`. Boxes are copied and frozen. Other shapes and dynamic obstacles are not supported in this bounded proof.

Only the **AIR phase** sweeps a conservative body envelope against these static OBBs, testing the full motion segment to avoid tunneling. The envelope is X ±3 m, Z ±1.35 m, Y −0.03…1.85 m in car-local coordinates; exact preserved vertices of all seven cars fit inside it. An impact emits `surface-obstacle` with `obstacleId`, `impactSpeed` (m/s) and `safetyReturn:true`, then one recovery with reason `structure-contact`. It does not invent a rigid-body rebound, crash damage or reward. Supported ribbon travel is not blocked by behind-the-deck piers.

The outer guidance rails are **non-solid visual guides**. Actual edge safety is tire-footprint release plus world-gravity fall/clearance return. No rail collision claim is made.

## Player/render/audio contract

Player includes existing renderer/audio fields plus:

```js
surfaceFrame: {forward:[x,y,z], up:[x,y,z], right:[x,y,z]},
supportPoint:[x,y,z], groundPoint:[x,y,z], supportNormal:[x,y,z],
surfaceS, surfaceL, attached, airborne, bankAngle,
adhesionAcceleration, adhesionLimit:30, wallMinimumSpeed:8,
velocityX, velocityY, velocityZ
```

`surfaceFrame` includes steering yaw and is authoritative in both attached and airborne phases. Car root is the wheel-contact point. `supportPoint` and supportNormal are for attached shadows; scalar groundY cannot represent a wall. `player.vz` retains the legacy vertical-velocity alias, while velocityZ is world-Z velocity. Ballistic release sets `airborne=true`, `flying=false`: no manual-thruster label. Energy stays 1, ultraCharge stays 0 and all boost/flip activation states stay false.

## Optional façade / ordinary game isolation

`new StuntGameModel(route,{...normalOptions,surfaceProfile:world.surface_profile})` creates a menu model. Profile-first construction is also supported. `start('free-drive')` is the only allowed event; other IDs throw. Main explicitly selects this class for the surface-test track and hides unsupported control/reward UI.

Public `surfaceBank` mirrors player bank angle. `ribbonProfile`, `surfaceSample(s,l)` and `surfaceProject(point)` expose shared analytic queries. `sampleTerrain()` returns world ground Y=0 for camera safety. Normal route sampling remains the straight centreline for radar/progress; use surfaceProject for 3D contact/camera queries. Endpoint warning uses `recoveryWarning={reason:'route-end',endpoint:'start'|'end',warningOnly:true}`.

The façade never invokes normal race update: rivals, police, coins, helicopters, checkpoints and results stay empty/inactive. Dynamic obstacles are ignored. The ordinary GameModel, garage, economy and persistence files are unchanged. Existing saved car/upgrades are read-only modifiers; the proof cannot bank currency or story completion.

## Reproducible checks

- `node web/tests/surface-model.test.mjs`: analytic derivatives/frames, 120 Hz invariance, seven-car traversal/steering/braking/reverse, low-speed release, full-footprint recontact, endpoint return, pause/reset, no-reward façade and swept static safety tests.
- `node web/tests/surface-world.test.mjs`: exact runtime/canonical profile match, all seven shipped GLB envelopes and released wall vertices, 42 actual-profile forward/reverse traversals, all 68 exported structure proxies and no repeated reset/reward.
- Reports: `web/tests/surface_model_metrics.json`, `web/tests/surface_world_metrics.json`.

These are deterministic model and asset-geometry checks, not GPU/browser driving acceptance or engineering validation.
