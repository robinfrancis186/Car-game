# V15 model contract — authored upright ramps and observational air traffic

This is an original arcade implementation, not the reference video's reward formula or a real aircraft/vehicle simulation. Loops, wall/ceiling adhesion and inverted track surfaces are **not implemented**.

## Wedge surface

`GameModel(route, {ramps})` accepts optional `ramps` (default `[]`):

```js
{id:'skyline-rise',startS:2675,lipS:2710,rise:2.6,
 centerOffset:0,halfWidth:3.6,minSpeed:12,
 enabledScenarios:null}
```

Distances are horizontal route arc length/metres. Surface height is unchanged route Y plus `rise*(s-startS)/(lipS-startS)`. `centerOffset` uses route normal `(-tz,tx)`. Null/omitted enabledScenarios enables all events; a supplied array restricts surface and boundary contacts. Routes, terrain and existing physics are unchanged when ramps are absent. Wedges are at least5m long, at most150m, rise0.5–8m, maximum added grade35%; invalid entries are discarded and IDs deduplicated.

Grounded support uses the actual wedge gradient; road grip remains active. The lip launches a forward-aligned vehicle only above minSpeed, using its forward velocity times the local grade, capped14m/s upward. The separate ballistic apex ceiling prevents an elevated launch being clipped by a stale manual-flight ceiling. Gravity and the pre-existing automatic landing assist then apply. Manual thrust/flip still works but disqualifies the reward. AI rivals/police use the same wedge and ballistic departure, with road-following horizontal motion; below-deck side merges are held outside the ramp until its lip is passed; they are arcade path followers, not independent rigid-body pilots.

Vertical sidewalls and the lip block a car entering below the wedge. An already supported car may depart without hitting its own ramp. These contacts use the existing capsule impulse/damage solver; do not add a full static convex hull or full-height lip box. Generated checkpoints and coin positions use wedge height without changing gate order/count, coin values or reward rules. Reverse uphill/downhill travel on the ramp is supported, but reverse entry into its vertical lip is not.

## Airtime/energy

`model.airtime = {active,seconds,rampId,eligible,reason,lastReward,energyAwarded}`.

- `ramp-launch`: `{rampId,verticalSpeed,alongSpeed}`.
- `airtime-reward`: `{episodeId,rampId,airtimeSeconds,distanceMetres,energyAward,actualEnergyAdded,reason:null}`.
- Clean minimum:0.65s airborne,12m displacement, road landing, lateral speed≤5m/s and vertical impact≤6m/s.
- Original formula: energyAward = min(0.12,0.04×airtimeSeconds, remaining0.30 run allowance). Energy is normalized0–1. `actualEnergyAdded` is clamped to the available battery headroom and is the only value UI/audio should call a delivered boost reward.
- Each ramp can pay once/run; successful full-energy landings consume that ramp's eligibility but report actualAdded0. Ten seconds between eligible awards. At most0.30 actual energy/run.
- Any manual flight/flip, solid contact/damage, discontinuous movement, recovery, episode>8s or450m invalidates that episode. Recovery preserves the used-ramp ledger and cannot grant a reward. Restart clears the run ledger. Pause freezes clocks. No coin/profile changes.
- Existing passive recharge and automatic landing assist remain separate from this explicit award.

## Helicopters

`GameModel(route, {airTraffic:true})` explicitly enables both actors; default false preserves the previous baseline. `model.helicopter` and `model.civilianHelicopter` expose:

```js
{active,visible,phase,x,y,z,heading,pitch,roll,
 velocityX,velocityZ,verticalVelocity,rotorRpm,flightSeconds,
 beamVisible,beamTarget:{x,y,z},spotlightIntensity}
```

Coordinates are metres with +Y up; heading0 points+X, positive toward+Z. Angles radians, velocities m/s, rotorRpm approximate visual/acoustic cadence only. Renderer/audio must consume these model states, not advance independent wall-clock flight schedules. At most one police and one civilian actor.

Police is observational: it cannot arrest, damage, grant coins/energy or alter ground-police behavior. It dispatches only after30s active pursuit and12s sustained heat≥0.76 while moving>8m/s, arrest progress<0.2 and nearest ground unit>12m away. Phases are idle→approach→track/search→withdraw, with finite approach/search/withdraw timers and30s redispatch cooldown. Searchlight requires range<190m, active wanted state, a conservative≤0.62rad downward gimbal angle and terrain/solid/deck line of sight. Tracking uses a20m-back/12m-side station with player-velocity feed-forward, subject to the aircraft speed limit. Roof/terrain clearance uses a9.2m full swept-airframe footprint margin and at least18m clearance; it slows/stops horizontally to climb before steep roof/terrain boundaries. Max horizontal speed55m/s, vertical climb9m/s/descent5m/s. Approx rotor420rpm.

Civilian pass starts12s into a race, anchors one fixed crossing at route s + clamp(abs(player speed)×8,100,600), plus150m tangent offset, travels460m at28m/s, and repeats sparsely90s after completing. Path altitude surveys terrain/roofs before spawning with42m clearance, approx rotor400rpm. It does not follow a moving anchor or affect pursuit. No civilian/police actor in Explore, menu or results. All state/clocks freeze on pause; result/restart resets actors. Recovery sends an active police actor to search and immediately hides its beam.

The model beam is a conservative prefilter, not the final optical ray. The renderer must also test the actual articulated world-space lens socket to the final beam target through `model._airLineOfSight(lensWorld, targetWorld)` before displaying the light; a root-origin approximation alone can miss a thin intervening roof.

Aircraft are deterministic kinematic visual/audio actors, not flight simulators or multiplayer entities. Conservative obstruction bounds can hide a beam early; they intentionally must not illuminate through an occupied roof.
