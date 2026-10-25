# V15 model validation / frozen handoff

All checks below were run against the frozen model source listed in `model_freeze.sha256` and the exact enabled runtime configurations. These are pure-model/geometry checks, not a claim of browser rendering, human handling acceptance, rigid-body loop support or real-vehicle flight behavior.

| Suite | Passing checks | Additional coverage |
|---|---:|---|
| Airtime / air support | 40 | Reward caps, contact/teleport/manual-thrust rejection, quiet contact, AI sidewall entry, intermediate deck LOS, safe clearance, pause/recovery/result lifecycle |
| Exact-world ramps | 98 | 42 stock jumps across seven cars/two tracks/30–60–120Hz, 14 fully upgraded boosted jumps, 42 complete races |
| Existing gameplay | 208 | Both courses, ordered gates, actual world collisions, grades, Explore starts |
| Garage / boost | 76 | Existing local purchase/performance loop and upgraded driving |
| Dedicated braking | 82 | 672 stopping runs, frozen reverse-crawl block hash |
| Handling / recovery | 383 | Binary-input comfort, impacts and endpoint-safe returns |
| Reverse crawl | 63 car/surface/grade fixtures | 30/60/120Hz; 231 actual obstacle approaches, 189 contacts |
| Coins / vehicle | 20 | Real earn→purchase→reload→performance loop |
| Story model | 38 | 30 actual driven story events |

Exact default comparison against frozen V14.1 also passed: four scenarios, 14,400 fixed steps, player/all AI/events exactly equal with ramps absent and airTraffic false. `garage.js` and `story.js` are byte-identical to V14.1. The braking test's former whole-file historical hash was replaced by the exact unchanged reverse-crawl block hash plus the retained stock-vs-constant-brake behavioral comparison; new imports resolve portably from its in-memory module.

## Measured new-feature results

- Exact world: all 42 full races finished with zero damage and zero recovery. The conservative sprint controller finished third; this is **not** a first-place/win claim.
- Actual red-car stock jumps: Coast approximately1.48s /61.86m and0.05933 energy added; Highland approximately1.39s /58.01m and0.05567 energy added at120Hz.
- Fourteen maximum-upgrade controlled jumps launched at67.79–68.07m/s and landed cleanly. This is not a guarantee that arbitrary full-speed steering/flight inputs are safe.
- Moving target at30m/s: police beam visible9.992 of the final10s; conservative model gimbal angle≤0.57681rad. Renderer/camera visibility is tested separately by the parent.
- Aircraft obstruction fixture: minimum clearance18.0667m, max climb9m/s; full9.2m swept-airframe footprint is used in world roof/terrain sampling.
- Runtime hashes still match the exact-world report. No candidate overrides remain in the test: enabled root/nested ramp metadata must agree.

Reports: `web/tests/airtime_air_support_metrics.json`, `airtime_world_metrics.json`, `v15_default_compatibility_metrics.json`, plus existing suite reports. Source freeze is for the model-owned files only; the parent owns whole-build acceptance and publication.
