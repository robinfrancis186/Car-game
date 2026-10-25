> Historical R1/R2 record retained for provenance. It is not current R3 acceptance evidence. See the root `design-qa.md` and `STATUS.md` for R3 status; supported cloud CUA later became available, but WebGL remains disabled. Do not rerun the historically denied custom Chromium launch.

# V17 reference UI candidate — unpublished

## Visual targets actually inspected

The latest two user uploads are distinct from the earlier pair. Actual image pixels were inspected through local JPEG inspection copies (the PNG viewer transport failed). Latest Workshop and Shop take priority; earlier Home and Run Ended are consistent supporting targets. Original references and inspection copies are outside this project and are excluded from all runtime and source archives.

- Home: warm orange full-width Play tile, Garage/Map row, Shop/Story/Workshop row, outlined icon dock, left display wordmark, right original 3D car.
- Workshop: back/title/subtitle header, Inspect/Owned/Shop tabs, left car information card, five compact performance rows, outlined coin actions, right interactive original car. Existing 360-degree drag/arrow orbit remains active.
- Shop: three desktop columns, locked badges, original-model thumbnails, names, true performance bars and prices, Inspect action. Filter buttons and sort dropdown are functional presentation-only grouping and do not alter car capability or economy.
- Run Ended: centered dark translucent card, display heading, clock, finish/collected breakdown, total row, orange Retry, Help/settings and Home.
- Shared stage: actual Three.js glass/steel coastal pavilion, cedar ceiling, tiled floor, original 3D palms, procedural sunset sky/ocean/headlands, 512px planar reflection. No photo/screenshot overlay. Original car geometry is unchanged.

## Dynamic truth retained

The supplied 580 balance is a reference state, NOT a new default. Real saved balance and ownership remain authoritative on each device. Crimson and Silver are the only free cars; all five other cars retain their original coin prices. The 20-coin figure at a level-one upgrade with 580 balance is labeled MORE COINS, not falsely offered as a 20-coin upgrade. Purchases still cost 300/600/1000 and change actual performance/parts; caliper colors remain red/red/orange/violet. Shop previews cannot purchase or replace the selected owned car. Home carousel only cycles owned cars.

All 138 protected V16 modules/assets and139 of 143 frozen V16.1 runtime files remain byte-identical. Only HTML, CSS, main UI controller and menu-only scene integration are changed; two scene helper modules are added. Normal racing physics, surface-wall route, saves, rewards, coins, audio and original models are unchanged.

## Verification status and limitations

- Source/controller, geometry and byte identity checks are not rendered acceptance.
- The full game build and106 embedded-asset/notice identity audits pass.
- The old generated interface preview is layout-only and save-isolated. Its stale Loft image background has been removed; it must not be used to assess the new real 3D pavilion. The V16.1 preview alias remains only for inherited tests.
- Cloud Chromium cannot start: normal launch reports `process_singleton_posix.cc:297 socket() failed: Operation not permitted`; supported escalation is blocked by wrapper `bwrap: Can't create file at /home/agent/.codex/sessions: Read-only file system`. No denied-path read or workaround attempted.
- Therefore no V17 screenshots, screenshot comparison, WebGL rendering, native FPS, audio listening or exact visual match is claimed. Exposure, car/environment framing, reflection support and shader rendering remain unverified.
- Known visual gap: current Shop cards retain original transparent-model thumbnails on styled gradients; they are not the reference's photorealistic coastal car photographs. After a supported cloud browser is restored, render new scenic card art from our own actual models if needed; never crop/reuse the user's references.

## Required acceptance before publishing

Run `node tests/v17/browser-qa.mjs` in a supported cloud browser environment, then inspect saved actual-game pixels against the four private references at 1440x722,390x844,844x390,320x568. Iterate until controls, panel bounds, 360-car framing, contrasts and scene composition are accepted. Check isolated 580-coin save (never user Mac), upgrade/ownership/reload and wall-route regression. Native user-browser testing remains a separate parent-owned gate. This candidate MUST NOT replace live V16.1 without parent review.

## Frozen source gate — 2026-10-23

The final `npm test` command, including the inherited aggregate suite, new V17 reference-UI controller tests and138-file preservation test, exited0. `tests/v17/aggregate-result.json` and `npm-test-frozen.log` are the evidence. The standalone rebuild and106-asset/license audit pass; CSS parses with zero warnings. This final source gate does NOT remove the browser/screenshot blocker above.
