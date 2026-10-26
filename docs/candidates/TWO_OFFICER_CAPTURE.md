# Two-officer capture — unpublished review candidate

Base: R3.5, `9dab7aaae7e284eb00d041ea4ccf246055b558c5`.
Branch: `feature/two-officer-capture`. This candidate has not been pushed or deployed.
On 26 October 2026, remote `main` matched that base. The live site's `release.json`,
`index.html` and `src/main.js` also matched the base's bytes. The supplied R3.5
runtime source identity is retained in the existing release receipts.

## Behavior

The existing boxed-in police rule starts an eight-second capture instead of
immediately showing the result. Driving, other race cars, recovery and the race
clock stop. Exactly two original officer figures emerge from one nearby patrol,
walk around the two stopped cars, approach the driver, and perform a non-graphic
hands-behind-back/wrist-securing interaction. A wide establishing shot cuts to a
closer static interaction shot; there is no moving cinematic camera. The existing
**Caught** result then settles once, with zero banked coins and no eligible
leaderboard entry. There is no attack, weapon, injury or graphic content.

The ordinary driving model is byte-identical. A small subclass defers only the
existing busted settlement; normal races still use the original physics and
terminal/reward logic. New starts and Home replace/reset the capture state.
Repeated terminal triggers cannot create extra actors or duplicate results.
Pause remains touch-accessible while driving controls and instruments are hidden.
Blur/visibility handlers pause the sequence; graphics loss stops the run and
requires reload using the existing interruption flow. The Home showroom, setup
drawer and sole Play action are retained. Save formats and leaderboard rules are
unchanged.

## Visual direction and asset rights

This is a bounded scene/behavior candidate, **not photorealistic asset delivery**.
All existing native Blender files and exported car/world assets are preserved.
New figures, simple joints, caps, fictional uniforms, door overlays and cuffs are
original procedural project geometry. No third-party human/motion asset was
downloaded, no account was created, and no purchase was made. See `LICENSES.md`.

| Area | This pass | Further work for realism |
| --- | --- | --- |
| Cars | Clearcoat over existing authored paint; existing lights/reflections retained. | Higher-fidelity body/interior/door geometry, calibrated material references and model-specific character exits. |
| Roads | Existing original asphalt normal/roughness maps, metre-space detail and road geometry retained. | Surface variation, convincing markings/edge wear and scene-specific wetness where justified. |
| Buildings | Restrained, filtered procedural variation on plaster/concrete rough surfaces. | Less repetitive architecture, believable glazing/interiors and physically scaled facade detail. |
| Vegetation | Existing palms, leaf wind and detail/instance budgets retained. | Better leaf/branch silhouettes, natural species/placement variation and measured mobile LODs. |
| Lighting | Existing ACES, sun, sky, environment reflections and shadow pipeline retained; static capture framing added. | Consistent sky/reflection illumination, softer contact detail and measured day/night tuning. |
| Characters | Exactly two articulated officers and one driver with visible wrist interaction. | Properly licensed rigged humanoids, realistic proportions, skin/clothing materials, authored exit/walk/cuff animation and foot locking. |

## Known staging limits

- The original patrol car has a merged closed body. Opening door overlays are
  visual staging, not a validated cutaway door mechanism. Driver emergence also
  lacks a fully articulated car-door/interior animation.
- The small visibility graph avoids the two stopped car envelopes, including
  opposite-facing patrols. It is not a pedestrian navmesh: buildings, railings,
  transit, close overlapping cars and arbitrary obstructed/off-road locations
  need authored walkable staging and camera-obstruction work before release.
  The path fallback is intentionally documented in source.
- Poses and gait remain visibly stylized. Turns at path corners, hand/foot motion
  and the change to the closer shot need animation polish. The cuffs are small,
  especially on phones. No photorealism or universal staging claim is made.
- Mobile evidence uses desktop Chrome with a portrait viewport, not a physical
  phone GPU or a touch-driving acceptance run. Safari, sustained performance,
  audio listening and all-route/all-car arrest locations are not accepted here.

## Review and verification

Run from `web/`: `npm ci --ignore-scripts --no-audit --no-fund`, `npm test`,
`npm run build`, and `npm run serve` (local `127.0.0.1:8080`). From the repository
root run `python3 tools/verify-standalone.py <output-json>` and
`node tools/build-static.mjs`. The latter builds locally; it does not deploy.

The test chain now has 56 command stages. New tests cover the real boxed-in
trigger, exactly two officers, input/recovery freeze, pause, duplicate triggers,
one zero-reward result, ineligible capture results, replay, vehicle-clear paths
at four patrol headings, actual hand-to-wrist proximity, finite scene geometry,
desktop/portrait framing and material changes. Existing regression checks retain
the 138 protected runtime files and existing original assets byte-for-byte.

Browser evidence uses an isolated installed Google Chrome through Playwright
because the Browser plugin is unavailable. It checks desktop 1440×900 and
portrait 390×844. The existing accessible primary action is
"Play COAST SPRINT on HOT COAST" (the suffix changes with setup), not simply
"Play". The test was corrected to that observed name; the product was not renamed.

The browser fixture puts a patrol nearby and raises arrest progress just below
the threshold, then lets the real police update trigger capture. Stage screenshots
seek a paused capture for inspection. The video also includes a natural,
unmodified eight-second playback through all four phases to **Caught**. This is
controlled feature QA, not evidence of a human-driven full pursuit. Pause/replay,
Home cancellation, a dispatched blur event and actual `WEBGL_lose_context`
interruption are checked. `qa.json` records final pass/fail, console output and
the precise evidence inventory. The final review archive also contains the test
log, standalone-integrity receipt, changed-source patch and source-file hashes.

Initial test failures were an obsolete exact accessible-name selector and a
portrait framing assertion. Visual inspection additionally found a hood-crossing
officer path and an overly wide interaction view. The selector, framing and path
were corrected; original failed screenshots are excluded from final evidence.

### Final acceptance record

| Check | Outcome | Scope |
| --- | --- | --- |
| `npm test` | PASS, 56 stages, exit 0 | Full existing chain plus new capture test. The focused capture/UI checks were also repeated after framing and pause-control refinements. |
| JavaScript syntax | PASS, 123 files | Repository JS/MJS excluding dependencies, generated distributions and vendored code. |
| Standalone build | PASS | 106 existing assets embedded; byte-for-byte inventory, font, bundle and third-party notices verified. |
| Static package build | PASS | Local output only; no publishing. |
| Protected runtime/native sources | PASS | Existing 138 protected runtime files and all 45 Blender source hashes retained. |
| Desktop/portrait Chrome review | PASS | Actual WebGL rendering, 1440×900 and 390×844, no app console errors/warnings; screenshots and video. |
| Capture interruptions | PASS | Real Pause capture button, repeated trigger, replay, Home cancellation, dispatched blur, and actual WebGL context loss. |
| Earlier failed checks | RESOLVED | Selector/framing tests and image-review route/framing findings corrected; no unresolved failing automated check. |
| Safari/physical phones/performance/audio listening | NOT RUN | No cross-browser, physical-device FPS or sound-quality acceptance claim. |
| All-world pedestrian navigation/camera clearance | NOT ACCEPTED | Tight scenery/overlapping-car staging remains limited; see known limits above. |
| Production publication/deployment verification of this candidate | NOT RUN | Intentionally unpublished. R3.5 production remains unchanged. |

No push, Vercel deployment, new credentials, asset purchase or production change
is part of this candidate. Existing published-release manifests intentionally
continue to describe R3.5; they are not relabelled as a new accepted release.
