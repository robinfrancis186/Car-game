# V17 R3.1 design QA — pending rendered acceptance

R3.1 is a narrow CSS hit-target correction based on actual R3 browser evidence. It changes no scene or functionality. Source and synthetic tests cannot prove the new target dimensions or header spacing until rendered in an authorized supported browser route.

## R3 findings (actual pixels, not this patch)
All 16 Home/Workshop/Shop/results samples were inspected at 1440×722, 390×844, 844×390, 320×568. Home had no duplicated dock, no caption/control overlap and all visible Home controls ≥44×44. All four body bounds matched viewport. Built-in 308 cases passed but omitted actual targets that independent DOM measurement found: native Shop select 36px high at every size; 844×390 Workshop/Shop utilities/back 36×36; Shop ALL 37.56×44. Thus R3 verdict is changes required, not blanket pass.

## Patch gates
- Actual new 44×44 targets, no title/wallet/header overlap, and unchanged four-size bounds: pending rendered R3.1 review.
- Full source aggregate/build: see new R3.1 receipts, not inherited R3 logs.
- Exact runtime delta: style.css only ; 144/145 R3 files unchanged.
- Actual 3D/native: blocked in cloud. R3 game root shows Graphics unavailable with GL_VENDOR and GL_RENDERER Disabled, BindToCurrentSequence failed.
- Photorealistic coastal Shop cards and scene match: not achieved. Existing original stills/gradient backgrounds and stylized car remain a gap. Offline Blender proof is partial and not gameplay.
- Production/pending Sites37: unchanged, no publication authorized.

No uploaded private reference pixels are incorporated. Historical detailed R3 scene proof and earlier blocker notes remain in `docs/provenance/r3-baseline/design-qa.md`.

## Reproduce patch-specific checks from a clean restored source
```sh
cd web
npm ci --ignore-scripts
npm test
node tests/v17-r3-1-hit-targets.test.mjs
npm run build
cd ..
python tools/audit_standalone.py
python tools/audit_runtime_payload.py
node tools/ui-review-r3-1/build-review.mjs
node tools/ui-review-r3-1/review-smoke.test.mjs
```
The last script is synthetic and does not start a browser. Use only an authorized supported browser/review route for actual pixels; do not retry denied custom Chromium or hosting publication.
