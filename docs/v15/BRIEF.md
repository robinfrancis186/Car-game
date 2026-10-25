# V15 first playable slice — air support and authored ramp airtime

Base: separate copy of frozen V14.1. The current public UI release and its source remain unchanged.

## Reference interpretation
The user's sixty-second video shows connected surfaces: banked city roads, ceiling sections, jump ramps, wall/ceiling tunnel, loop and half-pipe. These are not demonstrated random road swaps. The analysis worker reviewed the full clip and sampled landing frames at 0.1-second intervals; the lead inspected three transition contact sheets. The source video and frames stay in analysis-only storage outside the project and will not ship.

Explicit airtime and landing-associated boost refill are visible, but the video does not reveal an exact reward formula. Helicopters/police searchlights are a separate original user request, not an observed mechanic in the clip.

## Bounded first slice
1. Original Blender light-twin helicopter, separately animated main/tail rotors, navigation lights, searchlight gimbal/sockets, modest mobile draw budget. Civilian flyovers during races and one police air-support vehicle after sustained difficult ground pursuit.
2. Deterministic helicopter escalation/approach/track/search/withdraw, safe terrain/roof clearance, obstruction-aware spotlight target, distance-scaled original synthesis. Observational support only in this slice: no unavoidable instant arrest or hidden economy change.
3. Authored route-aligned ramps with actual graded support and ballistic lip departure, coherent AI behavior, visible approach/landing cues and safe runway. No camera-only imitation of a wall/loop; upright ramp/interchange geometry is the bounded first mechanic. Full inverted driving is not claimed implemented by this slice.
4. Actual airborne duration followed by a one-time bounded clean-landing boost refill. Manual flight/flip, recovery, contact/teleport, paused time and repeated same-ramp farming cannot manufacture reward. HUD reports actual boost added separately from duration.

## Guardrails
- Preserve existing seven-car ownership, balance, tuning and storage namespaces. No coins, paid currency, new accounts or multiplayer claims.
- Maintain existing driving behavior when no ramp metadata is enabled. Default routes and all old source contracts must pass regression.
- Separate roles: model worker owns gameplay/new model modules; asset worker owns only helicopter Blender/native/export artifacts; lead owns world/runtime/audio integration. No simultaneous file writers.
- Pause/menu/results/restart clear or freeze rotor/beam/audio/reward clocks correctly. Mobile quality mode lowers optional visual cost.
- Every native/GLB milestone gets geometry/rig tests and a Blender screenshot labeled as such. Source checkpoints are uploaded durably before publish handoff. WebGL/audio/native acceptance is distinct from model tests.
