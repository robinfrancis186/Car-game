# Silver angular fan-concept car

Original Blender-authored optional game vehicle inspired by the user-supplied silver wedge and rear-wing photographs. It is an approximate fan concept, not manufacturer CAD, not an official Tesla product asset, and not an engineering simulation. No photographs, manufacturer logos or downloaded meshes are embedded. The four wheel assemblies are reused from this project's original Blender model.

## Files
- `car_silver.blend`: editable Blender scene with articulated wheel and wing nodes.
- `car_silver.glb`: browser-ready glTF 2.0 asset. Identical public copy: `web/public/assets/car_silver.glb`.
- `car_silver_preview_front.png`, `car_silver_preview_rear.png`: 1280×800 actual-GLB reimport renders in Cycles CPU, up to 384 adaptive samples (minimum 64, threshold 0.015), no denoiser. Inspected for canopy continuity, genuine arch openings, tire fit, nozzle/wing details and export consistency.
- `car_silver_manifest.json`: complete integration contract and budget.
- `car_silver_validation.json`: actual-GLB Blender hierarchy, rotation and static tire-intersection tests.
- `car_silver_pose_validation.json`: initial lean-only cosmetic roll/pitch corner tests.
- `car_silver_combined_pose_validation.json`: complete sampled roll/pitch/body-only-heave/steer envelope tests (216 tire/body checks per candidate envelope).
- `car_silver_render_validation.json`: exact final-GLB hash and high-sample preview provenance.
- `car_silver_validate_three.mjs`: reusable Node test; optional input GLB and output JSON arguments.
- `car_silver_three_validation.json`: independent Three.js 0.170.0 GLTFLoader parse and node-motion checks (Node test, not browser rendering).
- `blender/build_silver_car.py`: reproducible original mesh construction. Requires project's `assets/web/car_web.blend` for original wheel assemblies.

## Browser budget
29,571 triangles, 29 material primitives / draw calls, 10 merged mesh nodes, 1,332,188 bytes. No textures or external resources. Body paint material retains exact API name `Crimson multi-coat | original fan concept` for runtime recoloring, but defaults to silver here.

## Articulation (Three.js axes)
- Root `CAR_ROOT`, static body `CarBody`; +X forward, +Y up, -Z left. Units are meters.
- `Steer_Front_Left`, `Steer_Front_Right`, `Steer_Rear_Left`, `Steer_Rear_Right`: local Y steering. Front hubs x=+1.35; rear hubs x=-1.35; vertical y=0.368; lateral z=±0.924.
- Each `Spin_*` is a child of its corresponding steering pivot; rotate local -Z for forward wheel travel. Rolling radius 0.366 m.
- `Caliper_*` is under steering, not spin. Material-multi-part GLBs may load each `Wheel_*` and `CarBody` as a Three Group with mesh children; traverse when recoloring or finding renderable geometry.
- `AeroWing_Hinge`: rotate local -Z; `AeroWing` is its child. Static pylons remain part of `CarBody`.
- `Thruster_Rear_0` through `_3`: rear VFX sockets, fire toward -X.
- `Thruster_Down_RL`, `Thruster_Down_RR`: downward VFX sockets, fire toward -Y.

## Cosmetic chassis motion
Animate a runtime visual group containing `CarBody`, `AeroWing_Hinge` and all `Thruster_*` sockets so the wing, pylons and jets move together. Keep `Steer_*` wheel nodes separate. Recommended combined visual-only clamps for this tight-fender model: roll ±0.010 rad, pitch ±0.006 rad, and body-only vertical heave ±0.002 m. All 27 combinations of negative/zero/positive roll, pitch and heave passed, each tested with both front wheels at steer 0/±0.4 rad and rear wheels at zero (216 individual tire/body checks). Keep wheel pivots fixed vertically so cosmetic bob does not move tire contact. The larger lean-only range ±0.012/±0.008 passes at zero heave but **does clip when combined with -0.002 m body heave**. Larger lean values also clip. These tests cover the stated discrete configurations, not every possible continuous trajectory. Do not equate these static geometry checks with real suspension simulation.

## Verification actually run
- Actual GLB reimport: all four steering/spin hierarchies and stationary-caliper parent relationships PASS.
- Blender imported pivots explicitly switched to Euler mode before rotation tests; test vertex movement asserted (to prevent vacuous quaternion-mode tests).
- At spin 0.7 rad, sample tire vertices moved ~0.251 m; all caliper matrices and hub centers remained unchanged.
- At wing pitch 0.18 rad, sample wing vertex moved ~0.0521 m.
- BVH tire/body surface tests: zero overlapping triangle pairs with front steering 0 and ±0.4 rad, and rear steering 0. Axle-area undertray notches provide steering clearance. This is a static surface-intersection test, not a suspension/contact/dynamic-safety claim.
- Three.js GLTFLoader independently confirmed steering moves a sample tire vertex ~0.1454 m, wheel spin moves it ~0.251 m, wing pitch moves it ~0.0521 m, and calipers do not spin.
- Public/source GLB SHA-256 match: `3bec86298c9c22a7e1e91deeff4ef2a614744cadf170e9abea2855f2ec82a749`.

## Rebuild
```sh
blender -b --threads 4 --python blender/build_silver_car.py
# Geometry, exports and checks without re-rendering:
blender -b --threads 4 --python blender/build_silver_car.py -- --no-render
```
Run from `kerala_racing/` (or pass the script's absolute path). Browser integration and vehicle-handling tests are owned by the main game project.

## Deliberate limitations
This is a lightweight original approximation, not a photoreal or production-accurate model. Opaque bronze-black PBR glazing avoids costly browser transmission; this optional variant has no detailed cockpit. Metallic paint and aero structures use material values rather than photographic texture maps. Flight, nozzle behavior and active-aero behavior are fictional game mechanics. Reference photographs are not shipped in the asset.

## Final runtime steering constraint
The frozen silver mesh supports front visual steering **±0.4 rad** under the shared game chassis envelope (roll ±0.008, pitch ±0.005, heave ±0.002 m). Later extended tests at ±0.57/±0.6 rad found tire/body clipping even with no chassis lean. Cap silver visual steering at ±0.4; changing cosmetic lean alone does not fix the larger steering angles. `car_silver_extended_steer_validation.json` deliberately retains that failed wider-range test. `car_silver_common_pose_validation.json` checks the supported release range. Neither changes the GLB hash.
