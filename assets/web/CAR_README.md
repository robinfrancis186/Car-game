# Browser vehicle assets — frozen prototype release

Original Blender-authored fan interpretations, not Tesla CAD or verified production models. No third-party mesh or photo texture is redistributed. Police equipment is generic/fictional; no official Kerala Police insignia is included. Flight/thruster handling is fictional gameplay, not engineering simulation.

## Red car

- `car.glb`: **904,716 bytes; 29,957 triangles; 33 material primitives; 9 glTF mesh definitions**. Three's loader splits material primitives into mesh children; 9 is the assembly count, not the renderer's complete mesh-object count.
- SHA-256: `4a8b5f4fe463822c9641b48f68233bdb12bea75a37368200c5c164277b2a6bc9`.
- Exact public copy: `../../web/public/assets/car.glb`.
- `car_web.blend`: editable optimized derivative.
- `car_manifest.json`: budget, hierarchy, material API and per-part reduction audit.
- `car_validation.json`: actual GLB reimport, hierarchy, material, copy-hash and steering-clearance checks — **PASS**.
- `car_three_validation.json`: actual Three.js 0.170 GLTFLoader parse and vertex/control motion tests — **PASS**, not a browser rendering test.
- `car_web_preview.png`: actual reimported GLB rendered in Blender for QA, not gameplay.

### Three.js contract

Axes **+X forward, +Y up, -Z left**. Approximate dimensions 4.512 m length × 2.330 m width including mirrors × 1.23 m height.

- Root `CAR_ROOT`; static body assembly node `CarBody`.
- `Steer_Front_Left`, `Steer_Front_Right`, `Steer_Rear_Left`, `Steer_Rear_Right`: local **Y** steering, rear normally zero.
- Corresponding `Spin_*` children contain `Wheel_*`. Forward rolling: `spin.rotation.z -= distanceMeters / 0.366`.
- `Caliper_*` is a child of steering, not spin.
- Paint material: exactly **`Crimson multi-coat | original fan concept`**. Clone shared materials before per-car recoloring.
- Opaque dark PBR glazing deliberately avoids transmission cost. The detailed Blender source retains separate transmissive glass and refined cockpit. An actual interior camera would require deliberate canopy/material and camera-clipping work; bonnet mode is separate.

### Geometry/cosmetic movement evidence

Neutral-body wheel clearance passes actual mesh tests at steer 0, ±0.4 and ±0.6 rad, with sample-vertex displacement assertions to prevent stationary false-passes. Undertray cutouts are preserved without destructive reduction; sill tips are shortened.

`car_cosmetic_pose_validation.json` records sampled combined chassis poses. Requested large roll/pitch/heave failed, correctly recorded as a negative test. Smaller sampled limits roll ±0.008 rad, pitch ±0.005 rad and body-only heave ±0.004 m passed at the originally sampled steering angles. **The game uses the stricter shared setting: roll ±0.008, pitch ±0.005, chassis-only heave ±0.002 m**, with grounded independent wheels. `car_common_pose_validation.json` additionally checks the exact shared setting and runtime steering maximum. These are sampled static geometry checks, not continuous suspension/contact/dynamics proof.

### Reduction

Body shell retains approximately 6,000 triangles. Shared canopy boundaries and undertray wheel cutouts are preserved. Sub-pixel tread sipes, lug bolts, inner rim lips, stitching and static dashboard glyphs/map lines are omitted. Detailed perforated rotors become simple low-LOD discs; wheel barrel caps remain open. Cabin surfaces are reduced more aggressively than exterior surfaces because glazing is opaque. Body/wheels/calipers are merged by assembly/material, with high-detail editable parts retained separately in `../car/`.

## Silver wedge variant

`car_silver.glb`, its exact public copy, `.blend`, front/rear previews, manifest, README and independent validation files are under `car_silver*`. Final budget **29,571 triangles / 29 material primitives / 1,332,188 bytes**. Same wheel/paint API; additional articulated `AeroWing_Hinge` and six fictional thruster FX sockets. Refer to `car_silver_manifest.json` and `car_silver_README.md` for exact socket names/positions. Silver has opaque glazing and no detailed cockpit. **Silver visual front steering must be capped at ±0.4 rad.** Extended ±0.57/±0.6 tests clip even at zero chassis lean; the negative evidence is retained in `car_silver_extended_steer_validation.json`. The supported common-pose envelope is checked separately in `car_silver_common_pose_validation.json`.

## Generic police lightbar

`police_lightbar.glb` and matching public copy: 3 meshes, 564 triangles, 18,356 bytes. Original Blender source is `police_lightbar.blend`.

Bottom-center origin; mount the root at **[0, 1.232, 0]** on the red car. Three XYZ size **[0.29, 0.115, 1.02] m**. Emissive material names: `PoliceLightbar_Red`, `PoliceLightbar_Blue`. No official insignia or real police-vehicle claim.

## Rebuild / tests

From project root:

```sh
blender -b --factory-startup -t 2 --python blender/optimize_web_car.py
blender -b --factory-startup -t 2 --python blender/test_web_car.py
node assets/web/car_silver_validate_three.mjs assets/web/car.glb assets/web/car_three_validation.json
blender -b --factory-startup -t 2 --python blender/test_common_car_cosmetics.py
```

The common-pose checker reads both final GLBs and does not modify geometry. `car_overlap_debug.json` is historical evidence from before the clearance repair, not the final release result. No rendered browser gameplay or Unreal test is claimed by these asset reports; those require separate runtime evidence.
