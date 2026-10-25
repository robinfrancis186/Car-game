# Coastal Twin — original civilian and police helicopter kit

Original fictional game aircraft, not manufacturer CAD, real-world aircraft specification or airworthy engineering design. Primary manufacturer references were inspected for general light-twin proportions only; see REFERENCE_NOTES.md. No reference photographs, downloaded meshes, real agency logos or imported font files are shipped. Generic markings are Blender-built text outlines.

## Files and budgets
- `civilian/Coastal_Twin_Civilian.blend`, `civilian/helicopter_civilian.glb`:31,728 triangles, 16 draws, 8 PBR materials, 1,183,288 bytes.
- `police/Coastal_Twin_Police.blend`, `police/helicopter_police.glb`:31,846 triangles, 17 draws, 9 PBR materials, 1,180,800 bytes.
- `Rotor_Blur_LOD.blend`, `helicopter_rotor_blur.glb`: optional 192-triangle/2-draw/1-material transparent annuli. Base models contain no blur disks, animation or light cones by default.
- Exact identical staged/public copies live under assets/web and web/public/assets. Per-variant manifests carry exact hashes. Generator: `blender/build_helicopter.py`; existing original project helper `blender/rebuild_car_helpers.py` is imported read-only.

## Geometry and PBR
Smooth lofted cabin, actual transparent canopy/side-window openings, interior seats and flight controls, two turbine cowlings/intakes/exhaust rims, tubular skid gear, steps, recessed panel/door seams, tapering tail boom, real open shrouded anti-torque duct, fixed bearing supports, swept fins, two independently articulated rotors, nav lamps and a yaw/pitch search-pod assembly. Police and civilian paint/labels are distinct generic game liveries.

Paint roughness 0.30–0.32, composite 0.53, glazing 0.10 and brushed metal 0.29 are authored PBR values. No image textures or shader dependency is required. There is no broad third-party asset dependency beyond existing Blender/Three.js tooling.

## Coordinates and scene graph
Metres. Native Blender +X forward/+Y left/+Z up; glTF +X forward/+Y up/−Z left. Root `HELICOPTER_ROOT` is at the skid sole plane Y0, not at rotor hub. Overall stopped bounds are in each manifest; use **swept_bounds_three_m** when sizing an animated aircraft (parked blade AABB is narrower).

- `Airframe`: fixed body/gear/cabin/fin assembly.
- `MainRotor`: pivot[-0.35,3.35,0], rotate about +Y. Four tapered blades. Actual swept radius 5.11606 m.
- `TailRotor`: pivot[-6.75,2.0,0], rotate about −Z. Ten blades. Actual swept radius 0.63848 m; conservative radial gap to duct aperture ≈50 mm.
- `SearchlightYaw > SearchlightPitch > SearchlightSocket`: yaw about +Y; forward tilt about +Z; tested forward/back pitch ±0.70 rad. Socket[1.45,0.35,0] at rest, local light direction[0,−1,0]. The lens's emissive material is **not** a projected spotlight. Runtime must attach a real spot light and target, or a separately labeled visual beam.
- `NavPortSocket`[-1.25,1.52,−1.03] red, `NavStarboardSocket`[-1.25,1.52,+1.03] green, `NavTailSocket`[-7.18,3.47,0] white, `BeaconSocket`[-0.97,2.96,0].

Optional blur asset root `HelicopterBlurRoot` has MainRotorBlur/TailRotorBlur at the identical pivots. Attach at the same aircraft transform and explicitly choose visibility/material opacity with rotor speed. Transparent annuli do not magically blur or spin themselves; exclude them from shadow casting if appropriate. No gameplay/controller code was changed by the asset generator.

## Evidence and limits
`glb_validation.json` per variant uses actual Three GLTFLoader, checks every triangle, finite/unit normals, independent rotor movement, unchanged airframe/other rotor, beam-direction math, dimensions/budgets and identical public copies. It does not claim WebGL rendering.

`mechanics_validation.json` per variant uses the actual GLB reimported into Blender: 72 angular samples for each rotor (144 total) against the fixed airframe; 25 search-pod yaw/pitch combinations against solid skin/glazing. Intentional metallic hub/bearing and gimbal mounting contacts are excluded. These are discrete tests, not continuous mechanical/flight engineering proof. A boom intrusion found in the first draft was fixed before final export.

`native_validation.json` verifies editable source, independent rotor pivots, no image dependencies, measured tail-aperture clearance and 36 interior parts fully within the smooth fuselage cross-section. An initially protruding rectangular aft bulkhead/floor was replaced/fitted before final freeze. Preview front/rear images are actual GLBs imported into CPU Blender, not a prettier alternate model, reference-photo composite or gameplay screenshot. No denoising backend was available.

Aircraft pathing, hovering, chase escalation, collisions, audio, real spotlight projection and runtime performance are separate integration work. The delivered kit does not claim those behaviors already run.

Original project geometry/materials: **reuse license not selected by owner**. No new project-wide CC0/MIT/public-domain grant. Existing third-party software notices remain in force.

## Final asset checkpoint
Final authoring/export, native validation and sampled mechanical checks are recorded in `freeze.json`; compact runtime paths and exact hashes are in `helicopter_kit_manifest.json`. All five final previews carry per-image source-GLB hashes in adjacent provenance JSONs. Final changes were limited to continuous finer door seams and open, visibly dark exhaust ends; rotor, gimbal and mounting contracts are unchanged. No further appearance pass is pending.
