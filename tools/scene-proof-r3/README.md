# R3 original coastal pavilion — scene source and offline proof

**Status:** runtime and proof source frozen. Final corrected proof inspected by child and parent: a partial visual improvement only. Orange sea-edge wedge and dark headland bar are resolved in the offline proof; sea remains muted/flat, foliage repetitive/stylized, ceiling composition imperfect and some grain visible. Not published, not a WebGL screenshot, not exact/photoreal reference acceptance.

## Runtime scope

Only `web/src/scene.js` and `web/src/showroom-scene.js` changed in this pass. The reflector implementation, original GLBs, driving cameras, physics, routes, upgrades, economy and saves were not changed.

- Darker warm cedar/charcoal interior; lower golden sun, richer custom sky, original curved planted border and deep reflective slate.
- Original menu-only PMREM environment replaces the bright gray studio environment.
- Light colors, light intensities, environment and exposure restore exactly on menu exit.
- Desktop Home fixed-angle camera minimum scale is 0.82. Garage keeps its original 1.0 minimum, and portrait values are unchanged: an experimental closer Garage camera failed actual seven-car 360 bounds and was rejected.
- The final sea is a real 10km square/two triangles. The earlier narrow rectangle exposed the sky past its side under the oblique camera, causing an orange wedge. The sky radius is 5km, within the unchanged 6.5km camera far plane. Distant headlands are low atmospheric geometry rather than the earlier dark bar.
- Runtime scene: 56 meshes / 49,184 triangles including loaded original palms. Procedural pavilion excluding palms: 20 meshes / 11,906 triangles. The existing 512px reflection is still one additional menu render pass; no measured FPS claim is made.

## Reproduce the offline proof

From the project root, with its pinned Three dependency installed and Blender available:

```sh
node tools/scene-proof-r3/export-scene.mjs
blender -b -t 8 --python tools/scene-proof-r3/render-pavilion.py -- \
  --source-root "$PWD/web/public/assets" \
  --geometry "$PWD/tools/scene-proof-r3/pavilion-geometry.json" \
  --output "$PWD/tools/scene-proof-r3/rebuilt" --width 960 --samples 384
```

The geometry JSON is generated from the current actual runtime pavilion meshes and can be regenerated. The original car is imported directly from `web/public/assets/car.glb`; its source geometry/materials/livery are not edited. Input hashes, including palms, are recorded in `runtime-input-hashes.json`. No private reference PNG/JPEG, image URL or copied screenshot pixel is loaded by either script.

## Exact evidence boundary

The Blender proof preserves exported pavilion geometry but is **not** a browser capture:

- Three sky shader -> original Blender procedural cloud-emission nodes on the same dome.
- Three ocean shader -> physical wave-normal material plus a restrained authored teal ambient term on the same sea geometry.
- Three planar-reflection floor shader -> Cycles glossy procedural tiles on the same floor geometry.
- Runtime PMREM/point lighting -> original Blender sunset sun/large soft areas.
- Offline camera -> an authored reference-composition camera, recorded in the render receipt, not a captured runtime UI camera.
- The source car's imported materials are unchanged; runtime paint styling, profile upgrades, UI and dynamic values are not represented by this offline scene proof. Loaded palm geometry is exact; its inherited world-material styling can vary from the standalone export.

No full photorealism or exact screenshot match is claimed. Remaining gaps include simplified original palms, repetitive border foliage, approximate sea/sky lighting, and render grain because supported CPU Blender has no denoiser. Native WebGL/UI fit, performance and full responsive visual acceptance remain separate parent QA gates.

## Checks

- Actual `scene-contract.test.mjs`: passed, including seven-car 360/Home bounds, upgrade visuals and driving/cinematic behavior.
- `portrait-menu-projection.test.mjs`: passed (390×844, 320×568, 430×932; 35 cases each).
- `verify-menu-isolation.mjs`: passed, 48 mode transitions; exact light color/intensity/exposure/environment restoration and finite geometry.
- All are graph/state checks, **not GPU verification**. The ocean-coverage regression assertion verifies that the sea square contains the full sky-sphere horizontal cross section, preventing the finite-plane side-edge defect.

`proof-final-corrected/pavilion-crimson.png` is the only selected final partial proof. Its PNG, editable `.blend`, and render receipt are retained. Rejected intermediate images/logs were moved outside this candidate. The 4.4MB geometry JSON is retained as a direct, hash-verifiable Blender input (and compresses well in the full source backup); it is also reproducible from the frozen runtime source.

The two earlier proof images with a visible orange ocean wedge were rejected and are not the final proof. No Shop batch was produced from this scene.
