# Original red Roadster-inspired car — final prototype assets

Original procedural Blender geometry, visually informed by the user's red Roadster photograph. This is an approximate **2017-inspired fan interpretation**, not Tesla CAD, an official model, a latest-production specification, or a finished production-quality vehicle. No downloaded mesh, photo texture or Tesla emblem is redistributed. Flight hardware/handling is fictional gameplay design.

## Deliverables

- `roadster_concept.blend`: editable detailed model, wheel steering/spin demonstration and independently animated RHD handwheel.
- `roadster_studio.blend`: same model with studio lights/camera, for inspection.
- `roadster_concept.glb`, `roadster_concept.fbx`: articulated full model. FBX deliberately does not bake animation.
- `SM_CarBody.fbx/.glb`, alias `car_body.fbx/.glb`: combined fixed body geometry at the car origin; includes fixed brake calipers for simple component import.
- `SM_Wheel_{Front,Rear}_{Left,Right}.fbx/.glb`: wheel assemblies centered on their respective hubs.
- `manifest.json`, `materials.json`: component/material metadata.
- `validation.json`: actual Blender/FBX/GLB checks; **PASS**.
- `parts_validation.json`: actual rotor/harness-slot topology and handwheel-animation checks; **PASS**.
- Browser-optimized derivative and its independent evidence: `../web/car.glb`, `../web/CAR_README.md`.

## Final per-part inspection images

These are **Blender component renders, not gameplay screenshots**, at 1000 × 900 and 96 CPU Cycles samples, without unavailable denoising:

- `part_right_hand_drive_cockpit_refined.png`
- `part_rotor_and_caliper_refined.png`
- `part_bucket_seats_refined.png`
- `part_wheel_and_steer_refined.png`

Files without `_refined` are earlier blockout inspection history, not final part views. `hero_front.png` and `hero_rear.png` show the reference-refined exterior; the later interior/machined-face cleanup is best inspected in the definitive part images above. `articulation_demo_NOT_GAMEPLAY.mp4` is an earlier, explicitly labelled Blender wheel-animation demonstration, not a game capture.

## Coordinates and control API

Blender meters: **+X forward, +Y left, +Z up**. FBX: `axis_forward='X'`, `axis_up='Z'`, `apply_unit_scale=True`. Wheelbase is **2.7 m / 270 cm**.

| Hub | X m | Y m | Z m |
|---|---:|---:|---:|
| Front Left | 1.35 | 0.924 | 0.368 |
| Front Right | 1.35 | -0.924 | 0.368 |
| Rear Left | -1.35 | 0.924 | 0.368 |
| Rear Right | -1.35 | -0.924 | 0.368 |

`CAR_ROOT` contains `Steer_Front_Left/Right`, `Steer_Rear_Left/Right`, each with matching `Spin_*` child. Steering rotates local **Z**; forward rolling rotates local **positive Y**. Visual rolling radius **0.366 m**. Calipers steer but do not spin in the articulated source. `Interior_Steering_Pivot` turns the handwheel about local X and follows the source steering demonstration at 3.2× its angle.

Approximate dimensions including mirrors/trim: **4.512 × 2.330 × 1.23 m**. These are not measured dimensions of a real Tesla.

## Refined modeled detail

- Closed sculpted shell, wheel cutouts, pronounced front haunches, concave flanks, shared-boundary canopy surfaces and thin integrated trim.
- Triangular inset projector lamps, hood/door/deck seams, mirrors, flush handles, splitter, shortened side sills, diffuser and fictional rear nozzles.
- Rounded tires/tread, open rim barrels, paired turbine spokes, hub/lugs, fixed calipers and **48 actual through-drilled apertures per rotor**. Each closed rotor has Euler characteristic −94, confirming 48 tunnels rather than raised decorative dots.
- Contoured bucket shells/pads, thigh and shoulder bolsters, stitching paths and two true harness through-slots in each back shell/pad.
- Shaped dashboard, vents, cup recesses, RHD steering column/handwheel and modeled vector instrument/navigation graphics. **Screen graphics are static parked-state design props, not live telemetry.**

## Test evidence and limits

Full GLB reimport: **509 detailed meshes, 8 steering/spin pivots, 16 used materials**, plus the separate interior steering control. Base mesh audit: **171,677 polygons** before evaluation/export triangulation. Five component FBXs reimport as one mesh each with centered origins. Wheel bounds pass the 0.3672 m visual-bound check. Closed outer body has zero boundary edges and outward signed volume. Shared windshield/roof/rear seam error is zero; side glass normals face outward. Fender-crown skin is approximately 92 mm above front tire crowns and 112 mm above rear crowns; **this is not the smaller radial wheel-arch clearance**. Combined chassis-pose checks, not this crown measurement, determine cosmetic movement limits.

The browser asset separately passes actual GLB/Three motion tests and sampled geometric clearance tests. This asset report does **not** claim a rendered browser gameplay test, continuous dynamics validation, Unreal import testing, or physical/engineering accuracy. No crash deformation, tire contact solver, suspension simulation, authored collision hulls, scanned material textures or production UV/lightmap pipeline is supplied. The source is a refined custom prototype, with high-detail parts separated from the cheaper browser derivative.

## Rebuild / inspect

From project root:

```sh
CAR_SKIP_RENDER=1 blender -b --factory-startup -t 3 --python blender/build_car.py
blender -b --factory-startup -t 2 --python blender/test_car.py
blender -b --factory-startup -t 2 --python blender/test_car_parts.py
PARTS_ONLY=1 blender -b --factory-startup -t 3 --python blender/render_car_parts.py
```

Omit `CAR_SKIP_RENDER=1` to render whole-car hero images after generation. Blender 4.3.2 here lacks OpenImageDenoise; denoising is explicitly disabled. The optional Draco module is also unavailable; GLBs are intentionally uncompressed. Old helper `finalize_car.py` records an earlier normal/export repair; it is **not required** for the current generator.
