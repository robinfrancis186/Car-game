# V17 R3.2 — graphics-interruption safety (unpublished)

This separate candidate advances R3.1 without changing the live V16.1 game or the hosted R3 review. It is not publication approval or native GPU acceptance.

## Concrete defect

The installed, locked Three.js 0.170.0 renderer stops drawing when its WebGL context is lost. The former application controller did not listen for that event, so its animation callback continued advancing driving, race time and audio while a visible tab had no rendered view. A simulated context-loss event reproduces that control-flow defect; it is not a physical GPU-loss test.

## Correction

- Latch graphics interruption immediately, stop simulation/render callbacks, pause the model, clear held controls and silence audio.
- Reuse the existing accessible loading-error dialog with a **Graphics interrupted** explanation and explicit **Reload** action.
- Never automatically resume a race after a browser context-restored event, focus change, repeated loss, or late asset completion. Reload intentionally abandons the current run.
- Ignore late asset progress and failure callbacks so they cannot erase the interruption message or reopen the game.
- Do not write, reset, award or migrate any progression in the interruption handler. If storage was already session-only, warn that reload can lose session-only changes.
- Include dedicated controller regressions using actual gameplay/storage logic, synthetic DOM/audio/rendering, and simulated graphics events.

Only `web/src/main.js` is intended to change among R3.1 runtime files. CSS, HTML, game assets, physics, economy and save modules remain byte-identical. The package test command includes the new regression; dependency versions and package lock remain unchanged.

## Reproduce

Use Node 20 or newer and a writable npm cache:

```sh
cd web
npm ci --ignore-scripts --no-audit --no-fund --cache ../.npm-cache
npm test
npm run build
```

The first attempt in this cloud workspace used npm's default cache location, which was unavailable. The bounded retry used a cache inside the permitted workspace and successfully installed the exact locked packages. No dependency versions, integrity checks or lifecycle-script restrictions were relaxed.

## Evidence boundaries

The current receipts are under `tests/v17/r3-2-evidence/`; old R3 and R3.1 receipts are baseline provenance. The final manifest anchors the exact new runtime and standalone build. Test and build results establish source/controller/scene-graph behavior, not real GPU restoration, rendered appearance, mobile handling, frame rate or audio listening. Those acceptance gates remain open. No push or deployment was performed.
