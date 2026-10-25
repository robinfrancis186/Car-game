# V13 Silver surface and glazing refinement

Original project interpretation, not manufacturer CAD or an exact branded replica. This is a bounded update to the existing Silver car, not a new vehicle.

## Changes
- Replaced the very sparse faceted shell with closely sampled, smoothly shaded hood/shoulder/side surfaces while retaining the wedge proportions and exact overall footprint.
- Curved the front fascia in plan and narrowed its dark band.
- Replaced opaque brown glazing with a neutral blue-charcoal, clear-coated translucent material and compound-curved panes. Added a compact original cockpit beneath the glass: recessed floor, seats/bolsters/stitch seams, dashboard and unbranded steering wheel.
- Preserved the exact existing wheel vertex-coordinate set, root/steer/spin/caliper/active-wing hierarchy, six thruster sockets and all their transforms.

## Source and runtime files
- Generator: `blender/build_silver_car.py`.
- Construction source with named editable parts/modifiers: `assets/cars/silver_refinement/silver_editable.blend`.
- Rigged compact native source: `assets/web/car_silver.blend`.
- Runtime: `assets/web/car_silver.glb`; matching `web/public/assets/car_silver.glb`.
- Original Silver dependency: `assets/cars/silver_refinement/baseline/car_silver.glb`, SHA `3bec86298c9c22a7e1e91deeff4ef2a614744cadf170e9abea2855f2ec82a749`. It supplies the existing original wheel assemblies; the former body is discarded by the generator.
- Rendering/test/cleanup scripts are retained in this folder. `clean_silver_glb.py` only removes zero-area float32 index triples; it does not move geometry or replace normals/materials.

## Unchanged runtime contract
Metres, glTF +X forward/+Y up/−Z left; Blender +X forward/+Y left/+Z up. Root `CAR_ROOT`, body `CarBody`; `Steer_* > Spin_* > Wheel_*`, with each `Caliper_*` fixed below its matching steering pivot. Hubs X±1.35, Y .368, Z±.924 in Three; nominal rolling radius .366 m. Supported visual front steer ±.4 rad. Active `AeroWing_Hinge` and six named `Thruster_*` sockets are preserved, as are existing default boost mounts. Fictional arcade flight/aero mechanisms are not production or engineering claims.

Exact paint API stays `Crimson multi-coat | original fan concept`. New glazing API is `Silver concept | neutral smoked glazing`, with authored alpha .72, roughness .085 and neutral blue-charcoal tint. The name avoids the legacy substring-based glass tint override; current parent V13 renderer also removes the previous Silver-specific brown override. No runtime source was edited by this asset task.

## Validation scope
`three_validation.json` compares actual old/new GLBs and checks every documented node transform, exact wheel coordinate sets, unchanged bounds, finite unit normals, nonzero-area triangles, paint/glazing identity, wheel spin and fixed calipers. `pose_validation.json` checks 756 actual whole-wheel/body configurations at the common body-only cosmetic envelope (roll ±.008, pitch ±.005, heave ±.002 m) and seven steering samples. Active wing clearance is tested at runtime 0, −.10, −.20 and −.236 rad, including maximum installed handling trim. These are discrete mesh tests, not continuous dynamics or engineering certification.

`runtime_scene_contract.log` records the parent's real Node/Three scene-contract suite. This does not establish WebGL pixels, frame rate, browser input or user-device acceptance. Studio previews come directly from the exported GLB; they are not gameplay screenshots. Cabin geometry supports exterior glazing; no new interior-camera mode is claimed.

## Reproduction
From project root:
```
blender -b --threads 4 --python blender/build_silver_car.py -- --no-render
node assets/cars/silver_refinement/validate_silver_refinement.mjs
blender -b --threads 3 --python assets/cars/silver_refinement/test_silver_poses.py
SILVER_VIEWS=front,side,thumb blender -b --threads 4 --python assets/cars/silver_refinement/render_silver_refinement.py
```
Studio lighting is not part of the car asset. Cycles CPU is used with no denoiser; visible Monte Carlo grain is not retouched.

## Provenance and rights
Original project geometry/materials. User screenshots were visually inspected as feedback only; no photographic pixels, emblems or downloaded CAD are embedded.

No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.
