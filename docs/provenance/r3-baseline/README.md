# MALABAR — V17 R3 reference UI candidate (unpublished)

R3 revises the compact Home hierarchy and original coastal-showroom lighting after the user rejected the older V16.1 iPhone UI. It is functional DOM/CSS and original Three.js geometry, not an uploaded screenshot overlay. **Not visually accepted or published.** Current evidence and exact remaining gates are in [`design-qa.md`](design-qa.md). Live V16.1 and earlier candidates remain untouched.

The supported cloud browser can render CSS, but its WebGL is disabled. Prior R1 hosted CSS screenshots do not verify the new R3 files; any original offline Blender proof is separately labeled and cannot establish WebGL behavior or native FPS.

## Preserved V16.1 baseline


This candidate preserves the live V16 game and adds session-only render-resolution comparison, actual drawing-buffer/MSAA/shadow diagnostics, a five-second active frame-time window, late opaque sky drawing and clearer surface-mode HUD backing. Default Auto resolution is unchanged. All 138 protected V16 runtime files—including contact physics, assets, rewards and saves—remain exact. See `docs/v16_1/BROWSER_ACCEPTANCE_PLAN.md`. No native FPS improvement is claimed before the controlled browser check.

## Existing V16 surface proof

The V16 baseline was published as Sites 33. It added one original 900 m surface-contact course: a level approach, a smooth bank to a 90-degree wall, a wall hold and a smooth return to level. The car and camera follow the actual local contact frame; this is not a car-roll animation on a flat road. This remains an arcade, solo proof, **not** ceiling, tube or full-loop driving.

## Find and drive the proof

From Home open **Help → Solo surface test → Open solo wall test**, or use `?track=surface-test`. Choose an already-owned car and select Play → Start solo test. Accelerate before the bank; the wall requires about 29 km/h. Steering remains local to the surface. Brake, reverse, camera selection and pause work normally. R returns to a safe flat approach without a race penalty. The endpoint warning marks the finite end of the ribbon; turn back or recover rather than treating it as a loop. Normal course buttons return to Kerala races.

Only this optional mode uses the separate 120 Hz contact model, bounded adhesion and world-gravity departure/recontact. Falling into authored support piers or signs causes a safety return, not a simulated crash response. Outer rails are non-solid visual guidance: the actual drive-surface edge releases contact. Body-level rigid suspension approximates tire contact on the twisting surface; this is not a full suspension or rigid-body vehicle solver.

The proof has **no opponents, pursuit, coins, boost refill, thruster flight, kickflip or Story awards**. Existing seven-car ownership, tuning, balance and storage remain intact. In V16.1, all V16 physics/economy/save/audio modules, assets and camera helpers are byte-protected by `web/tests/v16-1-scope.test.mjs` (138 files). The normal route catalogue remains Coast and Highlands; the test route is an explicit opt-in URL.

## Existing V15 aircraft and ramp access

- Hot Coast → Explore → Skyline Flyover: drive about 145 m to the marked kicker at route 2.675 km.
- Highland Run → Explore → Divided Highway: drive about 300 m to its marked kicker at 0.330 km.
- Civilian flyovers occur during races, not Explore. Police air support requires sustained active high-heat pursuit and failed ground capture; its spotlight cannot itself arrest or damage you.
- Clean natural ramp landings can refill some regular boost once per authored ramp/run. The HUD reports actual delivered energy; manual flight, collisions and recovery do not earn it.

Source, actual-GLB geometry and scene-graph checks do not establish native GPU performance, readable motion or audio listening. V16 human driving and native browser acceptance are separate pending gates. V15 native testing saw a small moving helicopter, working reverse and reset/pause telemetry, but did not reach its ramp or high-heat police-helicopter conditions. No full feature acceptance is claimed from that partial test.

## Run and test

```sh
cd web
npm ci --ignore-scripts
npm test
npm run serve
# Open http://localhost:8080 in a WebGL2 browser.
npm run build
```

The generated `dist/malabar-hot-coast.html` embeds code, original game assets and required notices for desktop/offline use. Standard HTTP hosting is preferable on mobile. `web/` contains the split hosting layout. No real-money purchases, ads, accounts or analytics are included. Device-local progression is not authoritative multiplayer ownership.

The default local server binds to localhost. Node 20+ is required to rebuild/test; Blender 4.3+ is used for editable source assets but is not needed to play. Browser rendering, human handling, audio listening and mobile touch acceptance are distinct from source/scene-graph tests and must be reported separately.

## Sources and licensing notices

See `LICENSES.md` and the asset manifests. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. Approved forward-looking notice corrections do not erase prior public versions or assert that any earlier dedication was legally reversed. OSM-derived coastal data retain their ODbL attribution and availability; the Highland track is an original fictional route.

Private uploaded reference images are not game textures and must not be included in release archives. Recovery snapshots, old audit copies, caches and hosting credentials/metadata are also excluded from public source packaging.
