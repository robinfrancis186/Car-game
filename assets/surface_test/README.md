# Harbour Wall Run — original solo surface proof

A separate optional 900 m test route. It does not alter the coastal or Highland courses, is not a source-video reconstruction, and is not a ceiling, tube or full loop.

## Shared mathematical contract
The canonical file is `docs/v16/surface_profile.json` (SHA-256 `ab19f552d0dca7bec8aa93b8c03773d9fa42fd4f81dbbc0176e98d5a563e6698`). Runtime copies contain the same JSON values. All coordinates below are Three.js metres, +X forward, +Y up, +Z right.

- Centre: `[s, 8, 0]`; half-width: 6 m; finite domain: `0 <= s <= 900`.
- Flat approach: 0–160 m.
- Quintic smooth bank from 0° to 90°: 160–360 m.
- 90° wall: 360–540 m.
- Quintic smooth return to 0°: 540–740 m.
- Flat runout: 740–900 m, with SLOW/RETURN and END roadside signs.

For lateral coordinate `l`, bank `b(s)`, derivative `b'(s)`:

```
S(s,l) = [s, 8 + l*sin(b), l*cos(b)]
dS/ds  = [1, l*cos(b)*b', -l*sin(b)*b']
dS/dl  = [0, sin(b), cos(b)]
N(s,l) = normalize([-l*b', cos(b), -sin(b)])
```

Positive-right banking raises the right edge to Y14 and lowers the left edge to Y2. At 90°, the driveable normal is -Z. The quintic blend `6t^5 - 15t^4 + 10t^3` has zero first and second derivatives at each endpoint. The model uses the analytic surface; exported triangles are a measured approximation, not an exact continuous match.

## Geometry, materials and authoring
- Editable source: `Surface_Test_Route.blend`.
- Generator: `blender/build_surface_test_route.py`; reads the canonical profile directly.
- Three separate world-space GLBs: `SurfaceTest_Road`, `SurfaceTest_Furniture`, `SurfaceTest_Terrain`.
- Adaptive top tessellation limits angle/derivative changes, with collinear coincident row boundaries. Exact sampled intervals and lateral counts are in `manifest.json`; canonical mesh spacing is only the nominal starting recipe.
- Asphalt has authored metric ribbon UV, exported as `(s*0.5,l*0.5)`. UVs do not collapse on the vertical wall. No new texture images or materials shader dependencies are shipped; the existing renderer supplies its original asphalt micro-detail.
- Two-sided zero-thickness driving ribbon, narrow 24 cm edge fascia, open supporting piers and transverse beams. **There is no closed underside volume.** A coarse cosmetic underside was removed after it was seen intersecting the twisting surface.
- Segmented safety beams lie outside the lane at lateral ±6.38 m and normal offset 0.52 m. They are **non-solid guidance geometry**, not a full collision barrier or an invented invisible driveable strip; crossing the finite ribbon edge loses contact. Model-owned edge/departure behavior is separate.
- Angle signs use original Blender text outlines. No photo textures, manufacturer markings or downloaded mesh.
- Flat dry ground below, restrained low service-block silhouettes; no ocean or water plane, no air traffic, road traffic, transit, rewards or coin placements.

## Runtime handoff
`course_runtime_surface_test.json` has id `surface-test`, 901 centreline points, embedded `surface_profile`, `free_drive_only:true`, garage start S50, explicit district metadata, dedicated empty furniture collider file, visible support/sign box proxies and a flat ground grid. No Coast default furniture file is reused. Finite endpoint return/recovery, adhesion, speed limits and camera behavior are implemented/tested by the gameplay/renderer owners, not by the Blender generator.

## Validation and render scope
`validate_surface_test.mjs` loads actual GLBs through Three GLTFLoader and checks every triangle/normal, matching public copies, normal-directed analytic contact rays, structural intrusion rays, true bank-joint derivatives, asphalt wall UV determinants and paint clearance. `glb_validation.json` records exact final numbers and hashes. The 0.5° normal/1 cm contact targets apply to the measured sample set, not an unsampled formal bound.

Four `preview_*.png` images are actual exported GLBs imported into Blender, rendered with CPU Cycles at 48 samples and no denoising. They are **not gameplay screenshots**. Each has adjacent source-hash/camera provenance JSON. The preview uses original procedural asphalt micro-bump as a native approximation of runtime surface detail.

Original project geometry/materials: **reuse license not selected by owner**. No new project-wide CC0/MIT/public-domain grant. Existing third-party software notices remain applicable.
